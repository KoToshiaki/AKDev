# PATCH_CODE_REGION_MMIO_RELOCATION_V08 — ROADMAP（設計資料）

> v0.8（Device Expansion & Connection Validation）の **6 番目の候補パッチ**の設計資料。
> 本書は設計のみ。**実装・テスト追加・part.json 変更・挙動変更・commit/push は行わない。**
> 親計画: `ROADMAP8.md` / `CHECKLIST8.md`。所見: `V08_CODEBASE_REVIEW.md`。
> 前提: `PATCH_PORT_SCHEMA_V08` / `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08` /
> `PATCH_BUS_PROTOCOL_VALIDATION_V08` / `PATCH_DEVICE_REGISTRY_REFACTOR_V08` /
> `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08` 完了（`pytest tests/` 973 passed）。

---

## 1. 目的

- 現状の「**RAM 64KB 全域 + UART 窓 0x0100 固定**」構成を見直す。
- **コード領域 / RAM 領域 / MMIO 領域**を分けて扱える **MemoryLayout（アドレス配置ルール）**を整理する。
- UART 窓 `0x0100–0x0107` 固定から、**再配置可能な MMIO 領域**へ移行する準備をする。
- 複数 RAM 共存に向けて **RAM の base/size を可変**にする土台を作る。
- ROM / VRAM / Input / Video / Storage を置けるアドレス空間設計を用意する。
- ゲーム runtime 向けに、プログラム領域と I/O 領域の衝突を避ける配置を設計する。
- **ただし今回は設計のみ**。実装・既定挙動変更はしない。既定は現行互換（circuit_compat）。

### スコープ（明確化）

「**MemoryLayout という配置ルールの構造を設計し、現行を `circuit_compat` として明文化、将来の `game16` 等を
案として整理する**」まで。実装時も**既定 = 現行完全互換**を絶対条件とし、新 layout（MMIO 再配置・RAM 縮小）は
opt-in / 次段送りにする。AK32 は imm16（≤ `0xFFFF` / 64KB）であることを全案の前提とする。

---

## 2. 現在の問題

- circuit mode の RAM が **`0x0000–0xFFFF` 全域を占有**している（`CIRCUIT_RAM_SIZE = 0x10000`）。
- UART は **`0x0100–0x0107` 固定**で、RAM 内 MMIO 窓として `reserved` でくり抜かれている。
- 2 個目以降の UART は `0x0110`… に置けるが、**いずれも RAM 全域内の窓**として扱われている
  （`assign_mmio_bases` が `UART_BASE + n*0x10`）。
- **複数 RAM を置く空き領域がない**（1 個目が全域）。
- コードは **`0x0000` 開始**前提に近い（`reset_pc = 0x0000`、Write は RAM 先頭へロード）。
- **コード / スタック / データ / I/O の分離設計がない**（全部 RAM 全域に同居）。
- Address Map Editor が無く、**手動配置できない**（自動配置のみ）。
- AK32 は **imm16**（`LDI`/`JMP` 最大 `0xFFFF`）なので、当面 **64KB 空間内**で設計する必要がある（バンク無し）。

---

## 3. 目標メモリマップ案

> 全案 64KB（imm16）に収まる。`MemoryLayout` で表現する（§4）。

### 案 A: 互換寄り split（RAM を後ろへ）

```text
0x0000–0x00FF : code / zero page / test program
0x0100–0x01FF : MMIO（UART 等）
0x0200–0xFFFF : RAM（データ）
```

- **メリット**: UART は現行 `0x0100` 近辺を維持。コード領域と RAM データ領域を分離。MMIO 窓くり抜き不要
  （RAM が 0x0200 から始まるので MMIO と非重複）。
- **デメリット**: コード領域が 256B と狭い。現行は RAM 全域 64KB なので「RAM サイズ」が変わり、
  **Address Map dict が現行と一致しない**（既定にはできない）。selftest の `0x0200`（RAM）/ コードの配置前提が変わる。
