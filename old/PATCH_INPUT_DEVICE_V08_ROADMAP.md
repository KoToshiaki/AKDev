# PATCH_INPUT_DEVICE_V08 — ROADMAP（設計資料）

> v0.8（Device Expansion & Connection Validation）の候補パッチ。
> `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08` の **分割実装（Input 単独・先行）**。
> 本書は設計のみ。**実装・テスト追加・part.json 追加・挙動変更・commit/push は行わない。**
> 親計画: `ROADMAP8.md`（候補 D）/ `CHECKLIST8.md`。所見: `V08_CODEBASE_REVIEW.md`。
> 前提: v0.8 の `PATCH_PORT_SCHEMA_V08` 〜 `PATCH_ADDRESS_MAP_EDITOR_V08` +
> `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08`（設計）+ ROADMAP8 重複修正 完了（`pytest tests/` 1011 passed）。

---

## 1. 目的

- `io.input` device を追加する。
- Input device を **MMIO device** として Address Map に載せる。
- CPU が**既存の `LD rd, [rs]` 命令**で Input 状態を読めるようにする（`IN` 命令は**追加しない**）。
- Debug UI / 仮想ボタンから Input 状態を変更できるようにする（最小は API + テスト）。
- ゲーム runtime に必要な「入力」を最小構成で実現する。
- **今回は設計のみ**。実装・既存挙動変更はしない。**Input を置かない限り現行と完全一致**を絶対条件にする。

### スコープ（明確化）

ROM は配置問題（circuit_compat で RAM が 0x0000 全域を占有）・game16 前提が絡むため **Input を先行**。
本パッチは Input device + InputPart + Address Map/Editor 統合 + `resolve_circuit` の device 収集拡張まで。
ROM / Timer / GPIO / VRAM / Storage、CPU 命令拡張は対象外。

---

## 2. 現在の到達点

- device spec / Address Map / MemoryLayout / Address Map Editor 整備済み。
- Address Map Editor で per-device `base`/`size` override 可（`apply_address_overrides` / `validate_address_overrides`）。
- `assign_mmio_bases()` は複数 MMIO device 対応（窓を `mmio_base + n*stride` に並べる）。
- AK32 の `LD rd,[rs]` は `bus.read(regs[rs])` → **MMIO read 可能**（UART STATUS も LD で読める）。
  → **Input を読むのに `IN` 命令は不要**。
- 現状 **`io.input` part.json も `InputPart` runtime も無い**。
- `resolve_circuit()` は CPU/RAM/UART 中心（`plan["cpu"]`/`["rams"]`/`["uarts"]`）。Input を収集する拡張が必要。
- **重要な既存仕様（要・整合）**: 現状 `assign_mmio_bases()` は **最初の MMIO のみ runtime-backed**、2 個目以降は
  `runtime_backed=False`（複数 UART を想定）。Input は UART と**別 kind**なので、UART がある場合に Input が
  2 個目 MMIO 扱いで runtime 化されないと困る → **runtime-backing を kind 単位**にする必要がある（§7/§9）。

---

## 3. Input device 仕様

| 項目 | 値 |
|---|---|
| kind | `input` |
| role | `mmio` |
| addressable | true |
| runtime_backed | true（kind 単位で 1 個目） |
| runtime_id | `sim_input` |
| base/size | `assign_mmio_bases()` に従う（MMIO 窓割当） |
| size | 8B 基本（`layout.mmio_size`） |
| Address Map Editor | base/size override 可（既存ロジックで） |

---

## 4. MMIO register 設計

base 相対・word read 前提。推奨:

```text
base + 0x00 : KEY_STATE   (read)  現在押下中キーのビットマスク
base + 0x04 : EDGE_STATE  (read)  前回 clear 以降に押された（立ち上がり）ビットマスク
base + 0x04 : CLEAR_EDGE  (write) EDGE_STATE をクリア
```

bit 割り当て（案）:

| bit | キー |
|---|---|
| 0 | up |
| 1 | down |
| 2 | left |
| 3 | right |
| 4 | A |
| 5 | B |
| 6 | Start |
| 7 | Select |

- **word read** で返す（`RamPart`/`UartPart` と同じ 32bit 値）。上位ビットは将来拡張用に 0。
- API: `set_keys(mask)`（UI/test から押下状態を設定）/ `get_keys()` / `clear_edge()`。
- reset 時: KEY_STATE / EDGE_STATE を 0 に戻す。
- **最小実装**: KEY_STATE read + `set_keys` を必須。**EDGE_STATE / CLEAR_EDGE は段階**（設計は本書に残すが、
  最小では KEY_STATE のみでも可。EDGE は「押した瞬間」検出用で後続でよい）。

---

## 5. CPU / ASM との関係

- **`IN` 命令は今回不要**。既存 `LD rd, [rs]` で Input を読む（rs に Input base を入れて LD）。
- assembler の拡張は**原則不要**（数値リテラルで base 指定。hello/selftest と同様）。
- 将来 `INPUT_BASE` symbol / MMIO label 支援を追加する余地は残す（本パッチではやらない）。
- 既存 Hello World / ram_selftest / legacy は壊さない（Input device 非配置時は経路不変）。

