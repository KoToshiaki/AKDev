# AKDev 引き継ぎメモ

更新日: 2026-05-30（セッション 36）

---

## ドキュメント体系

| ファイル | 役割 |
|---|---|
| `ROADMAP5.md` | **現在の優先作業**: v0.4 Visual Debug Canvas の設計書 |
| `CHECKLIST5.md` | **現在の優先作業**: v0.4 Visual Debug Canvas のチェックリスト |
| `old/ROADMAP4.md` | v0.3 Project & Target Foundation の設計書（完了・アーカイブ） |
| `old/CHECKLIST4.md` | v0.3 Project & Target Foundation のチェックリスト（完了・アーカイブ） |
| `HANDOFF.md` | このファイル — セッション間引き継ぎ |
| `old/ROADMAP3.md` | v0.2 Workspace UI Refinement の計画（完了・アーカイブ） |
| `old/CHECKLIST3.md` | v0.2 UI 改善のチェックリスト（完了・アーカイブ） |
| `old/PATCH_PROJECT_DIALOG_ROADMAP.md` | Project Dialog パッチ設計書（完了・アーカイブ） |
| `old/PATCH_PROJECT_DIALOG_CHECKLIST.md` | Project Dialog パッチチェックリスト（完了・アーカイブ） |
| `old/PATCH_SAVE_ROADMAP.md` | 保存仕様修正パッチの設計書（完了・アーカイブ） |
| `old/PATCH_SAVE_CHECKLIST.md` | 保存仕様修正パッチのチェックリスト（完了・アーカイブ） |
| `old/ROADMAP2.md` | 参照用（v0.1 完了時点の計画） |
| `old/CHECKLIST2.md` | 参照用（v0.1 完了時点のチェックリスト） |
| `old/ROADMAP.md` | 参照用（初期構想の詳細） |
| `old/CHECKLIST.md` | 参照用（旧全項目リスト） |

---

## 現在のブランチ

`dev`（clean）

