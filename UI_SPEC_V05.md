# AKDev UI_SPEC_V05

> v0.5 UI Polish & Usability の仕様書。
> 設計方針は `ROADMAP6.md` を参照。
> 進捗管理は `CHECKLIST6.md` を参照。

最終更新: 2026-06-07（PATCH_WIRING_PORTS_V05 — Dynamic Visual Port）

---

## 0. v0.5 の目的

**AKDev を「機能が動くアプリ」から「人間が迷わず使える開発環境」にする。**

v0.4.1 までで機能は一通り動作する。v0.5 では、増え続ける機能に対して UI が
破綻しないよう、入口（Hub）・初期表示・リボン構成・操作性・見た目の土台を整える。

将来（v1.0）では自作 CPU 上でゲーム実行環境を動かし、1 本のゲームを起動できる
状態を目指す。そのため v0.5 では大機能追加ではなく、**UI の整理・拡張性・操作性の
改善**を優先する。

### プロトタイプ方針

このフェーズの最初の実装は **v0.5 UI Prototype Patch** として扱う。
完成版 UI ではなく、**使いやすい UI の方向性を確認するためのたたき台**である。
最終 UI はユーザーの UI ラフ受領後に確定する（セクション 12）。

---

## 1. 現在の UI の問題点

### 1-1. リボンの問題

| 問題 | 詳細 |
|---|---|
| タブが少なくボタンが密集 | 現行は File / Build-Run / View / Tools の 4 タブしかない |
| View タブに何でも入る | Zoom / Grid / Snap / Wire Mode / Debug パネルトグルが混在している |
| パーツ操作とデバッグ操作が分離されていない | 同じタブに無関係な機能が並ぶ |
| Build-Run タブが操作ハブになりすぎ | Build / Step / Run / Reset / Pause の全操作が 1 タブに集中 |

### 1-2. パネルの問題

| 問題 | 詳細 |
|---|---|
| デバッグパネルが常時表示 | Register View / Memory Viewer / Bus Trace / UART Console は常時 dock されている |
| 非表示にする方法が分かりにくい | View タブのトグルボタンを探す必要がある |
| パネルが多いと Canvas 面積が狭くなる | 縦横に複数の Dock が配置されると Canvas が圧迫される |
| 将来のパネル増加に耐えられない | Video / Input / Display 等が増えるとさらに逼迫する |

### 1-3. Canvas の問題

| 問題 | 詳細 |
|---|---|
| ノードの色がカテゴリ色のみ | part.json の color / size フィールドは未実装 |
| 接続線の kind 判別が視覚的に難しい | 太さの違いのみで色は青一色（bus）または細め（signal 等） |
| ポート情報がノード上に見えない | ポート名・方向・幅を確認する方法がない |

### 1-4. 操作性の問題

| 問題 | 詳細 |
|---|---|
| Wire Mode の開始方法が分かりにくい | 右クリックメニューの深い階層にある |
| ショートカットが整理されていない | F5（Build）以外に一般的なショートカットが少ない |
| Canvas Pan が中ボタンのみ | マウスに中ボタンがない環境では使いにくい（v0.4.1 で修正済みだが追加方法の整理が必要） |

### 1-5. 入口・ブランドの問題

| 問題 | 詳細 |
|---|---|
| 開発 Hub としての入口がない | 起動直後からいきなり Workspace が表示される |
| 拡張時に入口が必要 | 将来 OS / コンパイラ / ゲーム機開発などへ拡張するには Hub 画面が要る |
| 初見ユーザーの注意が奪われる | 初期表示で Register View / Memory などが見えている |
| Canvas が主役なのに圧迫される | 周辺パネルで作業領域が狭くなっている |
| リボンの分類が粗い | Parts / Wiring / Run / Debug の導線が弱い |
| ボタンが素人っぽく見える | 枠線が強く、もっさりして見える |
| ブランド感が弱い | 文字中心で、ロゴ・アイコン・アクセントカラーがない |
| Debug 情報が前面に出すぎ | デバッグ系が最初から目立つ位置にある |

---

## 2. v0.5 UI 設計方針

### 基本方針

1. **拡張性**: 将来の機能追加に対して UI が破綻しない設計にする
2. **操作性**: よく使う操作が 1〜2 アクションで届く位置に置く
3. **シンプル表示**: 初期表示は最低限。必要なものは表示・非表示を切り替える
4. **UI ラフ優先**: ユーザーが作成した UI ラフを優先して実装範囲を確定する

---

## 3. 初期表示パネル

起動時に常時表示するパネル（シンプルセット）:

