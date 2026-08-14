<p align="center">
  <img src="docs/assets/banner.svg" alt="Repository-State Agent Workflow" width="100%" />
</p>

<h1 align="center">Repository-State Agent Workflow</h1>

<p align="center">
  <strong>持久工作流、快取感知的 context、可即時觀測的執行。</strong>
</p>

<p align="center">
  RSAW 將長期專案記憶保存在 repository，明確規劃最小 context，僅在快取與
  任務關聯仍有價值時沿用 Codex thread，於真正邊界自動 ROTATE，並在 VS Code
  Integrated Terminal 中提供清楚的即時 Runtime Console。
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.5.0-7c3aed" alt="Version 0.5.0" />
  <img src="https://img.shields.io/badge/python-3.10%2B-2563eb" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/context-cache_aware-0891b2" alt="Cache-aware context" />
  <img src="https://img.shields.io/badge/UI-live_terminal-0f766e" alt="Live terminal UI" />
</p>

---

## RSAW 是什麼

RSAW 是供長時間 coding / research agent 使用的 **repository-first operating
model 與 runtime supervisor**。

- repository 保存 durable memory；
- context epoch 是有上限、可替換的 worker；
- 每個 checkpoint 經驗證後，只會得到四種 action：
  `CONTINUE / ROTATE / PAUSE / COMPLETE`。

0.5 版在 0.4 Live Runtime Console 上增加兩個核心能力：

1. **Cache-aware Context Planner**：穩定 prefix 與動態 authority 分離；
2. **Deterministic Rotation Policy**：同時考慮 turn、hard/soft input、fresh input
   與 cache reuse，不交由模型自行決定 context 壽命。

<p align="center">
  <img src="docs/assets/runtime-architecture-v05.svg" alt="RSAW 0.5 架構" width="100%" />
</p>

> **Workstream 持續存在；context 被規劃、量測並可安全替換。**

---

## 快速開始

```bash
python -m pip install   git+https://github.com/hanklin9188/repository-state-agent-workflow.git

cd /path/to/project
rsaw init .
rsaw verify .
rsaw context .
rsaw doctor . --agent codex
rsaw preview . --seconds 6
rsaw run . --agent codex
```

嚴格檢查 bootstrap budget：

```bash
rsaw context . --strict
```

需要原始 log：

```bash
rsaw run . --agent codex --no-tui
```

---

## Context Planner

`rsaw context .` 會產生可重現的 context manifest：

```text
Stable prefix
  AGENTS.md

Dynamic authority
  ACTIVE.md
  active task
  bounded required reads
```

每個檔案都有 path、category、bytes、約略 tokens 與 SHA-256。CONTINUE 只需重新
讀動態 authority；stable fingerprint 未變時，不應重讀 stable prefix。ROTATE
才重新建立完整但最小的 bootstrap。

<p align="center">
  <img src="docs/assets/context-lifecycle.svg" alt="Context lifecycle" width="100%" />
</p>

預設設定：

```json
{
  "runtime": {
    "context": {
      "bootstrap_token_budget": 15000,
      "max_files": 12,
      "max_file_bytes": 262144,
      "include_workstream_spec": false,
      "enforce_budget": false
    }
  }
}
```

---

## Rotation Policy

RSAW 會先遵守角色、審查與科學邊界，再依照 deterministic policy 評估：

```text
MAX_TURNS_PER_RUNTIME_EPOCH
HARD_INPUT_TOKEN_PRESSURE
FRESH_INPUT_TOKEN_PRESSURE
LOW_CACHE_REUSE_AT_SOFT_LIMIT
```

```json
{
  "runtime": {
    "rotation": {
      "soft_input_tokens": 48000,
      "hard_input_tokens": 60000,
      "max_fresh_input_tokens": 18000,
      "min_cache_reuse_ratio": 0.5
    }
  }
}
```

目標不是讓 cached token 越多越好，而是：

```text
有用的 cache reuse
+ 更少 stale context
+ ROTATE 後的小型 fresh bootstrap
+ 每個成功 checkpoint 更低的 fresh-input cost
```

---

## Live Runtime Console

<p align="center">
  <img src="docs/assets/live-terminal-dashboard.svg" alt="RSAW Live Runtime Console" width="100%" />
</p>

在 VS Code Terminal 直接顯示：

- **NOW**：Codex 現在讀檔、改檔、執行 command 或驗證；
- **PROGRESS**：workstream、task、role、epoch、checkpoint、下一個 action；
- **CONTEXT**：soft/hard pressure、cached、fresh input；
- **RECENT**：重要事件，不洗版 raw JSON；
- **GATE**：是否需要人工介入。

TUI 是本機 presentation layer，不會把 dashboard 文字放進 prompt，也不會新增
model turn。真正的 context/token 效率來自 repository state、bounded epoch、
CONTINUE、ROTATE 與 progressive disclosure。

---

## 指標

```text
fresh input = max(0, input - cached input)
cache reuse ratio = cached input / input
input per checkpoint = total input / accepted checkpoints
fresh input per checkpoint = fresh input / accepted checkpoints
```

```bash
rsaw report .
rsaw report . --json
```

---

## 安全邊界

- 每個 supervised turn 前後都驗證 repository；
- 成功 turn 必須推進 `ACTIVE.md`；
- single-supervisor lock 防止兩個 writer；
- human gate 不推測授權；
- 失敗的正式執行不自動重試；
- role / scientific boundary 必須 fresh；
- context planner 與 TUI 都不能改變 lifecycle authority。

---

## 證據與限制

目前有 cross-version CI、context-plan / rotation-policy unit tests、runtime/TUI
測試與歷史 case study。以下仍不可過度宣稱：

- chars/4 是估算，不是 provider billing；
- TUI 本身不省 token；
- deterministic default 不等於所有專案的最佳參數；
- universal token / quality improvement 仍需 matched prospective study。

---

## 文件

- [Architecture](docs/architecture.md)
- [Context Planning](docs/context-planning.md)
- [Cache-Aware Rotation](docs/cache-aware-rotation.md)
- [Token-Efficient Runtime](docs/token-efficient-runtime.md)
- [Live Terminal UI](docs/live-terminal-ui.md)
- [Migration 0.4 → 0.5](docs/migration-v4-to-v5.md)
- [Runtime Evaluation](docs/runtime-evaluation.md)

RSAW 採 MIT License。Markdown 與 Git 仍是 durable authority；runtime、planner
與 console 都是可替換的執行層。
