# AKDev Project Dialog / Save As パッチ — CHECKLIST

> 詳細な設計は `PATCH_PROJECT_DIALOG_ROADMAP.md` を参照。

---

# 0. 現状確認

- [x] 現在の `_new_project()` の挙動を確認する
  - 確認済み: `build/current_project` 固定・`shutil.rmtree` + `create_project` で再作成。ユーザー選択なし
- [x] 現在の `_open_project()` の挙動を確認する
  - 確認済み: `build/current_project` 固定・ファイル選択なし
- [x] 現在の `_save_project()` の挙動を確認する
  - 確認済み: `_ensure_project_root()` が `build/current_project` に自動 fallback
- [x] `build/current_project` / `_DEFAULT_PROJECT` への依存箇所を洗い出す
  - 確認済み: `ui/win.py` の `_DEFAULT_PROJECT` / `_new_project` / `_open_project` / `_ensure_project_root` / `_build`
- [x] `_ensure_project_root()` の fallback 挙動を確認する
  - 確認済み: `project_root is None` のとき `build/current_project` を自動作成していた

---

# 1. New Project 仕様

- [x] 親フォルダを `QFileDialog.getExistingDirectory()` で選ぶ
- [x] プロジェクト名を `QInputDialog.getText()` で入力する
- [x] `<親フォルダ>/<project_name>/` を `project_root` として `create_project()` を呼ぶ
- [x] 既存フォルダがある場合は Log に警告して中断する（`FileExistsError` を捕捉）
- [x] Canvas をクリアする（`import_parts([], {})`）
- [x] `editor_tabs.close_all_tabs()` を呼ぶ
- [x] `editor_tabs.set_project_root(project_root)` を呼ぶ
- [x] UART Console / Bus Trace を初期化する（`clear()`）
- [x] Log に `"New project: <path>"` を出す
- [x] キャンセル時に `project_root` が変わらない（ダイアログキャンセルで処理を止める）

---

# 2. Open Project 仕様

- [x] `QFileDialog.getOpenFileName()` で `project.json` を選ぶ
  - フィルタ: `"AKDev Project (project.json);;JSON Files (*.json);;All Files (*)"`
- [x] 選択された `project.json` の親ディレクトリを `project_root` にする
- [x] `load_project(project_root)` を呼ぶ
- [x] `system.json` の `parts` から Canvas を復元する（`import_parts`）
- [x] `editor_tabs.set_project_root(project_root)` を呼ぶ
- [x] Log に `"Opened project: <path>"` を出す
- [x] キャンセル時に `project_root` が変わらない
- [x] `project.json` 読み込みエラーは Log にメッセージを出して中断する

---

# 3. Save Project 仕様

- [x] 現在の `project_root` に上書き保存する
- [x] `project_root` が `None` の場合は Log に案内を出して中断する
  - メッセージ: `"Save: New Project / Open Project / Save As を先に行ってください"`
- [x] `_persist_system()` を呼んで Canvas / system.json / sources を保存する
- [x] `editor_tabs.save_current()` で現在のエディタタブを保存する
- [x] Log に `"Saved project: <path>"` を出す
- [x] `_ensure_project_root()` の自動 fallback 挙動を削除（`project_root` をそのまま返すのみに変更）

---

# 4. Save Project As... 仕様

- [x] `QAction _a_save_as` を追加する（`Ctrl+Shift+S` ショートカット）
- [x] File メニューに `Save Project As...` を追加する（Save Project の直後）
- [x] Ribbon File タブに `Save Project As...` ボタンを追加する
- [x] 親フォルダを `QFileDialog.getExistingDirectory()` で選ぶ
- [x] 新しいプロジェクト名を `QInputDialog.getText()` で入力する
- [x] `<親フォルダ>/<project_name>/` を `new_root` にする
- [x] 既存フォルダがある場合は Log に警告して中断する（`FileExistsError` を捕捉）
- [x] `create_project(new_root, project_name)` を呼ぶ
- [x] 現在の Canvas / system.json / sources を `new_root` に保存する（`_persist_system()`）
- [x] 開いている source file を `new_root/src/` に保存する（`editor_tabs.save_current()`）
- [x] `project_root` を `new_root` に更新する（以降の Save はここに書く）
- [x] `editor_tabs.set_project_root(new_root)` を呼ぶ
- [x] Log に `"Saved project as: <path>"` を出す
- [x] キャンセル時に `project_root` が変わらない

---

# 5. テスト

- [x] New Project が指定場所に `project.json` / `system.json` / `src/` / `build/out/` / `asset/` を作る
- [x] Open Project が選択した `project.json` の親を `project_root` にする
- [x] Save Project が現在の `project_root` に保存する
- [x] Save Project が `project_root is None` のとき案内 Log を出して保存しない
- [x] Save Project As... が新しい場所にプロジェクトを作る
- [x] Save Project As... 後に `project_root` が `new_root` に切り替わる
- [x] Save Project As... 後に続けて Save Project を実行すると `new_root` に保存される
- [x] キャンセル時に `project_root` が変わらない（New Project / Open / Save As いずれも）
- [x] 既存テストが全件通過する（120 件 PASSED）

---

# 6. 完了条件

- [x] New / Open / Save / Save As が通常 GUI アプリとして自然に動作する（実装完了）
- [x] `build/current_project` 固定挙動に依存しない（`_DEFAULT_PROJECT` 廃止）
- [x] `pytest tests/` が全件通過する（120 件）
- [x] 手動確認: 任意フォルダに New Project → Build → Save → 再 Open できる
- [x] 手動確認: Save As... で別フォルダにプロジェクトを複製できる
