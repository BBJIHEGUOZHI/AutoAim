#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
91-client v1.4 构建脚本
==========================================================
基线：v1.3（91-client-beta1.0-v1.3.jar）
v1.4 内容（A0 + A0-ext + A1 + A2，相对 v1.3 改动 7 条目）：
  - autoaim.tacz.mixins.json               : required false -> true（失效即崩溃报清错，终结静默失效）
  - BulletWallbangMixin.class              : 重写穿墙（参照 nospread：mixin BlockRayTrace.rayTraceBlocks，
                                             RETURN 注入，Wallbang 开启且撞墙时强制返回 MISS -> 子弹穿墙）
  - Module.class / *Setting.class(4)       : A0 配置不落盘 / A0-ext 设置即存盘等配置系统修复

本脚本用于“从源码重建 v1.4 jar”：
  基座 = 同目录的 91-client-beta1.0-v1.4.jar（即本定版包本体）
  注入 = 由 src/com/xybaka/autoaim/mixin/tacz/BulletWallbangMixin.java 重编译出的 class
  审计 = 重建后 jar 与基座逐条目比对，应 0 漂移（证明源码可复现定版字节码）
"""
import os, shutil, subprocess, hashlib, zipfile, sys

ROOT    = "C:/Users/bao12/WorkBuddy/2026-09-05-16-11-07/91-client-stable/v1.4"
SRC     = os.path.join(ROOT, "src")
BUILD   = os.path.join(ROOT, "build")
OUT     = os.path.join(ROOT, "out")

BASE_JAR = os.path.join(ROOT, "91-client-beta1.0-v1.4.jar")
JAVAC    = "C:/Program Files/Eclipse Adoptium/jdk-21.0.12.8-hotspot/bin/javac.exe"
OUT_JAR  = os.path.join(ROOT, "91-client-beta1.0-v1.4.jar")

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

EXPECT_CHG = {
 "com/xybaka/autoaim/mixin/tacz/BulletWallbangMixin.class",
}

def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(65536), b''):
            h.update(b)
    return h.hexdigest()

def main():
    assert os.path.isfile(BASE_JAR), "baseline v1.4 jar missing"
    assert os.path.isfile(TACZ), "tacz jar missing: %s" % TACZ
    for v in LIBS:
        assert os.path.isfile(v), "missing lib: %s" % v
    assert os.path.isfile(JAVAC), "javac missing"
    print("[0] baseline v1.4 md5:", md5(BASE_JAR))

    if os.path.isdir(BUILD): shutil.rmtree(BUILD)
    if os.path.isdir(OUT):   shutil.rmtree(OUT)
    os.makedirs(BUILD); os.makedirs(OUT)

    # 1) unpack baseline
    print("[1] unpacking baseline v1.4 -> build/")
    with zipfile.ZipFile(BASE_JAR) as z:
        z.extractall(BUILD)

    # 2) snapshot baseline entry md5 (for later audit)
    baseline = {}
    with zipfile.ZipFile(BASE_JAR) as z:
        for i in z.infolist():
            baseline[i.filename] = hashlib.md5(z.read(i.filename)).hexdigest()

    # 3) compile the one source
    srcs = [os.path.join(SRC, "com/xybaka/autoaim/mixin/tacz/BulletWallbangMixin.java")]
    cp = os.pathsep.join(LIBS)
    cmd = [JAVAC, "--release", "17", "-proc:none", "-encoding", "UTF-8",
           "-cp", cp, "-d", OUT] + srcs
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

    # 5) audit vs baseline snapshot (expect 0 drift)
    print("[5] auditing vs baseline ...")
    new = {}
    with zipfile.ZipFile(OUT_JAR) as z:
        for i in z.infolist():
            new[i.filename] = hashlib.md5(z.read(i.filename)).hexdigest()
    added  = sorted(set(new) - set(baseline))
    removed= sorted(set(baseline) - set(new))
    changed= sorted([n for n in baseline if n in new and baseline[n] != new[n]])
    print("entries baseline:", len(baseline), "new:", len(new))
    print("added  :", added)
    print("removed:", removed)
    print("changed:", changed)
    ok = (not added and not removed and not changed)
    print("AUDIT " + ("PASS (0 drift, reproducible)" if ok else "WARN"))
    print("new jar md5:", md5(OUT_JAR))

if __name__ == "__main__":
    main()
