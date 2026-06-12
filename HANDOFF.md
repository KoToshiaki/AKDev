# AKDev 引き継ぎメモ

更新日: 2026-06-13（PATCH_VISUAL_PORT_MOVE_V05 — Visual Port Move）

---

## 現在の状況（PATCH_VISUAL_PORT_MOVE_V05 — Visual Port Move）

**フェーズ: v0.5（進行中）。visual port を Alt + 左ドラッグで辺上に移動できるようにした。**

### 完了した作業

| 項目 | 内容 |
|---|---|
| Alt + 左ドラッグ移動 | visual port 上で Alt + 左ドラッグ → port move 開始。Alt なしは従来の port-drag connect。`Canvas._port_move`（node_id / vp_id / original・current side+offset）+ `_start/_update/_finish/_cancel_port_move` |
| 辺拘束 | `PartNode.edge_from_local()` がマウスローカル座標から最近辺の side と clamp 済み offset を返す。`node_size()`（固定 `_NODE_W`/`_NODE_H`、将来サイズ変更の hook）。保存は side + offset のまま（scene 絶対座標なし）|
| wire 追従 | `_update_port_move` が side/offset 更新 + `update_connections()`。curved wire 端点が新位置に一致。**fan-out 共有 vp を動かすと参照する全 wire が追従** |
| 確定 / 取消 | release で確定、Esc / 右クリックで元の side/offset へ復元（`_cancel_port_move`）|
| locked | locked vp は移動開始しない（ログ "Visual port is locked" 1 行のみ）|
| 表示 | 移動中 vp は専用色リング（`_PORT_MOVE_COLOR`）で最強強調。優先度 moving > hover > normal。drop highlight とは別状態 |
| 互換 | port-drag connect / wire 選択・削除 / 右クリック接続 / curved wire / hover / export-import は不変 |

### 作成したパッチ文書

- `PATCH_VISUAL_PORT_MOVE_V05_ROADMAP.md` / `PATCH_VISUAL_PORT_MOVE_V05_CHECKLIST.md`

### テスト結果

- `pytest tests/` **685 件全通過**（PATCH_WIRE_SELECT_DELETE_V05 完了時 668 → +17）
- 新規 `tests/test_visual_port_move_v05.py`（17 件）
- 既存 668 件は無改変で通過
- headless 検証: Alt → move / Alt なし → port-drag ✅ / locked は不可 ✅ / side/offset・scene 座標更新 ✅ / wire 端点・fan-out 全 wire 追従 ✅ / release 確定・Esc/右クリックで復元 ✅ / move 中 node/wire 選択が誤発火しない ✅ / export-import で移動後 side/offset 維持 ✅

### 互換性メモ

- 保存は visual port 移動時に自動 persist せず、ノード移動・wire 削除と同じく保存時の
  `export_parts`/`export_canvas` に委ねる（MainWin の保存導線は変更していない）。

### まだ残っている問題（将来）

- visual port の通常左ドラッグ移動 / 複数選択 / 削除 UI / rename は未実装。
- wire 色変更 UI / wire ラベル / 接続可否の型判定（constraint）は未実装。
- Part Visual サイズ変更（`node_size()` を可変化）は別パッチ。
- legacy `_port_dot` の完全削除 / `ui/canvas.py` 分割は将来。
- GUI 目視確認はヘッドレス環境のため未実施（下記「UI 確認点」参照）。

### UI 上でユーザーが確認すべき点

- visual port を Alt + 左ドラッグするとリングが付き、辺に沿って動くか。接続 wire が追従するか。
- Alt なしの左ドラッグは従来どおり接続線（port-drag）が出るか。
- マウスを離すと位置が確定するか。Esc / 右クリックで元の位置に戻るか。
- locked にした visual port は Alt + ドラッグしても動かないか。
- fan-out（同じ port から複数 wire）の port を動かすと全 wire が追従するか。

### 次に行うべき作業

- ユーザー判断: wire 色変更 UI／Port Detail パネル／Part Visual サイズ変更／UI ラフ受領 のいずれへ進むか

---

## 現在の状況（PATCH_WIRE_SELECT_DELETE_V05 — Wire Select & Delete）

**フェーズ: v0.5（進行中）。作成済み wire を選択・削除できるようにした。**

### 完了した作業

| 項目 | 内容 |
|---|---|
| wire 選択 | design mode の左クリックで wire 選択（`Canvas._selected_conn_id` / `_set_selected_conn`）。`ConnectionLine.set_selected/is_selected`。visual port / PartNode クリックは従来優先、空白で解除 |
| 表示優先度 | `ConnectionLine._apply_pen()` を **selected > active > hover > normal** に拡張。selected は白・最太で signal overlay（active）と重なっても判別可能 |
| 削除 API | `Canvas._remove_connection(conn_id)` 新設。data + ConnectionLine 除去、selected/hover 解除、`_prune_orphan_visual_ports()`、`update_connections()`。**fan-out 元 vp が他 conn から参照されていれば残す** |
| Delete キー | 選択 wire（かつ port-drag でない）→ wire 削除、なければ従来のノード削除 |
| 右クリック | wire 近くで「Delete Wire」メニュー。PartNode 上 / port-drag 中 / wire mode は従来どおり |
| 整合 | `import_canvas`(clear) と `_remove_node`（選択 wire がノード削除で消えた場合）で選択を解除 |
| 互換 | 右クリック接続・port-drag 接続・curved wire・hover feedback・signal overlay・export/import は不変 |

### 作成したパッチ文書

- `PATCH_WIRE_SELECT_DELETE_V05_ROADMAP.md` / `PATCH_WIRE_SELECT_DELETE_V05_CHECKLIST.md`

### テスト結果

- `pytest tests/` **668 件全通過**（PATCH_WIRE_HOVER_FEEDBACK_V05 完了時 649 → +19）
- 新規 `tests/test_wire_select_delete_v05.py`（19 件）
- 既存 649 件は無改変で通過（`set_active`/`set_hovered` の pen 挙動を優先度拡張後も維持）
- headless 検証: クリック選択・選択移動・空白で解除 ✅ / Delete で wire 削除・選択なしはノード削除・port-drag 中は無効 ✅ / 削除で data+item 消去・orphan prune・共有 fan-out vp 残存 ✅ / selected > active > hover 優先度 ✅ / 右クリック接続・port-drag 接続・export-import 不変 ✅

### 互換性メモ

- 保存は wire 削除時に自動 persist せず、ノード削除と同じく保存時の `export_parts`/`export_canvas` に委ねる（MainWin の既存導線を変更していない）。

### まだ残っている問題（将来）

- wire Properties / 色変更 UI / ラベル / 複数 wire 選択 / Undo・Redo / z-order 調整は未実装。
- visual port の対話ドラッグ移動 / 接続可否の型判定（constraint）は未実装。
- legacy `_port_dot` の完全削除は将来。
- GUI 目視確認はヘッドレス環境のため未実施（下記「UI 確認点」参照）。

### UI 上でユーザーが確認すべき点

- wire を左クリックすると白く太く強調されるか。別 wire / 空白クリックで選択が移る・消えるか。
- 選択中 wire で Delete を押すとその wire だけ消えるか。選択がなければノードが消えるか。
- wire を右クリックすると「Delete Wire」が出て削除できるか。PartNode 右クリックは従来メニューのままか。
- Run 中の signal overlay（青く光る）と選択中 wire が重なっても、選択が判別できるか。

### 次に行うべき作業

- ユーザー判断: wire 色変更 UI／visual port 対話ドラッグ移動／UI ラフ受領 のいずれへ進むか

---

## 現在の状況（PATCH_WIRE_HOVER_FEEDBACK_V05 — Hover Feedback）

**フェーズ: v0.5（進行中）。Wiring / Port Drag Connect に hover feedback（視覚のみ）を追加。**

### 完了した作業

| 項目 | 内容 |
|---|---|
| visual port hover | port に近づくと明るく + 白枠 + 拡大表示。`Canvas._hover_vp` + `PartNode.set_hover_port/hover_port`。`mouseMoveEvent`（ボタン非押下時）で `_visual_port_at` から更新、`leaveEvent` で解除 |
| wire hover | wire に近づくと太く + 明るく。`ConnectionLine.set_hovered/is_hovered`。pen を `_apply_pen()` で集中管理し signal overlay（active）と両立（**active 優先**）。`Canvas._connection_at`（path 距離判定）/ `_set_hover_conn` |
| drop highlight | port-drag 中、カーソル下の**別ノード**をアクセント色（#3B82F6）外枠で候補表示。`Canvas._hover_drop_node_id` + `PartNode.set_drop_highlight`。`_update_drop_target` が同一ノードを除外、`_cancel_port_drag` が finish/cancel 両方で必ず解除 |
| ログ補助 | port-drag 開始時に 1 行のみ（mouseMove ではログしない）|
| 互換 | 右クリック接続・port-drag 接続・curved wire・export/import・signal overlay は不変 |

### 作成したパッチ文書

- `PATCH_WIRE_HOVER_FEEDBACK_V05_ROADMAP.md` / `PATCH_WIRE_HOVER_FEEDBACK_V05_CHECKLIST.md`

### テスト結果

- `pytest tests/` **649 件全通過**（PATCH_PORT_DRAG_CONNECT_V05 完了時 630 → +19）
- 新規 `tests/test_wire_hover_feedback_v05.py`（19 件）
- 既存 630 件は無改変で通過（`set_active` の pen 復元挙動を `_apply_pen` リファクタ後も維持）
- headless 検証: visual port hover 更新/解除 ✅ / wire hover pen 変化・active 優先 ✅ / drop highlight 別ノード ON・同一ノード除外・finish/cancel で解除 ✅ / port-drag 接続・右クリック接続・export-import 不変 ✅

### まだ残っている問題（将来）

- wire 選択 / Delete Wire / visual port の対話ドラッグ移動 / 空ポートからのドラッグ開始は未実装。
- 接続可否の厳密な型判定（Connection constraint）は未実装。
- legacy `_port_dot` の完全削除は将来。
- GUI 目視確認はヘッドレス環境のため未実施（下記「UI 確認点」参照）。

### UI 上でユーザーが確認すべき点

- visual port にカーソルを近づけると port が明るく拡大するか。
- wire にカーソルを近づけると太く明るくなるか。Run 中の signal overlay（active）と重なっても破綻しないか。
- visual port からドラッグ中、別パーツに乗るとアクセント色枠が出るか。元パーツには出ないか。
- ドラッグを離す / Esc / 右クリックで枠が確実に消えるか。

### 次に行うべき作業