| パネル | 配置 | 表示理由 |
|---|---|---|
| Ribbon | 上部 | 必須操作ハブ |
| Parts Library | 左 Dock | パーツ配置の出発点 |
| System Canvas | 中央 | メイン作業エリア |
| Properties | 右 Dock | 選択パーツの情報確認 |
| Log | 下 Dock | エラー・通知の確認 |

---

## 4. 非表示・表示切替パネル

必要時のみ表示するパネル（トグルで出せる）:

| パネル | 推奨表示タイミング | 表示トリガーの候補 |
|---|---|---|
| Register View | Run / Step 実行時 | Debug タブのトグル |
| Memory Viewer | RAM 内容確認時 | Debug タブのトグル |
| Bus Trace | バストランザクション確認時 | Debug タブのトグル |
| UART Console | UART 出力確認時 | Debug タブのトグル |
| Port Detail | ノードのポート確認時 | ノードダブルクリック / コンテキストメニュー |
| Signal Overlay 設定 | 接続線の色設定時 | Wiring タブのボタン（v0.6 以降） |

現行の View タブにあるデバッグパネルトグルは、**Debug タブ**に移設する。

---

## 5. リボンタブ構成（案）

### Project タブ

| ボタン / 操作 | 機能 |
|---|---|
| New Project | 新規プロジェクト作成 |
| Open Project | プロジェクトを開く |
| Save Project | 上書き保存 |
| Save As | 別名保存 |

### Parts タブ

| ボタン / 操作 | 機能 |
|---|---|
| Add Part | パーツを選択して追加 |
| Clone | 選択ノードを複製 |
| Delete | 選択ノードを削除 |
| （将来）Import Part | 外部パーツ定義の読み込み |

### Wiring タブ

| ボタン / 操作 | 機能 |
|---|---|
| Wire Mode | ワイヤモード切替（checkable） |
| Cancel Wire | ワイヤ操作をキャンセル |
| （将来）Edit Connection | 接続プロパティ編集 |
| （将来）Connection Color | 接続線の色変更 |

### Run タブ

| ボタン / 操作 | 機能 |
|---|---|
| Build | アセンブル → RAM ロード（F5） |
| Run | 最大ステップ数実行 |
| Step | 1 命令実行 |
| Pause | 実行停止 |
| Reset | CPU / UART リセット |

### View タブ

| ボタン / 操作 | 機能 |
|---|---|
| Zoom In / Out / Reset / Fit | Canvas ズーム操作 |
| Grid | グリッド表示切替 |
| Snap | スナップ ON/OFF |
| Parts Library | Parts Library 表示切替 |
| Properties | Properties パネル表示切替 |

### Debug タブ

| ボタン / 操作 | 機能 |
|---|---|
| Register View | レジスタ表示切替 |
| Memory Viewer | メモリビューア表示切替 |
| Bus Trace | バストレース表示切替 |
| UART Console | UART 出力パネル表示切替 |
| （将来）Breakpoint | ブレークポイント設定 |

### 現行リボンからの移設対応表（案）

| 現行タブ / ボタン | 移設先 |
|---|---|
| File タブ: New / Open / Save / Save As | Project タブ |
| Build-Run タブ: Build / Run / Step / Pause / Reset | Run タブ |
| View タブ: Zoom / Grid / Snap / Wire Mode | View タブ（Zoom/Grid/Snap）+ Wiring タブ（Wire Mode） |
| View タブ: Register View / Memory Viewer / Bus Trace / UART / Memory | Debug タブ |
| Tools タブ | 現状維持（内容確認後に整理） |

> この移設対応表は UI ラフとユーザー確認後に確定する。

---

## 6. マウス操作割り当て（案）

| 操作 | 動作 |
|---|---|
| 左クリック | 選択・ノード移動・ラバーバンド選択 |
| 右クリック | コンテキストメニュー / Wire Mode 操作 |
| 中ボタンドラッグ | Canvas Pan |
| ホイール | Zoom In / Out |
| ダブルクリック（ノード上） | Port Detail ウィンドウを開く（v0.5 実装予定） |

> ユーザーの UI ラフで変更が生じた場合はここを更新する。

---

## 7. ショートカット方針（案）

| ショートカット | 機能 |
|---|---|
| F5 | Build（既存） |
| F6 | Run |
| F7 | Step |
| F8 | Reset |
| Ctrl+S | Save Project（既存） |
| Ctrl+Shift+S | Save As（既存） |
| Ctrl++ / Ctrl+- | Zoom In / Out |
| Ctrl+0 | Reset Zoom |
| Ctrl+W | Wire Mode ON（トグル） |
| Escape | Wire Mode キャンセル / 選択解除 |
| Delete | 選択ノード削除 |

> ユーザーの UI ラフで変更が生じた場合はここを更新する。

