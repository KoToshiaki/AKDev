# AKDev ROADMAP 5

> v0.4 以降の開発計画。
> v0.3 完了時点の計画は `old/ROADMAP4.md` / `old/CHECKLIST4.md` を参照。
> 進捗管理は `CHECKLIST5.md` で行う。

---

## v0.3 到達点（2026-05-24 完了）

完了条件「**Project & Target Foundation**」達成。pytest 159 件通過。

### v0.3 実装済み一覧

| カテゴリ | 実装内容 |
|---|---|
| target.json 導入 | AK32 Baremetal 既定ターゲット、build.type による分岐 |
| tools.json 導入 | vscode / kicad 設定枠（kicad は enabled: false） |
| .vscode/ 生成 | settings.json / extensions.json を create_project() で自動生成 |
| 標準プロジェクト構造 | hdl/ / board/ / docs/ / build/rom/ / build/export/ 追加 |
| Source Type 分類 | src_type() 関数（asm/hdl/c/cpp/linker/binary/custom） |
| Build 設定分離 | internal_assembler / external_command の 2 分岐 |
| v0.5 橋渡し文書化 | localhost HTTP/WS 連携案・将来 API 案・isa.json 補完構想 |
| テスト | pytest 159 件 PASSED |

---

## v0.4 テーマ: Visual Debug Canvas（**完了: 2026-05-30**）

### 目的

**「回路設計ツールとして使える」Canvas UX を作る。**

### v0.4 完了内容まとめ

| セクション | 内容 | pytest 件数 |
|---|---|---|
| 1〜2 | AK32 命令拡張（ADD/SUB/LD/ST/JMP/BEQ/ADDI）+ アセンブラ更新 + address_map | 234 件 |
| 3 | Canvas UX Patch 1A — ドラッグ&ドロップ・中央配置 | 246 件 |
| 4 | Canvas UX Patch 1B — Zoom/Grid + ホイールズーム + 右ドラッグ Pan | 276 件 |
| 5 | Grid / Snap Patch | 291 件 |
| 6 | Part Visual / Port Detail / Bus Connection 方針確定 | 291 件 |
| 7.1〜7.3 | Bus Connection Patch — 接続データ構造 + export/import_canvas | 321 件 |
| 7.4 | 接続線描画 ConnectionLine + update_connections + _pos_changed_cb | 348 件 |
| 7.5 | Wire Mode — 右クリックメニュー起点 + マンハッタン配線 | 405 件 |
| 7.6 | Wire Routing Patch 2 — BFS 障害物回避 + RouteHandle 頂点編集 | 440 件 |
| 8 | Memory Viewer パネル（hex dump + PC ハイライト行）| 462 件 |
| 9 | PC ハイライト（エディタ現在実行行をハイライト）| 476 件 |
| 10 | Canvas Signal Overlay（bus kind 接続線を光らせる）| 505 件 |
| 11 | サンプル確認（hello.asm UART "Hi" ✅、fib.asm フィボナッチ ✅）| — |

**v0.4 最終 pytest: 505 件全通過（2026-05-30）**

**v0.4 完了イメージ（達成）:**
- ADD/SUB/LD/ST/JMP/BEQ/ADDI を使ったフィボナッチ数列プログラムが動く ✅
- Parts Library から Canvas へドラッグ&ドロップでパーツを配置できる ✅
- Zoom In/Out・Reset Zoom・Grid 表示が使える ✅
- Snap to Grid でパーツをグリッドに揃えられる ✅
- パーツ間を接続線で繋げられ、system.json に保存・復元できる ✅
- Wire Mode（右クリック起点）+ BFS 障害物回避ルーティング + RouteHandle 頂点編集 ✅
- Memory Viewer パネル・PC ハイライト・Canvas Signal Overlay ✅

---

## 1. AK32 命令セット拡張（完了: セッション 23）

### 追加命令一覧

