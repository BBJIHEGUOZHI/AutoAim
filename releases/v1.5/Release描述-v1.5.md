### 91-client v1.5 · AutoAim 增强版

基于 [xyBakaQAQ/AutoAim](https://github.com/xyBakaQAQ/AutoAim)（MIT 许可）的增强分支，面向 **Minecraft 1.20.1 / Forge 47.4.23 / TACZ（永恒枪械工坊：零）1.1.8**。

上游全部功能保留，本分支为严格超集。

#### 本版新增 / 修复

- **🏃 MobileFire 机动开火（v1.5 主线新功能）** — 冲刺 / 移动中可正常开枪，由 `modules/movement/MobileFire` 与 3 个 tacz SprintMixin 共同实现
- **🧱 子弹穿墙（Wallbang）真正生效**（自 v1.4）— 开启后子弹不再被墙体截断，直接穿透并在墙后命中目标
- **💾 配置落盘修复**（自 v1.4）— 中文环境下改动设置 / 按键后，重开游戏不再回退默认值
- **🔫 子弹放大上限 250**（自 v1.3）— 客户端滑块与服务端安全阀成对放开，联机不会被截回 10
- **🌐 联机生效** — `displayTest = IGNORE_ALL_VERSION`，好友未安装本 mod 也能进入房主开启的世界并看到效果

#### 安装

1. 把 `91-client-beta1.1-v1.5.3.jar` 放进 `.minecraft/mods/`（PCL 用户：版本目录 / mods /）
   - ⚠️ mods 目录同时只能留 **1 个**本 mod 的 jar，多放会因重复注册模块导致启动崩溃。换版本时把旧的改名末尾加 `.disabled` 留档，不要删除。
2. 把 `AutoAim/` 目录（含 `config.json` + `license.flag`）放进**游戏版本目录**下
   - 直接用下方参数包 zip 解压到版本目录即可

#### 回退

换装仓库 `历史版本/` 里的 jar 即可（fixed17 / v1.1 / v1.2 / v1.3 / v1.4 均已附）。

#### 已知限制

- **穿墙为无限穿透** — 1.20.1 的 `ClipContext` 未暴露实体接口，无法按每颗子弹计数穿透层数，因此「最多穿 N 面墙」暂未接入
- **不支持独立服务器** — jar 内约 50 个 class 引用 `net/minecraft/client/`，本质是纯客户端 mod。谁开房 / 开服谁安装即可
- **lightspeed 兼容性** — 同实例装 lightspeed 优化 mod 时，其 fresh 重变换会破坏本 mixin 类的 StackMapTable（删缓存重变换即崩）。当前 TACZ&生存 实例已将 lightspeed 设为 `.disabled`。如要启用须先确认不再重变换本 jar

#### 许可

MIT License · 保留原作者版权声明（© 2024 xyBakaQAQ）
