# AKDev 引き継ぎメモ

更新日: 2026-05-22

---

## ドキュメント体系

| ファイル | 役割 |
|---|---|
| `ROADMAP2.md` | **メイン計画書**（現在の到達点 / v0.1 残り / v0.2 以降） |
| `CHECKLIST2.md` | **メインチェックリスト**（残り作業・完了条件付き） |
| `HANDOFF.md` | このファイル — セッション間引き継ぎ |
| `old/ROADMAP.md` | 参照用（初期構想の詳細）、通常の進捗管理には使わない |
| `old/CHECKLIST.md` | 参照用（旧全項目リスト）、通常の進捗管理には使わない |

---

## 現在のブランチ

`dev`（clean）

直近のコミット:
```
c5cf889 core: add minimal ak32 cpu
de55821 core: add ram and uart devices
942ada9 core: add minimal simulator classes
7e5b5b1 ui: connect project save and open
74875f9 core: save canvas part positions
```

---

## 現在の到達点

### 完了済み

| カテゴリ | 詳細 |
|---|---|
| GUI 骨組み | QMainWindow / メニュー / ツールバー / Dock（左: Parts Library, 右: Properties, 下: Log） |
| Parts Library | `parts/` 再帰スキャン, カテゴリ表示, 11 パーツ定義 |
| System Canvas | PartNode 配置・移動・選択・Delete 削除・右クリックメニュー（複製・削除・タブ開くが動作） |
| node_id 管理 | `node_0001` 形式, 同種複数パーツをインスタンス別に管理 |
| Properties パネル | 選択パーツの名前・ID・カテゴリ・説明・ポート・resources 表示 |
| タブエディタ | `.asm` / `.v` タブ, dirty マーク（`*`）, `build/edit/<node_id>.<ext>` への仮保存 |
| シンタックスハイライト | .asm（キーワード/レジスタ/即値/コメント）/ .v（キーワード/数値/コメント） |
| 現在行ハイライト | ExtraSelections による薄黄色ライン |
| プロジェクト保存 | `project.json` / `system.json` 作成・保存・読み込み（File メニュー + Ctrl+S） |
| Canvas 座標保存 | `export_parts()` / `import_parts()` で位置を system.json に永続化 |
| シミュレータ基盤 | `core/sim.py` — Part / Port / Bus / Chip / Sim |
| RamPart | `core/dev.py` — 32-bit LE word 読み書き, 範囲外 BusError, load_bytes, dump |
| UartPart | `core/dev.py` — TX バッファ, CR/LF 正規化, status レジスタスタブ, output_text() |
| AK32Part | `core/cpu.py` — NOP/HALT/LDI/OUT, r0 固定ゼロ, Z フラグ, halted 状態, reset_pc |
| ヘッドレステスト | Bus フェッチ + load_bytes で UART に "Hi" を出力するテスト通過済み |

---

## 主要ファイル一覧

| ファイル | 役割 |
|---|---|
| `main.py` | エントリーポイント |
| `ui/win.py` | MainWin — レイアウト・メニュー・ツールバー・プロジェクト操作 |
| `ui/canvas.py` | Canvas / PartNode — 配置・移動・選択・コンテキストメニュー |
| `ui/editor.py` | EditorTabs — タブエディタ、dirty 管理、仮保存 |
| `ui/prop.py` | PropPanel — Properties パネル |
| `ui/highlighter.py` | AsmHighlighter / VerilogHighlighter / attach 系ヘルパー |
| `ui/lib.py` | load_parts() / cat_label() |
| `core/sim.py` | Part / Port / Bus / BusError / Chip / Sim |
| `core/dev.py` | RamPart / UartPart |
| `core/cpu.py` | AK32Part（最小 CPU エミュレータ） |
| `core/project.py` | create_project / save_system / load_project |
| `parts/*/part.json` | パーツ定義 11 種 |

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

アセンブラ実装時はこのエンコードに合わせること。

---

## 既知バグ

| # | 症状 | 原因 | 対応予定 |
|---|---|---|---|
| B-1 | タブを閉じて再度「プログラムを開く」すると内容が消える | `open_tab()` が `build/edit/<node_id>.<ext>` を読み込んでいない | v0.1 仕上げ前に最優先で修正 |

---

## 次にやるべき作業

`CHECKLIST2.md` の「1. v0.1 仕上げ」セクションを上から順に進める。

1. **1.1 エディタ再読み込み（バグ B-1 修正）** ← 最優先
2. **1.2 最小アセンブラ**（`asm/asm.py` 新規作成）
3. **1.3 Build ボタン接続**
4. **1.4 RAM ロード**
5. **1.5 GUI Sim 実行**（Run / Step / Reset）
6. **1.6 UART Console**
7. **1.7 Register View**
8. **1.8 Bus Trace**
9. **1.9 v0.1 統合テスト**

---

## 次回 Claude Code に最初に入れる指示文

```
HANDOFF.md、ROADMAP2.md、CHECKLIST2.md を読んで現在の状態を確認してください。
今後の開発は ROADMAP2.md と CHECKLIST2.md を使って進めます。

前回の作業で、以下が完了しています:
- GUI 骨組み、Parts Library、System Canvas、node_id 管理
- Properties パネル、タブエディタ、シンタックスハイライト
- プロジェクト保存・読み込み
- core/sim.py（Part / Bus / Chip / Sim）
- core/dev.py（RamPart / UartPart）
- core/cpu.py（AK32Part — NOP/HALT/LDI/OUT）
- ヘッドレステスト: RAM + Bus + UART で "Hi" 出力確認済み

既知バグが 1 件あります（B-1）:
- タブを閉じて再度「プログラムを開く」すると内容が消える
- 原因: ui/editor.py の open_tab() が build/edit/<node_id>.<ext> を読み込んでいない

今回は CHECKLIST2.md の「1.1 エディタ再読み込み（バグ B-1 修正）」を進めてください。

作業内容:
1. ui/editor.py の open_tab() を修正してください。
   - build/edit/<node_id>.<ext> が存在する場合、その内容を editor に読み込んでください。
   - ファイルがない場合は空のままで構いません（現在の動作と同じ）。
2. 動作確認の手順をヘッドレステストで確認してください（GUI 不要）。
   - EditorTabs.open_tab() を呼ぶ
   - テキストを入力して save_current() を呼ぶ
   - _close_tab() で閉じる
   - 同じ node_id + ext で open_tab() を再度呼ぶ
   - editor の内容が復元されていることを確認する
3. CHECKLIST2.md の 1.1 を [x] に更新してください。
4. commit してください（message: fix: reload saved editor content on tab open）

その後、余裕があれば CHECKLIST2.md の「1.2 最小アセンブラ」に進んでください。
```

---

## セッション記録

### セッション 1〜5（2026-05-22）

GUI 骨組み → Parts Library → Canvas → node_id 管理 → Properties → タブエディタ →
シンタックスハイライト → プロジェクト保存 → シミュレータ基盤 → RamPart / UartPart → AK32Part

### セッション 6（2026-05-22）

- `ROADMAP2.md` / `CHECKLIST2.md` を新規作成（旧ファイルを `old/` にコピー）
- `HANDOFF.md` を最新状態に更新
- 次回セッションは B-1 バグ修正から