| opcode | ニーモニック | 動作 |
|---|---|---|
| 0x04 | ADD rd, rs, rt | regs[rd] = regs[rs] + regs[rt] |
| 0x05 | SUB rd, rs, rt | regs[rd] = regs[rs] - regs[rt] |
| 0x06 | LD rd, [rs] | regs[rd] = bus.read(regs[rs]) |
| 0x07 | ST [rd], rs | bus.write(regs[rd], regs[rs]) |
| 0x08 | JMP imm16 | pc = imm16（絶対アドレスジャンプ） |
| 0x09 | BEQ rs, rt, rel8 | if regs[rs] == regs[rt]: pc += signed(rel8) * 4 |
| 0x0A | ADDI rd, rs, imm8 | regs[rd] = regs[rs] + imm8（符号なし拡張） |

---

## 2. アセンブラ更新（完了: セッション 23）

- 新命令のパーサ追加（ADD/SUB/ADDI/LD/ST/JMP/BEQ）
- 2-pass ラベル解決（JMP/BEQ の前方参照対応）
- `assemble_ex(text) -> (bytes, address_map)` を追加（既存 `assemble()` はそのまま）
- `address_map[byte_addr] = 0-origin 行番号`（PC ハイライト用）

---

## 3. fib.asm + テスト追加（完了: セッション 23）

- `src/fib.asm`: ADD/ST/ADDI/BEQ/JMP を使ったフィボナッチ数列プログラム
- `tests/test_cpu_v04.py` (30件) / `tests/test_asm_v04.py` (45件) / `tests/test_v04_flow.py` (10件)
- pytest 234 件全通過（既存 159 件 + 新規 75 件）

---

## 4. Canvas UX Patch 1A — ドラッグ＆ドロップ・中央配置

### 現状

`Canvas.add_part()` は左上 `_ORIGIN` から固定グリッドで配置する。
Parts Library からのドラッグ&ドロップには未対応。

### 設計

#### 4-1. Parts Library ドラッグ有効化

`ui/win.py` の Parts Library（`QTreeWidget`）でドラッグを有効にする。

```python
self._lib_tree.setDragEnabled(True)
self._lib_tree.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
```

ドラッグデータは `QMimeData` で `part_id` をテキストとして渡す。

`QTreeWidget` を継承した `LibTree` クラスを作り、`startDrag()` をオーバーライドしてもよいが、
`mouseMoveEvent` でシグナルを発行する最小実装でもよい。

#### 4-2. Canvas ドロップ受け付け

`Canvas` に `dragEnterEvent` / `dragMoveEvent` / `dropEvent` を追加する。

```python
self.setAcceptDrops(True)

def dropEvent(self, event):
    part_id = event.mimeData().text()
    part = self._part_library.get(part_id)
    if part is None:
        return
    scene_pos = self.mapToScene(event.position().toPoint())
    self.add_part_at(part, scene_pos)
    event.acceptProposedAction()
```

Canvas は `_part_library` を持つか、`win.py` 側でコールバックを用意する。
設計の選択肢:
- A. Canvas に `set_part_library(lib: dict)` メソッドを持たせる
- B. `win.py` の `dropEvent` を `Canvas` のサブクラスでオーバーライドする

→ A を採用（シンプルで既存の構造に合う）。

#### 4-3. add_part_at() の追加

```python
def add_part_at(self, part: dict, scene_pos: QPointF):
    """Add a PartNode at an explicit scene position."""
    node_id = self._next_node_id()
    node = PartNode(part, node_id)
    node.setPos(scene_pos)
    self.scene().addItem(node)
    self._log(f"Added: {part['name']}  ({part['id']})  [{node_id}]")
```

#### 4-4. 既存 add_part() の中央配置への変更

既存の `add_part()` は左上グリッド配置だが、
ビューの中央（viewport 中心の scene 座標）に配置するよう変更する。

```python
def add_part(self, part: dict):
    """Add a PartNode near the current viewport center."""
    center = self.mapToScene(self.viewport().rect().center())
    offset = QPointF(self._add_offset * 20, self._add_offset * 20)
    self._add_offset = (self._add_offset + 1) % 8   # 8 段階でリセット
    self.add_part_at(part, center + offset)
```