直近のコミット:
```
e47f6a6 docs: mark v0.1 complete
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

v0.1 完了条件「**アセンブリを書いて Build → CPU 実行 → UART に "Hi" が GUI 上で見える**」達成済み。
統合テスト `tests/test_v01_flow.py` 9 件通過済み。

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

## 保存仕様修正パッチ（完了）

`old/PATCH_SAVE_ROADMAP.md` / `old/PATCH_SAVE_CHECKLIST.md` に記録済み（アーカイブ）。
自動テスト 105 件通過。手動確認（UART Hi / タブ名確認）は次回以降。

---

## v0.2 Workspace UI Refinement（完了）

**2026-05-24 完了確認。**

### v0.2 で完了した内容

| 項目 | 状態 |
|---|---|
| View メニュー Dock トグル（全 6 パネル） | ✅ 完了 |
| Ribbon 風コマンドバー（File / Build-Run / View / Tools タブ） | ✅ 完了 |
| メニューバーと Ribbon の重複整理（File メニューのみ残存） | ✅ 完了 |
| Project Dialog（New / Open / Save / Save As、ダイアログ選択式） | ✅ 完了 |
| 保存仕様修正（project_root/src/ 分離、build/out/ 分離） | ✅ 完了 |
| 初期レイアウト（Canvas 幅 59%、現状許容） | ✅ 許容 |
| v0.1 回帰テスト（pytest 120 件、headless フロー確認） | ✅ 完了 |
| VS Code 連携 | ⏩ v0.3 以降に延期 |
| Parts Library ダイアログ化 | ⏩ v0.3 以降に延期 |

### 回帰テスト結果（2026-05-24）

- `pytest tests/` 120 件 PASSED（0 件 FAILED）
- headless フロー: New Project → AK32 CPU 配置 → Build → Reset → Run → UART "Hi" → Register View → Bus Trace 全通過

---

## v0.3 Project & Target Foundation（2026-05-24 完了）

### v0.3 の位置づけ

**v0.3 は v0.5 AKDev VS Code Companion の下準備バージョン。**
（v0.4 は Visual Debug Canvas に変更。VS Code Companion は v0.5 に移動。KiCad / Board 連携は v0.6 以降。）

AKDev と VS Code の関係は **Unity と VS Code のような関係**を目指す:
- AKDev 本体 = Unity Editor 側（プロジェクト管理 / Canvas / Build / Run / Target 設定）
- VS Code = コード編集側（ASM / HDL 編集 / 補完 / Git）

### v0.3 完了内容まとめ

| パッチ / 作業 | 状態 |
|---|---|
| ROADMAP4.md / CHECKLIST4.md 作成 | ✅ 完了 |
| Project Scaffold パッチ | ✅ 完了 |
| Build Target Wiring パッチ | ✅ 完了 |
| pytest 159 件全通過 | ✅ 完了 |
| target.json 仕様確定 | ✅ 完了 |
| tools.json 仕様確定（コマンドパス方針含む） | ✅ 完了 |
| 標準プロジェクト構造確定 | ✅ 完了 |
| .vscode/ 生成方針確定（settings.json / extensions.json のみ） | ✅ 完了 |
| v0.5 VS Code Companion への橋渡し文書化 | ✅ 完了 |
| ROADMAP4.md / CHECKLIST4.md 完了更新 | ✅ 完了 |

### tools.json コマンドパス方針

- `command` は PATH 上のコマンド名またはフルパスを許可する。既定値は `"code"`
- Windows では `code.cmd` / `code.exe`、macOS/Linux では `code` を想定
- ユーザーが `tools.json` の `command` フィールドを上書きすることで OS 差異を吸収できる
- OS 自動検出・設定 UI は v0.5 以降

### .vscode/ 生成方針

- `settings.json` / `extensions.json` のみ生成済み
- `tasks.json` は v0.3 では生成しない。Build / Run タスクは v0.5 AKDev VS Code Companion 側で扱う

### 次回の主作業

**v0.4 Visual Debug Canvas** — ROADMAP5.md / CHECKLIST5.md を作成してから実装開始。

### v0.3 Project Scaffold パッチ（2026-05-24 完了）

- 完了済みドキュメントを `old/` に整理（ROADMAP3.md / CHECKLIST3.md / PATCH_PROJECT_DIALOG_*.md）
- `core/project.py` に以下を追加:
  - `default_target_config()`: AK32 Baremetal の target.json / build 設定を返す
  - `default_tools_config()`: vscode / kicad 設定枠（kicad は enabled: false）を返す
  - `load_json_or_default(path, default_fn)`: JSON ファイルが存在しなければ default_fn() を返す
- `create_project()` を拡張（新規プロジェクトで以下を生成）:
  - `target.json` — AK32 Baremetal 既定
  - `tools.json` — vscode / kicad 設定枠
  - `hdl/` / `board/` / `docs/` / `build/rom/` / `build/export/`
  - `.vscode/settings.json` (`{"akdev.project": true}`)
  - `.vscode/extensions.json` (`akdev.akdev-companion` recommended)
- `tests/test_project_scaffold.py` を追加（17 件）
- pytest 137 件全通過（既存 120 件 + 新規 17 件）

### v0.3 Build Target Wiring パッチ（2026-05-24 完了）

- `core/project.py` に以下を追加:
  - `load_target(root)`: `root/target.json` を読む。存在しない場合は `default_target_config()` を返す。
  - `load_tools(root)`: `root/tools.json` を読む。存在しない場合は `default_tools_config()` を返す。
  - `src_type(path)`: ファイル拡張子から source type (`asm / hdl / c / cpp / linker / binary / custom`) を返す。
- `ui/win.py` の `_build()` を更新:
  - target.json の `build.type` を確認する
  - `internal_assembler`: 内蔵アセンブラでビルド（既存互換）
  - `external_command`: Log に "Build: external_command is not implemented yet" を出して中断
  - その他: Log に "Build: unsupported build type: <type>" を出して中断
  - target.json がない旧プロジェクトは `load_target()` フォールバックで AK32 Baremetal デフォルト動作
- `tests/test_target_build_config.py` を追加（22 件）
- pytest 159 件全通過（既存 137 件 + 新規 22 件）
- CHECKLIST4.md セクション 5 / 6 を完了扱いに更新
- ROADMAP4.md に `build.output` 役割方針と Source Type 方針を追記

### 次回の作業開始点

**ROADMAP5.md / CHECKLIST5.md を作成して v0.4 Visual Debug Canvas の計画を立てる。**

---

## v0.2 の方向性（完了）

**テーマ: Workspace UI Refinement** — 2026-05-24 完了。

詳細は `ROADMAP3.md` / `CHECKLIST3.md` を参照。

---

## 次回 Claude Code に最初に入れる指示文

```
HANDOFF.md を読んで現在の状態を確認してください。

v0.1 / v0.2 / v0.3 は完了済みです。
pytest 462 件全通過済み。

次は v0.4 Visual Debug Canvas の実装を続けます。
CHECKLIST5.md 完了状況:
- セクション 1〜8: 全完了済み（AK32命令拡張 / アセンブラ / Canvas UX / Grid Snap / Bus Connection / Wire Mode / Memory Viewer）
- pytest 462 件全通過済み

次は CHECKLIST5.md セクション 9（PC ハイライト）から始めてください。
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

