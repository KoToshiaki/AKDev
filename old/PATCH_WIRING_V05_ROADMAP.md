# PATCH_WIRING_V05 — Wiring Workflow Fix（設計書）

> v0.5 の別パッチ。Wiring 操作の問題（KI-1 ほか）を整理・修正する。
> 進捗管理は `PATCH_WIRING_V05_CHECKLIST.md`。
> 親フェーズは `ROADMAP6.md` / `CHECKLIST6.md`（v0.5 UI Polish & Usability）。
> UI 仕様は `UI_SPEC_V05.md` セクション 11-A / 11-G / 11-I を参照。

---

## 1. 背景

v0.5 UI Prototype Patch 2 までで、リボンは Parts / Wiring / Run / View / Debug の
5 タブに整理され、Wire Mode のトグル・Cancel Wire・ステータス表示・Escape 解除が
入った。しかし Wiring には **KI-1**（`ERROR.md`）として根本的な操作問題が残っている。

### 根本原因

wire モードへの入口が 2 系統あり、状態が食い違う:

| 入口 | 動作 | 問題 |
|---|---|---|
| 設計モード右クリック「接続を開始」→ `_start_wire(node)` | `_wire_from` を設定し preview 生成 | 正常 |
| リボン Wire Mode トグル → `set_mode("wire")` | `_mode="wire"` のみ。`_wire_from` 未設定 | 始点が無く「ここに接続」が無反応。右クリックが wire メニューに占有され通常操作が死ぬ |

---

## 2. 対象問題（ユーザー指摘）

1. Wire Mode 中に右クリックが「ここに接続」中心になり、通常操作が使いづらい
2. Wire Mode の開始・終了状態が分かりにくい
3. Cancel Wire がユーザーから見て信頼しにくい
4. 配線操作と通常 Canvas 操作が混ざっている
5. Wiring タブの操作導線がまだ弱い

---

## 3. 目標

Wiring を「使えるが分かりにくい状態」から、
**「開始・接続・キャンセル・通常操作復帰が明確な状態」** にする。

---

## 4. 設計方針

### 4-1. wire モードの状態整理

wire モードを 2 サブ状態として明確化する。

| サブ状態 | 条件 | 意味 |
|---|---|---|
| armed | `_mode == "wire"` かつ `_wire_from is None` | 配線モードだが始点未選択 |
| drawing | `_mode == "wire"` かつ `_wire_from is not None` | 始点選択済・接続先待ち |

- `_begin_wire_from(node_id, port_name)` を新設し、始点設定・preview 生成・handles 表示・
  装飾更新・`mode_changed` 発火を 1 箇所に集約する。
- 既存 `_start_wire()` は `_begin_wire_from()` への委譲にして、既存テストの互換を保つ。

### 4-2. 右クリックメニュー整理（wire モード中も通常操作を殺さない）

| 右クリック対象 | メニュー項目 |
|---|---|
| PartNode（armed）| **ここから接続を開始** / Wire Cancel / --- / Properties / プログラムを開く / HDLを開く / 複製 / 削除 |
| PartNode（drawing）| **ここに接続** / Wire Cancel / --- / Properties / プログラムを開く / HDLを開く / 複製 / 削除 |
| 空白（drawing）| Waypoint 追加 / Wire Cancel（design へ戻る）|
| 空白（armed）| Wire Cancel（design へ戻る）|

設計モードの右クリックメニューは **変更しない**。

### 4-3. キャンセルの統一

- Cancel Wire（リボン）／Escape（Canvas）／メニュー「Wire Cancel」は
  **すべて `_cancel_wire()` を経由して必ず design モードへ戻す**。
- `_cancel_wire()` は preview / waypoints / handles / pending / 装飾を確実にクリアする。
- キャンセル時は Log に分かりやすく出力する。

### 4-4. 接続完了後の挙動（仕様決定）

- **接続完了後は design モードへ戻る**（1 始点 = 1 接続）。
- 連続配線（接続後も wire モードを継続）は **将来拡張**とし、本パッチでは行わない。
- 本決定を `UI_SPEC_V05.md` 11-I に記録する。

### 4-5. 状態可視化