連続追加時のずれ量は `_add_offset` で制御する（0〜7 → 0〜140px）。
`_add_offset` は `__init__` で `0` に初期化し、追加のたびに `+1` する。

#### 4-5. 保存の確認

`export_parts()` / `import_parts()` は既存の実装のまま動作するため、
追加位置の変更に対して保存・復元の変更は不要。

---

## 5. Canvas UX Patch 1B — Zoom / Grid 表示

### 5-1. Zoom In / Zoom Out / Reset Zoom / Fit to View

`QGraphicsView.scale()` を使う。

```python
def zoom_in(self):
    self.scale(1.25, 1.25)

def zoom_out(self):
    self.scale(0.8, 0.8)

def reset_zoom(self):
    self.resetTransform()

def fit_to_view(self):
    items = self.scene().items()
    if items:
        self.fitInView(self.scene().itemsBoundingRect(),
                       Qt.AspectRatioMode.KeepAspectRatio)
```

Ribbon View タブ または Canvas ツールバーにボタンを追加する。

### 5-2. Grid 表示

`QGraphicsScene` をサブクラス化して `drawBackground()` をオーバーライドする。

```python
class GridScene(QGraphicsScene):
    GRID_SIZE = 20

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        if not self._grid_visible:
            return
        pen = QPen(QColor(220, 220, 220), 0.5)
        painter.setPen(pen)
        # ... draw lines every GRID_SIZE
```

Grid 表示は View タブのトグルボタンで on/off できるようにする。

---

## 6. Grid / Snap Patch

### 6-1. Snap to Grid

`PartNode.itemChange()` をオーバーライドして位置変化時にグリッドにスナップする。

```python
def itemChange(self, change, value):
    if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
        if self._snap_enabled:
            g = GridScene.GRID_SIZE
            value = QPointF(round(value.x() / g) * g, round(value.y() / g) * g)
    return super().itemChange(change, value)
```

### 6-2. Free Move / Grid Snap 切り替え

View タブに「Snap to Grid」チェックボックスを追加する。
Canvas が `set_snap(enabled: bool)` を持ち、全 PartNode の `_snap_enabled` を更新する。

### 6-3. ドロップ時 Snap

`add_part_at()` 内でスナップが有効な場合、`scene_pos` をグリッドに丸める。

---

## 7. Part Visual / Port Detail / Bus Connection 方針（確定: セッション 30）

### 7-1. パーツサイズ可変方針

v0.4 では固定サイズ（140 × 56）のまま。`_NODE_W = 140` / `_NODE_H = 56` の定数で管理する。

**将来拡張（v0.5 以降）の設計方針:**

`part.json` に省略可能な `"size"` フィールドを追加できる。

```json
{ "id": "fpga.ak100", "name": "AK100", "category": "fpga", "size": [200, 80] }
```

- フィールド未存在 または 値が `[int, int]` でない場合 → `_NODE_W` / `_NODE_H` のデフォルト値を使う
- 値は `[width_px, height_px]`（整数ピクセル単位、キャンバス座標系）
- `PartNode.boundingRect()` でサイズを返すため、`PartNode.__init__` で `part.get("size")` を参照する

実装時の変更箇所:
- `PartNode.__init__`: `self._w, self._h = part.get("size", [_NODE_W, _NODE_H])`（型チェック付き）
- `PartNode.boundingRect()`: `return QRectF(0, 0, self._w, self._h)`
- `PartNode.paint()`: `_NODE_W` / `_NODE_H` 参照を `self._w` / `self._h` に置き換え

### 7-2. default_color / instance color 方針

**現状:** カテゴリ別固定色（`_CAT_COLOR` dict、`canvas.py` に定義）。

**将来拡張（v0.5 以降）の設計方針:**

#### 優先度（低 → 高）

1. カテゴリ色（`_CAT_COLOR[category]` / `_DEFAULT_COLOR`）
2. `part.json` の `"color"` フィールド（パーツ定義色）
3. `system.json` の `"instance_color"` フィールド（インスタンス別色）

#### part.json 定義色