### セッション 12（2026-05-23）

- v0.2 テーマを「Workspace UI Refinement」に決定
- `ROADMAP2.md` / `CHECKLIST2.md` を `old/` にアーカイブし削除
- `ROADMAP3.md` / `CHECKLIST3.md` を新規作成（v0.2 計画）
- `HANDOFF.md` を更新

### セッション 13（2026-05-24）

- `PATCH_SAVE_ROADMAP.md` / `PATCH_SAVE_CHECKLIST.md` を作成（保存仕様修正計画）
- 保存仕様修正パッチを実装:
  - `ui/editor.py`: `_SAVE_DIR` 廃止、`set_project_root()` / `close_all_tabs()` / `validate_source_name()` 追加、保存先を `project_root/src/` に変更、タブ名を `source_name` に変更
  - `ui/canvas.py`: `PartNode` に `sources` フィールド追加、`export_parts()` / `import_parts()` 対応、`get_node()` 追加
  - `ui/win.py`: `_BUILD_OUT` 廃止、`_new_project()` でタブクリア、`_on_open_tab()` にファイル名ダイアログ追加、Build 出力を `project_root/build/out/` に変更
  - `core/project.py`: `build/out/` ディレクトリを作成するよう修正
  - `tests/test_editor_reload.py` / `test_build.py` / `test_sim_load.py` を新 API に更新
  - `tests/test_save_isolation.py` を新規作成（20 件）
- `pytest tests/` 105 件全通過
- 手動確認（タブ名・プロジェクト分離・UART Hi）は次回

### セッション 14（2026-05-24）

- `PATCH_PROJECT_DIALOG_ROADMAP.md` / `PATCH_PROJECT_DIALOG_CHECKLIST.md` を作成（Project Dialog / Save As パッチ計画）
- `HANDOFF.md` を更新（現在の優先作業を Project Dialog パッチに変更）

### セッション 36（2026-05-30）

- CHECKLIST5.md セクション 8（Memory Viewer パネル）を実装・完了:
  - `ui/memview.py` を新規作成: `_hex_dump(data)` モジュール関数 / `MemoryViewer(QDockWidget)` クラス
  - `_hex_dump`: 1行 16bytes、アドレス列 + hex 列 + ASCII 列。非印字文字は "."
  - `MemoryViewer.update_from_ram(ram_part)`: `ram_part.dump()` から bytes を読み hex dump 表示を更新
  - `MemoryViewer.highlight_addr(pc)`: PC が属する行を薄い黄色でハイライト（`QTextCharFormat` 使用）
  - `ui/win.py`: `_setup_memory_viewer()` 追加、下部タブ（Log/UART/Bus Trace と並列）に "Memory" ドック追加
  - `ui/win.py`: `_update_memory_viewer()` 追加、Build / Run / Step / Reset / Pause 後に呼び出し
  - `ui/win.py`: View Ribbon に Memory Viewer トグルを追加
  - `tests/test_memview.py` を新規作成（22 件）: hex dump 単体 / MemoryViewer 生成 / RAM 内容反映 / None/空 RAM 無クラッシュ / highlight_addr 無クラッシュ / MainWin 統合テスト
  - pytest 462 件全通過（既存 440 件 + 新規 22 件）
  - CHECKLIST5.md セクション 8 を全 [x] に更新

### セッション 35（2026-05-30）

- CHECKLIST5.md セクション 7.6（Wire Routing Patch 2 — 障害物回避と頂点編集）を実装・完了:
  - `ui/canvas.py`: `from collections import deque` / `from math import floor, ceil` を追加
  - `ui/canvas.py`: `QGraphicsRectItem` を Qt インポートに追加
  - `ui/canvas.py`: `_grid_pos(p)` / `_compress_path(path)` モジュールレベル関数を追加
  - `ui/canvas.py`: `RouteHandle(QGraphicsRectItem)` クラスを追加（6×6px ドラッグ可能 waypoint ハンドル、grid スナップ、移動コールバック）
  - `ui/canvas.py`: `Canvas.mode_changed = Signal(str)` を追加
  - `ui/canvas.py`: `Canvas.__init__` に `_handle_items: list = []` を追加
  - `ui/canvas.py`: `_block_cells(excl_ids)` を追加（PartNode の bounding rect + 1 セルマージンを blocked set として返す）
  - `ui/canvas.py`: `_route_segment(start, end, blocked)` BFS を追加（障害物回避、フォールバック H→V Manhattan）
  - `ui/canvas.py`: `_route_grid(start, end, waypoints, blocked)` を追加（waypoint 区間ごとに BFS、端点を正確な座標に置換）
  - `ui/canvas.py`: `_show_handles()` / `_hide_handles()` / `_on_handle_moved()` を追加
  - `ui/canvas.py`: `_start_wire()` を更新（`_show_handles()` 呼び出し、`mode_changed.emit("wire")`）
  - `ui/canvas.py`: `_cancel_wire()` を更新（`_hide_handles()` 呼び出し、`mode_changed.emit("design")`）
  - `ui/canvas.py`: `set_mode()` を更新（重複 emit を避ける early return 追加、wire モードでも handles/signal 対応）
  - `ui/canvas.py`: `update_connections()` を BFS ルーティングに更新（`_block_cells` + `_route_grid` 経由で描画）
  - `ui/canvas.py`: `import_canvas(clear=True)` で `_hide_handles()` を追加
  - `ui/win.py`: `_a_wire_mode` QAction（checkable）を追加し View Ribbon に配置、`mode_changed` シグナルで状態同期
  - `tests/test_canvas_routing.py`: 障害物回避・BFS ルーティング・RouteHandle・mode_changed テスト 35 件新規作成
  - pytest 440 件全通過（既存 405 件 + 35 件追加）
  - CHECKLIST5.md セクション 7.6 を新規追加・[x] に更新

