<p align="center">
  <img src="docs/assets/banner-v08.svg" alt="RSAW v0.8 — Relevance-First Context Runtime" width="100%" />
</p>

<h1 align="center">Repository-State Agent Workflow</h1>

<p align="center">
  <strong>把真相留在 repository，只把重要內容送進模型，並安全封存每個進度。</strong>
</p>

<p align="center">
  <img alt="Python 3.10–3.13" src="https://img.shields.io/badge/Python-3.10%E2%80%933.13-3776AB?logo=python&logoColor=white" />
  <img alt="RSAW 0.8.0" src="https://img.shields.io/badge/RSAW-0.8.0-14b8a6" />
  <img alt="Tests 121" src="https://img.shields.io/badge/Tests-121%20passing-22c55e" />
  <img alt="License MIT" src="https://img.shields.io/badge/License-MIT-64748b" />
  <img alt="Codex adapter" src="https://img.shields.io/badge/Adapter-Codex-6366f1" />
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="docs/relevance-first-context.md">設計</a> ·
  <a href="docs/edgeflow-v080-deployment.md">EdgeFlow 部署</a> ·
  <a href="docs/releases/v080-relevance-first-context.md">版本說明</a> ·
  <a href="CHANGELOG.md">Changelog</a>
</p>

---

## RSAW 是什麼？

RSAW 是一套為長時間 coding 與 research agent 設計的 repository-backed runtime。
Codex 仍負責真正的語意工程工作；RSAW 管理不應依賴模型記憶的部分：

- 精確的 task 與 repository authority；
- relevance-first working context；
- checksummed checkpoints 與 evidence；
- `CONTINUE / COMPACT / ROTATE / PAUSE / COMPLETE`；
- Human Gate 與 task-scoped sandbox；
- tool、output 與 provider-context budgets；
- 中斷或 transition 被拒絕後的復原。

整體只需要理解四步：

```text
Truth → Focus → Work → Checkpoint
```

> **模型可以忘記；repository 不可以。**

---

## 60 秒開始使用

### 安裝

```bash
python -m pip install --upgrade \
  "git+https://github.com/hanklin9188/repository-state-agent-workflow.git@v0.8.0"
```

### 已使用 RSAW 的 repository

```bash
rsaw upgrade . --apply
rsaw preflight .
rsaw start .
```

### 新 repository

```bash
rsaw init .
rsaw preflight .
rsaw start .
```

日常只需要：

```bash
rsaw start .
```

啟動模型前想先看 RSAW 選了哪些程式碼：

```bash
rsaw focus .
rsaw focus . --show-content
```

---

## 為什麼需要 v0.8？

初始 prompt 很小，不代表整個 agent session 會很省。Worker 仍可能全 repo 搜尋、讀取大量檔案、累積巨大 tool output，並在每一次 model call 重送越來越長的 transcript。這些流量常被列成 cached input，但 context 本身仍然過大。

v0.8 把主要優化移到 model turn **之前**：

| 舊方法 | v0.8 方法 |
|---|---|
| 告訴 Agent 不要亂找 | 先準備好相關 working set |
| tool 已膨脹後才踩煞車 | 先降低 discovery loop 的需求 |
| 把 cache 命中當成效率 | 分開衡量 total / cached / fresh input |
| 壓縮或摘要整個 repository | 多取候選，只送少量 exact excerpts |
| 再用一個 LLM 做摘要 | 使用 deterministic checkpoint 與 Semantic Capsule |

Live budgets 仍保留，但它是最後一道煞車，不是主要 retrieval 方法。

---

## Relevance-First Context

<p align="center">
  <img src="docs/assets/relevance-first-v08.svg" alt="RSAW v0.8 relevance-first context architecture" width="96%" />
</p>

### Truth

`ACTIVE.md`、active task contract、stable governance、bounded Semantic Capsule 與必要 evidence handles 維持精確且具 authority。

### Focus