- **既存互換**: ×（RAM 範囲・attach_ranges が変わる）。opt-in layout 向き。
- **実装難度**: 中（RAM base/size 可変 + ローダのコード配置調整）。

### 案 B: ゲーム runtime 向け（ROM/RAM/VRAM/MMIO 分離）

```text
0x0000–0x7FFF : ROM / program（32KB）
0x8000–0xBFFF : RAM（16KB）
0xC000–0xDFFF : VRAM（8KB）
0xE000–0xEFFF : MMIO（UART/GPIO/Timer/Input/Video regs）
0xF000–0xFFFF : reserved / system（reset vector 等）
```

- **メリット**: 役割ごとに非重複領域。ROM(code)/RAM(data)/VRAM/MMIO/system を自然に配置。ゲーム runtime に最適。
  MMIO はまとまった領域（`0xE000`）で複数 device を素直に並べられる。
- **デメリット**: 現行と全く違う（コードは ROM 領域、データは `0x8000`〜）。**既存 ASM（hello/fib/selftest）が
  そのままでは動かない**（アドレス前提が違う）。ROM runtime / reset vector / ローダ大改修が必要。
- **既存互換**: ×（プログラムの書き換えが要る）。**design-only / 将来の opt-in**。
- **実装難度**: 高（ROM 導入・reset vector・複数 device runtime・ASM 移行）。

### 案 C: 現行互換（RAM 全域 + MMIO overlay）= 既定

```text
0x0000–0xFFFF : RAM（64KB）
0x0100–0x0107 : UART（MMIO overlay・RAM からくり抜き）
0x0110–…      : 追加 MMIO 窓（あれば）
```

- **メリット**: **現状そのもの**。既存テスト・ASM・Address Map dict・runtime すべて不変。
- **デメリット**: コード/データ/I/O が同居。複数 RAM の空きが無い。大規模化に不向き。
- **既存互換**: ◎（完全一致）。**これを既定 `circuit_compat` として明文化**。
- **実装難度**: 低（現行を layout として名前付けするだけ）。

> **方針**: 既定 = 案 C（`circuit_compat`）。案 A/B は `MemoryLayout` の別 mode として**定義のみ**用意し、
> 実際の採用（MMIO 再配置・RAM 縮小・ROM 化）は本パッチでは行わず段階導入。

---

## 4. 今回の実装候補スコープ（次に実装するなら）

推奨（最小・互換最優先）:
- `core/devices.py` に **`MemoryLayout`（dict or dataclass）** を定義: `ram_base` / `ram_size` /
  `mmio_base` / `mmio_stride` / `mmio_size` / `mmio_inside_ram`（窓くり抜きの有無）/ `code_base` /
  `reset_pc` / `name`。
- 名前付き layout: **`legacy`** / **`circuit_compat`（既定）** を**現行値で**定義（+ `game16` は定義だけ or 次段）。
- `_make_sim()` / `_resolve_device_specs()` / `assign_mmio_bases()` / `build_address_map_from_devices()` が
  **layout を参照**するように引数を通す（既定で現行と同一結果）。
- **デフォルトは現行互換**。UART 窓の実変更・RAM 縮小は本パッチでは行わない（layout を渡せる配線まで）。
- `game16` の実採用・ROM runtime・MMIO 実再配置は**次段**。

やらないこと: 既定 layout の変更、MMIO base の実変更、ROM/VRAM runtime、Address Map Editor。

---

## 5. 互換維持方針（必須）

- **デフォルト layout = `circuit_compat` = 現行**。
- 既存単一 RAM/UART の **Address Map dict を壊さない**（`build_address_map_from_devices` の出力不変）。
- 既存 **Hello World / ram_selftest / fib** を壊さない（コードは RAM 先頭ロード・`reset_pc=0x0000`・UART 0x0100）。
- **legacy mode** を壊さない（256B RAM + UART 0x0100、`legacy` layout）。
- UART `0x0100` 前提の既存テストを壊さない。
- `self._sim_ram` / `_sim_uart` / `_sim_cpu`・`_sim_*_node`・runtime_id 互換を維持。
- `format_address_map_summary` の出力が大きく変わらない（既定では同一）。
- layout 引数は**省略時に現行値**になるよう既定を設定（後方互換の関数シグネチャ）。