- ユーザー判断: wire 選択 + Delete Wire／visual port 対話ドラッグ移動／UI ラフ受領 のいずれへ進むか

---

## 現在の状況（PATCH_PORT_DRAG_CONNECT_V05 — Port Drag Connect）

**フェーズ: v0.5（進行中）。visual port からドラッグして別ノードへ接続する操作を追加。**

### 完了した作業

| 項目 | 内容 |
|---|---|
| port-drag 開始 | visual port 上の左 press で開始（幾何ヒットテスト `_visual_port_at`）。`accept` し super を呼ばずノード移動を抑止 |
| preview | カーソルへ向かう **curved 破線** preview（source port の side 外向き制御点）|
| 接続確定 | 別ノードで release → target に新 vp 生成 + `add_connection(from_vp=既存, to_vp=新)`。Dynamic Visual Port + curved wire + export/import に乗る |
| キャンセル | 同一ノード / target 無し / Esc / 右クリック（ドラッグ中）|
| 互換 | 既存の右クリック接続・中ボタン pan・wire mode・Delete・削除同期・export-import は不変 |

### 作成したパッチ文書

- `PATCH_PORT_DRAG_CONNECT_V05_ROADMAP.md` / `PATCH_PORT_DRAG_CONNECT_V05_CHECKLIST.md`

### テスト結果

- `pytest tests/` **630 件全通過**（PATCH_WIRING_PORTS_V05 追加修正完了時 615 → +15）
- 新規 `tests/test_port_drag_connect_v05.py`（15 件）
- 既存 615 件は無改変で通過
- headless スモーク: 右クリックで vp 生成 → port-drag で別ノード接続（source vp 再利用・target 新 vp・curved）✅ / round-trip ✅ / cancel ✅ / hello.asm UART "Hi" ✅

### まだ残っている問題（将来）

- 接続先候補の hover ハイライト、visual port の対話ドラッグ移動、空ポートからのドラッグ開始。
- legacy `_port_dot` の完全削除。
- GUI 目視確認はヘッドレス環境のため未実施。

### 次に行うべき作業

- ユーザー判断: hover ハイライト／visual port 対話ドラッグ移動／UI ラフ受領 のいずれへ進むか

---

## 現在の状況（PATCH_WIRING_PORTS_V05 追加修正）

**フェーズ: v0.5（進行中）。Dynamic Visual Port の目視確認バグ 2 件を追加修正。**

### 完了した追加修正

| # | 内容 |
|---|---|
| B5 | visual port dot がパーツ移動後に古い位置へ残るゴーストを修正。`PartNode.boundingRect` を `_NODE_PAD` 分拡張し、辺上の dot を item bounds に内包（移動時に旧 dot がクリアされる）。visual port は side/offset から都度 scene 座標計算（絶対座標で持たない方針を維持）|
| B6 | Dynamic Visual Port 接続を **curved wire**（`ConnectionLine.update_curve`、cubic bezier・side 外向き制御点）で描画。`update_connections` を dynamic=curve / legacy=grid に分岐。データ構造は維持し、捨てたのは Dynamic 接続への grid/Manhattan 表示のみ。legacy（vp 無し）接続は grid 維持 |

### テスト結果（追加修正）

- `pytest tests/` **615 件全通過**（Dynamic Visual Port 導入時 610 → +5）
- `tests/test_wiring_ports_v05.py` に boundingRect 被覆・dynamic=curve・legacy≠curve・端点=vp座標・移動追従 を追加（計 28 件）
- headless スモーク: boundingRect が辺 dot を内包 ✅ / dynamic 接続が cubic curve（4要素）✅ / 端点=vp 座標・移動追従 ✅ / legacy 非 curve ✅ / hello.asm UART "Hi" ✅
- 右クリック接続 / Cancel Wire / Escape / 削除同期 / export-import は不変

### まだ残っている問題（将来）

- ポートからドラッグ接続開始、接続先候補 hover ハイライト、visual port の対話ドラッグ移動。
- legacy `_port_dot` の完全削除。
- GUI 目視確認はヘッドレス環境のため未実施。

### 次に行うべき作業

- ユーザー判断: 対話ドラッグ移動／ポートドラッグ接続／UI ラフ受領 のいずれへ進むか

---

## 現在の状況（PATCH_WIRING_PORTS_V05 — Dynamic Visual Port）

**フェーズ: v0.5（進行中）。Wiring を既存ノードエディタに寄せ、接続点をデータ化。**

### 完了した作業

| 項目 | 内容 |
|---|---|
| Dynamic Visual Port | パーツは初期 0 ポート。wire 接続時に接点へ visual port を生成（`PartNode._visual_ports` + `add/get/remove/set/visual_port_pos`、paint で小円描画）|
| logical / visual 分離 | 接続 from/to に `visual_port_id` + `logical_port` を追加（`port` は互換維持）|
| 端点解決 | `_conn_endpoint` で visual port 座標を使用、無ければ従来ノード端へ fallback。ノード移動で追従 |
| 生成 | `_create_visual_port`（辺ごとに自動スタック）、`_finish_wire` が両端に生成 |
| 移動 / 整列 | `set_visual_port_offset` / `set_visual_port_side` / `arrange_visual_ports`（locked 尊重）+ 設計右クリック「ポートを整列」|
| 保存 | export_parts に `visual_ports`（0 個は省略）、import で復元 + `_vp_seq` 巻き戻し防止 |
| 削除同期 | ノード削除で関連 wire 削除（既存）+ `_prune_orphan_visual_ports` で接続から外れた vp を削除 |
| legacy 互換 | `_port_dot` は `setVisible(False)` で残す（sim/`_on_port_click`・既存テスト用）。vp 無し接続は従来どおり |

### 作成したパッチ文書

- `PATCH_WIRING_PORTS_V05_ROADMAP.md` / `PATCH_WIRING_PORTS_V05_CHECKLIST.md`

### テスト結果

- `pytest tests/` **610 件全通過**（PATCH_PART_VISUAL_V05 完了時 587 → +23）
- 新規 `tests/test_wiring_ports_v05.py`（23 件）
- 既存 587 件は無改変で通過（後方互換・`_port_dot` 非表示でも維持）
- headless スモーク: 初期0ポート/legacy dot非表示 ✅ / 接続で両端 vp 生成・conn 参照 ✅ / 端点=vp 座標・移動追従 ✅ / 保存→読込 round-trip ✅ / ノード削除で orphan vp prune ✅ / hello.asm UART "Hi" ✅

### まだ残っている問題

- 将来: ポートからドラッグして接続開始、接続先候補の hover ハイライト、visual port の対話ドラッグ移動（本パッチは API + 整列のみ）。
- legacy `_port_dot` は非表示で残置（完全削除は将来）。
- GUI 目視確認はヘッドレス環境のため未実施。

### 次に行うべき作業

- ユーザー判断: ポートドラッグ接続の試作／visual port 対話ドラッグ／UI ラフ受領 のいずれへ進むか

---

## 現在の状況（PATCH_PART_VISUAL_V05 — Part Visual 第1段階）

**フェーズ: v0.5（進行中）。Part Visual 編集の第1段階（色変更）を実装。**

### 完了した作業

| 項目 | 内容 |
|---|---|
| PartNode 色 | `_color` + `set_color()/color()`、`paint()` で instance_color をカテゴリ色より優先 |
| Canvas API | `set_node_color(node_id, hex)`、`export_parts`/`import_parts` で `instance_color` を round-trip（色設定時のみ保存）|
| PropPanel | 「Visual」セクション + 100 色パレット（10×10、コード内生成）+「Default color」。`color_changed(node_id, hex)` シグナル |
| MainWin | `color_changed` → `set_node_color` → 開いていれば `_persist_system()` |

### 作成したパッチ文書

- `PATCH_PART_VISUAL_V05_ROADMAP.md` / `PATCH_PART_VISUAL_V05_CHECKLIST.md`

### テスト結果

- `pytest tests/` **587 件全通過**（PATCH_WIRING_V05 追加修正完了時 567 → +20）
- 新規 `tests/test_part_visual_v05.py`（20 件）
- headless スモーク: パレットで色適用 ✅ / export・import round-trip ✅ / Default で既定復帰 ✅ / palette 100 色 ✅ / hello.asm UART "Hi" ✅

### まだ残っている問題

- 第2段階（Canvas のサイズ変更ハンドル）は未着手（別パッチ候補）。
- GUI 目視確認はヘッドレス環境のため未実施。
- part.json の `color` 既定値対応・配線色変更 UI・Run Status・Error タブは未実装。

### 次に行うべき作業

- ユーザー判断: Part Visual 第2段階（サイズ）／part.json color 対応／UI ラフ受領 のいずれへ進むか

---

## 現在の状況（PATCH_WIRING_V05 追加修正）

**フェーズ: v0.5（進行中）。PATCH_WIRING_V05 の追加修正として目視確認バグ 3 件を修正。**

### 完了した作業（追加修正 B1〜B3 + B4 調査）

| # | 内容 |
|---|---|
| B1 | ノード削除時に接続 wire も削除。`_remove_node()` を単一窓口にし全削除経路を集約（Delete キー / 右クリック design・wire / `delete_selected`）。接続データ・ConnectionLine・wire/pending を同期削除し export に孤立を残さない |
| B2 | wire 端点を実ポート座標で上書き（grid に丸めない）。snap OFF パーツでも隙間なく接続、移動追従。BFS/waypoint は grid 維持 |
| B3 | `setSceneRect(4000²)` で Pan 可動域確保、起動時 `center_origin()`、grid OFF でも原点十字常時描画、"Canvas ready" を Log/ステータスバー表示 |
| B4 | 既存ノード UI（Unity/Blender/Unreal）の挙動を `PATCH_WIRING_V05_ROADMAP.md` 9 に調査メモ反映。当面は右クリック方式維持＋内部はポート接続モデルへ |

### 変更ファイル（追加修正）

- `ui/canvas.py`（`_remove_node`/`_delete_node`/`center_origin`、`update_connections` 端点上書き、`setSceneRect`、GridScene 原点十字）
- `ui/win.py`（`_arrange_initial_layout` に center+ready）
- `tests/test_canvas_delete.py`（新規 13 件）/ `tests/test_canvas_routing.py`（B2/B3 6 件追加）/ `tests/test_canvas_connection_lines.py`（端点テストを正挙動へ更新）

### テスト結果（追加修正）

- `pytest tests/` **567 件全通過**（PATCH_WIRING_V05 完了時 551 → +16）
- headless スモーク: B1 削除で wire/export 同期 ✅ / B2 端点 (153,35)・(317,71) 実ポート一致 ✅ / B3 sceneRect 4000² ✅ / hello.asm UART "Hi" ✅

