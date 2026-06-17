# PATCH_BUS_PROTOCOL_VALIDATION_V08 — ROADMAP（設計資料）

> v0.8（Device Expansion & Connection Validation）の **3 番目の候補パッチ**の設計資料。
> 本書は設計のみ。**実装・テスト追加・part.json 変更・挙動変更・commit/push は行わない。**
> 親計画: `ROADMAP8.md` / `CHECKLIST8.md`。所見: `V08_CODEBASE_REVIEW.md`。
> 前提: `PATCH_PORT_SCHEMA_V08`（ports v2 / `core/ports.py`）と
> `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08`（`core/port_validation.py` / warning-only）完了
> （`pytest tests/` 913 passed）。

---

## 1. 目的

- port 対 port の検証から一段進め、**bus 全体の構造**として正しい構成かを診断する。
- `bus.master` / `bus.slave` の関係を **bus group**（bus 接続で繋がったまとまり）として捉える。
- CPU / bridge などの master から RAM/UART などの slave へ繋がっているかを診断する。
- 1 つの bus group に **複数 master** がいる問題、**master 不在**、**slave 不在**を検出する。
- Address Map と接続構造を突き合わせる**到達性診断の土台**を作る（本格到達性は次段）。
- 今回も **warning only**。接続ブロックはしない。port validation の issue 構造と互換にする。

### スコープ（明確化）

本パッチは「**bus group の構築 + group 単位の master/slave 数診断 + 表示**」まで。
bridge 越しの完全 routing、多階層到達性、複数 device 本対応は**次パッチ以降**。

---

## 2. 現在の問題

- `core/port_validation.py` は **port 対**（direction/width/role/kind）は見るが、**bus 全体の構造**は見ない。
- 同一 bus に複数 master がぶら下がっても、port 対の役割一致（master↔slave）チェックだけでは
  「group として master が 2 個」を検出できない。
- slave だけで master がいない bus、master だけで slave がいない bus を全体として検出していない。
- Address Map 上の device と Canvas 接続構造の整合（device が bus 上にいるか・target CPU から届くか）は未診断。
- Bus Bridge（master + slave を持つ part）が入ったときの扱いが未整理。
- 今後の複数 RAM/UART・ROM/VRAM/Input 追加の前に、bus protocol の基本診断が必要。

---

## 3. bus protocol validation 方針

### 全体方針

- **warning only**（severity は `warning` / `info`。`error` でブロックしない）。
- 接続は従来どおり作成・削除でき、診断は別レイヤ。既存プロジェクト・既存テストを壊さない。
- `core/port_validation.py` の issue dict と**同じ基本形**（severity / code / message / details）を返し、
  group 単位の項目（`group_id` / `nodes`）を加える。Port Detail の既存 Validation 描画にそのまま載る
  （`conn_id` が無くても描画可能なことは確認済み）。
- 純粋関数（Qt 非依存）で実装し、将来 Diagnostics Panel / Project Validation から再利用できるようにする。

### bus group の定義（提案）

- **bus port** = part.json port のうち `base_port_type(type) == "bus"`（`core/ports.base_port_type` を再利用）。
- **bus edge** = connection の両端の論理ポートがともに bus port である接続。
  （論理ポート名は `end.get("logical_port") or end.get("port")` で解決し、node→part→`find_port` で port dict を引く。）
- **bus group** = bus edge で繋がった **(node_id, bus-port) 端点**の連結成分。
  - 同一 node が複数 bus port を持つ場合（例: bridge の master/slave）、**port 単位**で扱うため、
    bridge の 2 ポートは別 group に分かれうる（= bridge が 2 つの bus を橋渡しする自然な表現）。
  - bus 以外の connection（clock/reset/irq/serial/gpio/video など）は **対象外**（無視）。
- **評価対象**: bus edge を 1 本以上含む group のみ診断する（**未接続の単独 bus port は対象外**）。
  - 理由: 置いただけ・配線前の part の未接続 bus port まで毎回 warning すると**ノイズが多すぎる**ため。
    未接続は既存の Port Detail「unconnected」表示と将来の required-port 診断に委ねる。
  - （代替案: 単独 port も singleton group として評価。実装時に確定。本 ROADMAP は「≥1 edge」を推奨。）

### master / slave 数の判定

group 内の bus port を role で数える:

| 条件 | 判定 | code |
|---|---|---|
| masters == 0 | warning | `BUS_NO_MASTER` |
| masters >= 2 | warning | `BUS_MULTIPLE_MASTERS` |
| slaves == 0 | warning | `BUS_NO_SLAVE` |
| masters == 1 かつ slaves >= 1 | OK | — |
| role 不明（null）な bus port | role 判定からは除外（kind は bus だが master/slave 不明）。必要なら info |

