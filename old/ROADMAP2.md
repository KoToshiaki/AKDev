# AKDev ROADMAP 2

> このドキュメントは、ここまでの実装を前提にした**今後の開発計画**です。
> 初期構想の詳細は `old/ROADMAP.md` を参照してください。
> 進捗管理は `CHECKLIST2.md` で行います。

---

## v0.1 完了（2026-05-23）

v0.1 完了条件「**アセンブリを書いて Build → CPU 実行 → UART に "Hi" が GUI 上で見える**」達成。
統合テスト `tests/test_v01_flow.py` 9 件通過済み。

### v0.1 実装済み一覧

| カテゴリ | 実装内容 |
|---|---|
| GUI 骨組み | QMainWindow / メニュー / ツールバー / 各 Dock パネル |
| Parts Library | `parts/` 再帰スキャン、カテゴリ表示、11 パーツ定義 |
| System Canvas | PartNode 配置・移動・選択・Delete 削除・右クリックメニュー |
| node_id 管理 | `node_0001` 形式、複数同種パーツを個別インスタンスとして管理 |
| Properties パネル | 選択パーツの名前・ID・カテゴリ・説明・ポート・resources 表示 |
| タブエディタ | `.asm` / `.v` タブ、dirty マーク、`build/edit/` への仮保存・再読み込み |
| シンタックスハイライト | `.asm`（キーワード/レジスタ/即値/コメント）/ `.v`（キーワード/数値/コメント） |
| プロジェクト保存 | `project.json` / `system.json` 作成・保存・読み込み |
| Canvas 座標保存 | `export_parts()` / `import_parts()` で位置を system.json に永続化 |
| アセンブラ | `asm/asm.py` — NOP/HALT/LDI/OUT、行番号付きエラー、ラベル（1-pass） |
| Build パイプライン | F5 → アセンブル → `build/out/*.bin` → RAM 自動ロード |
| Part / Bus / Chip / Sim | `core/sim.py` — tracing 機能付き Bus を含む最小シミュレータ基盤 |
| RamPart / UartPart | `core/dev.py` — 32-bit LE RAM、TX UART |
| AK32Part | `core/cpu.py` — NOP/HALT/LDI/OUT、r0 固定ゼロ、halted 状態 |
| Run / Step / Reset / Pause | メニュー + ショートカット（Ctrl+R / F10 / Ctrl+Shift+R / F6） |
| UART Console | QDockWidget（下部タブ）、UartPart.output_text() を表示 |
| Register View | QTableWidget（右側タブ）、pc / cycle / halted / r0〜r15 表示 |
| Bus Trace | QDockWidget（下部タブ）、`[cycle] READ/WRITE addr val part` 形式で記録 |
| サンプルソース | `src/hello.asm` — UART に "Hi" を出力する最小プログラム |
| テスト | 合計 56 件（test_asm×17 / test_build×7 / test_gui_sim_run×21 / test_v01_flow×9 / 他） |

### v0.1 完了条件チェックリスト

- [x] メインウィンドウが開く
- [x] Parts Library が見える
- [x] System Canvas が見える
- [x] chip0 / AK32 / RAM / UART を配置できる
- [x] 右クリックメニューが動く
- [x] `プログラムを開く` でタブが開く
- [x] asm を保存できる
- [x] asm を開き直したとき内容が復元される（B-1 修正済み）
- [x] asm をビルドできる（アセンブラ）
- [x] CPU がプログラムを実行できる
- [x] UART Console に "Hi" が表示される
- [x] Register View が更新される
- [x] Bus Trace に write が出る

---

## v0.2 候補（v0.1 完了後に順番を確定）

詳細は `CHECKLIST2.md` のセクション 3 参照。

### 高優先（実用性向上）

- **追加命令**（ADD / SUB / LD / ST / JMP / BEQ / CALL / RET / IN）— ループや条件分岐を書けるようにする
- **Memory Viewer**（RAM の hex ダンプパネル）— 実行中のメモリ状態を視覚化
- **アセンブラ強化**（2-pass ラベル前方参照、disasm）

### 中優先（ツール完成度）

- ポート表示（Canvas 上のノードにポートを描画）
- 接続線（ポート間のエッジ描画・system.json 保存）
- Timer パーツ（`core/dev.py` に追加）
- project.json の不正 JSON エラーハンドリング

### 低優先（UX 改善）

- グリッド表示・スナップ
- キャンバス拡大縮小
- パーツ設定編集（ベースアドレス、サイズ）

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