### まだ残っている問題

- GUI 起動の目視確認はヘッドレス環境のため未実施。
- ポートからドラッグ接続・接続可否ハイライト・連続配線は将来拡張（B4 方針として記載）。
- Part Visual 編集・Run Status 表示・Error タブ・配線色変更 UI は方針記載のみ（未実装）。

### 次に行うべき作業

- ユーザー判断: ポートドラッグ接続の試作／Part Visual 第1段階（色変更）／UI ラフ受領 のいずれへ進むか

---

## 現在の状況（PATCH_WIRING_V05 — Wiring Workflow Fix）

**フェーズ: v0.5（進行中）。Patch 2 で残った KI-1 を別パッチ PATCH_WIRING_V05 で解決。**

### 完了した作業（PATCH_WIRING_V05）

| 項目 | 内容 |
|---|---|
| wire 状態整理 | armed（始点未選択）/ drawing（始点選択済）の 2 サブ状態に整理。`_begin_wire_from()` 新設、`_start_wire()` は委譲 |
| 右クリック整理 | wire モード中の右クリックに通常操作（Properties/開く/HDL/複製/削除）を併設。armed=「ここから接続を開始」、drawing=「ここに接続」 |
| キャンセル統一 | Cancel Wire / Escape / メニュー Wire Cancel を `_cancel_wire()` で統一。preview/waypoints/handles/pending/装飾を確実クリア |
| フロー仕様 | 接続完了後は design へ戻る（1 始点 1 接続）。連続配線は将来。`UI_SPEC_V05.md` 11-I に記録 |
| 状態可視化 | ステータスバー文言調整 + Wiring トグル checked + Canvas 枠をアクセント色（`_refresh_wire_decoration`）|
| KI-1 | `ERROR.md` で解決済みに更新 |

### 作成したパッチ文書

- `PATCH_WIRING_V05_ROADMAP.md` / `PATCH_WIRING_V05_CHECKLIST.md`

### テスト結果（PATCH_WIRING_V05）

- `pytest tests/` **551 件全通過**（Patch 2 完了時 534 件 → +17 件）
- 新規: `tests/test_wiring_v05.py`（17 件）
- 既存 `test_canvas_wire_mode.py` / `test_canvas_routing.py` は変更なしで通過
- headless スモーク: トグル→armed→接続を開始→ここに接続→design 復帰 ✅ / Escape 解除 ✅ / Canvas 枠装飾 ON/OFF ✅ / hello.asm UART "Hi" ✅

### まだ残っている問題

- 連続配線（接続後も wire を継続して複数本引く）は将来拡張（本パッチ対象外）。
- GUI 起動の目視確認はヘッドレス環境のため未実施。
- Part Visual 編集・Run Status 表示・Error タブ・配線色変更 UI は方針記載のみ（未実装）。

### 次に行うべき作業

- ユーザー判断: Part Visual 第1段階（色変更）／連続配線モード／UI ラフ受領 のいずれへ進むか
- UI ラフ受領 → `UI_SPEC_V05.md` セクション 12 反映

---

## 現在の状況（v0.5 UI Prototype Patch 2 — User Review Fixes）

**フェーズ: v0.5 UI Polish & Usability（進行中）。Patch 1 をユーザー目視レビューし、Patch 2 で反映。**

### 完了した作業（Patch 2）

| # | 項目 | 内容 |
|---|---|---|
| A | Project タブ削除 | リボンから撤去。New/Open/Save/Save As は File メニューに残存 |
| B | リボンボタン幅縮小 | `ui/ribbon.py` を自然幅・左詰め・余白縮小に変更（min width 96→0, height 48→28）|
| C | Parts タブ再設計 | Add Part/Clone/Delete/Properties を撤去。Parts Library トグル + Import Part…(disabled+説明) + Open Parts Folder |
| D | Parts Library 初期非表示 | `_parts_lib_dock.hide()`。Parts タブのトグルで表示 |
| E | Part Visual 編集方針 | `UI_SPEC_V05.md` 11-D に記載（実装は次パッチ）|
| F | Wiring 最小修正 | Cancel Wire 強化 + Escape キャンセル + ステータスバー表示。右クリック占有は KI-1 記録 |
| G | Run 確認 | `UI_SPEC_V05.md` 11-F に Status 候補記載（実装は将来）|
| H | View タブ整理 | Grid 起動時 OFF、Zoom In/Out をリボンから撤去（ホイールズーム維持、Reset/Fit 残存）|
| I | Log/Console 分離 | Log dock 改称 + Console dock 新規追加。Run/UART 出力を Console へ |

### テスト結果（Patch 2）

- `pytest tests/` **534 件全通過**（Patch 1 完了時 532 件 → +2 件）
- 更新: `tests/test_ribbon.py`（5タブ・Parts/View/Debug・ボタンサイズ）/ `tests/test_dock_visibility.py`（Parts Library 初期非表示）
- headless スモーク: リボン 5 タブ ✅ / Grid OFF ✅ / Parts Library 非表示 ✅ / Cancel Wire ✅ / Escape ✅ / hello.asm UART "Hi" ✅ / Console 出力 ✅

### まだ残っている問題

- **KI-1（Wiring 右クリック占有）**: 未解決。`ERROR.md` に記録。本パッチでは抜ける導線のみ確保。本質修正は別パッチ **`PATCH_WIRING_V05`**（未作成・提案中）。
- GUI 起動の目視確認はヘッドレス環境のため未実施。
- Part Visual 編集・Run Status 表示・Error タブは方針記載のみ（未実装）。

### 次に行うべき作業

- ユーザー判断: `PATCH_WIRING_V05` を起こすか／Part Visual 第1段階（色変更）に進むか
- UI ラフ受領 → `UI_SPEC_V05.md` セクション 12 反映

---

## 現在の状況（v0.5 UI Prototype Patch 1）

**フェーズ: v0.5 UI Polish & Usability（進行中）。最初の実装として UI Prototype Patch を実施。**

完成版 UI ではなく、使いやすい UI の方向性を確認するためのたたき台。

### 完了した作業

| 項目 | 内容 |
|---|---|
| Hub 画面 | `ui/hub.py` 新規。起動時の入口（New / Open / Recent枠 / Templatesカード / Docs導線）。New/Open はシグナルで既存処理へ接続 |
| 入口遷移 | `main.py` で Hub 先行表示 → New/Open で Workspace へ遷移 |
| Workspace 初期表示整理 | `_arrange_initial_layout()` で Log/Console と Properties を前面化（Canvas主役） |
| Ribbon 再構成 | File/Build-Run/View/Tools の 4 タブ → **Project / Parts / Wiring / Run / View / Debug** の 6 タブ |
| Debug パネル整理 | デバッグパネルのトグルを Debug タブへ集約 |
| Visual Identity 土台 | `ui/theme.py` 新規。アクセントカラー `#3B82F6`、枠線軽減、hover/selected/active、QSS を `main.py` で全体適用 |
| Canvas 公開メソッド | `delete_selected()` / `clone_selected()` を `ui/canvas.py` に追加（Parts タブ Delete/Clone から利用） |

### テスト結果

- `pytest tests/` **532 件全通過**（v0.4.1 完了時 518 件 → +14 件）
- 新規: `tests/test_hub.py`（7 件）/ `tests/test_theme.py`（5 件）
- 更新: `tests/test_ribbon.py`（4 タブ → 6 タブ構成に追従）
- hello.asm headless 検証: UART "Hi" ✅ / HALT ✅

### 既知の制約・未確認

- GUI 起動の目視確認はヘッドレス環境のため未実施（headless スモーク + pytest で代替）
- Debug パネルの**完全な初期非表示**は未実施。`test_dock_visibility` の「可視＝checked」契約を維持するため、今回は前面化のみ（完全非表示は UI ラフ確定後）
- Recent Projects / Templates は枠・カードのみで実機能なし（プロトタイプ）

### 次に行うべき作業

- ユーザーの **UI ラフ受領 → `UI_SPEC_V05.md` セクション 12 へ反映 → 実装範囲確定**
- ラフ確定後に Debug パネル初期非表示・Port Detail・配線色変更 UI の実装可否を決定

---

## ドキュメント体系

| ファイル | 役割 |
|---|---|
| `ROADMAP6.md` | v0.5 の設計書（**現在のフェーズ**） |
| `CHECKLIST6.md` | v0.5 のチェックリスト（**現在のフェーズ**） |
| `old/ROADMAP5.md` | v0.4 Visual Debug Canvas の設計書（完了・アーカイブ） |
| `old/CHECKLIST5.md` | v0.4 Visual Debug Canvas のチェックリスト（完了・アーカイブ） |
| `old/PATCH_V041_ROADMAP.md` | v0.4.1 Patch の設計書（完了・アーカイブ） |
| `old/PATCH_V041_CHECKLIST.md` | v0.4.1 Patch のチェックリスト（完了・アーカイブ） |
| `old/ROADMAP4.md` | v0.3 Project & Target Foundation の設計書（完了・アーカイブ） |
| `old/CHECKLIST4.md` | v0.3 Project & Target Foundation のチェックリスト（完了・アーカイブ） |
| `HANDOFF.md` | このファイル — セッション間引き継ぎ |
| `old/ROADMAP3.md` | v0.2 Workspace UI Refinement の計画（完了・アーカイブ） |
| `old/CHECKLIST3.md` | v0.2 UI 改善のチェックリスト（完了・アーカイブ） |
| `old/PATCH_PROJECT_DIALOG_ROADMAP.md` | Project Dialog パッチ設計書（完了・アーカイブ） |
| `old/PATCH_PROJECT_DIALOG_CHECKLIST.md` | Project Dialog パッチチェックリスト（完了・アーカイブ） |
| `old/PATCH_SAVE_ROADMAP.md` | 保存仕様修正パッチの設計書（完了・アーカイブ） |
| `old/PATCH_SAVE_CHECKLIST.md` | 保存仕様修正パッチのチェックリスト（完了・アーカイブ） |
| `old/ROADMAP2.md` | 参照用（v0.1 完了時点の計画） |
| `old/CHECKLIST2.md` | 参照用（v0.1 完了時点のチェックリスト） |
| `old/ROADMAP.md` | 参照用（初期構想の詳細） |
| `old/CHECKLIST.md` | 参照用（旧全項目リスト） |

---

## 現在のブランチ

`dev`（clean）

