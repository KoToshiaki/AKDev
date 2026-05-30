# AKDev Project Dialog / Save As パッチ — ROADMAP

> 保存仕様修正パッチ完了後の次パッチ。
> 進捗管理は `PATCH_PROJECT_DIALOG_CHECKLIST.md` で行う。

---

## 問題の概要

New Project / Open Project / Save Project の挙動が、通常の GUI アプリとしてユーザーの期待に沿わない。
`build/current_project` という固定パスに常に書き込まれており、ユーザーが保存先やプロジェクト名を決められない。

---

## 現在の挙動

| 操作 | 現在の挙動 |
|---|---|
| New Project | `build/current_project` を消して再作成。ユーザー選択なし |
| Open Project | `build/current_project/project.json` を固定で開く。ファイル選択なし |
| Save Project | `_ensure_project_root()` が `build/current_project` に fallback する |
| Save Project As... | 存在しない |

---

## 理想の挙動

| 操作 | 理想の挙動 |
|---|---|
| New Project | 保存先フォルダ → プロジェクト名をユーザーが選択。任意の場所に作成 |
| Open Project | ファイルダイアログで既存 `project.json` を選択して開く |
| Save Project | 現在の `project_root` に上書き保存。未設定なら案内を出す |
| Save Project As... | 保存先フォルダ → 新プロジェクト名をユーザーが選択して別名保存 |

---

## New Project 仕様

1. `QFileDialog.getExistingDirectory()` で保存先の親フォルダを選ぶ
2. `QInputDialog.getText()` でプロジェクト名を入力する
3. `<親フォルダ>/<project_name>/` を `project_root` として作成する
4. 既に存在する場合は Log に警告して中断する
5. `create_project(project_root, project_name)` を呼ぶ
6. Canvas をクリアする（`import_parts([], {})`）
7. `editor_tabs.close_all_tabs()` を呼ぶ
8. `editor_tabs.set_project_root(project_root)` を呼ぶ
9. UART Console / Bus Trace / Register View を初期化する
10. Log に `"New project: <path>"` を出す
11. キャンセル時は何もしない（`project_root` を変えない）

---

## Open Project 仕様

1. `QFileDialog.getOpenFileName()` で `project.json` を選ぶ
   - フィルタ: `"AKDev Project (project.json);;JSON Files (*.json);;All Files (*)"`
2. 選択された `project.json` の親ディレクトリを `project_root` とする
3. `load_project(project_root)` を呼ぶ
4. `system.json` の `parts` から Canvas を復元する（`import_parts`）
5. `editor_tabs.set_project_root(project_root)` を呼ぶ
6. Log に `"Opened project: <path>"` を出す
7. キャンセル時は何もしない（`project_root` を変えない）
8. `project.json` 読み込みエラーは Log にメッセージを出して中断する

---

## Save Project 仕様

1. 現在の `project_root` に上書き保存する
2. `project_root` が `None` の場合は Log に案内を出して中断する
   - メッセージ: `"Save: New Project / Open Project / Save As を先に行ってください"`
3. `_persist_system()` を呼んで Canvas / system.json / sources を保存する
4. 現在のエディタタブを `editor_tabs.save_current()` で保存する
5. Log に `"Saved project: <path>"` を出す

---

## Save Project As... 仕様

1. `QFileDialog.getExistingDirectory()` で保存先の親フォルダを選ぶ
2. `QInputDialog.getText()` で新しいプロジェクト名を入力する
3. `<親フォルダ>/<project_name>/` を `new_root` とする
4. 既に存在する場合は Log に警告して中断する
5. `create_project(new_root, project_name)` を呼ぶ
6. 現在の Canvas / system.json / sources を `new_root` に保存する
7. 開いている source file を `new_root/src/` に保存する
8. `project_root` を `new_root` に更新する（以降の Save はここに書く）
9. `editor_tabs.set_project_root(new_root)` を呼ぶ
10. Log に `"Saved project as: <path>"` を出す
11. キャンセル時は何もしない（`project_root` を変えない）

---

## File メニュー / Ribbon 仕様

### File メニュー

```
File
  New Project        Ctrl+N
  Open Project       Ctrl+O
  ─────────────────
  Save Project       Ctrl+S
  Save Project As...
  ─────────────────
  Exit
```

### Ribbon — File タブ

```
[ New Project ]  [ Open Project ]  [ Save Project ]  [ Save Project As... ]
```

---

## 変更対象ファイル

### ui/win.py（主要変更）

| 対象 | 変更内容 |
|---|---|
| `_DEFAULT_PROJECT` 定数 | 廃止または dev fallback 専用にする |
| `_new_project()` | `QFileDialog` + `QInputDialog` で場所・名前を選択させる |
| `_open_project()` | `QFileDialog.getOpenFileName()` で `project.json` を選択させる |
| `_save_project()` | `project_root is None` の場合に案内ログを出す |
| `_save_project_as()` | 新規追加。`QFileDialog` + `QInputDialog` で別名保存 |
| `_ensure_project_root()` | `project_root is None` 時に自動作成しないよう変更 |
| `QAction _a_save_as` | 新規追加 |
| File メニュー | セパレータ追加、Save As... 追加 |
| Ribbon File タブ | Save As... ボタン追加 |

### core/project.py（確認のみ）

- `create_project()` が既存フォルダで `FileExistsError` を送出する → そのまま利用
- 追加変更は不要の見込み

### ui/editor.py（Save As 対応確認）

- `save_current()` が `project_root/src/<source_name>` に保存する → 既存実装を確認
- Save As 時に `set_project_root(new_root)` を呼んで切り替えれば対応できるか確認
- 必要なら開いているタブ一覧を返すメソッドを追加

### tests/（追加）

- `QFileDialog` / `QInputDialog` を `monkeypatch` / `mock` してテストする

---

## 実装順序

1. **0. 現状確認** — 現在の `_new_project` / `_open_project` / `_save_project` の実装詳細を把握する
2. **1. New Project** — `QFileDialog` + `QInputDialog` でユーザーが場所・名前を選べるようにする
3. **2. Open Project** — `QFileDialog.getOpenFileName()` で `project.json` を選べるようにする
4. **3. Save Project** — `project_root is None` のガードと案内ログを追加する
5. **4. Save Project As...** — `_save_project_as()` / `_a_save_as` / メニュー / Ribbon を追加する
6. **5. テスト** — 各操作の自動テストを追加する
7. **6. 完了確認** — `pytest tests/` 全件通過 + 手動確認

---

## 完成条件

- New / Open / Save / Save As が通常 GUI アプリとして自然に動作する
- `build/current_project` 固定挙動に依存しない
- `pytest tests/` が全件通過する
- 手動確認で任意フォルダにプロジェクトを作成・保存・再オープンできる

---

## 回帰テスト方針

- 既存テスト `tests/` を全件通過させる（保存仕様パッチで 105 件）
- 新規テストは `QFileDialog` / `QInputDialog` を mock してダイアログなしで実行する
- GUI テストは `pytest-qt` の `monkeypatch` を使う

---

## 今回やらないこと

- 保存仕様パッチの再設計
- Ribbon の追加改善（Save As 追加のみ）
- VS Code 連携
- 追加命令（アセンブラ拡張）
- Memory Viewer
- Canvas 接続線
- GPU / VRAM 対応
- 実機出力
