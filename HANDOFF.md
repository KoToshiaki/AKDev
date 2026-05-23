# AKDev 引き継ぎメモ

更新日: 2026-05-23

---

## ドキュメント体系

| ファイル | 役割 |
|---|---|
| `ROADMAP2.md` | **メイン計画書**（v0.1 完了 / v0.2 以降の計画） |
| `CHECKLIST2.md` | **メインチェックリスト**（残り作業・完了条件付き） |
| `HANDOFF.md` | このファイル — セッション間引き継ぎ |
| `old/ROADMAP.md` | 参照用（初期構想の詳細）、通常の進捗管理には使わない |
| `old/CHECKLIST.md` | 参照用（旧全項目リスト）、通常の進捗管理には使わない |

---

## 現在のブランチ

`dev`（clean）

直近のコミット:
```
4b87818 test: add v0.1 integration flow
4f9acda ui: add bus trace panel
ec32d79 ui: add register view panel
f37a40b ui: add uart console panel
5817330 ui: add basic simulator run controls
2b22894 ui: load built binary into simulator ram
ed35da2 ui: connect build action to assembler
75e39f0 asm: add minimal ak32 assembler
01ec726 fix: reload saved editor content on tab open (B-1)
```

---

## v0.1 完了（2026-05-23）

v0.1 の完了条件「**アセンブリを書いて Build → CPU 実行 → UART に "Hi" が GUI 上で見える**」をすべて達成済み。

### 完了済み（v0.1 までの全実装）

| カテゴリ | 詳細 |
|---|---|
| GUI 骨組み | QMainWindow / メニュー / ツールバー / Dock（左: Parts Library, 右: Properties + Register View, 下: Log + UART Console + Bus Trace） |
| Parts Library | `parts/` 再帰スキャン, カテゴリ表示, 11 パーツ定義 |
| System Canvas | PartNode 配置・移動・選択・Delete 削除・右クリックメニュー |
| node_id 管理 | `node_0001` 形式, 同種複数パーツをインスタンス別に管理 |
| Properties パネル | 選択パーツの名前・ID・カテゴリ・説明・ポート・resources 表示 |
| タブエディタ | `.asm` / `.v` タブ, dirty マーク（`*`）, `build/edit/<node_id>.<ext>` への仮保存・再読み込み（B-1 修正済み） |
| シンタックスハイライト | .asm（キーワード/レジスタ/即値/コメント）/ .v（キーワード/数値/コメント） |
| プロジェクト保存 | `project.json` / `system.json` 作成・保存・読み込み（File メニュー + Ctrl+S） |
| Canvas 座標保存 | `export_parts()` / `import_parts()` で位置を system.json に永続化 |
| アセンブラ | `asm/asm.py` — NOP/HALT/LDI/OUT の 4 命令、行番号付きエラー、ラベル（1-pass）、16 進即値 |
| Build パイプライン | F5 でアクティブ .asm タブをアセンブル → `build/out/<node_id>.bin` 保存 → RAM 自動ロード |
| シミュレータ基盤 | `core/sim.py` — Part / Port / Bus（tracing 付き）/ Chip / Sim |
| RamPart | `core/dev.py` — 32-bit LE word 読み書き, 範囲外 BusError, load_bytes |
| UartPart | `core/dev.py` — TX バッファ, CR/LF 正規化, status レジスタスタブ |
| AK32Part | `core/cpu.py` — NOP/HALT/LDI/OUT, r0 固定ゼロ, Z フラグ, halted 状態 |
| Bus Trace | Bus に `tracing` + `cycle_fn` を追加。`[cycle] READ/WRITE addr val part` 形式で記録 |
| Run / Step / Reset | `_do_run()` 最大 1000 step HALT 停止 / `_do_step()` 1 命令 / `_do_reset()` CPU+UART リセット（RAM 保持） |
| UART Console | QDockWidget（下部タブ）、Run/Step 後に `output_text()` を反映、Reset でクリア |
| Register View | QTableWidget（右側タブ）、pc / cycle / halted / r0〜r15 を表示、Run/Step/Reset 後に更新 |
| Bus Trace パネル | QDockWidget（下部タブ）、Step/Run 後に更新、Reset/Build でクリア |
| サンプルソース | `src/hello.asm` — "Hi" を UART に出力する最小プログラム |
| 統合テスト | `tests/test_v01_flow.py` — 9 件（file 存在 / assemble / UART / Register / Bus Trace） |

---

## 主要ファイル一覧