| 手段 | 内容 |
|---|---|
| ステータスバー | wire 時に操作ヒントを表示、design で消去（既存を踏襲・文言調整）|
| Wiring タブ | Wire Mode トグルの checked 状態で ON/OFF が分かる |
| Canvas 装飾 | wire 時に Canvas 枠を薄いアクセント色にする（軽い表示）|

---

## 5. 変更範囲

| ファイル | 変更 |
|---|---|
| `ui/canvas.py` | `_begin_wire_from` 追加、`_start_wire` 委譲化、contextMenuEvent の wire 分岐刷新、Canvas 装飾、`_cancel_wire` 装飾クリア、clone ヘルパ |
| `ui/win.py` | `_cancel_wire_action` 堅牢化、`_on_mode_changed` 文言調整 |
| `tests/test_canvas_wire_mode.py` | begin/cancel/decoration の追加テスト |
| `tests/test_wiring_v05.py` | 本パッチ専用テスト（新規）|

---

## 6. やらないこと

- 配線 UI の完全作り直し
- 連続配線モード（接続後の継続）
- Port Detail / Part Visual の本実装
- 配線色変更 UI
- commit / push

---

## 7. 完了条件

- Cancel Wire / Escape / メニュー Wire Cancel で必ず design に戻る
- wire モード中も Properties / 開く / 複製 / 削除 が右クリックから使える
- armed → drawing → 接続 → design のフローが動く
- Waypoint 追加・接続作成が壊れていない
- 既存 canvas routing / wire mode テストが通る
- `pytest tests/` 全通過
- KI-1 を `ERROR.md` で解決済みに更新

---

## 8. 追加修正（ユーザー目視確認で発見したバグ）

PATCH_WIRING_V05 完了後の目視確認で見つかった 3 件を本パッチの追加修正として扱う。
進捗は `PATCH_WIRING_V05_CHECKLIST.md` の W9〜W14。

### B1. ノード削除時に接続 wire が残る

- **原因**: 削除経路（Delete キー / 右クリック削除 / `delete_selected`）が分散し、
  `_connections` データと ConnectionLine アイテムを同期削除していなかった。
- **対応**: `_remove_node(node_id)` を単一の削除窓口にし、ノード本体・接続データ・
  ConnectionLine・wire/pending 状態をまとめて削除。全削除経路を集約。

### B2. wire とパーツの間に隙間ができる

- **原因**: `update_connections` で端点を grid snap していたため、snap OFF（自由座標）の
  パーツでは wire 端点が実ポートからずれていた。
- **対応**: BFS/waypoint は grid のまま、**端点だけ実ポート座標で上書き**。移動追従も保証。

### B3. 中ボタン Pan 初回で画面が動かず未読込に見える

- **原因**: `sceneRect` 未設定で空シーンでは scrollbar 可動域が無く Pan が無反応。
  grid OFF で背景も無地のため移動が分からなかった。
- **対応**: 広い `setSceneRect` を初期化、起動時 `center_origin()`、grid OFF でも原点十字を
  常時描画、"Canvas ready" を Log/ステータスバー表示。

---

## 9. 参考: 既存ノード UI 調査（B4）

wire の挙動は既存のノード系アプリに近づけたい。代表例として
**Unity Animator / Shader Graph、Blender Node Editor、Unreal Blueprint** を参考にする。

### 一般的なノード UI の挙動

- ポート / ソケット / ピンからドラッグして別ポートへ接続する
- 接続中はプレビュー線を表示する
- 接続可能な相手をハイライトする／接続できない相手は不可表示にする
- 接続制約を持つ（入力側は 1 本、出力側は複数本 など）
- **ノード削除時は関連する接続も自動削除する**（← B1 で AKDev も対応）
- ノード移動時は接続線が追従する（← B2 で端点追従を保証）
- 未接続時はデフォルト入力や未接続表示を持つ場合がある
- リンクの切断・差し替え・再接続ができる

### AKDev での当面の方針

- v0.5 では **右クリック方式を維持**しつつ、内部設計は **ポート接続モデルへ寄せる**。
- 将来的には「**ポートからドラッグして接続**」を実装候補にする。
- 接続可能/不可能のハイライトは将来。
- 今回は **削除同期（B1）・端点座標（B2）・初期 Canvas 表示（B3）** を優先修正した。
