# PATCH_ROM_DEVICE_V08 — ROADMAP（設計資料）

> v0.8（Device Expansion & Connection Validation）の候補パッチ。
> `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08` の **分割実装（ROM 単独・Input の次）**。
> 本書は設計のみ。**実装・テスト追加・part.json 追加・挙動変更・commit/push は行わない。**
> 親計画: `ROADMAP8.md`（候補 D）/ `CHECKLIST8.md`。所見: `V08_CODEBASE_REVIEW.md`。
> 前提: v0.8 の `PATCH_PORT_SCHEMA_V08` 〜 `PATCH_INPUT_DEVICE_V08` 完了（`pytest tests/` 1034 passed）。

---

## 1. 目的

- `mem.rom` device を追加する。
- ROM device を **read-only memory** として Address Map に載せる。
- 将来プログラム領域を RAM から ROM へ分離する土台を作る（`game16` layout の ROM 領域の受け皿）。
- 既定の `circuit_compat` では **現行の RAM ロード挙動を維持**（Hello World / ram_selftest / legacy 不変）。
- ROM 非配置時は現行完全互換。
- **今回は設計のみ**。実装・既存挙動変更はしない。

### スコープ（明確化）

ROM device + `RomPart`（read-only）+ device 収集 + runtime 化 + Address Map/Editor 統合まで。
**Program loader は RAM ロードのまま**（ROM への書き込み導線は後続 `PATCH_PROGRAM_TARGET_ROM_V08`）。
CPU 命令拡張・VRAM/Timer/GPIO/Storage・game16 自動切替は対象外。

---

## 2. 現在の到達点

- device spec / Address Map / MemoryLayout / Address Map Editor 整備済み。Input device 実装済み。
- `resolve_circuit()` は `plan["devices"]`（wired な addressable device 全 kind）を収集できる。
  → **`rom` は role=`memory`＝addressable なので、wired な ROM は既に `plan["devices"]` に kind=`rom` で入る**
  （ただし runtime 化はされない）。
- `core/devices.py` の現状（ROM 関連で既に存在するもの）:
  - `_ROLE_BY_KIND["rom"] = "memory"`（既存）/ `_LABEL_BY_KIND["rom"] = "ROM"`（既存）/ `_MEMORY_KINDS` に `rom`（既存）。
  - **未対応**: `_KIND_BY_PART_ID` に `mem.rom` 無し / `_RUNTIME_BACKED` に `rom` 無し / `_RUNTIME_ID` に `rom` 無し /
    `_base_size()` が `rom` を扱わない（base/size が None になる）。
- `MemoryLayout` に **ROM 領域フィールドが無い**（`ram_base/ram_size/mmio_*` のみ）。game16 も ROM 領域を持たない。
- CPU の fetch は `bus.read(pc)`。**ROM を bus に載せ `reset_pc` を ROM base にすれば ROM から fetch 可能**。
- **circuit_compat では RAM が 0x0000–0xFFFF 全域を占有**するため、ROM を 0x0000 に単純配置すると RAM と overlap する。

---

## 3. ROM device 仕様

| 項目 | 値 |
|---|---|
| kind | `rom` |
| role | `memory`（既存） |
| addressable | true（memory role） |
| runtime_backed | true（kind 単位で 1 個目） |
| runtime_id | `sim_rom` |
| read/write | read=32bit LE word（RAM と同様）/ **write=no-op**（read-only） |
| load_bytes | IDE/loader から内容を初期化（CPU/bus からは書けない） |
| reset | **内容を消さない**（ROM image は保持。CPU reset では消えない） |
| base/size | layout の ROM 領域（あれば）/ Address Map Editor override |
| Address Map Editor | base/size override 可 |

---

## 4. ROM memory map 設計

ROM の配置は **layout に依存**する。`MemoryLayout` に ROM 領域フィールド（`rom_base` / `rom_size`、既定 None）を
追加する案を採る:

- **`circuit_compat`（既定）**: `rom_base = None`（RAM が 64KB 全域）。
  - ROM を置いても auto base が無く、0x0000 に置けば RAM と overlap。
  - → **ROM 配置は Address Map Editor の manual override**（+ RAM を縮小する override）で行う。
  - 既存 Hello World は RAM ロード維持。ROM 非配置なら一切影響なし。