---

## 8. Canvas 表示方針

### 現状

- ノード色: カテゴリ別固定色（`_CAT_COLOR` dict）
- 接続線色: bus は青（#66ccff）/ signal は緑（#88ddaa）/ clock は黄（#ffcc66）/ reset は赤（#ff8888）
- グリッド: 20px 格子線（GridScene、デフォルト非表示）
- ポート表示: ノード右端に小円（PortDot）のみ

### 改善方針（案）

| 項目 | 方針 |
|---|---|
| ノード色 | v0.5 では現状維持。将来 `part.json` の `color` フィールドに対応（v0.6 以降） |
| 接続線色 | kind 別の色は現状維持。色変更 UI は v0.6 以降 |
| ノードサイズ | v0.5 では現状維持（140×56px 固定）。将来 `part.json` の `size` フィールドに対応（v0.6 以降） |
| ポート情報表示 | Port Detail ウィンドウ（ダブルクリックで開く）を v0.5 で実装を検討 |

> ユーザーの UI ラフで変更が生じた場合はここを更新する。

---

## 9. Debug パネル整理方針

### 各パネルの役割

| パネル | 役割 | 表示タイミング |
|---|---|---|
| Register View | CPU レジスタ（PC / cycle / halted / r0〜r15）の現在値確認 | Step / Run 実行後 |
| Memory Viewer | RAM 内容の hex ダンプ表示・PC 行ハイライト | Step / Run 実行後・デバッグ時 |
| Bus Trace | バストランザクション履歴（READ/WRITE / addr / val）の確認 | Step / Run 実行後 |
| UART Console | UART TX バッファの文字出力確認 | UART 出力プログラムの実行時 |

### 整理方針

- 上記 4 パネルは Debug タブのトグルボタンで個別に ON/OFF できるようにする
- 起動時はすべて非表示（ユーザーが必要に応じて開く）
- Run タブに「Debug パネルを全て開く」ボタンを追加することも検討する（UI ラフ待ち）

---

## 10. Port Detail 方針

### 表示トリガー

| 操作 | 動作 |
|---|---|
| ノード上でダブルクリック | Port Detail ウィンドウを開く |
| ノードの右クリックメニュー → 「ポートを見る」 | 同上 |

### 表示内容（1 ポートにつき 1 行）

| 列 | 内容 |
|---|---|
| Name | ポート名（例: `bus_master`） |
| Direction | `in` / `out` / `inout` |
| Kind | `bus` / `signal` / `clock` / `reset` |
| Width | ビット幅（例: `32`） |
| Range | ビット範囲（例: `[31:0]`） |
| Description | 説明文 |

### 実装優先度

**v0.5 で実装を検討する。** ただし UI ラフとユーザー確認後に最終決定する。

---

## 11. 配線表示方針

### 現状

| kind | 色 | 太さ |
|---|---|---|
| bus | #66ccff（青） | 3.0px |
| signal | #88ddaa（緑） | 1.5px |
| clock | #ffcc66（黄） | 1.5px |
| reset | #ff8888（赤） | 1.5px |

### 改善方針（案）

- v0.5 では現状の色・太さを維持する
- 配線色変更 UI（右クリックメニューまたは Wiring タブ）は v0.5 実装を検討
- 実装優先度は UI ラフとユーザー確認後に最終決定する

---

## 11-A. Hub 画面方針

### 目的

起動直後に Workspace へ入らず、**開発 Hub** を入口にする。
Hub は将来 OS / コンパイラ / ゲーム機開発などのプロジェクト種別へ拡張できる構造にする。

### Hub 画面の役割

| 役割 | 内容 |
|---|---|
| 新規プロジェクト作成 | New Project（既存 `_new_project` 処理へつなぐ） |
| 既存プロジェクトを開く | Open Project（既存 `_open_project` 処理へつなぐ） |
| 最近開いたプロジェクト | Recent Projects（v0.5 Prototype では空表示枠のみ） |
| テンプレート選択 | Templates（カードのみ、実機能は後回し） |
| ドキュメント導線 | Documentation / Quick Start への入口 |

### Hub レイアウト（Prototype）

```
+------------------------------------------------------+
|  AKDev                                               |
|  Custom CPU / FPGA / Game Console Development Env.    |
|                                                      |
|  [ + New Project ]   [ Open Project ]                |
|                                                      |
|  Recent Projects                                     |
|   (なし — 最近のプロジェクトはここに表示されます)    |
|                                                      |
|  Templates                                           |
|   [ AK32 Baremetal ] [ Empty ] [ (Coming soon) ]     |
|                                                      |
|  Documentation / Quick Start                         |
|   - Quick Start (docs/QUICKSTART.md)                 |
|   - User Guide  (docs/USER_GUIDE.md)                 |
+------------------------------------------------------+
```

