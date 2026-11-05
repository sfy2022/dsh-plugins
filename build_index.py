#!/usr/bin/env python3
"""Rebuild sfy2022/dsh-plugins' index.json + README from the plugins actually
installed in this DSH profile.

Source of truth:
  * installed package names  <- $DSH_HOME/profiles/web/package.json (dependencies)
  * installed versions       <- <profile>/node_modules/<pkg>/package.json
  * version history / repo   <- npm registry packument (cached in .npm-cache/)

Output: index.json (format 1, see @deepseek-ai/dsh-plugin-market-index) + README.md
"""

import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

DSH_HOME = os.environ.get("DSH_HOME", "/vol1/@apphome/fn-deepseek-harness")
PROFILE = os.path.join(DSH_HOME, "profiles", "web")
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, ".npm-cache")
REGISTRY = "https://registry.npmjs.org"

# ---------------------------------------------------------------- metadata ---
# zh/en descriptions + category are curated by hand; everything else comes from
# the installed package and npm.
CURATED = {
    "dsh-design-studio": (
        "ui",
        "右侧设计工作台：一句话出几个方向的网页 / App 界面 / 海报 / 幻灯片，"
        "点元素回传对话，调设计变量、对比版本",
        "Design workbench in the right sidebar: generated web / app / poster / "
        "slide screens on a canvas, click an element to send it back to the chat.",
    ),
    "dsh-guizang-design": (
        "ui",
        "歸藏设计：网页 PPT、图文卡片、网页排版、去 AI 味四个 skill 加语气档案，"
        "共用一套设计系统，带作品库，一键做同款",
        "Guizang design plugin: web PPT, social cards, page layout and humanizer "
        "skills sharing one design system, plus a works library and voice profile.",
    ),
    "dsh-media-desk": (
        "ui",
        "自媒体工作台：一句话记灵感，一键生成口播脚本、标题、封面、配图和分镜；"
        "稿子拖到日历排期，发完回来复盘",
        "Media desk: capture an idea in one line, generate script, titles, cover, "
        "images and storyboard, schedule posts and review the results.",
    ),
    "dshmarket": (
        "ui",
        "可视化插件市场：在 DSH 里逛、搜、一键装社区插件，也能更新和卸载",
        "Visual plugin market inside DSH: browse, search and one-click install "
        "community plugins, with update and uninstall.",
    ),
    "dsh-prompt-chain": (
        "prompt",
        "提示词链式增强：继续生成 / 重新生成 / 历史回退 / 差异逐行对比，结果回填输入框",
        "Prompt chain enhancer: continue, regenerate, roll back through history and "
        "diff line by line; the result goes back into the input box.",
    ),
    "@tnnevol/dsh-failover-search": (
        "search",
        "网页搜索与抓取的多来源故障转移：TinyFish → Tavily → 官方搜索依次兜底，"
        "同平台多账号轮转分摊，带用量展示",
        "Composite web-search and fetch provider that fails over TinyFish → Tavily → "
        "official DeepSeek and spreads requests across accounts.",
    ),
    "@tnnevol/dsh-codex-auth": (
        "model",
        "ChatGPT / Codex 登录与账号管理：浏览器授权登录、默认模型与思考强度，"
        "输入框旁看用量和剩余额度",
        "Standalone ChatGPT / Codex OAuth account management: browser login, default "
        "model and reasoning effort, usage and quota next to the input.",
    ),
    "ds-bot": (
        "tools",
        "常驻 Bot 团队：主 Bot、Bot 之间互发消息、群聊、团队记忆、权限预设和用量统计",
        "DS Bot: a team of long-lived Bots with Main Bots, Bot-to-Bot messages, "
        "group chats, memory, permission presets and usage stats.",
    ),
    "agentero-dsh": (
        "tools",
        "Agentero 科研工作台：文献库、笔记、PDF 阅读器搬进 DSH，右侧读论文、"
        "中间对话，资料全留在本地",
        "Agentero research workbench: local-first literature library, notes and PDF "
        "reader inside DSH, so the Agent can query your own papers.",
    ),
    "dsh-context": (
        "tools",
        "上下文洞察与管理：跨会话用量看板、上下文组成与趋势、/context 命令、"
        "多 Agent 舰队视图",
        "Context insight and management: cross-session usage dashboard, context "
        "composition and trends, /context command and a multi-agent fleet view.",
    ),
    "@tnnevol/dsh-fnos": (
        "tools",
        "fnOS 系统集成：主题跟随、授权目录管理、在 fnOS 应用里打开文件、"
        "把窗口标题同步给 fnOS",
        "fnOS-specific integrations: follow the NAS theme, manage authorized "
        "directories, open files in fnOS apps and sync the window title.",
    ),
}

# Plugins installed from a local directory (link:) cannot be expressed as a
# format-1 version source, so they are documented in the README only.
LOCAL_ONLY_NOTE = {
    "dsh-fnos-cli": "让 Agent 直接调用 fnOS CLI：文件、相册、应用中心、Docker、存储、网络、监控和用户",
}