```json
{ "id": "cpu.ak32", "name": "AK32", "category": "cpu", "color": "#2ecc71" }
```

- `"color"` フィールドは省略可能
- 値は `"#RRGGBB"` 形式の文字列
- 値が無効 / 省略時はカテゴリ色にフォールバック
- `QColor(color_str).isValid()` で妥当性チェック

#### system.json インスタンス色

```json
{
  "parts": [
    {
      "node_id": "node_0001",
      "part_id": "cpu.ak32",
      "x": 100, "y": 80,
      "instance_color": "#e74c3c"
    }
  ]
}
```

- `"instance_color"` フィールドは省略可能
- 省略時は `part.json` の `"color"` → カテゴリ色の順でフォールバック
- `PartNode` は `_instance_color: str | None` を持ち、`paint()` で最終色を決定する

実装時の `paint()` 色解決ロジック（将来）:

```python
def _resolve_color(self) -> QColor:
    if self._instance_color:
        c = QColor(self._instance_color)
        if c.isValid():
            return c
    part_color = self._part.get("color", "")
    if part_color:
        c = QColor(part_color)
        if c.isValid():
            return c
    return _CAT_COLOR.get(self._part.get("category", ""), _DEFAULT_COLOR)
```

### 7-3. Port Detail 方針

**v0.4 では実装しない。** 方針のみ確定する。

#### 表示トリガー

| 操作 | 動作 |
|---|---|
| ノード上でダブルクリック | Port Detail ウィンドウを開く |
| ノードのコンテキストメニュー → 「ポートを見る」 | 同上 |

#### 表示内容（1 ポートにつき 1 行）

| 列 | 内容 |
|---|---|
| Name | ポート名（例: `bus_master`） |
| Direction | `in` / `out` / `inout` |
| Kind | `bus` / `signal` / `clock` / `reset` |
| Width | ビット幅（例: `32`） |
| Range | ビット範囲（例: `[31:0]`） |
| Description | 説明文 |

#### ウィンドウ形式

- `QDialog` または `QDockWidget`（フローティング）
- ノードを選択中は常時更新（選択変更で内容切り替え）
- ポート情報は `part.json` の `"ports"` フィールドから取得する（将来定義）

#### ノード上の常時表示

大量ポートをノード矩形上に常時表示しない。  
v0.4 ではノード上部にパーツ名、下部に part_id のみ表示する（現状維持）。  
ポート接続点（小円）の描画は Bus Connection Patch（セクション 8）で追加する。

### 7-4. Bus Connection 保存形式（確定）

`system.json` の `"connections"` フィールドに接続情報を保存する。

```json
{
  "connections": [
    {
      "id":    "conn_0001",
      "from":  { "node_id": "node_0001", "port": "bus_master" },
      "to":    { "node_id": "node_0002", "port": "bus_slave" },
      "kind":  "bus",
      "width": 32,
      "label": "AK32 System Bus"
    },
    {
      "id":    "conn_0002",
      "from":  { "node_id": "node_0001", "port": "uart_tx" },
      "to":    { "node_id": "node_0003", "port": "uart_rx" },
      "kind":  "signal",
      "width": 1,
      "label": ""
    }
  ]
}
```

#### フィールド仕様

| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `id` | string | ○ | 接続の一意ID（`conn_NNNN` 形式） |
| `from` | object | ○ | 接続元（`node_id` + `port`） |
| `to` | object | ○ | 接続先（`node_id` + `port`） |
| `kind` | string | ○ | `"bus"` / `"signal"` / `"clock"` / `"reset"` |
| `width` | int | ○ | ビット幅（signal/clock/reset は通常 1） |
| `label` | string | △ | 表示ラベル（省略可 / 空文字可） |

#### 方向性

- `from` → `to` の方向は論理的な方向（`out` ポートが `from`）
- 双方向バス（`inout`）は慣例として `bus_master` 側を `from` とする
- 将来的に `"bidirectional": true` フィールドを追加できる

#### v0.4 での scope

