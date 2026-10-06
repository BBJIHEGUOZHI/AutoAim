#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
91-client v1.5.3 构建脚本
==========================================================
基线：v1.5.1（91-client-beta1.1-v1.5.1.jar.disabled，即 MobileFire 机动开火原始构建）
v1.5.3 内容（相对 v1.5.1 仅改动 1 条目）：
  - com/xybaka/autoaim/mixin/tacz/LocalPlayerSprintMixin.class
    修复：@Redirect handler autoaim$ignoreStopSprint() 由 static 改为 实例方法，
    并真重编译以重算 StackMapTable。
    （目标方法 LocalPlayerSprint.getProcessedSprintStatus 是实例方法，handler 的
     static 修饰符必须与其一致；仅翻转访问标志位会破坏栈帧、Mixin 加载即崩。）

本脚本用于“从源码重建 v1.5.3 jar”：
  基座 = 同目录的 91-client-beta1.1-v1.5.1.jar.disabled（本定版包基线）
  注入 = 由 src/com/xybaka/autoaim/mixin/tacz/LocalPlayerSprintMixin.java 重编译出的 class
  审计 = 重建后 jar 与基座逐条目比对，应仅 1 条目变更（其余 0 漂移）
"""
import os, shutil, subprocess, hashlib, zipfile, sys

ROOT    = os.path.dirname(os.path.abspath(__file__))
SRC     = os.path.join(ROOT, "src")
BUILD   = os.path.join(ROOT, "build")
OUT     = os.path.join(ROOT, "out")

BASE_JAR = os.path.join(ROOT, "91-client-beta1.1-v1.5.1.jar.disabled")
JAVAC    = "C:/Users/bao12/AppData/Roaming/.minecraft/runtime/java-runtime-beta/bin/javac.exe"
OUT_JAR  = os.path.join(ROOT, "91-client-beta1.1-v1.5.3.jar")

TACZ     = "D:/tenrp/versions/TACZ&生存/mods/tacz-1.20.1-1.1.8-hotfix.jar"
LIBS = [
 "D:/tenrp/libraries/net/minecraft/client/1.20.1-20230612.114412/client-1.20.1-20230612.114412-srg.jar",
 "D:/tenrp/libraries/net/minecraftforge/forge/1.20.1-47.4.23/forge-1.20.1-47.4.23-universal.jar",
 "D:/tenrp/libraries/net/minecraftforge/forge/1.20.1-47.4.23/forge-1.20.1-47.4.23-client.jar",
 "D:/tenrp/libraries/net/minecraftforge/eventbus/6.0.5/eventbus-6.0.5.jar",
 "D:/tenrp/libraries/org/spongepowered/mixin/0.8.5/mixin-0.8.5.jar",
 "D:/tenrp/libraries/org/apache/logging/log4j/log4j-api/2.19.0/log4j-api-2.19.0.jar",
 "D:/tenrp/libraries/it/unimi/dsi/fastutil/8.5.9/fastutil-8.5.9.jar",
 BASE_JAR,
 TACZ,
]
EXPECT_CHG = {"com/xybaka/autoaim/mixin/tacz/LocalPlayerSprintMixin.class"}

def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(65536), b''):
            h.update(b)
    return h.hexdigest()

def main():
    assert os.path.isfile(BASE_JAR), "baseline v1.5.1 jar (.disabled) missing"
    assert os.path.isfile(TACZ), "tacz jar missing: %s" % TACZ
    for v in LIBS:
        assert os.path.isfile(v), "missing lib: %s" % v
    assert os.path.isfile(JAVAC), "javac missing"
    print("[0] baseline v1.5.1 md5:", md5(BASE_JAR))

    if os.path.isdir(BUILD): shutil.rmtree(BUILD)
    if os.path.isdir(OUT):   shutil.rmtree(OUT)
    os.makedirs(BUILD); os.makedirs(OUT)

    # 1) unpack baseline
    print("[1] unpacking baseline v1.5.1 -> build/")
    with zipfile.ZipFile(BASE_JAR) as z:
        z.extractall(BUILD)

    # 2) snapshot baseline entry md5
    baseline = {}
    with zipfile.ZipFile(BASE_JAR) as z:
        for i in z.infolist():
            baseline[i.filename] = md5(z.read(i.filename))

    # 3) compile the one source
    srcs = [os.path.join(SRC, "com/xybaka/autoaim/mixin/tacz/LocalPlayerSprintMixin.java")]
    cp = os.pathsep.join(LIBS)
    cmd = [JAVAC, "-proc:none", "-encoding", "UTF-8", "-cp", cp, "-d", OUT] + srcs
    print("[2] compiling %d source ..." % len(srcs))
    r = subprocess.run(cmd, capture_output=True)
    def dec(b):
        try: return b.decode('gbk')
        except Exception: return b.decode('utf-8', 'replace')
    print("--- javac stdout ---"); print(dec(r.stdout) or "(empty)")
    print("--- javac stderr ---"); print(dec(r.stderr) or "(empty)")
    if r.returncode != 0:
        print("COMPILE FAILED"); sys.exit(1)
    print("COMPILE OK")

    produced = []
    for dp, _, fs in os.walk(OUT):
        for f in fs:
            if f.endswith(".class"):
                produced.append(os.path.relpath(os.path.join(dp, f), OUT).replace(os.sep, "/"))
    print("[3] produced classes:", sorted(produced))
    assert sorted(produced) == sorted(EXPECT_CHG), \
        "compiled set mismatch: %s" % sorted(produced)

    for rel in produced:
        dstp = os.path.join(BUILD, rel)
        os.makedirs(os.path.dirname(dstp), exist_ok=True)
        shutil.copy2(os.path.join(OUT, rel), dstp)

    # 4) package
    print("[4] packaging ->", OUT_JAR)
    if os.path.isfile(OUT_JAR): os.remove(OUT_JAR)
    with zipfile.ZipFile(OUT_JAR, 'w', zipfile.ZIP_DEFLATED) as z:
        for dp, _, fs in os.walk(BUILD):
            for f in fs:
                full = os.path.join(dp, f)
                z.write(full, os.path.relpath(full, BUILD))
    print("packaged bytes:", os.path.getsize(OUT_JAR))

    # 5) audit vs baseline snapshot (expect only 1 drift)
    print("[5] auditing vs baseline ...")
    new = {}
    with zipfile.ZipFile(OUT_JAR) as z:
        for i in z.infolist():
            new[i.filename] = md5(z.read(i.filename))
    added  = sorted(set(new) - set(baseline))
    removed= sorted(set(baseline) - set(new))
    changed= sorted([n for n in baseline if n in new and baseline[n] != new[n]])
    print("entries baseline:", len(baseline), "new:", len(new))
    print("added  :", added)
    print("removed:", removed)
    print("changed:", changed)
    ok = (not added and not removed and changed == sorted(EXPECT_CHG))
    print("AUDIT " + ("PASS (only LocalPlayerSprintMixin changed)" if ok else "WARN"))
    print("new jar md5:", md5(OUT_JAR))

if __name__ == "__main__":
    main()
