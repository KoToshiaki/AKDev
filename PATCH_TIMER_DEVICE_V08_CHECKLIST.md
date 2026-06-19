# PATCH_TIMER_DEVICE_V08 — CHECKLIST（設計資料）

> 設計詳細は `PATCH_TIMER_DEVICE_V08_ROADMAP.md` を参照。
> 本書は**実装時に使うチェックリスト**。現状は **設計のみ完了・実装は未着手**。
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

## 2. 実装予定（今回は未実装）

* [ ] part.json 追加（`parts/io/timer/part.json`・v2）
* [ ] device registry 追加（`core/devices.py` `_RUNTIME_BACKED` に timer / `_RUNTIME_ID["timer"]="sim_timer"`）
* [ ] TimerPart 追加（`core/dev.py` — `tick()` / `reset()` / `read()` TICK・DELTA / `write()` clear・32bit mask）
* [ ] resolve_circuit timers 追加（`core/circuit.py` `plan["timers"]`・devices は既収集）
* [ ] runtime 生成（`ui/win.py` `_auto_device_specs` / `_build_runtime_devices` で 1 個目 Timer を runtime 化・`self._sim_timer` / `_sim_timer_node`）
* [ ] timer tick 更新（`core/runtime.py` `VirtualCircuitRuntime` に timer 保持・`step()` の step_count++ 後に `timer.tick()`）
* [ ] reset/load 統合（`runtime.reset()` で timer reset・program load 時 tick=0）
* [ ] Run Status 表示（`ui/run_status.py` 可能なら `Timer: tick=...`）
* [ ] tests 追加（`tests/test_timer_device_v08.py`）
* [ ] checklist 更新（本 CHECKLIST・`CHECKLIST8.md` / `ROADMAP8.md` 最小追記）

## 3. テスト予定

* [ ] part/library（`io.timer` が出る・v2 正規化）
* [ ] device registry（kind=timer・role=mmio・addressable・runtime_backed・runtime_id sim_timer）
* [ ] Address Map（Timer が載る・UART+Input+Timer で 0x0100/0x0110/0x0120・Timer 無しは dict 一致）
* [ ] TimerPart unit（read TICK/DELTA・write clear・reset・tick +1・32bit mask）
* [ ] runtime step（`step()` N 回で TICK==N・reset/load で 0）
* [ ] CPU LD/ST integration（`LD [0x0120]` で tick 読取・`ST [0x0120]` で clear）
* [ ] existing tests（Hello World / ram_selftest / Input / ROM / Program Target / Bitwise 不変）

## 4. 検証予定

* [ ] `python -m pytest tests/`（全通過・新規テスト込み）
* [ ] Timer read sample（`LD [0x0120]` で tick 取得）
* [ ] Step/Run で tick 増加（step 数に一致）
* [ ] reset/clear 確認（reset で 0・`ST` clear で減る）

## 5. 完了条件

* [x] Timer device 仕様が明確（part/kind/role/runtime/MMIO）
* [x] MMIO register 仕様が明確（0x08 窓・TICK / DELTA・read=値 / write=clear）
* [x] deterministic tick 方針が明確（CPU step 数・wall-clock 不使用）
* [x] 既存互換が守れる（Timer 非配置は現行一致・命令/ASM 不変）
* [x] 次の Timer 実装へ進める
