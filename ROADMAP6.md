# AKDev ROADMAP 6

> v0.5 UI Polish & Usability の開発計画。
> v0.4 / v0.4.1 完了時点の計画は `old/ROADMAP5.md` / `old/PATCH_V041_ROADMAP.md` を参照。
> 進捗管理は `CHECKLIST6.md` で行う。

---

## v0.4.1 到達点（2026-06-03 完了・アーカイブ）

完了条件「**v0.4 公開前 Canvas Routing Polish & Pre-Release Docs**」達成。pytest 518 件通過。

| 修正内容 | 概要 |
|---|---|
| 配線ルートの角修正 | `update_route` 直線化・ポート位置から配線 |
| Canvas Pan 中ボタン化 | RightButton → MiddleButton、右クリックメニュー干渉解消 |
| 公開前ドキュメント追加 | `docs/QUICKSTART.md` / `docs/USER_GUIDE.md` / README 更新 |

---

## プロジェクト最終目標（v1.0）

**自作 CPU 上でゲーム実行環境を動かし、1 本のゲームを起動・操作できる状態にする。**

これに向けて、AKDev は今後 Video / Input / Display / Game Runtime などの機能が増えていく。
v0.5 はその増加に耐えられる UI 基盤を作るフェーズである。

---

## v0.5 テーマ: UI Polish & Usability

**「機能が動くアプリ」から「人間が迷わず使える開発環境」にする。**

v0.4 までで機能は一通り動作する。
v0.5 では、増え続ける機能に対して UI が破綻しないよう、
パネル管理・リボン構成・操作性を整理する。

---

## v0.5 設計方針

### 1. 拡張性

- 今後 Video / Input / Display / Game Runtime などが増えても破綻しない UI にする
- 使わないパネルや機能を常時表示しない
- 必要なものは後から表示・非表示を切り替えられるようにする
- 初期表示はシンプルにする
- 機能を減らすのではなく、**必要なときだけ表示できる構成**にする

### 2. 操作性

- よく使う操作はすぐアクセスできる位置に置く
- よく使う操作はマウス操作・リボン・ショートカットに割り当てる
- 操作頻度の低い機能は常時表示しない
- ユーザーが迷う時間を減らす

### 3. リボン整理

一つのリボンタブに機能を集約しすぎない。
PowerPoint のように、目的別にタブを分ける。

| タブ名 | 目的 |
|---|---|
| Project | 新規・開いた・保存・閉じる |
| Parts | パーツ配置・削除・クローン |
| Wiring | 配線・Wire Mode・接続操作 |
| Run | Build・Run・Step・Reset |
| View | 表示切替・Zoom・Grid・Snap |
| Debug | Memory Viewer・Bus Trace・Register View・UART |

### 4. 初期表示

**起動時に常時表示するパネル（シンプルセット）:**

| パネル | 理由 |
|---|---|
| Ribbon | 必須操作ハブ |
| Parts Library | パーツ配置の出発点 |
| System Canvas | メイン作業エリア |
| Properties | 選択パーツの情報 |
| Log | エラーや通知の確認 |

**必要時のみ表示（トグルで出せる）:**

| パネル | 表示タイミングの例 |
|---|---|
| Register View | Run / Step 時 |
| Memory Viewer | デバッグ時 |
| Bus Trace | デバッグ時 |
| UART Console | UART 出力確認時 |
| Port Detail | ノードのポート確認時 |
| Signal Overlay 設定 | 接続線の色設定時 |

### 5. UI ラフ前提

ユーザーが UI ラフ画像を作成する予定。
**v0.5 では UI ラフの反映まで含む。**

そのため、以下の順序で進める:

1. `UI_SPEC_V05.md` を作成して設計方針を文書化する（現フェーズ）
2. ユーザーが UI ラフを作成する（ユーザー担当）
3. UI ラフを `UI_SPEC_V05.md` に反映する
4. 実装範囲を確定してユーザー確認を挟む
5. 実装に入る

---

## v0.5 作業一覧