---

## 6. RAM サイズ可変方針

- `MemoryLayout.ram_base` / `ram_size` で RAM の範囲を決める。
  - `circuit_compat`: base `0x0000` / size `0x10000`（現行）。
  - `legacy`: base `0x0000` / size `0x0100`（現行）。
  - 案 A: base `0x0200` / size `0xFE00`。案 B: base `0x8000` / size `0x4000`。
- `make_device_spec()` の RAM base/size を **layout 由来**にする（現在は定数）。既定で現行値。
- 複数 RAM の base/size: layout に「RAM 領域」を持たせ、2 個目以降を**領域内で自動分割**する将来規則を設計
  （本パッチでは複数 RAM は引き続き warning。分割実装は Address Map Editor / 次段）。
- `assign_mmio_bases()` との関係: RAM 領域と MMIO 領域が **重なる（overlay）か非重複か**を layout の
  `mmio_inside_ram` で切替（circuit_compat=True=くり抜き / game16=False=非重複）。

---

## 7. MMIO 再配置方針

- 現行 UART `0x0100` は **`circuit_compat` の `mmio_base`** として維持。
- 新 layout（game16 等）では `mmio_base` を `0xE000` 等へ。
- 複数 UART/GPIO/Timer/Input/Video regs は `mmio_base + n*mmio_stride`（既定 stride `0x10`・size `0x08`）で並べる。
  - `assign_mmio_bases(specs, layout)` を **layout aware** にする（既定 layout で現行と同一 = 0x0100, 0x0110…）。
- **16byte アライン**は維持（stride 0x10）。size は当面 8B、将来 device kind ごとに可変化（layout/spec で指定）。
- 窓方式: `mmio_inside_ram=True` なら現行どおり RAM からくり抜き（overlay）。`False` なら RAM と MMIO を
  **非重複領域**として扱い、くり抜き不要（`reserved` 空）。`build_address_map_from_devices` はどちらも表現可能。

---

## 8. コード領域 / ROM 領域の設計

- 現行: コードを **RAM にロード**し `reset_pc = 0x0000`。ROM は無い。
- 設計（将来）:
  - `MemoryLayout.code_base` / `reset_pc` を持つ（既定 `0x0000`）。
  - ROM 導入時は ROM を `0x0000` から置き、`reset_pc = code_base`、RAM を別領域へ（案 B）。
  - RAM/ROM 分離: ROM=読み出し専用（コード/定数）、RAM=読み書き（データ/スタック）。
  - **reset vector / boot address**: `reset_pc` を layout から CPU（`AK32Part(reset_pc=...)`）へ渡す
    （現在 `_SIM_RAM_BASE` 固定 → layout 由来へ）。
  - **ローダ**（Write Program / `_assemble_and_load`）はプログラムを `code_base` へ書き込む（既定 0x0000=現行）。
  - Hello World 維持: 既定 layout で `code_base=0x0000` のため**現行どおり**。ROM 採用は opt-in/次段。

---

## 9. Stack / Heap / Data 領域の設計（将来・設計のみ）

- 現在 CALL/RET/SP は無い（`PATCH_AK32_INSTRUCTION_EXPANSION_V08` 予定）。
- 設計指針（メモリマップに影響する点のみ整理）:
  - **スタック**: RAM 上位から下方向に伸ばす（`SP 初期 = ram_end+1` を layout/規約で定義）。
  - **data/heap**: コード直後〜スタック手前。heap は上方向。
  - CALL/RET 導入時に **SP 初期値を layout から**与える（`MemoryLayout.stack_top` 案）。
  - 本パッチでは**実装しない**が、`MemoryLayout` に `stack_top`（任意）を予約しておくと後段が楽。

