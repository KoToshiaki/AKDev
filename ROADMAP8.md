# AKDev ROADMAP 8

> v0.8 開発計画（**候補整理のみ**。実装は未着手。ユーザー指示後に着手する）。
> **現行の管理ファイルは `ROADMAP8.md` / `CHECKLIST8.md`。**
> v0.7（Plan-driven Virtual Devices & Address Map）の到達点は
> `old/ROADMAP7.md`（✅ v0.7 PHASE COMPLETE）/ `old/CHECKLIST7.md` を参照。
> v0.6 以前の計画書・チェックリスト（`ROADMAP6.md`〜・`CHECKLIST6.md`〜）も `old/` に収納済み。
> 進捗管理は実装開始時に `CHECKLIST8.md` で行う。

---

## v0.7 からの引き継ぎ状況

v0.7 で、Canvas に描いた CPU+RAM+UART 回路を CircuitPlan から実デバイス化して実行し、
Address Map・実行状態（Run Status Panel）・ポート/接続（Port Detail Panel）を確認できる
ところまで到達した。`pytest tests/` = 860 passed。

v0.8 は、この実行基盤の上で **接続の妥当性検証** と **デバイス種別の拡張**、そして
**ゲーム runtime / HDL・FPGA export への準備**を進めるフェーズと位置づける。

---

## v0.8 テーマ（候補）

**Device Expansion & Connection Validation**
（接続検証とデバイス拡張 — 実行基盤から「正しく組めるか」を検証し、デバイス種別を増やす）

---

## v0.8 作業候補（未確定・優先順位は今後決定）

> **進捗**: A〜E は実装完了（`PATCH_PORT_SCHEMA_V08` / `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08` /
> `PATCH_BUS_PROTOCOL_VALIDATION_V08` / `PATCH_DEVICE_REGISTRY_REFACTOR_V08` /
> `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08` / `PATCH_CODE_REGION_MMIO_RELOCATION_V08` /
> `PATCH_ADDRESS_MAP_EDITOR_V08`）。`PATCH_DEVICE_EXPANSION_ROM_INPUT_V08` は設計資料作成済み（実装未着手）。
> 各 PATCH の進捗詳細は `CHECKLIST8.md` を参照。
> 検証系（A/B）は **warning only**（接続ブロックはせず Log + Port Detail に診断表示）の方針。

### A. Port direction / width validation
- part.json の `ports` に direction / width を明示し、接続時に整合を検証。
- 前段の ports schema 正規化（`PATCH_PORT_SCHEMA_V08`）は完了。
- 本体 `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08` は **warning only** で開始（ブロックは次以降）。
- master↔slave / out↔in / width 一致などの接続可否ルール。

### B. Bus protocol validation
- bus.master ↔ bus.slave の対応、1 master 制約などの検証。
- Address Map と組み合わせた到達性チェック。
- `PATCH_BUS_PROTOCOL_VALIDATION_V08` 実装済み。初手は **warning only**（bus group の master/slave 数診断。
  到達性本対応は次段）。設計資料: `PATCH_BUS_PROTOCOL_VALIDATION_V08_ROADMAP.md` / `..._CHECKLIST.md`。

### C. 複数 RAM / UART handling
- 現状は単一前提。複数 RAM/UART を Address Map 上で共存させる。
- target CPU から見た複数スレーブのアドレス割当・選択。
- `PATCH_DEVICE_REGISTRY_REFACTOR_V08`（device list driven 化・VRAM≠RAM 土台）と
  `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08`（複数 UART/MMIO 配置・複数 RAM 検出+warning・`resolve_circuit`
  を device_kind ベースへ）で実装済み。複数 RAM の真の共存は 16bit 制約のため候補 F へ送る。

### D. ROM / VRAM / Storage / Input device expansion
- 新デバイス種別の plan-driven 生成（v0.7 の RAM/UART と同方式）。
- それぞれの MMIO 窓・Address Map 統合。
- **次候補として `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08` を検討中**（`PATCH_ADDRESS_MAP_EDITOR_V08`
  の次）。**ROM / Input を優先**し VRAM/Storage は後続へ。Input は AK32 の `LD`（=bus.read）で読めるため
  `IN` 命令不要。新 device を置かない限り現行互換。実装は分割案（`PATCH_INPUT_DEVICE_V08` 先行 →
  `PATCH_ROM_DEVICE_V08`）も検討。設計資料: `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08_ROADMAP.md` /
  `..._CHECKLIST.md`（実装は未着手）。