每個 fresh model context 前，RSAW 會建立本機 content-addressed index，並用可以解釋的訊號選出小型 working set：

- task 明確提到的 exact paths；
- symbols 與 file names；
- current Git changes；
- rejecting / regression tests；
- direct imports 與附近 dependencies；
- task vocabulary 與 source ranges。

預設 budget：

```json
{
  "mapTokens": 900,
  "focusTokens": 3000,
  "maxSnippets": 5,
  "candidateLimit": 20,
  "snippetLines": 64
}
```

Index 使用 SHA-256 content identity；檔案未變就不重新 parse。預設不需要 vector database、embedding API 或 LLM summarizer。

### Work

Codex 收到 Truth + Focus。Broad repository discovery 只有在存在具體 unresolved question 時才使用，不再是預設第一步。

### Checkpoint

RSAW 驗證真實 diff、validation commands、allowed-write scope、artifacts、evidence 與 successor task，再以 transaction 封存狀態。

---

## 三層 Context 控制

```text
1. Focus first      先選出最小但足夠的程式碼 working set
2. Bound the turn   限制 tool calls、output 與 broad discovery
3. Compact later    在 checkpoint 邊界替換昂貴的 hot context
```

若 completed turn 超過預設：

```json
{
  "maxProviderInputTokens": 180000,
  "maxCachedInputTokens": 120000
}
```

而下一步原本是 `CONTINUE`，RSAW 會改成 `COMPACT`。這無法追回已消耗 token，但能避免昂貴 transcript 被無限沿用。

---

## Terminal 使用體驗

<p align="center">
  <img src="docs/assets/live-terminal-dashboard-v08.svg" alt="RSAW v0.8 Live Runtime Console" width="96%" />
</p>

Terminal 顯示 observable runtime state，不顯示 hidden reasoning：

| 區域 | 回答的問題 |
|---|---|
| **NOW** | 現在是哪個 task、role、sandbox、durable checkpoint？ |
| **LIFECYCLE** | 下一步是 continue、compact、rotate、pause 還是 complete？ |
| **WORKING MEMORY** | Envelope、Focus、Semantic Capsule 各有多大？ |
| **EFFICIENCY GUARD** | Provider 與 tool traffic 是否失控？ |
| **RECENT** | 最近封存了哪些 durable runtime events？ |

`PAUSED` 與 `COMPLETE` 等正常 operator state 會 clean exit；automation 可用 `--strict-exit-codes` 保留 machine status code。

---

## 什麼時候直接用 Codex？什麼時候用 RSAW？

| 直接 Codex | RSAW + Codex |
|---|---|
| 小型、一次性 task | 多 checkpoint workstream |
| 沒有特殊 authority | Human Gate 或 one-shot execution |
| 不需要中斷復原 | 中斷後必須安全續跑 |
| 人工 context 已足夠 | Repository state 必須具 authority |
| 沒有 role boundary | Runner → Analyst、Builder → Reviewer |
| 不需要 audit | Evidence、sandbox、operator action 必須 durable |

RSAW 不是要把五分鐘修改變複雜，而是要在工作超過單一 session 後，移除你一直當人工 Supervisor 的負擔。

---

## v0.8 刻意不加入的複雜度

- 不把 whole repository 塞進 prompt；
- 不強制使用 vector database；
- 預設不呼叫 embedding service；
- critical path 不使用 LLM summarizer；
- 不 index raw runtime、evidence、artifact、secret 或 environment；
- 不新增 lifecycle state；
- 不把 prompt-cache hit 當成 context reduction；
- 不宣稱已在所有任務全面勝過所有 coding agent。

設計必須保持可讀、可測、可重現。

---

## Safety 與 Authority

v0.8 保留 v0.7.1 的 safety boundary：

- checkpoint advancement 是 transaction，驗證失敗就完整 rollback；
- evidence handle 由 Supervisor 擁有；
- Human Gate 操作具 audit；
- `danger-full-access` 綁定 exact task，且每個 turn 重新解析；
- sandbox class 改變會強制 fresh context boundary；
- checkpoint 失敗不會讓 one-shot execution 可以重跑；
- diagnostic / capability-smoke output 不會自動成為 scientific evidence。