---

## 10. Address Map Editor との関係

- **layout mode を先に**作る（本パッチ系）→ Editor は layout の**上書き**として後段（`PATCH_ADDRESS_MAP_EDITOR_V08`）。
- Editor は device ごとの base/size を手動変更し、layout の自動配置結果を override する位置づけ。
- 必要な内部データ構造: `MemoryLayout`（自動配置の既定）+ device spec の base/size（Editor が上書き）+
  `validate_address_map`（手動編集の overlap 検出）。これらは既に揃いつつある。
- base/size の手動編集 UI は**次パッチ**。本パッチは layout（自動配置ルール）の土台のみ。

---

## 11. 実装候補案（安全な順序）

1. `core/devices.py` に `MemoryLayout` 構造 + `legacy` / `circuit_compat`（既定）を**現行値**で定義。
2. 現行互換 layout を明示（既定で現行と完全一致）。
3. `_make_sim()` / `_resolve_device_specs()` / `assign_mmio_bases()` /
   `build_address_map_from_devices()` に **layout 引数を通す**（既定 = circuit_compat）。
4. **テストで現行互換を保証**（Address Map dict 一致・UART 0x0100・RAM 64KB・Hello World）。
5. 次パッチで `game16` layout を追加（opt-in・ROM/MMIO 再配置）。
6. さらに次で Address Map Editor。

> 本パッチ（実装時）は **1–4 まで**を推奨。5–6 は別パッチ。

---

## 12. テスト方針（実装時に追加するテスト）

- **デフォルト layout が現行互換**（`circuit_compat` が既定）。
- UART `0x0100–0x0107` が維持される（既定）。
- RAM 64KB（circuit）/ 256B（legacy）が維持される。
- **Address Map dict が既存と完全一致**（`build_address_map_from_devices` 既定 layout）。
- `MemoryLayout` の各 layout の base/size/mmio_base が期待どおり（`legacy`/`circuit_compat`、案として `game16`）。
- MMIO が複数窓として配置される（既定 layout で 0x0100/0x0110…）。
- RAM 縮小 layout（案 A）で MMIO と RAM が overlap しない（`validate_address_map` OK）— 採用するなら。
- Hello World / ram_selftest / fib が壊れない（既定 layout）。
- legacy mode が壊れない。
- 既存 v07/v08（address map / plan-driven / cpu-ram / target cpu / device registry / multi RAM-UART）不変。
- `python -m pytest tests/` 全通過。

---

## 13. 今回やらないこと

- 実際の MMIO base 変更
- 既存デフォルト layout の変更（既定は現行のまま）
- Address Map Editor 実装
- ROM runtime 実装
- VRAM runtime 実装
- Input / Storage runtime 実装
- CPU 命令拡張
- CALL / RET / stack 実装
- HDL / FPGA export
- コード実装 / テスト追加 / part.json 変更
- commit / push

---

## 14. 次に続くパッチ（候補順）

1. `PATCH_CODE_REGION_MMIO_RELOCATION_V08`（本パッチ — MemoryLayout 土台・既定は現行互換）
2. `PATCH_ADDRESS_MAP_EDITOR_V08`（base/size の GUI 編集・layout の上書き）
3. `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08`（ROM / Input などの runtime 追加 — game16 layout を活用）
4. `PATCH_AK32_INSTRUCTION_EXPANSION_V08`（CALL / RET / IN・stack — `stack_top` を layout から）
5. `PATCH_GAME_RUNTIME_MINIMAL_V08`（最小ゲーム runtime — game16 layout + ROM + Input + Video）

> 横断候補（`V08_CODEBASE_REVIEW.md` §4）: Diagnostics Panel / Project Validation / opcode 単一化 /
> テストフィクスチャ整理。
