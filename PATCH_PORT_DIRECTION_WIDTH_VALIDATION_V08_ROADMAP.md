# PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08 — ROADMAP（設計資料）

> v0.8（Device Expansion & Connection Validation）の **2 番目の候補パッチ**の設計資料。
> 本書は設計のみ。**実装・テスト追加・part.json 変更・挙動変更・commit/push は行わない。**
> 親計画: `ROADMAP8.md` / `CHECKLIST8.md`。所見: `V08_CODEBASE_REVIEW.md`。
> 前提: `PATCH_PORT_SCHEMA_V08` 完了（ports schema v2 / `core/ports.py` / `pytest tests/` 878 passed）。

---

## 1. 目的

- `PATCH_PORT_SCHEMA_V08` で明示した ports schema v2 の `direction` / `width` / `role` を使い、
  **配線時に接続の妥当性を判定**する。
- master-master / slave-slave / out-out / in-in / width 不一致のような不自然な接続を**早期に検出**する。
- **初手は warning / diagnostics のみ**（接続ブロックはしない）。既存プロジェクト・既存テストを壊さない。
- 検証結果を**構造化データ**として取得でき、Log と Port Detail に表示できるようにする。
- 将来の `PATCH_BUS_PROTOCOL_VALIDATION_V08` / 複数デバイス対応 / Address Map validation の土台にする。

### スコープ（明確化）

本パッチは「**port 単位の direction/width/role 整合チェック + 表示**」まで。bus 全体のトポロジ検証
（1 master 制約・到達性）や複数デバイスは**次パッチ以降**。

---

## 2. 現在の問題

- v2 で `direction`/`width`/`role` は明示されたが、**接続時にはまだ一切使われていない**。
- `ui/canvas.py` の `add_connection` は型・向き・幅を見ずにどんな組み合わせでも wire を作れる:
  - master↔master / slave↔slave のような role 不整合
  - out↔out（複数ドライバ）/ in↔in（ドライバ不在）の向き不整合
  - width 不一致（例 32 ↔ 1）
  - bus 端子と clock 端子のような **kind 違い**の接続
- `required` な port が未接続でも診断されない。
- `core/port_validation.py` 相当の**検証ロジックの単一の置き場が無い**。
- Bus protocol validation（次段）へ進む前に、まず port 対 port の基本検証が必要。

---

## 3. validation 方針

### 全体方針

- **warning only**（severity は `warning` / `info` のみ。`error` で**ブロックしない**）。
- 接続は**従来どおり必ず作成**し、検証結果は wire に付随情報として保持／Log と Port Detail に表示。
- 既存テスト・既存プロジェクトを壊さない（無検証で配線していたテストはそのまま通る）。
- 検証は**純粋関数**（Qt 非依存）で実装し、構造化 issue リストを返す。
- 検証は v2 正規化済み port を前提（`core/ports.py:normalize_part` 後）。未正規化でも crash しない。

### 判定ルール（提案）

接続データは無向（from/to は単なる両端）なので、**port 対は対称**に判定する。

#### (a) direction compatibility（向き）

| 向きの組（順不同） | 判定 | code |
|---|---|---|
| out ↔ in | OK | — |
| inout ↔ inout | OK | — |
| inout ↔ in | OK | — |
| inout ↔ out | OK | — |
| out ↔ out | warning（複数ドライバ） | `PORT_DIRECTION_MULTIPLE_DRIVERS` |
| in ↔ in | warning（ドライバ不在） | `PORT_DIRECTION_NO_DRIVER` |
| 不明/欠落 | skip（info 任意） | `PORT_DIRECTION_UNKNOWN` |

#### (b) role compatibility（bus の master/slave）

- 両端が bus 系（`role` が `master`/`slave`）のときのみ判定。
  - master ↔ slave: OK
  - master ↔ master: warning `PORT_ROLE_MASTER_CONFLICT`
  - slave ↔ slave: warning `PORT_ROLE_SLAVE_CONFLICT`
- いずれかの `role` が `null`（非 bus）: role 判定は **skip**（柔軟に扱う）。

