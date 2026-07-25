# PATCH_VRAM_DEVICE_V08 — ROADMAP（設計資料）

> v0.8（Device Expansion & Connection Validation）の次パッチ候補。仮想回路上に VRAM device を追加する設計。
> 将来の `PATCH_GAME_RUNTIME_MINIMAL_V08`（自作 CPU がメモリへ書いた内容を画面表示する）の**最小表示基盤（framebuffer）**。
> 本書は設計のみ。**実装・part.json 追加・VramPart 追加・描画 UI 実装・device registry 変更・CPU 命令追加・ASM 変更・テスト追加・既存挙動変更・commit/push は行わない。**
> 親計画: `ROADMAP8.md` / `CHECKLIST8.md`。所見: `V08_CODEBASE_REVIEW.md`。
> 前提: v0.8 の `PATCH_PORT_SCHEMA_V08` 〜 `PATCH_TIMER_DEVICE_V08` 完了（`python -m pytest tests/` 1136 passed）。

> 位置づけ: **Timer の次・Game Runtime Minimal の直前**。VRAM は **書き込み可能な memory device**（ROM の writable 版・reset で 0 クリア）。
> 表示 UI（画面 panel）は **今回やらない**（後続 `PATCH_GAME_RUNTIME_MINIMAL_V08` / `PATCH_VRAM_VIEWER_V08`）。

---

## 1. 目的

- `mem.vram` device を追加する。
- CPU が **既存 `ST`** で VRAM へ書き込めるようにする。
- CPU が **既存 `LD`** で VRAM から読めるようにする。
- 将来の Game Runtime Minimal で画面表示に使える**最小 framebuffer** を用意する。
- まずは小さい indexed-color VRAM（32×32・1 byte/pixel・1024 bytes）にする。
- reset で 0 クリア（RAM と同じく runtime 状態）。
- **今回は設計のみ**。実装・描画 UI・既存挙動変更はしない。

### スコープ（明確化）

`mem.vram` part + `VramPart`（read/write/reset/dump/pixel）+ device registry の runtime 化 + Address Map 統合 + resolve_circuit 収集 + 最小テスト。
描画 panel・sprite/tile・palette 本格実装・DMA・GPU・game runtime・HDL/FPGA は対象外。

---

## 2. 現在の到達点（実コード確認）

- ROM / Input / Timer は実装済み。Timer で時間管理、Bitwise で Input bit 判定が可能。**まだ表示用メモリが無い**。
- **registry は VRAM を一部認識済み**（`core/devices.py`）:
  - `_KIND_BY_PART_ID["mem.vram"] = "vram"`（**既存**）→ VRAM を **RAM 扱いしない**（`device_kind("mem.vram")=="vram"`）。
  - `_ROLE_BY_KIND["vram"] = "memory"`（**既存**）→ addressable・memory role。
  - `_LABEL_BY_KIND["vram"] = "VRAM"`（**既存**）。
  - `_MEMORY_KINDS = ("ram", "vram", "rom")`（**既存**・`core/devices.py` / `core/circuit.py` 両方）。
  - **未対応**: `_RUNTIME_BACKED` に `vram` 無し（現状 `{cpu,ram,uart,input,rom,timer}`）/ `_RUNTIME_ID` に `vram` 無し / `_base_size()` が `vram` を扱わない（base/size None）。
- **Address Map は memory-kind を既に汎用処理**: `build_address_map_from_devices` は `_MEMORY_KINDS`（ram/vram/rom）を memory コンテナとして同様に扱い、MMIO 窓を carve、複数 memory device は非重複前提。
  → **VRAM は ROM と同じ「もう 1 つの memory device」として自然に載る**。
- **`MemoryLayout`**（`core/devices.py`）の現フィールド: `name / ram_base / ram_size / mmio_base / mmio_stride / mmio_size / mmio_inside_ram / code_base / reset_pc / stack_top / rom_base / rom_size`。
  - **VRAM 用フィールド（`vram_base` / `vram_size`）は無い**。
  - `GAME16` は `rom_base=0x0000 / rom_size=0x8000 / ram_base=0x8000 / ram_size=0x4000 / mmio_base=0xE000 / stack_top=0xBFFF`。コメント上 VRAM は 0xC000–0xDFFF を想定するが**フィールド未定義**。