### セッション 34（2026-05-26）

- CHECKLIST5.md セクション 7.5（配線 UX 改善 — wire mode + マンハッタン配線）を実装・完了:
  - `ui/canvas.py`: `_LINE_COLOR` を削除し `_KIND_COLORS` dict（bus=#66ccff / signal=#88ddaa / clock=#ffcc66 / reset=#ff8888）と `_WIRE_PREVIEW_COLOR` に置換
  - `ui/canvas.py`: `ConnectionLine.__init__` に `color: str` 引数を追加（`_KIND_COLORS` またはカスタム色）
  - `ui/canvas.py`: `ConnectionLine.update_route(points)` を追加（H-then-V Manhattan routing）
  - `ui/canvas.py`: `ConnectionLine.update_line(p1, p2)` を `update_route([p1, p2])` のラッパーに変更
  - `ui/canvas.py`: `Canvas.__init__` に `_mode = "design"` / `_wire_from` / `_wire_waypoints` / `_wire_preview` を追加
  - `ui/canvas.py`: `Canvas.set_mode()` を追加（"design" → wire state cancel）
  - `ui/canvas.py`: `Canvas._start_wire()` / `_add_waypoint()` / `_finish_wire()` / `_cancel_wire()` / `_update_wire_preview()` を追加
  - `ui/canvas.py`: `add_connection()` に `route: list | None` / `color: str` 引数を追加、`"route"` / `"color"` を conn dict に保存
  - `ui/canvas.py`: `_make_conn_item()` で `color` を `ConnectionLine` に渡す
  - `ui/canvas.py`: `update_connections()` を `update_route()` 対応に更新（route waypoints 反映）
  - `ui/canvas.py`: `import_canvas(clear=True)` で `_cancel_wire()` を呼ぶ
  - `ui/canvas.py`: `contextMenuEvent()` を wire mode 対応に更新（design: "接続を開始"追加 / wire + PartNode: "ここに接続"/"キャンセル" / wire + 空白: waypoint追加）
  - `ui/canvas.py`: `add_part_at()` / `import_parts()` / clone から `_port_dot._click_cb` 設定を削除（PortDot は visual のみ）
  - `ui/canvas.py`: `mouseMoveEvent()` で wire mode 時に `_update_wire_preview()` を呼ぶ
  - `tests/test_canvas_wire_mode.py`: wire mode テスト 37 件新規作成
  - `tests/test_canvas_port_connect.py`: `_click_cb` チェックのテスト 2 件を削除（wiring 廃止）
  - pytest 405 件全通過（既存 373 件 + 37 件追加 − 2 件削除 + 差分調整）
  - CHECKLIST5.md セクション 7.5 を新規追加・[x] に更新

### セッション 33（2026-05-26）

