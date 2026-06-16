# PATCH_WIRE_STYLE_V05 — CHECKLIST

> 設計は `PATCH_WIRE_STYLE_V05_ROADMAP.md`。
> v0.5 UI Polish & Usability の一部。今回は PHASE COMPLETE ではない。

---

## 0. 事前確認

* [x] CLAUDE.md / ROADMAP6.md / CHECKLIST6.md / HANDOFF.md / UI_SPEC_V05.md を確認した
* [x] 変更予定ファイルと作業範囲をユーザーへ提示した
* [x] `pytest tests/` 直近全通過（685 件）をベースラインとして確認した
* [x] 既存 ConnectionLine pen 管理 / add_connection / export / PropPanel / MainWin 通知を確認した
* [x] `conn["width"]`（論理バス幅）と `style.width`（描画幅）の別物性を確認した

## 1. ROADMAP / CHECKLIST 作成

* [x] `PATCH_WIRE_STYLE_V05_ROADMAP.md` を作成
* [x] `PATCH_WIRE_STYLE_V05_CHECKLIST.md` を作成

## 2. ConnectionLine 描画

* [x] `apply_style(color="", width=None)` を追加（base pen を再構築 → `_apply_pen()`）
* [x] `base_color()` / `base_width()` アクセサを追加
* [x] selected > active > hover > custom style > kind default の優先度を維持

## 3. Canvas API + データ

* [x] `_make_conn_item` で `conn["style"]` を `apply_style` に反映
* [x] `set_connection_style(conn_id, color=None, width=None)`（color="" でクリア、未設定は style 削除）
* [x] `reset_connection_style(conn_id)`（style を消す）
* [x] `get_connection(conn_id)` を追加
* [x] 変更後に ConnectionLine 表示更新、selected/hover 維持

## 4. wire 選択通知

* [x] Canvas に `wire_selected(dict)` / `wire_selection_cleared()` signal を追加
* [x] `_set_selected_conn` で選択/解除時に emit
* [x] `set_/reset_connection_style` で選択中 conn なら `wire_selected` を再 emit（Properties 更新）
* [x] wire 選択時に node 選択をクリア（mousePress / 右クリック wire 経路）

## 5. Properties（Wire セクション）

* [x] `PropPanel` に Wire セクション（情報 + パレット + width + Reset）を追加
* [x] `show_wire(conn)` を追加（id/kind/from/to/color/width 表示）
* [x] `wire_color_changed(conn_id, hex)` / `wire_width_changed(conn_id, width)` / `wire_style_reset(conn_id)` signal
* [x] node 選択（show_part）/ 未選択（show_none）と排他表示（wire/visual box の出し分け）
* [x] wire 用 palette と part 用 palette を別 swatch・別ハンドラに

## 6. MainWin 配線

* [x] `wire_selected` → `show_wire`、`wire_selection_cleared` → `show_none`
* [x] `wire_color_changed` / `wire_width_changed` / `wire_style_reset` → Canvas API + persist
* [x] node 選択 Properties（`_on_canvas_selection`）を壊さない

## 7. 右クリックメニュー

* [x] wire 右クリックに「Reset Wire Style」を追加（Delete Wire は維持）
* [x] PartNode / port-drag / port-move / wire mode の右クリックは不変

## 8. 保存形式

* [x] export/connections に style を含める（未設定は出さない）
* [x] import で style を復元、style 無しでも読める、round-trip で維持

## 9. テスト（`tests/test_wire_style_v05.py`）

* [x] connection style を設定できる
* [x] color 指定の ConnectionLine が custom color を base pen に使う
* [x] width 指定の ConnectionLine が custom width を base pen に使う
* [x] style 未設定時は既存 kind 色/幅が使われる
* [x] selected > active > hover > custom style > kind default の優先度が破綻しない
* [x] `set_connection_style` が存在する conn で True、存在しない conn で False
* [x] `reset_connection_style` で style が消える
* [x] export/import round-trip で style が維持される
* [x] style 未設定 connection に余計な style が保存されない
* [x] wire 選択時に Properties が wire 情報表示へ切り替わる
* [x] node 選択時の Properties 表示が壊れていない
* [x] wire color palette で選んだ色が selected wire に適用される
* [x] Reset Style / Default で既定表示へ戻る
* [x] wire 右クリック Delete Wire が壊れていない
* [x] 既存 wire 選択/削除・port-drag・visual port move・右クリック接続が壊れていない
* [x] `pytest tests/` 全件実行

## 10. ドキュメント更新

* [x] `UI_SPEC_V05.md` に wire style 仕様を追記
* [x] `ROADMAP6.md` にパッチ項目を追記
* [x] `CHECKLIST6.md` にパッチ参照を追記
* [x] `HANDOFF.md` を更新

## 11. 実装後レビュー

* [x] 変更ドキュメントを読み返す（見出し・リンク・矛盾）
* [x] 作業報告（変更ファイル・テスト結果・互換性・UI 確認点・git status・commit message 案）
