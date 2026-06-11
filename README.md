# ProjectE Obfuscated

基于 [ProjectE](https://github.com/sinkillerj/ProjectE) (mc1.12.x 分支) 的混淆构建版本。通过对 MODID、MODNAME 和 Java 包名的随机化，防止其他模组通过固定标识符检测本模组的物品、方块和行为。

## 构建要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Java | OpenJDK 8 | 编译 Minecraft 1.12.2 模组必需 |
| Python | 3.10+ | 运行混淆脚本 `obfuscate.py` |
| Task | 3.x | [Taskfile](https://taskfile.dev/) 任务编排工具 |
| Gradle | 2.7 (wrapper) | 项目自带 `gradlew`，无需手动安装 |

容器环境下确保 `JAVA8_HOME` 指向正确的 JDK 8 路径（默认 `/usr/lib/jvm/java-8-openjdk-amd64`）。

## 快速开始

```bash
task setup       # 首次使用：创建 Original_Src/ 保存原始源码
task build       # 混淆构建（默认任务，等同于直接运行 task）
```

第一次构建较慢（~90s），因为 ForgeGradle 需要反混淆 Minecraft 源码。**第二次开始 ~25s**，得益于 Gradle Daemon 和增量编译。

`gradle.properties` 中已配置性能优化：
```properties
org.gradle.daemon=true
org.gradle.jvmargs=-Xmx4g -Xms512m
org.gradle.parallel=true
```

## 项目结构

执行 `task setup` 后：

```
ProjectE/
├── src/                 ← 工作源码（会被临时覆盖，勿手动修改）
├── Original_Src/        ← 原始源码永久备份（gitignored，只读，永不被修改）
├── .obfuscated/         ← 混淆后的源码副本（gitignored，可复用缓存）
├── obfuscate.py         ← 混淆脚本
├── Taskfile.yml         ← 任务编排
├── build.gradle         ← Gradle 构建脚本（原始版本）
└── gradle.properties    ← Gradle 配置（含 daemon 优化）
```

## 可用任务

| 任务 | 说明 |
|------|------|
| `task` / `task build` | 混淆构建（默认） |
| `task setup` | **首次执行一次**，创建 `Original_Src/` |
| `task obfuscate` | 仅生成 `.obfuscated/` 混淆源码，不构建 |
| `task test` | 运行测试（从 `Original_Src/` 还原后执行） |
| `task jar` | 仅打 jar 包，跳过测试 |
| `task clean` | 清理 `build/` 构建产物 |
| `task clean-obf` | 删除 `.obfuscated/` 缓存，下次生成全新随机名称 |

## 混淆构建流程 (`task build`)

### 数据流

```
Original_Src/ (只读源码)  +  build.gradle (原始)
        │
        │  obfuscate.py 读取并生成
        ▼
   .obfuscated/ (混淆副本，包含混淆后的 build.gradle)
        │
        │  rm -rf src && cp -a .obfuscated src   (部署混淆源码)
        │  cp src/build.gradle build.gradle        (替换构建脚本)
        ▼
     src/ (混淆版)  →  ./gradlew build  →  universal.jar
        │
        │  trap EXIT: rm -rf src
        │             cp -a Original_Src src      (还原源码)
        │             git checkout build.gradle    (还原构建脚本)
        ▼
     src/ (已还原为原始状态)
```

### 混淆的三项内容

| 项目 | 原始值 | 混淆后 |
|------|--------|--------|
| MODID | `projecte` | 随机 8-12 位小写字母数字 |
| MODNAME | `ProjectE` | 随机 8-12 位混合大小写 |
| Java 包名 | `moze_intel.projecte` | 两段随机名，如 `abc123.xyz789` |
| Maven group | `moze_intel` | 与包名第一段一致 |

### obfuscate.py 替换范围

- **Java 源文件**: 包声明、import 语句、硬编码的 `"projecte"` / `"ProjectE"` 字符串、`@SidedProxy` 等注解中的全限定类名
- **资源文件**:
  - JSON 模型/配方：`projecte:` → 随机 MODID 前缀
  - lang 翻译键：`itemGroup.projecte` → `itemGroup.{随机ID}`
  - 路径：`assets/projecte/` → `assets/{随机ID}/`
  - 命令引用：`/projecte ` → `/{随机ID} `
  - mcmod.info：`"projecte"` / `"ProjectE"` → 随机值
  - `_factories.json` 中的全限定工厂类名
- **build.gradle**：shadowJar `relocate` 目标包名、Maven `group`
- **物理目录**：`moze_intel/projecte/` → 随机包路径、`assets/projecte/` → 随机 MODID

### 随机名称持久化

混淆名称生成后保存在 `.obfuscated/.obf_seed`。后续构建复用相同种子，确保产物一致。运行 `task clean-obf` 清除种子后，下次生成全新随机名称。

## 验证混淆结果

用 JD-GUI 或任意反编译器打开 `build/libs/ProjectE-*-universal.jar`：

- Java 类应位于随机包名路径下
- `mcmod.info` 中 `modid` / `name` 应为随机值
- `assets/` 下应是随机 MODID 目录名
- shadow 重定向的 `org.apache.commons.math3` 应位于随机包名下

用 `/give` 等原版命令给物品时应使用新的 MODID：
```
/give @p <新MODID>:<物品名>
```

## 注意

- `Original_Src/` 被 `.gitignore` 排除，不会被提交到 Git
- `task setup` 只需执行一次，除非删除了 `Original_Src/`
- 如果 `Original_Src/` 不存在，构建会直接报错并提示先执行 `task setup`
- `src/` 在构建过程中会被临时覆盖，构建后自动还原

---

基于 [sinkillerj/ProjectE](https://github.com/sinkillerj/ProjectE) mc1.12.x 分支，原始 README 见上游仓库。
