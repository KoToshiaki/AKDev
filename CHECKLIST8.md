# AKDev CHECKLIST 8

> v0.8 進捗管理チェックリスト（**候補整理のみ**。実装は未着手）。
> **現行の管理ファイルは `ROADMAP8.md` / `CHECKLIST8.md`。**
> 設計詳細・候補は `ROADMAP8.md` を参照。
> v0.7 の進捗は `old/CHECKLIST7.md`（✅ v0.7 PHASE COMPLETE・履歴保管）を参照。
> v0.6 以前（`old/ROADMAP6.md`〜・`old/CHECKLIST6.md`〜）も `old/` に収納済み。

---

# 0. v0.8 開始準備

* [x] `ROADMAP8.md` を作成した（候補整理）
* [x] `CHECKLIST8.md` を作成した
* [x] 前フェーズ資料を `old/` へ整理した（2026-06-17）
  - `git mv` で `ROADMAP6.md` / `CHECKLIST6.md` / `ROADMAP7.md` / `CHECKLIST7.md` を `old/` へ収納
  - root の現行管理ファイルは `ROADMAP8.md` / `CHECKLIST8.md` のみ（v0.6 / v0.7 は完了済み履歴）
* [x] v0.8 最初の候補として `PATCH_PORT_SCHEMA_V08` の設計資料を作成した（2026-06-17）
  - `PATCH_PORT_SCHEMA_V08_ROADMAP.md` / `PATCH_PORT_SCHEMA_V08_CHECKLIST.md`
* [x] `PATCH_PORT_SCHEMA_V08` 実装完了（2026-06-17）
  - `core/ports.py` 追加 / `parts/**/part.json` 11 種を v2 へ migration / `ui/lib.py` 正規化 / `ui/port_detail.py` 明示値優先表示
  - `python -m pytest tests/` → **878 passed**（860 + 新規 18）
  - 次候補: `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08`（接続時 direction/width 検証）
* [x] 次候補 `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08` の設計資料を作成した（2026-06-17）
  - `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08_ROADMAP.md` / `..._CHECKLIST.md`
* [x] `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08` 実装完了（2026-06-17・**warning only**）
  - `core/port_validation.py` 追加 / `ui/canvas.py` 接続時検証+API / `ui/port_detail.py` Validation 表示
  - `python -m pytest tests/` → **913 passed**（878 + 新規 35）
  - 次候補: `PATCH_BUS_PROTOCOL_VALIDATION_V08`（1 master 制約・到達性）
* [x] 次候補 `PATCH_BUS_PROTOCOL_VALIDATION_V08` の設計資料を作成した（2026-06-17）
  - `PATCH_BUS_PROTOCOL_VALIDATION_V08_ROADMAP.md` / `..._CHECKLIST.md`
* [x] `PATCH_BUS_PROTOCOL_VALIDATION_V08` 実装完了（2026-06-17・**warning only**）
  - `core/bus_validation.py` 追加 / `ui/canvas.py` bus validation API+Log / `ui/port_detail.py` bus issue 表示
  - `python -m pytest tests/` → **937 passed**（913 + 新規 24）
  - 次候補: `PATCH_DEVICE_REGISTRY_REFACTOR_V08` または `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08`
* [x] 次候補 `PATCH_DEVICE_REGISTRY_REFACTOR_V08` の設計資料を作成した（2026-06-17）
  - `PATCH_DEVICE_REGISTRY_REFACTOR_V08_ROADMAP.md` / `..._CHECKLIST.md`
* [x] `PATCH_DEVICE_REGISTRY_REFACTOR_V08` 実装完了（2026-06-17・**挙動不変リファクタ**）
  - `core/devices.py` 追加 / `core/circuit.py` に `build_address_map_from_devices`（`build_address_map` は委譲）/ `ui/win.py:_make_sim` を device spec 駆動に分割
  - `mem.vram` を part_id ベースで分類し RAM 化しない土台
  - `python -m pytest tests/` → **957 passed**（937 + 新規 20）
  - 次候補: `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08`
* [x] 次候補 `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08` の設計資料を作成した（2026-06-17）
  - `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08_ROADMAP.md` / `..._CHECKLIST.md`