#### (c) width compatibility（信号幅）

- 両方が既知（int）で**一致**: OK
- 両方が既知で**不一致**: warning `PORT_WIDTH_MISMATCH`
- 片方/両方が `None`（unknown）: **skip**（info `PORT_WIDTH_UNKNOWN` を出すかは任意。ノイズ回避のため既定 skip 推奨）

#### (d) kind compatibility（種別。任意・推奨）

- `base_port_type`（`core/ports.py`）が異なる接続（例 bus ↔ clock）は warning `PORT_KIND_MISMATCH`。
- 最も多い実ミスを拾えるが誤検出も出うるため、**初手は info か、設定で抑制可**にしてもよい。

#### (e) required port 未接続（node レベル・任意）

- `required: true` の port がどの connection からも参照されない場合 warning `UNCONNECTED_REQUIRED_PORT`。
- 本パッチでは **node レベル検証（`validate_node_connections`）に含める設計**とし、実装は段階的でよい。

#### (f) same-node connection / duplicate connection

- from_node == to_node: warning `SELF_CONNECTION`。
- 同一 port 対の重複接続: info/warning `DUPLICATE_CONNECTION`。
- いずれも**ブロックしない**。

> すべて warning/info。**この段階で接続を拒否・削除・色変更することはしない。**

---

## 4. validation API 案

### 配置（推奨）

純粋関数を **`core/port_validation.py`（新規）** に切り出す（Qt 非依存・単体テスト容易・将来の
bus protocol / address map validation と並べやすい）。`core/ports.py` は schema 正規化に専念させ、
検証は別モジュールに分離する。

### 関数案

```python
SEVERITY_WARNING = "warning"
SEVERITY_INFO    = "info"

def find_port(part: dict, port_name: str) -> dict | None:
    """v2 正規化済み part から名前で port を引く（無ければ None）。"""

def validate_port_pair(port_a: dict, port_b: dict, *, context: dict | None = None) -> list[dict]:
    """2 つの port dict（v2）の direction/role/width/kind 整合を判定し issue 一覧を返す。
    対称。port は normalize_port 済み想定。None/欠落でも crash しない。"""

def validate_connection(from_part: dict, from_port_name: str,
                        to_part: dict, to_port_name: str,
                        *, conn_id: str | None = None) -> list[dict]:
    """part + port 名で解決し validate_port_pair を呼ぶ。port 名が見つからなければ
    PORT_NOT_FOUND（info/warning）を返してペア判定は skip。"""

def validate_node_connections(nodes: list[dict], connections: list[dict]) -> list[dict]:
    """全 connection を走査して issue を集約（self/duplicate/required も含む）。
    nodes: [{node_id, part}], connections: [{id, from:{node_id,port|logical_port}, to:{...}}]。"""
```

### issue 構造案

```python
{
    "severity": "warning",                 # "warning" | "info"
    "code": "PORT_WIDTH_MISMATCH",         # 安定した識別子
    "message": "width mismatch: bus(32) <-> serial(1)",
    "conn_id": "conn_0003",                # 任意（node 走査時）
    "from_node": "node_0001",
    "from_port": "bus",
    "to_node": "node_0004",
    "to_port": "serial",
    "details": {"from_width": 32, "to_width": 1},
}
```

- `code` は安定識別子（テスト・将来の抑制設定で参照）。
- `from_*` / `to_*` は port 対判定では nominal な向き、node 走査では connection の from/to を採用。
- `details` は code ごとの補助情報（任意）。

---

## 5. UI 反映方針

- **Log**: 接続作成時（`add_connection`）に warning を 1 行ずつ出す（例
  `Wire conn_0003: PORT_WIDTH_MISMATCH — width mismatch ...`）。
- **Port Detail Panel**: 選択中 wire / node の validation issue を「Validation」セクションとして表示
  （`build_wire_info` / `build_node_info` に issues を載せ、`render_detail` で描画）。
