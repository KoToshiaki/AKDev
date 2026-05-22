# AKDev CHECKLIST 2

> これから使う実用チェックリストです。完了済みの基盤を前提に、残り作業を中心に記載しています。
> 詳細な旧チェックリストは `old/CHECKLIST.md` を参照してください。

---

# 0. 現在の基盤（完了済み）

* [x] GUI 骨組み（QMainWindow / メニュー / ツールバー / Dock）
* [x] Parts Library（`parts/` スキャン・カテゴリ表示・11 パーツ定義）
* [x] System Canvas（配置・移動・選択・削除・右クリックメニュー）
* [x] node_id インスタンス管理（`node_0001` 形式、同種複数対応）
* [x] Properties パネル（名前・ID・カテゴリ・説明・ポート・resources 表示）
* [x] タブエディタ（`.asm` / `.v`、dirty マーク、`build/edit/` 仮保存）
* [x] シンタックスハイライト（.asm / .v）・現在行ハイライト
* [x] プロジェクト保存／読み込み（`project.json` / `system.json`）
* [x] Canvas 座標保存復元（`export_parts()` / `import_parts()`）
* [x] シミュレータ基盤（Part / Port / Bus / Chip / Sim — `core/sim.py`）
* [x] RamPart（32-bit LE、BusError、load_bytes — `core/dev.py`）
* [x] UartPart（TX バッファ、CR/LF 正規化、status stub — `core/dev.py`）
* [x] AK32Part（NOP/HALT/LDI/OUT、r0 固定ゼロ — `core/cpu.py`）
* [x] ヘッドレステスト（Bus フェッチで UART に "Hi" 出力確認済み）

---

# 1. v0.1 仕上げ

## 1.1 エディタ再読み込み（バグ B-1 修正）

* [x] `open_tab()` で `build/edit/<node_id>.<ext>` が存在すれば読み込む
  - 完了条件: タブを閉じて「プログラムを開く」を再実行しても内容が復元される

## 1.2 最小アセンブラ（`asm/asm.py`）

* [ ] 行読み込み・コメント除去・空行スキップ
  - 完了条件: `#` コメントと空行が正しく無視される
* [ ] トークン化（ニーモニック / レジスタ / 即値）
  - 完了条件: `LDI r1, 72` が `['LDI', 'r1', '72']` に分解される
* [ ] ラベル解析（1 パス目でアドレス収集）
  - 完了条件: `loop:` 形式のラベルが認識される
* [ ] 命令エンコード（NOP / HALT / LDI / OUT の 4 命令）
  - 完了条件: 各命令が 32-bit LE バイナリに正しく変換される
* [ ] バイナリ出力（`bytearray` / ファイル書き出し）
  - 完了条件: アセンブル結果を `bytes` として返せる
* [ ] エラー報告（行番号付きエラーメッセージ）
  - 完了条件: 不正命令・不正レジスタ・即値範囲外を行番号付きで返す

## 1.3 Build ボタンとアセンブラの接続

* [ ] `Build > Build`（F5）でアクティブタブの内容をアセンブルする
  - 完了条件: asm タブがアクティブなとき F5 でビルドが走る
* [ ] 成功時にバイナリを `build/<node_id>.bin` に保存する
  - 完了条件: `build/` に `.bin` ファイルが生成される
* [ ] 失敗時に Log パネルにエラーを出す
  - 完了条件: エラー行番号がログに表示される

## 1.4 asm → binary → RAM ロード

* [ ] ビルド成功後に対象 RAM PartNode を特定する
  - 完了条件: CPU ノードと同一 Chip 上の RAM を自動選択（または手動指定）
* [ ] `RamPart.load_bytes()` でバイナリを RAM にロードする
  - 完了条件: ビルド後に CPU が即実行できる状態になる

## 1.5 GUI から Sim 実行

* [ ] `Run > Reset`（Ctrl+Shift+R）で `Sim.reset()` を呼ぶ
  - 完了条件: CPU pc / regs / halted が初期化される
* [ ] `Run > Step`（F10）で `Sim.step()` を 1 回呼ぶ
  - 完了条件: 1 命令実行されて Register View が更新される
* [ ] `Run > Run`（Ctrl+R）で HALT または指定サイクルまで連続実行する
  - 完了条件: HALT で自動停止する
* [ ] `Run > Pause`（F6）で実行を中断する
  - 完了条件: Run 中に Pause できる

## 1.6 UART Console

* [ ] UART 出力を表示するパネルを追加する
  - 完了条件: UartPart.output_text() の内容がリアルタイムで表示される
* [ ] Reset 時に UART 出力をクリアする
  - 完了条件: Reset 後にコンソールが空になる

## 1.7 Register View

* [ ] r0〜r15 と pc を表示するパネルを追加する
  - 完了条件: Step/Run のたびに表示が更新される