- **分割の先行候補 `PATCH_INPUT_DEVICE_V08` 実装完了**（Input 単独・MMIO・`sim_input`・`LD` で読む）。
- **`PATCH_ROM_DEVICE_V08` 実装完了**（ROM 単独・read-only memory・`sim_rom`）。`mem.rom` を追加し
  `RomPart`（write=no-op・reset で内容保持）として runtime 化。`MemoryLayout` に `rom_base`/`rom_size`
  （既定 None・GAME16 0x0000/0x8000）。既定 `circuit_compat` は **RAM ロード維持**（ROM 非配置は現行互換・
  ROM 配置は Editor override で base 付与+RAM 縮小）、`game16` は ROM 0x0000 / RAM 0x8000 非重複。
  **Program loader は RAM のまま**（ROM target 化は後続 `PATCH_PROGRAM_TARGET_ROM_V08`）。
- **`PATCH_PROGRAM_TARGET_ROM_V08` 実装完了**（program target: RAM / ROM 選択）。Write Program のロード先を
  RAM/ROM で切替（`self._program_target`・`system.json` に `program_target` 永続化・無/不正は RAM）。ROM target は
  `RomPart.load_bytes()` でロードし CPU `reset_pc=rom.base`（CPU/bus write は no-op のまま）。ROM 不成立（無し/未配置/
  overlap/size 超過）は error で RAM へ fallback しない。**既定は RAM・既存 project は RAM 互換**。
  `python -m pytest tests/` → 1080 passed（+21）。次候補 `PATCH_AK32_INSTRUCTION_EXPANSION_V08` / `PATCH_TIMER_DEVICE_V08`。
- **次候補として `PATCH_AK32_INSTRUCTION_EXPANSION_V08`（AK32 ISA 拡張）を検討中**（親設計）。一気に足さず段階分割し、
  **最初は Bitwise（`AND`/`OR`/`XOR`/`NOT`）を優先**（Input bit 判定直結・stack 不要）。`CALL`/`RET` は stack 設計が要るため
  後続 `PATCH_AK32_STACK_CALL_RET_V08` へ。opcode は既存 0x00–0x0A 不変・末尾追記（0xFF 予約）。opcode 三重管理
  （cpu/asm/disasm）の単一化は任意先行 `PATCH_AK32_OPCODE_TABLE_V08`。設計資料:
  `PATCH_AK32_INSTRUCTION_EXPANSION_V08_ROADMAP.md` / `..._CHECKLIST.md`（実装は未着手）。
- **`PATCH_AK32_BITWISE_INSTRUCTIONS_V08` 実装完了**（`AND`=0x0B/`OR`=0x0C/`XOR`=0x0D/`NOT`=0x0E）。`AND`/`OR`/`XOR` は
  3 オペランド・`NOT` は 2 オペランド。CPU（`_execute`・`_set_reg`・Z 更新・32bit mask）/ ASM（`_OPCODES`+encode）/
  disasm の 3 か所に追記。**Input bit 判定が可能**（`LD`+`AND`+`BEQ`・押下/非押下を実証）。ROM target からも fetch/execute。
  既存 opcode 0x00–0x0A 不変・0xFF は unknown のまま。`CALL`/`RET`/stack は後続 `PATCH_AK32_STACK_CALL_RET_V08`。
  `python -m pytest tests/` → 1111 passed（+31）。次候補 `PATCH_AK32_SHIFT_IMM_BITWISE_V08` / `PATCH_AK32_BRANCH_EXPANSION_V08` / `PATCH_TIMER_DEVICE_V08`。
