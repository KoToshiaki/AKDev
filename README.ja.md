# AKDev

**言語 / Language: [English](README.md) | 日本語**

AKDev は、自作の **AK32 CPU アーキテクチャ**を中心とした FPGA ゲーム機向けの統合開発・
シミュレーション環境です。Visual System Canvas に CPU / メモリ / I/O 部品を配置して回路に
配線し、**AK32 アセンブリ**を書いて、内蔵の仮想マシン上で Build / Run / Step できます。
CPU・RAM・UART・Input・ROM・Timer・VRAM はすべてソフトウェアでシミュレートされます。
最終的には自作 CPU 上で小さなゲームを起動・動作させることを目指し、HDL / FPGA export を
長期目標としています。

> **物理的には PC 上で動く Python プログラムです。** AKDev 内部に仮想 CPU / メモリ / デバイス
> の状態を持ち、AK32 命令を 1 つずつ実行します（Step = 1 命令、Run = Step の繰り返し）。
> 「Write Program」は仮想回路へのロードであり、**実機 FPGA への書き込みではありません**。

---

## 概要（Overview）

- **Visual System Canvas** — 部品（CPU / RAM / UART / Input / ROM / Timer / VRAM）の配置・配線。
- **AK32 アセンブリ** — 15 命令（`NOP HALT LDI OUT ADD SUB LD ST JMP BEQ ADDI AND OR XOR NOT`）。
- **仮想マシン** — Build / Write Program / Run / Step / Reset と、完全な命令トレース。
- **デバイス** — CPU に加え、書き込み可能 RAM、MMIO UART、MMIO Input、読み取り専用 ROM、
  決定論的 Timer、書き込み可能な 32×32 VRAM フレームバッファ。
- **メモリモデル** — 設定可能な `MemoryLayout`、overlap 検出付き Address Map、per-device の
  base/size override を行う Address Map Editor。
- **プログラムターゲット** — プログラムを RAM（既定）または ROM（ROM から fetch）へロード。
- **最小ゲーム runtime** — ROM + Input + Timer + VRAM を同時に動かし、小さな 32×32
  グレースケール VRAM Viewer で表示。
- **デバッグパネル** — レジスタ / メモリ hex dump / バストレース / UART コンソール / Run Status /
  Port Detail / Address Map Editor / VRAM Viewer / PC ハイライト / signal overlay。
- **プロジェクト** — Canvas レイアウト・ソース割り当て・プログラムターゲット・アドレス
  override の保存／再読み込み。

---

## 現在のバージョン状態（Current Status）

**v0.8 complete（2026-06-23）— Device Expansion & Connection Validation。**

- 14 個のパッチ（`PATCH_PORT_SCHEMA_V08` 〜 `PATCH_GAME_RUNTIME_MINIMAL_V08`）として実装し、
  `PATCH_V08_STABILIZE_AND_DOCS` で最終整理しました。
- `python -m pytest tests/` → **1182 passed**。21 件の warning は PySide6 の `Deprecation`
  通知のみで、テスト失敗はありません。
- `tests/test/system.json` に **差分なし**（テスト実行で追跡対象 fixture は変化しません）。
- 新デバイスを使わない既存プロジェクトは従来どおり。legacy mode（Canvas に CPU を置かない）も
  従来どおりです。
