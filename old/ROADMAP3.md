# AKDev ROADMAP 3

> v0.2 以降の開発計画。
> v0.1 完了時点の計画は `old/ROADMAP2.md` を参照。
> 進捗管理は `CHECKLIST3.md` で行う。

---

## v0.1 到達点（2026-05-23 完了）

完了条件「**アセンブリを書いて Build → CPU 実行 → UART に "Hi" が GUI 上で見える**」達成。
統合テスト `tests/test_v01_flow.py` 9 件通過。

### v0.1 実装済み一覧

| カテゴリ | 実装内容 |
|---|---|
| GUI 骨組み | QMainWindow / メニュー / ツールバー / Dock（Parts Library / Properties / Register View / Log / UART Console / Bus Trace） |
| Parts Library | `parts/` 再帰スキャン、カテゴリ表示、11 パーツ定義 |
| System Canvas | PartNode 配置・移動・選択・削除・右クリックメニュー |
| node_id 管理 | `node_0001` 形式、同種複数パーツを個別インスタンスとして管理 |
| Properties パネル | 選択パーツの名前・ID・カテゴリ・説明・ポート・resources 表示 |
| タブエディタ | `.asm` / `.v`、dirty マーク、`build/edit/` 仮保存・再読み込み |
| シンタックスハイライト | `.asm`（キーワード/レジスタ/即値/コメント）/ `.v`（キーワード/数値/コメント） |
| プロジェクト保存 | `project.json` / `system.json` 作成・保存・読み込み |
| アセンブラ | `asm/asm.py` — NOP/HALT/LDI/OUT、行番号付きエラー、ラベル（1-pass） |
| Build パイプライン | F5 → アセンブル → `build/out/*.bin` → RAM 自動ロード |
| シミュレータ基盤 | `core/sim.py` — tracing 付き Bus を含む最小構成 |
| AK32Part | `core/cpu.py` — NOP/HALT/LDI/OUT、r0 固定ゼロ、halted 状態 |
| Run / Step / Reset | メニュー + ショートカット（Ctrl+R / F10 / Ctrl+Shift+R） |
| UART Console | QDockWidget（下部タブ）、UartPart の出力を表示 |
| Register View | QTableWidget（右側タブ）、pc / cycle / halted / r0〜r15 表示 |
| Bus Trace | QDockWidget（下部タブ）、`[cycle] READ/WRITE addr val part` 形式で記録 |
| サンプルソース | `src/hello.asm` — UART に "Hi" を出力 |
| テスト | 56 件（asm×17 / build×7 / gui_sim_run×21 / v01_flow×9 / 他） |

---

## v0.2 テーマ: Workspace UI Refinement

### 目的

v0.1 で完成した最小 CPU シミュレータを、実際に使いやすい開発環境へ整理する。
機能追加ではなく、**UI/UX の整合性・使い勝手**を改善するバージョン。

---

## v0.2 でやること

### 1. View メニューから閉じた Dock を再表示できるようにする

現状、Dock を閉じると再表示する手段がない。View メニューにトグルアクションを追加し、全パネルを復元可能にする。

対象パネル:
- Parts Library
- Properties
- Register View
- Log / Console
- UART Console
- Bus Trace

### 2. ツールバーを整理し、Ribbon 風コマンドバーへ移行する

**v0.2 の最終 UI 方針: 通常のツールバーではなく、Ribbon 風コマンドバーを導入する。**

PowerPoint / Autodesk Inventor のように、カテゴリタブで操作をまとめたコマンドバーを上部に配置する。

#### 2a. ツールバーの暫定整理（完了済み）

通常ツールバーとして以下の構成を実装済み（Ribbon 移行前の中間状態）:

- Project 系（Open / Save）→ セパレータ → Execution 系（Build / Reset / Run / Step）
- New Project と Pause はメニュー側に移動済み

#### 2b. Ribbon 風コマンドバーの設計

カテゴリタブ構成:

| タブ | ボタン |
|---|---|
| **Project** | New Project / Open Project / Save Project |
| **Build / Run** | Build / Reset / Run / Step / Pause |
| **View** | Parts Library / Properties / Register View / Log / UART Console / Bus Trace（各トグル） |
| **Tools** | Open Project in VS Code / Open Current ASM in VS Code / Open Current HDL in VS Code |

実装方針:
- Qt 標準の `QTabBar` + `QWidget` スタック、または `QStackedWidget` でカテゴリパネルを切り替える
- 既存の `QAction` をそのまま再利用し、ボタンは `QToolButton` で包む
- 既存のメニューバーはリボンと共存させるか、リボン完成後に簡略化する
- ショートカット（F5 / Ctrl+R / F10 / Ctrl+Shift+R 等）は変更しない

