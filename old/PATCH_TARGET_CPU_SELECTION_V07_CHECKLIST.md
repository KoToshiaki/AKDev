# PATCH_TARGET_CPU_SELECTION_V07 — CHECKLIST

> 設計詳細は `PATCH_TARGET_CPU_SELECTION_V07_ROADMAP.md` を参照。
> 親計画: `ROADMAP7.md` / `CHECKLIST7.md`（5. Target CPU Selection）。

---

## 実装項目

* [x] `core/circuit.py` `resolve_circuit(nodes, connections, target_cpu_id=None)` に拡張
  - [x] 戻り値に `target_cpu` を追加（`cpu == target_cpu`）
  - [x] CPU 0 個: legacy（cpu/target_cpu=None, cpu_present=False）
  - [x] CPU 1 個: その CPU が target（選択非依存）
  - [x] CPU 複数 + target_cpu_id が CPU: その CPU を target、接続のみ検証
  - [x] CPU 複数 + target 未指定/非CPU: ambiguous（`multiple CPU parts (N). Select one CPU to run.`）
  - [x] 接続不足 issue は `target CPU <id> has no connected RAM/UART`
* [x] `ui/win.py` `_resolve_circuit_plan()` で `selected_node_id()` を target_cpu_id に渡す
* [x] `ui/win.py` `_circuit_asm_source(plan)`（target CPU の asm のみ解決）を追加
* [x] `write_program()` を circuit mode で target CPU の asm のみ使用に変更
  - [x] 無ければ `No ASM source assigned to target CPU`
  - [x] `loaded_program.target_node_id = target_cpu`
* [x] `_build()` を circuit mode で target CPU の asm のみ使用に変更（`using assigned asm` 維持）
* [x] `_bind_circuit_runtime()` の Log に `Target CPU: <id>` を追加
* [x] Run/Step が target CPU 基準の plan で実行される（既存 guard 経由で確認）

## テスト項目（`tests/test_target_cpu_selection_v07.py` — 18 件）

### resolve_circuit 単体
* [x] 単一 CPU で target_cpu == cpu
* [x] 複数 CPU + target 指定で target が選択 CPU
* [x] 複数 CPU + 未指定で ambiguous（multiple CPU / Select one CPU）
* [x] 複数 CPU + 選択 CPU 未接続で RAM/UART issue
* [x] 非選択 CPU 未接続でも選択 CPU 接続済みなら ok

### 単一 CPU（MainWin）
* [x] 単一 CPU が target、Write→Run できる
* [x] Hello World が壊れない

### 複数 CPU（MainWin）
* [x] 選択 CPU が target、その RAM/UART が使われる
* [x] 非選択 CPU 未接続でも選択 CPU 接続済みなら Run できる
* [x] target CPU の sources.asm が使われる
* [x] 非選択 CPU の sources.asm は使われない

### ambiguous
* [x] 複数 CPU + 未選択で Write がブロック
* [x] 複数 CPU + 未選択で Run/Step がブロック
* [x] メッセージに `multiple CPU` / `Select one CPU`

### selected CPU 未接続
* [x] 複数 CPU + 選択 CPU RAM 未接続でブロック
* [x] 複数 CPU + 選択 CPU UART 未接続でブロック
* [x] 非選択 CPU が接続済みでも選択 CPU 未接続なら実行しない

### 既存互換
* [x] Plan-driven / Address Map / CPU RAM Validation テストが壊れない
* [x] legacy mode Build→Run（"Hi"）が従来通り
* [x] Step Trace が壊れない
* [x] Program/Sources の既存テストが壊れない

## 検証項目

* [x] `python -m pytest tests/` 全件通過（**829 passed**）
* [x] commit / push を行っていない
* [x] 作業後にドキュメントを読み返した（ROADMAP/CHECKLIST 整合）