- **v0.9 の方針は意図的に未決定**です。現状の機能を確認したうえでユーザーが焦点を決めます
  （[v0.9 候補](#v09-候補planning-candidates)参照）。`PHASE COMPLETE`（計画を `old/` へ収納し
  v0.9 計画を作成する処理）は別のユーザー宣言ステップで、**まだ実施していません**。

---

## 機能一覧（Feature Overview）

| 分類 | 今できること |
|---|---|
| Visual Canvas | 部品の配置 / 選択 / 移動 / 配線、pan / zoom、パネルでの確認 |
| 接続検証 | port direction/width・bus master/slave のチェック（**warning only**・ブロックしない） |
| AK32 アセンブリ | `.asm` 編集、label 付きアセンブル、15 命令 |
| Build / Write | アセンブルして仮想回路（RAM または ROM）へロード |
| Run / Step / Reset | 命令ごとの完全トレース付きで実行 |
| デバイス | CPU, RAM, UART, Input, ROM, Timer, VRAM |
| Memory / Address Map | layout 由来の base/size、overlap 検出、per-device override |
| VRAM Viewer | 32×32 グレースケール表示・Step/Run/Reset 後に更新 |
| 最小ゲーム runtime | ROM + Input + Timer + VRAM（ROM 実行・入力/タイマ読み・VRAM 描画） |
| プロジェクト | Canvas + ソース + プログラムターゲット + address override の保存/読込 |
| テスト | `pytest tests/` → 1182 passed |

---

## Visual Canvas

Parts Library から部品を Canvas へドロップし、配線してシステムを組みます。

| 操作 | 動作 |
|---|---|
| 左ドラッグ | 部品の選択 / 移動 |
| wire を左クリック | wire を選択（Properties が Wire 表示に切替） |
| visual port から左ドラッグ | 別の部品への接続を開始 |
| Alt + visual port を左ドラッグ | port を辺に沿って移動（接続 wire が追従） |
| 右クリック | コンテキストメニュー（wire mode / ASM source 設定 / 削除 など） |
| 中ドラッグ | Canvas を pan |
| ホイール | ズーム |
| Delete | 選択中の wire を削除（無ければ選択ノードを削除） |

Canvas の詳細:

- **部品は初期状態でポートを固定しません**。2 つの部品を配線したときに接続点へ *visual port* を
  生成します（接続は visual port と logical port の両方を保持）。
- **wire** は visual port 間の曲線で描画され、ノードやポートの移動に追従します。fan-out
  （1 つのポートから複数 wire）に対応。
- **選択**が側面パネルを駆動します。ノード選択で **Properties** と **Port Detail**、wire 選択で
  wire スタイルが表示されます。
- **Run Status** / **Port Detail** / **Address Map Editor** は、選択・配線変更・
  Write/Build/Run/Step/Reset で更新されます。

---

## デバイス（Devices）

全デバイスは CPU バス上に載ります。memory ロール（RAM/ROM/VRAM）は addressable な領域、
MMIO ロール（UART/Input/Timer）は小さなレジスタ窓です。CPU は既存の `LD` / `ST`（と `OUT`）で
すべてのデバイスにアクセスします — **専用 I/O 命令はありません**。

| デバイス | Part ID | Role | Runtime ID | アクセス | 機能 | 備考 |
|---|---|---|---|---|---|---|
| CPU | `cpu.ak32` | cpu | `sim_cpu` | — | AK32 命令を実行 | reset PC は layout / ROM target 由来 |
| RAM | `mem.ram` | memory | `sim_ram` | `LD` / `ST` | 読み書き作業メモリ | 32bit LE word、**reset で 0 クリア** |
| UART | `io.uart` | mmio | `sim_uart` | `OUT` / `ST`（書込）, `LD`（status） | 書き込まれたバイトをテキスト出力として蓄積 | `+0` DATA（バイト書込）, `+4` STATUS（TX ready） |
| Input | `io.input` | mmio | `sim_input` | `LD`（読出） | 押下キー / エッジを読む | `+0` KEY_STATE, `+4` EDGE_STATE、UI/テストから駆動 |
| ROM | `mem.rom` | memory | `sim_rom` | `LD`（読出） | 読み取り専用のプログラム/ファーム領域 | CPU/bus からの書込は no-op・**reset で内容保持**・ROM target で使用 |
| Timer | `io.timer` | mmio | `sim_timer` | `LD`（読出）, `ST`（clear） | 決定論的ステップカウンタ | `+0` TICK, `+4` DELTA、1 命令ごとに +1、割り込みなし |
| VRAM | `mem.vram` | memory | `sim_vram` | `LD` / `ST` | 書き込み可能な 32×32 フレームバッファ | 1 byte/pixel・1024 B・`dump()`/`pixel()`・**reset で 0 クリア** |

各 kind の **最初の 1 個**だけが runtime part になります。2 個目以降の UART/RAM 等は Address Map
上に配置・診断はされますが実行はされません（本格的な複数デバイス runtime は将来課題）。配置
されていないデバイスは単に存在しないだけで、置かないプロジェクトは従来どおりです。

---

## AK32 アセンブリ（AK32 Assembly）

15 命令を実装しています。レジスタは `r0`–`r15`。即値は 10 進または `0x` 16 進。`[rX]` は
「rX が指すアドレスのメモリ」を意味します。label（`name:`）に対応し、`JMP` は label/アドレス、
`BEQ` は label（PC 相対）を取ります。

| 命令 | 形式 | 意味 | 例 |
|---|---|---|---|
| `NOP` | `NOP` | 何もしない | `NOP` |
| `HALT` | `HALT` | CPU を停止 | `HALT` |
| `LDI` | `LDI rd, imm16` | 16bit 即値ロード | `LDI r1, 0xC000` |
| `OUT` | `OUT [ra], rs` | [ra] のデバイスへ rs を書く | `OUT [r2], r1` |
| `ADD` | `ADD rd, rs, rt` | rd = rs + rt | `ADD r3, r1, r2` |
| `SUB` | `SUB rd, rs, rt` | rd = rs − rt | `SUB r3, r1, r2` |
| `LD` | `LD rd, [rs]` | [rs] のメモリ/MMIO から word をロード | `LD r2, [r1]` |
| `ST` | `ST [rd], rs` | [rd] のメモリ/MMIO へ word(rs) をストア | `ST [r1], r2` |
| `JMP` | `JMP target` | 無条件ジャンプ | `JMP loop` |
| `BEQ` | `BEQ rs, rt, target` | rs == rt なら target へ分岐 | `BEQ r1, r0, done` |
| `ADDI` | `ADDI rd, rs, imm8` | rd = rs + imm8 | `ADDI r2, r2, 1` |
| `AND` | `AND rd, rs, rt` | rd = rs & rt | `AND r3, r1, r2` |
| `OR` | `OR rd, rs, rt` | rd = rs \| rt | `OR r3, r1, r2` |
| `XOR` | `XOR rd, rs, rt` | rd = rs ^ rt | `XOR r3, r1, r2` |
| `NOT` | `NOT rd, rs` | rd = ~rs | `NOT r3, r1` |

**未実装**（v0.9 候補）: `BNE` / `BEQZ` / `BNEZ`（追加分岐）、`SHL` / `SHR` / `ANDI` / `ORI`
（シフト・即値ビット演算）、`CALL` / `RET` / stack。**`IN` 命令はありません** — Input は MMIO
なので `LD` で読みます。特定ビットの判定は `LD` + `AND` + `BEQ` で行います。

---

## Build / Write / Run

### プログラムターゲット

`Write Program` は割り当てた `.asm` をアセンブルし、仮想回路へロードします。**プログラム
ターゲット**でロード先を選びます。

- **RAM target**（既定・完全後方互換）: プログラムを RAM へロードし、CPU は layout の reset PC
  （既定 `0x0000`）から開始します。これは従来の動作です。
- **ROM target**: プログラムを ROM へロードし、CPU の `reset_pc` を ROM base に設定して ROM から
  fetch します。ROM が成立しない場合（ROM デバイス無し / 未配置 / overlap / size 超過）は
  **エラー**で、RAM へ**勝手に fallback しません**。ROM 内容は reset で保持され、ROM への
  CPU/bus 書込は無視されます。

### Run / Step / Reset

- **Step** はちょうど 1 命令を実行し、全デバッグパネルを更新します。
- **Run** は Step を繰り返します（最大 1000 命令、または `HALT` / pause まで）。
- 各ステップはトレース（PC 前後、デコード結果、レジスタ変化、メモリ/IO アクセス、UART 出力、
  halted/error）を生成し、Log / Bus Trace / Run Status に表示します。
- **Timer** は 1 命令ごとに 1 tick 進むため、タイミングは完全に再現可能です。
- **Reset** は CPU と runtime をリセットします。RAM と VRAM は 0 クリア、Timer はリセット、
  ROM は内容を保持します。Reset はパネル（VRAM Viewer を含む）も更新します。

---

## Memory Layout と Address Map

**Address Map** は 16bit バス上のデバイス配置（各デバイスの base / size / end と attach range）で、
overlap と range の検出を行います。

- **MemoryLayout** プリセットが既定の base/size を決めます。

  | Layout | RAM | ROM | VRAM | MMIO base |
  |---|---|---|---|---|
  | `LEGACY` | `0x0000` / 256 B | — | — | `0x0100` |
  | `CIRCUIT_COMPAT`（既定） | `0x0000` / 64 KB | —（override） | —（override） | `0x0100`（RAM 内） |
  | `GAME16` | `0x8000` / 16 KB | `0x0000` / 32 KB | `0xC000` / 1 KB | `0xE000` |

- **MMIO アドレスは配置順で割り当て**られます。UART / Input / Timer は `MMIO base`, `+0x10`,
  `+0x20` … に載るため、GAME16 では概ね `0xE000` / `0xE010` / `0xE020`、CIRCUIT_COMPAT では
  `0x0100` / `0x0110` / `0x0120` になります。**プログラムに焼き込む前に、実際の番地を Address Map
  / Run Status で確認してください。**
- **Address Map Editor**（dock パネル）で per-device の `base` / `size` を override（auto ↔
  manual）でき、Reset to Auto、range / overlap / alignment の検証を行います。override は
  プロジェクトの `system.json` に永続化されます。override なしなら layout 完全自動（現行既定動作）。
- インタラクティブな MainWin は `CIRCUIT_COMPAT` を自動選択します。`GAME16` はテストおよび
  その配置を再現する Editor override（例: VRAM を `0xC000` に置き RAM を縮小）で使われます。
- このパッチ群は `tests/test/system.json` を**変更しません**。

---

## Input / Timer / VRAM

### Input（MMIO・`LD` で読む）

- レジスタ窓: `+0` **KEY_STATE**（現在押下中のキー bitmask）、`+4` **EDGE_STATE**（前回 clear 以降に
  押されたキー。EDGE_STATE への書込で clear）。
- キービット: `0` up, `1` down, `2` left, `3` right, `4` A, `5` B, `6` Start, `7` Select。
- CPU は `LD` でキーを読み、`AND` + `BEQ` で個別ビットを判定します。入力状態は UI / テストから
  駆動します（`IN` 命令は不要）。

### Timer（MMIO・`LD` で読む / `ST` で clear）

- 決定論的: wall-clock ではなく **CPU ステップ数**を数えるため、実行は再現可能です。
- レジスタ窓: `+0` **TICK**（単調増加のステップ数。書込で clear）、`+4` **DELTA**（前回 DELTA
  clear 以降の tick 数。書込で「今」に rebase）。
- `LD` で読み、`ST` で clear。**割り込みはまだありません**。

### VRAM（書き込み可能フレームバッファ）

- memory デバイス: 32×32 ピクセル、**1 byte / pixel**（インデックス値）、合計 1024 バイト。
- CPU は `ST` で書き、`LD` で読みます（32bit LE word・1 word = 横 4 ピクセル）。`dump()` /
  `pixel(x, y)` / `set_pixel(x, y, v)` でフレームバッファにアクセスできます。
- reset で 0 クリア。内容は **VRAM Viewer** に表示されます。
- **palette / sprite / tile はまだありません** — 値はグレースケールの濃淡として描画されます。

---

## 最小ゲーム runtime（Minimal Game Runtime）

現時点で動く「ゲームっぽい」挙動は、ゲームエンジンではなく **最小** runtime です。

- **ROM + Input + Timer + VRAM** を（CPU/RAM/UART と一緒に）同時配置します。
- **ROM target** で実行: CPU は ROM からコードを fetch します。
- プログラムは **Input** と **Timer** を `LD` で読み、**VRAM** へ `ST` で描画します。
- **VRAM Viewer**（小さな dock）が 32×32 フレームバッファを拡大したグレースケール画像として
  表示し、Step / Run / Reset / Write 後に更新します。
- 新しい `GameRuntime` クラスは追加していません。既存の **Run/Step** ループ上で動き、**CPU 命令
  も ASM 構文も変更していません**。Run Status パネルには有効デバイスを示す `Game:` 行が出ます
  （例: `ROM+Input+Timer+VRAM`）。

これは v0.8 の到達点です。ROM + Input + Timer + VRAM が一緒に動くことと、可視化された
フレームバッファを示すには十分です。sprite / tile / palette / audio / フレーム同期 / 本格的な
ゲームループは**含みません**（Known Limitations / v0.9 候補を参照）。

---

## デバッグパネル（Debug Panels）

| パネル | 表示内容 |
|---|---|
| UART Console | 蓄積された UART テキスト出力 |
| Console / Log | Build/run メッセージとステップごとのトレース |
| Register View | CPU レジスタ・PC・cycle |
| Memory Viewer | シミュレータ RAM の hex dump（PC 行ハイライト付き） |
| Bus Trace | 直近のバス read/write トランザクション |
| Run Status | mode・プログラムターゲット・Timer/VRAM/Game 行・target CPU・Address Map・last trace・UART |
| Port Detail | logical/visual ポート・direction/width・接続・wire 詳細 |
| Address Map Editor | per-device base/size 表示 + override（auto/manual）+ 検証 |
| VRAM Viewer | 32×32 グレースケールフレームバッファ（未配置時は `VRAM: None`） |
| Canvas overlay | エディタ / Canvas 上の PC ハイライト・Run 中の signal overlay |

---

## プロジェクトの保存 / 読み込み（Project Save / Load）

保存されるプロジェクト（`system.json`）に現在含まれるもの:

- **Canvas レイアウト**（ノード・座標・visual port・wire/接続・wire スタイル）、
- 部品ごとの**ソース割り当て**（`sources.asm` / `hdl` / `rom` のパス）、
- **プログラムターゲット**（`ram` / `rom`）、
- **Address Map override**（per-device base/size）。

まだ永続化されないもの: ロード済みプログラムイメージそのもの（`loaded_program` はセッション
限定）。より強力な save/load（プログラム永続化・移植性）は v0.9 候補です。

---

## サンプルプログラム（Sample Programs）

既存サンプル:

| ファイル | 説明 |
|---|---|
| `src/hello.asm` | `LDI` / `OUT` / `HALT` で UART に "Hi" を出力 |
| `src/fib.asm` | `ADD` / `ST` / `ADDI` / `BEQ` / `JMP` でフィボナッチ |

最小の VRAM / デバイススニペット（実装済み命令のみ）。下記アドレスは **GAME16** マップ
（VRAM = `0xC000`）を前提とします。Input/Timer の MMIO base は配置順で決まるため、依存する前に
**Address Map / Run Status で実際の base を確認**してください。

VRAM に固定値を書く:

```asm
LDI r1, 0xC000      ; VRAM base（GAME16）
LDI r2, 0x00FF      ; pixel value
ST  [r1], r2        ; VRAM[0] = 0xFF
HALT
```

Timer の tick を VRAM へコピー（`<TIMER_BASE>` は Address Map に表示される番地に置換）:

```asm
LDI r1, <TIMER_BASE>  ; GAME16 では例えば 0xE020 — Address Map で確認
LD  r2, [r1]          ; TICK を読む
LDI r3, 0xC000
ST  [r3], r2          ; VRAM[0] = tick
HALT
```

Input 状態を VRAM へコピー（`<INPUT_BASE>` は Address Map に表示される番地に置換）:

```asm
LDI r1, <INPUT_BASE>  ; GAME16 では例えば 0xE010 — Address Map で確認
LD  r2, [r1]          ; KEY_STATE を読む
LDI r3, 0xC000
ST  [r3], r2          ; VRAM[0] = keys
HALT
```

---

## 動作要件（Requirements）

- Python 3.11+
- PySide6

## セットアップ（Setup）

```
pip install -r requirements.txt
```

## 起動（Run）

```
python main.py
```

## テスト（Test）

```
python -m pytest tests/
```

現在の結果: **1182 passed**（21 件の warning は PySide6 `Deprecation` 通知のみ）。GUI の目視確認
（VRAM Viewer の見た目、画面上の Run Status 行など）はヘッドレステスト環境では**実施していません**。
基盤ロジック（`snapshot()` / `pixel()` によるフレームバッファ描画、status フォーマット）は
`pytest` でカバーされています。

---

## 既知の制限（Known Limitations）

- **GUI 目視確認**は一部未検証（ヘッドレステストはロジックを検証し、画面表示は対象外）。
- **VRAM Viewer** は最小: 32×32 グレースケールのみ — palette / color UI / 拡大率 UI なし。
- **sprite / tile なし**、**palette なし**（バイト値をグレー濃淡で表示）。
- **audio なし**、**DMA / GPU なし**、**physics / asset system なし**。
- **HDL / FPGA export はまだなし**。
- **命令セットの不足**: 追加分岐なし（`BNE` / `BEQZ` / `BNEZ`）、シフト/即値ビット演算なし
  （`SHL` / `SHR` / `ANDI` / `ORI`）、stack / `CALL` / `RET` なし。
- **本格的なゲーム runtime なし** — 最小 runtime はデバイス統合を示すもので、ゲームループでは
  ありません。
- **同梱のプロジェクトテンプレート / サンプルゲームプロジェクトはまだなし**。
- **複数 RAM/UART**: 追加デバイスは配置・診断されますが各 kind の最初の 1 個だけ実行されます。
  真の複数 RAM 共存は未解決（16bit アドレス空間の制約）。
- `tests/test/system.json` のテスト実行差分の扱い（破棄 / コミット / gitignore 化）はユーザー
  判断の繰越事項です。

---

## v0.9 候補（Planning Candidates）

v0.9 の方向性は **意図的に未決定**です。現状の機能を確認したうえでユーザーが v0.9 の焦点を
決めます。候補（未確定・優先順位なし）:

- AK32 **branch 拡張**（`BNE` / `BEQZ` / `BNEZ`）
- **シフト / 即値ビット演算**（`SHL` / `SHR` / `ANDI` / `ORI`）
- **stack / `CALL` / `RET`**
- **VRAM Viewer 拡張**（palette / color / 拡大率 UI）
- **Game Runtime 拡張**（フレーム同期 / 入力エッジ / 本格ゲームループ / 複数 VRAM）
- **sprite / tile / palette** グラフィクス
- **HDL / FPGA export** 準備
- **プロジェクトテンプレート / サンプルプロジェクト**
- **save/load 強化**（プログラム永続化・移植性）
- **GUI polish**
- **パッケージング / リリース**準備

---

## ドキュメント（Documentation）

- **[Quick Start](docs/QUICKSTART.md)** — 5 分で hello.asm を動かす手順
- **[User Guide](docs/USER_GUIDE.md)** — 全機能の詳細説明
- **計画**: [ROADMAP8.md](ROADMAP8.md) / [CHECKLIST8.md](CHECKLIST8.md)。パッチごとの設計資料は
  `PATCH_*_V08_*.md`。完了したフェーズ計画は `old/` に収納（履歴保管）: v0.7 は
  [old/ROADMAP7.md](old/ROADMAP7.md) / [old/CHECKLIST7.md](old/CHECKLIST7.md)、v0.6 は
  [old/ROADMAP6.md](old/ROADMAP6.md) / [old/CHECKLIST6.md](old/CHECKLIST6.md)。
- **引き継ぎ / 現在状態**: [HANDOFF.md](HANDOFF.md)。