> 補足: 既存の複数 CPU テスト（2 CPU を同一 RAM/UART に配線）は、この診断では
> **`BUS_MULTIPLE_MASTERS`** に該当する（同一 bus に master 2 個）。warning only なのでテストは壊れないが、
> 「target CPU 選択（`PATCH_TARGET_CPU_SELECTION_V08`/v07）」が *どの* master を実行するかを決める仕様と
> 整合する診断として妥当（bus 上に master が複数あるのは構造警告、実行対象は別途選択）。

### target CPU との関係

- 各 group に target CPU の bus port が含まれるか（group 所属）を**情報として**持てるようにする。
- target CPU から RAM/UART への**到達性診断は本パッチでは行わない**（group 所属の特定までに留め、
  本格到達性は次段 `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08` 以降）。
- **`resolve_circuit()` の挙動は変更しない**（target CPU 選択ロジックは現状維持）。
- `validate_bus_protocol(..., target_cpu_id=...)` は引数として受けるが、本パッチでは group 所属の付与のみ
  （`details` に target 所属可否を載せる程度）に留める。

### Address Map との関係

- `validate_bus_protocol(..., address_map=...)` を引数で受けられる形にしておく（将来用）。
- 本パッチでは **overlap 検出は既存 Address Map 側（`core/circuit.validate_address_map`）に任せる**。
- Address Map device が bus group 上に存在するか／target から到達可能かの本格突き合わせは**次段**。
  （任意で「Address Map に載るが bus group に居ない」を info `BUS_DEVICE_NOT_ON_BUS` として設計だけ示すが、
  実装は次段送りでよい。）

### bridge の扱い

- bus bridge は **master port と slave port を両方持つ part** として扱う（part.json は v2 で role 明示済み）。
- port 単位 group 化により、bridge の master 側と slave 側は別 group に属しうる（橋渡しの自然な表現）。
- **bridge 越しの到達性 routing は今回やらない**（次段以降）。初手は単純な per-group 診断に留める。

---

## 4. validation API 案

### 配置（推奨）

**`core/bus_validation.py`（新規）**。`core/port_validation.py`（port 対）とは分離し、bus 構造専用にする。
`core/ports.base_port_type` を再利用。Qt 非依存・純粋関数。

### 関数案

```python
def is_bus_port(port: dict) -> bool:
    """base_port_type(port['type']) == 'bus'。None/欠落でも False。"""

def build_bus_groups(nodes: list[dict], connections: list[dict]) -> list[dict]:
    """bus edge の連結成分を bus group のリストにする（port 単位・bus 以外は無視）。
    nodes: [{node_id, part}], connections: [{id, from:{node_id,port|logical_port}, to:{...}}]。"""

def validate_bus_group(group: dict) -> list[dict]:
    """1 つの group の master/slave 数を判定して issue を返す。"""

def validate_bus_protocol(nodes: list[dict], connections: list[dict],
                          *, target_cpu_id: str | None = None,
                          address_map: dict | None = None) -> list[dict]:
    """build_bus_groups → 各 group を validate して集約。target/address_map は将来用。"""
```

### bus group の構造案

```python
{
    "id": "bus_group_0001",
    "nodes": ["node_0001", "node_0002"],     # group 内のユニーク node
    "ports": [                                 # group 内の bus port 端点
        {"node_id": "node_0001", "part_id": "cpu.ak32", "port": "bus", "role": "master"},
        {"node_id": "node_0002", "part_id": "mem.ram",  "port": "bus", "role": "slave"},
    ],
    "masters": [ ...portエントリ... ],
    "slaves":  [ ...portエントリ... ],
    "connections": ["conn_0001"],              # group を構成した bus edge の conn id
}
```

### validation issue の構造案（port validation と互換）

```python
{
    "severity": "warning",
    "code": "BUS_MULTIPLE_MASTERS",
    "message": "Bus group has multiple masters: cpu.ak32, cpu.ak32",
    "group_id": "bus_group_0001",
    "nodes": ["node_0001", "node_0002"],
    "details": {"masters": ["node_0001:bus", "node_0002:bus"]},
}
```

- 共通キー `severity` / `code` / `message` / `details` は port validation と同一。
- group 単位なので `from_node/...` の代わりに `group_id` / `nodes` を持つ。
- Port Detail の Validation 描画は `code` / `message` / `severity` を表示する汎用実装なので**そのまま載る**。

---

## 5. UI 反映方針