* [x] `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08` 実装完了（2026-06-17・**単一構成完全互換**）
  - `resolve_circuit` を `device_kind` ベースへ（VRAM≠RAM 本修正・rams/uarts を node_id ソート）/ `core/devices.py` に `assign_mmio_bases`・`multi_device_warnings` / `ui/win.py` を複数 UART 配置 + 複数 RAM warning へ
  - 複数 UART = 0x0100/0x0110/0x0120…（RAM を複数窓カービング）、runtime は 1 個目互換、複数 RAM は warning
  - `python -m pytest tests/` → **973 passed**（957 + 新規 16）
  - 次候補: `PATCH_ADDRESS_MAP_EDITOR_V08` または `PATCH_CODE_REGION_MMIO_RELOCATION_V08`
* [x] 次候補 `PATCH_CODE_REGION_MMIO_RELOCATION_V08` の設計資料を作成した（2026-06-17）
  - `PATCH_CODE_REGION_MMIO_RELOCATION_V08_ROADMAP.md` / `..._CHECKLIST.md`
* [x] `PATCH_CODE_REGION_MMIO_RELOCATION_V08` 実装完了（2026-06-17・**既定は現行互換**）
  - `core/devices.py` に `MemoryLayout`（LEGACY/CIRCUIT_COMPAT 既定/GAME16 design-only）+ `get_memory_layout` / `make_device_spec`・`assign_mmio_bases`・`build_address_map_from_devices`・`_make_sim` を layout aware に / `reset_pc` を layout 由来
  - 既定 = circuit_compat = 現行（Address Map dict・UART 0x0100・RAM 64KB・reset_pc 0x0000 不変）
  - `python -m pytest tests/` → **988 passed**（973 + 新規 15）
  - 次候補: `PATCH_ADDRESS_MAP_EDITOR_V08` または `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08`
* [x] 次候補 `PATCH_ADDRESS_MAP_EDITOR_V08` の設計資料を作成した（2026-06-18）
  - `PATCH_ADDRESS_MAP_EDITOR_V08_ROADMAP.md` / `..._CHECKLIST.md`
* [x] `PATCH_ADDRESS_MAP_EDITOR_V08` 実装完了（2026-06-18・**override 無しは現行互換**）
  - `ui/address_map_editor.py`（Dock + 表 + Apply/Reset/Refresh）/ `core/devices.py` に `apply_address_overrides`・`parse_address_int` / `core/circuit.py` に `validate_address_overrides` / `ui/win.py` を `_auto_device_specs`+override 分割・editor API・persist
  - GUI で per-device base/size override（auto/manual・Reset to Auto・range/overlap/align validation・error は Apply ブロック）・system.json 永続化
  - `python -m pytest tests/` → **1011 passed**（988 + 新規 23）
  - 次候補: `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08` または `PATCH_AK32_INSTRUCTION_EXPANSION_V08`
* [x] 分割先行候補 `PATCH_INPUT_DEVICE_V08` の設計資料を作成した（2026-06-18）
  - `PATCH_INPUT_DEVICE_V08_ROADMAP.md` / `..._CHECKLIST.md`
* [x] `PATCH_INPUT_DEVICE_V08` 実装完了（2026-06-18・**Input 非配置は現行互換**）
  - `parts/io/input/part.json` 追加 / `core/devices.py`（input kind/role/runtime・`assign_mmio_bases` を kind 単位 backing）/ `core/dev.py` `InputPart` / `core/circuit.py` `resolve_circuit` に `inputs`/`devices` / `ui/win.py` Input runtime + `set_input_keys`
  - CPU は既存 `LD` で Input を読む（`IN` 命令不要）。UART+Input で UART 0x0100 / Input 0x0110・両 backed
  - `python -m pytest tests/` → **1034 passed**（1011 + 新規 23）
  - 次候補: `PATCH_ROM_DEVICE_V08` または `PATCH_AK32_INSTRUCTION_EXPANSION_V08`
* [x] 次候補 `PATCH_ROM_DEVICE_V08` の設計資料を作成した（2026-06-18）
  - `PATCH_ROM_DEVICE_V08_ROADMAP.md` / `..._CHECKLIST.md`。**実装は未着手・ROM 単独（read-only memory・`sim_rom`）・既定 circuit_compat は RAM ロード維持・ROM 配置は game16 / Editor override・Program loader は RAM のまま（ROM target 化は後続）・ROM 非配置は現行互換**
