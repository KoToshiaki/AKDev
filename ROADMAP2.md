# AKDev ROADMAP 2

> このドキュメントは、ここまでの実装を前提にした**今後の開発計画**です。
> 初期構想の詳細は `old/ROADMAP.md` を参照してください。
> 進捗管理は `CHECKLIST2.md` で行います。

---

## 現在の到達点（2026-05-22）

### 完了済み

| カテゴリ | 実装内容 |
|---|---|
| GUI 骨組み | QMainWindow / メニュー / ツールバー / 各 Dock パネル |
| Parts Library | `parts/` 再帰スキャン、カテゴリ表示、11 パーツ定義 |
| System Canvas | PartNode 配置・移動・選択・Delete 削除・右クリックメニュー |
| node_id 管理 | `node_0001` 形式、複数同種パーツを個別インスタンスとして管理 |
| Properties パネル | 選択パーツの名前・ID・カテゴリ・説明・ポート・resources 表示 |
| タブエディタ | `.asm` / `.v` タブ、dirty マーク、`build/edit/` への仮保存 |
| シンタックスハイライト | `.asm`（キーワード/レジスタ/即値/コメント）/ `.v`（キーワード/数値/コメント） |
| 現在行ハイライト | `ExtraSelections` による薄黄色ライン |
| プロジェクト保存 | `project.json` / `system.json` 作成・保存・読み込み |
| Canvas 座標保存 | `export_parts()` / `import_parts()` で位置を system.json に永続化 |
| Part / Bus / Chip / Sim | `core/sim.py` — 最小シミュレータ基盤 |
| RamPart | `core/dev.py` — 32-bit LE word 読み書き、範囲外 BusError、load_bytes |
| UartPart | `core/dev.py` — TX バッファ、CR/LF 正規化、status レジスタスタブ |
| AK32Part | `core/cpu.py` — NOP/HALT/LDI/OUT、r0 固定ゼロ、Z フラグ、halted 状態 |
| ヘッドレステスト | load_bytes + Bus フェッチで UART に "Hi" を出力するテスト済み |

---

## 既知バグ

| # | 症状 | 原因 | 対応予定 |
|---|---|---|---|
| B-1 | タブを閉じて再度「プログラムを開く」すると内容が消える | `open_tab()` が `build/edit/<node_id>.<ext>` を読み込んでいない | v0.1 仕上げ前に修正（最優先） |

---

## v0.1 残り作業

v0.1 の完了条件: **アセンブリを書いて Build → CPU 実行 → UART に "Hi" が GUI 上で見える**

### 優先順

| 順 | 作業 | 依存 |
|---|---|---|
| 1 | **エディタ再読み込み** (B-1 修正) | なし |
| 2 | **最小アセンブラ** (`asm/asm.py`) | なし |
| 3 | **Build ボタンとアセンブラの接続** | 2 |
| 4 | **asm → binary → RAM ロード** | 2, 3 |
| 5 | **GUI から Sim 実行** (Run/Step/Reset) | 4 |
| 6 | **UART Console** (出力表示パネル) | 5 |
| 7 | **Register View** (r0〜r15, pc 表示) | 5 |
| 8 | **Bus Trace** (write ログ表示) | 5 |
| 9 | **v0.1 統合テスト** | 1〜8 |

---

## v0.1 完了条件チェックリスト

- [ ] メインウィンドウが開く ✅
- [ ] Parts Library が見える ✅
- [ ] System Canvas が見える ✅
- [ ] chip0 / AK32 / RAM / UART を配置できる ✅
- [ ] 右クリックメニューが動く ✅
- [ ] `プログラムを開く` でタブが開く ✅
- [ ] asm を保存できる ✅
- [ ] **asm を開き直したとき内容が復元される** ← B-1 修正
- [ ] **asm をビルドできる（アセンブラ）**
- [ ] **CPU がプログラムを実行できる**
- [ ] **UART コンソールに "Hi" が表示される**
- [ ] **Register View が更新される**
- [ ] **Bus Trace に write が出る**

---

## v0.2 候補

実装難易度と優先度で整理。v0.1 完了後に順番を確定する。

### 高優先

- ポート表示（Canvas 上のノードにポートを描画）
- 接続線（ポート間のエッジ描画・system.json 保存）
- Memory Viewer（RAM の hex ダンプ表示）
- Timer パーツ（`core/dev.py` に追加）
- 追加命令（ADD / SUB / LD / ST / JMP / BEQ / CALL / RET / IN）

### 中優先

- アセンブラ強化（ラベル、エラー行番号、2-pass）
- project.json の不正 JSON エラーハンドリング
- パーツ設定編集（ベースアドレス、サイズ、名前）
- system.json のパーツ設定保存

### 低優先

- グリッド表示・スナップ
- キャンバス拡大縮小
- プロジェクトウィザード（プリセット選択）
- 自作パーツテンプレート生成

---

## v0.3 以降（長期）

- Graphics Register パーツ
- VRAM / Virtual Screen
- Tile Engine / Sprite Engine
- アセットツール（PNG → タイル変換）
- ROM Builder
- 実機エクスポート（Verilog 雛形、メモリマップ出力）
- UART 実機接続

---

## 命令エンコード仕様（現行）

32-bit 固定長。アセンブラ実装時にここに合わせる。

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
├─ asm/            (未実装) asm.py / tok.py / enc.py
├─ ui/
│  ├─ win.py       MainWin
│  ├─ canvas.py    Canvas / PartNode
│  ├─ lib.py       load_parts() / cat_label()
│  ├─ prop.py      PropPanel
│  ├─ editor.py    EditorTabs
│  └─ highlighter.py AsmHighlighter / VerilogHighlighter
├─ parts/          part.json × 11
├─ spec/           仕様書
├─ old/            旧 ROADMAP.md / CHECKLIST.md
└─ build/          gitignore 対象
```
