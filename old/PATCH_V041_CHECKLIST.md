# v0.4.1 Patch — CHECKLIST

> **注意:** このパッチは CLAUDE.md Rule 3（「実装前に CHECKLIST を作成する」）に反して、
> 実装後に後追いで記録したものです。
> 次回以降のパッチでは必ず実装前に ROADMAP / CHECKLIST を作成してください。

設計詳細は `PATCH_V041_ROADMAP.md` を参照。

---

## 0. 事前確認

* [x] v0.4 が pytest 505 件全通過で完了していることを確認する
* [x] HANDOFF.md に v0.4 完了内容が記録されていることを確認する
* [x] v0.4.1 パッチの対象問題（3 点）を特定する
  - 配線の角が不自然
  - 右クリック Pan がコンテキストメニューと競合
  - 公開前ドキュメント不足

---

## 1. 配線ルートの角修正

### 1.1 ConnectionLine.update_route の修正

* [x] `update_route()` を H-V 二重描画から直線 lineTo チェーンに変更する
  - 完了条件: `update_route([A, B, C])` → path.elementCount() == 3（MoveTo + 2×LineTo）
  - 完了条件: BFS が返すコーナー点列をそのまま繋ぐため余分な折れ線が出ない

### 1.2 ConnectionLine.update_line の修正

* [x] `update_line(p1, p2)` を明示的 H-V コーナー挿入に変更する
  - 完了条件: `[p1, QPointF(p2.x, p1.y), p2]` の 3 点で `update_route` を呼ぶ
  - 完了条件: `update_line` の elementCount() == 3

### 1.3 ポート位置ヘルパーの追加

* [x] `Canvas._from_port_pos(node_id)` を追加する
  - 完了条件: ノード右端中央 `(node.x + _NODE_W, node.y + _NODE_H/2)` を返す
  - 完了条件: node が存在しない場合は None を返す
* [x] `Canvas._to_port_pos(node_id)` を追加する
  - 完了条件: ノード左端中央 `(node.x, node.y + _NODE_H/2)` を返す
  - 完了条件: node が存在しない場合は None を返す

### 1.4 update_connections のポート位置対応

* [x] `update_connections()` をノード中心 → ポート位置（グリッドスナップ）に変更する
  - 完了条件: `_from_port_pos` / `_to_port_pos` を使う
  - 完了条件: 取得した位置をグリッドスナップ（`round(x/g)*g`）してから BFS に渡す
  - 完了条件: 接続線がノード右端から出て左端に入る見た目になる

### 1.5 Wire Mode Preview のポート位置対応

* [x] `_update_wire_preview()` を `_node_center` → `_from_port_pos` に変更する
  - 完了条件: プレビュー線がポート位置から出る

### 1.6 既存機能の保護

* [x] route / export_canvas / import_canvas の保存形式が壊れていないことを確認する
* [x] BFS 障害物回避（`_route_segment` / `_route_grid`）が変更されていないことを確認する
* [x] RouteHandle 頂点編集が正常に動作することを確認する

---

## 2. Canvas Pan 中ボタン化

### 2.1 イベントハンドラの変更

* [x] `mousePressEvent` の `RightButton` → `MiddleButton` に変更する
  - 完了条件: 中ボタン押下で `_pan_origin` がセットされる
  - 完了条件: 中ボタン押下で `ClosedHandCursor` がセットされる
* [x] `mouseMoveEvent` の `RightButton` → `MiddleButton` に変更する
  - 完了条件: 中ボタン保持中のみ Pan が動作する
* [x] `mouseReleaseEvent` の `RightButton` → `MiddleButton` に変更する
  - 完了条件: 中ボタン離でカーソルが戻り `_pan_origin` がリセットされる

### 2.2 contextMenuEvent の修正

* [x] `contextMenuEvent` の `_panned` ガード（右クリックメニュー抑制）を削除する
  - 完了条件: `_panned` が True でも右クリックメニューが表示される
  - 完了条件: wire mode の右クリック waypoint 追加が正常に動作する

### 2.3 既存機能の保護

* [x] 右クリック → コンテキストメニューが正常に動作する（design mode）
* [x] wire mode → 右クリック → PartNode → 「ここに接続」/「キャンセル」が動作する
* [x] wire mode → 右クリック → 空白 → waypoint 追加が動作する
* [x] 左クリック選択・移動・ラバーバンドが壊れていないことを確認する
* [x] ホイールズームが壊れていないことを確認する

---

## 3. 公開前ドキュメント追加

### 3.1 docs/QUICKSTART.md の作成

* [x] `docs/` ディレクトリを作成する
* [x] `docs/QUICKSTART.md` を新規作成する
  - 完了条件: 環境準備の手順が書かれている
  - 完了条件: 起動方法が書かれている
  - 完了条件: New Project → パーツ配置 → hello.asm 記述 → Build → Run の手順が書かれている
  - 完了条件: UART に "Hi" が出ることの確認手順が書かれている
  - 完了条件: よくある詰まりが書かれている

### 3.2 docs/USER_GUIDE.md の作成