- CHECKLIST5.md セクション 7（port-to-port クリック操作）を実装・完了:
  - `ui/canvas.py`: `_DOT_RADIUS` / `_DOT_COLOR` / `_DOT_PENDING` モジュール定数を追加
  - `ui/canvas.py`: `PortDot(QGraphicsEllipseItem)` クラスを追加（node_id / port_name / _click_cb / set_pending() / mousePressEvent → _click_cb 呼び出し）
  - `ui/canvas.py`: `PartNode.__init__` で `_port_dot = PortDot(node_id, "bus", self)` を作成し右端中央に配置
  - `ui/canvas.py`: `Canvas.__init__` に `_pending_port = None` を追加
  - `ui/canvas.py`: `Canvas._on_port_click(dot)` を追加（1回目 → pending セット、2回目 → add_connection / 同一node → キャンセル）
  - `ui/canvas.py`: `import_canvas(clear=True)` で `_pending_port = None` を追加
  - `ui/canvas.py`: `add_part_at` / `import_parts` / contextMenu clone で `_port_dot._click_cb = self._on_port_click` を設定
  - `tests/test_canvas_port_connect.py`: port 接続テスト 25 件追加
  - `tests/test_save_isolation.py`: `scene().items()[0]` → `isinstance` フィルタ修正（PortDot が z=1 で先頭に来るため）
  - pytest 373 件全通過（既存 348 件 + 新規 25 件）
  - CHECKLIST5.md セクション 7 の port-to-port クリック操作項目を [x] に更新

### セッション 32（2026-05-26）

- CHECKLIST5.md セクション 7.4（接続線描画）を実装・完了:
  - `ui/canvas.py`: `_LINE_COLOR` / `_KIND_PEN_WIDTH` モジュール定数を追加
  - `ui/canvas.py`: `ConnectionLine(QGraphicsPathItem)` クラスを追加（conn_id / from/to_node_id / kind → pen幅 / zValue=-1 / update_line(p1, p2)）
  - `ui/canvas.py`: `PartNode.__init__` に `_pos_changed_cb = None` を追加
  - `ui/canvas.py`: `PartNode.itemChange()` で `ItemPositionHasChanged` 時に `_pos_changed_cb()` を呼び出す
  - `ui/canvas.py`: `Canvas.__init__` に `_conn_items: dict = {}` を追加
  - `ui/canvas.py`: `Canvas._node_center()` / `_make_conn_item()` / `_rebuild_conn_items()` を追加
  - `ui/canvas.py`: `Canvas.update_connections()` を追加（全接続線の位置を現在ノード座標に更新）
  - `ui/canvas.py`: `add_connection()` 後に ConnectionLine をシーンへ追加
  - `ui/canvas.py`: `import_canvas()` 後に `_rebuild_conn_items()` で接続線を復元
  - `ui/canvas.py`: `add_part_at()` / `import_parts()` / contextMenu clone に `_pos_changed_cb` を設定
  - `tests/test_canvas_connection_lines.py`: 接続線テスト 27 件追加
  - pytest 348 件全通過（既存 321 件 + 新規 27 件）
  - CHECKLIST5.md セクション 7.4 を [x] に更新

### セッション 31（2026-05-26）

- CHECKLIST5.md セクション 7（Bus Connection Patch）を追加・一部完了:
  - セクション番号を繰り下げ: 旧 7-13 → 新 8-14（Bus Connection Patch を 7 として挿入）
  - `ui/canvas.py`: `Canvas.__init__` に `_conn_seq: int = 0` / `_connections: list[dict] = []` を追加
  - `ui/canvas.py`: `_next_conn_id()` を追加（`conn_0001` 形式の連番 ID）
  - `ui/canvas.py`: `add_connection(from_node_id, from_port, to_node_id, to_port, kind, width, label)` を追加
  - `ui/canvas.py`: `export_canvas()` を追加 — `{"parts": [...], "connections": [...]}` を返す
  - `ui/canvas.py`: `import_canvas(data, part_library, clear=True)` を追加 — parts / connections を復元
  - `tests/test_canvas_connections.py`: 接続データ構造テスト 30 件追加
  - pytest 321 件全通過（既存 291 件 + 新規 30 件）
  - CHECKLIST5.md セクション 7.1 / 7.2 / 7.3 を [x] に更新

### セッション 30（2026-05-26）

- CHECKLIST5.md セクション 6（Part Visual / Port Detail / Bus Connection 方針）を完了:
  - `ROADMAP5.md` セクション 7 を大幅拡充（方針確定）:
    - 7-1: `part.json` `"size": [w, h]` 省略可能フィールド方針（v0.5 以降実装、`_NODE_W`/`_NODE_H` フォールバック）
    - 7-2: `part.json` `"color"` / `system.json` `"instance_color"` カラー優先度方針（カテゴリ色 < part.json < instance_color, `QColor.isValid()` バリデーション付き）
    - 7-3: Port Detail 方針（ダブルクリック / コンテキストメニューで開く、表示列: Name/Direction/Kind/Width/Range/Description、v0.4 では実装しない）
    - 7-4: `system.json` `connections` スキーマ確定（`id`, `from: {node_id, port}`, `to: {node_id, port}`, `kind`, `width`, `label`）
  - CHECKLIST5.md セクション 6 全項目を [x] に更新
  - pytest 291 件全通過（変化なし）