- `_base_size()` は ram→`ram_base/ram_size`、rom→`rom_base/rom_size`、uart→`mmio_*`。**vram は (None,None)**（＝未配置）。
- **circuit_compat は RAM が 0x0000–0xFFFF 全域**。VRAM を置くには Editor override で base/size を与え、RAM を縮小（overlap 回避）する必要がある（ROM と同じ事情）。
- CPU の bus read/write は **32bit little-endian word 単位**（`RamPart` / `RomPart` と同じ `_offset` ベース・範囲外は `BusError`）。

> 結論: **VRAM は ROM device 実装（`PATCH_ROM_DEVICE_V08`）をほぼ踏襲できる**。違いは「writable」「reset で 0 クリア」「pixel/dump 表示ビュー」。

---

## 3. VRAM device 仕様案

| 項目 | 値 |
|---|---|
| part_id | `mem.vram` |
| name | `VRAM` |
| category | `mem` |
| kind | `vram`（既存 `_KIND_BY_PART_ID`） |
| role | **`memory`**（既存 `_ROLE_BY_KIND`） |
| addressable | true（memory role） |
| runtime_backed | true（**新規** — `_RUNTIME_BACKED` に追加） |
| runtime_id | `sim_vram`（**新規** — `_RUNTIME_ID` に追加） |
| read/write | **read=32bit LE word / write=32bit LE word**（RAM と同様・CPU から `LD`/`ST`） |
| reset | **0 クリア**（RAM と同じ runtime 状態・ROM と違い保持しない） |
| base/size | layout の VRAM 領域（あれば）/ Address Map Editor override |

- **role は `memory`**（VRAM は連続した大きめ領域＝framebuffer。MMIO レジスタ窓ではない）。
- **`mem.vram` を RAM 扱いしない**（kind=vram で別 device。Address Map にも RAM とは別行で表示）。
- CPU からは通常 memory として `LD`/`ST` できる（命令追加なし）。

---

## 4. VRAM 容量・形式案

| 案 | 形式 | size | 備考 |
|---|---|---|---|
| A monochrome 32×32 | 1 byte/pixel・0=黒/非0=白 | 1024 B | 表示が単純 |
| **B indexed color 32×32（採用）** | 1 byte/pixel・0–255=palette index | **1024 B** | 表示は後続・dump で確認可 |
| C text-like 32×16 | 1 byte/cell | 512 B | セル表示 |

**採用案: B — indexed color 32×32 / 1 byte per pixel / 1024 bytes（width=32, height=32）。**

- palette 本格実装は後続（最初は index 値をそのまま持つだけ）。
- 表示 UI は今回なし。`VramPart.dump()` / `pixel(x, y)` で中身を確認できればよい。
- **CPU の 32bit word write と 1 byte/pixel の対応**: bytearray(1024) を 32bit LE word でアクセス（RAM と同じ）。1 word = 4 連続 pixel（バイト境界）。`pixel(x,y)` は `_mem[y*width + x]` の 1 byte を返す（表示/テスト用ビュー）。CPU は word 単位で 4 pixel まとめて書ける。

---

## 5. Address Map 方針

VRAM の配置は ROM と同じ方針（memory device・layout 依存・circuit_compat は override 必須）:

- **`circuit_compat`（既定・初回採用）**: `vram_base = None`（RAM が 64KB 全域）。
  - VRAM は **Address Map Editor の manual override** で base/size を与え、RAM を縮小して配置（overlap 回避）。
  - override 無しなら VRAM は未配置（runtime 化しない）＝**既存完全互換**。
- **`game16`（後続 or 実装時に安全なら）**: `MemoryLayout` に `vram_base=0xC000 / vram_size=0x0400` を追加し自動配置。
  - 想定マップ: ROM 0x0000–0x7FFF / RAM 0x8000–0xBFFF / **VRAM 0xC000–0xC3FF** / MMIO 0xE000。RAM/ROM/VRAM 非重複。
- **`legacy`**: `vram_base = None`（VRAM 非使用）。

実装上:

- `_base_size()` に vram 分岐（`vram` → `layout.vram_base / layout.vram_size`・None なら未配置）を追加。
- `MemoryLayout` に `vram_base` / `vram_size`（既定 None）を追加し、`GAME16` のみ 0xC000 / 0x0400 を設定する案（ROM の `rom_base/rom_size` 追加と同型）。
- VRAM/RAM/ROM overlap は **error**（`build_address_map_from_devices` の memory 非重複前提 → `validate_address_map` が検出）。circuit_compat で VRAM を 0xC000 に置くだけだと RAM(全域)と overlap するので RAM 縮小 override が要る。
- **VRAM 非配置なら既存 Address Map dict 完全一致**。

> **最初の実装案（選択）**: **circuit_compat は VRAM base 未確定（Editor override で配置）**。game16 の自動配置（`vram_base/vram_size` 追加）は同時に入れても安全だが、最小スコープなら override-only でも可。ROM と同じ判断。

---

## 6. VramPart 仕様案（`core/dev.py`）

`VramPart`（`RamPart` に近い・writable・pixel ビュー付き）:

- `VramPart(part_id, name, size, base=0, width=32, height=32)`。
- 内部: `bytearray(size)`。
- `read(addr)`: 32bit LE word（RAM と同様の `_offset` ベース・範囲外は `BusError`）。
- `write(addr, value)`: 32bit LE word を書く（範囲外は `BusError`・RAM と同方針）。
- `reset()`: **0 クリア**（`bytearray(size)` で初期化。RAM と同じ）。
- `dump()`: 内容を bytes で返す（テスト / 将来の表示用）。
- `pixel(x, y)`: `_mem[y*width + x]` の 1 byte を返す（表示/テスト用ビュー）。
- `set_pixel(x, y, value)`: 1 byte 書き込み（テスト / UI 用）。
- 範囲外 read/write の扱いは **RAM/ROM に合わせる**（`_offset` が範囲外で `BusError`）。

重要:

- **CPU の bus アクセスは 32bit LE word**（RAM/ROM と同じ）。VramPart も word 単位 read/write を主 API にする。
- UI 表示用の 1 byte/pixel ビュー（`pixel`/`set_pixel`/`dump`）は word アクセスと同じ bytearray を見る（別バッファにしない）。
- bus trace は既存 `Bus.on_access` でそのまま（device_id `sim_vram`）。
- 複数 VRAM instance は当面 1 個目のみ runtime 化。

---

## 7. CPU / ASM との関係

- **CPU 命令追加なし**。VRAM は memory なので既存 `LD`/`ST` でアクセス。
- 既存 `LDI` で base address をレジスタに入れ、`ST [r], rs` で書く / `LD rd, [r]` で読む。
- `AND`/`OR`/`XOR`/`NOT` は色/ビット制御に使えるが必須ではない。
- branch 拡張・stack は今回不要。**ASM 変更なし**。

---

## 8. UI / 表示方針

- **今回は表示 UI（画面 panel）なし**。
- Address Map に VRAM 行が出る（base/size）。Address Map Editor で base/size override 可。
- **Run Status に `VRAM: base=.. size=.. ` 程度を可能なら追加**（Timer の `Timer:` 行と同じ最小パターン）。`dirty` 等は任意。VRAM 未配置なら `VRAM: None`。
- Port Detail で VRAM の port が見える（既存 port detail に自動で乗る）。
- **画面表示 panel は後続** `PATCH_GAME_RUNTIME_MINIMAL_V08` または `PATCH_VRAM_VIEWER_V08` に分離。
- 初回は `VramPart.dump()` / `pixel()` + tests で中身確認できれば十分。GUI 目視はヘッドレスのため未実施になる可能性あり。

---

## 9. resolve_circuit 方針（`core/circuit.py`）

- 便宜キー **`plan["vrams"]`** を追加（`rams`/`uarts`/`inputs`/`roms`/`timers` と同形・target CPU に wired な vram node・sort 済み）。
- `plan["devices"]`（addressable 全 kind）には VRAM も含まれる（memory role・既存収集に乗る）。
- 既存キー（`cpu / rams / uarts / inputs / roms / timers / devices / target_cpu / cpu_present / ok / issues`）は**互換維持**。早期 return の dict にも `vrams: []` を追加。
- target CPU と wired な VRAM のみ収集（bus 未接続 VRAM は収集しない）。
- **VRAM が無くても `ok` 判定は変えない**（VRAM は必須にしない）。
- **VRAM があっても RAM/ROM/Input/Timer を必須にしない**。