* [x] `docs/USER_GUIDE.md` を新規作成する
  - 完了条件: 画面構成が説明されている
  - 完了条件: Parts Library の使い方が説明されている
  - 完了条件: Canvas 操作（選択・移動・右クリックメニュー・Pan・Zoom）が説明されている
  - 完了条件: Wire Mode（接続作成・waypoint・RouteHandle）が説明されている
  - 完了条件: Build / Run / Step / Reset が説明されている
  - 完了条件: UART Console / Register View / Bus Trace / Memory Viewer が説明されている
  - 完了条件: PC ハイライト / Canvas Signal Overlay が説明されている
  - 完了条件: プロジェクト保存・読み込みが説明されている
  - 完了条件: 既知の制限が記載されている

### 3.3 README.md の更新

* [x] `README.md` に `docs/QUICKSTART.md` へのリンクを追加する
* [x] `README.md` に `docs/USER_GUIDE.md` へのリンクを追加する
* [x] v0.4.1 時点でできることを整理して記載する
* [x] Canvas 操作（中ボタンドラッグ = Pan）を正しく記載する

---

## 4. テスト確認

### 4.1 既存テストの更新

* [x] `tests/test_canvas_pan.py` を MiddleButton 対応に更新する
  - `_Press` / `_Move` / `_Release` クラスのデフォルトボタンを `MiddleButton` に変更
* [x] `tests/test_canvas_connection_lines.py` の `test_conn_line_endpoint_is_node_center` を更新する
  - テスト名を `test_conn_line_endpoint_is_port_position` に変更
  - 期待値をノード中心 → ポート位置（グリッドスナップ）に変更
* [x] `tests/test_canvas_wire_mode.py` の `test_update_route_manhattan_midpoint` を更新する
  - `update_route` の新挙動（直線）に合わせてリネーム・修正
  - `update_line` の H-V 確認テストを新規追加

### 4.2 新規テストの追加

* [x] `tests/test_canvas_routing.py` に以下を追加する（9 件）
  - `test_update_route_straight_segments_count` — 3 点で elementCount == 3
  - `test_update_route_two_points_straight` — 2 点で elementCount == 2
  - `test_update_line_hv_corner_element_count` — update_line で 3 elements
  - `test_update_line_corner_x_matches_end` — コーナーの x が end.x と一致
  - `test_update_line_corner_y_matches_start` — コーナーの y が start.y と一致
  - `test_update_connections_starts_at_right_edge` — 線の始点がノード右端付近
  - `test_update_connections_path_ends_near_left_edge` — 線の終点がノード左端付近
  - `test_from_port_pos_returns_right_edge` — `_from_port_pos` の返り値確認
  - `test_to_port_pos_returns_left_edge` — `_to_port_pos` の返り値確認
  - `test_from_port_pos_missing_node_returns_none` — 欠損ノードで None
  - `test_to_port_pos_missing_node_returns_none` — 欠損ノードで None
* [x] `tests/test_canvas_pan.py` に 1 件追加する
  - `test_middle_pan_does_not_block_context_menu` — _panned ガード廃止の確認

### 4.3 pytest 全件通過確認

* [x] `pytest tests/` を実行して全件通過を確認する
  - 完了条件: 518 件 PASSED（0 件 FAILED）

---

## 5. ドキュメント確認（CLAUDE.md Rule 15）

* [x] `PATCH_V041_ROADMAP.md` を読み返し、文章の欠けがないことを確認する
* [x] `PATCH_V041_CHECKLIST.md` を読み返し、実装内容と矛盾がないことを確認する
* [x] `docs/QUICKSTART.md` を読み返し、手順が完結していることを確認する
* [x] `docs/USER_GUIDE.md` を読み返し、全機能がカバーされていることを確認する
* [x] `README.md` を読み返し、リンクが存在し内容が正確であることを確認する
* [x] `CHECKLIST5.md` の v0.4.1 セクションと本ファイルが矛盾していないことを確認する
* [x] `HANDOFF.md` の v0.4.1 記録と実装内容が一致していることを確認する

---

## 6. v0.4.1 完了条件

* [x] pytest 518 件全通過（v0.4 完了時 505 件 → +13 件）
* [x] 配線がパーツ右端から出て左端に入る自然な H/V 形で表示される
* [x] 中ボタンドラッグで Canvas Pan できる（ClosedHandCursor 付き）
* [x] 右クリックメニューが中ボタンパン後も正常に動作する
* [x] wire mode の右クリック操作が正常に動作する
* [x] `docs/QUICKSTART.md` が存在し、5 分で hello.asm を動かせる内容になっている
* [x] `docs/USER_GUIDE.md` が存在し、全機能を説明している
* [x] `README.md` が v0.4.1 対応で、QUICKSTART / USER_GUIDE にリンクしている
* [x] `PATCH_V041_ROADMAP.md` が存在し、パッチ目的・方針・完了条件が記録されている
* [x] `PATCH_V041_CHECKLIST.md` が存在し、実装内容がチェックリスト化されている

---

## v0.4.1 完了 ✅（2026-05-30）

pytest 518 件全通過。配線角修正・中ボタン Pan・公開前ドキュメント追加・ROADMAP/CHECKLIST 後追い記録。
