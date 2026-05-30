# AKDev ROADMAP 4

> v0.3 以降の開発計画。
> v0.2 完了時点の計画は `ROADMAP3.md` / `CHECKLIST3.md` を参照。
> 進捗管理は `CHECKLIST4.md` で行う。

---

## v0.2 到達点（2026-05-24 完了）

完了条件「**Workspace UI Refinement**」達成。pytest 120 件通過。headless フロー全通過。

### v0.2 実装済み一覧

| カテゴリ | 実装内容 |
|---|---|
| View メニュー | Dock 再表示トグル（全 6 パネル） |
| Ribbon 風コマンドバー | File / Build-Run / View / Tools タブ |
| メニューバー整理 | File メニューのみ残存、Build/Run/View は Ribbon に集約 |
| Project Dialog | New / Open / Save / Save As（ダイアログ経由） |
| 保存仕様修正 | `project_root/src/` / `build/out/` 分離 |
| テスト | pytest 120 件 PASSED |

---

## v0.3 テーマ: Project & Target Foundation（2026-05-24 完了）

### 目的

AKDev を AK32 固定の最小シミュレータから、将来的に自作命令セット・自作 OS・外部ツール連携・VS Code Companion 拡張へつなげられる**プロジェクト基盤**へ拡張する。

v0.3 は **v0.5 AKDev VS Code Companion の下準備**バージョンと位置づける。
（v0.4 は Visual Debug Canvas に変更。VS Code Companion は v0.5 に移動。）

---

## AKDev と VS Code の関係

**Unity と VS Code のような関係を目指す。**

| 役割 | 担当 |
|---|---|
| AKDev 本体 | プロジェクト管理 / System Canvas / シミュレーション / Build / Run / Target 設定 / 将来的な基板・実機書き出し |
| VS Code | ASM / HDL / C / 自作言語の編集 / 補完 / 検索 / Git / 将来的な AKDev Companion 拡張による Build / Run / 状態表示 |

AKDev は Unity Editor 側、VS Code はコード編集側として役割を分担する。

---

## v0.5 AKDev VS Code Companion（将来機能）

v0.5 で作るものの概要を先に示す。v0.3 はこれへのブリッジになる。

| 機能 | 概要 |
|---|---|
| VS Code 拡張本体 | AKDev Companion（`akdev.akdev-companion`） |
| target.json / isa.json 補完 | target の ISA 定義に基づく ASM 補完 |
| Build / Run / Reset / Step 要求 | AKDev への操作コマンド送信 |
| Problems 連携 | ビルドエラーを Problems パネルへ表示 |
| Register / UART / Bus Trace 表示 | AKDev の状態を VS Code サイドパネルに表示 |
| localhost HTTP / WebSocket 連携 | AKDev との相互連携プロトコル |

---

## v0.3 でやること

### 1. target.json の導入

プロジェクトごとに CPU / ISA / runtime / memory map / build output を持てるようにする。

#### target.json 仕様案

```json
{
  "target": {
    "name": "AK32 Baremetal",
    "isa": "ak32",
    "cpu": "ak32",
    "runtime": "baremetal",
    "entry": "src/main.asm",
    "output": "build/out/main.bin",
    "load_address": "0x0000",
    "entry_point": "0x0000"
  }
}
```

| フィールド | 説明 |
|---|---|
| `name` | ターゲット名（表示用） |
| `isa` | ISA 識別子（`ak32` / 将来拡張） |
| `cpu` | CPU 種別（`ak32` / 将来拡張） |
| `runtime` | 実行環境（`baremetal` / 将来: `akos`） |
| `entry` | エントリポイントソースファイル |
| `output` | ビルド出力ファイル |
| `load_address` | RAM ロード先アドレス |
| `entry_point` | CPU 実行開始アドレス |

v0.3 では AK32 Baremetal を既定ターゲットとする。複数 ISA の完全対応は v0.5 以降。

#### build 設定フィールド（target.json 内に持たせる案）

```json
{
  "target": { ... },
  "build": {
    "type": "internal_assembler",
    "input": "src/main.asm",
    "output": "build/out/main.bin"
  }
}
```

将来:

```json
{
  "build": {
    "type": "external_command",
    "command": "make",
    "args": ["all"],
    "output": "build/out/kernel.bin"
  }
}
```

v0.3 では既存の AK32 hello.asm → Build → Run → UART "Hi" フローを壊さない範囲で、build 設定を target.json 側へ寄せる計画を立てる。