CATEGORIES = {
    "ui": ("界面与画布", "UI & Canvas"),
    "prompt": ("提示词", "Prompt"),
    "search": ("检索与联网", "Search & Web"),
    "model": ("模型与账号", "Models & Accounts"),
    "tools": ("工具与能力", "Tools"),
    "other": ("其他", "Other"),
}

LABELS = {"using": ("在用的", "In use")}
CATEGORY_ORDER = ["ui", "prompt", "search", "model", "tools", "other"]

VERSION_HISTORY_LIMIT = 60  # per plugin; newest first


def installed_plugins():
    """[(name, installed_version, dep_range)] from the running profile."""
    pkg = json.load(open(os.path.join(PROFILE, "package.json"), encoding="utf-8"))
    out = []
    for name, spec in pkg.get("dependencies", {}).items():
        pkgjson = os.path.join(PROFILE, "node_modules", name, "package.json")
        if not os.path.isfile(pkgjson):
            print(f"warn: {name} is declared but not installed", file=sys.stderr)
            continue
        version = json.load(open(pkgjson, encoding="utf-8")).get("version")
        out.append((name, version, spec))
    return out


def packument(name):
    os.makedirs(CACHE, exist_ok=True)
    fname = os.path.join(CACHE, name.replace("/", "%2f") + ".json")
    if os.path.isfile(fname) and os.path.getsize(fname) > 0:
        return json.load(open(fname, encoding="utf-8"))
    url = f"{REGISTRY}/{urllib.parse.quote(name, safe='@')}"
    with urllib.request.urlopen(url, timeout=60) as resp:
        raw = resp.read()
    open(fname, "wb").write(raw)
    return json.loads(raw)


def clean_repo_url(repo):
    if isinstance(repo, dict):
        url = repo.get("url") or ""
        directory = repo.get("directory")
    else:
        url = repo or ""
        directory = None
    url = url.strip()
    url = re.sub(r"^git\+", "", url)
    url = re.sub(r"^git://", "https://", url)
    if url.endswith(".git"):
        url = url[:-4]
    url = url.rstrip("/")
    return url, directory


def clean_http_url(url):
    if not url:
        return None
    url = url.split("#", 1)[0].strip()
    if not re.match(r"^https?://", url):
        return None
    return url


def iso_to_epoch(text):
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def clean_engines(engines):
    # keep only a plausible dsh range; the node check below is authoritative
    dsh = (engines or {}).get("dsh")
    if not isinstance(dsh, str) or not dsh.strip() or "workspace:" in dsh:
        return {}
    return {"dsh": dsh.strip()}


def version_entries(name, doc, want_upto):
    times = doc.get("time", {})
    versions = doc.get("versions", {})
    rows = []
    for ver, meta in versions.items():
        ts = iso_to_epoch(times.get(ver, ""))
        if ts is None:
            continue
        rows.append((ver, ts, clean_engines(meta.get("engines"))))
    rows.sort(key=lambda r: r[1], reverse=True)
    # keep the newest VERSION_HISTORY_LIMIT entries, always including want_upto
    keep = rows[:VERSION_HISTORY_LIMIT]
    if want_upto and all(r[0] != want_upto for r in keep):
        for r in rows:
            if r[0] == want_upto:
                keep.append(r)
                break
    return [
        {
            "version": ver,
            "publishTimestamp": ts,
            "source": {"type": "npm"},
            "engines": engines,
        }
        for ver, ts, engines in keep
    ]


def build_plugin(name, installed_version, doc):
    if name not in CURATED:
        raise SystemExit(f"no curated description for {name}; add it to CURATED")
    category, zh, en = CURATED[name]
    latest = (doc.get("dist-tags") or {}).get("latest")
    repo_url, repo_dir = clean_repo_url(doc.get("repository"))
    entry = {
        "name": name,
        "description": {"zh": zh, "en": en},
    }
    author = doc.get("author")
    if isinstance(author, dict):
        author = author.get("name")
    if author:
        entry["author"] = author
    homepage = clean_http_url(doc.get("homepage"))
    if homepage:
        entry["homepage"] = homepage
    if repo_url:
        entry["repository"] = {"url": repo_url}
        if repo_dir:
            entry["repository"]["directory"] = repo_dir
    keywords = [k for k in (doc.get("keywords") or []) if isinstance(k, str)][:8]
    entry["metadata"] = {
        "labels": ["using"],
        "keywords": keywords,
        "category": category,
        "sortKeys": {},
    }
    entry["versions"] = version_entries(name, doc, installed_version)
    return entry, latest


