# PATCH_PORT_DRAG_CONNECT_V05 — Port Drag Connect（チェックリスト）

> 設計書: `PATCH_PORT_DRAG_CONNECT_V05_ROADMAP.md`。
> 親フェーズ: `ROADMAP6.md` / `CHECKLIST6.md`（v0.5）。

---

## P0. 事前確認

* [x] 既存ドキュメント（CLAUDE / ROADMAP6 / CHECKLIST6 / HANDOFF / UI_SPEC_V05）を確認
* [x] 現状コード（mousePress/Move/Release/keyPress/contextMenu・visual port 描画）を精査
* [x] パッチ ROADMAP / CHECKLIST を先に作成

## P1. visual port ヒットテスト

* [x] `_visual_port_at(scene_pos)` を追加（全 node の vp を距離判定）
* [x] 近ければ (node, vp)、遠ければ None

## P2. port-drag 状態

* [x] `_port_drag` / `_port_drag_preview` を `__init__` に追加
* [x] `_start_port_drag(node, vp)`（状態セット + 破線 preview 生成）
* [x] `_cancel_port_drag()`（preview 除去 + 状態クリア）

## P3. preview 表示

* [x] `_update_port_drag_preview(cursor_scene)` を curved 破線で描画
* [x] source port の side 外向きに制御点

## P4. 接続確定

* [x] `_finish_port_drag(to_node_id)`：target に新 vp 生成 + `add_connection(from_vp=既存, to_vp=新)`
* [x] 同一ノード / target 無しはキャンセル
* [x] 確定後 preview 除去・状態クリア

## P5. イベントフック

* [x] mousePress（左）: vp hit → `_start_port_drag`・accept・super 呼ばない
* [x] mouseMove: `_port_drag` 中は preview 更新して return
* [x] mouseRelease（左）: `_port_drag` 中は finish/cancel
* [x] keyPress Esc: `_port_drag` 中はキャンセル
* [x] contextMenu: `_port_drag` 中はキャンセルしてメニュー抑止
* [x] 中ボタン pan・右クリック wire・Delete は不変

## P6. 既存資産への接続

* [x] 確定接続は Dynamic Visual Port（visual_port_id 両端）になる
* [x] curved wire で描画される
* [x] ノード移動で追従・削除で同期削除（既存実装を流用）

## P7. 既存 Wiring 互換

* [x] 既存の右クリック接続（`_begin_wire_from`/`_finish_wire`）が動く
* [x] Cancel Wire / Escape（wire mode）/ pan / 削除同期 / export-import が不変

## P8. テスト

* [x] `_visual_port_at` hit / miss
* [x] `_start_port_drag` 状態 + preview
* [x] `_finish_port_drag` で接続生成（from=既存 vp, to=新 vp）
* [x] 同一ノードはキャンセル
* [x] `_cancel_port_drag` で preview/状態クリア
* [x] Esc キャンセル
* [x] mousePress→release 統合（vp→別ノード）
* [x] export/import round-trip
* [x] 既存右クリック接続が壊れていない
* [x] `pytest tests/` 全通過

## P9. ドキュメント更新

* [x] `UI_SPEC_V05.md` 11-J に port-drag を追記
* [x] `ROADMAP6.md` / `CHECKLIST6.md` に本パッチ参照
* [x] `HANDOFF.md` 更新

## P10. 実装後レビュー

* [x] hello.asm headless 検証（UART "Hi"）維持
* [x] port-drag → 接続 → 保存読込 の headless スモーク
* [ ] GUI 目視確認（ヘッドレス環境のため未実施 — 報告に記載）
* [x] 作業報告
