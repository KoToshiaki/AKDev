# PATCH_TIMER_DEVICE_V08 — CHECKLIST（設計資料）

> 設計詳細は `PATCH_TIMER_DEVICE_V08_ROADMAP.md` を参照。
> 本書は**実装時に使うチェックリスト**。**実装完了（2026-06-20・`python -m pytest tests/` 1136 passed）**。
> Timer は **MMIO device**（CPU 命令追加なし・既存 `LD`/`ST`）。tick は **deterministic（CPU step 数ベース）**。割り込みなし。commit/push は未実施。

---

## 0. 事前確認

* [x] `git status --short` がクリーン
* [x] `python -m pytest tests/` が全通過（着手時ベースライン **1111 passed**）
* [x] `dev` ブランチである
* [x] `ROADMAP8.md` の見出し重複が無い（`# AKDev ROADMAP 8` / `## v0.8 作業候補` 各 1 回）
* [x] `PATCH_AK32_BITWISE_INSTRUCTIONS_V08` が完了・コミット済み（`3950180`）
* [x] `PATCH_AK32_INSTRUCTION_EXPANSION_V08`（`6a74d36`）/ `PATCH_PROGRAM_TARGET_ROM_V08`（`baf5fe3`）/ `PATCH_ROM_DEVICE_V08`（`fcfa19f`）/ `PATCH_INPUT_DEVICE_V08`（`18a58b3`）/ 以前の v0.8 がコミット済み
* [x] `tests/test/system.json` に差分が無い
* [x] Input / ROM / device registry を確認（`core/devices.py` — `_KIND_BY_PART_ID["io.timer"]="timer"` / `_ROLE_BY_KIND["timer"]="mmio"` / `_LABEL_BY_KIND["timer"]="TIMER"` は**既存**。`_RUNTIME_BACKED` / `_RUNTIME_ID` は timer 未対応）
* [x] runtime step/cycle を確認（`runtime.step()` で `step_count += 1`・`MainWin._do_step/_do_run` が `self._sim_cycle = self._runtime.step_count`）
* [x] Address Map / MMIO 配置を確認（`assign_mmio_bases`：window=`layout.mmio_size`=**0x08**・stride 0x10・UART 0x0100 / Input 0x0110 / Timer 0x0120）

## 1. 設計

* [x] Timer 仕様（part_id `io.timer` / kind `timer` / role `mmio` / runtime_id `sim_timer` / addressable / runtime_backed）
* [x] MMIO register 仕様（**最小案・0x08 窓**：`0x00 TICK`（read=tick / write=clear）・`0x04 DELTA`（read=経過 / write=clear）。4 レジスタ案は mmio_size 拡張要で後続）
* [x] tick 単位（CPU step 数＝`runtime.step_count` と同進み・wall-clock 不使用・deterministic）
* [x] runtime 統合方針（`runtime.step()` の step_count++ 後に `timer.tick()`・`runtime.reset()` / load で timer reset・未配置は None で互換）
* [x] device registry 方針（`_RUNTIME_BACKED` に timer / `_RUNTIME_ID["timer"]="sim_timer"`・base/size は `assign_mmio_bases` 任せ・複数 Timer は 1 個目のみ runtime-backed）
* [x] part.json 方針（`parts/io/timer/part.json`・v2・ports bus/clk/reset・io.input/io.uart と同形）
* [x] resolve_circuit 方針（`plan["timers"]` 追加・既存キー互換・Timer は必須にしない）
* [x] UI / Run Status 方針（Address Map 表示・Editor override・可能なら `Timer: tick=...`・UI 大改造なし）
* [x] CPU / ASM 方針（命令追加なし・既存 `LD` で read・既存 `ST` で clear・`IN` 不要）
* [x] テスト方針（part/registry/Address Map/TimerPart/runtime step/LD・ST 統合/既存互換）
* [x] 既存互換方針（Timer 非配置は dict 一致・既存命令/ASM 不変・system.json 差分なし）

## 2. 実装（`core/devices.py` / `core/dev.py` / `core/circuit.py` / `core/runtime.py` / `ui/win.py` / `ui/run_status.py`）

