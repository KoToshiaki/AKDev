# PATCH_INPUT_DEVICE_V08 — CHECKLIST（設計資料）

> 設計詳細は `PATCH_INPUT_DEVICE_V08_ROADMAP.md` を参照。
> 本書は**実装時に使うチェックリスト**。現時点では実装未着手（設計資料のみ）。
> コード変更・テスト追加・part.json 追加・commit/push は本タスクでは行わない。

---

## 0. 事前確認

* [ ] `git status --short` がクリーンであることを確認
* [ ] `python -m pytest tests/` が全通過（着手時ベースライン取得）
* [ ] `ROADMAP8.md` の見出し重複が無い（`# AKDev ROADMAP 8` / `## v0.8 作業候補` 各 1 回）
* [ ] `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08`（設計）が完了・コミット済み
* [ ] `PATCH_ADDRESS_MAP_EDITOR_V08` / 以前の v08 パッチが完了・コミット済み
* [ ] `core/devices.py` の `device_kind`/`_KIND_BY_PART_ID`/`_ROLE_BY_KIND`/`_RUNTIME_BACKED`/`_RUNTIME_ID`/`make_device_spec`/`assign_mmio_bases` を確認
* [ ] `assign_mmio_bases` の「最初の MMIO のみ runtime-backed」ロジック（kind 単位へ要調整）を確認
* [ ] `core/dev.py` の `RamPart`/`UartPart`（read/write/reset）を確認
* [ ] `core/cpu.py` の `LD`（=bus.read）で MMIO read 可・`IN` 命令が無いことを確認
* [ ] `core/circuit.py:resolve_circuit`（cpu/ram/uart 収集）/ `ui/win.py:_auto_device_specs`/`_build_runtime_devices` を確認
* [ ] part library に `io.input` が無いことを確認・Address Map Editor / MemoryLayout を確認

## 1. 設計

* [ ] Input device 仕様確定（kind=input / role=mmio / addressable / runtime_backed / runtime_id sim_input / size 8B）
* [ ] MMIO register 仕様確定（KEY_STATE +0x00 read / EDGE_STATE +0x04 read / CLEAR_EDGE +0x04 write / bit 割当）
* [ ] CPU/ASM 方針確定（`IN` 不要・`LD` で読む・assembler 拡張なし・既存 asm 不変）
* [ ] part.json 方針確定（`parts/io/input/part.json`・v2・ports bus/keys/clk/reset）
* [ ] device registry 方針確定（kind/role/addressable/runtime_backed/runtime_id/label マップ + `assign_mmio_bases` kind 単位 backing）
* [ ] resolve_circuit 方針確定（`plan["devices"]` 追加・既存キー互換・wired addressable 収集・1 個目のみ runtime 化）
* [ ] runtime 方針確定（`InputPart` read/write/reset/set_keys/get_keys/clear_edge・bus trace）
* [ ] UI/Debug 方針確定（最小は set_keys + test・目視用に簡易仮想ボタン・keyboard は次段）
* [ ] Address Map / Editor 方針確定（MMIO 窓・override 可・Input 非配置は現行一致）

## 2. 実装予定（今回は未実装）

* [ ] `parts/io/input/part.json` 追加（v2 schema）
* [ ] `core/devices.py` device maps 更新（input→mmio/addressable/runtime_backed/sim_input/INPUT）
* [ ] `core/devices.py` `assign_mmio_bases` を kind 単位 runtime-backing へ調整（UART+Input 両 backed）
* [ ] `core/dev.py` に `InputPart` 追加
* [ ] `core/circuit.py:resolve_circuit` に addressable device 収集（`plan["devices"]` / 任意 `plan["inputs"]`・互換維持）
* [ ] `ui/win.py:_auto_device_specs` が Input も spec 化
* [ ] `ui/win.py:_build_runtime_devices` が 1 個目 Input を runtime 化（parts_by_id に sim_input）
* [ ] `ui/win.py` に `self._sim_input` / `self._sim_input_node` 追加
* [ ] Address Map 表示（Input が載る）/ Address Map Editor override 確認
* [ ] （任意）Debug の簡易 Input パネル / 仮想ボタン
* [ ] tests 追加

## 3. テスト予定（今回は未追加）

* [ ] `io.input` が library に出る
* [ ] `device_kind("io.input") == "input"` / `device_role("input") == "mmio"`
* [ ] input が addressable / runtime_backed・runtime_id sim_input
* [ ] `make_device_spec()` が Input spec を作る
* [ ] Input が Address Map に載る・UART+Input で UART 0x0100 / Input 0x0110・両方 runtime_backed
* [ ] Address Map Editor で Input base/size override
* [ ] `InputPart.set_keys()` / `read()`（KEY_STATE）が動く・reset で 0
* [ ] CPU が `LD` で Input を読める（`LDI base; LD r,[base]`）
* [ ] Input 無し構成は既存 Address Map dict 完全一致
* [ ] Hello World / ram_selftest / legacy が壊れない

## 4. 検証予定

* [ ] `python -m pytest tests/` が全件通過
* [ ] GUI 目視: Input を置く・Address Map に出る・仮想ボタン押下で CPU が読む値が変わる
* [ ] Input 配置時の Address Map 表示（Run Status summary）
* [ ] 既存 project（system.json）round-trip 不変（Input 無し）

## 5. 完了条件

* [ ] Input device 方針が明確（kind/role/runtime/レジスタ）
* [ ] 既存命令 `LD` で読める設計（`IN` 命令不要）が明確
* [ ] 既存互換を維持できる（Input 非配置で現行完全一致）方針が明確
* [ ] `assign_mmio_bases` の kind 単位 runtime-backing 調整方針が固まっている
* [ ] 次の Input 実装（および `PATCH_ROM_DEVICE_V08`）へ進める
