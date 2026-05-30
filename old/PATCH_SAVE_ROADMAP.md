# AKDev 保存仕様修正パッチ — ROADMAP

> v0.2 UI 改善の途中で発見した保存仕様バグの修正計画。
> 進捗管理は `PATCH_SAVE_CHECKLIST.md` で行う。
> UI 改善の計画は `ROADMAP3.md` / `CHECKLIST3.md` で継続予定。

---

## 問題の概要

新しいプロジェクトを開始しても、以前のプロジェクトで編集した `node_0001.asm` などの内容が引き継がれる。

ユーザー視点での症状:
- New Project → Parts 配置 → "プログラムを開く" → 前回のプロジェクトのコードが出る
- プロジェクト A と プロジェクト B で同じ node_id を持つノードのソースが混在する
- タブ名が `AK32 CPU [node_0001].asm` のように内部管理 ID を露出している

---

## 現在の推定原因

### 原因 1: エディタ保存先がグローバル（`build/edit/`）

`ui/editor.py` L36:
```python
_SAVE_DIR = Path("build/edit")
```
L64:
```python
save_path = self._SAVE_DIR / f"{node_id}.{ext}"
```

保存先が `build/edit/<node_id>.<ext>` というグローバルパスで固定されており、プロジェクトに依存しない。
異なるプロジェクトで同じ `node_id`（例: `node_0001`）を持つノードが存在すると、前のプロジェクトの内容を読み込む。

### 原因 2: Build 出力先もグローバル（`build/out/`）

`ui/win.py` L27:
```python
_BUILD_OUT = Path("build/out")
```

プロジェクトをまたいで `build/out/<node_id>.bin` が共有される。

### 原因 3: node_id がユーザー向けファイル名として直接使われている

`ui/editor.py` L58–L64:
```python
base_name = f"{part['name']} [{node_id}].{ext}"
save_path = self._SAVE_DIR / f"{node_id}.{ext}"
```

内部管理 ID（`node_0001` 等）がそのままタブ名・ファイル名になっており、ユーザーにとって分かりにくい。
また、将来 node_id が変わった場合にファイルが対応づかなくなる危険がある。

---

## 修正方針

1. **project_root の外にプロジェクト固有ファイルを保存しない**
2. **node_id は内部管理用 ID として残す**（CanvasやSystem JSONでの識別に使う）
3. **ユーザーが扱うソースファイル名は node_id と分離する**
4. **エディタ保存先をプロジェクトごとの `src/` にする**
5. **Build 出力先をプロジェクトごとの `build/out/` にする**
6. **node_id とソースファイル名の対応を `system.json` の `sources` フィールドに保存する**
7. **New Project 時にエディタタブを全て閉じる**
8. **Open Project 時は project_root を基準にファイルを扱う**

---

## 内部 node_id とユーザー向け source file name の分離方針

| 概念 | 現状 | 修正後 |
|---|---|---|
| 内部 ID | `node_0001` | `node_0001`（変更なし） |
| エディタ保存ファイル | `build/edit/node_0001.asm` | `<project_root>/src/main.asm` |
| Build 出力 | `build/out/node_0001.bin` | `<project_root>/build/out/main.bin` |
| タブ表示名 | `AK32 CPU [node_0001].asm` | `main.asm` |
| ファイル名の決定者 | コード（自動） | ユーザー（ダイアログで入力） |

---

## 新しい保存レイアウト

```
<project_root>/
├─ project.json
├─ system.json        ← sources フィールドを追加
├─ src/
│  ├─ main.asm        ← ユーザーが命名
│  ├─ boot.asm
│  ├─ uart_test.asm
│  └─ cpu_core.v
├─ build/
│  └─ out/
│     ├─ main.bin     ← src ファイル名に対応
│     └─ uart_test.bin
└─ asset/
```

---

## system.json の sources 仕様

`parts[]` の各エントリに `sources` フィールドを追加する。

```json
{
  "parts": [
    {
      "node_id": "node_0001",
      "part_id": "cpu.ak32",
      "name": "AK32 CPU",
      "x": 120,
      "y": 80,
      "sources": {
        "asm": "src/main.asm",
        "hdl": null
      }
    },
    {
      "node_id": "node_0002",
      "part_id": "mem.ram",
      "name": "RAM",
      "x": 300,
      "y": 80,
      "sources": {
        "asm": null,
        "hdl": null
      }
    }
  ]
}
```

