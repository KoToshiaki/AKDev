# AKDev 引き継ぎメモ

作成日: 2026-05-22

---

## 現在の目的

AKDev v0.1 Minimal Interactive Simulator の実装。
自作 FPGA ゲーム機向けの統合開発環境兼シミュレータ。

最初のマイルストーンは以下がすべて動くこと:

- メインウィンドウが開く ✅
- Parts Library と System Canvas が見える ✅
- chip0 / AK32 / RAM / UART をキャンバスに配置できる ✅
- 右クリックメニューが動く ✅
- アセンブラで `main.asm` をビルドできる
- CPU がプログラムを実行し、UART に `Hi` が出る
- Register View と Bus Trace が更新される

---

## Git の状態

- Git インストール済み（2.54.0.windows.1）
- リポジトリ初期化済み
- 現在ブランチ: `dev`
- `dev` はクリーン
- 直近のコミット履歴:
  - `docs: clarify checklist pending items`
  - `canvas: add node context menu`
  - `canvas: add basic part node placement`
  - `parts: add initial part library loader`
  - `ui: add menu actions and toolbar buttons`
  - `docs: update HANDOFF.md for session 2`

---

## CHECKLIST.md のどこまで進んだか

| セクション | 状態 |
|---|---|
| **1.1 リポジトリ初期化** | 完了 |
| **1.2 基本ファイル** | 完了 |
| **1.3 ディレクトリ構成** | 完了 |
| **1.4 初期仕様書** | 完了 |
| **2.1 アプリ起動** | 完了 |
| **2.2 メインレイアウト** | 完了 |
| **2.3 メニュー項目** | 完了（プレースホルダ実装、Log にアクション名を出力） |
| **2.4 ツールバー** | 完了（同上） |
| **3. プロジェクト保存形式** | 未着手 |
| **4.1 パーツ定義形式** | 完了 |
| **4.2 パーツ読み込み** | 完了 |
| **4.3 初期パーツ作成** | 完了（11 パーツ） |
| **4.4 パーツカテゴリ表示** | 完了（FPGA/CPU/Memory/I/O/Video/Bus） |
| **4.5 自作パーツ** | 部分完了（スキャン・エラー表示済み / テンプレートは後工程） |
| **5.1 パーツ配置** | 完了（ダブルクリック追加・移動・選択・Delete 削除） |
| **5.2〜5.5** | 未着手 |
| **6.1 右クリックメニュー** | 完了（7 項目表示） |
| **6.2 メニュー動作** | 部分完了（複製・削除のみ / タブ・Properties 連携は後工程） |
| **6.3 パーツ別メニュー** | 未着手（シミュレータ実装後） |
| **7. Properties パネル** | 未着手 ← 次はここ |
| **8 以降** | 未着手 |

---

## 現在の画面状態

```
┌─────────────────────────────────────────────────────┐
│ File  Build  Run  View          [メニューバー]        │
│ [New][Open][Save] | [Build] | [Run][Pause][Step][Reset]│
├────────────────┬────────────────────────┬────────────┤
│ Parts Library  │   System Canvas        │ Properties │
│                │                        │            │
│ ▶ FPGA         │  [node] [node] ...     │ (no        │
│ ▶ CPU          │                        │ selection) │
│ ▶ Memory       │  ノードはドラッグ移動   │            │
│ ▶ I/O          │  右クリックメニュー有   │            │
│ ▶ Video        │                        │            │
│ ▶ Bus          │                        │            │
├────────────────┴────────────────────────┴────────────┤
│ Log / Console  │  Editor                             │
│  (ログ出力)    │  (テキストエリア)                    │
└─────────────────────────────────────────────────────┘
```

- Parts Library のパーツをダブルクリック → キャンバスに追加
- ノードをドラッグ → 移動
- ノードをクリック → 選択（白枠）
- 空白でドラッグ → ラバーバンド複数選択
- Delete キー → 選択ノードを削除
- ノード右クリック → コンテキストメニュー（複製・削除は動作、他は Log 出力のみ）

---

## 主要ファイル一覧

| ファイル | 役割 |
|---|---|
| `main.py` | エントリーポイント |
| `ui/win.py` | メインウィンドウ（レイアウト・メニュー・ツールバー・各パネルのセットアップ） |
| `ui/canvas.py` | System Canvas（`PartNode` / `Canvas` クラス） |
| `ui/lib.py` | パーツライブラリローダー（`load_parts()` / `cat_label()`） |
| `parts/*/part.json` | パーツ定義（fpga/cpu/mem/io/video/bus の 11 種） |

### SPDX ヘッダのルール

今後の Python ソースコードには先頭に以下を付ける:

```python
# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
```

---

## 既知バグ

| # | 症状 | 原因 | 対応予定 |
|---|---|---|---|
| 1 | タブを閉じて再度「プログラムを開く」すると内容が消える | `save_current()` は `build/edit/<node_id>.<ext>` に保存するが、`open_tab()` で保存済みファイルを読み込んでいない | 最後のテスト・修正フェーズで対応 |

---

## 次にやるべき作業

