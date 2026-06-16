# PATCH_WIRE_SELECT_DELETE_V05 — CHECKLIST

> 設計は `PATCH_WIRE_SELECT_DELETE_V05_ROADMAP.md`。
> v0.5 UI Polish & Usability の一部。今回は PHASE COMPLETE ではない。

---

## 0. 事前確認

* [x] CLAUDE.md / ROADMAP6.md / CHECKLIST6.md / HANDOFF.md / UI_SPEC_V05.md を確認した
* [x] 変更予定ファイルと作業範囲をユーザーへ提示した
* [x] `pytest tests/` 直近全通過（649 件）をベースラインとして確認した
* [x] 既存 `_apply_pen` / `_prune_orphan_visual_ports` / `_remove_node` / persist 導線を確認した

## 1. ROADMAP / CHECKLIST 作成

* [x] `PATCH_WIRE_SELECT_DELETE_V05_ROADMAP.md` を作成
* [x] `PATCH_WIRE_SELECT_DELETE_V05_CHECKLIST.md` を作成

## 2. wire 選択

* [x] `ConnectionLine` に `_selected` + `set_selected(bool)` / `is_selected()` を追加
* [x] `ConnectionLine._apply_pen()` の優先度を selected > active > hover > normal に拡張
* [x] `Canvas._selected_conn_id` + `_set_selected_conn(conn_id)` を追加
* [x] `mousePressEvent`（design mode・左クリック）で wire 選択（port / node 優先を維持）
* [x] 空白 / ノードクリックで wire 選択を解除

## 3. wire 削除 API

* [x] `Canvas._remove_connection(conn_id)` を新設
* [x] `_connections` から削除 + `_conn_items` の line を scene から除去
* [x] selected / hovered がその conn を指していれば解除
* [x] `_prune_orphan_visual_ports()` を呼ぶ（共有 vp は残す）
* [x] `update_connections()` を呼ぶ

## 4. Delete キー

* [x] selected wire（かつ port-drag でない）→ wire 削除、それ以外 → `delete_selected()`
* [x] ノード削除・port-drag Esc・wire mode Esc の既存挙動を壊さない

## 5. wire 右クリックメニュー

* [x] design mode・wire 近くの右クリックで wire を選択し「Delete Wire」を表示
* [x] Delete Wire で `_remove_connection` を呼ぶ
* [x] PartNode 上 / wire でない場所 / port-drag 中 / wire mode は従来どおり

## 6. 選択解除 / 整合

* [x] `import_canvas`（clear）で wire 選択・hover を解除
* [x] `_remove_node` で選択中 wire が消えた場合に選択解除

## 7. テスト（`tests/test_wire_select_delete_v05.py`）

* [x] wire クリックで `_selected_conn_id` が設定される
* [x] 選択中 wire の ConnectionLine が selected 表示になる
* [x] 別 wire クリックで選択が移る
* [x] 空白クリックで wire 選択が解除される
* [x] Delete キーで選択中 wire が削除される
* [x] wire 削除後、connection data と ConnectionLine item が消える
* [x] wire 削除後、orphan visual port が prune される
* [x] fan-out 元 vp が他 conn から参照されていれば削除されない
* [x] wire 右クリック相当（`_remove_connection`）が呼べる
* [x] PartNode 右クリックメニューが壊れていない（design メニュー経路）
* [x] port-drag 中の右クリックキャンセルが壊れていない
* [x] 既存 port-drag 接続が壊れていない
* [x] 既存右クリック接続が壊れていない
* [x] export/import が壊れていない
* [x] signal overlay active と selected の pen 優先度が破綻しない
* [x] `pytest tests/` 全件実行

## 8. ドキュメント更新

* [x] `UI_SPEC_V05.md` に wire 選択・削除仕様を追記
* [x] `ROADMAP6.md` にパッチ項目を追記
* [x] `CHECKLIST6.md` にパッチ参照を追記
* [x] `HANDOFF.md` を更新

## 9. 実装後レビュー

* [x] 変更ドキュメントを読み返す（見出し・リンク・矛盾）
* [x] 作業報告（変更ファイル・テスト結果・互換性・UI 確認点・git status・commit message 案）
