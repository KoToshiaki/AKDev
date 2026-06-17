# PATCH_DEVICE_EXPANSION_ROM_INPUT_V08 — ROADMAP（設計資料）

> v0.8（Device Expansion & Connection Validation）の **8 番目の候補パッチ**の設計資料。
> 本書は設計のみ。**実装・テスト追加・part.json 追加・挙動変更・commit/push は行わない。**
> 親計画: `ROADMAP8.md` / `CHECKLIST8.md`。所見: `V08_CODEBASE_REVIEW.md`。
> 前提: `PATCH_PORT_SCHEMA_V08` / `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08` /
> `PATCH_BUS_PROTOCOL_VALIDATION_V08` / `PATCH_DEVICE_REGISTRY_REFACTOR_V08` /
> `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08` / `PATCH_CODE_REGION_MMIO_RELOCATION_V08` /
> `PATCH_ADDRESS_MAP_EDITOR_V08` 完了（`pytest tests/` 1011 passed）。

---

## 1. 目的

- Address Map 上に配置できる **runtime device の種別を増やす**（ROM / Input / Timer / GPIO / VRAM / Storage）。
- v0.7 の CPU+RAM+UART 実行基盤を、よりゲーム runtime に近い構成へ拡張する。
- `MemoryLayout` と Address Map Editor の上に、新 device を**安全に配置・実行**できるようにする。
- 最小実装では **ROM runtime** と **Input runtime** を優先する。
- **今回は設計のみ**。実装・既存挙動変更はしない。**新 device を置かない限り現行と完全一致**を絶対条件にする。

### スコープ（明確化）

「ROM / Input を runtime-backed device として追加する仕様 + Address Map/Editor 統合 + resolve_circuit の
device 収集拡張」を設計し、Timer/GPIO/VRAM/Storage は**後続送り**として位置づける。実装は分割案（§13）を推奨。

---

## 2. 現在の到達点

- device spec（kind / role / addressable / runtime_backed / runtime_id / base / size / overlay）の土台がある。
- Address Map は複数 MMIO 窓カービング対応（`build_address_map_from_devices` + `assign_mmio_bases`）。
- `MemoryLayout`（`LEGACY` / `CIRCUIT_COMPAT` / `GAME16`）+ `get_memory_layout()`。
- Address Map Editor で per-device `base`/`size` override（auto/manual・validation・system.json 永続化）。
- **ただし runtime-backed は実質 CPU/RAM/UART のみ**（`_RUNTIME_BACKED = {"cpu","ram","uart"}`）。
- `mem.vram` は RAM 扱いしない土台があるが **VRAM runtime は未実装**。
- ROM / Input / Timer / GPIO / Storage runtime は未実装（gpio/timer/vram の **part.json は存在**するが
  runtime_backed=False で Address Map にも載らない＝`resolve_circuit` が cpu/ram/uart しか収集しない）。
- **重要（CPU 側）**: AK32 の `LD rd, [rs]` は `bus.read(regs[rs])` なので、**MMIO read は既存命令で可能**
  （UART STATUS も LD で読める）。よって **Input は `IN` 命令なしでも LD で読める**。`IN` 命令拡張は不要。

---

## 3. 追加候補 device 一覧

| device | kind | role | addressable | runtime_backed | 優先度 | 今回 | 備考 |
|---|---|---|---|---|---|---|---|
| ROM        | rom        | memory | true | 段階(true) | 高 | **対象** | code/program 用・read-only |
| Input      | input      | mmio   | true | true       | 高 | **対象** | key/button 状態・LD で読む |
| Timer      | timer      | mmio   | true | true       | 中 | 後続 | frame/tick/cycle |
| GPIO       | gpio       | mmio   | true | true       | 中 | 後続 | 汎用 I/O port |
| VRAM       | vram       | memory | true | 段階       | 中 | 後続 | video 用・大きい |
| Video regs | video_regs | mmio   | true | 中         | 中 | 後続 | VRAM/描画制御 |
| Storage    | storage    | mmio/storage | true | 低   | 低 | 後続 | block I/O |

- 今回（または分割）対象: **ROM, Input**。
- 後続: Timer, GPIO, VRAM, Video regs, Storage（同じ device spec / Bus Part パターンで段階追加）。

---

## 4. 優先順位（理由つき）

