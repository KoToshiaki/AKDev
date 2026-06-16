# PATCH_PLAN_DRIVEN_DEVICES_V07 — CHECKLIST

> 設計: `PATCH_PLAN_DRIVEN_DEVICES_V07_ROADMAP.md` / 親: `ROADMAP7.md` / `CHECKLIST7.md` §2。

---

## 0. 事前確認

* [x] 作業ツリーが安全（clean・v0.6 PHASE COMPLETE はコミット済み `2fdcd7f`）
* [x] `python -m pytest tests/` の現状を確認（779 passed）
* [x] アドレス空間制約（imm16 / load base 0 / UART 0x0100）を確認し設計に反映

## 1. 設計

* [x] circuit mode の RAM/UART/CPU を plan ノードから生成する方針を確定
* [x] RAM 64KB + UART MMIO ウィンドウ（0x0100–0x0107）の構成を確定
* [x] legacy mode は従来挙動を維持する方針を確定
* [x] ROADMAP / CHECKLIST を作成（本ファイル）

## 2. 実装

* [x] `_CIRCUIT_RAM_SIZE`（64KB）定数を追加
* [x] `_make_sim(plan)` を circuit/legacy 分岐にする
* [x] circuit build: 64KB RAM を 2 レンジ attach + UART を MMIO ウィンドウに attach
* [x] plan ノード id を `_sim_ram_node` / `_sim_uart_node` / `_sim_cpu_node` に保持
* [x] legacy build は従来コードのまま（256B RAM / UART 0x0100）
* [x] device id（sim_ram/sim_uart/sim_cpu）は不変に保つ

## 3. テスト

* [x] `tests/test_plan_driven_devices_v07.py` を新規作成（12 件）
* [x] plan 由来 RAM/UART が runtime の実行デバイス（`runtime.ram/uart/cpu is win._sim_*`）
* [x] circuit mode RAM サイズ拡張（>= 0x10000）
* [x] Write Program が接続 RAM へロード
* [x] Run で接続 UART へ Hello World
* [x] 拡張 RAM 高位アドレス（0x2000）へ read/write、UART ウィンドウ 0x0100 維持
* [x] legacy Build→Run 従来どおり（UART "Hi" / RAM 256B / 高位アドレス拒否）
* [x] 未接続ブロック維持
* [x] Step Trace 維持

## 4. 検証

* [x] `python -m pytest tests/` 全件通過（779 + 12 = **791 passed**）
* [x] 既存互換（legacy / Hello World / Step Trace / Program-Sources / Wiring / Save-Load）を確認
* [x] 変更ドキュメントを読み返す

## 5. 報告

* [x] 実装内容・変更/作成ファイル・テスト結果・残課題・次パッチ案を報告して停止