- **`game16`**: `rom_base = 0x0000` / `rom_size = 0x8000`（ROM 32KB）/ RAM 0x8000–0xBFFF / VRAM 0xC000 / MMIO 0xE000。
  - ROM が ROM 領域に auto 配置される。RAM は ROM と非重複。
- **`legacy`**: `rom_base = None`（現行互換・ROM 非使用）。

ROM を runtime-backed にするのは全 layout 共通（device があれば）だが、**auto base/size が決まるのは ROM 領域を
持つ layout（game16）だけ**。circuit_compat/legacy では base が無く、Editor override で base/size を与える
（与えないと overlap validation が error → Apply ブロック、で気付ける）。

> 代替案: MemoryLayout に rom フィールドを足さず、ROM base は常に Editor override 必須にする。よりシンプルだが
> game16 で自動配置できない。**推奨は rom_base/rom_size を MemoryLayout に追加**（game16 で自動・他は override）。

---

## 5. Program loading 方針

- **現行は RAM へプログラムを書く**（Write Program → `_assemble_and_load` → RAM）。
- **ROM 導入後も既定は RAM ロード維持**（Hello World / ram_selftest / legacy 不変）。
- ROM が配置されていても、**本パッチでは Write Program を ROM へ向けない**（RAM のまま）。
  ROM への IDE ロードは `RomPart.load_bytes()` を**テスト/将来導線**から呼ぶに留める。
- `reset_pc` は layout.reset_pc（既定 0x0000）。game16 で ROM が 0x0000 を占め program target が ROM のときに
  ROM から fetch する流れは **後続 `PATCH_PROGRAM_TARGET_ROM_V08`** で扱う（program target: RAM/ROM 選択）。
- ROM write 禁止と「プログラムロード」は別扱い:
  - CPU/bus の `write` → ROM では **no-op**（ST/OUT で書いても黙って無視）。
  - IDE loader だけ `RomPart.load_bytes()` で内容を入れられる。
- ram_selftest は引き続き RAM へロード（RAM テストなので RAM 必須）。
- **既存 Hello World / ram_selftest / legacy を壊さない・ROM 非配置時は現行完全一致**。

---

## 6. CPU / ASM との関係

- **CPU 命令追加はしない**。ROM fetch は既存 `bus.read(pc)` で可能。
- `AK32Part(reset_pc=...)` と ROM base: ROM から実行する場合 `reset_pc = ROM base`（= layout.reset_pc を ROM 領域に
  合わせる）。本パッチでは reset_pc は layout 既定（0x0000）のまま（program target=RAM 既定）。
- assembler 拡張は**原則不要**。将来、ROM/RAM を分けたコード配置には `ORG` / section / ROM symbol / 簡易 linker
  のような仕組みが要る可能性がある（本パッチでは扱わない）。
- CALL / RET / stack / IN / AND 等の命令拡張はやらない（別パッチ）。

---

## 7. part.json 方針

`parts/mem/rom/part.json`（**新規**・schema v2）:

```json
{
  "id": "mem.rom",
  "name": "ROM",
  "category": "mem",
  "schema_version": 2,
  "ports": [
    {"name": "bus",   "type": "bus.slave", "role": "slave", "direction": "inout", "width": 32, "required": true,  "description": "Memory bus (slave, read-only)"},
    {"name": "clk",   "type": "clock",     "role": null,    "direction": "in",    "width": 1,  "required": true,  "description": "Clock input"},
    {"name": "reset", "type": "reset",     "role": null,    "direction": "in",    "width": 1,  "required": true,  "description": "Reset input"}
  ]
}
```

- id `mem.rom` / name `ROM` / category `mem` / `schema_version: 2`。
- ports: bus(bus.slave) + clk + reset（mem.ram と同形・read-only は description で示す。load/program port は入れない）。
- visual / icon は既存 mem 系のカテゴリ色を流用。
- 注: `mem.vram` と同じ category `mem` だが **part_id ベース分類**で `mem.rom`→rom・`mem.ram`→ram・`mem.vram`→vram
  と区別される（VRAM 誤認対策と同じ仕組み）。