Focus 只是 advisory context，不會取代 authorization、validation、evidence 或 interference check。

---

## 驗證結果

v0.8 release gate 包含：

- **121 tests passing**；
- Python compile validation；
- repository verification；
- FRESH / CONTINUE / COMPACT context tests；
- deterministic Focus selection 與 token ceilings；
- content-hash cache reuse 與 one-file invalidation；
- sensitive/runtime/evidence/artifact exclusion；
- provider-pressure compaction；
- 4 / 16 / 64-checkpoint lifecycle acceptance；
- Markdown link validation；
- CI package build 與 isolated installation。

Deterministic fixture 包含一個 implementation、一個 rejecting test、一個 supporting module 與 36 個 distractor modules，結果為：

```text
baseline context      36,712 tokens
selected Focus           252 tokens
mechanism reduction    99.31%
target implementation      kept
target rejecting test      kept
second index build      43/43 cache hits
```

這是 **mechanism test**，不是 universal provider-cost 或 task-success claim。正式 promotion 仍需與 direct Codex 及舊 RSAW 做 matched evaluation。詳見 [validation](docs/validation/V080_RELEASE_VALIDATION.md)。

---

## EdgeFlow 部署

EdgeFlow 必須停在 durable boundary 才升級：

```bash
python3 -m venv /home/hank/.venvs/rsaw-v080
/home/hank/.venvs/rsaw-v080/bin/python -m pip install --upgrade \
  "git+https://github.com/hanklin9188/repository-state-agent-workflow.git@v0.8.0"

rsaw upgrade . --apply
rsaw focus . --rebuild
rsaw verify .
rsaw preflight .
```

目前 exact-task GPU sandbox 與 Focus Context 是兩個獨立邊界。部署不會授權或執行 EdgeFlow diagnostic。完整流程見 [EdgeFlow v0.8.0 deployment guide](docs/edgeflow-v080-deployment.md)。

---

## 日常命令

| 目的 | Command |
|---|---|
| 開始 supervised work | `rsaw start .` |
| 看選中的程式碼 | `rsaw focus .` |
| 看 exact excerpts | `rsaw focus . --show-content` |
| 開始前完整檢查 | `rsaw preflight .` |
| 看 active state | `rsaw status .` |
| 看 token / runtime metrics | `rsaw report .` |
| 預覽 compiled context | `rsaw compile . --mode FRESH` |
| 正規化 ACTIVE | `rsaw state normalize .` |
| 查看 Human Gate | `rsaw gate show .` |
| 查看 sandbox | `rsaw sandbox show .` |

---

## 文件

- [Relevance-First Context](docs/relevance-first-context.md)
- [EdgeFlow v0.8.0 部署](docs/edgeflow-v080-deployment.md)
- [v0.8.0 release notes](docs/releases/v080-relevance-first-context.md)
- [v0.8.0 validation](docs/validation/V080_RELEASE_VALIDATION.md)
- [GPU sandbox incident](docs/incidents/2026-08-15-edgeflow-gpu-sandbox.md)
- [Architecture](docs/architecture.md)
- [Concepts](docs/concepts.md)
- [Adoption guide](docs/adoption-guide.md)
- [Changelog](CHANGELOG.md)
- [Roadmap](ROADMAP.md)

---

## 開發驗證

```bash
python -m pip install -e '.[dev]'
ruff format --check .
ruff check .
pytest -q
rsaw verify .
rsaw focus . --json
rsaw compile . --mode FRESH --json
rsaw acceptance . --horizon all --json
python scripts/benchmark_relevance.py
python scripts/check_markdown_links.py .
python -m build
```

CI 驗證 Python 3.10、3.12、3.13，以及 clean isolated wheel installation。

## License

MIT