| # | 作業 | 担当 |
|---|---|---|
| 1 | `UI_SPEC_V05.md` 作成 | Claude Code |
| 2 | 現在 UI の問題点整理 | Claude Code |
| 3 | 初期表示パネルの整理 | Claude Code |
| 4 | パネル表示/非表示ルール整理 | Claude Code |
| 5 | リボンタブ構成整理 | Claude Code |
| 6 | マウス操作・ショートカット整理 | Claude Code |
| 7 | Debug パネルの役割整理 | Claude Code |
| 8 | Canvas 視認性改善方針整理 | Claude Code |
| 9 | Port Detail 方針整理 | Claude Code |
| 10 | 配線表示方針整理 | Claude Code |
| 11 | ユーザーの UI ラフ反映 | ユーザー → Claude Code |
| 12 | UI ラフをもとに実装範囲を確定 | Claude Code + ユーザー確認 |
| 13 | 実装前レビュー | ユーザー確認 |
| 14 | 実装 | Claude Code（スコープ確定後） |

---

## v0.5 UI Prototype Patch（最初の実装）

> v0.5 の主軸は **UI Polish & Usability**。
> その最初の実装を **UI Prototype Patch** として行う。完成版 UI ではなく、
> 使いやすい UI の方向性を確認するためのたたき台。
> 設計根拠は `UI_SPEC_V05.md`（セクション 0 / 11-A / 11-B / 11-C）を参照する。

### 主軸

| # | 項目 | 概要 |
|---|---|---|
| 1 | Hub 画面 | 起動時の入口。New / Open / Recent / Templates / Docs（`ui/hub.py`） |
| 2 | Workspace 初期表示整理 | Log / Console と Properties を前面化、Canvas を主役に |
| 3 | Ribbon 再構成 | Project / Parts / Wiring / Run / View / Debug の 6 タブ |
| 4 | Debug パネルの初期非表示 / 必要時表示 | デバッグパネルのトグルを Debug タブへ集約 |
| 5 | Visual Identity の土台 | アクセントカラー・枠線軽減・状態表示（`ui/theme.py`） |

### 設計判断

- Hub は **独立ウィンドウ**（`ui/hub.py`）にする。MainWin の既定状態を変えず既存テストへの影響を抑える。
- 初期表示整理は Dock を hide せず **Log / Properties を `raise_()` で前面化**する。
- Ribbon 再構成に伴い `tests/test_ribbon.py` を新構成へ更新する。
- 既存機能（Build / Run / Step / Reset / Canvas / 配線 / hello.asm）は壊さない。

### 進捗管理

進捗は `CHECKLIST6.md` の「**UI Prototype Patch**」ブロックで管理する。

---

## v0.5 UI Prototype Patch 2（User Review Fixes）

> Patch 1 の Workspace を**ユーザー目視レビュー**し、リボン構成・初期表示・
> 死んでいる機能を整理する。完成版 UI ではない。
> 設計根拠は `UI_SPEC_V05.md`（11-D〜11-H）を参照する。

### レビュー反映項目

| # | 項目 | 概要 |
|---|---|---|
| A | Project タブ削除 | File と重複するためリボンから撤去 |
| B | リボンボタン幅縮小 | 均等引き伸ばしをやめ、コンパクトに |
| C | Parts タブ再設計 | 死にボタンを撤去し意味のある操作のみ残す |
| D | Parts Library 初期非表示 | Canvas を主役に |
| E | Part Visual 編集方針 | 色・サイズ編集の方針を記載（実装は次パッチ）|
| F | Wiring 最小修正 | Cancel Wire / Escape / 状態表示。占有問題は KI-1 記録 |
| G | Run 確認 | Status 表示候補を記載（実装は将来）|
| H | View タブ整理 | Grid 初期 OFF / Zoom In・Out 撤去 |
| I | Log/Console 分離 | Log 改称 + Console dock 追加 |

### 設計判断

- リボンは **Parts / Wiring / Run / View / Debug の 5 タブ**にする。
- Grid の Canvas 既定値（True）は変えず、**MainWin 起動時に OFF へ上書き**する（既存 canvas テスト維持）。
- Wiring の本質修正（右クリック占有 = KI-1）は大規模なため、別パッチ
  **`PATCH_WIRING_V05`** の作成を提案する（本パッチでは作成しない）。

### 進捗管理

進捗は `CHECKLIST6.md` の「**UI Prototype Patch 2 — User Review Fixes**」ブロックで管理する。

---

## v0.5 PATCH_WIRING_V05（Wiring Workflow Fix）

