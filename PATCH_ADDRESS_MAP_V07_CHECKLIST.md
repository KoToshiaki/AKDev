# PATCH_ADDRESS_MAP_V07 — CHECKLIST

> 設計: `PATCH_ADDRESS_MAP_V07_ROADMAP.md` / 親: `ROADMAP7.md` / `CHECKLIST7.md` §3。

---

## 0. 事前確認

* [x] 作業ツリーが安全（clean・`PATCH_PLAN_DRIVEN_DEVICES_V07` は `6885a70` でコミット済み）
* [x] `python -m pytest tests/` の現状確認（791 passed）
* [x] 既存 `_make_sim` の circuit/legacy 構成とアドレス制約を確認

## 1. 設計

* [x] Address Map データ構造（案A: logical device + attach ranges）を確定
* [x] circuit/legacy の base/size/attach を整理
* [x] overlap 検出は attach ranges のみ・MMIO overlay は除外する方針を確定
* [x] ROADMAP / CHECKLIST を作成（本ファイル）

## 2. 実装

* [x] `core/circuit.py` に `build_address_map()` を追加
* [x] `core/circuit.py` に `validate_address_map()` を追加（unintended overlap 検出）
* [x] `core/circuit.py` に `format_address_map_summary()` を追加（Log 行）
* [x] `core/runtime.py` `VirtualCircuitRuntime` に `address_map` 属性（既定 None）を追加
* [x] `ui/win.py` `_make_sim` を Address Map 駆動にする（amap の attach_ranges どおりに bus attach）
* [x] `ui/win.py` `_runtime.address_map = amap` を保持・`win.address_map()` アクセサ追加
* [x] `_bind_circuit_runtime` で summary + 検証 issue を Log 出力（`_log_address_map`）
* [x] circuit mode の Run 開始時に summary を Log 出力（legacy は出さない）
* [x] `self._address_map`（asm 行マップ）と名前衝突しないことを確認（runtime 側に保持）

## 3. テスト（`tests/test_address_map_v07.py` 新規・13 件）

* [x] circuit mode で Address Map が作られる
* [x] RAM の base/size/end が正しい（0x0000 / 0x10000 / 0xFFFF）
* [x] UART の base/size/end が正しい（0x0100 / 8 / 0x0107）
* [x] UART が 0x0100–0x0107 に残っている
* [x] 既定 RAM+UART 構成が valid（issue 空）
* [x] unintended overlap を検出できる（単体）
* [x] Write Program 後に `win._runtime.address_map` を参照できる
* [x] Run 後も Address Map が維持される
* [x] legacy mode の Address Map（RAM 256B / overlay なし）
* [x] bus attach が Address Map と一致（高位 read/write・UART 窓）
* [x] Write 時 Log に Address Map summary が出る

## 4. 検証

* [x] `python -m pytest tests/` 全件通過（791 + 13 = **804 passed**）
* [x] 既存互換（Plan-driven Devices / legacy / Hello World / Step Trace / Wiring / Save-Load）
* [x] 変更ドキュメントを読み返す

## 5. 報告

* [x] 実装内容・変更/作成ファイル・Log 例・テスト結果・残課題・次パッチ案を報告して停止
