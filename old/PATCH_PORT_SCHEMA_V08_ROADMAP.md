# PATCH_PORT_SCHEMA_V08 — ROADMAP（設計資料）

> v0.8（Device Expansion & Connection Validation）**最初の候補パッチ**の設計資料。
> 本書は設計のみ。**実装・part.json 変更・テスト追加・挙動変更・commit/push は行わない。**
> 親計画: `ROADMAP8.md` / `CHECKLIST8.md`。コードベース所見: `V08_CODEBASE_REVIEW.md`。
> 前提: v0.7 PHASE COMPLETE（`pytest tests/` 860 passed）。

---

## 1. 目的

- part.json の `ports` 定義を、今後の **接続検証（direction/width/bus protocol）に耐える形へ正規化**する。
- 現在の `name` / `type` 中心の定義に、`direction` / `width` / `role` / `required` / `description` を明示し、
  part 単位で `schema_version` を持たせる。
- **direction / width / role の単一の真実源**を part.json 側に確立し、Port Detail Panel の「type からの推定」
  をやめ、明示値を表示できる前提を作る。
- 次パッチ `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08` の土台にする（本パッチは schema と表示のみ・検証はしない）。

### スコープ外（明確化）

本パッチは「**スキーマ正規化 + 正規化層 + 表示**」まで。**接続可否の検証・ブロック・警告は次パッチ**で行う。

---

## 2. 現在の問題

- part.json の各 port は `{"name","type"}` のみ（`parts/**/*.json` 全 11 種で共通）。`direction` / `width` が無い。
- `type` が kind と role を兼ねている（例 `bus.master` / `bus.slave`）。master/slave/in/out を**文字列から推定**している。
- `ui/port_detail.py` の `direction_from_type()` は type から direction を推定（master→out / slave→in /
  clock・reset・irq→in / serial→bidir / その他→`-`）。width は `port.get("width","-")` で、**実体が無いので常に `-`**。
- **推定では正しく出せないケースがある**: `irq` は CPU 側では入力（消費）だが Timer/UART 側では出力（生成）。
  現状の type ベース推定は両方を同一に扱うため、**part 固有の direction を表現できない**。これが明示 schema を
  必要とする決定的理由。
- `core/circuit.py` のロール判定は category 依存（`_is_ram` = `category=="mem"`）。`mem.vram` も "mem" のため
  **VRAM を RAM と誤認**しうる。type/role の明示があれば将来この判定を正確化できる（本パッチでは判定変更まではしない）。
- 接続可否検証・bus protocol 検証・複数デバイス対応の前提として、現 schema は曖昧。
- `ui/lib.py:load_parts()` は `_REQUIRED = {id,name,category,ports}` を検証するのみで、ports の中身・版管理は無い。

---

## 3. 新しい ports schema 案

### 方針（2 案を比較し、B を推奨）

- **案 A（理想・type 分割）**: `type` を純粋な kind（"bus"/"clock"/"irq"…）に正規化し、master/slave は `role` へ。
  きれいだが、`type` の意味が変わるため既存参照（`port_detail.direction_from_type`、将来 `circuit.py`）を一斉に
  書き換える必要があり、破壊的。
- **案 B（推奨・後方互換重視）**: 既存 `type` はそのまま残し（`bus.master` 等も許容）、`role` / `direction` /
  `width` / `required` / `description` を**追加**する。`schema_version` で版を明示。正規化層が v1（旧形式）から
  v2 相当を補完する。既存読み出しを壊さず、明示値を新設できる。

### v2 schema（案 B）

part レベルに `schema_version` を追加。各 port は以下のフィールドを持つ:

```json
{
  "id": "cpu.ak32",
  "name": "AK32 CPU",
  "category": "cpu",
  "schema_version": 2,
  "ports": [
    {
      "name": "bus",
      "type": "bus",
      "role": "master",
      "direction": "inout",
      "width": 32,
      "required": true,
      "description": "AK32 main memory/IO bus (master)"
    },
    {
      "name": "irq",
      "type": "irq",
      "role": null,
      "direction": "in",
      "width": 1,
      "required": false,
      "description": "Interrupt request input (CPU consumes)"
    }
  ]
}
```

### フィールド定義