直近のコミット:
```
e47f6a6 docs: mark v0.1 complete
4b87818 test: add v0.1 integration flow
4f9acda ui: add bus trace panel
ec32d79 ui: add register view panel
f37a40b ui: add uart console panel
5817330 ui: add basic simulator run controls
2b22894 ui: load built binary into simulator ram
ed35da2 ui: connect build action to assembler
75e39f0 asm: add minimal ak32 assembler
01ec726 fix: reload saved editor content on tab open (B-1)
```

---

## v0.1 完了（2026-05-23）

v0.1 完了条件「**アセンブリを書いて Build → CPU 実行 → UART に "Hi" が GUI 上で見える**」達成済み。
統合テスト `tests/test_v01_flow.py` 9 件通過済み。

### 完了済み（v0.1 までの全実装）

| カテゴリ | 詳細 |
|---|---|
| GUI 骨組み | QMainWindow / メニュー / ツールバー / Dock（左: Parts Library, 右: Properties + Register View, 下: Log + UART Console + Bus Trace） |
| Parts Library | `parts/` 再帰スキャン, カテゴリ表示, 11 パーツ定義 |
| System Canvas | PartNode 配置・移動・選択・Delete 削除・右クリックメニュー |
| node_id 管理 | `node_0001` 形式, 同種複数パーツをインスタンス別に管理 |
| Properties パネル | 選択パーツの名前・ID・カテゴリ・説明・ポート・resources 表示 |
| タブエディタ | `.asm` / `.v` タブ, dirty マーク（`*`）, `build/edit/<node_id>.<ext>` への仮保存・再読み込み（B-1 修正済み） |
| シンタックスハイライト | .asm（キーワード/レジスタ/即値/コメント）/ .v（キーワード/数値/コメント） |
| プロジェクト保存 | `project.json` / `system.json` 作成・保存・読み込み（File メニュー + Ctrl+S） |
| Canvas 座標保存 | `export_parts()` / `import_parts()` で位置を system.json に永続化 |
| アセンブラ | `asm/asm.py` — NOP/HALT/LDI/OUT の 4 命令、行番号付きエラー、ラベル（1-pass）、16 進即値 |
| Build パイプライン | F5 でアクティブ .asm タブをアセンブル → `build/out/<node_id>.bin` 保存 → RAM 自動ロード |
| シミュレータ基盤 | `core/sim.py` — Part / Port / Bus（tracing 付き）/ Chip / Sim |
| RamPart | `core/dev.py` — 32-bit LE word 読み書き, 範囲外 BusError, load_bytes |
| UartPart | `core/dev.py` — TX バッファ, CR/LF 正規化, status レジスタスタブ |
| AK32Part | `core/cpu.py` — NOP/HALT/LDI/OUT, r0 固定ゼロ, Z フラグ, halted 状態 |
| Bus Trace | Bus に `tracing` + `cycle_fn` を追加。`[cycle] READ/WRITE addr val part` 形式で記録 |
| Run / Step / Reset | `_do_run()` 最大 1000 step HALT 停止 / `_do_step()` 1 命令 / `_do_reset()` CPU+UART リセット（RAM 保持） |
| UART Console | QDockWidget（下部タブ）、Run/Step 後に `output_text()` を反映、Reset でクリア |
| Register View | QTableWidget（右側タブ）、pc / cycle / halted / r0〜r15 を表示、Run/Step/Reset 後に更新 |
| Bus Trace パネル | QDockWidget（下部タブ）、Step/Run 後に更新、Reset/Build でクリア |
| サンプルソース | `src/hello.asm` — "Hi" を UART に出力する最小プログラム |
| 統合テスト | `tests/test_v01_flow.py` — 9 件（file 存在 / assemble / UART / Register / Bus Trace） |

---

## 主要ファイル一覧

| ファイル | 役割 |
|---|---|
| `main.py` | エントリーポイント |
| `ui/win.py` | MainWin — レイアウト・メニュー・ツールバー・Run コントロール・全パネル更新 |
| `ui/canvas.py` | Canvas / PartNode — 配置・移動・選択・コンテキストメニュー |
| `ui/editor.py` | EditorTabs — タブエディタ、dirty 管理、仮保存、再読み込み |
| `ui/prop.py` | PropPanel — Properties パネル |
| `ui/highlighter.py` | AsmHighlighter / VerilogHighlighter |
| `ui/lib.py` | load_parts() / cat_label() |
| `core/sim.py` | Part / Port / Bus（tracing）/ BusError / Chip / Sim |
| `core/dev.py` | RamPart / UartPart |
| `core/cpu.py` | AK32Part（最小 CPU エミュレータ） |
| `core/project.py` | create_project / save_system / load_project |
| `asm/asm.py` | AK32 アセンブラ（assemble() / AsmError） |
| `src/hello.asm` | "Hi" 出力サンプルプログラム |
| `parts/*/part.json` | パーツ定義 11 種 |
| `tests/test_editor_reload.py` | エディタ再読み込みテスト |
| `tests/test_asm.py` | アセンブラ単体テスト（17 件） |
| `tests/test_build.py` | Build パイプラインテスト（7 件） |
| `tests/test_sim_load.py` | シミュレータ基盤テスト |
| `tests/test_gui_sim_run.py` | GUI Sim 実行テスト（21 件） |
| `tests/test_v01_flow.py` | v0.1 統合フローテスト（9 件） |

### SPDX ヘッダのルール

全 Python ソースファイルの先頭:
```python
# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
```

---

## 命令エンコード仕様（AK32 現行）

```
bits 31..24  opcode
bits 23..16  rd / ra  (destination or address register)
bits 15..8   rs        (source register)  [LDI: imm16 high byte]
bits  7..0   imm8                         [LDI: imm16 low byte]
```

| opcode | ニーモニック | 動作 |
|---|---|---|
| 0x00 | NOP | なし |
| 0x01 | HALT | 実行停止（pc は HALT 位置を指す） |
| 0x02 | LDI rd, imm16 | regs[rd] = imm16（bits 15:0） |
| 0x03 | OUT [rd], rs | bus.write(regs[rd], regs[rs]) |

---

## 既知バグ・技術的負債

| # | 症状 | 優先度 |
|---|---|---|
| B-2 | Ctrl+S でキャンバスと現在タブの両方が保存されるが責務が不明確 | 低 |
| B-3 | project.json が壊れていると例外でクラッシュ | 低 |
| B-4 | タブが 0 枚の状態で Ctrl+S するとエラーの可能性 | 低 |

---

## 保存仕様修正パッチ（完了）

`old/PATCH_SAVE_ROADMAP.md` / `old/PATCH_SAVE_CHECKLIST.md` に記録済み（アーカイブ）。
自動テスト 105 件通過。手動確認（UART Hi / タブ名確認）は次回以降。

---

## v0.2 Workspace UI Refinement（完了）

**2026-05-24 完了確認。**

### v0.2 で完了した内容

| 項目 | 状態 |
|---|---|
| View メニュー Dock トグル（全 6 パネル） | ✅ 完了 |
| Ribbon 風コマンドバー（File / Build-Run / View / Tools タブ） | ✅ 完了 |
| メニューバーと Ribbon の重複整理（File メニューのみ残存） | ✅ 完了 |
| Project Dialog（New / Open / Save / Save As、ダイアログ選択式） | ✅ 完了 |
| 保存仕様修正（project_root/src/ 分離、build/out/ 分離） | ✅ 完了 |
| 初期レイアウト（Canvas 幅 59%、現状許容） | ✅ 許容 |
| v0.1 回帰テスト（pytest 120 件、headless フロー確認） | ✅ 完了 |
| VS Code 連携 | ⏩ v0.3 以降に延期 |
| Parts Library ダイアログ化 | ⏩ v0.3 以降に延期 |

### 回帰テスト結果（2026-05-24）

- `pytest tests/` 120 件 PASSED（0 件 FAILED）
- headless フロー: New Project → AK32 CPU 配置 → Build → Reset → Run → UART "Hi" → Register View → Bus Trace 全通過

---

## v0.3 Project & Target Foundation（2026-05-24 完了）

### v0.3 の位置づけ

**v0.3 は v0.5 AKDev VS Code Companion の下準備バージョン。**
（v0.4 は Visual Debug Canvas に変更。VS Code Companion は v0.5 に移動。KiCad / Board 連携は v0.6 以降。）

AKDev と VS Code の関係は **Unity と VS Code のような関係**を目指す:
- AKDev 本体 = Unity Editor 側（プロジェクト管理 / Canvas / Build / Run / Target 設定）
- VS Code = コード編集側（ASM / HDL 編集 / 補完 / Git）

### v0.3 完了内容まとめ

| パッチ / 作業 | 状態 |
|---|---|
| ROADMAP4.md / CHECKLIST4.md 作成 | ✅ 完了 |
| Project Scaffold パッチ | ✅ 完了 |
| Build Target Wiring パッチ | ✅ 完了 |
| pytest 159 件全通過 | ✅ 完了 |
| target.json 仕様確定 | ✅ 完了 |
| tools.json 仕様確定（コマンドパス方針含む） | ✅ 完了 |
| 標準プロジェクト構造確定 | ✅ 完了 |
| .vscode/ 生成方針確定（settings.json / extensions.json のみ） | ✅ 完了 |
| v0.5 VS Code Companion への橋渡し文書化 | ✅ 完了 |
| ROADMAP4.md / CHECKLIST4.md 完了更新 | ✅ 完了 |

### tools.json コマンドパス方針

- `command` は PATH 上のコマンド名またはフルパスを許可する。既定値は `"code"`
- Windows では `code.cmd` / `code.exe`、macOS/Linux では `code` を想定
- ユーザーが `tools.json` の `command` フィールドを上書きすることで OS 差異を吸収できる
- OS 自動検出・設定 UI は v0.5 以降

### .vscode/ 生成方針

- `settings.json` / `extensions.json` のみ生成済み
- `tasks.json` は v0.3 では生成しない。Build / Run タスクは v0.5 AKDev VS Code Companion 側で扱う

### 次回の主作業

**v0.4 Visual Debug Canvas** — ROADMAP5.md / CHECKLIST5.md を作成してから実装開始。

### v0.3 Project Scaffold パッチ（2026-05-24 完了）

- 完了済みドキュメントを `old/` に整理（ROADMAP3.md / CHECKLIST3.md / PATCH_PROJECT_DIALOG_*.md）
- `core/project.py` に以下を追加:
  - `default_target_config()`: AK32 Baremetal の target.json / build 設定を返す
  - `default_tools_config()`: vscode / kicad 設定枠（kicad は enabled: false）を返す
  - `load_json_or_default(path, default_fn)`: JSON ファイルが存在しなければ default_fn() を返す
