<p align="center">
  <img src="docs/assets/banner-v06.svg" alt="Repository-State Agent Workflow" width="100%" />
</p>

# Repository-State Agent Workflow (RSAW) v0.6

**持久工作流、編譯式工作記憶、確定性 checkpoint。**

RSAW 是為長時間 coding / research agent 設計的 repository-backed runtime。它把真正的專案狀態保存在 repository，而不是把 conversation 當成唯一記憶；在每次 agent 工作前，由 Context Compiler 組出下一個 checkpoint 真正需要的最小工作記憶。

> **Persist aggressively. Infer sparingly. Rotate selectively.**

[English README](README.md) · [v0.6 架構](docs/v06-context-operating-system.md) · [EdgeFlow 升級](docs/edgeflow-v06-migration.md)

---

## 為什麼 v0.6 不是單純調整 v5

舊 RSAW v3 matched evaluation 顯示，問題不是 `ACTIVE.md` 本身太大，而是：

- checkpoint 與 context rotation 綁太緊；
- model 自己讀／改 ACTIVE、執行 deterministic bookkeeping；
- Explore → Plan → Implement 之間過度建立 fresh context；
- tool loop 重複支付大量 system/tool/context prefix；
- fresh agent 缺乏可恢復的 semantic working memory；
- reviewer 重新探索太多 repository；
- 長 diff/log/source 被反覆送回模型。

v0.6 直接把 runtime 改成：

```text
Durable Repository State
        ↓
Semantic Capsule
        ↓
Context Compiler
        ↓
Agent Epoch
        ↓
Typed CheckpointResult
        ↓
Deterministic Gate
        ↓
Token Governor
        ↓
CONTINUE / COMPACT / ROTATE / PAUSE / COMPLETE
```

<p align="center">
  <img src="docs/assets/runtime-architecture-v06.svg" alt="RSAW v0.6 architecture" width="94%" />
</p>

---

## 最關鍵的改變

### 1. Checkpoint 不再等於換 context

```text
Checkpoint = durability boundary
Epoch      = cognitive boundary
```

Builder 可以在同一條工作 context 中完成 Explore → Plan → Implement 並留下多個 durable checkpoints；只有真正需要獨立認知時才 ROTATE。

### 2. `COMPACT != ROTATE`

- `CONTINUE`：同角色、同 objective、working context 還有價值。
- `COMPACT`：context 太貴，但不需要認知獨立；保存 Semantic Capsule 後以同角色 compact context 繼續。
- `ROTATE`：Builder → Reviewer、Runner → Analyst 或其他 independence boundary。
- `PAUSE`：真實 human/external gate。
- `COMPLETE`：stop condition 真正完成。

### 3. Supervisor 擁有 bookkeeping

v0.6 supervised agent：

- 不可以修改 `ACTIVE.md`；
- 不可以跑 `advance.py`；
- 只做 semantic engineering work；
- 最後回傳 `rsaw.checkpoint-result.v1` JSON。

Supervisor 負責：

- 檢查真實 diff；
- 驗證 allowed writes；
- 對照實際 validation command events；
- 驗證 artifact/checksum；
- 產生 Evidence Handles；
- 更新 Semantic Capsule；
- 封存 immutable checkpoint + SHA-256；
- 原子更新 active pointer / `ACTIVE.md`；
- 決定下一個 lifecycle action。

### 4. Semantic Capsule

跨 COMPACT / ROTATE 保存：

- facts；
- decisions；
- excluded hypotheses；
- evidence refs；
- unresolved risks；
- high-value code relations；
- validation status；
- next exact action。

它是 bounded structured memory，不是無限制 summary log。

### 5. Context Compiler

不是單純列「要讀哪些檔案」，而是編譯 sealed Context Envelope：

```text
Exact task / acceptance / safety
+ Semantic Capsule
+ Current delta
+ bounded exact evidence
+ evidence references
```

