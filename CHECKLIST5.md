# AKDev CHECKLIST 5

> v0.4 Visual Debug Canvas の進捗管理チェックリスト。
> 設計詳細は `ROADMAP5.md` を参照。

---

# 0. 事前確認

* [x] ROADMAP5.md / CHECKLIST5.md が作成されている
  - 完了条件: このファイルと ROADMAP5.md が存在し、セクション構成が揃っている
* [x] pytest 159 件全通過を確認する
  - 完了条件: `pytest tests/` が 159 PASSED で通過する（v0.3 完了時点の基準）
* [x] HANDOFF.md が v0.4 の優先作業を指している
  - 完了条件: HANDOFF.md の「次回の主作業」が v0.4 Visual Debug Canvas になっている

---

# 1. AK32 命令セット拡張（完了）

## 1.1 ADD / SUB 命令

* [x] `core/cpu.py` に ADD 命令（opcode 0x04）を実装する
  - 完了条件: `regs[rd] = regs[rs] + regs[rt]`、Z フラグ更新
* [x] `core/cpu.py` に SUB 命令（opcode 0x05）を実装する
  - 完了条件: `regs[rd] = regs[rs] - regs[rt]`、Z フラグ更新（32-bit wrapping）
* [x] `core/cpu.py` に ADDI 命令（opcode 0x0A）を実装する
  - 完了条件: `regs[rd] = regs[rs] + imm8`（符号なし拡張）、Z フラグ更新

## 1.2 LD / ST 命令

* [x] `core/cpu.py` に LD 命令（opcode 0x06）を実装する
  - 完了条件: `regs[rd] = bus.read(regs[rs])`、Z フラグ更新
* [x] `core/cpu.py` に ST 命令（opcode 0x07）を実装する
  - 完了条件: `bus.write(regs[rd], regs[rs])`、フラグ更新なし

## 1.3 JMP / BEQ 命令

* [x] `core/cpu.py` に JMP 命令（opcode 0x08）を実装する
  - 完了条件: `pc = imm16`（絶対アドレスジャンプ）、フラグ更新なし
* [x] `core/cpu.py` に BEQ 命令（opcode 0x09）を実装する
  - 完了条件: `if regs[rs] == regs[rt]: pc += signed(rel8) * 4`、フラグ更新なし
  - BEQ の基準 pc は「BEQ 命令の次の命令アドレス」（`pc_after_branch`）

## 1.4 r0 固定ゼロの保証

* [x] ADD / SUB / LD / ADDI 命令が r0 への書き込みを無視することを確認する
  - 完了条件: rd=0 の場合、regs[0] が 0 のまま維持される（既存の r0 固定ゼロ仕様を継承）

---

# 2. アセンブラ更新（完了）

## 2.1 新命令パーサ

* [x] `asm/asm.py` に ADD / SUB / ADDI のパーサを追加する
  - 完了条件: `ADD r1, r2, r3` → `[0x04, 0x01, 0x02, 0x03]`
* [x] `asm/asm.py` に LD / ST のパーサを追加する
  - 完了条件: `LD r1, [r2]` → `[0x06, 0x01, 0x02, 0x00]`、`ST [r1], r2` → `[0x07, 0x01, 0x02, 0x00]`
* [x] `asm/asm.py` に JMP のパーサを追加する
  - 完了条件: `JMP label` / `JMP 0x0010` → `[0x08, 0x00, imm_hi, imm_lo]`
* [x] `asm/asm.py` に BEQ のパーサを追加する
  - 完了条件: `BEQ r1, r2, label` → `[0x09, r1, r2, rel8]`（rel8 はラベルから計算）

## 2.2 2-pass アセンブル

* [x] Pass 1 でラベルのアドレスを収集する
  - 完了条件: 前方参照ラベルを含む JMP / BEQ が正しくアセンブルできる
* [x] Pass 2 で JMP の imm16 / BEQ の rel8 を解決する
  - 完了条件: `BEQ rs, rt, label` の rel8 が正しい値になる
* [x] rel8 の範囲チェック（-128〜+127）をエラーとして報告する
  - 完了条件: 範囲外の場合 `AsmError` を発生させる
