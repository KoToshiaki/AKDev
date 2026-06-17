# PATCH_PORT_DETAIL_V07 — ROADMAP

> v0.7（Plan-driven Virtual Devices & Address Map）6 番目（最終候補）のパッチ。
> 親計画: `ROADMAP7.md` / 進捗: `PATCH_PORT_DETAIL_V07_CHECKLIST.md`。
> 前提: `PATCH_PLAN_DRIVEN_DEVICES_V07` / `PATCH_ADDRESS_MAP_V07` /
> `PATCH_CPU_RAM_VALIDATION_V07` / `PATCH_TARGET_CPU_SELECTION_V07` /
> `PATCH_RUN_STATUS_PANEL_V07` 完了（`pytest tests/` 842 passed）。

---

## 目的

選択中のパーツ / wire について、**論理ポート（part.json `ports`）・visual port・
direction・kind・width・connection・接続先ノード/ポート・wire/connection id** を
1 つの **Port Detail Panel** で確認できるようにする。配線デバッグと、今後の
direction/width 検証・接続可否チェック・bus protocol 検証・複数デバイス対応の土台にする。

## 現在の問題

- パーツを置き visual port を作って配線できるが、選択中パーツの「どの論理ポートが
  どの visual port に対応し、どこへ繋がっているか」をまとめて見る場所がない。
- connection の id / from-to / peer part / wire style は Properties（Wire）で一部見えるが、
  ノード視点での「このノードの全接続」一覧がない。
- part.json の `ports`（name/type）が UI から確認できない。

## 実装方針

- **read-only の概要パネル**（Run Status Panel と同方針）。新規の編集 UI は作らない。
- `ui/port_detail.py` に `PortDetailPanel(QDockWidget)` を新規作成（monospace QPlainTextEdit）。
  - `update_detail(info: dict)` で受け取った info を整形表示、`detail_text()` で文字列取得。
  - `info["selection"]` が `node` / `wire` / `none` で表示を分岐。
- 情報収集は純粋関数 `build_node_info(canvas, node_id)` / `build_wire_info(canvas, conn_id)` /
  整形 `render_detail(info)` に分離（canvas の public API のみ使用・単体テスト可能）。
- Canvas に最小の read-only API を追加（既存データ構造は変更しない）:
  - `node_connections(node_id)` … このノードに繋がる connection の一覧
  - `part_logical_ports(node_id)` … part.json の `ports`
  - `connections_changed` シグナル（add_connection / _remove_connection で emit）
- `MainWin`:
  - `_setup_port_detail()` でパネル生成し右側 Dock（Run Status とタブ化）へ追加。
  - `_collect_port_detail()`（wire 選択優先 → node 選択 → none）。
  - `_update_port_detail()` を選択変更 / wire 選択 / 接続変更 / 起動時に呼ぶ。
  - Debug リボンに `toggleViewAction()` を追加。

## 表示する情報

### 選択なし
- `No node or wire selected`（クラッシュしない）。

### ノード選択時
- **Selected Node**: node id / part id / part name / category / position
- **Logical Ports**（part.json `ports`）: name / type(kind) / direction（type から推定）/ width
- **Visual Ports**: id / linked logical port(label) / side / offset / kind / locked / connected
- **Connections**: connection id / from-node / to-node / from-port / to-port /
  peer node / peer part / direction（out/in）/ kind / width / style(あれば)

### wire 選択時
- connection id / kind / width / from-node / to-node / from-port / to-port /
  from-part / to-part / from-vp / to-vp / wire style(あれば)

> direction は part.json に明示が無いため type から推定（master→out / slave→in /
> clock・reset・irq→in / serial→bidir / それ以外→`-`）。width は未定義なら `-`。

## 更新タイミング

- 起動時（初期表示）
- Canvas の選択変更時（`selection_changed`）
- wire 選択時 / wire 選択解除時（`wire_selected` / `wire_selection_cleared`）
- 接続作成後 / 接続削除後（新規 `connections_changed`）

（visual port 移動後・Save/Load 後の自動更新は、次に選択イベントが起きた時点で反映。
最低限の「選択変更・wire 選択・接続作成/削除後」は満たす。）

## 既存 Properties / Run Status Panel との関係

- **Properties**: 選択中パーツの設定・編集（色 / Program Sources / Wire style 編集）。
- **Run Status Panel**: 実行状態の概要（target CPU / Address Map / runtime / UART）。
- **Port Detail Panel**: 選択中 node/wire のポートと接続の **確認・デバッグ**（read-only）。
- Properties / Run Status を置き換えず、共存する。既存動作は変更しない。

## テスト方針（`tests/test_port_detail_v07.py` 新規）

- パネル生成: MainWin 作成時に存在・初期 `No node or wire selected`・クラッシュしない。
- ノード選択: node id / part id / name / category 表示・logical ports（direction/kind/width）・
  visual ports・connected/unconnected 表示。
- 接続表示: CPU+RAM 接続で CPU 側に connection（peer node/part・conn id・from/to）表示。
- wire 選択: wire id / from-to node / from-to part / wire style 表示。
- 更新: 選択変更で内容更新・接続削除後に更新・visual port 移動後に壊れない。
- 既存互換: Properties / Run Status / Wiring / Plan-driven / Address Map /
  CPU RAM Validation / Target CPU Selection / Run Status Panel テストが壊れない。
- `build_node_info` / `build_wire_info` / `render_detail` の単体（none/欠損で例外なし）。

## 今回やらないこと

Port direction/width の接続可否検証 / bus protocol 検証 / 自動配線 / Port Editor /
visual port 本格編集 UI / 複数 RAM・UART 本格対応 / VRAM・Storage・Input・Display 本実装 /
MMU / 割り込み / C コンパイラ / HDL 合成 / FPGA 実機書き込み / ゲーム実行 / commit / push。

## 既存互換性の注意点

- Canvas の既存データ構造（connection / visual port dict）は変更しない（read-only API のみ追加）。
- `connections_changed` は `add_connection` / `_remove_connection` で emit。`import_canvas` は
  直接 `_connections` に追加するため emit せず（ロード時の不要発火を避ける）。
- パネルは read-only。実行ロジック・Properties・Run Status は変更しない。
- `build_*` は None / 欠損キー / 未接続 / legacy でも例外を出さない。
