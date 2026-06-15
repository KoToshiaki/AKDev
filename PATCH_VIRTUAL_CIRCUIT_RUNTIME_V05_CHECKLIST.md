# PATCH_VIRTUAL_CIRCUIT_RUNTIME_V05 — CHECKLIST

> 設計は `PATCH_VIRTUAL_CIRCUIT_RUNTIME_V05_ROADMAP.md`。
> v0.5 の一部。今回は PHASE COMPLETE ではない。commit / push しない。

---

## 0. 事前確認

* [x] CLAUDE.md / ROADMAP6.md / CHECKLIST6.md / HANDOFF.md / UI_SPEC_V05.md を確認した
* [x] `core/runtime.py` が固定内部回路に依存している箇所を確認した
* [x] `_setup_sim` / `write_program` / `_build` / `_do_run` / `_do_step` の実行経路を確認した
* [x] circuit-mode 化で影響する既存テスト（孤立 CPU で run）を特定した
* [x] `pytest tests/` 762 件全通過をベースライン確認した

## 1. ROADMAP / CHECKLIST 作成

* [x] `PATCH_VIRTUAL_CIRCUIT_RUNTIME_V05_ROADMAP.md`
* [x] `PATCH_VIRTUAL_CIRCUIT_RUNTIME_V05_CHECKLIST.md`

## 2. CircuitPlan（core/circuit.py）

* [x] `resolve_circuit(nodes, connections)` を実装
* [x] CPU/RAM/UART 検出（category ベース、UART は name/part_id 判定）
* [x] CPU–RAM / CPU–UART の wire 接続解析（無向隣接）
* [x] issues 生成（不在 / 未接続 / 複数 CPU）
* [x] `ok` / `cpu_present` を返す

## 3. win.py — Canvas 由来 runtime

* [x] `_make_sim()` を factory 化（startup + 再生成で共用）
* [x] `_resolve_circuit_plan()`（canvas nodes/connections → plan）
* [x] `_circuit_guard(action) -> plan|None`（不正ならブロックログ + None）
* [x] `write_program`: circuit mode で guard → runtime 再生成 + plan バインド → 接続 RAM へロード
* [x] `_build`: circuit mode で guard → runtime 再生成 → ロード（legacy は従来）
* [x] `_do_run` / `_do_step`: guard のみ（未接続でブロック、runtime 再生成しない）
* [x] `runtime.plan` を Properties / loaded_program 表示へ反映（最小）

## 4. 既存テスト更新（正しい回路構成へ）

* [x] `tests/test_virtual_cpu_step_trace_v05.py` の `_assign_hello_world` を CPU+RAM+UART 配置・配線へ
* [x] `tests/test_circuit_write_run_hello_v05.py` の `_assign_hello_world` を同様に
* [x] `tests/test_part_program_assign_v05.py` の run/build 経路を同様に
* [x] legacy（CPU 無し）テストは変更しない

## 5. テスト（`tests/test_virtual_circuit_runtime_v05.py`）

* [x] resolve_circuit: CPU+RAM+UART 接続 → ok / 正しい node_id
* [x] CPU–RAM 未接続 → not ok + issue
* [x] CPU–UART 未接続 → not ok + issue
* [x] CPU 不在 → not ok（cpu_present False）
* [x] 複数 CPU → issue
* [x] MainWin: 正しい回路で write_program → True / runtime.plan セット
* [x] MainWin: write_program → run で UART `Hello World !`
* [x] MainWin: 孤立 CPU（RAM/UART 無し）で write_program False + ブロックログ
* [x] MainWin: 孤立 CPU で run ブロック
* [x] MainWin: Write は接続 RAM へロード（runtime.memory に binary）
* [x] legacy（CPU 無し）で従来の Build→Run / RAM直ロード Run が動く
* [x] hello.asm headless "Hi" 維持
* [x] `pytest tests/` 全件実行

## 6. ドキュメント更新

* [x] `UI_SPEC_V05.md`（11-M）に Virtual Circuit Runtime を追記
* [x] `ROADMAP6.md` にパッチ項目を追記
* [x] `CHECKLIST6.md` にパッチ参照を追記
* [x] `HANDOFF.md` を更新

## 7. 実装後レビュー

* [x] 変更ドキュメントを読み返す（見出し・リンク・矛盾）
* [x] 作業報告（変更ファイル・テスト結果・互換性・UI 確認点・git status・commit message 案）