1. **ROM runtime 最小** — プログラム領域を RAM から分離する前提。game16 layout の ROM 領域の受け皿。
2. **Input runtime 最小** — ゲーム runtime に必須。LD で読めるため CPU 改修不要 = 低リスクで価値大。
3. Timer runtime — ゲームループ（フレーム/tick）に必要だが Input の後でよい。
4. GPIO runtime — 汎用。Timer と同パターン。
5. VRAM / Video regs — 画面表示。サイズが大きく game16 layout 前提なので段階導入。
6. Storage — block I/O。最後。
7. game16 layout 本格利用 — ROM/RAM/VRAM/MMIO 分離が揃ってから。
8. CPU 命令拡張との接続 — CALL/RET/IN は別パッチ（Input は LD で足りるので前提にしない）。

ROM/Input を優先する理由: ROM は「コード/データ分離」の土台、Input は「操作」の最小要素。両者が入ると
"自作 CPU 上で入力に反応するプログラム" という最小ゲーム runtime の核に到達できる。

---

## 5. ROM 設計

- `RomPart`（`core/dev.py`）= **read-only memory**（`RamPart` と同じ 32bit LE word read、write は **no-op**
  または warning。`load_bytes` で内容初期化、`dump`、`reset` は内容保持 or 再ロード）。
- role=`memory`、kind=`rom`、addressable=True、runtime_backed=True（段階: まず Part 追加 → runtime 化）。
- **配置**:
  - `game16` では `0x0000–0x7FFF` を ROM 候補（code）。
  - `circuit_compat` では RAM が 0x0000–0xFFFF を占有するため **ROM をそのまま 0x0000 に置けない**
    （RAM と衝突）。→ circuit_compat では **既定で ROM を使わない**（置いても Address Map Editor で base/size を
    手動指定 or RAM を縮小しない限り overlap）。**既定の Hello World は RAM ロードのまま不変**。
- **ロード方法**（重要・互換）:
  - 既定（circuit_compat）: **現行どおり RAM へロード**（`reset_pc=0x0000`）。ROM 非使用。
  - ROM を使う構成（opt-in / game16）: Write Program を **ROM へロード**、`reset_pc=layout.code_base`（=ROM 先頭）。
  - どちらに載せるかは「CPU の program 対象が ROM か RAM か」を plan / layout から決める（設計のみ）。
- ROM write 禁止: `RomPart.write` は no-op（CPU が ST/OUT で書いても黙って無視 or bus warning）。RAM と違い破壊不可。
- **既存 Hello World/selftest を壊さない**: ROM device を置かない限り経路は現行（RAM ロード）。

---

## 6. Input 設計

- `InputPart`（`core/dev.py`）= MMIO device。role=`mmio`、kind=`input`、addressable=True、runtime_backed=True。
- **base/size**: 既存 UART と同じ MMIO 窓割当（`assign_mmio_bases`：1 個目 0x0100 系列、複数なら 0x0110…）。
  size 8B（`layout.mmio_size`）。Address Map Editor で override 可。
- **レジスタ案**（base 相対・word read 前提）:
  - `+0x00` `KEY_STATE` (read): 現在押されているキーのビットマスク。
  - `+0x04` `EDGE_STATE` (read): 前回 clear 以降に押された（立ち上がり）ビットマスク。
  - （書込）`+0x00` or `+0x04` への write = `CLEAR_EDGE`（edge をクリア）。最小では read のみでも可。
- **CPU からの読み出し**: `LD rd, [rs]`（rs=Input base）で `KEY_STATE` を読む。**`IN` 命令は不要**
  （必要になれば `PATCH_AK32_INSTRUCTION_EXPANSION_V08` で追加）。
- **入力の供給経路**（UI → runtime）:
  - 最小: **Debug パネル / virtual buttons**（押下で `InputPart.set_keys(mask)`）。
  - 次段: Canvas/MainWin の **keyboard event** を InputPart へ橋渡し。
  - テスト: `InputPart.set_keys()` を直接叩いて LD で読めることを検証（headless 可）。
- **最小実装**: InputPart（KEY_STATE read + set_keys）+ Address Map 配置 + LD で読める + Debug の簡易ボタン。
  EDGE_STATE/CLEAR_EDGE は段階。

---

## 7. Timer / GPIO 設計（今回は後続）

- **Timer**: MMIO。`+0x00` cycle/tick カウンタ（`bus.read` で現在の `step_count`/cycle を返す）、`+0x04` frame。
  ゲームループ用。Input の後。
- **GPIO**: MMIO。8/16bit の汎用 in/out port（`+0x00` data）。Timer と同 Bus Part パターン。
- いずれも **今回やらない**（part.json は既存。runtime_backed=True 化 + Part 追加は後続パッチ）。
- Input と register/window が重複しないよう、それぞれ別 MMIO 窓（`assign_mmio_bases` が自動で別 base に並べる）。