預設工程 budget：target 6k、hard 12k tokens；critical evidence、capsule、validation summary 各有獨立限制。

### 6. Evidence Handles + Read-if-changed

長 log、diff、source 可以 content-addressed 封存。內容 hash 沒變時不必重新送；只有真正需要時才展開。

### 7. Bounded Reviewer

Fresh Reviewer 保持獨立，但取得 Review Manifest：claim、acceptance、changed files、validation、evidence、known risks、revision。它不需要繼承 Builder hidden reasoning，也不需要預設重新掃整個 repo。

---

## v0.6 Live Runtime Console

<p align="center">
  <img src="docs/assets/live-terminal-dashboard-v06.svg" alt="RSAW v0.6 Live Runtime Console" width="96%" />
</p>

現在 UI 顯示：

- current task / role / checkpoint；
- CONTINUE / COMPACT / ROTATE / PAUSE / COMPLETE；
- deterministic gate；
- Context Envelope / Semantic Capsule；
- estimated occupancy；
- total / cached / fresh provider input；
- model calls / tool calls；
- repeated input；
- evidence resend；
- recent durable events。

UI 只是 presentation layer，不會擁有 lifecycle state，也不會把 hidden reasoning 顯示出來。

---

## 安裝

正式 `v0.6.0` tag 發布後：

```bash
python -m pip install --upgrade \
  "git+https://github.com/hanklin9188/repository-state-agent-workflow.git@v0.6.0"
```

確認：

```bash
python - <<'PY'
from importlib.metadata import version
import repo_state_agent
print(repo_state_agent.__version__)
print(version("repository-state-agent-workflow"))
PY
```

應輸出兩個 `0.6.0`。

---

## 舊專案升級

**不要 `rsaw init --force`。**

先 preview：

```bash
rsaw migrate . --to 0.6 --json
```

再 apply：

```bash
rsaw migrate . --to 0.6 --apply
```

Migration 會保留 `ACTIVE.md` byte-identical，備份舊 config，再啟用 v0.6 runtime。

驗證：

```bash
rsaw verify .
rsaw compile . --mode FRESH --json
rsaw run . --dry-run
rsaw acceptance . --horizon all
rsaw preview-v6 . --seconds 8
```

---

## v0.6 與 v4 / v5

| 能力 | v4 | v5 | v6 |
|---|---:|---:|---:|
| Live Console | ✓ | ✓ | ✓ 強化 |
| Stable/dynamic context | — | ✓ | ✓ |
| Semantic Capsule | — | — | **✓** |
| Context Compiler | — | 部分 | **✓** |
| Supervisor-owned ACTIVE | — | — | **✓** |
| Typed checkpoint result | — | — | **✓** |
| Checksummed checkpoint | — | — | **✓** |
| Evidence Handle | — | — | **✓** |
| Read-if-changed | — | fingerprint | **✓** |
| COMPACT vs ROTATE | — | — | **✓** |
| Bounded Reviewer | — | — | **✓** |
| Repeated/evidence telemetry | — | 部分 | **✓** |

---

## 驗收標準

v0.6 不會因為 pytest PASS 就宣稱 token optimization 成功。

必須另外經過 matched prospective evaluation：

- Semantic success 不得低於 No-RSAW；
- short horizon 不得有明顯 input/success regression；
- medium horizon 目標 total/cached per success 至少下降 20%，uncached 至少 15%；
- long horizon 32–64 checkpoints 要看到 total/repeated input per success 明顯分離；
- manual relay = 0；
- fresh recovery 正常；
- stale-state errors 不增加。

上述百分比是 promotion targets，不是目前已量測完成的結果。

---

## Claim boundary

v0.6 可以用 CI / unit / migration / synthetic lifecycle 測試證明**工程實作正確性**。

但「success 從舊 v3 14/24 回到 23/24」、「input/success 降低約 45–50%」等數字，在真實 matched benchmark 完成前都只能視為 hypothesis，不能寫成已證明成果。

MIT License.
