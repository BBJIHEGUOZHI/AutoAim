import os, zipfile, shutil, subprocess, json

ROOT = "D:/Users/bao12/Desktop/91-client-备份/v1.6-AA"
SRC = os.path.join(ROOT, "src")
CLS = os.path.join(ROOT, "build", "classes")
STAGE = os.path.join(ROOT, "build", "stage")
OUT = os.path.join(ROOT, "out")
V153 = "D:/Users/bao12/Desktop/91-client-备份/v1.5-最新稳定版（MobileFire机动开火）/91-client-beta1.1-v1.5.3.jar"
JAVAC = "C:/Program Files/Java/jdk-17/bin/javac.exe"
LIBS_DIR = "D:/tenrp/libraries"

def find_jars(patterns):
    res = []
    for dp, _, fs in os.walk(LIBS_DIR):
        for f in fs:
            if not f.endswith(".jar"):
                continue
            for p in patterns:
                if p in f:
                    res.append(os.path.join(dp, f))
                    break
    return res

needed = ["client-1.20.1", "forge-1.20.1", "fmlcore-1.20.1", "fmlloader-1.20.1",
          "javafmllanguage-1.20.1", "forgespi", "eventbus", "mixin-0.8.5",
          "log4j-api", "fastutil", "gson", "brigadier", "lwjgl-glfw"]
cp = find_jars(needed)
cp.append(V153)
# TACZ 本体：TaczAimSupplierMixin 用 value= 直接引用 ModernKineticGunScriptAPI，
# 编译期需要 TACZ 类在 classpath（否则 "程序包 com.tacz.guns.item 不存在"）。
# 运行时是否安装 TACZ 由 mixin 的 @Mixin 目标决定，不依赖此编译期依赖。
TACZ_JAR = "D:/tenrp/versions/TACZ&生存/mods/tacz-1.20.1-1.1.8-hotfix2.jar"
if os.path.isfile(TACZ_JAR):
    cp.append(TACZ_JAR)
    print("  [TACZ]", TACZ_JAR)
else:
    print("  [WARN] 找不到 TACZ jar：", TACZ_JAR)
cp = list(dict.fromkeys(cp))
print("== classpath (%d jars) ==" % len(cp))
for c in cp:
    print("  ", c)

os.makedirs(CLS, exist_ok=True)
shutil.rmtree(CLS, ignore_errors=True)  # 每次清空编译输出，防止旧 class 残留混进 jar
os.makedirs(CLS, exist_ok=True)
sources = []
for dp, _, fs in os.walk(SRC):
    for f in fs:
        if f.endswith(".java"):
            sources.append(os.path.join(dp, f))
print("== sources ==")
for s in sources:
    print("  ", s)

cmd = [JAVAC, "-encoding", "UTF-8", "-proc:none", "-d", CLS, "-cp", ";".join(cp)] + sources
print("== compiling ==")
r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
print(r.stdout)
print(r.stderr)
if r.returncode != 0:
    print("COMPILE FAILED")
    raise SystemExit(1)
print("COMPILE OK")

# ---- jar surgery ----
shutil.rmtree(STAGE, ignore_errors=True)
os.makedirs(STAGE)
with zipfile.ZipFile(V153) as z:
    z.extractall(STAGE)

# 1) 删除旧大陀螺 SpinBot
fun_dir = os.path.join(STAGE, "com/xybaka/autoaim/modules/fun")
if os.path.isdir(fun_dir):
    for f in os.listdir(fun_dir):
        if f.startswith("SpinBot"):
            os.remove(os.path.join(fun_dir, f))
            print("removed", f)