---

## 8. VRAM / Video 設計（今回は後続）

- `mem.vram`（kind=vram, role=memory）は既に RAM 扱いしない土台がある。VRAM runtime は未実装。
- VRAM は **memory** として配置（フレームバッファ）。サイズが大きい（数 KB〜）ため **game16 layout 前提**
  （`0xC000–0xDFFF` 等）。circuit_compat の 64KB RAM 全域とは共存しづらい → 段階導入。
- Video regs（kind=video_regs, role=mmio）で描画モード/画面サイズ/コマンドを管理。
- **実際の画面表示（描画）は今回やらない**。最小ゲーム runtime（`PATCH_GAME_RUNTIME_MINIMAL_V08`）で
  VRAM→簡易描画を検討。VRAM/Video は ROM/Input の後。

---

## 9. Address Map / MemoryLayout との関係

- `circuit_compat`（既定）: 既存互換を守る（新 device を置かなければ現行どおり）。新 device を置いた場合のみ
  Address Map に追加され、MMIO は窓カービング、ROM/VRAM(memory) は RAM と重なるため Editor で base/size 調整
  か game16 が前提。
- `game16`: ROM(0x0000–0x7FFF) / RAM(0x8000) / VRAM(0xC000) / MMIO(0xE000) を分ける（layout 既定値）。
- Address Map Editor: 新 device も per-device base/size override 可（既存 `apply_address_overrides` /
  `validate_address_overrides` がそのまま効く）。
- `make_device_spec()`: kind→role/addressable/runtime_backed の表を拡張（rom/input を runtime_backed True へ）。
- `assign_mmio_bases()`: input も role=mmio なので**自動的に窓割当の対象**（UART と同列に並ぶ）。
- overlap validation: 既存 `validate_address_map` / `validate_address_overrides` が新 device にもそのまま適用。

---

## 10. part.json / Library 方針

新規 part（追加が必要なもの）:
- `mem.rom`（**新規**）: id `mem.rom` / name "ROM" / category `mem` / ports（bus.slave, clk, reset）/ v2 schema。
- `io.input`（**新規**）: id `io.input` / name "Input" / category `io` / ports（bus.slave, input(type 新規), clk, reset）。
既存利用（runtime 化のみ・part.json 変更最小）:
- `io.timer` / `io.gpio` / `mem.vram` / `video.regs` は**既存**。device_kind は既に timer/gpio/vram/video_regs。
  runtime 化時に `_RUNTIME_BACKED` へ追加するだけ（part.json は基本そのまま、必要なら ports 補足）。

各 part.json 必須項目（schema v2）: `id` / `name` / `category` / `schema_version` / `ports`（各 port に
direction/width/role/required/description）。`device_kind` は part_id ベースなので **`_KIND_BY_PART_ID` に
`mem.rom`→rom / `io.input`→input を追加**する必要がある（devices.py 側）。icon/visual は既存カテゴリ色を流用。

---

## 11. runtime 設計

`core/dev.py` に Bus Part を追加（既存 `RamPart`/`UartPart` と同じ Bus device インターフェース）:
- `RomPart(part_id, name, size, base)`: read=word LE / **write=no-op** / `load_bytes` / `dump` / `reset`(内容保持 or 0)。
- `InputPart(part_id, name, base)`: read（KEY_STATE/EDGE_STATE）/ write（CLEAR_EDGE・最小では no-op）/
  `set_keys(mask)` / `reset`。
- （後続）`TimerPart` / `GpioPart` / `VramPart`。

共通方針:
- 既存 `RamPart`/`UartPart` と同様、`Bus.attach` で base/size 範囲に載せ、`bus.read/write` でアクセス。
- `reset` 挙動: RAM は 0 クリア、ROM は内容保持、Input は state クリア。
- save/load: 内容（ROM image / input state）は基本 runtime のみ（永続化は project の役割・最小では非永続）。
- **bus trace**: 既存 `on_access` フックでそのまま trace に出る（device_id で識別）。
- **runtime_id**: rom→`sim_rom` / input→`sim_input`（複数時は 1 個目のみ backed、追加は multi-UART と同様
  `device_id` ユニーク化・runtime_backed False＝Address Map 配置のみ）。
- `_build_runtime_devices`（ui/win.py）: runtime_backed な kind を Part 化する分岐に rom/input を追加。
- **複数 instance**: 当面 1 個目のみ runtime 化（multi-RAM/UART と同方針）。

---

## 12. CPU / ASM との関係