* [x] 既存の LDI / OUT / NOP / HALT の動作を維持する（回帰テスト）

## 2.3 address_map 生成

* [x] `assemble_ex()` を追加して `address_map: dict[int, int]` を返す
  - 完了条件: `address_map[addr] = line_no`（0-origin 行番号）が正しく生成される
  - 完了条件: `assemble()` は bytes を返すまま維持（既存コードへの影響なし）
* [x] `address_map` が逆引き（`addr → line`）できることを確認する
  - 完了条件: `address_map[cpu.pc]` でエディタのハイライト行番号が取れる

---

# 3. Canvas UX Patch 1A — ドラッグ＆ドロップ・中央配置

## 3.1 Parts Library ドラッグ有効化

* [x] Parts Library（`QTreeWidget`）でドラッグを有効にする
  - 完了条件: パーツ行をドラッグできる状態になる（`setDragEnabled(True)`）
* [x] ドラッグデータ（`part_id`）を `QMimeData` に乗せる
  - 完了条件: ドラッグ開始時に `part_id` が `mimeData().text()` で取得できる

## 3.2 Canvas ドロップ受け付け

* [x] `Canvas` に `setAcceptDrops(True)` を設定する
* [x] `Canvas` に `dragEnterEvent` / `dragMoveEvent` を追加する
  - 完了条件: Canvas 上をドラッグ中にカーソルが変わる
* [x] `Canvas` に `dropEvent` を追加する
  - 完了条件: ドロップ時に `part_id` を取得できる
* [x] `Canvas.set_part_library(lib: dict)` を追加して `dropEvent` 内で参照できるようにする
* [x] ドロップ位置（scene 座標）に `PartNode` を配置する
  - 完了条件: `mapToScene(event.position().toPoint())` で scene 座標変換が正しく行われる

## 3.3 add_part() の中央配置変更

* [x] `Canvas.add_part_at(part, scene_pos)` を追加する
  - 完了条件: 指定 scene 座標に `PartNode` を作成・追加できる
* [x] `Canvas.add_part()` を viewport 中央付近配置に変更する
  - 完了条件: `mapToScene(viewport().rect().center())` を起点にする
* [x] 連続追加時に `_add_offset` で少しずつずらす
  - 完了条件: 同じパーツを連続追加しても完全に重ならない（20px ずつオフセット）
* [x] `_place_col` / `_place_row` による旧グリッド配置コードを削除する

## 3.4 保存・回帰確認

* [x] 追加されたパーツが `export_parts()` の対象になることを確認する
  - 完了条件: ドロップ追加したパーツが Save → Open 後に復元される
* [x] 既存のコンテキストメニュー「複製」「削除」が動作することを確認する
* [x] pytest 全件通過を確認する（2026-05-24: 246 件）

---

# 4. Canvas UX Patch 1B — Zoom / Grid 表示（完了）

* [x] `Canvas.zoom_in()` を追加する
  - 完了条件: `scale(1.25, 1.25)` でズームインする（上限 10.0 で打ち止め）
* [x] `Canvas.zoom_out()` を追加する
  - 完了条件: `scale(0.8, 0.8)` でズームアウトする（下限 0.1 で打ち止め）
* [x] `Canvas.reset_zoom()` を追加する
  - 完了条件: `resetTransform()` で等倍に戻る
* [x] `Canvas.fit_to_view()` を追加する
  - 完了条件: `fitInView(scene.itemsBoundingRect())` で全パーツが収まる（アイテム無しでクラッシュしない）
* [x] Ribbon View タブにズームボタン（Zoom In / Zoom Out / Reset Zoom / Fit）を追加する
* [x] `GridScene(QGraphicsScene)` を作成して `drawBackground()` でグリッド線描画する
  - 完了条件: `GRID_SIZE = 20` の格子線が Canvas 背景に表示される
* [x] Grid 表示 on/off トグル（View タブ）を追加する
* [x] マウスホイールでズームイン/ズームアウトできるようにする
  - 完了条件: `Canvas.wheelEvent()` を追加し、`angleDelta().y()` でズームイン/アウトを振り分ける
  - 完了条件: `setTransformationAnchor(AnchorUnderMouse)` でホイール位置を中心に拡大縮小する