---

## 10. device registry 方針（`core/devices.py`）

更新候補（**既存で足りているものは確認のみ**）:

- `_KIND_BY_PART_ID["mem.vram"] = "vram"`（**既存・確認**）→ RAM 扱いしない。
- `_ROLE_BY_KIND["vram"] = "memory"`（**既存・確認**）→ addressable True。
- `_LABEL_BY_KIND["vram"] = "VRAM"`（**既存・確認**）。
- `_RUNTIME_BACKED` に `"vram"` を追加（**新規**）→ `is_runtime_backed_kind("vram")` True。
- `_RUNTIME_ID["vram"] = "sim_vram"`（**新規**）。
- `_base_size()` に vram 分岐（**新規**）: `vram` → `layout.vram_base / layout.vram_size`（None なら未配置）。
- `MemoryLayout` に `vram_base` / `vram_size`（既定 None）を追加し、`GAME16` を 0xC000 / 0x0400 に設定（§5・採否は実装時）。
- `make_device_spec()` が VRAM spec を作れる（role memory・addressable・runtime_backed・runtime_id sim_vram・base/size は layout）。RAM 扱いしないこと（kind=vram）。
- `build_address_map_from_devices()` は既に memory-kind を汎用処理（VRAM 対応済み）。確認のみ。
- 複数 VRAM 時は **1 個目だけ runtime-backed**（`_build_runtime_devices` の seen_* dedup に `seen_vram` を追加）。2 個目以降は placement のみ。warning は任意（RAM の `multi_device_warnings` を VRAM に広げるかは設計判断）。

---

## 11. part.json 方針

`parts/mem/vram/part.json`（**新規 or 既存確認**・schema v2・`mem.ram` / `mem.rom` と同形）:

```json
{
  "id": "mem.vram",
  "name": "VRAM",
  "category": "mem",
  "schema_version": 2,
  "ports": [
    {"name": "bus",   "type": "bus.slave", "role": "slave", "direction": "inout", "width": 32, "required": true,  "description": "Memory bus (slave)"},
    {"name": "clk",   "type": "clock",     "role": null,    "direction": "in",    "width": 1,  "required": true,  "description": "Clock input"},
    {"name": "reset", "type": "reset",     "role": null,    "direction": "in",    "width": 1,  "required": true,  "description": "Reset input"}
  ]
}
```

- id `mem.vram` / name `VRAM` / category `mem` / `schema_version: 2`。
- ports: bus(bus.slave) + clk + reset（mem.ram / mem.rom と同形）。
- **実装時に既存ファイルの有無を確認**（`io.timer` のように scaffold 済みの可能性あり）。あれば schema/ports を確認し、要件を満たすなら流用（不要な変更をしない）。
- 注: `mem.ram` / `mem.rom` と同 category `mem` だが **part_id ベース分類**で `mem.vram`→vram と区別される（VRAM 誤認対策の既存仕組み）。

---

## 12. テスト方針（実装時に追加するテスト）

- `mem.vram` が Library に出る・v2 schema 正規化。
- `device_kind({"id":"mem.vram"}) == "vram"` / `device_role("vram") == "memory"` / addressable・runtime_backed・runtime_id sim_vram。
- **VRAM を RAM 扱いしない**（kind=vram・`_KIND_BY_PART_ID` 経由）。
- `make_device_spec` が VRAM spec を作る。
- VRAM が Address Map に載る（layout/override で base/size 確定時）。
- **VRAM 無し構成は既存 Address Map dict 完全一致**。
- Address Map Editor override で VRAM base/size を配置できる（RAM 縮小と併用）。
- VRAM/RAM overlap が error として検出される。
- `VramPart`: `read()` / `write()`（32bit LE word）・`reset()`（0 クリア）・`dump()` / `pixel()` / `set_pixel()`。
- **CPU から `ST` で VRAM に書ける**・**`LD` で読める**（MainWin 統合・override で VRAM 配置）。
- **ROM target + VRAM 構成でも実行できる**（ROM からコードを fetch しつつ VRAM に書く）。
- VRAM 非配置時は既存挙動完全互換。
- Hello World / ram_selftest / Input / ROM / Program Target / Bitwise / Timer 既存テストが壊れない。
- `python -m pytest tests/` 全通過・`tests/test/system.json` 差分なし。

