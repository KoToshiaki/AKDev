# PATCH_WIRING_V05 — Wiring Workflow Fix（チェックリスト）

> 設計書: `PATCH_WIRING_V05_ROADMAP.md`。
> 親フェーズ: `ROADMAP6.md` / `CHECKLIST6.md`（v0.5）。

---

## W0. 事前確認

* [x] 既存ドキュメント（CLAUDE.md / ROADMAP6 / CHECKLIST6 / HANDOFF / UI_SPEC_V05 / ERROR）を確認
* [x] wire モードの現状コード（`_start_wire` / `_cancel_wire` / `_finish_wire` / contextMenuEvent / set_mode）を精査
* [x] KI-1 の根本原因（入口 2 系統）を特定
* [x] 既存テスト（test_canvas_wire_mode / test_canvas_routing / test_ribbon）の前提を確認
* [x] パッチ ROADMAP / CHECKLIST を先に作成

## W1. wire モードの状態整理

* [x] `_begin_wire_from(node_id, port_name)` を新設（始点設定・preview・handles・装飾・emit を集約）
* [x] `_start_wire()` を `_begin_wire_from()` へ委譲（既存テスト互換）
* [x] armed / drawing サブ状態が `_wire_from` で判別できる

## W2. 右クリックメニュー整理

* [x] wire モード中の PartNode 右クリックに通常操作（Properties/開く/HDL/複製/削除）を併設
* [x] armed では「ここから接続を開始」、drawing では「ここに接続」を出す
* [x] 空白右クリックに Waypoint 追加（drawing 時）/ Wire Cancel を出す
* [x] 設計モードの右クリックメニューは変更しない
* [x] Properties 項目で対象ノードを選択し Properties パネルに反映

## W3. キャンセルの統一

* [x] Cancel Wire（リボン）で必ず design へ戻る
* [x] Escape で必ず design へ戻る
* [x] メニュー Wire Cancel で design へ戻る
* [x] preview / waypoints / handles / pending / 装飾を確実にクリア
* [x] キャンセル時に Log へ表示

## W4. 接続完了後の挙動

* [x] 接続完了後は design へ戻る（1 始点 1 接続）
* [x] `UI_SPEC_V05.md` 11-I に仕様決定を記録
* [x] 連続配線は将来拡張として記載

## W5. 状態可視化

* [x] ステータスバーに wire 状態を表示（文言調整）
* [x] Wiring タブの Wire Mode トグルで ON/OFF が分かる
* [x] wire 時に Canvas 枠をアクセント色にする

## W6. テスト

* [x] `_begin_wire_from` のテスト
* [x] `_cancel_wire` が全状態をクリアするテスト
* [x] Escape / Cancel Wire で design 復帰のテスト
* [x] Waypoint 追加・接続作成が壊れていないテスト
* [x] Canvas 装飾の on/off テスト
* [x] 既存 test_canvas_wire_mode / test_canvas_routing が通る
* [x] `pytest tests/` 全通過

## W7. 手動確認

* [x] hello.asm headless 検証（UART "Hi"）維持
* [x] armed → 接続を開始 → ここに接続 → design のフロー headless 確認
* [x] GUI 目視確認（ヘッドレス環境のため未実施 — 報告に記載）

## W8. ドキュメント / 実装後レビュー

* [x] `UI_SPEC_V05.md`（11-A / 11-G / 11-I）更新
* [x] `ROADMAP6.md` / `CHECKLIST6.md` に本パッチを参照追加
* [x] `ERROR.md` の KI-1 を解決済みに更新
* [x] `HANDOFF.md` 更新
* [x] 作業報告

---

# 追加修正（ユーザー目視確認で発見したバグ）

## W9. 追加バグ修正: ノード削除時の wire 削除（B1）

* [x] 削除処理を共通化（`_remove_node(node_id)` / `_delete_node(item)`）
* [x] ノード削除時に接続データ（`_connections`）から from/to 該当を削除
* [x] ConnectionLine アイテム（`_conn_items`）も同期削除
* [x] 対象ノードが wire 始点/pending の場合は Cancel Wire
* [x] Delete キー・右クリック削除（design/wire）・delete_selected を共通経路へ
* [x] export_canvas に孤立 wire が残らない
* [x] `tests/test_canvas_delete.py` 追加

## W10. 追加バグ修正: wire 端点座標の実ポート追従（B2）

* [x] wire の始点・終点を実ポート座標で上書き（grid snap しない）
* [x] 途中の BFS/waypoint は grid 維持
* [x] snap OFF パーツでも端点がポートに接する
* [x] パーツ移動後も端点が追従する
* [x] 既存 routing テストを壊さない（端点テストは正挙動へ更新）

## W11. 追加改善: Canvas 初期表示/読み込み感（B3）

* [x] `setSceneRect` で十分な広さを初期化（中ボタン Pan の可動域確保）
* [x] 起動時 `center_origin()` で原点中心表示
* [x] grid OFF でも原点十字を常時描画
* [x] Log / ステータスバーに "Canvas ready" を表示
* [x] 既存 Canvas Pan テストを壊さない

## W12. 参考 UI 調査反映（B4）

* [x] 一般的なノード UI（Unity Animator / Shader Graph / Blender / Unreal Blueprint）
  の挙動を `PATCH_WIRING_V05_ROADMAP.md` に調査メモとして反映
* [x] AKDev の当面方針（右クリック方式維持・内部はポート接続モデルへ）を記載

## W13. 追加テスト

* [x] ノード削除で接続 wire も消える（test_canvas_delete）
* [x] connections / 孤立接続 / export が孤立しない
* [x] snap OFF 端点がポート座標一致（test_canvas_routing）
* [x] パーツ移動後 端点追従（test_canvas_routing）
* [x] sceneRect / center_origin（test_canvas_routing）
* [x] `pytest tests/` 全通過（567 件）

## W14. 追加レビュー

* [x] 全削除経路で同一挙動を確認（headless スモーク）
* [x] hello.asm headless 検証維持（UART "Hi"）
* [x] `ERROR.md` / `HANDOFF.md` 更新
* [x] GUI 目視確認（ヘッドレス環境のため未実施 — 報告に記載）