- **`PATCH_TIMER_DEVICE_V08` 実装完了**（MMIO Timer・`io.timer` / `TimerPart` / `sim_timer`）。**deterministic tick（CPU step 数
  ベース・wall-clock 不使用・割り込みなし）**。CPU から既存 `LD` で読み・`ST` で clear（CPU 命令追加なし）。MMIO 窓 0x08（stride
  0x10）で UART+Input+Timer は 0x0100/0x0110/0x0120 に自動配置。registry は `_RUNTIME_BACKED`/`_RUNTIME_ID` に timer 追加
  （kind/role/label は既存）。`VirtualCircuitRuntime(timer=…)` が `step()` の step_count++ 後に `timer.tick()`・reset/load で reset。
  Run Status に `Timer:` 行。**Timer 非配置は現行互換**（dict 一致・Hello World/legacy 不変）。`python -m pytest tests/` → 1136
  passed（+25）。**Game Runtime Minimal の前段**（次: VRAM→Game Runtime→Stabilize）。設計資料: `PATCH_TIMER_DEVICE_V08_ROADMAP.md` / `..._CHECKLIST.md`。
- **次候補として `PATCH_VRAM_DEVICE_V08`（最小 framebuffer）を検討中**。`mem.vram`（kind=vram・role=memory・writable・reset 0
  クリア）を追加し、CPU から既存 `LD`/`ST` でアクセス（CPU 命令追加なし）。初期は **indexed color 32×32 / 1 byte/pixel / 1024 B**。
  ROM と同型の memory device で circuit_compat は Editor override 配置（game16 は 0xC000 案）。**表示 UI は後続**（`PATCH_GAME_RUNTIME_MINIMAL_V08`
  / `PATCH_VRAM_VIEWER_V08`）。**Game Runtime Minimal の前段**（VRAM→Game Runtime→Stabilize）。VRAM 非配置は現行互換。
  設計資料: `PATCH_VRAM_DEVICE_V08_ROADMAP.md` / `..._CHECKLIST.md`（実装は未着手）。

### E. Address Map Editor
- ユーザーによる base/size の任意編集 UI（v0.7 は固定既定）。
- overlap 検出（既存）と連動した編集時バリデーション。
- `PATCH_ADDRESS_MAP_EDITOR_V08` 実装済み（`MemoryLayout` の自動配置の上に per-device `base`/`size`
  override・auto/manual・Reset to Auto・range/overlap/align validation・system.json 永続化）。
  既定（override 無し）は現行互換。

### F. コード領域の拡張設計 / UART MMIO 窓の再配置・可変化
- 現状コードは 0x0000 開始・UART 窓 0x0100–0x0107 固定。
- 大きめプログラム/ゲーム向けにコード領域・MMIO 配置を見直す。
- `PATCH_CODE_REGION_MMIO_RELOCATION_V08` で `MemoryLayout`（`LEGACY` / `CIRCUIT_COMPAT` 既定 /
  `GAME16` 候補）を導入し RAM base/size・MMIO base を可変化する土台を実装済み（既定は現行互換・
  MMIO 実再配置や ROM 化は段階導入）。

### G. CPU 命令拡張
- CALL / RET / IN 等（スタック設計が必要）。
- 既存 11 命令（NOP/HALT/LDI/OUT/ADD/SUB/LD/ST/JMP/BEQ/ADDI）の上に追加。
- 候補 `PATCH_AK32_INSTRUCTION_EXPANSION_V08`。Input は `LD` で読めるため本命令拡張の前提にはしない。

### H. ゲーム runtime 準備
- 最終目標「自作 CPU 上でゲーム 1 本を起動・操作」に向けた実行環境の整備。
- 入力・表示・タイミングの最小ループ設計。
- 候補 `PATCH_GAME_RUNTIME_MINIMAL_V08`（Input + Timer + VRAM/簡易描画）。

### I. HDL / FPGA export 準備
- 回路 → HDL 出力、合成（iverilog / Yosys）、FPGA 実機書き込みの準備。

---

## v0.8 ではまだ確定でないこと

- 上記候補の取捨選択・順序はユーザー判断で確定する。
- 1 パッチ = 1 機能の運用（`PATCH_*_V08_*` の ROADMAP/CHECKLIST を着手前に作成）。

---

## 今回（v0.7 完了整理）でやらないこと

- 上記の実装。新機能・挙動変更・テスト追加・commit / push は行わない。
- 本ファイルは候補整理のみ。実装はユーザーが最初のパッチを指示してから着手する。