> Patch 2 で残った **KI-1（Wire Mode 中の右クリック占有）** を解決する別パッチ。
> 設計書: `PATCH_WIRING_V05_ROADMAP.md` ／ 進捗: `PATCH_WIRING_V05_CHECKLIST.md`。

| 項目 | 概要 |
|---|---|
| wire 状態整理 | armed / drawing の 2 サブ状態に整理（`_begin_wire_from` 新設）|
| 右クリック整理 | wire 中も通常操作（Properties/開く/複製/削除）を併設し死なせない |
| キャンセル統一 | Cancel Wire / Escape / メニュー Wire Cancel を design 復帰で統一 |
| フロー仕様 | 接続完了後は design へ戻る（1 始点 1 接続）。連続配線は将来 |
| 状態可視化 | ステータスバー + トグル checked + Canvas 枠の色 |

---

## v0.5 PATCH_WIRING_PORTS_V05（Dynamic Visual Port）

> Wiring を既存ノードエディタに寄せ、接続点をデータ化する **Dynamic Visual Port** を導入。
> 設計書: `PATCH_WIRING_PORTS_V05_ROADMAP.md` ／ 進捗: `PATCH_WIRING_PORTS_V05_CHECKLIST.md`。
> 仕様: `UI_SPEC_V05.md` 11-J。

| 項目 | 概要 |
|---|---|
| Dynamic Visual Port | 見た目ポートは初期 0 個。接続時に接点へ visual port を生成し保存 |
| logical / visual 分離 | logical port（sim 意味）と visual port（見た目接点）を分ける |
| 端点・削除同期 | wire 端点は visual port 座標、ノード削除で wire + orphan vp を削除 |
| 移動 / 整列 | visual port の移動 API・整列 API（対話ドラッグは将来）|
| legacy 互換 | `_port_dot` は非表示で残す。vp 無し接続は従来どおりノード端 |

---

## v0.5 PATCH_PORT_DRAG_CONNECT_V05（Port Drag Connect）

> visual port からドラッグして別ノードへ接続する操作を追加。
> 設計書: `PATCH_PORT_DRAG_CONNECT_V05_ROADMAP.md` ／ 進捗: `PATCH_PORT_DRAG_CONNECT_V05_CHECKLIST.md`。
> 仕様: `UI_SPEC_V05.md` 11-J（Port Drag Connect）。

| 項目 | 概要 |
|---|---|
| port-drag | visual port 上の左ドラッグで開始、curved 破線 preview を表示 |
| 確定 | 別ノードで離すと接続確定（source=既存 vp、target=新 vp）。Dynamic Visual Port + curved wire に乗る |
| キャンセル | 同一ノード / 不正位置 / Esc / 右クリック |
| 互換 | 既存の右クリック接続・pan・wire mode・削除同期・export-import は不変 |
| ヒットテスト | visual port は独立 item にせず幾何ヒットテスト（`_visual_port_at`）|

---

## v0.5 PATCH_WIRE_HOVER_FEEDBACK_V05（Hover Feedback）

> Wiring / Port Drag Connect の操作対象を hover で視認できるようにする（視覚のみ）。
> 設計書: `PATCH_WIRE_HOVER_FEEDBACK_V05_ROADMAP.md` ／ 進捗: `PATCH_WIRE_HOVER_FEEDBACK_V05_CHECKLIST.md`。
> 仕様: `UI_SPEC_V05.md` 11-J（Hover Feedback）。

| 項目 | 概要 |
|---|---|
| visual port hover | port に近づくと明るく + 白枠 + 拡大。`PartNode.set_hover_port` |
| wire hover | wire に近づくと太く + 明るく。`ConnectionLine.set_hovered`（active 優先）|
| drop highlight | port-drag 中、カーソル下の別ノードをアクセント色外枠で候補表示（同一ノード除外）|
| 解除 | leaveEvent / port-drag 終了・キャンセルで確実に解除 |
| 範囲外 | wire 選択・Delete Wire・vp 対話移動・接続可否の型判定はやらない |

---

## v0.5 PATCH_WIRE_SELECT_DELETE_V05（Wire Select & Delete）

> 作成済みの wire を選択・削除できるようにする。
> 設計書: `PATCH_WIRE_SELECT_DELETE_V05_ROADMAP.md` ／ 進捗: `PATCH_WIRE_SELECT_DELETE_V05_CHECKLIST.md`。
> 仕様: `UI_SPEC_V05.md` 11-J（Wire Select & Delete）。

