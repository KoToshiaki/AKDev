# PATCH_CPU_RAM_VALIDATION_V07 — CHECKLIST

> 設計: `PATCH_CPU_RAM_VALIDATION_V07_ROADMAP.md` / 親: `ROADMAP7.md` / `CHECKLIST7.md` §4。

---

## 0. 事前確認

* [x] 作業ツリー状態を確認（ADDRESS_MAP_V07 未コミット差分あり / ユーザー承認の上で続行）
* [x] `python -m pytest tests/` 現状確認（804 passed）
* [x] AK32 ASM 構文（LDI/ST/LD/BEQ/OUT/JMP/HALT）とアドレス制約を確認

## 1. 設計

* [x] selftest ASM のアドレス方針（RAM 0x0200・UART 0x0100・コード <0x0100）を確定
* [x] PASS/FAIL 出力・BEQ 一致判定の構成を確定
* [x] Fibonacci は既存 src/fib.asm を再利用する方針を確定
* [x] ROADMAP / CHECKLIST を作成（本ファイル）

## 2. 実装（ASM 追加・ロジック変更なし）

* [x] `tests/test/ram_selftest.asm` を新規作成（ST→LD→BEQ→PASS/FAIL）
* [x] selftest が UART 窓 0x0100–0x0107 を書き込み先にしない（テストアドレス 0x0200）
* [x] selftest コードが 0x0100 未満に収まる（96 bytes・0x00–0x5F）

## 3. テスト（`tests/test_cpu_ram_validation_v07.py` 新規・7 件）

* [x] 正しい CPU+RAM+UART 回路で ram_selftest.asm を Write→Run できる
* [x] UART に `PASS` が出る（FAIL は出ない）
* [x] RAM 0x0200 に期待値 0xABCD が書かれている（memory_snapshot 直接確認）
* [x] LD 読み戻しが正しい（PASS 出力／trace で確認）
* [x] Step Trace に 0x0200 への memory write と read が現れる
* [x] selftest アドレス 0x0200 が Address Map の RAM 領域内
* [x] selftest アドレス 0x0200 が UART MMIO 窓外
* [x] UART 窓 0x0100–0x0107 は従来どおり UART として機能（Z 出力・RAM 未変更で実証）
* [x] Fibonacci（src/fib.asm）を Canvas 由来 runtime で実行し RAM の fib 値 [0,1,1,2,3,5,8,13] を確認
* [x] legacy mode Build→Run（"Hi"）が従来どおり

## 4. 検証

* [x] `python -m pytest tests/` 全件通過（804 + 7 = **811 passed**）
* [x] 既存互換（Plan-driven / Address Map / Step Trace / Hello World / Wiring / Save-Load）
* [x] 変更ドキュメントを読み返す

## 5. 報告

* [x] 実装内容・追加 ASM 概要・検証アドレス・UART 出力例・テスト結果・残課題・次パッチ案を報告して停止