- スキーマ定義（本セクション）のみ確定
- 接続線描画・保存・復元の実装はセクション 8（Bus Connection Patch）で行う
- `export_canvas()` / `import_canvas()` への拡張はセクション 8 で設計する

---

## 8. Bus Connection Patch

### 8-1. port-to-port 接続

- PartNode 上のポート点をクリックして接続を開始
- 別のポート点でクリックして接続を確定
- `QGraphicsLineItem` または `QGraphicsPathItem` で接続線を描画

### 8-2. system.json connections 保存/復元

- `export_parts()` を `export_canvas()` に拡張し `connections` を含める
- `import_parts()` を `import_canvas()` に拡張し接続線を復元する

### 8-3. 実装スコープ

v0.4 後半で実装。スコープ:
- 接続線の描画（見た目）
- system.json への保存・復元
- 既存の Bus Trace との対応は v0.5 で行う

---

## 9. Memory Viewer パネル（後続）

### 概要

RAM の内容を hex ダンプ形式で表示する QDockWidget。
下部タブ（UART Console / Bus Trace と並ぶ）に追加する。

### 表示形式

```
Addr     00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F  ASCII
0x0000   02 01 00 48 02 02 00 69 03 01 02 00 01 00 00 00  ..H..i......
0x0010   00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
```

- 1 行 = 16 bytes（4 words）
- アドレス列（hex）+ 16 bytes hex 値列 + ASCII 列（印字可能文字のみ、それ以外 `.`）

### 実装方針

- `ui/memview.py` 新規作成、`QPlainTextEdit`（固定フォント）で実装
- Build / Run / Step / Reset 後に更新
- PC が指すアドレスの行をハイライト（薄い黄色）

---

## 10. PC ハイライト（後続）

### 概要

Step 実行時、エディタタブ上の現在実行中の命令行を視覚的にハイライトする。

### 実装方針

1. `address_map` は `assemble_ex()` で生成済み（セクション 2 完了）
2. `EditorTabs` に `highlight_line(line_no)` / `clear_highlight()` メソッドを追加
3. `win.py` の `_build()` で `address_map` を `self._address_map` に保存
4. Step/Run 後に `cpu.pc` → `address_map` → `highlight_line()` の連携

---

## 11. Canvas Signal Overlay（後続）

### 概要

System Canvas 上のパーツノードにバス最終値をオーバーレイ表示する。

### 実装方針

1. `Bus` に `last_transactions: dict[str, tuple]` を追加
2. `PartNode.set_overlay(text)` を追加（`QGraphicsSimpleTextItem`）
3. Step/Run 後に `bus.last_transactions` を参照してオーバーレイ更新

---

## v0.4 でやらないこと

| 項目 | 理由 |
|---|---|
| CALL / RET 命令 | スタック設計が必要。v0.5 以降 |
| IN 命令 | LD との役割整理が必要。v0.5 以降 |
| ブレークポイント設定 UI | v0.5 以降 |
| localhost HTTP / WebSocket サーバー | v0.5 |
| VS Code Companion | v0.5 |
| KiCad / Board 連携 | v0.6 以降 |

---

## 実装順序（更新）

1. ~~AK32 命令セット拡張~~ **完了**
2. ~~アセンブラ更新~~ **完了**
3. ~~fib.asm + テスト追加~~ **完了**
4. **Canvas UX Patch 1A** — ドラッグ&ドロップ・中央配置（次の作業）
5. **Canvas UX Patch 1B** — Zoom / Grid 表示
6. **Grid / Snap Patch**
7. **Part Visual / Port Detail / Bus Connection 方針**
8. **Bus Connection Patch**
9. Memory Viewer パネル
10. PC ハイライト
11. Canvas Signal Overlay
12. 回帰テスト

---

## v0.4 完成条件（全達成 ✅）