| ファイル | 役割 |
|---|---|
| `main.py` | エントリーポイント |
| `ui/win.py` | MainWin — レイアウト・メニュー・ツールバー・Run コントロール・全パネル更新 |
| `ui/canvas.py` | Canvas / PartNode — 配置・移動・選択・コンテキストメニュー |
| `ui/editor.py` | EditorTabs — タブエディタ、dirty 管理、仮保存、再読み込み |
| `ui/prop.py` | PropPanel — Properties パネル |
| `ui/highlighter.py` | AsmHighlighter / VerilogHighlighter |
| `ui/lib.py` | load_parts() / cat_label() |
| `core/sim.py` | Part / Port / Bus（tracing）/ BusError / Chip / Sim |
| `core/dev.py` | RamPart / UartPart |
| `core/cpu.py` | AK32Part（最小 CPU エミュレータ） |
| `core/project.py` | create_project / save_system / load_project |
| `asm/asm.py` | AK32 アセンブラ（assemble() / AsmError） |
| `src/hello.asm` | "Hi" 出力サンプルプログラム |
| `parts/*/part.json` | パーツ定義 11 種 |
| `tests/test_editor_reload.py` | エディタ再読み込みテスト |
| `tests/test_asm.py` | アセンブラ単体テスト（17 件） |
| `tests/test_build.py` | Build パイプラインテスト（7 件） |
| `tests/test_sim_load.py` | シミュレータ基盤テスト |
| `tests/test_gui_sim_run.py` | GUI Sim 実行テスト（21 件） |
| `tests/test_v01_flow.py` | v0.1 統合フローテスト（9 件） |

### SPDX ヘッダのルール

全 Python ソースファイルの先頭:
```python
# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
```

---

## 命令エンコード仕様（AK32 現行）

```
bits 31..24  opcode
bits 23..16  rd / ra  (destination or address register)
bits 15..8   rs        (source register)  [LDI: imm16 high byte]
bits  7..0   imm8                         [LDI: imm16 low byte]
```

| opcode | ニーモニック | 動作 |
|---|---|---|
| 0x00 | NOP | なし |
| 0x01 | HALT | 実行停止（pc は HALT 位置を指す） |
| 0x02 | LDI rd, imm16 | regs[rd] = imm16（bits 15:0） |
| 0x03 | OUT [rd], rs | bus.write(regs[rd], regs[rs]) |

---

## 既知バグ・技術的負債

| # | 症状 | 優先度 |
|---|---|---|
| B-2 | Ctrl+S でキャンバスと現在タブの両方が保存されるが責務が不明確 | 低 |
| B-3 | project.json が壊れていると例外でクラッシュ | 低 |
| B-4 | タブが 0 枚の状態で Ctrl+S するとエラーの可能性 | 低 |

---

## v0.2 以降の方向性

CHECKLIST2.md のセクション 3（v0.2 候補）を参照。有力候補:

1. **追加命令 + アセンブラ強化**（ADD/SUB/LD/ST/JMP/BEQ/CALL/RET/IN）— CPU の実用性向上
2. **Memory Viewer**（RAM hex ダンプパネル）— デバッグ効率向上
3. **ポート描画 + 接続線**（Canvas の視覚強化）— ツールとしての完成度向上

---

## 次回 Claude Code に最初に入れる指示文

```
HANDOFF.md、ROADMAP2.md、CHECKLIST2.md を読んで現在の状態を確認してください。

v0.1 は完了しています。次は v0.2 の作業に進みます。
CHECKLIST2.md のセクション 3 または 4 を参照してください。

今回取り組む作業を指示します:
[ここに具体的な作業内容を入れる]
```

---

## セッション記録

### セッション 1〜5（2026-05-22）

GUI 骨組み → Parts Library → Canvas → node_id 管理 → Properties → タブエディタ →
シンタックスハイライト → プロジェクト保存 → シミュレータ基盤 → RamPart / UartPart → AK32Part

### セッション 6（2026-05-22）

- `ROADMAP2.md` / `CHECKLIST2.md` を新規作成（旧ファイルを `old/` にコピー）
- `HANDOFF.md` を更新
- B-1 バグ（エディタ再読み込み）を修正

### セッション 7〜11（2026-05-23）

- 1.2: アセンブラ (`asm/asm.py`) 実装
- 1.3: Build ボタンとアセンブラ接続
- 1.4: asm → binary → RAM ロード
- 1.5: Run / Step / Reset / Pause 実装
- 1.6: UART Console パネル追加
- 1.7: Register View パネル追加
- 1.8: Bus Trace（Bus への tracing 機能 + パネル）追加
- 1.9: `src/hello.asm` 作成 + `tests/test_v01_flow.py` 統合テスト
- **v0.1 完了**