### 遷移

- New Project / Open Project を実行したら Hub を閉じて Workspace へ移る
- 既存の New / Open 処理は壊さない（Hub は既存メソッドのトリガーに徹する）

---

## 11-B. Visual Identity 方針

### 今回の範囲

フォント変更は今回優先しない。代わりに以下の土台を作る。

| 項目 | 方針 |
|---|---|
| アプリ名表示 | AKDev を Hub（大きく）と Workspace（ウィンドウタイトル）で見やすく表示 |
| アクセントカラー | 1 色を決めて UI に使う（`ui/theme.py` の `ACCENT`） |
| ボタン枠線 | 枠線を弱め、もっさり感を減らす |
| 状態表示 | hover / selected / active を少し分かりやすくする |
| アイコン構造 | 主要ボタンに後からアイコンを差し替えやすい構造にする（今回はテキストでも可） |

### 制約

- 外部アイコンライブラリは追加しない
- 新しい画像素材のダウンロードは禁止
- 仮ロゴ・仮アイコンはコード内描画またはテキストで行う
- スタイルは `ui/theme.py` の QSS に集約し、`main.py` でアプリ全体に適用する

### アクセントカラー

- `ACCENT = #3B82F6`（青）／ hover `#2563EB`／ light `#DBEAFE`
- 選択・アクティブ状態とリンク系の強調に使用する

---

## 11-C. v0.5 UI Prototype Patch 実装範囲

### 今回実装する範囲

| # | 項目 | 内容 |
|---|---|---|
| 1 | `ui/theme.py` | アクセントカラー定数 + QSS スタイルシート |
| 2 | `ui/hub.py` | Hub ウィンドウ（New / Open / Recent / Templates / Docs） |
| 3 | Workspace 初期表示整理 | Log / Console と Properties を前面化、Canvas を広く |
| 4 | Ribbon 再構成 | Project / Parts / Wiring / Run / View / Debug の 6 タブ |
| 5 | Debug パネル整理 | デバッグパネルのトグルを Debug タブへ集約 |
| 6 | Visual Identity 土台 | 枠線軽減・hover/selected/active・アクセント適用 |
| 7 | Hub → Workspace 遷移 | `main.py` で Hub 先行表示、既存 New/Open へ接続 |

### 今回やらないこと

- 完成版 UI の確定（UI ラフ受領後）
- VS Code Companion / KiCad 連携 / C コンパイラ / HDL 合成 / 実機書き込み
- Video / Input Device の本実装・ゲーム実行
- GUI Designer の本実装・完成ロゴ作成
- 外部素材ダウンロード・外部 UI ライブラリ導入
- 大量の新 CPU 命令追加
- フォント変更
- Debug パネルの完全な初期非表示（テスト契約維持のため前面化のみ。完全非表示は UI ラフ確定後）

---

## 11-D. Part Visual 編集方針（段階実装）

PowerPoint のように、パーツの色・大きさをマウス操作で変更できるようにしたい。
**いきなり完全実装はしない。** 土台（色変更）から小さく分けて進める。

> **第1段階（色変更）は `PATCH_PART_VISUAL_V05` で実装済み（2026-06-06）。**

### 編集対象

| 対象 | 操作場所 | 段階 | 状態 |
|---|---|---|---|
| PartNode の色 | Properties パネルの Visual セクション + Color Palette | 第1段階 | **実装済み** |
| PartNode のサイズ | Canvas 上のサイズ変更ハンドル（角ドラッグ）| 第2段階 | 未実装（別パッチ候補）|

### Properties への Visual Editing 項目（案）

- 選択中の PartNode に対し、Properties に「Visual」セクションを追加
- 色: Color Palette（仮に 100 色程度のスウォッチ）から選択
- サイズ: 幅・高さの数値入力（ハンドルは第2段階）

### Color Palette（案）

- 10×10 程度のスウォッチグリッド（約 100 色）
- コード内生成（外部素材・外部ライブラリは使わない）
- 選択色は即座に PartNode に反映

### 保存形式（system.json）

- インスタンスごとの上書き値を `parts[].instance_color` / `parts[].size` に保存
- 優先度: カテゴリ既定色 < `part.json` の `color` < `system.json` の `instance_color`
- サイズも同様に `part.json` の `size` < `instance_color` 相当でインスタンス上書き
- `part.json` は配布物の既定値、`instance_color` / `size` はそのプロジェクト固有の上書き

### 段階分け