* [x] part.json（`parts/io/timer/part.json`・v2・bus/clk/reset+任意 irq）は**既存**を確認・変更なし（必要 port を満たす）
* [x] device registry 追加（`core/devices.py` `_RUNTIME_BACKED` に `timer` / `_RUNTIME_ID["timer"]="sim_timer"`。kind/role/label は既存）
* [x] TimerPart 追加（`core/dev.py` — `tick()` / `reset()` / `read()` TICK(0x00)・DELTA(0x04) / `write()` clear・32bit mask・範囲外 read=0）
* [x] resolve_circuit timers 追加（`core/circuit.py` `_is_timer` + `plan["timers"]`・早期 return にも timers:[]・devices は既収集）
* [x] runtime 生成（`ui/win.py` `_auto_device_specs` で timers を spec 化（UART/Input の後）/ `_build_runtime_devices` で 1 個目 Timer を runtime 化・`self._sim_timer` / `_sim_timer_node`・parts_by_id に sim_timer）
* [x] timer tick 更新（`core/runtime.py` `VirtualCircuitRuntime(timer=None)` 保持・`step()` の step_count++ 後に `timer.tick()`）
* [x] reset/load 統合（`runtime.reset()` / `load_program()` で timer reset・program load 時 tick=0）
* [x] Run Status 表示（`ui/run_status.py` に `Timer: tick=.. delta=.. @0x..` / 未配置は `Timer: None`・`_collect_run_status` で timer dict）
* [x] tests 追加（`tests/test_timer_device_v08.py` — 25 件）
* [x] checklist 更新（本 CHECKLIST・`CHECKLIST8.md` / `ROADMAP8.md` 最小追記）

## 3. テスト（`tests/test_timer_device_v08.py` — 25 件）

* [x] part/library（`io.timer` が出る・v2・bus/clk/reset port）
* [x] device registry（kind=timer・role=mmio・addressable・runtime_backed・runtime_id sim_timer・make_device_spec）
* [x] Address Map（`assign_mmio_bases` で UART 0x0100 / Input 0x0110 / Timer 0x0120・size 0x08・MainWin で配置・Timer 無しは uart 0x0100 維持・timer 不在）
* [x] resolve_circuit（timers 収集・未接続は非収集・Timer 無しは ok 不変）
* [x] TimerPart unit（初期 0・tick +1・TICK/DELTA read・clear TICK / clear DELTA・reset・32bit wrap・範囲外 read=0）
* [x] runtime step（`step()` N 回で TICK==N・reload で 0）
* [x] CPU LD/ST integration（`LD [0x0120]` で tick 読取（=1）・`ST [0x0120]` で clear（r2=5→r3=1））
* [x] Run Status（未配置 `Timer: None` / 配置時 `Timer: tick=..`・MainWin render）
* [x] existing tests（Hello World / legacy は Timer 無し・`disasm` 不変・Input/ROM/Program Target/Bitwise 不変）

## 4. 検証

* [x] `python -m pytest tests/` 全件通過 — **1136 passed**（1111 + 25）
* [x] Timer read sample（`LD [0x0120]` で tick 取得・テストで実証）
* [x] Step/Run で tick 増加（`step()` 数に一致・テストで実証）
* [x] reset/clear 確認（reset/reload で 0・`ST` clear で減る・テストで実証）
* [x] `tests/test/system.json` に差分なし
* [ ] GUI 目視（Run Status の Timer 行。ヘッドレスのため未実施）

## 5. 完了条件

* [x] Timer device 仕様が明確・実装済み（part/kind/role/runtime/MMIO）
* [x] MMIO register 仕様が明確・実装済み（0x08 窓・TICK / DELTA・read=値 / write=clear）
* [x] deterministic tick（CPU step 数・wall-clock 不使用）— `runtime.step()` で 1 tick・テスト実証
* [x] 既存互換が守れる（Timer 非配置は現行一致・CPU 命令/ASM 不変・system.json 差分なし・1136 passed）
* [x] CPU から `LD` で読み・`ST` で clear できる（テスト実証）
* [x] 次（`PATCH_VRAM_DEVICE_V08` / `PATCH_GAME_RUNTIME_MINIMAL_V08`）へ進める