### 7.1 Properties パネルの基本表示（`ui/win.py` + `ui/prop.py` 新規作成）

キャンバスでノードを選択したとき、右側の Properties ドックに以下を表示する:

- パーツ名
- パーツ ID
- カテゴリ
- 説明（`description`）
- ポート一覧（`ports[].name` と `ports[].type`）

実装の流れ:
1. `ui/prop.py` を新規作成（`PropPanel` クラス、`QWidget` ベース）
2. `Canvas` の `selectionChanged` シグナルを `win.py` に引き回す
3. `win.py._setup_properties()` で `PropPanel` を Properties ドックに設定
4. 選択ノードが変わったら `PropPanel.show_part(part_dict)` を呼ぶ

完了条件:
- キャンバスのノードをクリックすると右側 Properties に情報が表示される
- 選択解除（空白クリック）すると `(no selection)` 表示に戻る

---

## 次回 Claude Code に最初に指示する文章

```
HANDOFF.md、ROADMAP.md、CHECKLIST.md を読んで現在の状態を確認してください。

前回の作業で以下が完了しています:
- 2.2 メインレイアウト
- 2.3 メニュー項目 / 2.4 ツールバー（プレースホルダ実装）
- 4. パーツライブラリ（part.json 読み込み・カテゴリ表示）
- 5.1 System Canvas（パーツ配置・移動・選択・削除）
- 6.1 右クリックメニュー（複製・削除動作済み）
- CHECKLIST.md 整理済み

今回は「7. Properties パネル」の 7.1 基本表示を進めてください。

作業内容:
1. ui/prop.py を新規作成してください（SPDX ヘッダ付き）
2. PropPanel クラスを実装してください
   - 選択パーツの name / id / category / description / ports を表示する
   - ポートは「名前: 型」形式で列挙する
   - 選択なし時は「(no selection)」を表示する
3. ui/win.py を変更し、Canvas の selectionChanged シグナルと PropPanel を接続してください
4. 起動確認後、CHECKLIST.md の 7.1 完了項目を [x] に更新してください
5. commit してください（message: ui: add properties panel basic display）
```

---

## セッション記録

### セッション 1（2026-05-22）

**主な作業:**
- プロジェクト基盤（`.gitignore` / `README.md` / `requirements.txt` / `main.py` / `ui/win.py`）を作成
- ディレクトリ構成と初期仕様書（`spec/*.md`）を作成
- CHECKLIST.md 1.1〜1.4 を更新
- Git が未インストールのため初期化は未完了

**残課題（セッション 2 に持ち越し）:**
- Git 初期化、`dev` ブランチ作成
- PySide6 インストールと起動確認

### セッション 2（2026-05-22）

**主な作業:**
- Git が利用可能なことを確認（`git version 2.54.0.windows.1`）
- 初回コミット（`initial project setup`）が既に完了していることを確認
- `dev` ブランチを作成（`git checkout -b dev`）
- LICENSE を MIT → BSD-3-Clause に変更（著作権: Toshiaki Kou 2026）
- `main.py` / `ui/win.py` / `{core,ui,asm}/__init__.py` に SPDX ヘッダを追加
- `python -m pip install -r requirements.txt` で PySide6 6.11.1 をインストール
- `MainWin` インスタンス化テストで起動確認（タイトル `AKDev`、サイズ `1280×800`）
- CHECKLIST.md 1.1（git 項目）・2.1（全 7 項目）を `[x]` に更新
- 変更を 2 コミットで `dev` に記録

### セッション 3（2026-05-22）

**主な作業:**
- `ui/win.py` に 2.2 メインレイアウト実装
  - 左 Dock: Parts Library（`QDockWidget` + `QTreeWidget`）
  - 中央: System Canvas（`QGraphicsView`）
  - 右 Dock: Properties（プレースホルダ）
  - 下 Dock: Log / Console（`QTextEdit` + Editor タブ）
- `ui/win.py` に 2.3 メニュー項目・2.4 ツールバーを実装
  - File / Build / Run / View メニューに QAction 追加（ショートカット付き）
  - ツールバーに New / Open / Save / Build / Run / Pause / Step / Reset ボタン追加
  - 全 action はクリックで Log に `Action: <name>` を出力
- `ui/lib.py` を新規作成（パーツライブラリローダー）
  - `parts/` 以下を再帰スキャン、必須キー検証、エラー収集
- `parts/` 以下に 11 個の `part.json` を作成（fpga×2, cpu, mem×2, io×3, video×2, bus）
- `ui/win.py` の Parts Library を `load_parts()` 使用に変更
- `ui/canvas.py` を新規作成
  - `PartNode`（`QGraphicsItem`）: カテゴリ別色、パーツ名・ID 表示、移動・選択対応
  - `Canvas`（`QGraphicsView`）: ダブルクリック追加、Delete 削除、右クリックメニュー
- 右クリックメニュー（複製・削除は動作、他は Log 出力）
- CHECKLIST.md の歯抜け整理（実装済み `[ ]` の `[x]` 化、後工程依存の注記追加）