| 段階 | 内容 | 扱い |
|---|---|---|
| 1 | Properties の Color Palette で PartNode 色変更 + system.json 保存 | **実装済み（PATCH_PART_VISUAL_V05）** |
| 2 | Canvas のサイズ変更ハンドル | 大きくなるため別パッチへ分離（未着手）|

### 第1段階の実装（PATCH_PART_VISUAL_V05）

- `PartNode._color` + `set_color()/color()`、`paint()` で instance_color を優先。
- `Canvas.set_node_color(node_id, hex)`、`export_parts`/`import_parts` で `instance_color` を round-trip。
- `PropPanel` に「Visual」セクション + 100 色パレット（コード内生成）+ 「Default color」。
  スウォッチクリックで `color_changed(node_id, hex)` を発火。
- `MainWin._on_part_color_changed` が色を適用し、プロジェクトが開いていれば保存。
- サイズ（`size`）は第2段階。本パッチでは扱わない。

---

## 11-E. Log / Console / Error の役割整理

Log と Console は役割が異なるため分離する。Error は将来分離する。

| パネル | 役割 | 本パッチでの扱い |
|---|---|---|
| Log | アプリ操作・Build 結果・状態通知 | 既存 dock をタイトル「Log」に改称 |
| Console | 実行中プログラムの出力（Run 開始/停止・UART 出力テキスト）| **新規 dock を追加** |
| UART Console | UART デバイスの TX バッファ（生の出力）| 既存維持 |
| Error | Build error / Runtime error / Validation error | **今回は実装しない**（将来タブとして追加）|

### Console と UART Console の関係

- **UART Console**: UART パートの `output_text()` をそのまま表示する低レベルビュー
- **Console**: 実行セッション視点のプログラム出力ログ（Run started / HALTED / UART テキスト差分）
- 役割が重なる部分はあるが、Console は「実行の流れ」、UART Console は「デバイス生出力」と整理する
- 将来 Error を分離する際は Console から Error 種別を切り出す

---

## 11-F. Run Status 表示候補（設計のみ）

現状、プログラムが Build 済みか／CPU が動いているかが UI 上で分かりにくい。

### Status 表示候補（将来）

| 表示 | 内容 |
|---|---|
| Build 状態 | `Built` / `Not built`（最後の Build 成否） |
| CPU 状態 | `running` / `HALTED` / `idle` |
| 現在 PC・cycle | ステータスバーまたは Run タブ近傍に表示 |

> 本パッチでは **候補として記載のみ**。実装は将来パッチ。
> なお Wire Mode 状態はステータスバーに表示する（11-A の操作性改善として本パッチで実装）。

---

## 11-G. Known Issues（v0.5 時点）

| # | 症状 | 状態 | 記録先 |
|---|---|---|---|
| KI-1 | リボン Wire Mode トグル ON では開始ポートが無く、右クリック「ここに接続」が機能しない。右クリックメニューが wire 用に占有され通常操作ができない | **解決済み（PATCH_WIRING_V05）** | `ERROR.md` |

### KI-1 の解決（PATCH_WIRING_V05）

- wire モードを armed / drawing の 2 サブ状態に整理（`_begin_wire_from` 新設）。
- リボントグル ON は **armed**（始点未選択）。右クリック「ここから接続を開始」で drawing へ。
- wire モード中の右クリックメニューに **通常操作（Properties / 開く / 複製 / 削除）を併設**し、
  通常操作が死なないようにした。
- Cancel Wire / Escape / メニュー Wire Cancel はすべて design へ戻す（preview/waypoints/handles/
  pending/装飾を確実クリア）。
- 詳細は 11-I・`PATCH_WIRING_V05_ROADMAP.md` を参照。

---

## 11-H. v0.5 UI Prototype Patch 2 実装範囲（User Review Fixes）

| # | 項目 | 内容 |
|---|---|---|
| A | Project タブ削除 | リボンから Project タブを削除（File メニューに New/Open/Save/Save As は残す）|
| B | リボンボタン幅縮小 | 横幅いっぱいの均等配置をやめ、自然幅・左詰め・余白縮小 |
| C | Parts タブ再設計 | Add Part/Clone/Delete/Properties を撤去。Parts Library トグル + Import Part…(disabled) + Open Parts Folder |
| D | Parts Library 初期非表示 | 起動時は非表示。Parts タブのトグルで表示 |
| E | Part Visual 編集方針 | 11-D に方針記載（実装は次パッチ）|
| F | Wiring 最小修正 | Cancel Wire 強化 + Escape + 状態表示。右クリック占有は KI-1 として記録 |
| G | Run 確認 | 11-F に Status 候補記載（実装は将来）|
| H | View タブ整理 | Grid 初期 OFF / Zoom In・Out をリボンから撤去（ホイールズーム維持）|
| I | Log/Console 分離 | Log 改称 + Console dock 追加（11-E）|

