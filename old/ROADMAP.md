# AKDev ROADMAP

## 0. プロジェクトの目的

AKDev は、自作 FPGA ゲーム機のための統合開発環境兼シミュレータです。

これは単なる CPU エミュレータではありません。仮想ハードウェアを画面上で組み、パーツライブラリから部品を追加し、各パーツのプログラムや HDL 風の定義を編集し、パーツ間のデータの流れをシミュレーションできるアプリを目指します。

最初に想定する実機は、2個の FPGA を使った携帯ゲーム機風の自作機です。ただし、2個の FPGA を最初から「CPU 用」「GPU 用」と固定して考えません。アプリ上では、2個の FPGA を汎用のロジックチップとして扱い、その中に CPU、RAM コントローラ、映像回路、VRAM、UART、タイマー、デバッグ回路などを割り当てられるようにします。

---

## 1. 基本方針

### 1.1 パーツベースのハード設計

AKDev では、ゲーム機全体を複数のパーツの集まりとして扱います。

パーツ例:

* FPGA チップ
* CPU コア
* RAM
* VRAM
* UART
* タイマー
* 割り込みコントローラ
* バスブリッジ
* 映像コントローラ
* タイルエンジン
* スプライトエンジン
* 音源ブロック
* 入力コントローラ
* 電源監視ブロック

ユーザーはパーツライブラリからパーツを追加し、System Canvas 上で接続できるようにします。

### 1.2 チップは役割固定ではなく、パーツの入れ物として扱う

内部設計では、`CPU FPGA` や `GPU FPGA` のように役割を固定しません。

代わりに、次のような名前を使います。

* `chip0`
* `chip1`

プリセットでは `chip0` に CPU 系、`chip1` に映像系を置いてもよいですが、アプリの構造としてはそれに依存しないようにします。

### 1.3 実機より先にシミュレーションする

シミュレータ上で、次を確認できるようにします。

* CPU の命令実行
* RAM の読み書き
* GPU レジスタへの書き込み
* VRAM 更新
* バス通信
* 割り込み
* UART 出力
* 仮想画面の更新

これにより、PCB を作る前にハードウェア構成とソフトウェア仕様を検証できます。

### 1.4 各パーツの内部を編集できるようにする

各パーツには、必要に応じて編集可能な中身を持たせます。

例:

* CPU パーツ: アセンブリプログラム
* FPGA パーツ: HDL 風ソース
* GPU パーツ: レジスタ動作や HDL 風ソース
* RAM パーツ: メモリダンプ、バイナリ読み込み
* 映像パーツ: 解像度、色形式、表示設定

ユーザーがエディタで保存すると、そのパーツに疑似的に書き込まれた状態としてシミュレータへ反映します。

### 1.5 拡張可能なパーツライブラリ

このアプリを今回のゲーム機専用で終わらせないようにします。

パーツは外部定義ファイルとして保存し、後から新しい FPGA、CPU、メモリ、I/O、映像ブロックなどを追加できるようにします。

---

## 2. アプリ構成案

```text
akdev/
├─ main.py
├─ core/
│  ├─ sim.py
│  ├─ part.py
│  ├─ chip.py
│  ├─ bus.py
│  ├─ mem.py
│  ├─ cpu.py
│  ├─ gpu.py
│  ├─ uart.py
│  ├─ timer.py
│  └─ irq.py
├─ asm/
│  ├─ asm.py
│  ├─ tok.py
│  ├─ enc.py
│  └─ disasm.py
├─ ui/
│  ├─ win.py
│  ├─ canvas.py
│  ├─ lib.py
│  ├─ prop.py
│  ├─ edit.py
│  ├─ reg.py
│  ├─ memv.py
│  ├─ gpuv.py
│  ├─ busv.py
│  └─ log.py
├─ parts/
│  ├─ fpga/
│  ├─ cpu/
│  ├─ mem/
│  ├─ io/
│  ├─ video/
│  └─ custom/
├─ spec/
│  ├─ cpu.md
│  ├─ gpu.md
│  ├─ bus.md
│  ├─ mem.md
│  └─ rom.md
├─ sample/
│  ├─ hello/
│  └─ video_test/
└─ docs/
   └─ roadmap.md
```