* [x] 右ドラッグで Pan（画面平行移動）できるようにする
  - 完了条件: `mousePressEvent` / `mouseMoveEvent` / `mouseReleaseEvent` を追加し、右ボタンドラッグでスクロールバーを動かす
  - 完了条件: ドラッグ中は `ClosedHandCursor` になる
  - 完了条件: 移動量が閾値（`_PAN_THRESHOLD = 4px`）未満の場合はコンテキストメニューを出す（短押し扱い）
  - 完了条件: 左ドラッグの範囲選択 / 右クリックメニューを壊さない
* [x] pytest 全件通過を確認する（2026-05-25: 276 件）

---

# 5. Grid / Snap Patch（完了）

* [x] `PartNode.itemChange()` をオーバーライドして Snap to Grid を実装する
  - 完了条件: `ItemPositionChange` 時にグリッドサイズで丸める
  - `PartNode._snap_enabled` フラグを追加、`set_snap()` メソッドを追加
* [x] `Canvas.set_snap(enabled: bool)` を追加する
  - 完了条件: 全 `PartNode` の `_snap_enabled` フラグを一括更新できる
  - 新規ノード（`add_part_at`・`import_parts`）も現在の snap 設定を継承する
* [x] View タブに「Snap」チェックボックスを追加する
  - 初期値: OFF（自由配置）
* [x] ドロップ時（`add_part_at()`）にもスナップを適用する
  - snap ON のとき、scene_pos を `round(x/g)*g` で丸めてから PartNode を配置する
* [x] pytest 全件通過を確認する（2026-05-26: 291 件）

---

# 6. Part Visual / Port Detail / Bus Connection 方針

* [x] パーツサイズ可変の方針を決める
  - 完了条件: `part.json` の `"size": [w, h]` フィールドでサイズ上書きできる設計を文書化する
* [x] `part.json` の `default_color` 方針を決める
  - 完了条件: カテゴリ色以外に `part.json` の `"color"` で上書きできる方針を ROADMAP5.md に記載する
* [x] `system.json` の instance color 方針を決める
  - 完了条件: インスタンス別上書き方針を ROADMAP5.md に記載する
* [x] 大量ポートは常時表示せず Port Detail ウィンドウで表示する方針を決める
  - 完了条件: Port Detail ウィンドウの表示形式・開き方の方針を ROADMAP5.md に記載する
* [x] `system.json` の `connections` 保存形式を決める
  - 完了条件: `from` / `to` の JSON 構造が ROADMAP5.md に記載されている

---

# 7. Bus Connection Patch

## 7.1 接続データ構造（完了）

* [x] `Canvas._connections: list[dict]` と `Canvas._conn_seq: int` を追加する
  - 完了条件: `__init__` に `self._connections = []` と `self._conn_seq = 0` が追加される
* [x] `Canvas._next_conn_id()` を追加する
  - 完了条件: `conn_0001` / `conn_0002` 形式の連番 ID を返す
* [x] `Canvas.add_connection()` を追加する
  - 完了条件: `from_node_id`, `from_port`, `to_node_id`, `to_port`, `kind`, `width`, `label` を受け取り `_connections` に追加する
  - 完了条件: 接続情報を dict で返す

## 7.2 export_canvas / import_canvas（完了）

* [x] `Canvas.export_canvas()` を追加する
  - 完了条件: `{"parts": [...], "connections": [...]}` を返す
  - 完了条件: 既存の `export_parts()` を内部で使用し、互換を保つ
* [x] `Canvas.import_canvas()` を追加する
  - 完了条件: `data["parts"]` と `data["connections"]` を読み込む
  - 完了条件: `clear=True` のとき `_connections` / `_conn_seq` もリセットする
  - 完了条件: 既存の `import_parts()` を内部で使用し、互換を保つ
  - 完了条件: import 後に `_conn_seq` が読み込んだ最大 ID 番号以上になる

## 7.3 テスト（完了）

* [x] `tests/test_canvas_connections.py` を新規作成する
  - 完了条件: conn_id 形式 / 連番 / add_connection / export_canvas / import_canvas を検証
  - 完了条件: 既存 `export_parts()` / `import_parts()` の動作を壊していないことを確認