def main():
    plugins = installed_plugins()
    entries = []
    missing = []
    local = []
    latest_versions = {}
    for name, version, spec in plugins:
        if spec.startswith("link:") or spec.startswith("file:"):
            local.append((name, version, spec))
            continue
        try:
            doc = packument(name)
        except Exception as exc:  # noqa: BLE001
            print(f"warn: cannot fetch {name}: {exc}", file=sys.stderr)
            missing.append(name)
            continue
        entry, latest = build_plugin(name, version, doc)
        entries.append(entry)
        latest_versions[name] = latest

    cat_index = {c: i for i, c in enumerate(CATEGORY_ORDER)}
    entries.sort(key=lambda e: (cat_index.get(e["metadata"]["category"], 99), e["name"]))

    index = {
        "format": 1,
        "title": "大嘴哥的 DSH 插件短名单",
        "description": "我自己装、自己在用的 DSH 插件。装插件不用再翻几千条目录。",
        "metadata": {
            "categories": {
                cid: {"title": {"zh": zh, "en": en}} for cid, (zh, en) in CATEGORIES.items()
            },
            "labels": {
                lid: {"title": {"zh": zh, "en": en}} for lid, (zh, en) in LABELS.items()
            },
            "sortKeys": {},
        },
        "plugins": entries,
    }
    out_index = os.path.join(HERE, "index.json")
    with open(out_index, "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    # ------------------------------------------------------------- README ---
    installed = {name: version for name, version, _ in plugins}
    by_cat = {}
    for entry in entries:
        by_cat.setdefault(entry["metadata"]["category"], []).append(entry)

    lines = []
    lines.append("# 大嘴哥的 DSH 插件短名单\n")
    lines.append(
        "这台机器上**真正装着在用**的 DSH 插件。不是从几千条目录里抄的清单——"
        "每一个都是我自己装了、留在 profile 里的；哪天卸了，这里就跟着删。\n"
    )
    lines.append(
        "可以直接当作 DSH 的索引源用：**插件 → 发现 → 索引源**，填\n"
        "`https://raw.githubusercontent.com/sfy2022/dsh-plugins/main/index.json`，"
        "按名称搜、一键装。\n"
    )
    total = len(entries)
    lines.append(f"## 当前收录（{total} 个）\n")
    for cid in CATEGORY_ORDER:
        group = by_cat.get(cid, [])
        if not group:
            continue
        zh, en = CATEGORIES[cid]
        lines.append(f"### {zh} · {en}\n")
        lines.append("| 插件 | 装的版本 | 一句话 | 仓库 |")
        lines.append("|---|---|---|---|")
        for entry in group:
            name = entry["name"]
            ver = installed.get(name, "?")
            desc = entry["description"]["zh"]
            repo = (entry.get("repository") or {}).get("url", "")
            repo_cell = f"[{repo.split('github.com/')[-1]}]({repo})" if repo else "—"
            lines.append(f"| `{name}` | {ver} | {desc} | {repo_cell} |")
        lines.append("")

    if local:
        lines.append("### 本地插件（不进索引）\n")
        for name, version, spec in local:
            note = LOCAL_ONLY_NOTE.get(name, "")
            lines.append(
                f"- `{name}` {version} — {note}。本地 `link:` 安装（指向 workspace "
                "里的源码目录），没有发布到 npm，所以不在 index.json 里。"
            )
        lines.append("")

    updates = [
        (name, installed.get(name), latest_versions[name])
        for name in installed
        if name in latest_versions
        and latest_versions[name]
        and installed.get(name) != latest_versions[name]
    ]
    lines.append("## 更新提示\n")
    if updates:
        lines.append("下面这些有新版本（记录的是这台机器当前装的版本）：\n")
        lines.append("| 插件 | 当前 | 最新 |")
        lines.append("|---|---|---|")
        for name, cur, latest in sorted(updates):
            lines.append(f"| `{name}` | {cur} | {latest} |")
        lines.append("")
        lines.append("升级命令（以 web profile 为例）：\n")
        lines.append("```sh")
        lines.append("dsh plugin --profile web add <包名>@latest")
        lines.append("```\n")
    else:
        lines.append("全部已是最新。\n")

    lines.append("## 按包名装\n")
    lines.append("```sh")
    lines.append("dsh plugin --profile web add dsh-design-studio     # 任意一个包名")
    lines.append("```\n")
    lines.append(
        "或者在 DSH 里 **插件 → 添加插件** 填包名；装完重启 Web profile 生效。\n"
    )
    lines.append("## 数据\n")
    lines.append(
        "- [`index.json`](./index.json) 是 [plugin market index format 1]"
        "(https://github.com/deepseek-ai/deepseek-harness) 格式：`format: 1`，"
        "每个插件带分类、中英双语描述、仓库地址和按时间倒序的版本历史。\n"
        "- 版本历史取自 npm registry，最多保留每个插件最近 "
        f"{VERSION_HISTORY_LIMIT} 个版本。\n"
        "- 这份名单是脚本从已装环境生成的，`build_index.py` 一起放在仓库里，"
        "换机器或装完新插件重跑一次即可。\n"
    )
    out_readme = os.path.join(HERE, "README.md")
    open(out_readme, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    print(f"index.json: {total} plugins, {os.path.getsize(out_index)} bytes")
    print(f"README.md: {os.path.getsize(out_readme)} bytes")
    if local:
        print("local-only:", ", ".join(n for n, _, _ in local))
    if missing:
        print("unresolved:", ", ".join(missing))
    if updates:
        print("updates:", ", ".join(f"{n} {c}->{l}" for n, c, l in sorted(updates)))


if __name__ == "__main__":
    main()
