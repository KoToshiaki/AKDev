# PATCH_INPUT_DEVICE_V08 — CHECKLIST（設計資料）

> 設計詳細は `PATCH_INPUT_DEVICE_V08_ROADMAP.md` を参照。
> 本書は**実装時に使うチェックリスト**。現時点では実装未着手（設計資料のみ）。
> コード変更・テスト追加・part.json 追加・commit/push は本タスクでは行わない。

---

## 0. 事前確認

* [x] `git status --short` がクリーンであることを確認
* [x] `python -m pytest tests/` が全通過（着手時ベースライン **1011 passed**）
* [x] `ROADMAP8.md` の見出し重複が無い（各 1 回・再発なし）
* [x] `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08`（設計）が完了・コミット済み（`260fba4` 等）
* [x] `PATCH_ADDRESS_MAP_EDITOR_V08` / 以前の v08 パッチが完了・コミット済み
* [x] `core/devices.py` の device maps / `make_device_spec` / `assign_mmio_bases` を確認
* [x] `assign_mmio_bases` の「最初の MMIO のみ runtime-backed」（kind 単位へ調整）を確認
* [x] `core/dev.py` の `RamPart`/`UartPart`（read/write/reset）を確認
* [x] `core/cpu.py` の `LD`（=bus.read）で MMIO read 可・`IN` 命令が無いことを確認
* [x] `core/circuit.py:resolve_circuit` / `ui/win.py:_auto_device_specs`/`_build_runtime_devices` を確認
* [x] part library に `io.input` が無いことを確認・Address Map Editor / MemoryLayout を確認

## 1. 設計

* [x] Input device 仕様確定（kind=input / role=mmio / addressable / runtime_backed / runtime_id sim_input / size 8B）
* [x] MMIO register 仕様確定（KEY_STATE +0x00 read / EDGE_STATE +0x04 read / CLEAR_EDGE +0x04 write / bit 割当）
* [x] CPU/ASM 方針確定（`IN` 不要・`LD` で読む・assembler 拡張なし・既存 asm 不変）
* [x] part.json 方針確定（`parts/io/input/part.json`・v2・ports bus/keys/clk/reset）
* [x] device registry 方針確定（maps + `assign_mmio_bases` kind 単位 backing）
* [x] resolve_circuit 方針確定（`plan["devices"]` + `plan["inputs"]` 追加・既存キー互換・1 個目のみ runtime 化）
* [x] runtime 方針確定（`InputPart` read/write/reset/set_keys/get_keys/clear_edge・bus trace）
* [x] UI/Debug 方針確定（`set_input_keys` + test 中心・GUI 仮想ボタンは次段）
* [x] Address Map / Editor 方針確定（MMIO 窓・override 可・Input 非配置は現行一致）

## 2. 実装

* [x] `parts/io/input/part.json` 追加（v2 schema）
* [x] `core/devices.py` device maps 更新（input→mmio/addressable/runtime_backed/sim_input/INPUT）
* [x] `core/devices.py` `assign_mmio_bases` を **kind 単位 runtime-backing** へ調整（UART+Input 両 backed・複数 UART は従来どおり）
* [x] `core/dev.py` に `InputPart` 追加（KEY_STATE/EDGE_STATE/CLEAR_EDGE/set_keys/get_keys/clear_edge/reset）
* [x] `core/circuit.py:resolve_circuit` に `plan["inputs"]` / `plan["devices"]`（addressable 収集）追加（互換維持）
* [x] `ui/win.py:_auto_device_specs` が Input も spec 化
* [x] `ui/win.py:_build_runtime_devices` が 1 個目 Input を runtime 化（parts_by_id に sim_input）
* [x] `ui/win.py` に `self._sim_input` / `self._sim_input_node` + `set_input_keys()` API
* [x] Address Map 表示（Input が載る）/ Address Map Editor override 対応（既存ロジックで動作）
* [ ] Debug の簡易 Input パネル / 仮想ボタン（次段・本パッチは set_input_keys + test）
* [x] tests 追加

## 3. テスト（`tests/test_input_device_v08.py` — 23 件）

* [x] `io.input` が library に出る（v2 schema 正規化）
* [x] `device_kind("io.input") == "input"` / `device_role("input") == "mmio"` / addressable・runtime_backed・sim_input
* [x] `make_device_spec()` が Input spec を作る
* [x] `assign_mmio_bases`: 単一 UART 不変 / 複数 UART 1 個目のみ / UART+Input 両 backed / input-uart 順 / 複数 Input
* [x] `InputPart`: set_keys/read KEY_STATE・8bit mask・EDGE/CLEAR・reset・unknown offset
* [x] `resolve_circuit`: Input 収集 / Input 無し不変 / 未接続 Input 非収集
* [x] MainWin: Input runtime 構築・Address Map（UART 0x0100/Input 0x0110）・Editor 表示・base override
* [x] **CPU が `LD` で Input を読める**（set_input_keys(0x10) → `LD [0x0110]` → r2==0x10）
* [x] Input 無し構成は既存 Address Map dict 一致・Hello World / ram_selftest / legacy 不変

## 4. 検証

* [x] `python -m pytest tests/` 全件通過 — **1034 passed**（1011 + 23）
* [ ] GUI 目視: Input 配置・Address Map 表示・仮想ボタンで CPU が読む値変化（ヘッドレスのため未実施）
* [x] 既存 project（system.json）round-trip 不変（Input 無し・既存テスト通過）

## 5. 完了条件

* [x] Input device 方針が明確（kind/role/runtime/レジスタ）
* [x] 既存命令 `LD` で読める設計（`IN` 命令不要）が実装・テストで実証
* [x] 既存互換を維持（Input 非配置で現行完全一致・dict 一致・Hello World/selftest/legacy）
* [x] `assign_mmio_bases` の kind 単位 runtime-backing 調整が完了（複数 UART は従来どおり）
* [x] 次の `PATCH_ROM_DEVICE_V08` へ進める土台ができている