* [x] `PATCH_ROM_DEVICE_V08` 実装完了（2026-06-18・**ROM 非配置は現行互換**）
  - `parts/mem/rom/part.json` 追加 / `core/devices.py`（rom kind/runtime・`MemoryLayout` に `rom_base`/`rom_size`・`_base_size` ROM 分岐・GAME16 0x0000/0x8000）/ `core/dev.py` `RomPart`（read-only・reset 保持・load_bytes/dump）/ `core/circuit.py` `resolve_circuit` に `roms` / `ui/win.py` ROM runtime（`self._sim_rom`・base 有りのみ runtime 化）
  - read-only（CPU/bus write は no-op）。circuit_compat は base 無し→未配置（Editor override で配置・RAM 縮小要）。game16 は ROM 0x0000 / RAM 0x8000 非重複。**Program loader は RAM ロードのまま**（ROM target 化は後続）
  - `python -m pytest tests/` → **1059 passed**（1034 + 新規 25）
  - 次候補: `PATCH_PROGRAM_TARGET_ROM_V08` または `PATCH_AK32_INSTRUCTION_EXPANSION_V08`
* [x] 次候補 `PATCH_PROGRAM_TARGET_ROM_V08` の設計資料を作成した（2026-06-19）
  - `PATCH_PROGRAM_TARGET_ROM_V08_ROADMAP.md` / `..._CHECKLIST.md`。**実装は未着手・program target: RAM / ROM 選択・既定 RAM 互換・ROM target は `RomPart.load_bytes()` でロード・CPU/bus write は no-op のまま・ROM target 時 `reset_pc=rom.base`・ROM runtime（base 確定）がある時のみ ROM 有効・既存 project に `program_target` 無しは RAM 扱い**
* [x] `PATCH_PROGRAM_TARGET_ROM_V08` 実装完了（2026-06-19・**既定 RAM・既存 project は RAM 互換**）
  - `ui/win.py`（`_program_target` / `_normalize_program_target` / `set_program_target` / `program_target` / `_program_target_status` / `_rom_runtime_ready` / `_load_program_to_ram` / `_load_program_to_rom`・`_assemble_and_load` で RAM/ROM 分岐・`_build_runtime_devices` で ROM target 時 `reset_pc=rom.base`・project new/open/persist で `program_target`）/ `ui/run_status.py`（`Program Target` 行）
  - ROM target は `RomPart.load_bytes()` でロード（bus write ではない）。ROM 不成立（無し/未配置/overlap/size 超過）は error・RAM へ fallback しない。`VirtualCircuitRuntime.load_program` は不変。`tests/test/system.json` 差分なし
  - `python -m pytest tests/` → **1080 passed**（1059 + 新規 21）
  - 次候補: `PATCH_AK32_INSTRUCTION_EXPANSION_V08` または `PATCH_TIMER_DEVICE_V08`
* [x] 次候補 `PATCH_AK32_INSTRUCTION_EXPANSION_V08` の設計資料を作成した（2026-06-19・親設計）
  - `PATCH_AK32_INSTRUCTION_EXPANSION_V08_ROADMAP.md` / `..._CHECKLIST.md`。**実装は未着手・ISA 拡張は段階分割・最初の実装候補は Bitwise（`AND`/`OR`/`XOR`/`NOT`＝`PATCH_AK32_BITWISE_INSTRUCTIONS_V08`）・CALL/RET/stack は後続 `PATCH_AK32_STACK_CALL_RET_V08`・既存 opcode 0x00–0x0A 不変で末尾追記（0xFF 予約）・opcode 三重管理の単一化は任意先行 `PATCH_AK32_OPCODE_TABLE_V08`・既存互換維持**
* [x] 最初の子パッチ `PATCH_AK32_BITWISE_INSTRUCTIONS_V08` の設計資料を作成した（2026-06-19）
  - `PATCH_AK32_BITWISE_INSTRUCTIONS_V08_ROADMAP.md` / `..._CHECKLIST.md`。**実装は未着手・対象命令は `AND`/`OR`/`XOR`/`NOT` の 4 命令のみ・opcode `AND=0x0B`/`OR=0x0C`/`XOR=0x0D`/`NOT=0x0E`・`AND`/`OR`/`XOR` は 3 オペランド R-type・`NOT` は 2 オペランド・既存 opcode 0x00–0x0A 不変・0xFF 予約・CPU/ASM/disasm の 3 か所追記・Input bit 判定（`LD`+`AND`+`BEQ`）に直結・opcode 単一化/shift/imm bitwise/branch/CALL/RET/IN は対象外・既存互換維持**