- `create_project()` を拡張（新規プロジェクトで以下を生成）:
  - `target.json` — AK32 Baremetal 既定
  - `tools.json` — vscode / kicad 設定枠
  - `hdl/` / `board/` / `docs/` / `build/rom/` / `build/export/`
  - `.vscode/settings.json` (`{"akdev.project": true}`)
  - `.vscode/extensions.json` (`akdev.akdev-companion` recommended)
- `tests/test_project_scaffold.py` を追加（17 件）
- pytest 137 件全通過（既存 120 件 + 新規 17 件）

### v0.3 Build Target Wiring パッチ（2026-05-24 完了）

- `core/project.py` に以下を追加:
  - `load_target(root)`: `root/target.json` を読む。存在しない場合は `default_target_config()` を返す。
  - `load_tools(root)`: `root/tools.json` を読む。存在しない場合は `default_tools_config()` を返す。
  - `src_type(path)`: ファイル拡張子から source type (`asm / hdl / c / cpp / linker / binary / custom`) を返す。
- `ui/win.py` の `_build()` を更新:
  - target.json の `build.type` を確認する
  - `internal_assembler`: 内蔵アセンブラでビルド（既存互換）
  - `external_command`: Log に "Build: external_command is not implemented yet" を出して中断
  - その他: Log に "Build: unsupported build type: <type>" を出して中断
  - target.json がない旧プロジェクトは `load_target()` フォールバックで AK32 Baremetal デフォルト動作
- `tests/test_target_build_config.py` を追加（22 件）
- pytest 159 件全通過（既存 137 件 + 新規 22 件）
- CHECKLIST4.md セクション 5 / 6 を完了扱いに更新
- ROADMAP4.md に `build.output` 役割方針と Source Type 方針を追記

### 次回の作業開始点

**ROADMAP5.md / CHECKLIST5.md を作成して v0.4 Visual Debug Canvas の計画を立てる。**

---

## v0.4 Visual Debug Canvas（**完了: 2026-05-30**）

**テーマ: Visual Debug Canvas** — pytest 505 件全通過。

### v0.4 完了内容まとめ

| 機能 | 内容 |
|---|---|
| AK32 命令拡張 | ADD/SUB/LD/ST/JMP/BEQ/ADDI（opcode 0x04〜0x0A） |
| アセンブラ更新 | 2-pass ラベル解決、`assemble_ex()` で address_map 返却 |
| fib.asm | フィボナッチ数列（ADD/ST/ADDI/BEQ/JMP）サンプル |
| Canvas UX Patch 1A | Parts Library ドラッグ&ドロップ、add_part 中央配置 |
| Canvas UX Patch 1B | Zoom In/Out/Reset/Fit、GridScene、ホイールズーム、右ドラッグ Pan |
| Grid / Snap Patch | Snap to Grid（View タブトグル） |
| Bus Connection Patch | ConnectionLine, export/import_canvas, wire mode, BFS ルーティング, RouteHandle |
| Memory Viewer | hex dump パネル（下部タブ）、PC 行ハイライト |
| PC ハイライト | Step/Run 後にエディタ現在実行行を薄い緑でハイライト |
| Canvas Signal Overlay | bus kind 接続線を Bus トランザクション時に明るく光らせる |
| サンプル確認 | hello.asm UART "Hi" ✅、fib.asm RAM[0x40..0x5C] = フィボナッチ ✅ |
| pytest | 505 件全通過（v0.3 完了時 159 件 → v0.4 完了時 505 件） |

詳細は `old/ROADMAP5.md` / `old/CHECKLIST5.md` を参照。

---

## v0.2 の方向性（完了）

**テーマ: Workspace UI Refinement** — 2026-05-24 完了。

詳細は `ROADMAP3.md` / `CHECKLIST3.md` を参照。

---

## v0.4.1 フェーズ完了処理（2026-06-03）

### 完了評価

v0.4.1 Patch — Canvas Routing Polish & Pre-Release Docs を正式完了。

| 評価項目 | 結果 |
|---|---|
| 総合テスト（pytest 518 件） | ✅ 2026-06-03 実行・全通過（2.47s） |
| 配線角修正（update_route 直線化） | ✅ 完了 |
| Canvas Pan 中ボタン化 | ✅ 完了 |
| 公開前ドキュメント（QUICKSTART / USER_GUIDE）| ✅ 完了 |
| CLAUDE.md Rule 4 更新（PHASE COMPLETE 定義）| ✅ 完了 |

### old/ に収納したファイル

| ファイル | 理由 |
|---|---|
| `old/ROADMAP5.md` | v0.4 Visual Debug Canvas 完了 |
| `old/CHECKLIST5.md` | v0.4 Visual Debug Canvas 完了 |
| `old/PATCH_V041_ROADMAP.md` | v0.4.1 Patch 完了 |
| `old/PATCH_V041_CHECKLIST.md` | v0.4.1 Patch 完了 |

### 次フェーズの開始点

**v0.5** — `ROADMAP6.md` / `CHECKLIST6.md` を作成済み。主軸と実装範囲はそちらを参照。

---

## 次回 Claude Code に最初に入れる指示文

```
HANDOFF.md を読んで現在の状態を確認してください。

v0.1 / v0.2 / v0.3 / v0.4 / v0.4.1 は全て完了済みです。
pytest 518 件全通過済み（2026-06-03 確認）。

ROADMAP6.md / CHECKLIST6.md が作成済みです。
ROADMAP6.md を読んで v0.5 の主軸を確認し、実装を開始してください。

v0.5 主軸（ROADMAP6.md 参照）:
- 優先度 A（内部 UI 改善）: 配線色変更 UI / Part Visual 拡張 / Port Detail / 正確な Signal Overlay
- 優先度 B（外部連携）: VS Code Companion / CALL・RET・IN 命令 / ブレークポイント UI
- 優先度 C（長期）: KiCad 連携 / C コンパイラ / HDL 合成 / 実機書き込み
```

---

## セッション記録

### PHASE COMPLETE — v0.4.1（2026-06-03）

- CLAUDE.md Rule 4 に従って v0.4.1 フェーズ完了処理を実施
- `pytest tests/` 518 件全通過（2.47s）を総合確認として実行・記録
- `ROADMAP5.md` / `CHECKLIST5.md` / `PATCH_V041_ROADMAP.md` / `PATCH_V041_CHECKLIST.md` を `old/` に収納
- `HANDOFF.md` を v0.4.1 完了評価・次フェーズ開始点に更新
- `ROADMAP6.md` / `CHECKLIST6.md` を新規作成（v0.5 計画）
- 次フェーズ: v0.5 — ROADMAP6.md / CHECKLIST6.md を参照して実装開始

### セッション 1〜5（2026-05-22）

GUI 骨組み → Parts Library → Canvas → node_id 管理 → Properties → タブエディタ →
シンタックスハイライト → プロジェクト保存 → シミュレータ基盤 → RamPart / UartPart → AK32Part

### セッション 6（2026-05-22）

- `ROADMAP2.md` / `CHECKLIST2.md` を新規作成（旧ファイルを `old/` にコピー）
- `HANDOFF.md` を更新
- B-1 バグ（エディタ再読み込み）を修正

### セッション 7〜11（2026-05-23）

- 1.2: アセンブラ (`asm/asm.py`) 実装
- 1.3: Build ボタンとアセンブラ接続
- 1.4: asm → binary → RAM ロード
- 1.5: Run / Step / Reset / Pause 実装
- 1.6: UART Console パネル追加
- 1.7: Register View パネル追加
- 1.8: Bus Trace（Bus への tracing 機能 + パネル）追加
- 1.9: `src/hello.asm` 作成 + `tests/test_v01_flow.py` 統合テスト
- **v0.1 完了**

### セッション 12（2026-05-23）

- v0.2 テーマを「Workspace UI Refinement」に決定
- `ROADMAP2.md` / `CHECKLIST2.md` を `old/` にアーカイブし削除
- `ROADMAP3.md` / `CHECKLIST3.md` を新規作成（v0.2 計画）
- `HANDOFF.md` を更新

### セッション 13（2026-05-24）

- `PATCH_SAVE_ROADMAP.md` / `PATCH_SAVE_CHECKLIST.md` を作成（保存仕様修正計画）
- 保存仕様修正パッチを実装:
  - `ui/editor.py`: `_SAVE_DIR` 廃止、`set_project_root()` / `close_all_tabs()` / `validate_source_name()` 追加、保存先を `project_root/src/` に変更、タブ名を `source_name` に変更
  - `ui/canvas.py`: `PartNode` に `sources` フィールド追加、`export_parts()` / `import_parts()` 対応、`get_node()` 追加
  - `ui/win.py`: `_BUILD_OUT` 廃止、`_new_project()` でタブクリア、`_on_open_tab()` にファイル名ダイアログ追加、Build 出力を `project_root/build/out/` に変更
  - `core/project.py`: `build/out/` ディレクトリを作成するよう修正
  - `tests/test_editor_reload.py` / `test_build.py` / `test_sim_load.py` を新 API に更新
  - `tests/test_save_isolation.py` を新規作成（20 件）
- `pytest tests/` 105 件全通過
- 手動確認（タブ名・プロジェクト分離・UART Hi）は次回

### セッション 14（2026-05-24）

- `PATCH_PROJECT_DIALOG_ROADMAP.md` / `PATCH_PROJECT_DIALOG_CHECKLIST.md` を作成（Project Dialog / Save As パッチ計画）
- `HANDOFF.md` を更新（現在の優先作業を Project Dialog パッチに変更）

### セッション 40（2026-05-30）— v0.4.1 Patch

**v0.4.1 公開前修正パッチ完了。pytest 518 件全通過。**

#### P1. 配線ルートの角修正

- `ConnectionLine.update_route()` を H-V 二重描画から直線 lineTo に変更
  - BFS が返す経路点列（すでにコーナー点のみ）をそのまま直線で繋ぐことで余分な折れ線が消える
- `ConnectionLine.update_line(p1, p2)` を `[p1, (p2.x, p1.y), p2]` の明示 H-V に変更
- `Canvas._from_port_pos(node_id)` / `_to_port_pos(node_id)` を追加（右端・左端ポート位置）
- `Canvas.update_connections()` をノード中心 → ポート位置（グリッドスナップ）に変更
  - 接続線が "パーツ右端から出て左端に入る" 自然な形になった
- `_update_wire_preview()` も `_from_port_pos` を使うよう変更

#### P2. Canvas Pan を中ボタンドラッグへ変更