この構成は後で変更してよいです。ただし、最初の段階からシミュレータ本体、UI、アセンブラ、パーツライブラリは分離しておきます。

---

## 3. メイン UI の構想

### 3.1 メイン画面

```text
┌───────────────────────────────────────────────┐
│ File Edit Build Run Debug Tools Settings      │
├───────────────┬───────────────────────────────┤
│ Parts Library │ System Canvas                 │
│               │                               │
│ FPGA          │  [chip0] ── bus ── [chip1]    │
│ CPU           │     │                │        │
│ RAM           │   [RAM]            [VRAM]     │
│ UART          │     │                │        │
│ Video         │   [UART]          [Video]     │
├───────────────┴───────────────────────────────┤
│ Console / Log / Bus Trace / Errors            │
└───────────────────────────────────────────────┘
```

### 3.2 主なパネル

* Parts Library
* System Canvas
* Properties Panel
* Tab Editor
* Register View
* Memory View
* GPU/View Output
* Bus Trace
* UART Console
* Error Log
* Hardware Monitor Mock

### 3.3 パーツ右クリックメニュー

共通操作:

* プログラムを開く
* HDLを開く
* 設定を開く
* 信号を見る
* メモリを見る
* レジスタを見る
* 複製
* 削除
* エクスポート

内部 ID は英語で管理し、UI 表示は後で日本語化してもよいです。

---

## 4. プロジェクトファイル設計

各 AKDev プロジェクトは、次のような構成にします。

```text
project/
├─ project.json
├─ system.json
├─ src/
│  ├─ main.asm
│  └─ gpu_logic.v
├─ asset/
│  ├─ img/
│  ├─ snd/
│  └─ map/
├─ build/
│  ├─ main.bin
│  ├─ game.rom
│  └─ logs/
└─ parts/
   └─ custom/
```

### 4.1 `system.json` の例

```json
{
  "chips": [
    {
      "id": "chip0",
      "type": "fpga.ecp5_85f",
      "x": 200,
      "y": 120
    },
    {
      "id": "chip1",
      "type": "fpga.ecp5_85f",
      "x": 560,
      "y": 120
    }
  ],
  "parts": [
    {
      "id": "cpu0",
      "type": "cpu.ak32",
      "parent": "chip0"
    },
    {
      "id": "ram0",
      "type": "mem.ram",
      "parent": "chip0",
      "base": "0x10000000",
      "size": "16MiB"
    },
    {
      "id": "vram0",
      "type": "mem.vram",
      "parent": "chip1",
      "base": "0x40000000",
      "size": "8MiB"
    }
  ],
  "links": [
    {
      "from": "cpu0.bus",
      "to": "ram0.bus",
      "type": "bus32"
    },
    {
      "from": "chip0.bridge",
      "to": "chip1.bridge",
      "type": "parallel16"
    }
  ]
}
```

---

## 5. パーツライブラリ仕様

### 5.1 ディレクトリ形式

```text
parts/
├─ fpga/
│  ├─ ecp5_85f/
│  │  ├─ part.json
│  │  ├─ pins.json
│  │  ├─ resources.json
│  │  └─ sim.py
│  └─ ecp5_45f/
├─ cpu/
│  └─ ak32/
│     ├─ part.json
│     ├─ isa.json
│     └─ sim.py
├─ mem/
│  ├─ ram/
│  └─ vram/
├─ io/
│  ├─ uart/
│  ├─ timer/
│  └─ gpio/
└─ video/
   ├─ video_out/
   ├─ tile/
   └─ sprite/
```

### 5.2 `part.json` の例

```json
{
  "id": "fpga.ecp5_85f",
  "name": "Lattice ECP5-85F",
  "category": "fpga",
  "description": "84K LUT class FPGA",
  "ports": [
    {"name": "bus", "type": "bus.slave"},
    {"name": "jtag", "type": "debug.jtag"},
    {"name": "clk", "type": "clock"},
    {"name": "reset", "type": "reset"}
  ],
  "resources": {
    "lut": 84000,
    "bram_kbit": 3836,
    "dsp": 156
  },
  "editable": [
    {"name": "hdl", "type": "verilog"},
    {"name": "program", "type": "asm"}
  ],
  "sim": "sim.py"
}
```

