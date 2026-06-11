# Taskfile 开发工作流

本项目使用 [Taskfile](https://taskfile.dev/) 管理开发任务，通过 `Taskfile.yml` 编排构建流程。所有任务默认使用 Java 8 编译，避免修改系统全局环境变量。

## 首次使用

```bash
task setup     # 创建 Original_Src/，保存原始源码（只需执行一次）
```

执行后项目目录结构：

```
ProjectE/
├── src/                 ← 工作目录，会被临时覆盖
├── Original_Src/        ← 原始源码永久备份（gitignored，只读）
├── .obfuscated/         ← 混淆后的源码（gitignored，可复用）
├── Taskfile.yml         ← 任务编排
├── obfuscate.py         ← 混淆脚本
└── build.gradle
```

## 可用任务

| 任务 | 说明 |
|------|------|
| `task setup` | **首次使用执行一次**，创建 `Original_Src/` 保存原始源码 |
| `task build` | 普通构建（从 `Original_Src/` 还原后构建） |
| `task build-obf` | 一键混淆构建（生成混淆源码 → 部署 → 构建 → 还原） |
| `task obfuscate` | 仅生成 `.obfuscated/`，不构建 |
| `task clean-obf` | 删除 `.obfuscated/` 缓存，下次生成全新的随机名称 |
| `task jar` | 仅打 jar 包，跳过测试 |
| `task clean` | 清理构建产物 (`build/`) |
| `task test` | 仅运行测试 |

## 混淆构建原理 (`task build-obf`)

目的是对 MODID、MODNAME 和 Java 包名进行随机化，防止其他模组通过固定标识符检测本模组的物品和行为。

### 数据流

```
首次: task setup  →  cp -a src Original_Src/     (永久保存，从不动它)
                       cp build.gradle → Original_Src/

之后每次 build-obf:

  Original_Src/ (只读源码)  +  build.gradle (原始)
          │
          │  obfuscate.py 读取并生成
          ▼
     .obfuscated/ (混淆副本)
          │
          │  rm -rf src && cp -a .obfuscated src   (部署)
          │  cp src/build.gradle build.gradle        (替换构建脚本)
          ▼
       src/ (混淆版)  →  ./gradlew build  →  universal.jar
          │
          │  trap EXIT: rm -rf src
          │             cp -a Original_Src src      (还原源码)
          │             git checkout build.gradle    (还原构建脚本)
          ▼
       src/ (已还原)
```

### 混淆的三项内容

| 项目 | 原始值 | 混淆后 |
|------|--------|--------|
| MODID | `projecte` | 随机 8-12 位小写字母数字 |
| MODNAME | `ProjectE` | 随机 8-12 位混合大小写 |
| 包名 | `moze_intel.projecte` | 两段随机目录名，如 `abc123.xyz789` |
| Maven group | `moze_intel` | 与包名第一段一致 |

### build-obf 执行步骤

1. **`task obfuscate`** — 运行 `obfuscate.py`，从 `Original_Src/` 复制到 `.obfuscated/`，替换所有标识符字符串并重命名目录结构
2. **部署混淆副本** — `rm -rf src && cp -a .obfuscated src`，将混淆后的 `build.gradle` 复制到项目根目录
3. **Gradle 构建** — `./gradlew build`
4. **自动还原** — 通过 bash `trap EXIT` 确保无论构建成功或失败，都从 `Original_Src/` 还原 `src/`，用 `git checkout` 还原 `build.gradle`

不同于之前的实现，这里**没有备份步骤**——`Original_Src/` 是永久存在的只读副本，还原时直接从它 `cp` 即可，省去每次构建前的 `cp -a src src.bak` 操作。

### obfuscate.py 的替换范围

- **Java 源文件** (346 个): 包声明、import 语句、硬编码的 `"projecte"` / `"ProjectE"` 字符串、`@SidedProxy` 等注解中的全限定类名
- **资源文件** (319 个):
  - JSON 模型/配方: `projecte:` → 随机 MODID 前缀
  - lang 翻译键: `itemGroup.projecte` → `itemGroup.{随机ID}`
  - 路径: `assets/projecte/` → `assets/{随机ID}/`
  - 命令引用: `/projecte ` → `/{随机ID} `
  - mcmod.info: `"projecte"` / `"ProjectE"` → 随机值
  - `_factories.json` 中的全限定工厂类名
- **build.gradle**: shadowJar 的 `relocate` 目标包名、Maven `group`
- **物理目录重命名**:
  - `moze_intel/projecte/` → 随机包路径
  - `assets/projecte/` → 随机 MODID
  - 自动清理空父目录

### 随机名称持久化

混淆名称生成后在 `.obfuscated/.obf_seed` 中保存种子。后续运行 `task build-obf` 会复用相同的随机名称，确保多次构建产物一致。运行 `task clean-obf` 清除种子后，下次会生成全新的随机名称。

如果只想更换名称而不重新构建，可以 `task clean-obf && task obfuscate` 仅重新生成 `.obfuscated/`，然后 `task build-obf` 构建。