- `mousePressEvent` / `mouseMoveEvent` / `mouseReleaseEvent` を `RightButton` → `MiddleButton`
- `contextMenuEvent` の `_panned` ガード（右クリックメニュー抑制）を削除
  - 右クリックは常にコンテキストメニューを表示する
- `tests/test_canvas_pan.py` を MiddleButton 対応に全面更新

#### P3. 公開前ドキュメント追加

- `docs/QUICKSTART.md` 新規作成（5 分で hello.asm を動かす手順）
- `docs/USER_GUIDE.md` 新規作成（全機能説明）
- `README.md` を v0.4.1 対応に更新（リンク追加・できること整理）

#### テスト結果

- pytest 518 件全通過（v0.4 完了時 505 件 → +13 件）
- 更新テスト: `test_canvas_pan.py`（RightButton→MiddleButton）、`test_canvas_connection_lines.py`（center→port_pos）、`test_canvas_wire_mode.py`（update_route 挙動更新）
- 新規テスト: `test_canvas_routing.py` に 9 件追加（port_pos・update_route・update_line）、`test_canvas_pan.py` に 1 件追加

---

### セッション 39（2026-05-30）

- v0.4 Visual Debug Canvas を完了宣言:
  - pytest tests/ 505 件全通過を確認
  - src/hello.asm headless 検証: UART "Hi" ✅、Bus trace 8 件 ✅、last_transactions 更新 ✅
  - src/fib.asm headless 検証: RAM[0x40..0x5C] = 0,1,1,2,3,5,8,13 ✅、halted ✅
  - CHECKLIST5.md セクション 11〜14 を全 [x] に更新、v0.4 完了宣言を追記
  - ROADMAP5.md を v0.4 完了内容まとめ + v0.5 以降の候補リストに更新
  - HANDOFF.md を v0.4 完了・次作業 v0.5 計画に更新

### セッション 38（2026-05-30）

- CHECKLIST5.md セクション 10（Canvas Signal Overlay）を実装・完了:
  - `core/sim.py`: `Bus` に `last_transactions: dict` を追加（`{part_id: ("READ"|"WRITE", addr, val)}`）
  - `core/sim.py`: `Bus.read()` / `Bus.write()` で `last_transactions` を更新（tracing と独立）
  - `core/sim.py`: `Bus.reset_transactions()` を追加（`last_transactions.clear()`）
  - `ui/canvas.py`: `ConnectionLine` に `_kind` フィールドと `kind()` アクセサを追加
  - `ui/canvas.py`: `ConnectionLine` に `_base_pen` を保存し `set_active(active: bool)` を追加（active=True で brighter+太め、False で元のペンに戻す）
  - `ui/canvas.py`: `Canvas.update_signal_overlay(transactions)` を追加（transactions が空でなければ bus kind の ConnectionLine を active に）
  - `ui/canvas.py`: `Canvas.clear_signal_overlay()` を追加（全 ConnectionLine を active=False）
  - `ui/canvas.py`: `Canvas.get_all_nodes()` を追加（テスト補助用ヘルパー）
  - `ui/win.py`: `_update_signal_overlay()` を追加（`canvas.update_signal_overlay(bus.last_transactions)`）
  - `ui/win.py`: `_do_step()` 末尾に `_update_signal_overlay()` を追加
  - `ui/win.py`: `_do_run()` の 3 終了点（pause / halt / 1000 cycle limit）に `_update_signal_overlay()` を追加
  - `ui/win.py`: `_do_reset()` に `reset_transactions()` + `clear_signal_overlay()` を追加
  - `ui/win.py`: `_build()` に `reset_transactions()` + `clear_signal_overlay()` を追加
  - `tests/test_canvas_signal_overlay.py` を新規作成（29 件）
  - pytest 505 件全通過（既存 476 件 + 新規 29 件）
  - CHECKLIST5.md セクション 10 を全 [x] に更新

### セッション 37（2026-05-30）

- CHECKLIST5.md セクション 9（PC ハイライト）を実装・完了:
  - `ui/highlighter.py`: `attach_line_highlight()` を PC ハイライト対応に改修
    - `_PC_LINE_BG = QColor("#ccffcc")` 定数を追加
    - 戻り値として `set_pc_line(line_no: int | None)` callable を返すよう変更
    - カーソル行ハイライトと PC 行ハイライトを同一 `setExtraSelections` 呼び出しでマージ
    - `pc_state = [None]` クロージャで PC 行番号を管理
  - `ui/editor.py`: `_TabInfo` に `set_pc_line = None` フィールドを追加
  - `ui/editor.py`: `open_tab()` で `attach_line_highlight()` の戻り値を `info.set_pc_line` に保存
  - `ui/editor.py`: `EditorTabs.highlight_line(line_no: int)` を追加（0-origin、範囲外でも安全）
  - `ui/editor.py`: `EditorTabs.clear_highlight()` を追加
  - `ui/win.py`: `from asm.asm import assemble` → `assemble_ex` に変更
  - `ui/win.py`: `__init__` に `self._address_map: dict[int, int] = {}` を追加
  - `ui/win.py`: `_build()` で `assemble_ex()` を使用、成功時に `self._address_map = address_map` 保存、失敗時 `= {}` クリア
  - `ui/win.py`: `_build()` 成功・失敗後に `self._editor_tabs.clear_highlight()` を呼び出し
  - `ui/win.py`: `_update_pc_highlight()` を追加（`address_map.get(cpu.pc)` → `highlight_line` / `clear_highlight`）
  - `ui/win.py`: `_do_step()` 末尾に `_update_pc_highlight()` を追加
  - `ui/win.py`: `_do_run()` の 3 つの終了点に `_update_pc_highlight()` を追加
  - `ui/win.py`: `_do_reset()` 末尾に `clear_highlight()` を追加
  - `tests/test_editor_highlight.py` を新規作成（14 件）:
    - highlight_line/clear_highlight の無タブ/タブあり/範囲外/負値 テスト
    - MainWin: _address_map 初期化/build成功後保存/build失敗後クリア/step/run/reset 無クラッシュテスト
  - pytest 476 件全通過（既存 462 件 + 新規 14 件）
  - CHECKLIST5.md セクション 9 を全 [x] に更新

### セッション 36（2026-05-30）

- CHECKLIST5.md セクション 8（Memory Viewer パネル）を実装・完了:
  - `ui/memview.py` を新規作成: `_hex_dump(data)` モジュール関数 / `MemoryViewer(QDockWidget)` クラス
  - `_hex_dump`: 1行 16bytes、アドレス列 + hex 列 + ASCII 列。非印字文字は "."
  - `MemoryViewer.update_from_ram(ram_part)`: `ram_part.dump()` から bytes を読み hex dump 表示を更新
  - `MemoryViewer.highlight_addr(pc)`: PC が属する行を薄い黄色でハイライト（`QTextCharFormat` 使用）
  - `ui/win.py`: `_setup_memory_viewer()` 追加、下部タブ（Log/UART/Bus Trace と並列）に "Memory" ドック追加
  - `ui/win.py`: `_update_memory_viewer()` 追加、Build / Run / Step / Reset / Pause 後に呼び出し
  - `ui/win.py`: View Ribbon に Memory Viewer トグルを追加
  - `tests/test_memview.py` を新規作成（22 件）: hex dump 単体 / MemoryViewer 生成 / RAM 内容反映 / None/空 RAM 無クラッシュ / highlight_addr 無クラッシュ / MainWin 統合テスト
  - pytest 462 件全通過（既存 440 件 + 新規 22 件）
  - CHECKLIST5.md セクション 8 を全 [x] に更新

### セッション 35（2026-05-30）

- CHECKLIST5.md セクション 7.6（Wire Routing Patch 2 — 障害物回避と頂点編集）を実装・完了:
  - `ui/canvas.py`: `from collections import deque` / `from math import floor, ceil` を追加
  - `ui/canvas.py`: `QGraphicsRectItem` を Qt インポートに追加
  - `ui/canvas.py`: `_grid_pos(p)` / `_compress_path(path)` モジュールレベル関数を追加
  - `ui/canvas.py`: `RouteHandle(QGraphicsRectItem)` クラスを追加（6×6px ドラッグ可能 waypoint ハンドル、grid スナップ、移動コールバック）
  - `ui/canvas.py`: `Canvas.mode_changed = Signal(str)` を追加
  - `ui/canvas.py`: `Canvas.__init__` に `_handle_items: list = []` を追加
  - `ui/canvas.py`: `_block_cells(excl_ids)` を追加（PartNode の bounding rect + 1 セルマージンを blocked set として返す）
  - `ui/canvas.py`: `_route_segment(start, end, blocked)` BFS を追加（障害物回避、フォールバック H→V Manhattan）
  - `ui/canvas.py`: `_route_grid(start, end, waypoints, blocked)` を追加（waypoint 区間ごとに BFS、端点を正確な座標に置換）
  - `ui/canvas.py`: `_show_handles()` / `_hide_handles()` / `_on_handle_moved()` を追加
  - `ui/canvas.py`: `_start_wire()` を更新（`_show_handles()` 呼び出し、`mode_changed.emit("wire")`）
  - `ui/canvas.py`: `_cancel_wire()` を更新（`_hide_handles()` 呼び出し、`mode_changed.emit("design")`）
  - `ui/canvas.py`: `set_mode()` を更新（重複 emit を避ける early return 追加、wire モードでも handles/signal 対応）
  - `ui/canvas.py`: `update_connections()` を BFS ルーティングに更新（`_block_cells` + `_route_grid` 経由で描画）
  - `ui/canvas.py`: `import_canvas(clear=True)` で `_hide_handles()` を追加
  - `ui/win.py`: `_a_wire_mode` QAction（checkable）を追加し View Ribbon に配置、`mode_changed` シグナルで状態同期
  - `tests/test_canvas_routing.py`: 障害物回避・BFS ルーティング・RouteHandle・mode_changed テスト 35 件新規作成
  - pytest 440 件全通過（既存 405 件 + 35 件追加）
  - CHECKLIST5.md セクション 7.6 を新規追加・[x] に更新

### セッション 34（2026-05-26）

