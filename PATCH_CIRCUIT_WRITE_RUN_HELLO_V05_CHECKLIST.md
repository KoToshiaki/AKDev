# PATCH_CIRCUIT_WRITE_RUN_HELLO_V05 — CHECKLIST

> 設計は `PATCH_CIRCUIT_WRITE_RUN_HELLO_V05_ROADMAP.md`。
> v0.5 UI Polish & Usability の一部。今回は PHASE COMPLETE ではない。
> 「書き込み」は仮想回路へのロード（FPGA 実機ではない）。固定 hello_world.asm 専用ではない。

---

## 0. 事前確認

* [x] CLAUDE.md / ROADMAP6.md / CHECKLIST6.md / HANDOFF.md / UI_SPEC_V05.md を確認した
* [x] 変更予定ファイルと作業範囲をユーザーへ提示した
* [x] `pytest tests/` 直近全通過（729 件）をベースラインとして確認した
* [x] 既存 `src/hello.asm` / `asm/asm.py` / `core/dev.py`(UART) / `core/cpu.py` / `_build` / `_do_run` / `resolve_program_source` を確認した

## 1. ROADMAP / CHECKLIST 作成

* [x] `PATCH_CIRCUIT_WRITE_RUN_HELLO_V05_ROADMAP.md` を作成
* [x] `PATCH_CIRCUIT_WRITE_RUN_HELLO_V05_CHECKLIST.md` を作成

## 2. テスト用 ASM 作成

* [x] `tests/test/hello_world.asm` を作成（既存命令体系・UART 0x100 へ LDI+OUT）
* [x] 既存アセンブラで assemble できる
* [x] 出力は `Hello World !`（末尾改行付き）

## 3. Canvas API

* [x] `resolve_program_node(source_type, prefer_node_id)`（(node_id, path) を優先順位で返す）
* [x] `resolve_program_source` を `resolve_program_node` 経由にリファクタ（戻り値不変）
* [x] 右クリックに「Write Program to Circuit」+ `write_program_requested(node_id)` signal

## 4. MainWin Write Program

* [x] `_loaded_program` runtime 状態（dict, セッション中）
* [x] `write_program(prefer_node_id=None) -> bool`（解決→存在チェック→assemble→ロード→状態設定→ログ）
* [x] `_assemble_and_load` を bool 返却へ拡張（成功 True / 失敗 False）
* [x] Run リボンタブに `Write Program` アクションを追加
* [x] 右クリック signal を `write_program` へ配線

## 5. Run 接続

* [x] `Write Program` 成功で RAM/CPU ロード済み → `Run` で実行
* [x] 既存 `Build → Run` 経路を壊さない
* [x] hello.asm headless（UART "Hi"）を壊さない

## 6. Properties 表示

* [x] Program セクションに Loaded 状態（Loaded / Target / Program）を最小表示
* [x] `show_part(..., loaded=None)` 拡張、未ロードは `Loaded: No`
* [x] Wire Properties / Part Visual パレットを壊さない

## 7. テスト（`tests/test_circuit_write_run_hello_v05.py`）

* [x] `tests/test/hello_world.asm` が存在する
* [x] 既存 assembler で assemble できる
* [x] 実行すると UART 出力に `Hello World !` が含まれる（emulator 経由）
* [x] CPU パーツに `sources.asm = tests/test/hello_world.asm` を割り当てられる
* [x] `write_program` 相当で回路へロードできる
* [x] 書き込み成功時に `loaded_program` が設定される（target_node_id / path / source_type）
* [x] Properties に Loaded 状態が表示される
* [x] `Write Program` → `Run` で UART 出力に `Hello World !` が含まれる
* [x] ASM 未割り当て時に分かりやすいログ（No ASM source assigned）
* [x] 存在しない ASM path で分かりやすいログ（Program source not found）
* [x] 既存 `Build → Run` 経路が壊れていない
* [x] 既存 hello.asm headless で UART "Hi" が維持される
* [x] Program/Sources 割り当ての既存テストが壊れていない
* [x] Wire Style / Wiring 系の既存テストが壊れていない
* [x] `pytest tests/` 全件実行

## 8. ドキュメント更新

* [x] `UI_SPEC_V05.md` に Write Program / loaded_program 仕様を追記
* [x] `ROADMAP6.md` にパッチ項目を追記
* [x] `CHECKLIST6.md` にパッチ参照を追記
* [x] `HANDOFF.md` を更新

## 9. 実装後レビュー

* [x] 変更ドキュメントを読み返す（見出し・リンク・矛盾）
* [x] 作業報告（変更ファイル・テスト結果・互換性・UI 確認点・git status・commit message 案）
