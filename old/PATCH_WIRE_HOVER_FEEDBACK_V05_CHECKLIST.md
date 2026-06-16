# PATCH_WIRE_HOVER_FEEDBACK_V05 — CHECKLIST

> 設計は `PATCH_WIRE_HOVER_FEEDBACK_V05_ROADMAP.md`。
> v0.5 UI Polish & Usability の一部。今回は PHASE COMPLETE ではない。

---

## 0. 事前確認

* [x] CLAUDE.md / ROADMAP6.md / CHECKLIST6.md / HANDOFF.md / UI_SPEC_V05.md を確認した
* [x] 変更予定ファイルと作業範囲をユーザーへ提示した
* [x] `pytest tests/` 630 件全通過を確認した（着手前ベースライン）
* [x] 既存 set_active / port-drag テストの前提を確認した（pen 復元・ログ assert 無し）

## 1. ROADMAP / CHECKLIST 作成

* [x] `PATCH_WIRE_HOVER_FEEDBACK_V05_ROADMAP.md` を作成
* [x] `PATCH_WIRE_HOVER_FEEDBACK_V05_CHECKLIST.md` を作成

## 2. visual port hover

* [x] `PartNode` に `_hover_vp_id` 状態と `set_hover_port(vp_id)` / `hover_port()` を追加
* [x] `PartNode.paint()` で hover 中の visual port を強調描画（明るく + 白枠 + 拡大）
* [x] `Canvas` に `_hover_vp` 状態 + `_set_hover_vp` / `_clear_hover_vp` を追加
* [x] `mouseMoveEvent`（ボタン非押下時）で `_visual_port_at` を使い hover 更新
* [x] `leaveEvent` で hover を解除

## 3. wire hover

* [x] `ConnectionLine` に `_hovered` + `set_hovered(bool)` / `is_hovered()` を追加
* [x] `ConnectionLine._apply_pen()` を新設し set_active / set_hovered を集中管理（active 優先）
* [x] `Canvas._connection_at(scene_pos)` を追加（path 距離判定）
* [x] `Canvas._set_hover_conn(conn_id)` を追加し hover 切替
* [x] `mouseMoveEvent` で wire hover を更新（port hover 中は wire hover しない）

## 4. port-drag 中の接続先候補ハイライト

* [x] `PartNode` に `_drop_highlight` + `set_drop_highlight(bool)` / `drop_highlight()` を追加
* [x] `PartNode.paint()` で drop highlight をアクセント色外枠で表現
* [x] `Canvas._hover_drop_node_id` + `_set_drop_highlight(node_id)` を追加
* [x] `Canvas._update_drop_target(node_id)`（同一ノード除外）を追加
* [x] `mouseMoveEvent`（port-drag 中）でカーソル下ノードを drop target に
* [x] `_cancel_port_drag()` で drop highlight を必ず解除（finish 経由も含む）

## 5. ログ補助

* [x] `_start_port_drag` で 1 行だけログ補助を出す（mouseMove ではログしない）

## 6. テスト（`tests/test_wire_hover_feedback_v05.py`）

* [x] visual port hover 状態が更新される
* [x] hover 中の visual port を持つ PartNode の hover_port() が反映される
* [x] hover 解除で状態が消える
* [x] `ConnectionLine.set_hovered(True/False)` で pen が変化 / 復元する
* [x] set_hovered と set_active の両立（active 優先）を確認
* [x] port-drag 中に別ノードへ乗ると drop highlight が有効になる
* [x] 同一ノード上では接続候補扱いにならない
* [x] port-drag キャンセルで drop highlight が解除される
* [x] 既存の port-drag 接続が壊れていない
* [x] 既存の右クリック接続が壊れていない
* [x] export/import が壊れていない
* [x] `pytest tests/` 全件実行

## 7. ドキュメント更新

* [x] `UI_SPEC_V05.md` に hover feedback 仕様を追記
* [x] `ROADMAP6.md` にパッチ項目を追記
* [x] `CHECKLIST6.md` にパッチ参照を追記
* [x] `HANDOFF.md` を更新

## 8. 実装後レビュー

* [x] 変更ドキュメントを読み返す（見出し・リンク・矛盾）
* [x] 作業報告（変更ファイル・テスト結果・UI 確認点・git status・commit message 案）
