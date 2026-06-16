# PATCH_VISUAL_PORT_MOVE_V05 — CHECKLIST

> 設計は `PATCH_VISUAL_PORT_MOVE_V05_ROADMAP.md`。
> v0.5 UI Polish & Usability の一部。今回は PHASE COMPLETE ではない。

---

## 0. 事前確認

* [x] CLAUDE.md / ROADMAP6.md / CHECKLIST6.md / HANDOFF.md / UI_SPEC_V05.md を確認した
* [x] 変更予定ファイルと作業範囲をユーザーへ提示した
* [x] `pytest tests/` 直近全通過（668 件）をベースラインとして確認した
* [x] 既存 visual port API / mousePress / _vp_local / persist 導線を確認した

## 1. ROADMAP / CHECKLIST 作成

* [x] `PATCH_VISUAL_PORT_MOVE_V05_ROADMAP.md` を作成
* [x] `PATCH_VISUAL_PORT_MOVE_V05_CHECKLIST.md` を作成

## 2. PartNode 拡張

* [x] `_moving_vp_id` + `set_moving_port(vp_id)` / `moving_port()` を追加
* [x] `node_size()`（固定 `_NODE_W`/`_NODE_H` を返す）を追加
* [x] `edge_from_local(local)` で最近辺 side + clamp 済み offset を返す
* [x] `paint()` で移動中 visual port を最強強調（hover より強い）

## 3. Canvas port move 状態 + API

* [x] `_port_move` 状態（node_id / vp_id / original/current side・offset）を追加
* [x] `_start_port_move(node, vp)`（locked 拒否・highlight・状態保持）
* [x] `_update_port_move(scene_pos)`（辺拘束で side/offset 更新 + update_connections）
* [x] `_finish_port_move()`（highlight 解除・状態クリア・ログ）
* [x] `_cancel_port_move()`（original へ復元・update_connections・highlight 解除）

## 4. イベント配線

* [x] `mousePressEvent`: Alt + 左 on vp → port move、Alt なし → 既存 port-drag
* [x] `mouseMoveEvent`: `_port_move` 中は `_update_port_move` のみ（drag/hover/選択を起こさない）
* [x] `mouseReleaseEvent`: `_port_move` 中の左 release で確定
* [x] `contextMenuEvent`: `_port_move` 中はメニューを出さずキャンセル
* [x] `keyPressEvent`: Esc で `_port_move` をキャンセル
* [x] `import_canvas`(clear) で `_port_move` をリセット

## 5. locked

* [x] locked vp は move 開始しない + ログ 1 行（連続ログなし）

## 6. テスト（`tests/test_visual_port_move_v05.py`）

* [x] Alt + 左押下 on visual port で port move が開始される
* [x] Alt なし左押下 on visual port は既存どおり port-drag connect になる
* [x] locked visual port は move 開始しない
* [x] move 中に side / offset が更新される
* [x] move 中に visual port の scene 座標が変わる
* [x] move 中に接続 wire の端点が visual port に追従する
* [x] fan-out 元 visual port を移動すると参照する全 wire が追従する
* [x] マウス release で移動が確定する
* [x] Esc で元の side/offset へ戻る
* [x] 右クリックで元の side/offset へ戻る
* [x] move 中に node 選択 / wire 選択が誤発火しない
* [x] export/import round-trip で移動後の side/offset が維持される
* [x] 既存 port-drag connect が壊れていない
* [x] 既存 wire 選択 / 削除が壊れていない
* [x] 既存右クリック接続が壊れていない
* [x] `pytest tests/` 全件実行

## 7. ドキュメント更新

* [x] `UI_SPEC_V05.md` に visual port 移動仕様を追記
* [x] `ROADMAP6.md` にパッチ項目を追記
* [x] `CHECKLIST6.md` にパッチ参照を追記
* [x] `HANDOFF.md` を更新

## 8. 実装後レビュー

* [x] 変更ドキュメントを読み返す（見出し・リンク・矛盾）
* [x] 作業報告（変更ファイル・テスト結果・互換性・UI 確認点・git status・commit message 案）