### セッション 29（2026-05-26）

- CHECKLIST5.md セクション 5（Grid / Snap Patch）を実装:
  - `ui/canvas.py`: `PartNode` に `_snap_enabled: bool = False` と `set_snap()` を追加
  - `ui/canvas.py`: `PartNode.itemChange()` をオーバーライド — `ItemPositionChange` 時に `round(x/g)*g` で snap
  - `ui/canvas.py`: `Canvas.__init__` に `_snap_enabled: bool = False` を追加
  - `ui/canvas.py`: `Canvas.set_snap(enabled)` を追加 — 既存ノード全体に伝播
  - `ui/canvas.py`: `Canvas.add_part_at()` で snap ON のとき scene_pos を丸めてから配置、新ノードに snap 状態を渡す
  - `ui/canvas.py`: `Canvas.import_parts()` で復元ノードにも snap 設定を渡す
  - `ui/win.py`: `_a_snap` QAction（checkable, 初期値 OFF）を追加し、Ribbon View タブに追加
  - `tests/test_canvas_snap.py`: Snap テスト 15 件追加
  - pytest 291 件全通過（既存 276 件 + 新規 15 件）
  - CHECKLIST5.md セクション 5 を全 [x] に更新

### セッション 28（2026-05-25）

- `ui/canvas.py` に右ドラッグ Pan を実装:
  - `_PAN_THRESHOLD = 4` モジュール定数を追加
  - `__init__` に `_pan_origin` / `_pan_last` / `_panned` 状態変数を追加
  - `mousePressEvent`: 右ボタン押下時に pan 状態を初期化・`ClosedHandCursor` をセット
  - `mouseMoveEvent`: 右ボタン保持中、閾値超えで `_panned = True`、スクロールバーを差分移動
  - `mouseReleaseEvent`: 右ボタン離したらカーソル復元・状態リセット
  - `contextMenuEvent`: `_panned == True` の場合はメニューをスキップして `_panned` をリセット
- `tests/test_canvas_pan.py`: pan 状態テスト 10 件追加（duck-type 右ボタンイベント使用）
- pytest 276 件全通過（既存 266 件 + 新規 10 件）
- CHECKLIST5.md セクション 4 に右ドラッグ Pan 完了項目を追記

### セッション 27（2026-05-25）

- `ui/canvas.py` に `wheelEvent()` を追加:
  - `angleDelta().y() > 0` → `zoom_in()`、`< 0` → `zoom_out()`、`== 0` → `super()`
  - `event.accept()` でイベントを消費
  - `setTransformationAnchor(AnchorUnderMouse)` を `__init__` に追加（ホイール位置中心ズーム）
- `tests/test_canvas_zoom_grid.py` にホイールズームテスト 5 件追加（`_FakeWheelEvent` duck-type 使用）
  - anchor 確認 / wheel forward → zoom_in / wheel backward → zoom_out / 上下限ヒット確認
- pytest 266 件全通過（既存 261 件 + 新規 5 件）
- CHECKLIST5.md セクション 4 にホイールズーム完了項目を追記

### セッション 26（2026-05-25）

- CHECKLIST5.md セクション 4（Canvas UX Patch 1B）を実装:
  - `ui/canvas.py`: `_ZOOM_MIN = 0.1` / `_ZOOM_MAX = 10.0` モジュール定数を追加
  - `ui/canvas.py`: `GridScene(QGraphicsScene)` を追加（`GRID_SIZE = 20`、`drawBackground()` でグリッド線、`set_grid_visible()` / `grid_visible()`）
  - `ui/canvas.py`: `Canvas.__init__()` を `QGraphicsScene` → `GridScene` に変更
  - `ui/canvas.py`: `zoom_in()` / `zoom_out()` / `reset_zoom()` / `fit_to_view()` / `set_grid_visible()` を追加（zoom 上限/下限チェックは乗算後値で判定）
  - `ui/win.py`: `_a_zoom_in` / `_a_zoom_out` / `_a_zoom_reset` / `_a_fit` / `_a_grid` QAction を追加、Ribbon View タブに追加
  - `tests/test_canvas_zoom_grid.py`: Zoom / GridScene テスト 15 件追加
  - pytest 261 件全通過（既存 246 件 + 新規 15 件）
  - CHECKLIST5.md セクション 4・11.5 を全 [x] に更新

### セッション 25（2026-05-24）

