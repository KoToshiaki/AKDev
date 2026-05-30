# AKDev 保存仕様修正パッチ — CHECKLIST

> 詳細な設計は `PATCH_SAVE_ROADMAP.md` を参照。
> v0.2 UI 改善の継続計画は `ROADMAP3.md` / `CHECKLIST3.md` を参照。

---

# 0. 問題確認

* [x] 現在のエディタ保存先を確認する
  - 確認済み: `build/edit/<node_id>.<ext>` — グローバル、プロジェクト非依存
* [x] `build/edit/` 依存箇所を洗い出す
  - 確認済み: `ui/editor.py` の `_SAVE_DIR` と `save_path` 生成ロジック
* [x] `build/out/` 依存箇所を洗い出す
  - 確認済み: `ui/win.py` の `_BUILD_OUT = Path("build/out")`
* [x] node_id がユーザー向けファイル名として使われている箇所を洗い出す
  - 確認済み: `ui/editor.py` L58–L64 の `base_name` と `save_path` 生成

---

# 1. 保存レイアウト決定

* [x] エディタ保存先を `project_root/src/<source_name>` に決定する
  - 完了条件: `PATCH_SAVE_ROADMAP.md` に記載済み ✓
* [x] Build 出力先を `project_root/build/out/<source_name>.bin` に決定する
  - 完了条件: `PATCH_SAVE_ROADMAP.md` に記載済み ✓
* [x] project_root 外にプロジェクト固有ファイルを保存しない方針を明記する
  - 完了条件: `PATCH_SAVE_ROADMAP.md` に記載済み ✓
* [x] node_id と source file name を分離する方針を明記する
  - 完了条件: `PATCH_SAVE_ROADMAP.md` に記載済み ✓

---

# 2. system.json の sources 仕様

* [x] `parts[]` に `sources` フィールドを追加する仕様を決める
  - 完了条件: `PATCH_SAVE_ROADMAP.md` に JSON サンプルを記載済み ✓
* [x] `sources.asm` に `src/<file>.asm`（project_root 相対）を保存する
  - 完了条件: `sources.asm` のパス形式と意味が明確になっている
* [x] `sources.hdl` に `src/<file>.v`（project_root 相対）を保存する
  - 完了条件: `sources.hdl` のパス形式と意味が明確になっている
* [x] 既存 `system.json` に `sources` が無い場合の扱いを決める
  - 完了条件: `null` として扱い、初回アクセス時にダイアログを出す方針を決定する

---

# 3. ファイル名入力仕様

* [x] Open Program 時、未設定なら `.asm` ファイル名を入力させる
  - 完了条件: `QInputDialog.getText()` でファイル名を受け取るロジック実装済み
* [x] Open HDL 時、未設定なら `.v` ファイル名を入力させる
  - 完了条件: 同上
* [x] 拡張子なし入力時に `.asm` / `.v` を補う
  - 完了条件: `"main"` と入力されたら `"main.asm"` に自動補完する実装済み
* [x] 同名ファイルがある場合の扱いを決める
  - 完了条件: Log に警告して別名入力を促す（上書き禁止）実装済み
* [x] タブ名は `source_name`（ユーザー指定ファイル名）を優先表示する
  - 完了条件: タブ名が `main.asm` のように表示される（`test_tab_name_is_source_name` 通過）

---

# 4. ファイル名バリデーション

* [x] 空文字を禁止する
  - 完了条件: `validate_source_name(name, ext)` が空文字を拒否する
* [x] 絶対パスを禁止する
  - 完了条件: `Path(name).is_absolute()` で検出し拒否する
* [x] `../` を禁止する
  - 完了条件: `..` を含む相対パスを検出し拒否する
* [x] `src/` 外への保存を禁止する
  - 完了条件: `project_root / "src" / name` が `src/` 配下に収まることを `Path.resolve()` で確認する（`_on_open_tab` 内）
* [x] `.asm` / `.v` 以外を禁止する
  - 完了条件: 対応拡張子リストで検証する
* [x] Windows で使えない文字を禁止する（`\ / : * ? " < > |`）
  - 完了条件: 禁止文字セットに一致する場合は拒否する
* [x] バリデーション関数のユニットテストを追加する
  - 完了条件: `test_save_isolation.py` に正常系・異常系合わせて 6 件以上通過