## 7.4 接続線描画（完了）

* [x] `QGraphicsPathItem` ベースの `ConnectionLine` クラスを作成する
  - 完了条件: `conn_id` / `from_node_id` / `to_node_id` を保持し、`update_line(p1, p2)` でパスを更新できる
  - 完了条件: bus は太めペン（幅 3.0）、signal / clock / reset は細めペン（幅 1.5）
  - 完了条件: `zValue = -1`（PartNode の背面）
* [x] `Canvas._conn_items: dict[str, ConnectionLine]` を追加する
  - 完了条件: `add_connection()` 後に `ConnectionLine` がシーンに追加される
  - 完了条件: `import_canvas()` 後に接続線が復元される（clear=True で削除・再構築）
* [x] `Canvas.update_connections()` を追加する
  - 完了条件: 接続先ノードの中心座標で線の両端を更新する
  - 完了条件: `PartNode.setPos()` 後に `_pos_changed_cb` 経由で自動呼び出しされる
* [x] port-to-port クリック操作でユーザーが接続を作成できるようにする
  - 完了条件: `PortDot(QGraphicsEllipseItem)` を PartNode の右端中央に配置し、クリックで接続開始/確定できる
  - 完了条件: 1回目クリックで `_pending_port` にセット（amber 色変化）、2回目クリックで `add_connection()` 呼び出し
  - 完了条件: 同じ node_id のポートを 2 回クリックした場合は接続をキャンセルする
  - 完了条件: `Canvas._on_port_click(dot)` で状態機械を管理する

## 7.5 配線 UX 改善 — 右クリックメニュー起点 + マンハッタン配線（完了）

* [x] 配線操作を「PortDot クリック方式」から「右クリックメニュー起点の wire mode 方式」に変更する
  - 完了条件: `Canvas._mode` ("design" / "wire") でモードを管理する
  - 完了条件: `Canvas.set_mode(mode)` で "design" に切り替えると wire state をキャンセルする
  - 完了条件: `Canvas._start_wire(node_id, port_name)` で wire mode に入り、dashed preview item をシーンに追加する
  - 完了条件: `Canvas._cancel_wire()` で preview を削除し design mode に戻る
  - 完了条件: `Canvas._finish_wire(to_node_id, to_port_name)` で接続を確定し `add_connection()` を呼ぶ
  - 完了条件: `Canvas._add_waypoint(scene_pos)` でグリッドスナップした中継点を追加する
  - 完了条件: `Canvas._update_wire_preview(cursor_scene_pos)` で mouse 移動に合わせて preview を更新する
* [x] 右クリックメニューを wire mode 対応に更新する
  - 完了条件: design mode の PartNode 右クリック → "接続を開始" メニューを追加
  - 完了条件: wire mode の PartNode 右クリック → "ここに接続" / "キャンセル" メニューを表示
  - 完了条件: wire mode のキャンバス空白右クリック → waypoint を追加する
  - 完了条件: PortDot への右クリックヒットを parentItem() PartNode に解決する
* [x] `add_connection()` に `route` / `color` 引数を追加する
  - 完了条件: `route: list[QPointF] | None` を受け取り、`[{"x":..,"y":..}]` 形式で conn dict に保存する
  - 完了条件: `color: str` を受け取り conn dict に保存する
  - 完了条件: 既存の呼び出しは引数省略で動作維持する
* [x] `ConnectionLine` をマンハッタン配線に更新する
  - 完了条件: `update_route(points: list[QPointF])` を追加し H-then-V Manhattan routing でパスを描画する
  - 完了条件: `update_line(p1, p2)` は `update_route([p1, p2])` のラッパーとして維持する
  - 完了条件: `color` 引数を追加し、`_KIND_COLORS` dict（bus: #66ccff など）から色を選択する
* [x] `update_connections()` を route 対応に更新する
  - 完了条件: `conn.get("route", [])` から waypoints を読み、`update_route([p1] + waypoints + [p2])` を呼ぶ
* [x] `import_canvas(clear=True)` で wire mode をリセットする
  - 完了条件: `_cancel_wire()` を呼び、`_mode = "design"` に戻す