- `sources.asm` は `src/<filename>.asm` の相対パス（project_root 基準）、または `null`
- `sources.hdl` は `src/<filename>.v` の相対パス（project_root 基準）、または `null`
- ソース未割り当てのノードは両方 `null`

---

## Open Program / Open HDL の仕様

### ソース未割り当てのとき

1. ファイル名入力ダイアログを表示する（`QInputDialog.getText`）
2. ユーザーが入力例: `main.asm`
3. バリデーションを通過したら `<project_root>/src/main.asm` を作成（新規または既存）
4. `system.json` の `sources.asm` に `src/main.asm` を記録し保存
5. タブを開く（タブ名は `main.asm`）

### ソース割り当て済みのとき

1. `system.json` の `sources.asm`（または `sources.hdl`）のパスを取得
2. `<project_root>/<sources.asm>` を開く
3. タブを開く（タブ名はファイル名）

### project_root 未設定のとき

- Log に「プロジェクトを先に開いてください」と表示してキャンセル

---

## ファイル名バリデーション方針

ダイアログで入力されたファイル名に対して以下を検証する:

| チェック | 理由 |
|---|---|
| 空文字を禁止 | 無名ファイルは意味がない |
| 絶対パスを禁止 | project_root 外への逃げを防ぐ |
| `../` を含むパスを禁止 | ディレクトリトラバーサル防止 |
| `src/` 外への保存を禁止 | プロジェクト構成を維持する |
| `.asm` / `.v` 以外を禁止 | asm は `.asm`、HDL は `.v` のみ対応 |
| Windows で使えない文字を禁止 | `\ / : * ? " < > \|` |
| 同名ファイルが既に存在する場合 | Log に警告して別名入力を促す（上書きは禁止） |

---

## 変更対象ファイル

| ファイル | 変更内容 |
|---|---|
| `ui/editor.py` | `_SAVE_DIR` 廃止。`set_project_root()` 追加。保存先を `project_root/src/<source_name>` に変更。タブ名を `source_name` に変更 |
| `ui/win.py` | New Project 時にタブを全閉じ。project_root を EditorTabs に渡す。Open Program / HDL にダイアログ追加。Build 出力先を `project_root/build/out/` に変更。`_BUILD_OUT` グローバル定数を廃止 |
| `ui/canvas.py` | `export_parts()` / `import_parts()` が `sources` フィールドを扱えるようにする |
| `core/project.py` | `create_project()` が `build/out/` を確実に作るか確認。必要なら追記 |
| `tests/` | プロジェクト分離テスト・バリデーションテスト・sources 保存復元テストを追加 |

---

## 実装順序

1. `core/project.py` — `build/out/` 作成の確認・補完
2. `ui/editor.py` — `set_project_root()` 追加・保存先変更・タブ名変更
3. `ui/canvas.py` — `sources` フィールドの export / import 対応
4. `ui/win.py` — New Project 時のタブクリア、ダイアログ追加、Build 出力先変更
5. テスト追加
6. 手動フロー確認

---

## 完成条件

- [ ] New Project 後に古いソースコードが表示されない
- [ ] Project A の `main.asm` と Project B の `main.asm` が別ファイルになる
- [ ] タブ名が `main.asm` のようなユーザー向け名になる（`node_0001` を含まない）
- [ ] `system.json` の `parts[].sources` にパスが保存・復元される
- [ ] Build 出力が `<project_root>/build/out/<source_name>.bin` に作成される
- [ ] 不正なファイル名が拒否される
- [ ] `pytest tests/` が全件通過する
- [ ] 既存の v0.1 フロー（Build → Run → UART "Hi"）が壊れていない

---

## 回帰テスト方針

修正後も以下を必ず確認する:

- `tests/test_v01_flow.py`（9 件）の全通過
- `tests/test_build.py`（7 件）の全通過
- `tests/test_editor_reload.py` の通過
- 手動: `src/hello.asm` → Build → Run → UART "Hi" → Register View → Bus Trace

---

## 今回やらないこと

- UI Ribbon の追加改善
- VS Code 連携
- 追加命令
- Memory Viewer
- Canvas 接続線
- GPU / VRAM
- 実機出力
- ソースファイルの Rename / Relink 機能
- 複数ソースファイルを 1 ノードに複数割り当てる高度な管理