### 5.3 ポート型

初期対応するポート型:

* `bus.master`
* `bus.slave`
* `clock`
* `reset`
* `irq`
* `gpio`
* `video.rgb`
* `audio.pwm`
* `debug.jtag`
* `serial.uart`
* `spi.master`
* `spi.slave`
* `i2c.master`
* `i2c.slave`

接続できない組み合わせは、アプリ側で拒否します。

---

## 6. シミュレータ本体

### 6.1 パーツの基本インターフェース

```python
class Part:
    def reset(self):
        pass

    def tick(self):
        pass

    def read(self, addr: int) -> int:
        raise NotImplementedError

    def write(self, addr: int, value: int):
        raise NotImplementedError
```

### 6.2 シミュレーション規則

* シミュレータが全体の tick ループを管理する。
* CPU パーツは `tick()` で命令を実行する。
* GPU / Video パーツは `tick()` で内部状態や表示を更新する。
* Bus パーツは `read()` と `write()` をルーティングする。
* ログにはバス通信、エラー、デバイスメッセージを記録する。
* GUI から Run、Pause、Step、Reset できるようにする。

### 6.3 Bus Trace の例

```text
[00001234] CPU WRITE 0x30000008 = 0x0000003F  GPU_BG
[00001235] GPU  BG colour changed to 0x3F
[00001240] CPU WRITE 0x20000000 = 0x00000048  UART
```

---

## 7. 初期 CPU 仕様

### 7.1 CPU 名

初期カスタム CPU 名: `AK32`

### 7.2 レジスタ

* `r0`: 常に 0
* `r1` 〜 `r12`: 汎用
* `r13`: スタックポインタ
* `r14`: リンクレジスタ
* `r15`: 予約または汎用
* `pc`: プログラムカウンタ
* `flags`: Z, N, C, V

### 7.3 初期命令

```asm
NOP
HALT
LDI rd, imm
LD  rd, [ra + imm]
ST  rs, [ra + imm]
ADD rd, ra, rb
SUB rd, ra, rb
AND rd, ra, rb
OR  rd, ra, rb
XOR rd, ra, rb
SHL rd, ra, imm
SHR rd, ra, imm
JMP addr
BEQ ra, rb, offset
BNE ra, rb, offset
CALL addr
RET
IN  rd, [addr]
OUT [addr], rs
```

### 7.4 後回しにする CPU 機能

* 乗算
* 除算
* 割り込み
* キャッシュ
* パイプライン
* 特権モード
* MMU
* C コンパイラ対応

これらは最初のマイルストーンには含めません。

---

## 8. 初期メモリマップ

```text
0x0000_0000 - 0x0000_FFFF  Boot ROM
0x1000_0000 - 0x10FF_FFFF  Main RAM
0x2000_0000 - 0x2000_00FF  UART
0x2000_0100 - 0x2000_01FF  Timer
0x2000_0200 - 0x2000_02FF  Input
0x2000_0300 - 0x2000_03FF  Power Monitor
0x3000_0000 - 0x3000_0FFF  Graphics Registers
0x4000_0000 - 0x40FF_FFFF  VRAM Window
```

このマップは仮案です。シミュレータ、アセンブラ、後の HDL で同じ定義を使えるように、共有定義ファイルにまとめます。

---

## 9. 初期グラフィック仕様

### 9.1 初期グラフィックレジスタ

| Offset | Name       | Description    |
| -----: | ---------- | -------------- |
|   0x00 | `GFX_ID`   | 固定識別子          |
|   0x04 | `STATUS`   | READY/BUSY フラグ |
|   0x08 | `BG_COLOR` | 背景色            |
|   0x0C | `CMD`      | コマンドレジスタ       |
|   0x10 | `ARG0`     | コマンド引数 0       |
|   0x14 | `ARG1`     | コマンド引数 1       |
|   0x18 | `ARG2`     | コマンド引数 2       |
|   0x1C | `IRQ_EN`   | 割り込み許可         |
|   0x20 | `IRQ_FLAG` | 割り込み状態         |

### 9.2 初期グラフィックコマンド

| ID | Command    |
| -: | ---------- |
|  0 | NOP        |
|  1 | CLEAR      |
|  2 | SET_BG     |
|  3 | DRAW_RECT  |
|  4 | COPY       |
|  5 | LOAD_TILE  |
|  6 | SET_SPRITE |