---

### 2. tools.json の導入

外部アプリ連携の設定をプロジェクト内に持てるようにする。

#### tools.json 仕様案

```json
{
  "tools": {
    "vscode": {
      "command": "code",
      "args": ["{project_root}"]
    },
    "kicad": {
      "command": "kicad",
      "args": ["{project_root}/board/{project_name}.kicad_pro"]
    }
  }
}
```

| フィールド | 説明 |
|---|---|
| `command` | 実行コマンド（PATH 上のコマンド名またはフルパス） |
| `args` | 引数（`{project_root}` / `{project_name}` プレースホルダ対応） |

**v0.3 での対応範囲:**
- `vscode` tool の設定を定義・実装する
- KiCad 設定は定義のみ（実装は v0.5 以降の候補）

**コマンドパス方針（v0.3 確定）:**
- `command` は PATH 上のコマンド名またはフルパスを許可する
- 既定値は `"code"`（PATH 上の `code` コマンドを使用）
- Windows では `code.cmd` / `code.exe`、macOS / Linux では `code` を想定
- ユーザーが `tools.json` の `command` フィールドを上書きすることで OS 差異を吸収できる
- OS 自動検出・設定 UI は v0.5 以降に回す

---

### 3. .vscode/ 生成方針

Unity が VS Code 用のプロジェクトファイルを自動生成するように、AKDev も VS Code 用設定を生成する。

#### 生成候補ファイル

| ファイル | 内容 |
|---|---|
| `.vscode/settings.json` | AKDev プロジェクト向けの VS Code 設定 |
| `.vscode/extensions.json` | 推奨拡張一覧（AKDev Companion を含む） |
| `.vscode/tasks.json` | Build / Run タスク定義（将来用） |

#### extensions.json 案

```json
{
  "recommendations": [
    "akdev.akdev-companion"
  ]
}
```

`akdev.akdev-companion` 拡張本体は v0.4 で作る。v0.3 では推奨拡張として定義だけ書いておく。

#### v0.3 の実装方針

- プロジェクト作成時（`create_project()`）に `.vscode/` を自動生成する
- `settings.json` / `extensions.json` の最小構成を定義する
- `tasks.json` は v0.3 では**生成しない**。Build / Run タスクは v0.5 AKDev VS Code Companion 側で扱う。

---

### 4. 標準プロジェクト構造の拡張

今後の外部ツール連携・自作 OS・基板書き出しに備えて、標準プロジェクト構造を定める。

#### 想定構造

```
project/
├─ project.json       プロジェクトメタ（名前・作成日・バージョン）
├─ system.json        System Canvas（パーツ配置・接続）
├─ target.json        CPU / ISA / build 設定
├─ tools.json         外部ツール設定
├─ src/               ASM / C / 自作言語ソース
├─ hdl/               HDL（Verilog / VHDL 等）
├─ board/             KiCad プロジェクト等
├─ asset/             画像・データ等
├─ build/
│  ├─ out/            ビルド出力バイナリ
│  ├─ rom/            ROM イメージ（将来）
│  └─ export/         実機書き出し（将来）
├─ docs/              ドキュメント
└─ .vscode/           VS Code 設定（自動生成）
```

#### v0.3 での `create_project()` 拡張方針

- `target.json` / `tools.json` の初期ファイルを生成する
- `hdl/` / `board/` / `asset/` / `build/rom/` / `build/export/` / `docs/` ディレクトリを作成する
- `.vscode/` ディレクトリと設定ファイルを生成する
- 既存の `project.json` / `system.json` / `src/` / `build/out/` 生成は維持する

#### 既存プロジェクトとの互換

- `target.json` が存在しないプロジェクトは AK32 Baremetal デフォルトで動作する
- 既存フローを壊さない

---

### 5. Source Type 方針

C 前提にしない。ASM / HDL / C / C++ / 自作言語 / linker script / binary をすべて source type として扱える設計にする。

#### source type 候補

| type | 対象ファイル |
|---|---|
| `asm` | AK32 アセンブリ（`.asm`） |
| `hdl` | Verilog / VHDL（`.v` / `.vhd`） |
| `c` | C ソース（`.c`） |
| `cpp` | C++ ソース（`.cpp` / `.cc` / `.cxx`） |
| `linker` | リンカスクリプト（`.ld`） |
| `binary` | プリビルドバイナリ（`.bin` / `.hex`） |
| `custom` | 自作言語・その他（デフォルト） |