Input 読み出しイメージ:

```asm
LDI r1, 0x0110     ; Input base（UART が 0x0100 のとき Input は 0x0110 に並ぶ想定）
LD  r2, [r1]       ; r2 = KEY_STATE（bus.read 経由）
; 例: A ボタン(bit4)判定
LDI r3, 0x10
; （AND 命令は未実装なので、当面は単純な比較/分岐で扱う or 命令拡張は別パッチ）
```

> 注: bit マスク判定に AND が要る場面は CPU 命令拡張（別パッチ）。本パッチは「Input を LD で読める」までを保証。

---

## 6. part.json 方針

`parts/io/input/part.json`（**新規**・schema v2）:

```json
{
  "id": "io.input",
  "name": "Input",
  "category": "io",
  "schema_version": 2,
  "ports": [
    {"name": "bus",   "type": "bus.slave", "role": "slave", "direction": "inout", "width": 32, "required": true,  "description": "Register bus (slave)"},
    {"name": "keys",  "type": "input",     "role": null,    "direction": "in",    "width": 8,  "required": false, "description": "Button/key input lines"},
    {"name": "clk",   "type": "clock",     "role": null,    "direction": "in",    "width": 1,  "required": true,  "description": "Clock input"},
    {"name": "reset", "type": "reset",     "role": null,    "direction": "in",    "width": 1,  "required": true,  "description": "Reset input"}
  ]
}
```

- id `io.input` / name `Input` / category `io` / `schema_version: 2`。
- ports: bus(bus.slave) + keys(input・任意) + clk + reset。各 port に direction/width/role/required/description。
- visual / icon は既存 io 系のカテゴリ色を流用。

---

## 7. device registry 方針（`core/devices.py`）

更新候補:
- `_KIND_BY_PART_ID["io.input"] = "input"`
- `_ROLE_BY_KIND["input"] = "mmio"`（→ `is_addressable_kind("input")` True）
- `_RUNTIME_BACKED` に `"input"` を追加（→ `is_runtime_backed_kind("input")` True）
- `_RUNTIME_ID["input"] = "sim_input"`
- `_LABEL_BY_KIND["input"] = "INPUT"`
- `make_device_spec()` は kind=input を MMIO として spec 化（role mmio・base/size は MMIO 窓割当で後付け）。

**`assign_mmio_bases()` の整合（重要）**:
- 現状「最初の MMIO のみ runtime-backed・2 個目以降は False」は **複数 UART 前提**。
- Input は UART と別 kind。**runtime-backed/未 backed の判定を「kind ごとに 1 個目」へ変更**する（案）:
  - base/窓割当は従来どおり**全 MMIO 通し番号**（UART=0x0100, Input=0x0110 …）。
  - `runtime_backed` は **kind 単位**で 1 個目のみ True（UART1=backed, Input1=backed, UART2/Input2=placement のみ）。
  - `runtime_id` は kind 由来（uart→sim_uart, input→sim_input）。2 個目以降は `device_id=mmio_<node>` で placement のみ。
- これにより「UART あり + Input あり」で **UART(0x0100) と Input(0x0110) が両方 runtime 化**される。

---

## 8. resolve_circuit / plan 方針（`core/circuit.py`）

- 現状 `plan` は `cpu` / `rams` / `uarts` / `target_cpu` / `cpu_present` / `issues` / `ok`。
- **既存キーは互換維持**。target CPU に wired な **addressable device を収集**する新キーを追加（案）:
  - `plan["devices"]` = `[{"node_id", "kind"}]`（target CPU に wired な addressable device 全 kind。rams/uarts/input 等）。
  - 任意で `plan["inputs"]` = wired input node_id リスト（rams/uarts と同形の便宜キー）。
- 収集ルール: target CPU と wire 接続された device のうち `is_addressable_kind(kind)` を収集。bus 未接続 Input は
  **収集しない（= Address Map に出さない）**。`ok` 判定（RAM/UART 必須）は現状維持（Input は必須にしない）。
- Input が複数あるとき: **1 個目のみ runtime 化**（§7 の kind 単位ルール）。2 個目以降は Address Map 配置のみ。
- bus group / 到達性の本格突き合わせは本パッチではやらない（`PATCH_BUS_PROTOCOL_VALIDATION_V08` 由来の診断は別軸）。

推奨: `plan["devices"]` を追加（汎用）。`plan["inputs"]` は便宜キーとして任意。`rams`/`uarts` はそのまま。

---

## 9. runtime 設計（`core/dev.py`）