### 9.3 後回しにするグラフィック機能

* 複数背景レイヤ
* スプライト優先順位
* 半透明合成
* 回転・拡大縮小
* 3D パイプライン
* テクスチャマッピング
* 音声同期

---

## 10. プリセット

### 10.1 Minimal CPU

```text
chip0
├─ AK32 CPU
├─ RAM
└─ UART
```

### 10.2 Simple Video

```text
chip0
├─ AK32 CPU
├─ RAM
└─ UART

chip1
├─ VRAM
├─ Video Out
└─ RGB Output
```

### 10.3 Dual Chip Console

```text
chip0
├─ AK32 CPU
├─ RAM
├─ UART
├─ Timer
├─ Storage
└─ Bus Bridge

chip1
├─ VRAM
├─ Video Out
├─ Tile Engine
├─ Sprite Engine
└─ Audio
```

### 10.4 Handheld Prototype

```text
chip0
├─ AK32 CPU
├─ RAM
├─ Input
├─ Storage
├─ Power Monitor
└─ Bus Bridge

chip1
├─ VRAM
├─ Video Out
├─ Tile Engine
├─ Sprite Engine
└─ LCD Out
```

---

## 11. ロードマップ

## Phase 0: 計画と仕様書作成

目的:

* 基本アーキテクチャを定義する。
* 最初の仕様書を作る。
* アプリ構成を決める。

作業:

* `spec/cpu.md` を作る。
* `spec/gpu.md` を作る。
* `spec/mem.md` を作る。
* `spec/bus.md` を作る。
* `spec/rom.md` を作る。
* 初期パーツカテゴリを定義する。
* プロジェクトファイル形式を定義する。

完了条件:

* プロジェクト全体の設計概要が文章化されている。
* CPU、メモリマップ、グラフィックレジスタの初期仕様がある。

---

## Phase 1: GUI の骨組み

目的:

* デスクトップアプリの基本画面を作る。

作業:

* メインウィンドウを作る。
* メニューバーを追加する。
* ツールバーを追加する。
* パーツライブラリパネルを追加する。
* System Canvas パネルを追加する。
* プロパティパネルを追加する。
* ログパネルを追加する。
* プロジェクト保存/読み込みの仮実装をする。

完了条件:

* アプリが起動する。
* 空のプロジェクトを作成できる。
* 画面レイアウトが崩れず表示される。

---

## Phase 2: System Canvas とパーツ配置

目的:

* パーツを視覚的に配置、管理できるようにする。

作業:

* `parts/` からパーツ定義を読み込む。
* パーツライブラリパネルにパーツを表示する。
* パーツをキャンバスに追加できるようにする。
* パーツをキャンバス上で移動できるようにする。
* パーツを選択できるようにする。
* パーツを削除できるようにする。
* 位置情報を `system.json` に保存する。
* `system.json` から位置情報を読み込む。

完了条件:

* chip、CPU、RAM、UART、Video パーツをキャンバスに配置できる。
* プロジェクトを開き直しても配置が復元される。

---

## Phase 3: パーツ設定と右クリックメニュー

目的:

* パーツごとの編集と設定を可能にする。

作業:

* 右クリックメニューを追加する。
* `プログラムを開く` を追加する。
* `HDLを開く` を追加する。
* `設定` を追加する。
* プロパティ編集パネルを作る。
* ベースアドレス、サイズ、クロック、名前などを編集できるようにする。
* 設定を `system.json` に保存する。

完了条件:

* パーツを右クリックできる。
* プログラム/HDL エディタが新しいタブで開く。
* パーツ設定を編集して保存できる。

---

## Phase 4: タブエディタ

目的:

* アプリ内でコード編集できるようにする。

作業:

* タブ式エディタ領域を追加する。
* テキストエディタを追加する。
* syntax mode を保持できるようにする。
* エディタ内容をプロジェクトファイルへ保存する。
* パーツの右クリックメニューから該当タブを開く。
* 変更済みタブを管理する。

完了条件:

* パーツのプログラムを開くと新しいタブが作られる。
* 編集して保存できる。
* 同じパーツを再度開くと同じ内容が表示される。