# 2) 用新编译的 class 覆盖/新增
count = 0
for dp, _, fs in os.walk(CLS):
    for f in fs:
        if not f.endswith(".class"):
            continue
        full = os.path.join(dp, f)
        rel = os.path.relpath(full, CLS).replace("\\", "/")
        dest = os.path.join(STAGE, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(full, dest)
        count += 1
print("injected %d class files" % count)

# 3) 把 AntiAimModelMixin 并进主配置 autoaim.mixins.json（client 数组）。
#    ⚠️ 铁律：不要另建第二个 mixins.json + mods.toml [[mixins]] 注册！
#    实测 Forge 47 对追加的 [[mixins]] 条目不会转交给 Mixin（debug.log 里
#    只有主/tacz 两个配置被 "Registering mixin config"，autoaim-aa 彻底没
#    出现，AntiAim 静默不加载）。所以 AA 的 mixin 必须走主配置。
mixjson = os.path.join(STAGE, "autoaim.mixins.json")
with open(mixjson, "r", encoding="utf-8") as f:
    mj = json.load(f)
if "AntiAimModelMixin" not in mj.setdefault("client", []):
    mj["client"].append("AntiAimModelMixin")
# TaczAimSupplierMixin：AA 弹道解耦。注入 TACZ ModernKineticGunScriptAPI.setYawSupplier/
# setPitchSupplier，AA 伪装时 cancel 掉 TACZ 的赋值，让子弹走真实准星角度。
# 必须注册在同一份 autoaim.mixins.json（Forge 47 不转交第二个 mixins 配置）。
if "TaczAimSupplierMixin" not in mj.setdefault("client", []):
    mj["client"].append("TaczAimSupplierMixin")
with open(mixjson, "w", encoding="utf-8") as f:
    json.dump(mj, f, indent=2)
print("patched autoaim.mixins.json client:", mj["client"])

# 3.5) AA 汉化：把 AA 模块+设置的翻译写进语言包资源文件。
#      I18n 按游戏语言从 /assets/autoaim/lang/{lang}.json 加载；用户是中文，
#      故 zh_cn 必填；en_us 作为兜底（英文界面也能显示）。
AA_ZH = {
    "autoaim.module.AntiAim": "反自瞄",
    "autoaim.aa.HeadDown": "低头",
    "autoaim.aa.HeadPitch": "低头角度",
    "autoaim.aa.Spin": "大陀螺",
    "autoaim.aa.SpinSpeed": "陀螺速度 (圈/秒)",
    "autoaim.aa.Twitch": "抽搐",
    "autoaim.aa.TwitchMode": "抽搐模式",
    "autoaim.aa.TwitchValue": "抽搐幅度",
    "autoaim.aa.TwitchHead": "抽搐:头",
    "autoaim.aa.TwitchBody": "抽搐:身体",
    "autoaim.aa.TwitchRArm": "抽搐:右手",
    "autoaim.aa.TwitchLArm": "抽搐:左手",
    "autoaim.aa.TwitchRLeg": "抽搐:右腿",
    "autoaim.aa.TwitchLLeg": "抽搐:左腿",
    "autoaim.aa.DisableOnShoot": "射击时停用",
    # ---- AA 抽搐模式的四个选项值（ModeSetting 显式传 i18nKeys，键规则 autoaim.mode.<小写>）----
    "autoaim.mode.rotation": "旋转",
    "autoaim.mode.jitter": "抖动",
    "autoaim.mode.angle": "摆角",
    "autoaim.mode.position": "位移",
    # ---- v1.6 增强：NoRecoil 倍率 ----
    "autoaim.setting.NoRecoil.PitchKeep": "纵向保留 (%)",
    "autoaim.setting.NoRecoil.YawKeep": "横向保留 (%)",
    # ---- v1.6 增强：NoBolt 模式 / 倍率 ----
    "autoaim.setting.NoBolt.Skip": "跳过拉栓",
    "autoaim.setting.NoBolt.Speed": "拉栓速度 (倍)",
}
AA_EN = {
    "autoaim.module.AntiAim": "AntiAim",
    "autoaim.aa.HeadDown": "Head Down",
    "autoaim.aa.HeadPitch": "Head Pitch",
    "autoaim.aa.Spin": "Spin",
    "autoaim.aa.SpinSpeed": "Spin Speed (rps)",
    "autoaim.aa.Twitch": "Twitch",
    "autoaim.aa.TwitchMode": "Twitch Mode",
    "autoaim.aa.TwitchValue": "Twitch Value",
    "autoaim.aa.TwitchHead": "Twitch: Head",
    "autoaim.aa.TwitchBody": "Twitch: Body",
    "autoaim.aa.TwitchRArm": "Twitch: Right Arm",
    "autoaim.aa.TwitchLArm": "Twitch: Left Arm",
    "autoaim.aa.TwitchRLeg": "Twitch: Right Leg",
    "autoaim.aa.TwitchLLeg": "Twitch: Left Leg",
    "autoaim.aa.DisableOnShoot": "Disable On Shoot",
    "autoaim.mode.rotation": "Rotation",
    "autoaim.mode.jitter": "Jitter",
    "autoaim.mode.angle": "Angle",
    "autoaim.mode.position": "Position",
    "autoaim.setting.NoRecoil.PitchKeep": "Pitch Keep (%)",
    "autoaim.setting.NoRecoil.YawKeep": "Yaw Keep (%)",
    "autoaim.setting.NoBolt.Skip": "Skip Bolt",
    "autoaim.setting.NoBolt.Speed": "Bolt Speed (x)",
}

def merge_lang(lang_file, pairs):
    path = os.path.join(STAGE, "assets", "autoaim", "lang", lang_file)
    if not os.path.isfile(path):
        print("lang file missing, skip:", path)
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    changed = False
    for k, v in pairs.items():
        if k not in data:
            data[k] = v
            changed = True
    if changed:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("merged AA translations into", lang_file)
    else:
        print("AA translations already present in", lang_file)

merge_lang("zh_cn.json", AA_ZH)
merge_lang("en_us.json", AA_EN)


# 4) AntiAim 模块注册：直接写死在重编译的 ModuleManager 构造器里
#    （this.modules.add(new AntiAim())），不再用注入 mixin。

# 5) 修改 mods.toml：版本号（不动 [[mixins]] 段）
toml = os.path.join(STAGE, "META-INF", "mods.toml")
with open(toml, "r", encoding="utf-8") as f:
    t = f.read()
t = t.replace('version="1.0.0-beta"', 'version="1.6-beta"')
t = t.replace('displayName="91-client-beta1.0"', 'displayName="91-client-beta1.6"')
with open(toml, "w", encoding="utf-8") as f:
    f.write(t)
print("patched mods.toml")

# 6) 重新打包
outjar = os.path.join(OUT, "91-client-v1.6-beta.jar")
if os.path.exists(outjar):
    os.remove(outjar)
all_files = []
for dp, _, fs in os.walk(STAGE):
    for f in fs:
        full = os.path.join(dp, f)
        rel = os.path.relpath(full, STAGE).replace("\\", "/")
        all_files.append(rel)
all_files.sort(key=lambda x: (x != "META-INF/MANIFEST.MF", x))
with zipfile.ZipFile(outjar, "w", zipfile.ZIP_DEFLATED) as z:
    for rel in all_files:
        z.write(os.path.join(STAGE, rel), rel)
print("WROTE", outjar, os.path.getsize(outjar), "bytes")
