# AKDev User Guide

## 画面構成

```
+--[ Ribbon (File / Build-Run / View / Tools) ]--+
|                                                  |
| [Parts Library] | [System Canvas]  | [Properties]|
|                 |                  | [Register V.]|
|                 |                  |              |
+-----------------+------------------+--------------+
| [Log] [UART Console] [Bus Trace] [Memory]         |
+---------------------------------------------------+
```

| エリア | 説明 |
|---|---|
| Ribbon | コマンドバー（File / Build-Run / View / Tools タブ） |
| Parts Library | ドラッグ可能なパーツ一覧 |
| System Canvas | パーツを配置・配線するメインエリア |
| Properties | 選択パーツのプロパティ表示 |
| Register View | CPU レジスタ・PC・サイクル数 |
| Log | ビルド・実行ログ |
| UART Console | UART 出力バッファ |
| Bus Trace | バストランザクション履歴 |
| Memory | RAM hex ダンプ |

---

## Parts Library

- 左パネルにカテゴリ別でパーツが表示される
- ドラッグして System Canvas にドロップで配置
- ダブルクリックまたは Ribbon → Build-Run → Add Part でも配置可能

---

## Canvas 操作

| 操作 | 動作 |
|---|---|
| 左クリック + ドラッグ | パーツ選択・移動 |
| 左ドラッグ（空白） | 範囲選択（ラバーバンド） |
| 右クリック（パーツ） | コンテキストメニュー |
| 中ボタンドラッグ | Canvas Pan（画面移動） |
| ホイール | Zoom In / Out |
| Delete キー | 選択パーツを削除 |

### コンテキストメニュー（パーツ右クリック）

| メニュー | 動作 |
|---|---|
| 接続を開始 | Wire Mode に入り配線を開始 |
| プログラムを開く | .asm エディタタブを開く |
| HDLを開く | .v エディタタブを開く |
| 複製 | パーツをコピー |
| 削除 | パーツを削除 |

---

## Zoom / Grid / Snap

Ribbon → **View** タブで操作できる。

| ボタン | 動作 |
|---|---|
| Zoom In | Canvas を拡大 |
| Zoom Out | Canvas を縮小 |
| Reset Zoom | 等倍に戻す |
| Fit | 全パーツが表示される倍率に調整 |
| Grid | グリッド表示の ON/OFF |
| Snap | グリッドスナップの ON/OFF |

ホイールでも Zoom In/Out できる（マウス位置を中心に拡縮）。

---

## Wire Mode（配線の作成）

1. パーツを右クリック → **接続を開始**
2. 配線中は中間点を右クリックで waypoint（中継点）を追加できる
3. 接続先パーツを右クリック → **ここに接続** で配線完了
4. 右クリック → **キャンセル** で中断

Ribbon → View タブ → **Wire Mode** ボタンで Wire Mode の ON/OFF を切り替えられる。

### 配線の頂点編集（RouteHandle）

Wire Mode で既存の配線に付く橙色の小さな四角をドラッグすると、waypoint を移動できる。BFS 障害物回避ルーティングがリアルタイムで再計算される。

---

## Build / Run / Step / Reset

Ribbon → **Build-Run** タブ。

| ボタン | ショートカット | 動作 |
|---|---|---|
| Build | F5 | アクティブ .asm タブをアセンブル → RAM に書き込み |
| Run | Ctrl+R | 最大 1000 ステップ実行（HALT で停止） |
| Step | Ctrl+T | 1 命令実行 |
| Reset | Ctrl+Shift+R | CPU と UART をリセット（RAM 保持） |

---

## UART Console

- 下部タブの **UART Console** に UART 出力が表示される
- Run / Step 後に自動更新
- Reset でクリア

---

## Register View

- 右パネルの **Register View** タブに以下を表示:
  - `pc` — プログラムカウンタ
  - `cycle` — 実行サイクル数
  - `halted` — HALTED / RUNNING
  - `r0` 〜 `r15` — 汎用レジスタ（r0 は固定ゼロ）
- Run / Step / Reset 後に自動更新

---

## Bus Trace

- 下部タブの **Bus Trace** に以下の形式で記録される:

```
[cycle] READ/WRITE addr=0x... val=0x... (part)
```

- Step / Run 後に追記
- Build / Reset でクリア

---

## Memory Viewer

- 下部タブの **Memory** に RAM の hex ダンプが表示される:

```
0x0000  4C 44 49 20 72 32 2C 30  LDI r2,0
0x0008  78 31 30 30 0A 00 00 00  x100....
```

- 1 行 16 bytes。左: アドレス / 中: hex / 右: ASCII（非印字文字は `.`）
- PC が属する行を薄い黄色でハイライト
- Build / Run / Step / Reset 後に自動更新

---

## PC Highlight（エディタ行ハイライト）

Build → Run または Step 実行後、エディタの現在 PC 行が薄い緑色でハイライトされる。

- `address_map[cpu.pc]` でソース行を逆引きして表示
- Build 時にクリア
- Reset 時にクリア

---

## Canvas Signal Overlay

Run / Step 後、バストランザクションが発生した接続線が明るく光る。

- Bus kind の接続線のみ対象
- Reset でクリア

---

## プロジェクト保存 / 読み込み

| 操作 | 方法 |
|---|---|
| New Project | Ribbon File → New Project（フォルダ + 名前を選択） |
| Open Project | Ribbon File → Open Project（`project.json` を選択） |
| Save | Ctrl+S または Ribbon File → Save Project |
| Save As | Ctrl+Shift+S または Ribbon File → Save Project As |

保存ファイル:
- `project.json` — プロジェクトメタデータ
- `system.json` — Canvas 状態（パーツ位置・接続情報）
- `src/<node_id>.asm` — アセンブリソース
- `build/out/<node_id>.bin` — ビルド成果物
- `target.json` — ビルドターゲット設定
- `tools.json` — 外部ツール設定

---

## 既知の制限

| # | 内容 |
|---|---|
| 1 | CALL / RET / IN 命令は未実装（→ v0.5） |
| 2 | ブレークポイント UI は未実装（→ v0.5） |
| 3 | パーツサイズのカスタマイズは未実装（→ v0.5） |
| 4 | VS Code Companion 連携は未実装（→ v0.5） |
| 5 | 接続線の色変更 UI は未実装（→ v0.5） |
| 6 | `project.json` が壊れているとクラッシュする可能性がある |
| 7 | パーツが Canvas に 1 個もない状態で Run すると動作しない |
