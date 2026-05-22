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

## 読んだファイル

| ファイル | 内容 |
|---|---|
| `ROADMAP.md` | 全体設計・フェーズ計画・仕様概要 |
| `CHECKLIST.md` | 実装進捗チェックリスト |

---

## 作成・変更したファイル

### 新規作成

| ファイル | 説明 |
|---|---|
| `.gitignore` | Python / ビルド成果物 / エディタ一時ファイルの除外設定 |
| `README.md` | プロジェクト概要・セットアップ・起動方法 |
| `LICENSE` | MIT ライセンス |
| `requirements.txt` | 依存ライブラリ（PySide6>=6.6.0） |
| `main.py` | 起動エントリポイント。`ui.win.MainWin` を呼ぶ最小骨組み |
| `ui/__init__.py` | ui パッケージ化 |
| `ui/win.py` | MainWin スタブ。ウィンドウタイトルと初期サイズのみ |
| `core/__init__.py` | core パッケージ化 |
| `asm/__init__.py` | asm パッケージ化 |
| `spec/cpu.md` | AK32 CPU 仕様（レジスタ・命令セット・エンコード） |
| `spec/gpu.md` | グラフィックレジスタ仕様（アドレス・コマンド一覧） |
| `spec/mem.md` | メモリマップ仕様（アドレス範囲・アクセス幅） |
| `spec/bus.md` | バス仕様・アドレスルーティング・Bus Trace フォーマット |
| `spec/rom.md` | ROM ファイル形式仕様（ヘッダ・セクション構造） |
| `spec/part.md` | part.json 定義仕様（必須・任意フィールド・ポート型一覧） |
| `spec/project.md` | project.json / system.json のフォーマット仕様 |

### 作成済みディレクトリ

```
core/   ui/   asm/
parts/fpga/   parts/cpu/   parts/mem/
parts/io/     parts/video/ parts/custom/
spec/   sample/hello/   sample/video_test/
docs/   build/
asset/img/   asset/snd/   asset/map/
```

### 変更

| ファイル | 変更内容 |
|---|---|
| `CHECKLIST.md` | セクション 1.1〜1.4 の完了項目を `[x]` に更新 |

---

## 未完了の作業

### Git 初期化（1.1）

環境に Git がインストールされていなかったため以下が未完了:

- `git init`
- `main` ブランチ作成
- `dev` ブランチ作成

**対処方法**: Git をインストール後、プロジェクトルートで以下を実行。

```
git init
git checkout -b main
git add .
git commit -m "init: project foundation"
git checkout -b dev
```

### アプリ起動確認（2.1）

PySide6 をインストールして `python main.py` を実行し、ウィンドウが表示されることを手動確認する必要がある。

```
pip install -r requirements.txt
python main.py
```

---

## Git が未設定だった理由

PowerShell の PATH に `git` が登録されていなかった。
`Get-Command git` で見つからず、`C:\Program Files\Git` も存在しなかった。
Git 自体がインストールされていない可能性が高い。

---

## CHECKLIST.md のどこまで進んだか

| セクション | 状態 |
|---|---|
| **1.1 リポジトリ初期化** | `.gitignore` のみ完了。git 操作は未完了 |
| **1.2 基本ファイル** | 完了 |
| **1.3 ディレクトリ構成** | 完了 |
| **1.4 初期仕様書** | 完了 |
| **2. アプリ起動と GUI 骨組み** | 未着手 |
| **3 以降** | 未着手 |

---

## 次にやるべき作業

優先順（ROADMAP.md の推奨順に従う）:

1. **PySide6 インストール** — `pip install -r requirements.txt`
2. **アプリ起動確認** — `python main.py` でウィンドウが出ることを確認
3. **メインレイアウト実装（2.2）** — `ui/win.py` に以下を追加:
   - 左: Parts Library パネル（`QDockWidget` + `QTreeWidget`）
   - 中央: System Canvas（`QGraphicsView`）
   - 右: Properties パネル（`QDockWidget`）
   - 下: Log / Console パネル（`QDockWidget` + `QTextEdit`）
4. **メニューバー実装（2.3）** — File / Build / Run / View メニュー
5. **ツールバー実装（2.4）** — New / Open / Save / Build / Run / Pause / Step / Reset ボタン

---

## 次回 Claude Code に最初に指示する文章

```
このフォルダには AKDev という自作ゲーム機用 IDE を作るプロジェクトがあります。

まず HANDOFF.md を読み、次に CHECKLIST.md の現在の状態を確認してください。

前回の作業で「1. プロジェクト基盤」が完了しています。
今回は「2. アプリ起動と GUI 骨組み」から再開します。

方針:
- 一度に大きく作らないこと
- 各ステップごとに実装内容・変更ファイル・確認方法を説明すること
- 完了した CHECKLIST.md の項目は [x] に更新すること
- 仕様は ROADMAP.md を優先すること
- ファイル名・関数名は短くすること

まず 2.1 アプリ起動から進めてください。
PySide6 を使い、メインウィンドウを表示するところまで実装してください。
```
