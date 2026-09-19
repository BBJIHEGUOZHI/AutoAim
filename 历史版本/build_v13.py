#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
91-client v1.3 构建脚本
==========================================================
基线：v1.2（91-client-beta1.0-v1.2.jar）—— 当前最新稳定版。
v1.3 唯一内容：子弹放大（BulletScale）最大倍数上限 10 -> 250。

改动的 2 个类（全部是数值上限，无逻辑改动）：
  修改  com/xybaka/autoaim/modules/combat/BulletScale.class
        NumberSetting("...", "Scale", 5.0, 0.01, 10.0, 0.01)  ->  max 10.0 -> 250.0
        （default=5.0 / min=0.01 / step=0.01 均不变）
  修改  com/xybaka/autoaim/net/BulletScaleServer.class
        sanitize(): f > 10.0f ? 10.0f : f  ->  f > 250.0f ? 250.0f : f
        （为什么必须一起改：客户端 BulletScaleReporter 把 scale 上报给服务端，
          BulletScaleServer.sanitize 是服务端的安全阀；不同步改的话，联机时
          滑块拖到 250 会被服务端截回 10。）

改动资源：无。
"""
import os, shutil, subprocess, hashlib, zipfile, sys

ROOT    = "C:/Users/bao12/WorkBuddy/2026-09-05-16-11-07/91-client-v1.3"
SRC     = os.path.join(ROOT, "src")
BUILD   = os.path.join(ROOT, "build")
OUT     = os.path.join(ROOT, "out")

BASE_JAR = "C:/Users/bao12/WorkBuddy/2026-09-05-16-11-07/91-client-v1.2/91-client-beta1.0-v1.2.jar"
JAVAC    = "C:/Program Files/Java/jdk-17/bin/javac.exe"
OUT_JAR  = os.path.join(ROOT, "91-client-beta1.0-v1.3.jar")

LIBS = {
 "srg":           "D:/tenrp/libraries/net/minecraft/client/1.20.1-20230612.114412/client-1.20.1-20230612.114412-srg.jar",
 "forge":         "D:/tenrp/libraries/net/minecraftforge/forge/1.20.1-47.4.23/forge-1.20.1-47.4.23-universal.jar",
 "mixin":         "D:/tenrp/libraries/org/spongepowered/mixin/0.8.5/mixin-0.8.5.jar",
 "log4j":         "D:/tenrp/libraries/org/apache/logging/log4j/log4j-api/2.17.0/log4j-api-2.17.0.jar",
 "joml":          "D:/tenrp/libraries/org/joml/joml/1.10.5/joml-1.10.5.jar",
 "gson":          "D:/tenrp/libraries/com/google/code/gson/gson/2.10/gson-2.10.jar",
 "brigadier":     "D:/tenrp/libraries/com/mojang/brigadier/1.0.18/brigadier-1.0.18.jar",
 "authlib":       "D:/tenrp/libraries/com/mojang/authlib/1.5.21/authlib-1.5.21.jar",
 "datafixerupper":"D:/tenrp/libraries/com/mojang/datafixerupper/10.0.21/datafixerupper-10.0.21.jar",
 "commons":       "D:/tenrp/libraries/org/apache/commons/commons-lang3/3.12.0/commons-lang3-3.12.0.jar",
 "javafmllang":   "D:/tenrp/libraries/net/minecraftforge/javafmllanguage/1.20.1-47.4.23/javafmllanguage-1.20.1-47.4.23.jar",
 "forgespi":      "D:/tenrp/libraries/net/minecraftforge/forgespi/4.0.15-4.x/forgespi-4.0.15-4.x.jar",
 "eventbus":      "D:/tenrp/libraries/net/minecraftforge/eventbus/6.0.5/eventbus-6.0.5.jar",
 "lwjgl":         "D:/tenrp/libraries/org/lwjgl/lwjgl/3.2.2/lwjgl-3.2.2.jar",
 "lwjgl-glfw":    "D:/tenrp/libraries/org/lwjgl/lwjgl-glfw/3.2.2/lwjgl-glfw-3.2.2.jar",
 "tacz":          "D:/tenrp/versions/1.20.1-Forge_47.4.23/mods/[永恒枪械工坊：零] tacz-1.20.1-1.1.8-hotfix.jar",
}

EXPECT_CHG = {
 "com/xybaka/autoaim/modules/combat/BulletScale.class",
 "com/xybaka/autoaim/net/BulletScaleServer.class",
}

def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(65536), b''):
            h.update(b)
    return h.hexdigest()

def main():
    assert os.path.isfile(BASE_JAR), "baseline v1.2 jar missing"
    for k, v in LIBS.items():
        assert os.path.isfile(v), "missing lib %s: %s" % (k, v)
    assert os.path.isfile(JAVAC), "javac missing"
    print("[0] baseline v1.2 md5:", md5(BASE_JAR))

    # 1) fresh build dir = unpacked v1.2
    if os.path.isdir(BUILD): shutil.rmtree(BUILD)
    if os.path.isdir(OUT):   shutil.rmtree(OUT)
    os.makedirs(BUILD); os.makedirs(OUT)
    print("[1] unpacking baseline v1.2 -> build/")
    with zipfile.ZipFile(BASE_JAR) as z:
        z.extractall(BUILD)

    # 2) compile the two sources
    srcs = [
        os.path.join(SRC, "com/xybaka/autoaim/modules/combat/BulletScale.java"),
        os.path.join(SRC, "com/xybaka/autoaim/net/BulletScaleServer.java"),
    ]
    cp = os.pathsep.join([BASE_JAR] + list(LIBS.values()))
    cmd = [JAVAC, "--release", "17", "-g", "-encoding", "UTF-8", "-proc:none",
           "-sourcepath", SRC, "-cp", cp, "-d", OUT] + srcs
    print("[2] compiling %d sources ..." % len(srcs))
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

    # 4) package  (资源不动)
    print("[4] packaging ->", OUT_JAR)
    if os.path.isfile(OUT_JAR): os.remove(OUT_JAR)
    with zipfile.ZipFile(OUT_JAR, 'w', zipfile.ZIP_DEFLATED) as z:
        for dp, _, fs in os.walk(BUILD):
            for f in fs:
                full = os.path.join(dp, f)
                z.write(full, os.path.relpath(full, BUILD))
    print("packaged bytes:", os.path.getsize(OUT_JAR))

    # 5) audit
    print("[5] auditing vs baseline v1.2 ...")
    def entries(p):
        d = {}
        with zipfile.ZipFile(p) as z:
            for i in z.infolist():
                d[i.filename] = hashlib.md5(z.read(i.filename)).hexdigest()
        return d
    base = entries(BASE_JAR); new = entries(OUT_JAR)
    only_base = set(base) - set(new)
    only_new  = set(new) - set(base)
    diff = [n for n in base if n in new and base[n] != new[n]]
    print("entries baseline:", len(base), "new:", len(new))
    print("added  :", sorted(only_new))
    print("removed:", sorted(only_base))
    print("changed:", sorted(diff))
    ok = (not only_new and not only_base and set(diff) == EXPECT_CHG)
    print("AUDIT " + ("PASS" if ok else "WARN"))
    if not ok:
        print("  expect_chg", EXPECT_CHG, "got", set(diff))
    print("new jar md5:", md5(OUT_JAR))

if __name__ == "__main__":
    main()