---

## Phase 5: 最小シミュレータ本体

目的:

* 最小の仮想システムを動かす。

作業:

* 基本 `Part` クラスを作る。
* `Bus` を作る。
* `Memory` を作る。
* `UART` を作る。
* シミュレータの tick ループを作る。
* Reset、Run、Pause、Step を作る。
* ログ出力を追加する。

完了条件:

* 仮想 RAM と UART をバスに接続できる。
* シミュレータを reset / tick しても落ちない。

---

## Phase 6: AK32 CPU エミュレータ

目的:

* 基本的な自作 CPU 命令を実行する。

作業:

* レジスタを実装する。
* PC と flags を実装する。
* 命令 fetch を実装する。
* 命令 decode を実装する。
* 基本演算命令を実装する。
* load/store を実装する。
* 分岐と HALT を実装する。
* レジスタビューを追加する。
* Step 実行に対応する。

完了条件:

* 手書きバイナリを実行できる。
* レジスタが正しく更新される。
* HALT で停止する。

---

## Phase 7: アセンブラ v0.1

目的:

* アセンブリテキストをバイナリへ変換する。

作業:

* アセンブリをトークン化する。
* ラベルを解析する。
* 初期命令をエンコードする。
* バイナリを生成する。
* 行番号付きエラーを表示する。
* Build ボタンと統合する。

完了条件:

* `main.asm` からバイナリを作れる。
* バイナリを CPU パーツへ読み込める。
* UART 出力プログラムが動く。

テストプログラム:

```asm
LDI r1, 72
OUT 0x20000000, r1
LDI r1, 105
OUT 0x20000000, r1
HALT
```

期待出力:

```text
Hi
```

---

## Phase 8: Bus Trace と Memory Viewer

目的:

* 内部のデータの流れを見えるようにする。

作業:

* バス通信ログを追加する。
* Memory Viewer を追加する。
* アドレス検索を追加する。
* 監視アドレスを追加する。
* read/write フィルタを追加する。

完了条件:

* CPU の read/write が Bus Trace に表示される。
* RAM と I/O の内容を確認できる。

---

## Phase 9: グラフィックレジスタのシミュレーション

目的:

* CPU からグラフィック側へ値を渡す流れを再現する。

作業:

* グラフィックレジスタパーツを実装する。
* `GFX_ID` を追加する。
* `STATUS` を追加する。
* `BG_COLOR` を追加する。
* `CMD` と引数レジスタを追加する。
* 仮想画面パネルを追加する。
* 背景色レジスタに書き込むと画面色が変わるようにする。

完了条件:

* CPU が `GFX_ID` を読める。
* CPU が `BG_COLOR` に書ける。
* 仮想画面の色が変わる。

---

## Phase 10: VRAM と framebuffer

目的:

* メモリ内容をピクセルとして表示する。

作業:

* VRAM パーツを追加する。
* framebuffer mode を追加する。
* 8-bit indexed colour に対応する。
* パレットテーブルを追加する。
* VRAM Viewer を追加する。
* 仮想画面を更新する。

完了条件:

* CPU が VRAM に書ける。
* VRAM 内容が仮想画面に表示される。

---

## Phase 11: タイルとスプライトのシミュレーション

目的:

* ゲーム機らしい 2D グラフィックをシミュレートする。

作業:

* タイルメモリを追加する。
* タイルマップを追加する。
* スプライトテーブルを追加する。
* パレットエディタを追加する。
* 基本スクロールレジスタを追加する。
* スプライト座標レジスタを追加する。
* VBlank tick を追加する。

完了条件:

* タイル背景を表示できる。
* CPU プログラムでスプライトを動かせる。
* シミュレータ上に VBlank タイミングが存在する。

---

## Phase 12: プロジェクト管理とプリセット

目的:

* 実際のプロジェクト作成に使えるようにする。

作業:

* 新規プロジェクトウィザードを追加する。
* プリセットを追加する。
* `Minimal CPU` プリセットを追加する。
* `Simple Video` プリセットを追加する。
* `Dual Chip Console` プリセットを追加する。
* `Handheld Prototype` プリセットを追加する。
* プロジェクトツリーを追加する。

完了条件:

* プリセットから新規プロジェクトを作れる。
* プロジェクトを開くと、初期パーツが配置済みになる。

---

## Phase 13: 自作パーツ対応

目的:

* アプリを今回のゲーム機以外にも拡張できるようにする。

作業:

* `parts/custom/` から自作パーツを読み込む。
* `part.json` を検証する。
* 無効なパーツ定義のエラーを表示する。
* `New Part from Template` を追加する。
* メモリ、バスデバイス、映像デバイス、FPGA のテンプレートを追加する。

完了条件:

* アプリ本体を変更せず、JSON 定義で新しいパーツを追加できる。

---

## Phase 14: アセットツール

目的:

* ゲーム開発に必要な画像変換を可能にする。

作業:

* 画像インポートを追加する。
* 画像をパレットへ変換する。
* 画像をタイルデータへ変換する。
* 画像をスプライトデータへ変換する。
* バイナリアセットを書き出す。
* アセットプレビューを追加する。

完了条件:

* PNG をタイル/スプライトデータへ変換し、シミュレータで使える。

---

## Phase 15: ROM Builder

目的:

* ゲーム全体を1つの ROM ファイルとして生成する。

作業:

* ROM 形式を定義する。
* コードを格納する。
* アセットを格納する。
* メタデータを格納する。
* `game.rom` を生成する。
* ROM をエミュレータへ読み込む。

完了条件:

* サンプルゲームプロジェクトから1つの ROM ファイルを生成できる。
* その ROM が AKDev 上で動く。

---

## Phase 16: 実機ハードウェア向けエクスポート

目的:

* 実 FPGA / PCB 開発に使えるファイルを出力する。

作業:

* メモリマップヘッダを出力する。
* レジスタ定義を出力する。
* Verilog 雛形を出力する。
* ピン計画メモを出力する。
* パーツ使用リソース概要を出力する。
* バス仕様を出力する。

完了条件:

* HDL と PCB 設計に使える情報を AKDev から出力できる。

---

## Phase 17: 実機接続

目的:

* 将来の実機基板と通信できるようにする。

作業:

* シリアルポート選択を追加する。
* UART アップロードを追加する。
* モニタプロトコルを追加する。
* メモリ read/write コマンドを追加する。
* 電源監視情報の表示を追加する。
* 実機ログビューアを追加する。

完了条件:

* AKDev から UART 経由でテストバイナリを実機へ送れる。
* 実機からのログを AKDev で受信できる。

---

## 12. 最初のマイルストーン

最初のマイルストーンは小さく、明確にします。

マイルストーン名:

```text
AKDev v0.1 Minimal Interactive Simulator
```

必須機能:

* メインウィンドウが開く。
* パーツライブラリが見える。
* System Canvas が見える。
* `chip0`、`AK32`、`RAM`、`UART` を配置できる。
* 右クリックメニューが動く。
* `プログラムを開く` でタブが開く。
* アセンブリテキストを保存できる。
* アセンブラで小さいプログラムをビルドできる。
* CPU がプログラムを実行できる。
* UART パネルに `Hi` が表示される。
* Register View が更新される。
* Bus Trace に write が表示される。

これが最初の実用目標です。

---

## 13. 初期バージョンでやらないこと

最初から次は実装しません。

* 完全な Verilog 合成
* 正確な FPGA タイミングシミュレーション
* C コンパイラ
* Linux 対応
* 3D グラフィック
* HDMI シミュレーション
* PCB 自動生成
* 自動配置配線
* DS 相当のサイクル精度

最初の目的は、本格 EDA ではなく、アーキテクチャ検証と開発ワークフローの確立です。

---

## 14. Claude Code 向け実装メモ

実装時は変更を小さく分けます。

推奨順:

1. ファイル構成を作る。
2. プロジェクト保存/読み込みを作る。
3. UI の骨組みを作る。
4. パーツライブラリ読み込みを作る。
5. キャンバス配置を作る。
6. 右クリックメニューを作る。
7. タブエディタを作る。
8. シミュレータ本体を作る。
9. AK32 CPU を作る。
10. アセンブラを作る。
11. UART テストを通す。

一度に全部作らないこと。

各 Phase には、必ず簡単な手動テストを用意します。

関数名とファイル名は、可能な範囲で短くします。