| フィールド | 型 | 必須 | 意味 / 規約 |
|---|---|---|---|
| `schema_version` | int（part レベル） | v2 で必須 | 無い場合は **v1** とみなす |
| `name` | str | 必須 | 既存どおり。ポート識別名 |
| `type` | str | 必須 | kind。案 B では旧値（`bus.master` 等）も許容。正規化層が base kind（`bus`/`clock`/`reset`/`irq`/`serial`/`gpio`/`video`）を併せ持てるよう扱う |
| `role` | str \| null | 任意 | bus 系のみ意味を持つ: `"master"` / `"slave"`。非 bus は `null` |
| `direction` | str | v2 で推奨 | `"in"` / `"out"` / `"inout"`。**part 固有**（例 irq は CPU=in / Timer=out）。不明は `"inout"` を既定 |
| `width` | int \| null | v2 で推奨 | 信号幅(bit)。bus=32、単線(clock/reset/irq/serial/gpio)=1、未定義は `null`（= unspecified） |
| `required` | bool | 任意 | 接続必須か（既定 `true`）。検証は次パッチ。本パッチは表示のみ |
| `description` | str | 任意 | 説明（既定 `""`） |

### legacy / unknown / unspecified の扱い

- **legacy（v1, `schema_version` 無し）**: 正規化層が以下を補完して v2 相当へ変換。
  - `role`: `type` が `*.master`→`"master"` / `*.slave`→`"slave"` / それ以外→`null`
  - `direction`: 既定 `"inout"`。bus→`"inout"`、clock/reset→`"in"`、その他は `"inout"`（**irq の in/out は v1 では
    判別不能なので `"inout"` 扱い**。正確化は part.json を v2 へ移行して明示する）
  - `width`: type 既定（bus=32 / 単線=1 / 不明=`null`）
  - `required`: `true` / `description`: `""`
- **unknown type**: base kind 不明でも壊さない。`role=null` / `direction="inout"` / `width=null` とする。
- **unspecified width**: `null` を許可し、表示は `"-"`。検証（次パッチ）では「未指定はスキップ」を想定。

---

## 4. 対象 part 一覧（`parts/**/*.json`）

現状 11 種。各 part が持つ ports と、v2 で付すべき role/direction/width の方針（**案・実装時に確定**）:

| part.json | category | ports（現 type） | v2 方針（role / direction / width） |
|---|---|---|---|
| `cpu/ak32` | cpu | bus(bus.master), clk(clock), reset(reset), irq(irq) | bus: master/inout/32 ・ clk: -/in/1 ・ reset: -/in/1 ・ **irq: -/in/1（CPU は割込みを受ける）** |
| `mem/ram` | mem | bus(bus.slave), clk, reset | bus: slave/inout/32 ・ clk/reset: -/in/1 |
| `io/uart` | io | bus(bus.slave), serial(serial.uart), clk, reset, irq | bus: slave/inout/32 ・ serial: -/inout/1 ・ **irq: -/out/1（UART が割込みを出す）** |
| `io/gpio` | io | bus(bus.slave), gpio(gpio), clk, reset | bus: slave/inout/32 ・ gpio: -/inout/1（or 幅可変） |
| `io/timer` | io | bus(bus.slave), clk, reset, irq | bus: slave/inout/32 ・ **irq: -/out/1（Timer が割込みを出す）** |
| `mem/vram` | mem | bus(bus.slave), clk, reset | bus: slave/inout/32 ・ 注: category="mem" だが RAM ではない（ロール正確化は別パッチ） |
| `video/out` | video | video(video.rgb), clk, reset | video: -/out/24（or null） |
| `video/regs` | video | bus(bus.slave), video(video.rgb), clk, reset, irq | bus: slave/inout/32 ・ video: -/out/24 ・ irq: -/out/1 |
| `bus/bridge` | bus | master(bus.master), slave(bus.slave), clk, reset | master: master/inout/32 ・ slave: slave/inout/32 |
| `fpga/generic` | fpga | bus(bus.slave), clk, reset | bus: slave/inout/32 |

> 重要な気付き: **`irq` の direction は part 固有**（CPU=in / Timer・UART・Video=out）。type 推定では表現できず、
> 本パッチで part.json に明示する価値が最も出る箇所。