---

## 13. 既存互換方針（必須）

- **VRAM を置かない既存 project は完全互換**（runtime に vram なし）。
- 既存 Address Map は変えない（VRAM 非配置なら dict 一致）。
- 既存 CPU 命令・既存 ASM は変えない。
- Hello World / ram_selftest を壊さない。
- Input / ROM / Program Target / Bitwise / Timer テストを壊さない。
- `tests/test/system.json` に差分を出さない。
- `python -m pytest tests/` 全通過。

---

## 14. 実装スコープ案（次に実装するなら・安全な範囲）

- `parts/mem/vram/part.json`（新規 or 既存確認）。
- `core/devices.py`: `_RUNTIME_BACKED` に `vram` / `_RUNTIME_ID["vram"]="sim_vram"` / `_base_size` の vram 分岐 / `MemoryLayout` に `vram_base`/`vram_size`（GAME16 のみ値・採否は実装時）。kind/role/label は既存。
- `core/dev.py`: `VramPart`（writable・reset 0 クリア・dump/pixel/set_pixel）。
- `core/circuit.py:resolve_circuit`: `_is_vram` + `plan["vrams"]`（devices は既に収集・早期 return に `vrams:[]`）。
- `ui/win.py`: `_auto_device_specs` が VRAM も spec 化、`_build_runtime_devices` が 1 個目 VRAM（base 有り）を runtime 化（`self._sim_vram` / `self._sim_vram_node`・parts_by_id に sim_vram・`seen_vram` dedup・base None は addr_specs から除外）。`VramPart` import。
- `ui/run_status.py`: 可能なら `VRAM: base=.. size=..` 表示（`_collect_run_status` に vram dict）。
- tests 追加: `tests/test_vram_device_v08.py`。
- `PATCH_VRAM_DEVICE_V08_CHECKLIST.md` 更新・`CHECKLIST8.md` / `ROADMAP8.md` 最小追記。
- **既定（VRAM 非配置）は現行互換**。

やらないこと: 描画 panel・sprite/tile・palette 本格実装・DMA・GPU・game runtime・CPU 命令拡張。

---

## 15. 今回やらないこと

- 実装 / `parts/mem/vram/part.json` 追加 / `VramPart` 追加 / device registry 変更
- CPU 命令追加 / ASM 変更 / tests 追加
- VRAM 表示 panel（画面描画 UI）
- sprite / tile
- palette 本格実装
- DMA / GPU
- Game Runtime 実装
- HDL / FPGA export
- 既存挙動変更 / commit / push

---

## 16. 次に続くパッチ（候補順）

1. **`PATCH_VRAM_DEVICE_V08`（本パッチ — 書き込み可能 framebuffer・表示 UI なし）**
2. `PATCH_GAME_RUNTIME_MINIMAL_V08`（ROM + Input + Timer + VRAM の最小ゲームループ）
3. `PATCH_VRAM_VIEWER_V08`（VRAM 画面表示 panel・dump を可視化）
4. `PATCH_AK32_BRANCH_EXPANSION_V08`（`BNE`/`BEQZ`/`BNEZ` — ゲームループ判定に効く）
5. `PATCH_AK32_SHIFT_IMM_BITWISE_V08`（`SHL`/`SHR`/`ANDI`/`ORI`）
6. `PATCH_V08_STABILIZE_AND_DOCS`（v0.8 安定化・ドキュメント・PHASE COMPLETE 準備）

> **v0.8 完了を急ぐ場合は VRAM → Game Runtime Minimal → Stabilize の順を推奨**。
> 表示 panel（VRAM Viewer）は Game Runtime Minimal に内包するか独立パッチにするかは実装時に判断。
> 横断候補（`V08_CODEBASE_REVIEW.md` §4）: opcode 単一化 / Diagnostics Panel / テストフィクスチャ整理。
