# PATCH_VIRTUAL_CPU_STEP_TRACE_V05 — CHECKLIST

> 設計詳細は `PATCH_VIRTUAL_CPU_STEP_TRACE_V05_ROADMAP.md`。
> v0.5 進行中。**PHASE COMPLETE ではない。**

---

## 0. 事前確認

* [x] CLAUDE.md / ROADMAP6.md / CHECKLIST6.md / HANDOFF.md / ERROR.md を確認
* [x] 既存 emulator（core/cpu.py / dev.py / sim.py）と win.py の実行経路を読んだ
* [x] `pytest tests/` ベースライン 741 件全通過を確認（実装前）
* [x] 変更予定ファイルと作業範囲をユーザーへ提示

## 1. Virtual Runtime（core/runtime.py）

* [x] `VirtualCircuitRuntime` を新規作成（既存 bus/ram/uart/cpu を包む）
* [x] 状態: cpu/ram/uart/bus/loaded/loaded_program/step_count/last_trace/trace_history
* [x] `load_program(binary, *, source_name, target_node_id)`
* [x] `reset()`
* [x] `step() -> dict`
* [x] `run(max_steps=10000) -> list[dict]`
* [x] `registers()` / `memory_snapshot()` / `uart_text()`
* [x] 最小 disassembler（11 命令対応、本格版ではない）

## 2. Bus フック（core/sim.py）

* [x] `Bus.on_access`（既定 None、後方互換）を追加
* [x] read/write で `on_access(op, addr, value, part_id)` を呼ぶ
* [x] 既存 tracing / last_transactions は不変

## 3. Step Trace の内容

* [x] step / pc_before / pc_after
* [x] instruction（disassembler）+ raw
* [x] register_changes（変化レジスタのみ）
* [x] memory（RAM read/write、fetch 除外）
* [x] io（UART OUT など）
* [x] uart（出た文字）
* [x] halted / error

## 4. Step ボタン（ui/win.py）

* [x] 未ロードで `No program loaded. Use Write Program first.`
* [x] 1 押下 = 1 命令
* [x] halted 後 `CPU is halted`
* [x] Log に `[STEP nnnn] PC .. -> .. | <instr>` + REG/MEM/IO/UART
* [x] Register / Memory / Bus Trace / UART / signal overlay 更新

## 5. Run の内部構造

* [x] Run は `runtime.step()` の繰り返し
* [x] halted / 上限（1000）で停止
* [x] `Hello World !` が UART Console に出る
* [x] Log は要約（`Run finished: steps=.., halted=.., uart=".."`）
* [x] 詳細は trace_history に保持

## 6. Write Program 接続

* [x] Write Program 成功で runtime ロード済み
* [x] loaded_program 表示維持
* [x] Write Program → Step / Run が成立
* [x] Build → Run の既存経路維持

## 7. テスト（tests/test_virtual_cpu_step_trace_v05.py）

* [x] hello_world.asm を Write Program できる
* [x] Write 後 runtime が loaded
* [x] Step 1 回で PC が進む
* [x] trace に pc_before / pc_after
* [x] trace に instruction または raw
* [x] LDI の Step でレジスタ変更が trace に出る
* [x] OUT の Step で UART 出力が trace に出る
* [x] Step 繰り返しで UART が 1 文字ずつ増える
* [x] Run は Step 繰り返しで `Hello World !` を出力
* [x] halted 後の Step が安全
* [x] 未ロード時の Step で分かりやすいログ
* [x] Register / Memory / UART Console 更新が壊れていない
* [x] 既存 Build → Run 経路が壊れていない
* [x] hello.asm headless で UART `"Hi"` 維持
* [x] `pytest tests/` を全件実行

## 8. ドキュメント

* [x] PATCH_VIRTUAL_CPU_STEP_TRACE_V05_ROADMAP.md / _CHECKLIST.md
* [x] UI_SPEC_V05.md
* [x] ROADMAP6.md / CHECKLIST6.md
* [x] HANDOFF.md

## 9. 実装後レビュー

* [x] 変更ドキュメントを読み返す（見出し・リンク・矛盾）
* [x] 作業報告（変更ファイル・テスト結果・未確認事項）
* [ ] GUI 目視確認（ヘッドレス環境のため未実施 — 報告に理由を記載）