---

## 8. device registry 方針（`core/devices.py`）

更新候補（**既存で足りているものは確認のみ**）:
- `_KIND_BY_PART_ID["mem.rom"] = "rom"`（**新規**）
- `_ROLE_BY_KIND["rom"] = "memory"`（**既存・確認**）→ `is_addressable_kind("rom")` True（既存）
- `_RUNTIME_BACKED` に `"rom"` を追加（**新規**）→ `is_runtime_backed_kind("rom")` True
- `_RUNTIME_ID["rom"] = "sim_rom"`（**新規**）
- `_LABEL_BY_KIND["rom"] = "ROM"`（**既存・確認**）
- `_base_size()` に ROM 分岐（**新規**）: `rom` → `layout.rom_base` / `layout.rom_size`（None なら base/size None）。
- `MemoryLayout` に `rom_base` / `rom_size`（既定 None）を追加し、`GAME16` を 0x0000 / 0x8000 に設定（§4）。
- `make_device_spec()` が ROM spec を作れる（role memory・addressable・runtime_backed・runtime_id sim_rom・base/size は layout）。
- 複数 ROM 時は **1 個目だけ runtime-backed**（`_build_runtime_devices` の「1 個目のみ」ロジック）。2 個目以降は
  `multi_device_warnings` を ROM にも拡張するか、RAM と同様の扱いにする（設計で確定）。

---

## 9. resolve_circuit / plan 方針（`core/circuit.py`）

- Input 実装で `plan["devices"]`（addressable 全 kind）が既にあり、**ROM は memory role なので既に収集される**。
- 便宜キー **`plan["roms"]`** を追加（`rams`/`uarts`/`inputs` と同形・target CPU に wired な rom node・sort 済み）。
- 既存キー `cpu / rams / uarts / inputs / devices / target_cpu / cpu_present / ok / issues` は**互換維持**。
- target CPU と wired な ROM のみ収集（bus 未接続 ROM は収集しない＝Address Map に出さない）。
- ROM が複数あるときは **1 個目だけ runtime 化**（残りは placement/warning）。
- **ROM が無くても `ok` 判定は変えない**（ROM は必須にしない）。
- **ROM があっても RAM 必須は外さない**（今回は RAM 必須のまま。ROM-only 実行は後続で program target を ROM にしてから）。

---

## 10. runtime 設計（`core/dev.py`）

`RomPart`（`RamPart` に近い Bus device・ただし read-only）:
- `RomPart(part_id, name, size, base=0)`。
- `read(addr)`: 32bit LE word（RAM と同様の `_offset` ベース）。
- `write(addr, value)`: **no-op**（read-only。例外は投げない＝ST/OUT 誤書き込みでも halt しない）。
- `reset()`: **内容を保持**（ROM image は消さない。RAM は 0 クリアだが ROM は不変）。
- `load_bytes(data, offset=0)`: ROM image を設定（IDE/loader/test 用）。
- `dump()`: 内容を返す（メモリビューア用）。
- bus trace: 既存 `Bus.on_access` でそのまま（device_id `sim_rom`）。
- 複数 instance: 当面 1 個目のみ runtime 化。

---

## 11. UI / Loader 方針

- **最小**: `RomPart` 単体 + Address Map 表示 + Address Map Editor override。テストは `RomPart.load_bytes()` を直接使う。
- **Write Program は引き続き RAM へロード**（ROM へは入れない）。
- ROM へロードする UI / program target 選択は **後続 `PATCH_PROGRAM_TARGET_ROM_V08`**
  （Project 設定で `program target: RAM / ROM` を選べるように）。
- Address Map Editor で ROM の base/size を確認・override 可。Run Status / Address Map summary に ROM 行が出る。

---

## 12. Address Map / Editor との関係

- ROM は **memory role** なので RAM と overlap しやすい（circuit_compat は RAM が全域）。
- circuit_compat で ROM を置くと:
  - layout に rom 領域が無い → auto base 無し。Editor で base/size を manual 指定し、かつ RAM を縮小しないと
    **overlap → `ADDRESS_OVERLAP`（error）→ Apply ブロック**（既存 `validate_address_overrides` が検出）。