* [x] テスト
  - 完了条件: `tests/test_canvas_wire_mode.py` を新規作成（37 件）
  - 完了条件: `tests/test_canvas_port_connect.py` から `_click_cb` チェックの 2 件を削除
  - 完了条件: pytest 405 件全通過

---

# 7.6 Wire Routing Patch 2 — 障害物回避と頂点編集（完了）

* [x] `_grid_pos(p)` / `_compress_path(path)` モジュール関数を追加する
  - 完了条件: `_grid_pos(QPointF(40,60)) == (2,3)`
  - 完了条件: `_compress_path` が直線セルを圧縮し曲がり角のみ残す
* [x] `_block_cells(excl_ids)` を `Canvas` に追加する
  - 完了条件: 各 `PartNode` の bounding rect に 1 セルマージンを加えたセル集合を返す
  - 完了条件: `excl_ids` に含まれるノードは除外する（自ノード衝突回避）
* [x] `_route_segment(start, end, blocked)` BFS を実装する
  - 完了条件: 障害物を避けて H/V 移動でゴールまで経路を返す
  - 完了条件: パスが見つからない場合は H→V Manhattan フォールバックを返す
* [x] `_route_grid(start, end, waypoints, blocked)` を実装する
  - 完了条件: 各セグメントを `_route_segment` で接続し、端点を正確な座標に置き換える
* [x] `update_connections()` を BFS ルーティングに更新する
  - 完了条件: `_route_grid` の結果で `line.update_route()` を呼ぶ
  - 完了条件: `conn["route"]` にはユーザー指定 waypoint のみを保存（BFS 結果は保存しない）
* [x] `RouteHandle` クラスを追加する
  - 完了条件: `QGraphicsRectItem` ベースの 6×6px ドラッグ可能ハンドル
  - 完了条件: `itemChange` で grid スナップ、位置変更時に `_on_handle_moved` コールバックを呼ぶ
* [x] `_show_handles()` / `_hide_handles()` / `_on_handle_moved()` を `Canvas` に追加する
  - 完了条件: wire mode 突入時 (`_start_wire`, `set_mode("wire")`) にハンドル表示
  - 完了条件: wire mode 退出時 (`_cancel_wire`, `set_mode("design")`) にハンドル非表示
  - 完了条件: ハンドルドラッグで `conn["route"]` を更新し `update_connections()` を再描画
* [x] `Canvas.mode_changed = Signal(str)` を追加する
  - 完了条件: `_start_wire` / `set_mode("wire")` で `"wire"` を emit
  - 完了条件: `_cancel_wire` / `set_mode("design")` で `"design"` を emit
* [x] `ui/win.py` に Wire Mode チェックボタンを追加する
  - 完了条件: View タブ Ribbon に "Wire Mode" checkable ボタンを追加
  - 完了条件: `canvas.mode_changed` でボタン状態を同期する
* [x] テスト
  - 完了条件: `tests/test_canvas_routing.py` を新規作成（35 件）
  - 完了条件: pytest 440 件全通過

---

# 8. Memory Viewer パネル（完了）

## 7.1 パネル実装

* [x] `ui/memview.py` を新規作成する
  - 完了条件: `MemoryViewer(QDockWidget)` クラスを実装し、`update_from_ram(ram_part)` メソッドを持つ
* [x] hex ダンプ表示を実装する
  - 完了条件: 1 行 16 bytes（アドレス列 + 16 bytes hex 列 + ASCII 列）の固定フォント表示
* [x] PC 位置の行ハイライトを実装する
  - 完了条件: `highlight_addr(pc)` メソッドで PC が指す行を薄い黄色でハイライトできる（メソッドのみ実装、本格連携は セクション 9）

## 7.2 win.py への組み込み

* [x] `ui/win.py` に `MemoryViewer` を追加する
  - 完了条件: 下部タブ（UART Console / Bus Trace と並ぶ）に "Memory" タブとして表示される
* [x] Build 完了後に Memory Viewer を更新する
* [x] Run / Step 完了後に Memory Viewer を更新する
* [x] Reset 後に Memory Viewer を更新する

---

# 9. PC ハイライト

## 8.1 エディタへの実装

