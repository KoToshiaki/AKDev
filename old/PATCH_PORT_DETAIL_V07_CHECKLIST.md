# PATCH_PORT_DETAIL_V07 — CHECKLIST

> 設計詳細は `PATCH_PORT_DETAIL_V07_ROADMAP.md` を参照。
> 親計画: `ROADMAP7.md` / `CHECKLIST7.md`（7. Port Detail）。

---

## 実装項目

* [x] `ui/port_detail.py` `PortDetailPanel(QDockWidget)` を新規作成
  - [x] monospace QPlainTextEdit（read-only）
  - [x] `update_detail(info: dict)` / `detail_text()`
  - [x] selection: node / wire / none で分岐
  - [x] None / 欠損キーでも例外を出さない（単体テストで確認）
* [x] `build_node_info(canvas, node_id)` / `build_wire_info(canvas, conn_id)` / `render_detail(info)`
* [x] `ui/canvas.py` read-only API `node_connections(node_id)` を追加
* [x] `ui/canvas.py` read-only API `part_logical_ports(node_id)` を追加
* [x] `ui/canvas.py` `connections_changed` シグナル追加（add_connection / _remove_connection で emit）
* [x] `ui/win.py` `_setup_port_detail()`（右側 Dock・Run Status とタブ化）
* [x] `ui/win.py` `_collect_port_detail()` / `_update_port_detail()`
* [x] 更新フック: 起動時 / 選択変更 / wire 選択 / wire 解除 / 接続変更
* [x] Debug リボンに `port_detail.toggleViewAction()` を追加
* [x] 既存 Properties / Run Status / Wiring を壊さない

## 表示項目

* [x] 選択なし: `No node or wire selected`
* [x] node: node id / part id / name / category / position
* [x] logical ports: name / type(kind) / direction / width
* [x] visual ports: id / label / side / offset / kind / locked / connected
* [x] connections: conn id / from-to node / from-to port / peer node / peer part / direction / kind / width / style
* [x] wire: conn id / kind / width / from-to node / from-to part / from-to port / vp / style

## テスト項目（`tests/test_port_detail_v07.py` — 18 件）

### パネル生成
* [x] MainWin 作成時に Port Detail Panel が存在
* [x] 初期状態でクラッシュしない
* [x] 選択なしで `No node or wire selected`

### ノード選択
* [x] node id / part id / name / category 表示
* [x] logical ports（direction / kind / width）表示
* [x] visual ports 表示
* [x] connected / unconnected 表示

### 接続表示
* [x] CPU+RAM 接続で CPU 側に接続情報
* [x] peer node / peer part 表示
* [x] connection id 表示
* [x] from / to 表示

### wire 選択
* [x] wire 情報表示（from-to node）
* [x] wire style 表示（存在する場合）

### 更新
* [x] 選択変更でパネル更新
* [x] 接続削除後に更新
* [x] visual port 移動後に壊れない

### 既存互換
* [x] Properties / Run Status / Wiring 系テストが壊れない
* [x] Plan-driven / Address Map / CPU RAM Validation / Target CPU Selection / Run Status テストが壊れない

## 検証項目

* [x] `python -m pytest tests/` 全件通過（**860 passed**）
* [x] commit / push を行っていない
* [x] 作業後にドキュメントを読み返した