* [x] `PATCH_AK32_BITWISE_INSTRUCTIONS_V08` 実装完了（2026-06-20・**既存 opcode 0x00–0x0A 不変・0xFF は unknown のまま**）
  - 追加命令: `AND`=0x0B / `OR`=0x0C / `XOR`=0x0D（3 オペランド）/ `NOT`=0x0E（2 オペランド）。`core/cpu.py`（`OP_*` 定数 + `_execute` 4 分岐・`_set_reg`・Z 更新・32bit mask）/ `asm/asm.py`（`_OPCODES` + encode・operand 数チェック）/ `core/runtime.py:disasm`（4 命令表示）
  - Input bit 判定（`LD`+`AND`+`BEQ`・押下 r4==1 / 非押下 r4==0）・ROM target から fetch/execute（OR で r3==0x00FF）をテストで実証。`tests/test_ak32_bitwise_instructions_v08.py`（31 件）・`tests/test/system.json` 差分なし
  - `python -m pytest tests/` → **1111 passed**（1080 + 新規 31）
  - 次候補: `PATCH_AK32_SHIFT_IMM_BITWISE_V08` / `PATCH_AK32_BRANCH_EXPANSION_V08` / `PATCH_TIMER_DEVICE_V08`
* [x] 次候補 `PATCH_TIMER_DEVICE_V08` の設計資料を作成した（2026-06-20）
  - `PATCH_TIMER_DEVICE_V08_ROADMAP.md` / `..._CHECKLIST.md`。**実装は未着手・Timer は MMIO device（CPU 命令追加なし・既存 `LD`/`ST` で読む/clear）・deterministic tick（CPU step 数ベース・wall-clock 不使用）・割り込みなし・MMIO 窓 0x08（UART/Input と同じ）で自動配置 0x0120・registry は `_RUNTIME_BACKED`/`_RUNTIME_ID` のみ追加（kind/role/label は既存）・`runtime.step()` 後に `timer.tick()`・Timer 非配置は現行互換・Game Runtime Minimal の前段**
* [x] `PATCH_TIMER_DEVICE_V08` 実装完了（2026-06-20・**Timer は MMIO device・CPU 命令追加なし・Timer 非配置は現行互換**）
  - `core/devices.py`（`_RUNTIME_BACKED`/`_RUNTIME_ID` に timer）/ `core/dev.py`（`TimerPart`・TICK/DELTA・tick()/reset()・write=clear・32bit mask）/ `core/circuit.py`（`plan["timers"]`）/ `core/runtime.py`（`VirtualCircuitRuntime(timer=…)`・`step()` で `timer.tick()`・reset/load で reset）/ `ui/win.py`（`self._sim_timer`・`_auto_device_specs`/`_build_runtime_devices`・Run Status timer）/ `ui/run_status.py`（`Timer:` 行）。`parts/io/timer/part.json` は既存を流用（変更なし）
  - deterministic tick（CPU step 数・wall-clock 不使用・割り込みなし）。UART+Input+Timer で 0x0100/0x0110/0x0120。CPU は既存 `LD` で read・`ST` で clear。`tests/test_timer_device_v08.py`（25 件）・`tests/test/system.json` 差分なし
  - `python -m pytest tests/` → **1136 passed**（1111 + 新規 25）
  - 次候補: `PATCH_VRAM_DEVICE_V08` / `PATCH_GAME_RUNTIME_MINIMAL_V08` / `PATCH_V08_STABILIZE_AND_DOCS`
* [x] 次候補 `PATCH_VRAM_DEVICE_V08` の設計資料を作成した（2026-06-20）
  - `PATCH_VRAM_DEVICE_V08_ROADMAP.md` / `..._CHECKLIST.md`。**実装は未着手・VRAM は CPU から `LD`/`ST` 可能な memory device（kind=vram・role=memory・writable・reset 0 クリア・CPU 命令追加なし）・初期は indexed color 32×32 / 1 byte/pixel / 1024 B・ROM と同型で circuit_compat は Editor override 配置（game16 は 0xC000 案）・registry は `_RUNTIME_BACKED`/`_RUNTIME_ID`/`_base_size` のみ追加（kind/role/label は既存）・表示 UI は後続（`PATCH_GAME_RUNTIME_MINIMAL_V08` / `PATCH_VRAM_VIEWER_V08`）・VRAM 非配置は現行互換・Game Runtime Minimal の前段**