- CHECKLIST5.md セクション 7.5（配線 UX 改善 — wire mode + マンハッタン配線）を実装・完了:
  - `ui/canvas.py`: `_LINE_COLOR` を削除し `_KIND_COLORS` dict（bus=#66ccff / signal=#88ddaa / clock=#ffcc66 / reset=#ff8888）と `_WIRE_PREVIEW_COLOR` に置換
  - `ui/canvas.py`: `ConnectionLine.__init__` に `color: str` 引数を追加（`_KIND_COLORS` またはカスタム色）
  - `ui/canvas.py`: `ConnectionLine.update_route(points)` を追加（H-then-V Manhattan routing）
  - `ui/canvas.py`: `ConnectionLine.update_line(p1, p2)` を `update_route([p1, p2])` のラッパーに変更
  - `ui/canvas.py`: `Canvas.__init__` に `_mode = "design"` / `_wire_from` / `_wire_waypoints` / `_wire_preview` を追加
  - `ui/canvas.py`: `Canvas.set_mode()` を追加（"design" → wire state cancel）
  - `ui/canvas.py`: `Canvas._start_wire()` / `_add_waypoint()` / `_finish_wire()` / `_cancel_wire()` / `_update_wire_preview()` を追加
  - `ui/canvas.py`: `add_connection()` に `route: list | None` / `color: str` 引数を追加、`"route"` / `"color"` を conn dict に保存
  - `ui/canvas.py`: `_make_conn_item()` で `color` を `ConnectionLine` に渡す
  - `ui/canvas.py`: `update_connections()` を `update_route()` 対応に更新（route waypoints 反映）
  - `ui/canvas.py`: `import_canvas(clear=True)` で `_cancel_wire()` を呼ぶ
  - `ui/canvas.py`: `contextMenuEvent()` を wire mode 対応に更新（design: "接続を開始"追加 / wire + PartNode: "ここに接続"/"キャンセル" / wire + 空白: waypoint追加）
  - `ui/canvas.py`: `add_part_at()` / `import_parts()` / clone から `_port_dot._click_cb` 設定を削除（PortDot は visual のみ）
  - `ui/canvas.py`: `mouseMoveEvent()` で wire mode 時に `_update_wire_preview()` を呼ぶ
  - `tests/test_canvas_wire_mode.py`: wire mode テスト 37 件新規作成
  - `tests/test_canvas_port_connect.py`: `_click_cb` チェックのテスト 2 件を削除（wiring 廃止）
  - pytest 405 件全通過（既存 373 件 + 37 件追加 − 2 件削除 + 差分調整）
  - CHECKLIST5.md セクション 7.5 を新規追加・[x] に更新

### セッション 33（2026-05-26）

- CHECKLIST5.md セクション 7（port-to-port クリック操作）を実装・完了:
  - `ui/canvas.py`: `_DOT_RADIUS` / `_DOT_COLOR` / `_DOT_PENDING` モジュール定数を追加
  - `ui/canvas.py`: `PortDot(QGraphicsEllipseItem)` クラスを追加（node_id / port_name / _click_cb / set_pending() / mousePressEvent → _click_cb 呼び出し）
  - `ui/canvas.py`: `PartNode.__init__` で `_port_dot = PortDot(node_id, "bus", self)` を作成し右端中央に配置
  - `ui/canvas.py`: `Canvas.__init__` に `_pending_port = None` を追加
  - `ui/canvas.py`: `Canvas._on_port_click(dot)` を追加（1回目 → pending セット、2回目 → add_connection / 同一node → キャンセル）
  - `ui/canvas.py`: `import_canvas(clear=True)` で `_pending_port = None` を追加
  - `ui/canvas.py`: `add_part_at` / `import_parts` / contextMenu clone で `_port_dot._click_cb = self._on_port_click` を設定
  - `tests/test_canvas_port_connect.py`: port 接続テスト 25 件追加
  - `tests/test_save_isolation.py`: `scene().items()[0]` → `isinstance` フィルタ修正（PortDot が z=1 で先頭に来るため）
  - pytest 373 件全通過（既存 348 件 + 新規 25 件）
  - CHECKLIST5.md セクション 7 の port-to-port クリック操作項目を [x] に更新

### セッション 32（2026-05-26）

- CHECKLIST5.md セクション 7.4（接続線描画）を実装・完了:
  - `ui/canvas.py`: `_LINE_COLOR` / `_KIND_PEN_WIDTH` モジュール定数を追加
  - `ui/canvas.py`: `ConnectionLine(QGraphicsPathItem)` クラスを追加（conn_id / from/to_node_id / kind → pen幅 / zValue=-1 / update_line(p1, p2)）
  - `ui/canvas.py`: `PartNode.__init__` に `_pos_changed_cb = None` を追加
  - `ui/canvas.py`: `PartNode.itemChange()` で `ItemPositionHasChanged` 時に `_pos_changed_cb()` を呼び出す
  - `ui/canvas.py`: `Canvas.__init__` に `_conn_items: dict = {}` を追加
  - `ui/canvas.py`: `Canvas._node_center()` / `_make_conn_item()` / `_rebuild_conn_items()` を追加
  - `ui/canvas.py`: `Canvas.update_connections()` を追加（全接続線の位置を現在ノード座標に更新）
  - `ui/canvas.py`: `add_connection()` 後に ConnectionLine をシーンへ追加
  - `ui/canvas.py`: `import_canvas()` 後に `_rebuild_conn_items()` で接続線を復元
  - `ui/canvas.py`: `add_part_at()` / `import_parts()` / contextMenu clone に `_pos_changed_cb` を設定
  - `tests/test_canvas_connection_lines.py`: 接続線テスト 27 件追加
  - pytest 348 件全通過（既存 321 件 + 新規 27 件）
  - CHECKLIST5.md セクション 7.4 を [x] に更新

### セッション 31（2026-05-26）

- CHECKLIST5.md セクション 7（Bus Connection Patch）を追加・一部完了:
  - セクション番号を繰り下げ: 旧 7-13 → 新 8-14（Bus Connection Patch を 7 として挿入）
  - `ui/canvas.py`: `Canvas.__init__` に `_conn_seq: int = 0` / `_connections: list[dict] = []` を追加
  - `ui/canvas.py`: `_next_conn_id()` を追加（`conn_0001` 形式の連番 ID）
  - `ui/canvas.py`: `add_connection(from_node_id, from_port, to_node_id, to_port, kind, width, label)` を追加
  - `ui/canvas.py`: `export_canvas()` を追加 — `{"parts": [...], "connections": [...]}` を返す
  - `ui/canvas.py`: `import_canvas(data, part_library, clear=True)` を追加 — parts / connections を復元
  - `tests/test_canvas_connections.py`: 接続データ構造テスト 30 件追加
  - pytest 321 件全通過（既存 291 件 + 新規 30 件）
  - CHECKLIST5.md セクション 7.1 / 7.2 / 7.3 を [x] に更新

### セッション 30（2026-05-26）

- CHECKLIST5.md セクション 6（Part Visual / Port Detail / Bus Connection 方針）を完了:
  - `ROADMAP5.md` セクション 7 を大幅拡充（方針確定）:
    - 7-1: `part.json` `"size": [w, h]` 省略可能フィールド方針（v0.5 以降実装、`_NODE_W`/`_NODE_H` フォールバック）
    - 7-2: `part.json` `"color"` / `system.json` `"instance_color"` カラー優先度方針（カテゴリ色 < part.json < instance_color, `QColor.isValid()` バリデーション付き）
    - 7-3: Port Detail 方針（ダブルクリック / コンテキストメニューで開く、表示列: Name/Direction/Kind/Width/Range/Description、v0.4 では実装しない）
    - 7-4: `system.json` `connections` スキーマ確定（`id`, `from: {node_id, port}`, `to: {node_id, port}`, `kind`, `width`, `label`）
  - CHECKLIST5.md セクション 6 全項目を [x] に更新
  - pytest 291 件全通過（変化なし）

### セッション 29（2026-05-26）

- CHECKLIST5.md セクション 5（Grid / Snap Patch）を実装:
  - `ui/canvas.py`: `PartNode` に `_snap_enabled: bool = False` と `set_snap()` を追加
  - `ui/canvas.py`: `PartNode.itemChange()` をオーバーライド — `ItemPositionChange` 時に `round(x/g)*g` で snap
  - `ui/canvas.py`: `Canvas.__init__` に `_snap_enabled: bool = False` を追加
  - `ui/canvas.py`: `Canvas.set_snap(enabled)` を追加 — 既存ノード全体に伝播
  - `ui/canvas.py`: `Canvas.add_part_at()` で snap ON のとき scene_pos を丸めてから配置、新ノードに snap 状態を渡す
  - `ui/canvas.py`: `Canvas.import_parts()` で復元ノードにも snap 設定を渡す
  - `ui/win.py`: `_a_snap` QAction（checkable, 初期値 OFF）を追加し、Ribbon View タブに追加
  - `tests/test_canvas_snap.py`: Snap テスト 15 件追加
  - pytest 291 件全通過（既存 276 件 + 新規 15 件）
  - CHECKLIST5.md セクション 5 を全 [x] に更新

### セッション 28（2026-05-25）

- `ui/canvas.py` に右ドラッグ Pan を実装:
  - `_PAN_THRESHOLD = 4` モジュール定数を追加
  - `__init__` に `_pan_origin` / `_pan_last` / `_panned` 状態変数を追加
  - `mousePressEvent`: 右ボタン押下時に pan 状態を初期化・`ClosedHandCursor` をセット
  - `mouseMoveEvent`: 右ボタン保持中、閾値超えで `_panned = True`、スクロールバーを差分移動
  - `mouseReleaseEvent`: 右ボタン離したらカーソル復元・状態リセット
  - `contextMenuEvent`: `_panned == True` の場合はメニューをスキップして `_panned` をリセット
- `tests/test_canvas_pan.py`: pan 状態テスト 10 件追加（duck-type 右ボタンイベント使用）
- pytest 276 件全通過（既存 266 件 + 新規 10 件）
- CHECKLIST5.md セクション 4 に右ドラッグ Pan 完了項目を追記

### セッション 27（2026-05-25）

- `ui/canvas.py` に `wheelEvent()` を追加:
  - `angleDelta().y() > 0` → `zoom_in()`、`< 0` → `zoom_out()`、`== 0` → `super()`
  - `event.accept()` でイベントを消費
  - `setTransformationAnchor(AnchorUnderMouse)` を `__init__` に追加（ホイール位置中心ズーム）
- `tests/test_canvas_zoom_grid.py` にホイールズームテスト 5 件追加（`_FakeWheelEvent` duck-type 使用）
  - anchor 確認 / wheel forward → zoom_in / wheel backward → zoom_out / 上下限ヒット確認
- pytest 266 件全通過（既存 261 件 + 新規 5 件）
- CHECKLIST5.md セクション 4 にホイールズーム完了項目を追記

### セッション 26（2026-05-25）

