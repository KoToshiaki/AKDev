# PATCH_PART_PROGRAM_ASSIGN_V05 — CHECKLIST

> 設計は `PATCH_PART_PROGRAM_ASSIGN_V05_ROADMAP.md`。
> v0.5 UI Polish & Usability の一部。今回は PHASE COMPLETE ではない。
> 今回はテスト用の最小実装。保存形式と API は将来の正式実装へ拡張しやすくする。

---

## 0. 事前確認

* [x] CLAUDE.md / ROADMAP6.md / CHECKLIST6.md / HANDOFF.md / UI_SPEC_V05.md を確認した
* [x] 変更予定ファイルと作業範囲をユーザーへ提示した
* [x] `pytest tests/` 直近全通過（708 件）をベースラインとして確認した
* [x] 既存 sources / export_parts / import_parts / _build / _do_run / _on_open_tab / PropPanel を確認した
* [x] 既存 sources 既定 `{"asm":None,"hdl":None}` を変更してはいけない制約を確認した

## 1. ROADMAP / CHECKLIST 作成

* [x] `PATCH_PART_PROGRAM_ASSIGN_V05_ROADMAP.md` を作成
* [x] `PATCH_PART_PROGRAM_ASSIGN_V05_CHECKLIST.md` を作成

## 2. Canvas / PartNode API

* [x] `set_node_source(node_id, source_type, path) -> bool`（空/None でクリア、node 無しは False）
* [x] `clear_node_source(node_id, source_type) -> bool`
* [x] `node_sources(node_id) -> dict`
* [x] `node_source(node_id, source_type) -> str | None`（文字列/dict 両対応 `_source_path`）
* [x] `resolve_program_source(source_type="asm", prefer_node_id=None)`（優先順位解決）
* [x] `selected_node_id() -> str | None`

## 3. export / import

* [x] `export_parts` が sources を保存（既定維持、rom は設定時のみ）
* [x] `import_parts` が sources を復元（無しは既定補完）
* [x] round-trip 維持（既存テスト不変）

## 4. Properties（Program / Sources）

* [x] `PropPanel` に Program セクション（asm/hdl/rom 表示 + Set/Clear/Open）を追加
* [x] `show_part(part, node_id, sources=None)` に sources を渡せるよう拡張
* [x] `source_set_requested` / `source_clear_requested` / `source_open_requested` signal
* [x] node 選択時のみ表示（wire/visual/none と排他）

## 5. 右クリックメニュー

* [x] design メニューに「Set ASM Source…」を追加（`set_source_requested` emit）
* [x] 既存「プログラムを開く」（割り当て asm を直接開く）を維持

## 6. Build / Run 接続

* [x] `_assemble_and_load(text, source_name, root)` に共通処理を抽出
* [x] `_resolve_assigned_asm_path()`（優先順位 + 絶対化 + 存在チェック）
* [x] `_build()` が割り当てを優先、無ければ従来のタブ経路へフォールバック
* [x] hello.asm headless 検証（`_do_run`）を壊さない

## 7. Properties / 右クリックの MainWin 配線

* [x] `set_source_requested` → QFileDialog → `set_node_source` + persist + Properties 更新
* [x] `source_clear_requested` → `clear_node_source` + persist + 更新
* [x] `source_open_requested` → 割り当てあれば開く、無ければ "No ASM source assigned" ログ
* [x] `_on_canvas_selection` が show_part に sources を渡す
* [x] path は可能ならルート相対（`_rel_to_root`）、不可なら絶対（将来課題）

## 8. テスト（`tests/test_part_program_assign_v05.py`）

* [x] Canvas で sources を保持できる
* [x] `set_node_source(node, "asm", path)` が True
* [x] 存在しない node への set は False
* [x] `clear_node_source` で asm が消える
* [x] `export_parts` に sources.asm が保存される
* [x] `import_parts` で sources.asm が復元される
* [x] sources 無しの既存 project を読み込める
* [x] sources 既定が `{"asm":None,"hdl":None}` のまま（余計なキーなし）
* [x] Properties で node 選択時に Program セクションが表示される
* [x] Properties から ASM 設定 signal が出る
* [x] Properties から ASM クリア signal が出る
* [x] Wire Properties 表示が壊れていない
* [x] Part Visual Color Palette が壊れていない
* [x] 右クリック「プログラムを開く」が asm source を開く導線につながる
* [x] asm 未設定時に "No ASM source assigned" ログが出る
* [x] Build / Run が選択中パーツの sources.asm を参照できる（UART "Hi"）
* [x] sources.asm が無い場合も既存 hello.asm 検証が壊れない（UART "Hi"）
* [x] `resolve_program_source` の優先順位（選択 > CPU > 任意）
* [x] `pytest tests/` 全件実行

## 9. ドキュメント更新

* [x] `UI_SPEC_V05.md` に Program / Sources 仕様を追記
* [x] `ROADMAP6.md` にパッチ項目を追記
* [x] `CHECKLIST6.md` にパッチ参照を追記
* [x] `HANDOFF.md` を更新

## 10. 実装後レビュー

* [x] 変更ドキュメントを読み返す（見出し・リンク・矛盾）
* [x] 作業報告（変更ファイル・テスト結果・互換性・UI 確認点・git status・commit message 案）