* [x] `PATCH_VRAM_DEVICE_V08` 実装完了（2026-06-21・**VRAM は runtime-backed writable framebuffer・CPU 命令追加なし・VRAM 非配置は現行互換**）
  - `parts/mem/vram/part.json`（v2・bus/clk/reset・既存流用）/ `core/devices.py`（`_RUNTIME_BACKED`/`_RUNTIME_ID["vram"]="sim_vram"` / `_base_size` vram 分岐 / `MemoryLayout.vram_base`/`vram_size`・GAME16=0xC000/0x0400）/ `core/dev.py`（`VramPart`・32bit LE word read/write・reset 0 クリア・dump/pixel/set_pixel・範囲外 BusError）/ `core/circuit.py`（`_is_vram`・`plan["vrams"]`・早期 return に vrams:[]）/ `ui/win.py`（`self._sim_vram`/`_sim_vram_node`・`_auto_device_specs`/`_build_runtime_devices`・`seen_vram` dedup・base 無しは未配置）/ `ui/run_status.py`（`VRAM:` 行）
  - circuit_compat は Editor override で配置（game16 は 0xC000 自動）。CPU は既存 `LD`/`ST` で読み書き。ROM target + VRAM 構成も実行可。表示 panel は今回なし。`tests/test_vram_device_v08.py`（28 件）・旧 `test_device_registry_refactor_v08.py` の vram=runtime-backed 化に伴う 2 件を更新・`tests/test/system.json` 差分なし
  - `python -m pytest tests/` → **1164 passed**（1136 + 新規 28）
  - 次候補: `PATCH_GAME_RUNTIME_MINIMAL_V08` / `PATCH_VRAM_VIEWER_V08` / `PATCH_V08_STABILIZE_AND_DOCS`
* [x] 次候補 `PATCH_GAME_RUNTIME_MINIMAL_V08` の設計資料を作成した（2026-06-21）
  - `PATCH_GAME_RUNTIME_MINIMAL_V08_ROADMAP.md` / `..._CHECKLIST.md`。**実装は未着手・ROM/Input/Timer/VRAM を組み合わせた v0.8 完了前の最小ゲーム runtime・新 runtime class を足さず既存 Run/Step に「demo 構成 + sample program（既存命令のみ）+ VRAM 表示 + `_refresh_run_panels` refresh」の薄い層・VRAM Viewer（32×32 framebuffer・グレースケール）を含める案 B が第一候補（UI 肥大化時は `PATCH_VRAM_VIEWER_V08` へ分離）・game16 layout（ROM 0x0000/RAM 0x8000/VRAM 0xC000/MMIO 0xE000）・CPU 命令/ASM 変更なし・VRAM 非配置は現行互換・v0.8 を閉じる方針なら命令拡張は後回し**
* [x] `PATCH_GAME_RUNTIME_MINIMAL_V08` 実装完了（2026-06-23・**VRAM Viewer を含めた案 B・CPU 命令/ASM 変更なし・新 runtime class なし・VRAM 非配置は現行互換**）
  - `ui/vram_viewer.py`（新規・`VramViewer(QDockWidget)`・32×32 グレースケール framebuffer・`update_from_vram`/`snapshot`/`pixel`/`is_active`・`dump()`/`pixel()` を読むだけで VRAM 不変）/ `ui/win.py`（`_setup_vram_viewer` で dock 生成・Memory Viewer とタブ化・`_update_vram_viewer` を `_refresh_run_panels`/`_do_reset`/`write_program`/初期化に追加・`_collect_run_status` に `game` キー）/ `ui/run_status.py`（`Game:` 行）
  - ROM + Input + Timer + VRAM を同時配置し ROM target から実行 → Input/Timer を `LD` で読み VRAM へ `ST`。MMIO 実番地はテストで実取得（`self._sim_input.base`/`self._sim_timer.base`）・game16 は 0xE000/0xE010/0xE020 を unit 検証。MainWin は circuit_compat 自動選択のため統合テストは circuit_compat + Address Map override 配置。`tests/test_game_runtime_minimal_v08.py`（18 件）・`tests/test/system.json` 差分なし。GUI 目視はヘッドレスのため未実施（表示は `snapshot()`/`pixel()` で検証）
  - `python -m pytest tests/` → **1182 passed**（1164 + 新規 18）
  - 次候補: `PATCH_V08_STABILIZE_AND_DOCS`（v0.8 安定化・ドキュメント・PHASE COMPLETE 準備）
