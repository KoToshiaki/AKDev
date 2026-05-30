# AKDev Quick Start — 5 分で hello.asm を動かす

## 環境準備

```
Python 3.11 以上
pip install -r requirements.txt
```

## 起動

```
python main.py
```

## 新規プロジェクト作成

1. Ribbon の **File** タブ → **New Project** をクリック
2. 保存先フォルダを選択し、プロジェクト名を入力（例: `myproject`）
3. **OK** → `myproject/` が作成され、プロジェクトが開く

## AK32 CPU / RAM / UART 配置

Parts Library（左パネル）から以下をドラッグ＆ドロップで System Canvas に配置する:

| パーツ | カテゴリ |
|---|---|
| AK32 CPU | cpu |
| RAM 32K | mem |
| UART | io |

## プログラムを開いてビルド

1. System Canvas で **AK32 CPU ノード** を右クリック → **プログラムを開く**
2. エディタタブに `src/hello.asm` の内容（または下記）を入力:

```asm
; hello.asm — UART に "Hi" を出力
LDI r2, 0x100   ; UART base address
LDI r1, 72      ; 'H' = 72
OUT [r2], r1
LDI r1, 105     ; 'i' = 105
OUT [r2], r1
HALT
```

3. **F5** キー（または Ribbon → Build-Run タブ → **Build**）でアセンブル

## Run — UART に "Hi" が出る確認

1. Ribbon → Build-Run タブ → **Reset**（または Ctrl+Shift+R）
2. Ribbon → Build-Run タブ → **Run**（または Ctrl+R）
3. 下部 **UART Console** タブに `Hi` と表示されれば成功

## よくある詰まり

| 症状 | 対処 |
|---|---|
| Build でエラー | UART アドレスや即値の形式を確認（`0x100` 形式 OK） |
| UART Console に何も出ない | Reset してから Run する |
| プロジェクトが開けない | `project.json` があるフォルダを選択する |
| Canvas が動かない | ホイールでズーム、中ボタンドラッグでパン |

詳しい操作は [USER_GUIDE.md](USER_GUIDE.md) を参照してください。