---

## 5. 互換方針

- **旧形式（v1）も必ず読み込める**互換層を残す。`schema_version` が無い part は **v1** とみなす。
- v1 ports は**正規化関数**で v2 相当へ変換してから上位（Canvas / Port Detail）へ渡す（上位は常に v2 を見る）。
- いきなり全体を破壊的変更しない。`type` は維持（案 B）。
- `parts/custom/` のユーザー製 part（v1 のまま）も正規化層で救済する。
- 既存テスト（v0.7 系・wiring 系・port_detail）を壊さない。Port Detail の表示文言は、明示値があればそれを、無ければ
  従来推定にフォールバックする（既存テストの文字列期待を壊さないよう配慮）。
- project の `system.json` は part 定義を**埋め込まず** `part_id` 参照 + 座標 + sources を持つ（`export_parts`）。
  よって本パッチは**保存フォーマットに影響しない**見込み（実装時に再確認）。

---

## 6. 実装方針（今回は実装しない・着手時の指針）

| 対象 | 変更内容（案） |
|---|---|
| `core/ports.py`（新規・推奨） | `SCHEMA_VERSION=2`、`normalize_part(part)->part`、`normalize_port(port)->port`、`derive_role/direction/width(type)` ヘルパ。v1→v2 補完を集約 |
| `ui/lib.py` | `load_parts()` でロード後に `normalize_part()` を適用（library 経由の全 part を v2 化）。`_REQUIRED` 検証は維持 |
| `parts/**/*.json` | 11 種を v2 へ migration（`schema_version:2` + 各 port に role/direction/width/required/description 明示）。正規化層があるので段階移行も可能 |
| `ui/port_detail.py` | `build_node_info` の logical ports を、port の明示 `direction`/`width`/`role` 優先で構築（無ければ `direction_from_type` にフォールバック）。表示に `role` 行を追加 |
| `core/circuit.py` | **本パッチでは変更しない**（VRAM=mem 誤認の正確化は role 導入後の別パッチ「device-registry / role 正規化」へ） |
| テスト | `tests/test_port_schema_v08.py`（新規・実装時） |

> いずれも本パッチでは**作成・変更しない**。設計の記録のみ。

---

## 7. テスト方針（実装時に追加するテスト）

- **正規化関数**: v1 port → v2（role/direction/width/required/description 補完）の単体。
- **旧形式読み込み**: `schema_version` 無し part.json が v1 として読め、normalize 後に v2 相当になる。
- **新形式読み込み**: `schema_version:2` part.json の明示値がそのまま保持される（推定で上書きしない）。
- **part 固有 direction**: CPU の irq=in / Timer・UART の irq=out が正しく保持される。
- **Port Detail 表示**: logical ports に direction/width/role の**明示値**が出る。明示が無い旧 part では従来推定に
  フォールバックする。
- **既存 project import/export 互換**: system.json round-trip が不変。
- **既存 v0.7 系テストの維持**: plan-driven / address map / cpu-ram / target cpu / run status / port detail /
  wiring 系が全通過。

---

## 8. 今回やらないこと

- direction / width validation 本体（接続時チェック）
- 接続ブロック / 警告
- Bus protocol validation
- 複数 RAM/UART 対応
- Address Map Editor
- MMIO 再配置 / コード領域拡張
- CPU 命令拡張
- Input / Video / Storage 実装
- `core/circuit.py` のロール判定変更（VRAM=mem 正確化）
- コード変更 / part.json 変更 / テスト追加
- commit / push

---

## 9. 次に続くパッチ（候補順）

1. `PATCH_PORT_SCHEMA_V08`（本パッチ — schema 正規化 + 表示）
2. `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08`（接続時 direction/width 検証・初手は警告）
3. `PATCH_BUS_PROTOCOL_VALIDATION_V08`（master/slave・1 master・到達性）
4. `PATCH_DEVICE_REGISTRY_REFACTOR_V08`（Address Map / `_make_sim` のデバイスリスト駆動化・role 正規化）
5. `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08`（複数 RAM/UART 共存）

> 横断: opcode 単一化 / diagnostics コマンド / テストフィクスチャ整理（`V08_CODEBASE_REVIEW.md` §4 参照）。