* [ ] halted 状態を表示する
  - 完了条件: HALT 命令実行後に "HALTED" が表示される

## 1.8 Bus Trace

* [ ] Bus の read/write をログに記録する
  - 完了条件: CPU の OUT 実行時に `[cycle] WRITE addr = value` が Log に出る
* [ ] Bus Trace パネルまたは Log への出力として実装する
  - 完了条件: UART write が Bus Trace に見える

## 1.9 v0.1 統合テスト

* [ ] asm ソース（LDI + OUT + HALT で "Hi" を出力）を書く
  - 完了条件: ファイルが `src/hello.asm` に保存されている
* [ ] Build → RAM ロード → Run の全フローを GUI 上で実行する
  - 完了条件: UART Console に "Hi" が表示される
* [ ] Register View が実行後に正しい値を表示する
  - 完了条件: r1=105 (最後の LDI)、pc=HALT 位置が表示される
* [ ] Bus Trace に OUT write が表示される
  - 完了条件: UART アドレスへの write ログが見える

---

# 2. v0.1 バグ修正・品質改善

## 2.1 バグ修正

* [x] B-1: エディタ再読み込み（1.1 で対応済み）
* [ ] project save と editor save の責務整理
  - 完了条件: Ctrl+S でキャンバスと現在タブの両方が保存される（現状は save_current を呼んでいるが不完全な場合がある）
* [ ] 不正 JSON 読み込み時のエラーハンドリング
  - 完了条件: project.json / system.json が壊れていても Log にエラーを出してクラッシュしない

## 2.2 品質改善

* [ ] system.json の parts をソートして保存する（node_id 順）
  - 完了条件: 保存のたびに順序が変わらない
* [ ] タブが 0 枚のとき save_current() が None を返すことを UI 側でケアする
  - 完了条件: タブなし状態で Ctrl+S してもエラーが出ない

---

# 3. v0.2 候補

## 3.1 ポート・接続

* [ ] Canvas 上のノードにポートを描画する
  - 完了条件: パーツ定義の ports が視覚的に表示される
* [ ] ポート間を接続線で繋げる
  - 完了条件: ドラッグで接続線を引ける
* [ ] 接続情報を system.json に保存・復元する
  - 完了条件: プロジェクトを開き直しても接続線が復元される

## 3.2 Memory Viewer

* [ ] 選択 RAM の hex ダンプを表示するパネルを作る
  - 完了条件: 16 バイト × N 行の hex + ASCII 表示
* [ ] Step/Run のたびに更新される
  - 完了条件: 実行後に変化したアドレスが分かる

## 3.3 Timer パーツ

* [ ] `core/dev.py` に TimerPart を追加する
  - 完了条件: count register / compare register / enable flag を持つ
* [ ] tick() ごとにカウントアップする
  - 完了条件: compare 一致時に IRQ flag をセットする

## 3.4 追加命令

* [ ] ADD rd, ra, rb
* [ ] SUB rd, ra, rb
* [ ] AND rd, ra, rb
* [ ] OR rd, ra, rb
* [ ] XOR rd, ra, rb
* [ ] SHL rd, ra, imm
* [ ] SHR rd, ra, imm
* [ ] LD rd, [ra + imm]
* [ ] ST rs, [ra + imm]
* [ ] JMP addr
* [ ] BEQ ra, rb, offset
* [ ] BNE ra, rb, offset
* [ ] CALL addr
* [ ] RET
* [ ] IN rd, [addr]
  - 完了条件（各命令）: ヘッドレステストで動作確認済み

## 3.5 アセンブラ強化

* [ ] 全追加命令のエンコードを実装する
  - 完了条件: 3.4 の全命令が .asm からバイナリに変換できる
* [ ] 2 パス処理でラベル前方参照を解決する
  - 完了条件: ラベルを先に使って後で定義できる
* [ ] disasm（バイナリ → asm テキスト）を作る
  - 完了条件: バイナリを逆アセンブルして表示できる

---

# 4. 後工程

## 4.1 グラフィック

* [ ] Graphics Register パーツを実装する
* [ ] VRAM パーツを実装する
* [ ] Virtual Screen パネルを作る
* [ ] BG_COLOR 書き込みで画面色が変わる

## 4.2 Tile / Sprite

* [ ] Tile Memory を実装する
* [ ] Tile Map を実装する
* [ ] Sprite Table を実装する
* [ ] VBlank tick を実装する

## 4.3 実機向け

* [ ] 実機エクスポート（メモリマップヘッダ・Verilog 雛形）
* [ ] UART 実機接続（シリアルポート選択・送信）

## 4.4 アセットツール

* [ ] PNG インポート・パレット変換・タイルデータ生成
* [ ] ROM Builder（game.rom 生成）
