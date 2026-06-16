# PATCH_CPU_RAM_VALIDATION_V07 — ROADMAP

> v0.7（Plan-driven Virtual Devices & Address Map）3 番目のパッチ。
> 親計画: `ROADMAP7.md` / 進捗: `PATCH_CPU_RAM_VALIDATION_V07_CHECKLIST.md`。
> 前提: `PATCH_PLAN_DRIVEN_DEVICES_V07`（plan 由来デバイス・64KB RAM）/
> `PATCH_ADDRESS_MAP_V07`（Address Map）完了。

---

## 目的

Canvas 上で接続された CPU/RAM/UART 構成に対して、**CPU が接続 RAM へ LD/ST で
正しく読み書きできること**を検証する。Address Map の RAM 領域（UART MMIO 窓を避けた領域）
へ実際に CPU アクセスが通ることを、selftest ASM と pytest で確認する。

## 現在の到達点

- Canvas 接続 → CircuitPlan → 実行 RAM/UART 生成（64KB RAM・UART MMIO 窓 0x0100–0x0107）。
- Address Map で RAM/UART の base/size/range を管理、unintended overlap 検出、summary を Log 出力。
- ただし **CPU の LD/ST が接続 RAM へ実際に届くかの検証が弱い**（Hello World は OUT→UART のみ）。

## 今回検証すること

- `ST` で接続 RAM へ書き込める。
- `LD` で同じ値を読み戻せる。
- 書き込み先が UART MMIO 窓ではなく RAM 領域である（Address Map と整合）。
- pytest から RAM 内容（memory_snapshot）を直接確認できる。
- Step Trace に memory write/read が現れる。
- Canvas 由来 runtime 上で RAM selftest と Fibonacci が成立する。

## CPU/RAM validation の設計

- **新規ロジックは追加しない**。既存の Write Program → Run（plan 由来 runtime）を使い、
  検証用 ASM を流して結果を RAM / UART / Step Trace で確認する。
- 検証は pytest 主体。selftest ASM は UART に PASS/FAIL を出し、pytest は RAM 値・UART 出力・
  trace_history を直接確認する。

## 使用する ASM の方針

- `tests/test/ram_selftest.asm`（新規）:
  - UART base `0x0100`（既存 hello と同方式の OUT）。
  - RAM テストアドレス `0x0200`（UART 窓 0x0100–0x0107 を避ける／コード領域 0x0000–0x005F の外）。
  - 既知値 `0xABCD` を `ST` で書き、`LD` で読み戻し、`BEQ` で一致判定。
  - 一致なら UART に `PASS`、不一致なら `FAIL` を出力して `HALT`。
  - コードは 0x0100 未満（24 命令 = 0x60 bytes）に収め、UART 窓と衝突させない。
- Fibonacci: 既存 `src/fib.asm` を Canvas 由来 runtime 上で実行（RAM 0x0040–0x005C に fib[0..7]）。
  これは UART 窓・コード領域いずれとも衝突しないため、そのまま再利用する。

## テスト方針（`tests/test_cpu_ram_validation_v07.py` 新規）

- 正しい CPU+RAM+UART 回路で ram_selftest.asm を Write→Run できる。
- UART に `PASS` が出る。
- RAM の 0x0200 に期待値 0xABCD が書かれている（memory_snapshot 直接確認）。
- LD 読み戻し値が正しい（PASS 出力 = 一致が取れた証拠／trace でも確認）。
- Step Trace（trace_history）に 0x0200 への memory write と read が現れる。
- selftest アドレス 0x0200 が Address Map の RAM 領域内、かつ UART MMIO 窓外。
- UART 窓 0x0100–0x0107 は従来どおり UART として機能する（PASS 出力で実証）。
- Fibonacci を Canvas 由来 runtime で実行し RAM の fib 値を確認。
- legacy mode の Build→Run（hello.asm "Hi"）が従来どおり。
- 既存 Plan-driven / Address Map / Step Trace テストが壊れない。

## 今回やらないこと

Target CPU Selection / Run Status Panel / Port Detail / Address Map Editor /
複数 RAM・UART 本格対応 / 複数 CPU 同時実行 / VRAM・Storage・Input・Display /
MMU / 割り込み / C コンパイラ / HDL 合成 / FPGA 実機書き込み / ゲーム実行 / commit / push。

## 既存互換性の注意点

- runtime / win のロジック変更は行わない（検証用 ASM とテストの追加が中心）。
- circuit mode のコードは 0x0000–0x00FF 内（UART 窓のため）。selftest は 24 命令で収まる。
- legacy mode（RAM 256B / UART 0x0100 / "Hi" / 既存テスト）は不変。