- CHECKLIST5.md セクション 3（Canvas UX Patch 1A）を実装:
  - `ui/canvas.py`: グリッド配置定数 (`_GAP_X`/`_GAP_Y`/`_COLS`/`_ORIGIN`) と `_place_col`/`_place_row` を削除
  - `ui/canvas.py`: `setAcceptDrops(True)` / `_add_offset` / `_part_library` を `__init__` に追加
  - `ui/canvas.py`: `set_part_library(lib)` を追加（`dropEvent` 用パーツ辞書を保持）
  - `ui/canvas.py`: `add_part_at(part, scene_pos)` を追加（指定 scene 座標に PartNode 配置）
  - `ui/canvas.py`: `add_part()` を viewport 中央 + `_add_offset * 20px` ダイアゴナルオフセット方式に変更（8 ステップでサイクル）
  - `ui/canvas.py`: `dragEnterEvent` / `dragMoveEvent` / `dropEvent` を追加（MIME text = part_id でドロップ配置）
  - `ui/win.py`: `_PartsTree(QTreeWidget)` を追加（`startDrag()` オーバーライドで part_id を MIME text にセット）
  - `ui/win.py`: `_setup_parts_lib()` を `_PartsTree` に切り替え、`setDragEnabled(True)`、`canvas.set_part_library()` 呼び出しを追加
  - `tests/test_canvas_ux.py`: Canvas UX テスト 12 件追加
  - pytest 246 件全通過（既存 234 件 + 新規 12 件）
  - CHECKLIST5.md セクション 3・11.3 を全 [x] に更新

### セッション 24（2026-05-24）

- ROADMAP5.md / CHECKLIST5.md を Canvas UX 優先に再編:
  - v0.4 の次優先を Memory Viewer → Canvas UX Patch 1A（ドラッグ&ドロップ）に変更
  - ROADMAP5.md: セクション 1〜3 完了、4〜8 に Canvas UX 設計を追加（ドラッグ&ドロップ・Zoom・Grid・Snap・接続線）
  - CHECKLIST5.md: セクション 3〜6 に Canvas UX Patch 1A/1B・Grid Snap・方針を追加。旧セクション 3〜9 を 7〜13 に繰り下げ
  - 完了済みチェック項目（セクション 1・2・10・11.1・11.2・11.4・11.5）はすべて維持
- 次回の主作業を CHECKLIST5.md セクション 3（Canvas UX Patch 1A）に変更

### セッション 23（2026-05-24）

- ROADMAP4.md / CHECKLIST4.md を old/ にアーカイブ
- HANDOFF.md のドキュメント体系を old/ パス参照に更新
- v0.4 CHECKLIST5.md セクション 0〜2・6・7 を完了:
  - `core/cpu.py`: ADD / SUB / ADDI / LD / ST / JMP / BEQ 命令（opcode 0x04〜0x0A）を実装
  - `asm/asm.py`: 同命令のパーサ追加、2-pass ラベル解決、`assemble_ex()` 新規追加（address_map 返却）
  - `src/fib.asm`: フィボナッチ数列プログラム（ADD/ST/ADDI/BEQ/JMP 使用）を新規作成
  - `tests/test_cpu_v04.py`: CPU 命令テスト 30 件追加
  - `tests/test_asm_v04.py`: アセンブラテスト 45 件追加
  - `tests/test_v04_flow.py`: fib フロー統合テスト 10 件追加
  - pytest 234 件全通過（既存 159 件 + 新規 75 件）

### セッション 22（2026-05-24）

- ROADMAP5.md / CHECKLIST5.md を新規作成（v0.4 Visual Debug Canvas 計画）
  - ROADMAP5.md: 命令セット拡張（ADD/SUB/LD/ST/JMP/BEQ/ADDI）・アセンブラ更新・Memory Viewer・PC ハイライト・Canvas Signal Overlay・fib.asm サンプル の設計
  - CHECKLIST5.md: セクション 0〜9 の全チェック項目を作成
- HANDOFF.md のドキュメント体系を v0.4 優先に更新
- 次回指示文を「CHECKLIST5.md セクション 0 から実装開始」に更新

### セッション 21（2026-05-24）

- v0.3 Project & Target Foundation を完了扱いに移行:
  - ROADMAP4.md: v0.3 テーマを "完了" 表記に更新、v0.4 を Visual Debug Canvas に変更、VS Code Companion を v0.5 に移動、KiCad / Board を v0.6 以降に移動
  - ROADMAP4.md: セクション 7 を "v0.5 VS Code Companion への橋渡し" に改訂（localhost HTTP/WS 連携案・将来 API 案・isa.json 補完構想を追記）
  - ROADMAP4.md: v0.3 完成条件を全 [x] に更新
  - CHECKLIST4.md: 残未完了項目を全 [x] に（tools.json コマンドパス方針・tasks.json 不生成方針・セクション 7/8/9）
  - HANDOFF.md: v0.3 完了内容まとめ・次回作業を ROADMAP5.md / CHECKLIST5.md 作成に更新