- **現在の CPU 命令で MMIO read 可能**（`LD rd,[rs]` = bus.read）。→ Input/Timer/GPIO は **LD で読める**。
- ROM からの fetch: CPU の命令 fetch は `bus.read(pc)`。ROM を bus に載せて `reset_pc=ROM base` にすれば
  **ROM から fetch できる**（追加命令不要）。ただし circuit_compat 既定は RAM fetch のまま。
- `IN` 命令は**不要**（Input は LD で読む）。`CALL/RET/stack/IN` は `PATCH_AK32_INSTRUCTION_EXPANSION_V08`
  へ送る（本パッチの前提にしない）。
- assembler: device symbol / MMIO label（例 `INPUT_BASE = 0x0110`）は**任意**。最小では数値リテラルで足りる
  （hello/selftest と同様）。symbol 機能は後続で検討。
- **本パッチは CPU 命令も assembler も拡張しない**（ROM/Input device + bus 配線のみで実現）。

---

## 13. 実装スコープ案

比較:
- **A. ROM+Input を一括**（`PATCH_DEVICE_EXPANSION_ROM_INPUT_V08`）: まとまるが差分が大きい。
- **B. 分割（推奨）**: `PATCH_ROM_DEVICE_V08`（RomPart + mem.rom + 配置/読込方針）→ `PATCH_INPUT_DEVICE_V08`
  （InputPart + io.input + LD read + Debug ボタン）。各々小さく・回帰しやすい。
- **推奨**: **B（分割）**。Input の方が CPU 改修不要で低リスク・価値大なので、**Input を先に**実装する案も有力
  （ROM は circuit_compat で置き場が無く game16/Editor 前提のため、Input 先行が体験として早く効く）。

共通前提（どの順でも）:
- **resolve_circuit を「target CPU に wired な addressable device を全 kind 収集」へ拡張**（cpu/rams/uarts キーは
  互換維持しつつ `plan["devices"]` 等を追加）。これが ROM/Input を Address Map/runtime に載せる土台。
- 既定 `circuit_compat` で**新 device を置かなければ現行完全一致**。
- 新 device を置いたときだけ Address Map に出る／runtime 化される。
- 新 device を置かない限り既存テストは完全一致。

---

## 14. テスト方針（実装時に追加するテスト）

- 新 part（`mem.rom` / `io.input`）が Library に出る・v2 schema 正規化される。
- `device_kind`: `mem.rom`→rom / `io.input`→input。`device_role`/addressable/runtime_backed が正しい。
- `make_device_spec` が rom/input の spec を正しく作る（role/addressable/runtime_backed/base/size）。
- **ROM が read-only**（write 後も内容不変）/ ROM に load_bytes できる・読み戻せる。
- **Input が MMIO read で値を返す**（`set_keys` → `LD`/bus.read で KEY_STATE 取得）。
- Address Map に ROM/Input が載る・Editor で override できる・overlap validation が効く。
- resolve_circuit が ROM/Input を device として収集する（cpu/rams/uarts 互換維持）。
- **既存 CPU/RAM/UART 構成は壊れない**（新 device 無しで Address Map dict 完全一致）。
- Hello World / ram_selftest / legacy が壊れない。
- `python -m pytest tests/` 全通過。

---

## 15. 今回やらないこと

- 実装 / part.json 追加 / ROM runtime / Input runtime
- Timer / GPIO / VRAM / Video regs / Storage runtime
- CPU 命令拡張（CALL/RET/IN/stack）/ ASM 拡張
- game16 layout への自動切替
- VRAM 描画 / 画面表示
- Storage 実装
- HDL / FPGA export
- コード実装 / テスト追加 / 既存挙動変更
- commit / push

---

## 16. 次に続くパッチ（候補順）

1. `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08`（本パッチ）。**分割案**: `PATCH_INPUT_DEVICE_V08`（先・低リスク）
   → `PATCH_ROM_DEVICE_V08`（game16/Editor 前提）。
2. `PATCH_AK32_INSTRUCTION_EXPANSION_V08`（CALL / RET / IN・stack — `stack_top` を layout から）
3. `PATCH_GAME_RUNTIME_MINIMAL_V08`（最小ゲーム runtime: Input + Timer + VRAM/簡易描画）
4. `PATCH_V08_STABILIZE_AND_DOCS`（v0.8 安定化・ドキュメント・PHASE COMPLETE 準備）

> 横断候補（`V08_CODEBASE_REVIEW.md` §4）: Diagnostics Panel / Project Validation / opcode 単一化 /
> テストフィクスチャ整理。