### 今回やらないこと（Patch 2）

- Hub の大幅変更・完成版 UI 確定
- Part Visual の完全実装・サイズ変更ハンドル
- Wiring の全面再設計（別パッチ提案）
- Error タブ実装
- 外部素材・外部ライブラリ追加
- commit / push

---

## 11-I. Wiring 操作フロー（PATCH_WIRING_V05）

### wire モードの状態

| サブ状態 | 条件 | 意味 |
|---|---|---|
| design | `_mode == "design"` | 通常モード（配線しない）|
| armed | `_mode == "wire"` かつ `_wire_from is None` | 配線モードだが始点未選択 |
| drawing | `_mode == "wire"` かつ `_wire_from` 設定済 | 始点選択済・接続先待ち |

### 操作フロー

1. **Wire Mode 開始**: Wiring タブの Wire Mode トグル ON（= armed）、
   または PartNode 右クリック「接続を開始」（= 即 drawing）。
2. **始点選択**（armed のとき）: PartNode 右クリック「ここから接続を開始」→ drawing。
3. **Waypoint（任意）**: 空白を右クリック「Waypoint 追加」。
4. **接続先指定**: 対象 PartNode 右クリック「ここに接続」→ 接続作成。
5. **完了後**: **design モードへ自動で戻る**（1 始点 = 1 接続）。

### キャンセル

- Cancel Wire（リボン）／Escape（Canvas）／右クリック「Wire Cancel」は
  **すべて design モードへ戻る**。preview・waypoints・handles・pending・Canvas 装飾を
  確実にクリアする。

### 接続完了後の挙動（仕様決定）

- **接続完了後は design モードへ戻る。**
- 理由: 状態が予測しやすく、誤操作を減らせる。1 始点 1 接続で完結する。
- **連続配線**（接続後も wire モードを継続し複数本を続けて引く）は **将来拡張**。

### 状態可視化

| 手段 | 内容 |
|---|---|
| ステータスバー | wire 時に操作ヒントを表示、design で消去 |
| Wiring タブ | Wire Mode トグルの checked 状態 |
| Canvas 枠 | wire 時に薄いアクセント色の枠を表示 |

### wire モード中の右クリックメニュー

| 対象 | 項目 |
|---|---|
| PartNode（armed）| ここから接続を開始 / Wire Cancel / Properties / プログラムを開く / HDLを開く / 複製 / 削除 |
| PartNode（drawing）| ここに接続 / Wire Cancel / Properties / プログラムを開く / HDLを開く / 複製 / 削除 |
| 空白（drawing）| Waypoint 追加 / Wire Cancel |
| 空白（armed）| Wire Cancel |

> 設計モードの右クリックメニューは変更しない。

### 接続線と削除・移動の同期（PATCH_WIRING_V05 追加修正）

| 項目 | 仕様 |
|---|---|
| ノード削除 | ノードを削除すると、そのノードに繋がる接続も**自動削除**する（データ・線・export すべて同期）。全削除経路（Delete キー / 右クリック / 複数選択）で同一挙動。内部窓口は `_remove_node(node_id)` |
| 端点座標 | wire の始点・終点は**実ポート座標**に一致させる（grid に丸めない）。途中の BFS/waypoint は grid 維持。snap OFF パーツでも隙間なく接続し、移動にも追従 |

### Canvas 初期表示（PATCH_WIRING_V05 追加修正）

- 広い `sceneRect` を初期化して中ボタン Pan の可動域を確保する。
- 起動時に原点中心へ寄せ、grid OFF でも**原点十字**を常時描画する。
- Log / ステータスバーに "Canvas ready" を表示し、読み込み済みと分かるようにする。

### 参考: 既存ノード UI 挙動

一般的なノード UI（Unity Animator / Shader Graph、Blender Node Editor、
Unreal Blueprint）の挙動と当面の方針は `PATCH_WIRING_V05_ROADMAP.md` セクション 9 を参照。
当面は右クリック方式を維持しつつ内部はポート接続モデルへ寄せ、将来「ポートから
ドラッグして接続」「接続可否ハイライト」を実装候補とする。

---

## 11-J. Dynamic Visual Port（PATCH_WIRING_PORTS_V05）

Wiring を既存ノードエディタ（Shader Graph / Blueprint / Node-RED 等）に寄せるため、
**接続点をデータとして持つ Visual Port** を導入する。

### 用語

| 用語 | 意味 |
|---|---|
| logical port | part.json / sim 上の意味を持つポート（bus / signal / clock / reset）|
| visual port | Canvas 上で wire が接続される見た目の接点。ノードインスタンスごと・初期 0 個・system.json に保存 |