* [ ] `ui/editor.py` に `highlight_line(line_no)` メソッドを追加する
  - 完了条件: 指定行全体を薄い緑色でハイライトする（`QTextEdit.extraSelections()` を使用）
  - 完了条件: 既存の `AsmHighlighter` シンタックスハイライトと共存する
* [ ] `ui/editor.py` に `clear_highlight()` メソッドを追加する

## 8.2 win.py との連携

* [ ] `win.py` の `_build()` で `address_map` を `self._address_map` に保存する
* [ ] Step 後に `cpu.pc` → `address_map` → `highlight_line()` の連携を実装する
* [ ] Run 後にハイライトを最終 pc 行に更新する
* [ ] Reset / Build 時にハイライトをクリアする

---

# 10. Canvas Signal Overlay

## 9.1 Bus への last_transactions 追加

* [ ] `core/sim.py` の `Bus` に `last_transactions: dict` を追加する
  - 完了条件: `last_transactions[part_name] = ("READ" | "WRITE", addr, val)` が最新トランザクションを保持する
* [ ] `Bus` のトランザクション処理で `last_transactions` を更新する
* [ ] `Bus.reset_transactions()` を追加する

## 9.2 PartNode へのオーバーレイ表示

* [ ] `ui/canvas.py` の `PartNode` に `set_overlay(text)` メソッドを追加する
  - 完了条件: `QGraphicsSimpleTextItem` でノード右下に小さなテキストを表示できる
* [ ] オーバーレイテキストのフォント・色を設定する（8〜9pt）

## 9.3 win.py との連携

* [ ] Step / Run 後に `bus.last_transactions` を参照してオーバーレイを更新する
* [ ] Reset 時に全パーツノードのオーバーレイをクリアする
* [ ] Build 時にオーバーレイをクリアする

---

# 11. サンプルプログラム（完了）

## 10.1 src/fib.asm

* [x] `src/fib.asm` を作成する
  - 完了条件: ADD / ST / ADDI / BEQ / JMP を使ったフィボナッチ数列プログラムが書けている
  - 完了条件: Build → Run で RAM[0x0040..0x005C] に 0, 1, 1, 2, 3, 5, 8, 13 が格納される
* [x] `src/hello.asm` が変更されていないことを確認する
  - 完了条件: 既存の hello.asm が Build → Run → UART "Hi" のまま動作する

---

# 12. テスト

## 11.1 CPU テスト（完了）

* [x] `tests/test_cpu_v04.py` を新規作成する（30 件追加）

## 11.2 アセンブラテスト（完了）

* [x] `tests/test_asm_v04.py` を新規作成する（45 件追加）

## 11.3 Canvas UX テスト（完了）

* [x] `tests/test_canvas_ux.py` を新規作成する（12 件追加）
  - 完了条件: `add_part_at()` / `add_part()` の配置位置テスト
  - 完了条件: ドラッグ&ドロップの scene 座標変換テスト

## 11.4 fib フロー統合テスト（完了）

* [x] `tests/test_v04_flow.py` を新規作成する（10 件追加）

## 11.5 回帰テスト

* [x] `pytest tests/` 全件通過を確認する（2026-05-24 時点: 234 件）
* [x] Canvas UX Patch 1A 後に `pytest tests/` 全件通過を確認する（246 件）
* [x] Canvas UX Patch 1B 後に `pytest tests/` 全件通過を確認する（261 件）

---

# 13. v0.4 でやらないこと（確認）

* [ ] CALL / RET 命令は実装しない（→ v0.5）
* [ ] IN 命令は実装しない（→ v0.5）
* [ ] ブレークポイント設定 UI は実装しない（→ v0.5）
* [ ] バスライン上の信号アニメーションは実装しない（→ v0.5）
* [ ] Port 状態の詳細オーバーレイは実装しない（→ v0.5）
* [ ] VS Code Companion は実装しない（→ v0.5）
* [ ] localhost HTTP / WebSocket サーバーは実装しない（→ v0.5）

---

# 14. HANDOFF 更新

* [ ] HANDOFF.md に v0.4 の完了内容を追記する
* [ ] 次回の主作業を v0.5 AKDev VS Code Companion に更新する
* [ ] pytest 件数を HANDOFF.md に記録する