- game16 では ROM(0x0000–0x7FFF) / RAM(0x8000–) と非重複に auto 配置。
- Address Map Editor で ROM の base/size override 可（既存 `apply_address_overrides` / `validate_address_overrides`）。
- ROM/RAM overlap は **error**（両方 memory で carving 対象外なので attach_ranges が重なる → validate で検出）。
  MMIO 窓のような overlay 扱いは memory 同士では行わない。
- **ROM 非配置なら既存 Address Map dict 完全一致**。

---

## 13. 実装スコープ案（次に実装するなら）

推奨範囲:
- `parts/mem/rom/part.json` 追加（v2）。
- `core/devices.py`: `_KIND_BY_PART_ID["mem.rom"]`、`_RUNTIME_BACKED`/`_RUNTIME_ID` に rom、`_base_size` の ROM 分岐、
  `MemoryLayout` に `rom_base`/`rom_size`（GAME16 のみ値）。
- `core/dev.py`: `RomPart` 追加。
- `core/circuit.py:resolve_circuit`: `plan["roms"]` 追加（`devices` は既に収集）。
- `ui/win.py`: `_auto_device_specs` が ROM も spec 化、`_build_runtime_devices` が 1 個目 ROM を runtime 化、
  `self._sim_rom` / `self._sim_rom_node` 追加、parts_by_id に sim_rom。
- Program loader は**現行維持**（RAM ロード）。ROM への IDE ロードは後続。
- tests 追加。**既定（ROM 非配置）は現行互換**。

やらないこと: Write Program の ROM target 化、program target 選択 UI、game16 自動切替、CPU 命令拡張。

---

## 14. テスト方針（実装時に追加するテスト）

- `mem.rom` が Library に出る・v2 schema 正規化。
- `device_kind("mem.rom") == "rom"` / `device_role("rom") == "memory"` / addressable・runtime_backed・runtime_id sim_rom。
- `make_device_spec` が ROM spec を作る。
- `RomPart.load_bytes()` / `read()` が動く（word 読み出し）。
- `RomPart.write()` しても内容が変わらない（read-only）。
- `RomPart.reset()` で内容が消えない。
- ROM が Address Map に載る（layout/override で base/size が決まる場合）。
- Address Map Editor で ROM base/size override 可。
- ROM+RAM overlap が `ADDRESS_OVERLAP`（error）として検出される。
- game16 layout で ROM 0x0000 / RAM 0x8000 が非重複（layout を使う場合）。
- **ROM 非配置の既存構成は Address Map dict 完全一致**。
- Hello World / ram_selftest / legacy が壊れない。
- `python -m pytest tests/` 全通過。

---

## 15. 今回やらないこと

- 実装 / part.json 追加 / `RomPart` 追加 / runtime 追加
- Program loader 変更 / Write Program の ROM target 化
- CPU 命令追加 / ASM 拡張
- game16 layout への自動切替
- VRAM / Timer / GPIO / Storage 実装
- HDL / FPGA export
- コード実装 / テスト追加 / 既存挙動変更
- commit / push

---

## 16. 次に続くパッチ（候補順）

1. `PATCH_ROM_DEVICE_V08`（本パッチ — ROM device・read-only・既定は RAM ロード維持）
2. `PATCH_PROGRAM_TARGET_ROM_V08`（任意・program target: RAM/ROM 選択 + ROM ロード導線 + reset_pc 連動）
3. `PATCH_AK32_INSTRUCTION_EXPANSION_V08`（CALL / RET / IN / AND 等・stack）
4. `PATCH_GAME_RUNTIME_MINIMAL_V08`（ROM + Input + Timer + VRAM/簡易描画の最小ループ）
5. `PATCH_V08_STABILIZE_AND_DOCS`（v0.8 安定化・ドキュメント・PHASE COMPLETE 準備）

> 横断候補（`V08_CODEBASE_REVIEW.md` §4）: Diagnostics Panel / Project Validation / opcode 単一化 /
> テストフィクスチャ整理。