### 方針

- **見た目上のポートは最初 0 個**。パーツに wire を接続したとき、その接点に visual port を作る。
- visual port は `side`（left/right/top/bottom）と `offset`（辺に沿った位置）を持ち、後から移動・整列できる。
- 接続は visual port を `visual_port_id` で参照し、wire 端点は visual port の実座標に一致する。
- ノード移動で visual port も wire も追従。ノード削除で関連 wire と端点 visual port も削除。
- legacy `_port_dot`（右中央の単一 dot）は **Canvas 上は非表示**にする（コードは互換のため残す）。
  単一 dot を表示し続けることは「初期 0 個」方針に反するため行わない。

### 保存形式（system.json、抜粋）

```json
{
  "parts": [
    {"node_id": "node_0001", "part_id": "ak32_cpu", "x": 100, "y": 100,
     "visual_ports": [
       {"id": "vp_0001", "side": "right", "offset": 12.0,
        "kind": "bus", "label": "bus", "locked": false}]}
  ],
  "connections": [
    {"id": "conn_0001",
     "from": {"node_id": "node_0001", "port": "bus",
              "visual_port_id": "vp_0001", "logical_port": "bus"},
     "to":   {"node_id": "node_0002", "port": "bus",
              "visual_port_id": "vp_0002", "logical_port": "bus"},
     "kind": "bus", "route": []}
  ]
}
```

- `visual_ports` は 0 個なら省略。`from`/`to` は後方互換のため `port` を残す。
- `visual_port_id` を持たない既存接続は従来どおりノード端に接続する。

### 本パッチの範囲と将来

- **PATCH_WIRING_PORTS_V05**: データ構造・接続時生成・端点解決・export/import・削除同期・移動/整列 API・右クリック整列。
- **PATCH_PORT_DRAG_CONNECT_V05（実装済み）**: visual port からドラッグして別ノードへ接続。
- **将来**: 接続先候補の hover ハイライト、visual port の対話ドラッグ移動、空ポートからのドラッグ開始。

### Port Drag Connect（PATCH_PORT_DRAG_CONNECT_V05）

既存の右クリック接続に加え、**visual port からドラッグして接続**できる。

| 操作 | 動作 |
|---|---|
| visual port 上で左ドラッグ開始 | port-drag 開始、カーソルへ curved 破線 preview を表示 |
| 別ノード上で離す | 接続確定（source は既存 vp を参照、target に新 vp を生成）|
| 同一ノード / 何も無い場所で離す | キャンセル |
| Esc / 右クリック（ドラッグ中）| キャンセル |

- 確定接続は Dynamic Visual Port（両端 `visual_port_id`）として curved wire で描画され、
  移動追従・削除同期・export/import に乗る。
- visual port は接続時に生成されるため、**最初の接続は右クリック**で行う（port-drag は既存 port から）。
- 実装: Canvas の `_visual_port_at` / `_start_port_drag` / `_update_port_drag_preview` /
  `_finish_port_drag` / `_cancel_port_drag`。visual port は独立 item にせず幾何ヒットテスト。

### Hover Feedback（PATCH_WIRE_HOVER_FEEDBACK_V05）

接続操作の対象を、クリック前にマウスホバーで視認できるようにする（**視覚のみ**。
選択・削除・対話移動は含まない）。

| 対象 | ホバー時の見た目 | 内部状態 |
|---|---|---|
| visual port | 明るく + 白枠 + 少し拡大して描画 | `Canvas._hover_vp = {"node_id","vp_id"}` / `PartNode.set_hover_port()` |
| wire | 少し太く + 明るく（active と両立、active 優先）| `ConnectionLine.set_hovered()` / `Canvas._hover_conn_id` |
| port-drag 接続先候補 | カーソル下の**別ノード**をアクセント色外枠で強調 | `Canvas._hover_drop_node_id` / `PartNode.set_drop_highlight()` |

- hover 更新はボタン非押下時の `mouseMoveEvent` →`_update_hover()`。port が wire より優先。
- Canvas から離れると `leaveEvent` で hover 解除。
- port-drag 中はカーソル下ノードを `_update_drop_target()` で候補化（**同一ノードは除外**）。
  port-drag 終了 / キャンセルで `_cancel_port_drag()` が drop highlight を必ず解除。
- pen は `ConnectionLine._apply_pen()` で base / hover / active を集中管理（active が hover に優先）。
- **今回やらないこと**: wire 選択・Delete Wire・visual port 対話移動・接続可否の型判定。

### Wire Select & Delete（PATCH_WIRE_SELECT_DELETE_V05）

接続済み wire を選択し、不要な接続を削除できる。