- [x] ADD / SUB / LD / ST / JMP / BEQ / ADDI 命令が `core/cpu.py` で動作する
- [x] `assemble_ex()` が `address_map` を返す
- [x] `src/fib.asm` が Build → Run で正しく動作する（RAM にフィボナッチ数列格納）
- [x] 既存の hello.asm → Build → Run → UART "Hi" フローを壊していない
- [x] Parts Library から Canvas へのドラッグ&ドロップでパーツ追加できる
- [x] クリック追加が Canvas 中央付近に配置される
- [x] Zoom In / Out / Reset / Fit to View が動作する
- [x] Grid 表示 / Snap to Grid が動作する
- [x] Bus Connection（接続線）が描画・保存・復元できる
- [x] Wire Mode + BFS ルーティング + RouteHandle 頂点編集が動作する
- [x] Memory Viewer パネルが Step / Run / Reset 後に更新される
- [x] Step 時にエディタの現在実行行がハイライトされる
- [x] Canvas 上の bus kind 接続線にバストランザクション時のオーバーレイが表示される
- [x] pytest 505 件全通過（2026-05-30）

---

## v0.5 以降の候補

### v0.5 候補（次の主作業 — 計画は別途 ROADMAP6.md / CHECKLIST6.md で作成）

#### 優先度 A（内部 UI 改善系）

| 候補 | 概要 |
|---|---|
| 配線色変更 UI / 設定画面 | 接続線の kind / color を GUI から変更できるようにする |
| Part Visual 拡張 | `part.json` の `size` / `color` フィールドに対応するパーツ表示 |
| Port Detail ウィンドウ | ダブルクリックでポート詳細（Name/Direction/Kind/Width）を表示 |
| 正確な Signal Overlay | bus address map からどの接続線がどのデバイスに対応するか判定 |

#### 優先度 B（外部連携系）

| 候補 | 概要 |
|---|---|
| AKDev VS Code Companion | VS Code 拡張（ASM/HDL 補完、Build/Run 連携、localhost HTTP/WS） |
| CALL / RET 命令追加 | スタック設計 + CPU 拡張 |
| IN 命令追加 | LD との役割整理 + CPU 拡張 |
| ブレークポイント設定 UI | エディタのガター + CPU tick での PC 比較 |

#### 優先度 C（長期）

| 候補 | 概要 |
|---|---|
| KiCad 基板連携 | netlist 生成 / 自動配線（v0.6 以降） |
| C コンパイラ対応 | 外部コンパイラ連携（`external_command` build type 完全実装） |
| HDL 合成 | iverilog / Yosys 連携（v0.6 以降） |
| 実機書き込み | シリアル / USB（v0.6 以降） |

### v0.5 の主軸候補

1. **配線色変更 UI / 設定画面** — 小規模、Canvas の完成度を上げる
2. **Part Visual 拡張 + Port Detail** — パーツ表示のリッチ化
3. **AKDev VS Code Companion** — 外部連携の第一歩（大規模）

→ 次回セッションで ROADMAP6.md / CHECKLIST6.md を作成して主軸を決定する。

---

## 命令エンコード仕様（v0.4 拡張後）

```
bits 31..24  opcode
bits 23..16  rd / rs（宛先または比較 reg 1）
bits 15..8   rs / rt（ソース reg または比較 reg 2）
bits  7..0   rt / imm8 / rel8
```

| opcode | ニーモニック | 動作 |
|---|---|---|
| 0x00 | NOP | なし |
| 0x01 | HALT | 実行停止 |
| 0x02 | LDI rd, imm16 | regs[rd] = imm16 |
| 0x03 | OUT [rd], rs | bus.write(regs[rd], regs[rs]) |
| 0x04 | ADD rd, rs, rt | regs[rd] = regs[rs] + regs[rt] |
| 0x05 | SUB rd, rs, rt | regs[rd] = regs[rs] - regs[rt] |
| 0x06 | LD rd, [rs] | regs[rd] = bus.read(regs[rs]) |
| 0x07 | ST [rd], rs | bus.write(regs[rd], regs[rs]) |
| 0x08 | JMP imm16 | pc = imm16 |
| 0x09 | BEQ rs, rt, rel8 | if regs[rs] == regs[rt]: pc += signed(rel8)*4 |
| 0x0A | ADDI rd, rs, imm8 | regs[rd] = regs[rs] + imm8 |