* [x] `PATCH_V08_STABILIZE_AND_DOCS` 実施（2026-06-23・**v0.8 最終整理・コード変更なし**）
  - `PATCH_V08_STABILIZE_AND_DOCS_ROADMAP.md` / `..._CHECKLIST.md` 作成。`ROADMAP8.md` / `CHECKLIST8.md` / `HANDOFF.md` / `README.md` を v0.8 完了状態へ最小更新（既存履歴は保持・見出し重複なし）
  - v0.8（**Device Expansion & Connection Validation**）は `PATCH_PORT_SCHEMA_V08` 〜 `PATCH_GAME_RUNTIME_MINIMAL_V08` の 14 パッチで完了。安定化は document + 検証のみ（新機能/CPU命令/ASM/リファクタなし）
  - 最終検証: `python -m pytest tests/` → **1182 passed**・`tests/test/system.json` 差分なし・`# AKDev ROADMAP 8` 見出し 1 個。GUI 目視はヘッドレスのため未実施（ロジックは pytest 済み）
  - **v0.8 はこのパッチで完了**。`PHASE COMPLETE` 宣言・`old/` 収納・`ROADMAP9.md`/`CHECKLIST9.md` 作成はユーザー宣言後。v0.9 候補は `ROADMAP8.md` の「v0.9 以降へ送る候補」参照
* [x] 次候補 `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08` の設計資料を作成した（2026-06-18）
  - `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08_ROADMAP.md` / `..._CHECKLIST.md`。**実装は未着手・ROM/Input 優先（Input は LD で読め IN 命令不要）・VRAM/Storage は後続・新 device 無しは現行互換・分割案（INPUT 先行 → ROM）あり**
* [x] v0.8 テーマを確定した（**Device Expansion & Connection Validation**・2026-06-17 確定・14 パッチで実装完了）
* [x] 最初のパッチ `PATCH_PORT_SCHEMA_V08` 以降の実装をユーザー承認のもと進めた（v0.8 全パッチ完了）
* [x] 各パッチの `PATCH_*_V08_ROADMAP.md` / `..._CHECKLIST.md` を着手前に作成した（CLAUDE.md §3 準拠）

---

# 1. v0.8 作業候補（実施結果・2026-06-23 時点）

> v0.8 完了時点の取捨選択結果。詳細は上記パッチ履歴と `ROADMAP8.md` を参照。

* [x] A. Port direction / width validation（`PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08`・warning only）
* [x] B. Bus protocol validation（`PATCH_BUS_PROTOCOL_VALIDATION_V08`・warning only）
* [x] C. 複数 RAM / UART handling（`PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08`・複数 RAM 真の共存は v0.9 候補 F）
* [x] D. ROM / VRAM / Storage / Input device expansion（Input/ROM/Timer/VRAM 実装。Storage は v0.9 へ）
* [x] E. Address Map Editor（`PATCH_ADDRESS_MAP_EDITOR_V08`）
* [x] F. コード領域拡張 / MMIO 窓の再配置・可変化（`PATCH_CODE_REGION_MMIO_RELOCATION_V08`・MemoryLayout）
* [~] G. CPU 命令拡張: Bitwise（`AND/OR/XOR/NOT`）実装。**branch 拡張 / shift / CALL・RET・stack は v0.9 へ**
* [x] H. ゲーム runtime 準備（`PATCH_GAME_RUNTIME_MINIMAL_V08` + 32×32 VRAM Viewer。本格ゲームループは v0.9 へ）
* [ ] I. HDL / FPGA export 準備 → **v0.9 へ送る**

---

# 2. 繰越課題（v0.6 → v0.7 → v0.8 → v0.9）

* [ ] `tests/test/system.json` のテスト実行差分の扱いをユーザーが決定する → **v0.9 へ繰越**
  - 完了条件: 破棄 / コミット / .gitignore 化 のいずれかをユーザーが選ぶ（勝手に破棄しない）

---

# 3. v0.8 完了状態（2026-06-23）

* v0.8（**Device Expansion & Connection Validation**）は 14 パッチで実装完了し、`PATCH_V08_STABILIZE_AND_DOCS` で最終整理した。
* 最終テスト: `python -m pytest tests/` → **1182 passed**・`tests/test/system.json` 差分なし・見出し重複なし。
* commit / push は**未実施**（ユーザー操作）。`PHASE COMPLETE` 宣言後に `old/` 収納・`ROADMAP9.md`/`CHECKLIST9.md` 作成を行う（CLAUDE.md §4）。
* v0.9 へ送る候補は `ROADMAP8.md` の「v0.9 以降へ送る候補」を参照。
* GUI 目視はヘッドレス環境のため未実施（表示ロジックは pytest で検証済み）。