| 操作 | 動作 |
|---|---|
| design mode で wire を左クリック | その wire を選択（`Canvas._selected_conn_id`）|
| 別 wire を左クリック | 選択が移る |
| 空白 / ノードを左クリック | wire 選択を解除（ノードクリックはノード選択優先）|
| visual port クリック / port-drag 開始 | wire 選択しない（port-drag を優先）|
| Delete キー（wire 選択中）| その wire のみ削除。選択なしは従来のノード削除 |
| wire 近くで右クリック | wire を選択し「Delete Wire」メニュー → 削除 |

- 表示優先度は **selected > active > hover > normal**（`ConnectionLine._apply_pen()`）。
  selected は最も強い強調（白・最太）で、signal overlay（active）と重なっても selected を優先。
- 削除は `Canvas._remove_connection(conn_id)` に集約: connection data + ConnectionLine を除去し、
  selected/hover を解除、`_prune_orphan_visual_ports()`、`update_connections()` を呼ぶ。
  **fan-out 元の visual port が他 connection から参照されていれば残す**（orphan のみ prune）。
- 選択は hover とは独立した状態。`_set_hover_conn()` は selected を解除しない。
- 保存はノード削除と同じく既存の保存導線（保存時 `export_parts`/`export_canvas`）に委ねる。
- **今回やらないこと**: wire Properties / 色変更 UI / ラベル / 複数選択 / Undo / z-order 調整。

### Visual Port Move（PATCH_VISUAL_PORT_MOVE_V05）

visual port を PartNode の辺上で対話的に動かせる。

| 操作 | 動作 |
|---|---|
| visual port 上で **Alt + 左ドラッグ** | port move 開始（移動中は専用色リングで強調）|
| ドラッグ中 | カーソル下の最近辺に拘束し side/offset を更新、接続 wire がリアルタイム追従 |
| マウス release | 移動確定 |
| Esc / 右クリック | キャンセル（移動前の side/offset へ復元）|
| visual port 上で **Alt なし**左ドラッグ | 従来どおり port-drag connect（移動ではない）|
| locked=true の visual port | 移動開始しない（ログ "Visual port is locked" 1 行）|

- 位置は **辺拘束**: マウス scene 座標を PartNode ローカルへ変換し、最近辺で
  `side`（left/right/top/bottom）、辺に沿った距離で `offset` を決め、ノードサイズ内に clamp。
  保存値は side + offset のまま（scene 絶対座標は持たない）。`PartNode.edge_from_local()` /
  `node_size()`（現状固定 `_NODE_W`/`_NODE_H`、将来のサイズ変更に備えた hook）。
- 状態は `Canvas._port_move`（node_id / vp_id / original・current side+offset）。
  `_start_port_move` / `_update_port_move` / `_finish_port_move` / `_cancel_port_move`。
  `_port_drag`（接続）と `_port_move`（移動）は別状態。
- fan-out（共有 vp）を動かすと、その vp を参照する全 wire が追従（端点は vp 位置参照のため自動）。
- 保存はノード移動と同じく自動 persist せず、保存時の `export_parts`/`export_canvas` に委ねる。
  export/import round-trip で移動後の side/offset を維持。
- 表示優先度（visual port）は **moving > hover > normal**。drop target highlight とは別状態。
- **今回やらないこと**: 通常左ドラッグ移動 / 複数選択 / 削除 UI / rename / サイズ変更 / Undo。

---

## 12. ユーザー UI ラフ反映欄

> **このセクションはユーザーが UI ラフを作成した後に更新する。**

### UI ラフ受け取り後の手順

1. ユーザーが UI ラフ画像（または手書き図）を提供する
2. ラフと本仕様書の各セクションを照合する
3. 差分がある場合は理由を確認してから更新する
4. 最終方針を `UI_SPEC_V05.md` に反映する
5. 実装範囲を確定してユーザー確認を挟む

### ラフ受け取り状況

- [ ] UI ラフ未受領（ユーザー作成待ち）

### ラフと仕様の差分メモ

（ラフ受け取り後に記入）

---

## 未確定項目

| 項目 | 未確定理由 |
|---|---|
| リボン移設の最終配置 | UI ラフとユーザー確認待ち |
| Port Detail の実装優先度（v0.5 か v0.6 か） | UI ラフとユーザー確認待ち |
| 配線色変更 UI の実装優先度（v0.5 か v0.6 か） | UI ラフとユーザー確認待ち |
| Debug パネル「全部開く」ボタンの要否 | UI ラフとユーザー確認待ち |
| Canvas ノード色・サイズ変更の実装優先度 | UI ラフとユーザー確認待ち |
| Tools タブの扱い | 現行内容確認後に整理 |