- CHECKLIST5.md セクション 4（Canvas UX Patch 1B）を実装:
  - `ui/canvas.py`: `_ZOOM_MIN = 0.1` / `_ZOOM_MAX = 10.0` モジュール定数を追加
  - `ui/canvas.py`: `GridScene(QGraphicsScene)` を追加（`GRID_SIZE = 20`、`drawBackground()` でグリッド線、`set_grid_visible()` / `grid_visible()`）
  - `ui/canvas.py`: `Canvas.__init__()` を `QGraphicsScene` → `GridScene` に変更
  - `ui/canvas.py`: `zoom_in()` / `zoom_out()` / `reset_zoom()` / `fit_to_view()` / `set_grid_visible()` を追加（zoom 上限/下限チェックは乗算後値で判定）
  - `ui/win.py`: `_a_zoom_in` / `_a_zoom_out` / `_a_zoom_reset` / `_a_fit` / `_a_grid` QAction を追加、Ribbon View タブに追加
  - `tests/test_canvas_zoom_grid.py`: Zoom / GridScene テスト 15 件追加
  - pytest 261 件全通過（既存 246 件 + 新規 15 件）
  - CHECKLIST5.md セクション 4・11.5 を全 [x] に更新

### セッション 25（2026-05-24）

- CHECKLIST5.md セクション 3（Canvas UX Patch 1A）を実装:
  - `ui/canvas.py`: グリッド配置定数 (`_GAP_X`/`_GAP_Y`/`_COLS`/`_ORIGIN`) と `_place_col`/`_place_row` を削除
  - `ui/canvas.py`: `setAcceptDrops(True)` / `_add_offset` / `_part_library` を `__init__` に追加
  - `ui/canvas.py`: `set_part_library(lib)` を追加（`dropEvent` 用パーツ辞書を保持）
  - `ui/canvas.py`: `add_part_at(part, scene_pos)` を追加（指定 scene 座標に PartNode 配置）
  - `ui/canvas.py`: `add_part()` を viewport 中央 + `_add_offset * 20px` ダイアゴナルオフセット方式に変更（8 ステップでサイクル）
  - `ui/canvas.py`: `dragEnterEvent` / `dragMoveEvent` / `dropEvent` を追加（MIME text = part_id でドロップ配置）
  - `ui/win.py`: `_PartsTree(QTreeWidget)` を追加（`startDrag()` オーバーライドで part_id を MIME text にセット）
  - `ui/win.py`: `_setup_parts_lib()` を `_PartsTree` に切り替え、`setDragEnabled(True)`、`canvas.set_part_library()` 呼び出しを追加
  - `tests/test_canvas_ux.py`: Canvas UX テスト 12 件追加
  - pytest 246 件全通過（既存 234 件 + 新規 12 件）
  - CHECKLIST5.md セクション 3・11.3 を全 [x] に更新

### セッション 24（2026-05-24）

- ROADMAP5.md / CHECKLIST5.md を Canvas UX 優先に再編:
  - v0.4 の次優先を Memory Viewer → Canvas UX Patch 1A（ドラッグ&ドロップ）に変更
  - ROADMAP5.md: セクション 1〜3 完了、4〜8 に Canvas UX 設計を追加（ドラッグ&ドロップ・Zoom・Grid・Snap・接続線）
  - CHECKLIST5.md: セクション 3〜6 に Canvas UX Patch 1A/1B・Grid Snap・方針を追加。旧セクション 3〜9 を 7〜13 に繰り下げ
  - 完了済みチェック項目（セクション 1・2・10・11.1・11.2・11.4・11.5）はすべて維持
- 次回の主作業を CHECKLIST5.md セクション 3（Canvas UX Patch 1A）に変更

### セッション 23（2026-05-24）

- ROADMAP4.md / CHECKLIST4.md を old/ にアーカイブ
- HANDOFF.md のドキュメント体系を old/ パス参照に更新
- v0.4 CHECKLIST5.md セクション 0〜2・6・7 を完了:
  - `core/cpu.py`: ADD / SUB / ADDI / LD / ST / JMP / BEQ 命令（opcode 0x04〜0x0A）を実装
  - `asm/asm.py`: 同命令のパーサ追加、2-pass ラベル解決、`assemble_ex()` 新規追加（address_map 返却）
  - `src/fib.asm`: フィボナッチ数列プログラム（ADD/ST/ADDI/BEQ/JMP 使用）を新規作成
  - `tests/test_cpu_v04.py`: CPU 命令テスト 30 件追加
  - `tests/test_asm_v04.py`: アセンブラテスト 45 件追加
  - `tests/test_v04_flow.py`: fib フロー統合テスト 10 件追加
  - pytest 234 件全通過（既存 159 件 + 新規 75 件）

### セッション 22（2026-05-24）

- ROADMAP5.md / CHECKLIST5.md を新規作成（v0.4 Visual Debug Canvas 計画）
  - ROADMAP5.md: 命令セット拡張（ADD/SUB/LD/ST/JMP/BEQ/ADDI）・アセンブラ更新・Memory Viewer・PC ハイライト・Canvas Signal Overlay・fib.asm サンプル の設計
  - CHECKLIST5.md: セクション 0〜9 の全チェック項目を作成
- HANDOFF.md のドキュメント体系を v0.4 優先に更新
- 次回指示文を「CHECKLIST5.md セクション 0 から実装開始」に更新

### セッション 21（2026-05-24）

- v0.3 Project & Target Foundation を完了扱いに移行:
  - ROADMAP4.md: v0.3 テーマを "完了" 表記に更新、v0.4 を Visual Debug Canvas に変更、VS Code Companion を v0.5 に移動、KiCad / Board を v0.6 以降に移動
  - ROADMAP4.md: セクション 7 を "v0.5 VS Code Companion への橋渡し" に改訂（localhost HTTP/WS 連携案・将来 API 案・isa.json 補完構想を追記）
  - ROADMAP4.md: v0.3 完成条件を全 [x] に更新
  - CHECKLIST4.md: 残未完了項目を全 [x] に（tools.json コマンドパス方針・tasks.json 不生成方針・セクション 7/8/9）
  - HANDOFF.md: v0.3 完了内容まとめ・次回作業を ROADMAP5.md / CHECKLIST5.md 作成に更新

### セッション 20（2026-05-24）

- v0.3 Build Target Wiring パッチを実装:
  - `core/project.py`: `load_target()` / `load_tools()` / `src_type()` を追加
  - `ui/win.py`: `_build()` を target.json の `build.type` に対応させる（internal_assembler / external_command / unknown の 3 分岐）
  - `tests/test_target_build_config.py`: 22 件追加
  - pytest 159 件全通過（既存 137 件 + 新規 22 件）
- CHECKLIST4.md セクション 5 / 6 を [x] に更新
- ROADMAP4.md に build.output 役割方針・Source Type 方針を追記
- HANDOFF.md を更新

### セッション 19（2026-05-24）

- 完了済みドキュメントを `old/` に整理（ROADMAP3.md / CHECKLIST3.md / PATCH_PROJECT_DIALOG_ROADMAP.md / PATCH_PROJECT_DIALOG_CHECKLIST.md）
- v0.3 Project Scaffold パッチを実装:
  - `core/project.py`: `default_target_config()` / `default_tools_config()` / `load_json_or_default()` を追加
  - `create_project()`: target.json / tools.json / hdl/ / board/ / docs/ / build/rom/ / build/export/ / .vscode/ を生成するよう拡張
  - `tests/test_project_scaffold.py`: 17 件追加
  - pytest 137 件全通過（既存 120 件 + 新規 17 件）
- CHECKLIST4.md を更新（セクション 0〜4 の完了項目を [x] に）
- HANDOFF.md を更新

### セッション 18（2026-05-24）

- ROADMAP4.md / CHECKLIST4.md を新規作成（v0.3 Project & Target Foundation 計画）
- HANDOFF.md を更新（現在の優先作業を v0.3 に変更）

### セッション 17（2026-05-24）

- v0.2 最終整理:
  - CHECKLIST3.md を更新（3.1 完了、3.2/4 を v0.3 延期・注記、5 を現状許容、6 を完了マーク）
  - ROADMAP3.md を更新（v0.2 完成条件を現状に合わせて更新、v0.3 候補に VS Code 連携・自作 ISA 設定を追加）
  - HANDOFF.md を更新（v0.2 完了確認・次アクション整理）
  - v0.1 回帰テスト実施: pytest 120 件全通過
  - headless フロー確認: New Project → Build → Reset → Run → UART "Hi" → Register View → Bus Trace 全通過
  - **v0.2 完了**

### セッション 16（2026-05-24）

- Project Dialog / Save As パッチの手動確認（headless ダイアログ駆動で全フロー検証）
  - File メニュー・Ribbon 構造確認（New/Open/Save/Save As/Exit 順序・セパレータ位置）
  - Ctrl+Shift+S ショートカット確認
  - New Project → project.json / system.json / src / build/out / asset 作成確認
  - Save Project 未設定時の案内 Log 確認
  - Save Project As → project_root 切り替え確認
  - 以後の Save Project が new_root に書くことを確認
  - Open Project → project_root 復元確認
  - キャンセル / 既存フォルダ衝突 / 不正 JSON のエラーパス確認（全 4 プローブ通過）
- Project Dialog / Save As パッチを完了扱いに変更
- HANDOFF.md を更新（優先作業を v0.2 UI 改善に変更）

### セッション 15（2026-05-24）

- `PATCH_SAVE_ROADMAP.md` / `PATCH_SAVE_CHECKLIST.md` を `old/` に移動（完了アーカイブ）
- `ui/win.py` に Project Dialog / Save As パッチを実装:
  - `_DEFAULT_PROJECT` 定数を廃止
  - `import shutil` を削除
  - `QFileDialog` を追加インポート
  - `_new_project()`: `QFileDialog.getExistingDirectory()` + `QInputDialog.getText()` でユーザーが場所・名前を選択
  - `_open_project()`: `QFileDialog.getOpenFileName()` で `project.json` を選択
  - `_save_project()`: `project_root is None` 時に案内 Log を出して中断
  - `_save_project_as()`: 新規追加。別名保存で `project_root` を切り替え
  - `_ensure_project_root()`: fallback を廃止（`project_root` をそのまま返すのみ）
  - `_build()`: `_ensure_project_root()` 呼び出しを直接 `project_root` 参照に変更
  - File メニュー: セパレータ追加・`Save Project As...` 追加
  - Ribbon File タブ: `Save Project As...` ボタン追加
- `tests/test_project_dialog.py` を新規作成（15 件）
- `pytest tests/` 120 件全通過