| 項目 | 概要 |
|---|---|
| wire 選択 | 左クリックで選択（`Canvas._selected_conn_id`）。`ConnectionLine.set_selected/is_selected`。表示優先度 selected > active > hover > normal |
| 削除 API | `Canvas._remove_connection(conn_id)` に集約。共有 fan-out vp は残し orphan のみ prune |
| Delete キー | 選択 wire があれば wire 削除、なければ従来のノード削除 |
| 右クリック | wire 近くで「Delete Wire」メニュー。PartNode 上 / port-drag / wire mode は従来どおり |
| 範囲外 | Properties / 色変更 / ラベル / 複数選択 / Undo / z-order 調整はやらない |

---

## v0.5 PATCH_VISUAL_PORT_MOVE_V05（Visual Port Move）

> visual port を Alt + 左ドラッグで PartNode の辺上に移動できるようにする。
> 設計書: `PATCH_VISUAL_PORT_MOVE_V05_ROADMAP.md` ／ 進捗: `PATCH_VISUAL_PORT_MOVE_V05_CHECKLIST.md`。
> 仕様: `UI_SPEC_V05.md` 11-J（Visual Port Move）。

| 項目 | 概要 |
|---|---|
| Alt + 左ドラッグ | visual port 移動を開始（Alt なしは従来の port-drag connect）。`Canvas._port_move` |
| 辺拘束 | `PartNode.edge_from_local()` で最近辺 side + clamp 済み offset。scene 絶対座標は持たない |
| wire 追従 | `_update_port_move` で side/offset 更新 + `update_connections()`。fan-out 共有 vp も全 wire 追従 |
| 確定 / 取消 | release で確定、Esc / 右クリックで元の side/offset へ復元 |
| locked | locked vp は移動しない（ログ 1 行）|
| 範囲外 | 通常左ドラッグ移動 / 複数選択 / 削除 UI / rename / サイズ変更 / Undo はやらない |

---

## v0.5 PATCH_WIRE_STYLE_V05（Wire Style）

> 選択中 wire の色・太さを編集できるようにする（kind の意味は不変、表示のみ）。
> 設計書: `PATCH_WIRE_STYLE_V05_ROADMAP.md` ／ 進捗: `PATCH_WIRE_STYLE_V05_CHECKLIST.md`。
> 仕様: `UI_SPEC_V05.md` 11-J（Wire Style）。

| 項目 | 概要 |
|---|---|
| データ | connection に任意 `style{color,width}`。未設定は kind 既定。export/import 維持・空は保存しない |
| 描画 | `ConnectionLine.apply_style`。優先度 selected > active > hover > custom style > kind default |
| Canvas API | `set_connection_style` / `reset_connection_style` / `get_connection`。selected/hover 維持 |
| Properties | wire 選択で Wire セクション（info + 色パレット + width + Reset）。`wire_selected`/`wire_selection_cleared` 通知 |
| 右クリック | 「Delete Wire」+「Reset Wire Style」。色変更は Properties 主導 |
| 範囲外 | kind 本格編集 / 意味変更 / label / rename / constraint / Undo はやらない |

---

## v0.5 PATCH_PART_PROGRAM_ASSIGN_V05（Program / Sources 割り当て）

> Canvas 上のパーツに外部ソース（asm/hdl/rom）を割り当て、Build/Run が参照する。
> **テスト用の最小実装**だが、保存形式と API は将来の正式実装へ拡張しやすくする。固定 hello.asm 専用ではない。
> 設計書: `PATCH_PART_PROGRAM_ASSIGN_V05_ROADMAP.md` ／ 進捗: `PATCH_PART_PROGRAM_ASSIGN_V05_CHECKLIST.md`。
> 仕様: `UI_SPEC_V05.md` 11-K。

| 項目 | 概要 |
|---|---|
| データ | parts エントリ内 `sources{asm,hdl,rom}`（文字列 path、将来 dict 拡張可）。既定 `{asm,hdl}` は不変 |
| Canvas API | `set/clear_node_source` / `node_sources` / `node_source` / `resolve_program_source` / `selected_node_id` |
| Properties | node 選択時 Program セクション（Set/Clear/Open）。signal 3 種 |
| 右クリック | 「プログラムを開く」維持 +「Set ASM Source…」追加 |
| Build/Run | 選択 > CPU > 任意 の優先順で割り当て asm を Build。無ければ既存タブ Build へフォールバック |
| 将来 | dict 形式 / Build Graph 自動解決 / 内蔵エディタ / 実機書き込み |

