# PATCH_WIRING_PORTS_V05 — Dynamic Visual Port（チェックリスト）

> 設計書: `PATCH_WIRING_PORTS_V05_ROADMAP.md`。
> 親フェーズ: `ROADMAP6.md` / `CHECKLIST6.md`（v0.5）。

---

## P0. 事前確認

* [x] 既存ドキュメント（CLAUDE / ROADMAP6 / CHECKLIST6 / HANDOFF / UI_SPEC_V05）を確認
* [x] 現状の接続スキーマ（add_connection / export_canvas / import_canvas / update_connections）を精査
* [x] 既存テスト依存（_port_dot / PortDot / 端点テスト）を確認
* [x] パッチ ROADMAP / CHECKLIST を先に作成

## P1. Dynamic Visual Port 設計（PartNode）

* [x] PartNode に `_visual_ports` を追加（初期 0 個）
* [x] `add_visual_port` / `visual_ports` / `get_visual_port` / `remove_visual_port` / `set_visual_ports`
* [x] `visual_port_pos(id)`（side + offset → 実座標）
* [x] paint で visual port を小円描画（kind 色）

## P2. 保存形式設計

* [x] visual port のスキーマ確定（id / side / offset / kind / label / locked）
* [x] 接続 from/to に `visual_port_id` / `logical_port` を追加（`port` は互換維持）
* [x] vp ID 採番（`_next_vp_id`）

## P3. legacy _port_dot の非表示化・互換整理

* [x] `_port_dot` を `setVisible(False)`（Canvas 上で見えない）
* [x] クラス / インスタンス / `_on_port_click` は残す（シミュレーション互換）
* [x] 非表示にする理由を ROADMAP に明記（完了済み）
* [x] `test_canvas_port_connect.py` を非表示前提に更新（必要箇所）

## P4. 接続時 visual port 作成

* [x] `_create_visual_port(node_id, side, logical_port)` を追加
* [x] `_finish_wire` で両端に visual port を生成
* [x] 既定オフセットは辺ごとに自動スタック（重なり回避）

## P5. connection への visual_port_id 追加

* [x] `add_connection` に `from_vp` / `to_vp` を受け、from/to に保存
* [x] `_finish_wire` で生成した vp の id を接続に渡す
* [x] 既存呼び出し（vp 無し）は従来どおり

## P6. visual port scene 座標計算

* [x] `visual_port_pos` が side/offset から正しい scene 座標を返す
* [x] ノード移動で座標が追従する
* [x] `update_connections` の端点を visual port 座標で解決（無ければ従来端へ fallback）

## P7. visual port 移動 API

* [x] `set_visual_port_offset(node_id, vp_id, offset)`（locked 拒否・クランプ）
* [x] `set_visual_port_side(node_id, vp_id, side)`
* [x] 移動後に `update_connections` で wire 追従

## P8. visual port 整列 API

* [x] `arrange_visual_ports(node_id)`（辺ごとに均等配置・locked 尊重）
* [x] 設計モード右クリックに「ポートを整列」を追加

## P9. export/import 対応

* [x] export_parts に `visual_ports` を追加（0 個なら省略）
* [x] import_parts で `visual_ports` を復元
* [x] import 時に vp ID seq を巻き戻し防止
* [x] connection の visual_port_id / logical_port が round-trip する

## P10. node 削除時の visual port / connection 同期削除

* [x] ノード削除で関連 wire を削除（既存）
* [x] 端点 visual port を prune（接続から外れた vp を削除）
* [x] 残ノードに orphan visual port が残らない

## P11. 既存 Wiring 互換

* [x] `visual_port_id` の無い接続は従来どおりノード端に接続
* [x] legacy `_port_dot` は非表示でも参照可能（既存テスト）
* [x] 既存 add_connection 呼び出しの挙動を変えない

## P12. テスト

* [x] PartNode visual_port 追加/取得/削除/座標
* [x] `_finish_wire` で両端 visual port 生成・接続参照
* [x] 端点が visual port 座標・移動追従
* [x] export/import round-trip（visual_ports / visual_port_id / ID 衝突なし）
* [x] ノード削除で wire + orphan vp 削除
* [x] 整列・移動 API
* [x] 後方互換（vp 無し接続）
* [x] `_port_dot` が非表示（isVisible False）
* [x] `pytest tests/` 全通過

## P13. ドキュメント更新

* [x] `UI_SPEC_V05.md` に Dynamic Visual Port を追記
* [x] `ROADMAP6.md` / `CHECKLIST6.md` に本パッチ参照を追記
* [x] `HANDOFF.md` 更新

## P14. 実装後レビュー

* [x] hello.asm headless 検証（UART "Hi"）維持
* [x] 接続→保存→読込→端点追従 の headless スモーク
* [ ] GUI 目視確認（ヘッドレス環境のため未実施 — 報告に記載）
* [x] 作業報告

---

# 追加修正（実装後の目視確認で発見）

## B5. visual port dot がパーツ移動後に古い位置へ残る

* [x] 原因特定（boundingRect が dot を含まず外側描画 → ゴースト）
* [x] `PartNode.boundingRect` を `_NODE_PAD` 分拡張し dot を内包
* [x] visual port は scene 絶対座標で持たず side/offset から都度計算（既存方針を維持）
* [x] boundingRect が辺の dot を内包するテスト追加

## B6. wire を Dynamic Visual Port 接続では curved wire に変更

* [x] `ConnectionLine.update_curve`（cubic bezier・side 外向き制御点）を追加
* [x] `update_connections` を dynamic=curve / legacy=grid に分岐（`_is_dynamic_conn` / `_vp_side`）
* [x] Dynamic Visual Port のデータ構造は維持（捨てたのは grid 表示方式のみ）
* [x] legacy（vp 無し）接続は grid routing を維持（後方互換）
* [x] dynamic=curve / legacy≠curve / 端点=vp座標・移動追従のテスト追加

## B7. 追加レビュー

* [x] `pytest tests/` 全通過（615 件）
* [x] 右クリック接続 / Cancel Wire / Escape / 削除同期 / export-import が不変
* [x] hello.asm headless 検証維持
* [x] ROADMAP / CHECKLIST / HANDOFF 更新