`InputPart`（既存 `RamPart`/`UartPart` と同じ Bus device インターフェース）:
- `InputPart(part_id, name, base)`。
- `read(addr)`: `addr-base == 0x00` → KEY_STATE / `== 0x04` → EDGE_STATE / その他 → 0。
- `write(addr, value)`: `addr-base == 0x04` → CLEAR_EDGE（EDGE_STATE=0）。その他 write は no-op（最小では全 no-op 可）。
- `set_keys(mask)`: KEY_STATE 設定 + 立ち上がりを EDGE_STATE に OR（最小では KEY_STATE のみ更新でも可）。
- `get_keys()` / `clear_edge()` / `reset()`（KEY/EDGE を 0 に）。
- **bus trace**: 既存 `Bus.on_access` フックでそのまま trace に出る（device_id `sim_input`）。
- reset 時: state 0 クリア。
- 複数 instance: 当面 1 個目のみ runtime 化（multi-UART と同方針）。

---

## 10. UI / Debug 入力方針

- **最小**: `InputPart.set_keys(mask)` + MainWin の薄い API（例 `self._sim_input.set_keys(...)`）+ **テスト中心**。
- **目視確認用（推奨・小さく）**: Debug Dock に簡易 **Input パネル / 仮想ボタン**（up/down/left/right/A/B/Start/Select
  のトグル → `set_keys`）。最小実装では後続でも可だが、目視確認のため簡易ボタン案を残す。
- **次段**: Canvas/MainWin の keyboard event を `InputPart.set_keys` へ橋渡し（リアルタイム操作）。
- GUI 目視: Input を置いて配線 → 仮想ボタン押下 → CPU が `LD` で読んだ値が変わることを Register/Memory/Run Status で確認。

---

## 11. Address Map / Editor との関係

- Input は MMIO なので `assign_mmio_bases()` で自動配置。UART がある場合、Input は 2 個目 MMIO として `0x0110` 等に並ぶ。
- Address Map Editor で Input の base/size を override 可（既存 `apply_address_overrides` / `validate_address_overrides`
  がそのまま効く。MMIO align/size warning も適用）。
- **override 無し・Input 非配置なら既存 CPU/RAM/UART 構成の Address Map dict は完全一致**。
- §7 の kind 単位 runtime-backing 変更は、単一 UART のみ構成では挙動不変（UART1 が backed のまま）。

---

## 12. 実装スコープ案（次に実装するなら）

推奨範囲:
- `parts/io/input/part.json` 追加（v2）。
- `core/devices.py`: kind/role/addressable/runtime_backed/runtime_id/label マップ更新 + `assign_mmio_bases`
  を **kind 単位 runtime-backing** へ調整。
- `core/dev.py`: `InputPart` 追加。
- `core/circuit.py:resolve_circuit`: `plan["devices"]`（+任意 `plan["inputs"]`）に addressable device 収集（互換維持）。
- `ui/win.py`: `_auto_device_specs` が Input も spec 化、`_build_runtime_devices` が 1 個目 Input を runtime 化、
  `self._sim_input` / `self._sim_input_node` 追加、parts_by_id に sim_input。
- tests 追加。GUI Input パネルは最小 or 次段。
- **既定（Input 非配置）は現行完全一致**。

---

## 13. テスト方針（実装時に追加するテスト）

- `io.input` が Library に出る・v2 schema 正規化。
- `device_kind("io.input") == "input"` / `device_role("input") == "mmio"` / addressable・runtime_backed True。
- `make_device_spec` が Input spec を作る（role mmio・runtime_id sim_input）。
- Input が Address Map に載る。UART+Input で **UART 0x0100 / Input 0x0110**、**両方 runtime_backed**。
- Address Map Editor で Input base/size override 可。
- `InputPart.set_keys()` → `read(KEY_STATE)` が値を返す（EDGE/CLEAR は実装する場合のみ）。
- **CPU が `LD` で Input を読める**（`LDI base; LD r,[base]` で set_keys 値が取れる）。
- **Input 無し構成は既存 Address Map dict 完全一致**（回帰）。
- Hello World / ram_selftest / legacy が壊れない。
- `python -m pytest tests/` 全通過。

---

## 14. 今回やらないこと

- 実装 / part.json 追加 / `InputPart` 追加 / runtime 追加
- CPU 命令追加 / `IN` 命令追加 / ASM 拡張
- ROM 実装 / VRAM / Timer / GPIO / Storage 実装
- game16 layout への切替
- HDL / FPGA export
- コード実装 / テスト追加 / 既存挙動変更
- commit / push

---

## 15. 次に続くパッチ（候補順）

1. `PATCH_INPUT_DEVICE_V08`（本パッチ — Input device・LD で読む・IN 命令不要）
2. `PATCH_ROM_DEVICE_V08`（ROM device・read-only・game16/Editor 前提）
3. `PATCH_AK32_INSTRUCTION_EXPANSION_V08`（CALL / RET / IN / AND 等・stack）
4. `PATCH_GAME_RUNTIME_MINIMAL_V08`（Input + Timer + VRAM/簡易描画の最小ループ）
5. `PATCH_V08_STABILIZE_AND_DOCS`（v0.8 安定化・ドキュメント・PHASE COMPLETE 準備）

> 横断候補（`V08_CODEBASE_REVIEW.md` §4）: Diagnostics Panel / Project Validation / opcode 単一化 /
> テストフィクスチャ整理。