---

## v0.5 PATCH_CIRCUIT_WRITE_RUN_HELLO_V05（Write Program to Circuit）

> CPU パーツに割り当てた ASM を**仮想回路へ書き込み**（実機書き込みではない）、Run で UART に
> `Hello World !` を表示する。**テスト用最小実装**だが将来の Build Graph / ROM / 実機書き込みへ拡張可。
> **固定 hello_world.asm 専用ではない**（`sources.asm` 割り当てを優先順位で解決）。
> 設計書: `PATCH_CIRCUIT_WRITE_RUN_HELLO_V05_ROADMAP.md` ／ 進捗: `..._CHECKLIST.md`。
> 仕様: `UI_SPEC_V05.md` 11-L。

| 項目 | 概要 |
|---|---|
| テスト ASM | `tests/test/hello_world.asm`（既存命令体系で `Hello World !\n` 出力）|
| Write Program | Run タブのボタン + 右クリック。`write_program` が解決→assemble→RAM/CPU ロード |
| loaded_program | `{source_type,path,target_node_id,status}`（セッション中、今回は永続化しない）|
| Run | Write 後の RAM を既存 `_do_run` で実行 → UART `Hello World !` |
| Properties | Loaded 状態表示（Yes/No / Target / Program）|
| 互換 | 既存 Build/Run・hello.asm headless("Hi")・Program/Sources・Wire Style は不変 |

---

## v0.5 PATCH_VIRTUAL_CPU_STEP_TRACE_V05（Virtual CPU Step & Trace）

> AKDev 内の仮想 CPU 実行環境を明確化し、1 命令ずつ Step 実行して PC・命令・レジスタ変化・
> メモリ/IO・UART 出力を Log/Trace で確認できるようにする。
> **物理的には PC 上の Python だが、AKDev 内の仮想 CPU/RAM/UART を命令単位で動かす構造。**
> 設計書: `PATCH_VIRTUAL_CPU_STEP_TRACE_V05_ROADMAP.md` ／ 進捗: `..._CHECKLIST.md`。
> 仕様: `UI_SPEC_V05.md` 11-M。

| 項目 | 概要 |
|---|---|
| Virtual Runtime | `core/runtime.py` `VirtualCircuitRuntime` が既存 bus/ram/uart/cpu を包む（新規デバイス不要）|
| Step trace | `step()` が 1 命令の trace dict（pc 前後 / 命令 / レジスタ変化 / memory / io / uart / halted）を返す |
| Bus フック | `core/sim.py` `Bus.on_access`（既定 None・後方互換）で memory/IO を構造取得 |
| Step ボタン | 1 押下 = 1 命令。未ロード/halted を分かりやすくログ。Log に詳細 trace |
| Run | `runtime.step()` の繰り返し。要約ログ + 詳細は trace_history |
| 互換 | 既存 Build/Run・hello.asm "Hi"・Circuit Write/Run Hello・Program/Sources は不変 |
| 次候補 | `PATCH_CIRCUIT_CONNECTIVITY_REQUIRED_V05` / `PATCH_CPU_RAM_VALIDATION_V05` / `PATCH_BUILD_GRAPH_PROTOTYPE_V05` |

---

## v0.5 PATCH_VIRTUAL_CIRCUIT_RUNTIME_V05（Virtual Circuit Runtime）

> 固定内部回路で Hello World を出す構造から、**Canvas 由来の CircuitPlan をもとに
> VirtualCircuitRuntime を生成**する構造へ移行。最小ゴール構成は CPU + RAM + UART。
> 設計書: `PATCH_VIRTUAL_CIRCUIT_RUNTIME_V05_ROADMAP.md` ／ 進捗: `..._CHECKLIST.md`。
> 仕様: `UI_SPEC_V05.md` 11-N。