### セッション 20（2026-05-24）

- v0.3 Build Target Wiring パッチを実装:
  - `core/project.py`: `load_target()` / `load_tools()` / `src_type()` を追加
  - `ui/win.py`: `_build()` を target.json の `build.type` に対応させる（internal_assembler / external_command / unknown の 3 分岐）
  - `tests/test_target_build_config.py`: 22 件追加
  - pytest 159 件全通過（既存 137 件 + 新規 22 件）
- CHECKLIST4.md セクション 5 / 6 を [x] に更新
- ROADMAP4.md に build.output 役割方針・Source Type 方針を追記
- HANDOFF.md を更新

### セッション 19（2026-05-24）

- 完了済みドキュメントを `old/` に整理（ROADMAP3.md / CHECKLIST3.md / PATCH_PROJECT_DIALOG_ROADMAP.md / PATCH_PROJECT_DIALOG_CHECKLIST.md）
- v0.3 Project Scaffold パッチを実装:
  - `core/project.py`: `default_target_config()` / `default_tools_config()` / `load_json_or_default()` を追加
  - `create_project()`: target.json / tools.json / hdl/ / board/ / docs/ / build/rom/ / build/export/ / .vscode/ を生成するよう拡張
  - `tests/test_project_scaffold.py`: 17 件追加
  - pytest 137 件全通過（既存 120 件 + 新規 17 件）
- CHECKLIST4.md を更新（セクション 0〜4 の完了項目を [x] に）
- HANDOFF.md を更新

### セッション 18（2026-05-24）

- ROADMAP4.md / CHECKLIST4.md を新規作成（v0.3 Project & Target Foundation 計画）
- HANDOFF.md を更新（現在の優先作業を v0.3 に変更）

### セッション 17（2026-05-24）

- v0.2 最終整理:
  - CHECKLIST3.md を更新（3.1 完了、3.2/4 を v0.3 延期・注記、5 を現状許容、6 を完了マーク）
  - ROADMAP3.md を更新（v0.2 完成条件を現状に合わせて更新、v0.3 候補に VS Code 連携・自作 ISA 設定を追加）
  - HANDOFF.md を更新（v0.2 完了確認・次アクション整理）
  - v0.1 回帰テスト実施: pytest 120 件全通過
  - headless フロー確認: New Project → Build → Reset → Run → UART "Hi" → Register View → Bus Trace 全通過
  - **v0.2 完了**

### セッション 16（2026-05-24）

- Project Dialog / Save As パッチの手動確認（headless ダイアログ駆動で全フロー検証）
  - File メニュー・Ribbon 構造確認（New/Open/Save/Save As/Exit 順序・セパレータ位置）
  - Ctrl+Shift+S ショートカット確認
  - New Project → project.json / system.json / src / build/out / asset 作成確認
  - Save Project 未設定時の案内 Log 確認
  - Save Project As → project_root 切り替え確認
  - 以後の Save Project が new_root に書くことを確認
  - Open Project → project_root 復元確認
  - キャンセル / 既存フォルダ衝突 / 不正 JSON のエラーパス確認（全 4 プローブ通過）
- Project Dialog / Save As パッチを完了扱いに変更
- HANDOFF.md を更新（優先作業を v0.2 UI 改善に変更）

### セッション 15（2026-05-24）

- `PATCH_SAVE_ROADMAP.md` / `PATCH_SAVE_CHECKLIST.md` を `old/` に移動（完了アーカイブ）
- `ui/win.py` に Project Dialog / Save As パッチを実装:
  - `_DEFAULT_PROJECT` 定数を廃止
  - `import shutil` を削除
  - `QFileDialog` を追加インポート
  - `_new_project()`: `QFileDialog.getExistingDirectory()` + `QInputDialog.getText()` でユーザーが場所・名前を選択
  - `_open_project()`: `QFileDialog.getOpenFileName()` で `project.json` を選択
  - `_save_project()`: `project_root is None` 時に案内 Log を出して中断
  - `_save_project_as()`: 新規追加。別名保存で `project_root` を切り替え
  - `_ensure_project_root()`: fallback を廃止（`project_root` をそのまま返すのみ）
  - `_build()`: `_ensure_project_root()` 呼び出しを直接 `project_root` 参照に変更
  - File メニュー: セパレータ追加・`Save Project As...` 追加
  - Ribbon File タブ: `Save Project As...` ボタン追加
- `tests/test_project_dialog.py` を新規作成（15 件）
- `pytest tests/` 120 件全通過