- **Run Status Panel**: 今回は**出さない**（実行状態の概要であり接続診断とは別軸）。
- **Canvas の wire 色変更 / 警告アイコン**: **今回はやらない**（次以降）。
- **専用 Diagnostics Panel**: **今回はやらない**（次以降。`validate_node_connections` を回す受け皿として将来追加）。

推奨: **今回は Log + Port Detail まで**。

---

## 6. 実装方針案（今回は実装しない）

| 対象 | 変更内容（案） |
|---|---|
| `core/port_validation.py`（新規） | `validate_port_pair` / `validate_connection` / `validate_node_connections` / `find_port` と code 定数。Qt 非依存・純粋関数 |
| `ui/canvas.py` | `add_connection` 内（または直後）で from/to の part+port を解決し `validate_connection` を実行。issue を `conn["validation"]` に保持し、Log（`self._log`）へ warning 出力。**接続は従来どおり作成**。`connections_changed` は現状どおり |
| `ui/port_detail.py` | `build_wire_info` / `build_node_info` に `validation` を載せ、`render_detail` に「Validation」セクション追加（issue 無しは "(none)"） |
| `ui/win.py` | 必要なら Log 体裁のみ（Canvas 側 log_fn で足りるなら変更不要） |
| `core/ports.py` | 原則変更なし（`base_port_type` 等を import して使う） |
| `core/circuit.py` | **変更しない**（ロール判定・VRAM=mem 正確化は別パッチ） |
| テスト | `tests/test_port_validation_v08.py`（新規） |

port 解決の注意:
- connection 端点の論理ポート名は `end.get("logical_port") or end.get("port")`（既存 Port Detail と同様）。
- part dict は `canvas.get_node(node_id).part()`（v2 正規化済み）。

---

## 7. テスト方針（実装時に追加するテスト）

- direction: out→in OK / inout↔inout OK / inout↔in OK / inout↔out OK / out↔out warning / in↔in warning
- role: master↔slave OK / master↔master warning / slave↔slave warning / role=null は skip
- width: 一致 OK / 不一致 warning / 片方 None は skip（または info）/ 両方 None skip
- kind: bus↔clock などの kind 違いの扱い（warning か info）
- required: 未接続 required port の検出（node レベル・段階導入）
- self / duplicate connection の検出
- unknown port 名（part に無い）でも crash しない（`PORT_NOT_FOUND`）
- None / 欠落 port dict でも crash しない
- **warning only**: issue が出ても `add_connection` は wire を作る（接続は成功する）
- Port Detail に validation issue が表示される / issue 無しは "(none)"
- 既存 wiring 系（`test_wiring_ports_v05` / `test_port_drag_connect_v05` /
  `test_wire_select_delete_v05` / `test_wire_style_v05` / `test_port_detail_v07`）が壊れない
- `python -m pytest tests/` 全通過

---

## 8. 今回やらないこと

- 接続ブロック（不正接続の拒否・削除）
- wire 色変更 / 警告アイコン表示
- Diagnostics Panel 本実装
- Bus protocol validation 本体（1 master 制約・到達性）
- 複数 RAM/UART 対応
- Device Registry Refactor
- Address Map Editor
- MMIO 再配置 / コード領域拡張
- CPU 命令拡張
- Input / Video / Storage 実装
- `core/circuit.py` の変更
- コード実装 / テスト追加 / part.json 変更
- commit / push

---

## 9. 次に続くパッチ（候補順）

1. `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08`（本パッチ — port 対 port 検証・warning only）
2. `PATCH_BUS_PROTOCOL_VALIDATION_V08`（bus master/slave・1 master 制約・到達性）
3. `PATCH_DEVICE_REGISTRY_REFACTOR_V08`（Address Map / `_make_sim` のデバイスリスト駆動化・role 正規化）
4. `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08`（複数 RAM/UART 共存）

> 横断候補（`V08_CODEBASE_REVIEW.md` §4）: diagnostics コマンド / テストフィクスチャ整理 /
> 接続ブロック化（warning→error 昇格）の段階導入は本パッチ後に検討。