### 3. Parts Library の表示方式を改善する

Parts Library を常時 Dock 表示しなくても使える形にする。

- View メニュー / ツールバーボタンから再表示できれば最低限 OK
- 可能なら別ウィンドウ / ダイアログ化も検討する
- ただし、最初は Dock の再表示対応（上記 #1）を優先する

### 4. VS Code 連携（v0.3 以降に延期）

外部アプリ連携は v0.3 以降で扱う。v0.2 では実装しない。

- Open Project in VS Code（プロジェクトフォルダを VS Code で開く）
- Open Current ASM in VS Code（アクティブ .asm タブを VS Code で開く）
- `code` コマンドが使えない場合は Log にエラー表示

### 5. 初期レイアウト（現状で許容）

確認結果（2026-05-24）: Canvas 幅 = ウィンドウ幅の 59%。目安 60% にほぼ到達し、現状で許容。
追加実装は v0.3 以降の必要時に対応する。

### 6. 既存の v0.1 フローを壊さない

以下のフローが v0.2 終了後も動作すること:

- Build（F5）
- RAM ロード
- Reset（Ctrl+Shift+R）
- Run（Ctrl+R）
- UART Console に "Hi" が表示される
- Register View が更新される
- Bus Trace に write が出る

---

## v0.2 でやらないこと

- 追加命令（ADD / SUB / LD / ST / JMP / BEQ / CALL / RET / IN）
- Memory Viewer（RAM hex ダンプパネル）
- Canvas 接続線の本格実装
- GPU / VRAM
- 実機出力
- HDL 合成

---

## 実装順序

1. **View メニュー改善**（Dock 再表示トグル）— UI 整合性の基盤
2. **ツールバー整理**（Project系 / Execution系 に分割）— 視覚的整理
3. **Parts Library 改善**（Dock 再表示対応を優先、ダイアログ化は検討）
4. **VS Code 連携**（`subprocess` で `code` コマンドを呼ぶ）
5. **初期レイアウト改善**（Canvas 中心、不要 Dock を初期非表示）
6. **v0.1 回帰テスト**（全フロー確認）

---

## v0.2 完成条件

- [x] 閉じた全 Dock を View メニューから再表示できる
- [x] Ribbon 風コマンドバーで操作がまとまっている（File / Build-Run / View / Tools タブ）
- [x] Project Dialog — New / Open / Save / Save As がダイアログ経由でユーザーが場所を選べる
- [x] 初期表示で System Canvas が十分な広さを持つ（59%、現状許容）
- [x] v0.1 統合フロー（Build→Run→UART "Hi"→Register View→Bus Trace）が通る（pytest 120 件）
- ~~[ ] VS Code でプロジェクト / ASM / HDL を開けるメニューがある~~ → v0.3 以降に延期

---

## v0.3 以降の候補

### 外部ツール連携（v0.3 以降）

- **VS Code 連携**（Open Project / ASM / HDL in VS Code — `subprocess` で `code` コマンド）
- **自作 ISA 設定**（tools.json / target.json でアセンブラ・エミュレータを差し替え可能にする）

### 機能拡張

- **追加命令**（ADD / SUB / LD / ST / JMP / BEQ / CALL / RET / IN）— ループ・条件分岐
- **Memory Viewer**（RAM hex ダンプパネル）— デバッグ効率向上
- **アセンブラ強化**（2-pass ラベル前方参照、disasm）
- **ポート描画 + 接続線**（Canvas の視覚強化）
- **Timer パーツ**（`core/dev.py` に TimerPart 追加）
- **Graphics Register + VRAM + Virtual Screen**（グラフィック出力）
- **実機エクスポート**（Verilog 雛形、メモリマップ出力）

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

---

## ディレクトリ構成

```
AKdev/
├─ main.py
├─ core/
│  ├─ sim.py       Part / Port / Bus / Chip / Sim
│  ├─ dev.py       RamPart / UartPart
│  ├─ cpu.py       AK32Part
│  └─ project.py   project.json / system.json 管理
├─ asm/
│  └─ asm.py       AK32 アセンブラ
├─ ui/
│  ├─ win.py       MainWin
│  ├─ canvas.py    Canvas / PartNode
│  ├─ lib.py       load_parts() / cat_label()
│  ├─ prop.py      PropPanel
│  ├─ editor.py    EditorTabs
│  └─ highlighter.py AsmHighlighter / VerilogHighlighter
├─ parts/          part.json × 11
├─ spec/           仕様書
├─ src/            hello.asm
├─ tests/          テスト一式
├─ old/            旧計画書（ROADMAP.md / CHECKLIST.md / ROADMAP2.md / CHECKLIST2.md）
└─ build/          gitignore 対象
```