---

# 5. EditorTabs 修正（`ui/editor.py`）

* [x] `set_project_root(project_root: Path | None)` を追加する
* [x] `_SAVE_DIR` クラス変数を廃止する
* [x] `open_tab()` が `project_root/src/<source_name>` を読む
* [x] `save_current()` が `project_root/src/<source_name>` に保存する
* [x] タブ名が `source_name`（例: `main.asm`）で表示される
* [x] project_root 未設定時は開けない（`open_tab()` が `None` を返す）
* [x] `close_all_tabs()` を追加する

---

# 6. MainWin 修正（`ui/win.py`）

* [x] New Project 時に `editor_tabs.close_all_tabs()` を呼ぶ
* [x] New Project 時に新しい project_root を `EditorTabs.set_project_root()` に渡す
* [x] Open Project 時に project_root を `EditorTabs.set_project_root()` に渡す
* [x] Open Program 時に `system.json` の `sources.asm` を確認する
  - 完了条件: 割り当て済みならそのファイルを開く、未割り当てならダイアログを出す
* [x] Open HDL 時に `system.json` の `sources.hdl` を確認する
* [x] Build 出力先を `project_root/build/out/<source_name>.bin` にする
  - 完了条件: `_BUILD_OUT` グローバル定数を廃止し、project_root 基準に変更
* [x] Build 時にソースファイル名から bin 名を決定する
  - 完了条件: `main.asm` → `main.bin`、`uart_test.asm` → `uart_test.bin`

---

# 7. Canvas / system.json 保存復元（`ui/canvas.py`）

* [x] `export_parts()` が `sources` フィールドを含める
* [x] `import_parts()` が `sources` フィールドを復元する
  - 欠如していても `{"asm": null, "hdl": null}` として扱う
* [x] Save Project で `sources` が `system.json` に保存される
  - 完了条件: `test_system_json_sources_saved_and_restored` 通過
* [x] Open Project で `sources` が復元される
  - 完了条件: `test_import_parts_restores_sources` 通過

---

# 8. テスト

## 8.1 プロジェクト分離テスト

* [x] Project A で `main.asm` を保存する
  - `test_project_isolation` で `project_a/src/main.asm` が作成されることを確認
* [x] Project B を作成した後に `node_0001` の Open Program を選ぶ
  - `test_project_isolation` で Project A の内容が表示されないことを確認
* [x] Project A と Project B の `src/main.asm` が別ファイルである
  - `test_project_isolation` で確認済み
* [x] node_id が同じでも source file がプロジェクトごとに分離される
  - `test_open_tab_returns_none_without_project_root` / `test_project_isolation` で確認済み

## 8.2 system.json 保存復元テスト

* [x] `system.json` に `sources.asm` が保存される
  - `test_system_json_sources_saved_and_restored` 通過
* [x] Open Project で `sources.asm` が復元される
  - `test_import_parts_restores_sources` 通過

## 8.3 Build 出力テスト

* [x] Build 出力が `project_root/build/out/main.bin` に作成される
  - `test_build_out_isolated` 通過（`create_project` が `build/out/` を作成）

## 8.4 バリデーションテスト

* [x] 空文字が拒否される
* [x] 絶対パスが拒否される
* [x] `../` が拒否される
* [x] `.asm` / `.v` 以外が拒否される
* [x] Windows 禁止文字が拒否される
* [x] 有効なファイル名が受理される（`main.asm`, `boot.asm`, `cpu_core.v`）

## 8.5 v0.1 回帰テスト

* [x] `pytest tests/test_v01_flow.py` が全件通過する
* [x] `pytest tests/test_build.py` が全件通過する
* [x] `pytest tests/test_editor_reload.py` が通過する
* [x] `pytest tests/` 全件通過する（105 件 PASSED）
* [ ] 手動: `src/hello.asm` → Build → Reset → Run → UART "Hi" → Register View → Bus Trace

---

# 9. 完了条件

* [x] `pytest tests/` が全件通過する（105 件）
* [x] 手動確認: New Project 後に古いコードが出ない
* [x] 手動確認: タブ名が `node_0001.asm` ではなく `main.asm` になる
* [x] 手動確認: Project A と Project B のソースが混ざらない
* [ ] `PATCH_SAVE_CHECKLIST.md` の全項目が `[x]` になる