| 項目 | 概要 |
|---|---|
| CircuitPlan | `core/circuit.py` `resolve_circuit(nodes, connections)`。CPU/RAM/UART 検出 + CPU–RAM・CPU–UART 接続解析。`{ok,issues,cpu,rams,uarts,cpu_present}` |
| circuit mode | Canvas に CPU があれば plan を解決。未接続なら Write/Build/Run/Step をブロック |
| runtime 生成 | `_make_sim(plan)` で接続構成から runtime を生成。Write は接続 RAM へ、Run/Step は接続 CPU を動かし、OUT は接続 UART へ |
| legacy mode | CPU 未配置なら従来の固定 runtime（非 Canvas テスト・エディタタブ Build/Run を保持）|
| テスト更新 | 既存 Hello World テストを CPU+RAM+UART 配置・配線へ更新 |
| 互換 | hello.asm "Hi"・legacy Build/Run・runtime API は不変 |
| 次候補 | アドレスマップ / 複数デバイス / Storage・Video・Input / Fibonacci・RAM selftest |

---

## v0.5 でやらないこと

| 項目 | 理由 |
|---|---|
| VS Code Companion | 大規模。v0.6 以降 |
| KiCad 連携 | v0.6 以降 |
| C コンパイラ対応 | v0.6 以降 |
| HDL 合成 | v0.6 以降 |
| 実機書き込み | v0.6 以降 |
| Video / Input Device の本実装 | v0.6 以降 |
| ゲーム実行環境 | v1.0 目標 |
| GUI Designer の本実装 | 別フェーズ |
| 新 CPU 命令の大量追加 | 別フェーズ |
| UI ラフなしでの大規模 UI 実装 | UI ラフ確認後に実装する |

---

## v0.5 完成条件

- [ ] `UI_SPEC_V05.md` が作成されている
- [ ] 初期表示と表示切替対象が整理されている
- [ ] リボンタブ構成が決まっている
- [ ] よく使う操作の配置方針が決まっている
- [ ] マウス操作・ショートカット方針が決まっている
- [ ] Debug パネルの役割が整理されている
- [ ] Canvas 視認性改善方針が決まっている
- [ ] ユーザー作成の UI ラフが反映されている
- [ ] 実装範囲が明確になっている
- [ ] 実装前にユーザー確認を挟む
- [ ] CHECKLIST6.md の全項目が `[x]` になっている
- [ ] pytest が全件通過している
- [ ] HANDOFF.md が次フェーズを指している

---

## v0.6 以降の候補（参考）

| 候補 | 概要 |
|---|---|
| AKDev VS Code Companion | VS Code 拡張（ASM/HDL 補完、Build/Run 連携） |
| CALL / RET / IN 命令追加 | スタック設計 + CPU 拡張 |
| ブレークポイント設定 UI | エディタガター + CPU tick での PC 比較 |
| Video / Input Device | ゲーム入出力デバイスの実装 |
| Game Runtime | ゲーム実行環境の実装 |
| KiCad 基板連携 | netlist 生成 / 自動配線 |
| C コンパイラ対応 | 外部コンパイラ連携 |
| HDL 合成 | iverilog / Yosys 連携 |
| 実機書き込み | シリアル / USB |

---

## 命令エンコード仕様（v0.4.1 時点）

```
bits 31..24  opcode
bits 23..16  rd / rs（宛先または比較 reg 1）
bits 15..8   rs / rt（ソース reg または比較 reg 2）
bits  7..0   rt / imm8 / rel8
```

| opcode | ニーモニック | 動作 |
|---|---|---|
| 0x00 | NOP | なし |
| 0x01 | HALT | 実行停止 |
| 0x02 | LDI rd, imm16 | regs[rd] = imm16 |
| 0x03 | OUT [rd], rs | bus.write(regs[rd], regs[rs]) |
| 0x04 | ADD rd, rs, rt | regs[rd] = regs[rs] + regs[rt] |
| 0x05 | SUB rd, rs, rt | regs[rd] = regs[rs] - regs[rt] |
| 0x06 | LD rd, [rs] | regs[rd] = bus.read(regs[rs]) |
| 0x07 | ST [rd], rs | bus.write(regs[rd], regs[rs]) |
| 0x08 | JMP imm16 | pc = imm16 |
| 0x09 | BEQ rs, rt, rel8 | if regs[rs] == regs[rt]: pc += signed(rel8)*4 |
| 0x0A | ADDI rd, rs, imm8 | regs[rd] = regs[rs] + imm8 |
