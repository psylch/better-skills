# better-skills

[English](README.md)

一个面向 AI 编程 agent 的技能开发工具包 — 创建、走查和发布技能，内置运行时 UX 最佳实践。

## 技能列表

| 技能 | 用途 | 状态 |
|------|------|------|
| [**skill-creator**](skills/skill-creator/) | 从最佳实践模板创建新技能 | 可用 |
| [**skill-review**](skills/skill-review/) | 验证结构、建议改进并修复问题 | 可用 |
| [**skill-publish**](skills/skill-publish/) | 包装并发布技能 | 可用 |

## 安装

### 通过 skills.sh（推荐）

```bash
npx skills add psylch/better-skills -g -y
```

### 手动安装

```bash
git clone https://github.com/psylch/better-skills.git ~/.claude/skills/better-skills
```

安装后需重启 agent。

## 前置条件

- 任何支持 [skills.sh](https://skills.sh/) 的 AI 编程 agent（Claude Code、Cursor、Windsurf 等）
- **Python 3.11+**（脚手架脚本使用，stdlib-only 无外部依赖）

## 包含内容

### skill-creator

通过对话引导创建新技能 — 名称、层级（L0/L0+/L1）、环境策略（stdlib/uv/venv）、输出目录。生成的模板内置 preflight 框架、JSON 输出约定和错误处理。

### skill-review

结合自动化验证（7 类 22+ 项检查，A–F 评级）与基于最佳实践的分析建议。输出统一报告：评级、问题列表、按优先级排序的改进建议（附 before/after 示例），支持交互式修复。

### skill-publish

将技能打包为完整的 GitHub 仓库：生成 README（中英文）、LICENSE、plugin.json、marketplace.json、.gitignore。可选初始化 git 并创建 GitHub 仓库。

### 技能层级

**L0** — SKILL.md 就是整个技能。适合工作流指南和领域知识。

**L0+** — SKILL.md 加上轻量辅助脚本，用于环境检测和状态缓存。

**L1** — 脚本承载核心业务逻辑，SKILL.md 负责编排。脚本遵循 MCP 工具设计原则。

## 项目结构

```
better-skills/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── skills/
│   ├── skill-creator/        # L1: scaffold.py + 模板
│   ├── skill-review/         # L1: validate.py + analyze.sh
│   └── skill-publish/        # L1: publish.py + 模板
├── README.md
├── README.zh.md
└── LICENSE
```

## 许可证

MIT
