# PATCH_TARGET_CPU_SELECTION_V07 — ROADMAP

> v0.7（Plan-driven Virtual Devices & Address Map）4 番目のパッチ。
> 親計画: `ROADMAP7.md` / 進捗: `PATCH_TARGET_CPU_SELECTION_V07_CHECKLIST.md`。
> 前提: `PATCH_PLAN_DRIVEN_DEVICES_V07` / `PATCH_ADDRESS_MAP_V07` /
> `PATCH_CPU_RAM_VALIDATION_V07` 完了（`pytest tests/` 811 passed）。

---

## 目的

Canvas 上に CPU が複数ある場合に、**選択中 CPU を実行対象（target CPU）として扱える**
ようにする。CPU が 1 個なら従来通り、複数なら選択中 CPU、未選択なら ambiguous として
ブロックする。Write Program / Build / Run / Step が常に同じ target CPU を使い、
Program Sources も target CPU の `sources.asm` を優先する。

## 現在の問題

- `resolve_circuit()` は CPU が複数あると `multiple CPU` issue を付け、なお `cpus[0]` を
  固定で `cpu` にしていた。どの CPU を実行するかが不明確で、選択を反映できない。
- 非選択 CPU が未接続でも、`cpus[0]` 固定のため意図しない CPU で判定・実行されうる。
- Program Sources（`resolve_program_node`）が selected > CPU > any のフォールバックで
  解決するため、複数 CPU 時に target でない CPU の asm を誤って使う恐れがある。

## 実装方針

### 1. CircuitPlan の target CPU 対応（`core/circuit.py`）

`resolve_circuit(nodes, connections, target_cpu_id=None)` に拡張する。

- 戻り値に `target_cpu` を追加（既存の `cpu` キーは互換のため残し、`cpu == target_cpu`）。
- CPU 0 個: legacy。`ok=False / cpu=None / target_cpu=None / cpu_present=False`。
- CPU 1 個: `target_cpu = その CPU`（選択状態に依存しない）。接続を検証。
- CPU 複数 + `target_cpu_id` が CPU のいずれか: その CPU を target にし、その接続だけ検証。
- CPU 複数 + `target_cpu_id` が None / CPU でない: ambiguous。
  issue `multiple CPU parts (N). Select one CPU to run.` / `cpu=None / target_cpu=None`。
- 接続不足 issue は target CPU についてのみ:
  `target CPU <id> has no connected RAM` / `... has no connected UART`。

### 2. MainWin 側の target CPU 取得（`ui/win.py`）

`_resolve_circuit_plan()` で `self._canvas.selected_node_id()` を取得し、
`resolve_circuit(..., target_cpu_id=selected)` へ渡す。

### 3. circuit guard

`_circuit_guard(action)` は既存ロジックのまま（`cpu_present and not ok` でブロック）で、
ambiguous・選択 CPU 未接続のどちらも block メッセージに反映される。

### 4. Write Program / Build / Run / Step の target 統一

- Write / Build は circuit mode で target CPU の asm のみを解決する共通ヘルパ
  `_circuit_asm_source(plan)` を使う。
- Run / Step は `_circuit_guard` の plan（= target CPU 基準）で実行し、再生成しない。
- Write は target CPU に書き、`loaded_program.target_node_id = target_cpu`。

## target CPU 選択ルール

| CPU 数 | 選択ノード | 挙動 |
|---|---|---|
| 0 | - | legacy mode（従来のエディタタブ Build→Run） |
| 1 | 任意 | その CPU が target（選択無視）。未接続なら従来通りブロック |
| 複数 | CPU | その CPU が target。target の接続のみ検証 |
| 複数 | CPU でない / 無し | ambiguous（`multiple CPU parts (N). Select one CPU to run.`） |
| 複数 | CPU だが未接続 | その CPU について RAM/UART 未接続ブロック |

## Program Sources との関係

- circuit mode（CPU あり）: **target CPU の `sources.asm` のみ**を使用。
  無ければ `No ASM source assigned to target CPU` を出し、他 CPU へフォールバックしない。
- legacy mode（CPU 無し）: 従来通り `resolve_program_node`（selected > CPU > any）→
  なければエディタタブ Build。

## circuit guard との関係

- `_circuit_guard` は target CPU 基準の plan を返す。非選択 CPU の未接続は issue に含めない。
- 選択 CPU が未接続なら、非選択 CPU が正しく接続されていてもブロックする。

## Log 表示

- circuit build 時に `Target CPU: <id>` を出す（`Circuit built: ...` の前）。
- ambiguous / 未接続は `<action> blocked — ...` で明示。

## テスト方針（`tests/test_target_cpu_selection_v07.py` 新規）

- 単一 CPU: target になる / Write→Run できる / Hello World 維持。
- 複数 CPU + 選択: 選択 CPU が target、その RAM/UART が使われる、非選択未接続でも実行可、
  target の asm が使われ非選択の asm は使われない。
- ambiguous: 複数 CPU + 未選択で Write/Run/Step がブロック、メッセージに
  `multiple CPU` / `Select one CPU`。
- 選択 CPU 未接続: RAM/UART 未接続でブロック（非選択が接続済みでも実行しない）。
- 既存互換: Plan-driven / Address Map / CPU RAM Validation / Step Trace / Hello World / legacy。
- `resolve_circuit` 単体（target_cpu キー、ambiguous、single==target）。

## 今回やらないこと

複数 CPU 同時実行 / マルチコア / CPU 間通信 / Bus arbitration /
複数 RAM・UART 本格対応 / Run Status Panel / Port Detail / Address Map Editor /
VRAM・Storage・Input・Display / MMU / 割り込み / C コンパイラ / HDL 合成 /
FPGA 実機書き込み / ゲーム実行 / commit / push。

## 既存互換性の注意点

- `resolve_circuit` の `cpu` キーは維持し、`cpu == target_cpu`（単一 CPU では従来同値）。
- 既存テストは issue の部分一致（`"RAM"` / `"UART"` / `"multiple CPU"`）のみを確認しており、
  新メッセージはこれらの語を含むため壊れない。
- legacy mode（RAM 256B / UART 0x0100 / "Hi"）は不変。
- `No ASM source assigned to target CPU` は既存検査語 `No ASM source assigned` を内包する。