v0.3 では `src_type(path)` 関数（`core/project.py`）として分類構造を実装済み。
C コンパイラ対応・自作言語対応・Build パイプラインへの接続は v0.5 以降。

---

### 6. Build 設定分離

現在は内蔵アセンブラが固定だが、将来的に外部コマンドや自作コンパイラに差し替えられる設計にする。

#### v0.3 での 2 段階設計

| type | 説明 |
|---|---|
| `internal_assembler` | 現状の `asm/asm.py` を使う AK32 内蔵アセンブラ（v0.3 実装済み） |
| `external_command` | 任意の外部コマンドを呼ぶ（v0.3 では未実装 — Log に "not implemented yet" を出して中断） |

v0.3 では `_build()` が target.json の `build.type` を確認し:
- `internal_assembler`: 内蔵アセンブラでビルド
- `external_command`: Log に未実装メッセージを出して中断
- その他: Log に "unsupported build type: <type>" を出して中断

#### build.output の役割と今後の方針

- `build.output` は「既定ビルド出力先」として target.json に記録する
- **active tab ビルド時（v0.3 現在）**: active tab の `source_name` を優先し、出力は `build/out/<stem>.bin` に固定。`build.output` の値は参考情報として扱う
- **Project Build モード（v0.4 以降）**: `build.input` / `build.output` を完全に使い、ターゲット駆動ビルドに移行する

既存の AK32 hello.asm → Build → Run → UART "Hi" フローは v0.3 でも保持する。
target.json が存在しない旧プロジェクトは `load_target()` のフォールバックで AK32 Baremetal デフォルト動作。

---

### 7. v0.5 AKDev VS Code Companion への橋渡し

v0.3 では以下を文書化して完了扱いとする。実装は v0.5 以降。

#### VS Code Companion 将来機能一覧

| 機能 | 概要 |
|---|---|
| VS Code 拡張本体 | AKDev Companion（`akdev.akdev-companion`）の実装 |
| target.json / isa.json 補完 | ISA 定義に基づく ASM / HDL 補完 |
| Build / Run / Reset / Step 要求 | AKDev への操作コマンド送信 |
| Problems 連携 | ビルドエラーを Problems パネルへ表示 |
| Register / UART / Bus Trace 表示 | AKDev の状態を VS Code サイドパネルに表示 |
| .vscode/tasks.json 生成 | Build / Run タスク定義（v0.5 Companion 側で生成） |

#### localhost HTTP / WebSocket 連携案

AKDev 本体が localhost でサーバーを立て、VS Code Companion が接続する構成を想定する。

```json
{
  "protocol": "http+websocket",
  "base_url": "http://localhost:8765",
  "endpoints": {
    "GET /status":    "AKDev 状態（running / halted / project 名等）",
    "POST /build":    "ビルド要求",
    "POST /run":      "実行要求",
    "POST /reset":    "リセット要求",
    "POST /step":     "1ステップ実行要求",
    "GET /registers": "レジスタ状態取得",
    "WS /events":     "状態変化イベント（build_done / run_done / uart_output 等）"
  }
}
```

#### Build / Run / Reset / Step 将来 API 案

```json
// POST /build
{ "target": "default" }

// POST /step
{ "count": 1 }

// GET /registers → response
{
  "pc": 0, "cycle": 10, "halted": true,
  "regs": { "r0": 0, "r1": 72 }
}
```

#### target.json / isa.json を使った補完構想

- `target.json` の `isa` フィールドで ISA 識別子を参照する（例: `"isa": "ak32"`）
- `isa.json`（v0.5 以降で定義）に命令セット・レジスタ名・アドレッシングモードを記述する
- AKDev Companion が `isa.json` を読んで VS Code の ASM 補完・ホバー情報を提供する

#### v0.3 では実装しないこと

- VS Code 拡張本体（`akdev.akdev-companion`）
- localhost HTTP / WebSocket 通信
- ASM / HDL 補完
- Problems 連携（ビルドエラーの VS Code 表示）
- Register / UART / Bus Trace の VS Code パネル表示
- Debug Adapter Protocol 実装

---

## v0.3 でやらないこと

