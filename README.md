# 大嘴哥的 DSH 插件短名单

这台机器上**真正装着在用**的 DSH 插件。不是从几千条目录里抄的清单——每一个都是我自己装了、留在 profile 里的；哪天卸了，这里就跟着删。

可以直接当作 DSH 的索引源用：**插件 → 发现 → 索引源**，填
`https://raw.githubusercontent.com/sfy2022/dsh-plugins/main/index.json`，按名称搜、一键装。

## 当前收录（11 个）

### 界面与画布 · UI & Canvas

| 插件 | 装的版本 | 一句话 | 仓库 |
|---|---|---|---|
| `dsh-design-studio` | 0.7.1 | 右侧设计工作台：一句话出几个方向的网页 / App 界面 / 海报 / 幻灯片，点元素回传对话，调设计变量、对比版本 | [OrderG-X/dsh-design-studio](https://github.com/OrderG-X/dsh-design-studio) |
| `dsh-guizang-design` | 0.1.3 | 歸藏设计：网页 PPT、图文卡片、网页排版、去 AI 味四个 skill 加语气档案，共用一套设计系统，带作品库，一键做同款 | [op7418/dsh-guizang-design](https://github.com/op7418/dsh-guizang-design) |
| `dsh-media-desk` | 2.5.3 | 自媒体工作台：一句话记灵感，一键生成口播脚本、标题、封面、配图和分镜；稿子拖到日历排期，发完回来复盘 | [woniuniuniu/dsh-media-desk](https://github.com/woniuniuniu/dsh-media-desk) |
| `dshmarket` | 1.66.47 | 可视化插件市场：在 DSH 里逛、搜、一键装社区插件，也能更新和卸载 | [dsh-market/dsh-market](https://github.com/dsh-market/dsh-market) |

### 提示词 · Prompt

| 插件 | 装的版本 | 一句话 | 仓库 |
|---|---|---|---|
| `dsh-prompt-chain` | 1.1.1 | 提示词链式增强：继续生成 / 重新生成 / 历史回退 / 差异逐行对比，结果回填输入框 | [Nihao7-L/dsh-prompt-chain](https://github.com/Nihao7-L/dsh-prompt-chain) |

### 检索与联网 · Search & Web

| 插件 | 装的版本 | 一句话 | 仓库 |
|---|---|---|---|
| `@tnnevol/dsh-failover-search` | 7.0.1 | 网页搜索与抓取的多来源故障转移：TinyFish → Tavily → 官方搜索依次兜底，同平台多账号轮转分摊，带用量展示 | [FNOSP/fnos-dsh](https://github.com/FNOSP/fnos-dsh) |

### 模型与账号 · Models & Accounts

| 插件 | 装的版本 | 一句话 | 仓库 |
|---|---|---|---|
| `@tnnevol/dsh-codex-auth` | 7.0.1 | ChatGPT / Codex 登录与账号管理：浏览器授权登录、默认模型与思考强度，输入框旁看用量和剩余额度 | [FNOSP/fnos-dsh](https://github.com/FNOSP/fnos-dsh) |

### 工具与能力 · Tools

| 插件 | 装的版本 | 一句话 | 仓库 |
|---|---|---|---|
| `@tnnevol/dsh-fnos` | 7.0.1 | fnOS 系统集成：主题跟随、授权目录管理、在 fnOS 应用里打开文件、把窗口标题同步给 fnOS | [FNOSP/fnos-dsh](https://github.com/FNOSP/fnos-dsh) |
| `agentero-dsh` | 0.1.4 | Agentero 科研工作台：文献库、笔记、PDF 阅读器搬进 DSH，右侧读论文、中间对话，资料全留在本地 | [poco-ai/agentero-dsh-plugin](https://github.com/poco-ai/agentero-dsh-plugin) |
| `ds-bot` | 0.2.7 | 常驻 Bot 团队：主 Bot、Bot 之间互发消息、群聊、团队记忆、权限预设和用量统计 | [Fei2411/DS-Bot](https://github.com/Fei2411/DS-Bot) |
| `dsh-context` | 0.81.0 | 上下文洞察与管理：跨会话用量看板、上下文组成与趋势、/context 命令、多 Agent 舰队视图 | [bowenliang123/dsh-context](https://github.com/bowenliang123/dsh-context) |

### 本地插件（不进索引）

- `dsh-fnos-cli` 0.1.0 — 让 Agent 直接调用 fnOS CLI：文件、相册、应用中心、Docker、存储、网络、监控和用户。本地 `link:` 安装（指向 workspace 里的源码目录），没有发布到 npm，所以不在 index.json 里。

## 更新提示

下面这些有新版本（记录的是这台机器当前装的版本）：

| 插件 | 当前 | 最新 |
|---|---|---|
| `@tnnevol/dsh-codex-auth` | 7.0.1 | 7.0.16 |
| `@tnnevol/dsh-failover-search` | 7.0.1 | 7.0.16 |
| `@tnnevol/dsh-fnos` | 7.0.1 | 7.0.16 |
| `agentero-dsh` | 0.1.4 | 0.1.6 |
| `dsh-context` | 0.81.0 | 0.82.0 |
| `dsh-design-studio` | 0.7.1 | 0.9.0 |
| `dsh-guizang-design` | 0.1.3 | 0.1.4 |
| `dsh-media-desk` | 2.5.3 | 2.6.1 |
| `dshmarket` | 1.66.47 | 1.73.11 |

升级命令（以 web profile 为例）：

```sh
dsh plugin --profile web add <包名>@latest
```

## 按包名装

```sh
dsh plugin --profile web add dsh-design-studio     # 任意一个包名
```

或者在 DSH 里 **插件 → 添加插件** 填包名；装完重启 Web profile 生效。

## 数据

- [`index.json`](./index.json) 是 [plugin market index format 1](https://github.com/deepseek-ai/deepseek-harness) 格式：`format: 1`，每个插件带分类、中英双语描述、仓库地址和按时间倒序的版本历史。
- 版本历史取自 npm registry，最多保留每个插件最近 60 个版本。
- 这份名单是脚本从已装环境生成的，`build_index.py` 一起放在仓库里，换机器或装完新插件重跑一次即可。

