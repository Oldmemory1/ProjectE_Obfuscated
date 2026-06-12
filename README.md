![logo](/src/main/resources/assets/projecte/logo.png?raw=true)

# ProjectE

Complete rewrite of EE2 (Equivalent Exchange 2) for modern Minecraft. Alchemical tools, transmutation, EMC, and more.

## 项目说明

本项目基于 Minecraft Forge 1.16.5，提供了一套完整的 **源码混淆系统**，用于防止其他 Mod 通过 MODID 或包名检测到本 Mod 的存在。

### 混淆原理

构建时，Python 脚本 `obfuscate.py` 会将源码复制到 `.obfuscated/` 目录，并用随机生成的名称替换所有关键标识符：

| 混淆项 | 原始值 | 替换为 |
|--------|--------|--------|
| MODID | `projecte` | 8-12 位随机字符串 (a-z, 0-9) |
| MODNAME | `ProjectE` | 8-12 位随机字符串（首字母大写） |
| 包名 | `moze_intel.projecte` | 两段随机字符串，如 `abc.defg` |
| Maven 组 | `moze_intel` | 随机字符串 |
| 资产目录 | `assets/projecte/` | `assets/<新MODID>/` |
| 数据目录 | `data/projecte/` | `data/<新MODID>/` |

**.obf_seed** 文件记录了当次生成的随机名称，保证同一次混淆构建的一致性。删除后重新生成会得到新的随机名称。

## 编译要求

- **JDK**: OpenJDK 17+
- **Gradle**: 7.3.2 (自动下载)
- **Python**: 3.6+ (仅混淆构建需要)
- **Task**: [go-task](https://taskfile.dev) 3.x

## 快速开始

```bash
# 1. 创建原始源码备份（只需执行一次）
task setup

# 2. 混淆构建（推荐）
task build-obf

# 3. 普通构建（不混淆）
task build
```

产出的 jar 文件在 `build/libs/` 下：`<MODID>-PE1.0.2-universal.jar`。

## 项目结构

```
ProjectE/
├── src/                   # 工作源码目录（混淆构建时会临时替换）
│   ├── main/java/         # 主代码 (moze_intel/projecte/)
│   ├── api/java/          # API 层
│   ├── datagen/java/      # 数据生成器
│   ├── datagen/generated/ # 数据生成输出 (assets/, data/)
│   └── test/java/         # 测试代码
├── Original_Src/          # 原始源码备份（永久不变）
├── .obfuscated/           # 混淆后的源码（构建时生成）
├── libs/                  # 本地 Maven 仓库（补充离线依赖）
├── obfuscate.py           # 混淆脚本
├── Taskfile.yml           # Task 任务编排文件
├── build.gradle           # Gradle 构建脚本
└── gradle.properties      # 版本与依赖配置
```

## Taskfile 说明

所有构建操作通过 `task <命令>` 执行。

| 命令 | 说明 |
|------|------|
| `task build` | 普通构建：从 Original_Src 还原 src，然后 Gradle 编译 |
| `task build-obf` | 混淆构建：生成 .obfuscated → 替换 src → 编译 → 自动还原 src |
| `task obfuscate` | 仅生成 .obfuscated/，不编译 |
| `task clean-obf` | 删除 .obfuscated/，下次构建会生成新的随机名称 |
| `task setup` | 创建 Original_Src/ 备份（首次必须执行） |
| `task clean` | 清理 Gradle 构建产物 |
| `task jar` | 仅打 jar 包，跳过测试 |
| `task test` | 仅运行测试 |

### build-obf 工作流

```
task setup (一次性)
    │
    ▼
Original_Src/  ← 永久保存原始源码
    │
    ▼ obfuscate.py
.obfuscated/   ← 混淆后的源码 + 补丁后的 build.gradle
    │
    ▼ 部署到 src/
src/            ← 临时被混淆源码替换
    │
    ▼ ./gradlew build
build/libs/    ← 混淆后的 jar
    │
    ▼ trap EXIT
src/ 自动还原 ← 从 Original_Src 恢复
build.gradle 自动还原
```

### 混淆构建后验证

```bash
# 检查 jar 内是否还有原始 MODID
jar tf build/libs/<MODID>-PE1.0.2-universal.jar | grep -i "projecte\|moze_intel"

# 检查包名是否已替换
jar tf build/libs/<MODID>-PE1.0.2-universal.jar | head -20
```

## 依赖说明

| 集成 Mod | 依赖方式 | 状态 |
|----------|----------|------|
| JEI | 远程 Maven (`dvs1.progwml6.com`) | ✅ |
| CraftTweaker | 远程 Maven (`maven.blamejared.com`) | ✅ |
| Curios | 远程 Maven (`maven.theillusivec4.top`) | ✅ |
| Jade | CurseMaven | ✅ |
| TheOneProbe | 本地 `libs/` (maven.tterrag.com 已下线) | ✅ |

## License

MIT