| 項目 | 理由 |
|---|---|
| VS Code 拡張本体の実装 | v0.4 AKDev VS Code Companion で行う |
| KiCad 基板自動生成 | v0.5 以降の候補 |
| KiCad netlist 生成 | v0.5 以降の候補 |
| 自作 OS 本体の実装 | スコープ外 |
| C コンパイラ対応の本格実装 | v0.5 以降の候補 |
| 複数 ISA の完全対応 | v0.5 以降の候補 |
| HDL 合成 | スコープ外 |
| 実機書き込み | スコープ外 |
| GPU / VRAM | スコープ外 |
| 追加命令の大量実装 | v0.3 のスコープではない |

---

## 実装順序

1. **target.json 仕様確定** — 既存 Build フローへの影響を最小化する設計
2. **tools.json 仕様確定** — vscode tool を中心に設計
3. **.vscode/ 生成方針確定** — extensions.json / settings.json の最小構成
4. **標準プロジェクト構造確定** — create_project() の拡張計画
5. **Source Type 方針確定** — 分類構造の設計
6. **Build 設定分離確定** — internal_assembler の設定形式
7. **v0.4 への橋渡し整理** — VS Code Companion の将来 API 案を記録
8. **実装フェーズ** — 計画確定後に実装開始
9. **回帰テスト** — AK32 hello.asm → Build → Run → UART "Hi" フローが通ることを確認

---

## v0.3 完成条件（2026-05-24 全達成）

- [x] ROADMAP4.md / CHECKLIST4.md が作成されている
- [x] target.json の仕様が決まっている
- [x] tools.json の仕様が決まっている
- [x] 標準プロジェクト構造が決まっている
- [x] .vscode/ 生成方針が決まっている（settings.json / extensions.json のみ生成。tasks.json は v0.5 Companion 側）
- [x] v0.5 AKDev VS Code Companion へつながる設計になっている
- [x] 既存の AK32 hello.asm → Build → Run → UART "Hi" フローを壊していない（pytest 159 件全通過）

---

## v0.4 以降の候補

### v0.4 Visual Debug Canvas

- レジスタ / メモリの視覚的デバッグビュー
- System Canvas 上のリアルタイム信号可視化（バス値・ポート状態のオーバーレイ表示）
- ステップ実行時の状態ハイライト
- Memory Viewer（RAM hex ダンプパネル）
- 追加命令（ADD / SUB / LD / ST / JMP / BEQ / CALL / RET / IN）

### v0.5 AKDev VS Code Companion

- VS Code 拡張本体（`akdev.akdev-companion`）
- target.json / isa.json を読んだ ASM / HDL 補完
- AKDev への Build / Run / Reset / Step 要求（コマンド送信）
- Problems パネルへのビルドエラー表示
- Register / UART / Bus Trace の VS Code パネル表示
- localhost HTTP / WebSocket による AKDev との相互連携
- .vscode/tasks.json 生成（Build / Run タスク定義）
- OS 自動検出によるコマンドパス設定 UI

### v0.6 以降の候補（Board / KiCad Foundation）

- KiCad 基板自動生成 / netlist 生成
- C コンパイラ対応（外部コンパイラ連携）
- 複数 ISA 完全対応（自作 ISA の定義ファイル）
- 実機書き込み（シリアル / USB）
- HDL 合成（iverilog / Yosys 連携）
- 自作 OS 対応（`runtime: akos`）

---

## 命令エンコード仕様（現行 v0.1）

```
bits 31..24  opcode
bits 23..16  rd / ra (destination or address register)
bits 15..8   rs       (source register)   [LDI: imm16 high byte]
bits  7..0   imm8                         [LDI: imm16 low byte]
```

| opcode | ニーモニック | 動作 |
|---|---|---|
| 0x00 | NOP | なし |
| 0x01 | HALT | 実行停止 |
| 0x02 | LDI rd, imm16 | regs[rd] = imm16 |
| 0x03 | OUT [rd], rs | bus.write(regs[rd], regs[rs]) |

---

## メモリマップ（仮案）

```
0x0000_0000 - 0x0000_FFFF   Boot ROM / RAM
0x0001_0000 - 0x00FF_FFFF   Main RAM（拡張）
0x2000_0000 - 0x2000_0007   UART
0x2000_0100 - 0x2000_01FF   Timer（未実装）
0x3000_0000 - 0x3000_0FFF   Graphics Registers（未実装）
0x4000_0000 - 0x40FF_FFFF   VRAM Window（未実装）
```