- **Log**: 接続作成/削除後に bus protocol を再評価し、warning を出す（多重出力を避けるため group 単位で簡潔に）。
- **Port Detail Panel**:
  - node 選択時: その node が属する bus group の issue（`issue["nodes"]` に当該 node を含むもの）を表示。
  - wire 選択時: その wire が bus edge なら所属 group の issue を表示（任意。node 側を主とする）。
- **Run Status Panel**: 必要なら **summary のみ**（例 "Bus warnings: 1"）。詳細は出さない（任意・最小）。
- **Canvas の wire 色変更 / 警告アイコン**: **今回はやらない**（次以降）。
- **専用 Diagnostics Panel**: **今回はやらない**（次以降。`validate_bus_protocol` の自然な受け皿）。

推奨: **今回は Log + Port Detail まで**（Run Status summary は任意）。

---

## 6. 実装方針案（今回は実装しない）

| 対象 | 変更内容（案） |
|---|---|
| `core/bus_validation.py`（新規） | `is_bus_port` / `build_bus_groups` / `validate_bus_group` / `validate_bus_protocol` + code 定数。純粋・Qt 非依存 |
| `ui/canvas.py` | `bus_validation()`（現在の nodes/connections から `validate_bus_protocol` を実行して返す read-only API）。`connections_changed` 後に Log へ warning。port validation（per-connection）と**併用**（別レイヤ） |
| `ui/port_detail.py` | node（必要なら wire）の Validation セクションに、その node が属する bus group の issue を追加（既存 port issue と合算表示） |
| `ui/win.py` | 必要なら Run Status に bus warning 件数 summary（任意・最小） |
| `core/circuit.py` | **変更しない**（resolve_circuit / target CPU / Address Map ロジックは現状維持） |
| `core/port_validation.py` | 変更しない（bus は別モジュール） |
| テスト | `tests/test_bus_protocol_validation_v08.py`（新規） |

port 解決の注意:
- 論理ポート名 = `end.get("logical_port") or end.get("port")`（既存 Canvas/Port Detail と同様）。
- part dict は v2 正規化済み（`load_parts` 経由）。テストの inline part は `core/ports.normalize_part` 想定。

---

## 7. テスト方針（実装時に追加するテスト）

- CPU master + RAM slave → issue なし
- CPU master + RAM slave + UART slave → issue なし（1 master + 複数 slave）
- RAM slave + UART slave のみ（slave 同士を bus 配線）→ `BUS_NO_MASTER`
- master のみで slave 不在の group → `BUS_NO_SLAVE`
- CPU master + 2 つ目 master（CPU/bridge）同一 bus → `BUS_MULTIPLE_MASTERS`
- bus 以外の connection（clock/irq など）は group 構築で無視される
- kind/width/direction の不一致は **port validation 側**に委ね、bus 診断では扱わない
- `build_bus_groups` が連結成分を正しく作る（複数 group・bridge で port 単位に分かれる）
- role 不明（null）な bus port の扱いがクラッシュしない
- unknown / missing port・None part でもクラッシュしない
- **warning only**: bus warning が出ても接続はブロックされない
- Port Detail に bus issue が表示される / valid group では OK 表示
- 既存 v0.7 / v0.8 テスト（port schema / port validation / address map / target cpu / circuit runtime）が壊れない
- `python -m pytest tests/` 全通過

---

## 8. 今回やらないこと

- 接続ブロック
- bus bridge の完全な routing（橋渡し到達性）
- 複数 bus 階層の完全到達性解析
- Address Map Editor
- 複数 RAM/UART 本対応
- Device Registry Refactor
- MMIO 再配置 / コード領域拡張
- CPU 命令拡張
- Input / Video / Storage 実装
- wire 色変更 / 警告アイコン表示
- Diagnostics Panel 本実装
- `core/circuit.py` の変更
- コード実装 / テスト追加 / part.json 変更
- commit / push

---

## 9. 次に続くパッチ（候補順）

1. `PATCH_BUS_PROTOCOL_VALIDATION_V08`（本パッチ — bus group 診断・warning only）
2. `PATCH_DEVICE_REGISTRY_REFACTOR_V08`（Address Map / `_make_sim` のデバイスリスト駆動化・role 正規化。
   VRAM=mem 誤認の正確化もここで）
3. `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08`（複数 RAM/UART 共存・target からの到達性本対応）
4. `PATCH_ADDRESS_MAP_EDITOR_V08`（base/size 編集・MMIO 再配置準備）

> 横断候補（`V08_CODEBASE_REVIEW.md` §4）: Diagnostics Panel / Project Validation コマンド /
> warning→error 昇格（接続ブロック）の段階導入は本パッチ後に検討。
