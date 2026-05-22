# AKDev 引き継ぎメモ

作成日: 2026-05-22

---

## 現在の目的

AKDev v0.1 Minimal Interactive Simulator の実装。
自作 FPGA ゲーム機向けの統合開発環境兼シミュレータ。

最初のマイルストーンは以下がすべて動くこと:

- メインウィンドウが開く
- Parts Library と System Canvas が見える
- chip0 / AK32 / RAM / UART をキャンバスに配置できる
- 右クリックメニューが動く
- アセンブラで `main.asm` をビルドできる
- CPU がプログラムを実行し、UART に `Hi` が出る
- Register View と Bus Trace が更新される

---

## Git の状態

- Git インストール済み（2.54.0.windows.1）
- リポジトリ初期化済み、コミット済み
- 現在ブランチ: `dev`
- `main` / `dev` どちらもクリーン
- コミット履歴:
  - `initial project setup`
  - `license: change to BSD-3-Clause; add SPDX headers; mark 2.1 done`
  - `chore: mark dev branch created in checklist`

---

## CHECKLIST.md のどこまで進んだか

| セクション | 状態 |
|---|---|
| **1.1 リポジトリ初期化** | 完了 |
| **1.2 基本ファイル** | 完了 |
| **1.3 ディレクトリ構成** | 完了 |
| **1.4 初期仕様書** | 完了 |
| **2.1 アプリ起動** | 完了 |
| **2.2 メインレイアウト** | 未着手 ← 次はここ |
| **2.3 メニュー項目** | 未着手 |
| **2.4 ツールバー** | 未着手 |
| **3 以降** | 未着手 |

---

## 変更済みファイル一覧

| ファイル | 内容 |
|---|---|
| `LICENSE` | BSD-3-Clause（著作権: Toshiaki Kou 2026）に変更 |
| `main.py` | SPDX ヘッダ追加 |
| `ui/win.py` | SPDX ヘッダ追加 |
| `core/__init__.py` | SPDX ヘッダのみ（パッケージマーカー） |
| `ui/__init__.py` | SPDX ヘッダのみ（パッケージマーカー） |
| `asm/__init__.py` | SPDX ヘッダのみ（パッケージマーカー） |
| `CHECKLIST.md` | 1.1 / 2.1 全項目を `[x]` に更新 |

### SPDX ヘッダのルール

今後の Python ソースコードには先頭に以下を付ける:

```python
# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
```

---

## 次にやるべき作業

### 2.2 メインレイアウト（`ui/win.py` を編集）

- 左: Parts Library パネル（`QDockWidget` + `QTreeWidget`）
- 中央: System Canvas（`QGraphicsView`）
- 右: Properties パネル（`QDockWidget`）
- 下: Log / Console パネル（`QDockWidget` + `QTextEdit`）
- すべてリサイズ可能にする

### 2.3 メニュー項目

File / Build / Run / View の各メニューを追加する。

### 2.4 ツールバー

New / Open / Save / Build / Run / Pause / Step / Reset ボタンを追加する。

---

## 次回 Claude Code に最初に指示する文章

```
このフォルダには AKDev という自作ゲーム機用 IDE を作るプロジェクトがあります。

まず HANDOFF.md を読み、次に CHECKLIST.md の現在の状態を確認してください。

現在の状態:
- Git: dev ブランチで作業中
- CHECKLIST.md の 1.1〜1.4、2.1 が完了済み
- 次は 2.2 メインレイアウトから再開する

方針:
- 一度に大きく作らないこと
- 各ステップごとに実装内容・変更ファイル・確認方法を説明すること
- 完了した CHECKLIST.md の項目は [x] に更新すること
- 仕様は ROADMAP.md を優先すること
- ファイル名・関数名は短くすること
- 新規 Python ファイルには SPDX ヘッダを付けること

2.2 メインレイアウトを実装してください。
ui/win.py に QDockWidget を使って以下を追加してください:
- 左: Parts Library パネル（QTreeWidget）
- 中央: System Canvas（QGraphicsView）
- 右: Properties パネル
- 下: Log / Console パネル（QTextEdit）
実装後は python main.py で起動確認し、CHECKLIST.md を更新してください。
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
