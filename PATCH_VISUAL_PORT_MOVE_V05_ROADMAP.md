# PATCH_VISUAL_PORT_MOVE_V05 — ROADMAP

> v0.5 UI Polish & Usability の一部。visual port を Canvas 上で **対話的に移動**できるようにする。
> 進捗管理は `PATCH_VISUAL_PORT_MOVE_V05_CHECKLIST.md`。
> 仕様の親文書は `ROADMAP6.md` / `UI_SPEC_V05.md`（11-J 配下）。

---

## 1. 目的

接続済みの visual port を **Alt + 左ドラッグ**で PartNode の辺上に沿って動かせるようにする。
既存の `set_visual_port_offset` / `set_visual_port_side` API（プログラム的移動）を、
マウス操作の入口でつなぐ小さなパッチ。配線の見た目を手で整えられるようにする。

## 2. 前提（着手時点）

- `pytest tests/` 全通過（直近 668 件）。
- visual port は接続時に生成され、`side / offset / kind / label / locked` を持つ。
- `Canvas` に `set_visual_port_offset` / `set_visual_port_side` / `arrange_visual_ports` がある。
- port-drag connect（左ドラッグ）/ wire 選択・削除 / hover feedback / curved wire が実装済み。

## 3. スコープ

### 3-1. Alt + 左ドラッグ移動

- 通常左ドラッグは既存どおり **port-drag connect**。
- **Alt + 左押下 on visual port** のときだけ **port move** を開始する。
- 移動中は対象 visual port を強調表示し、マウスに合わせて位置を更新。接続 wire もリアルタイム追従。
- マウス release で確定。Esc / 右クリックでキャンセル（移動前へ復元）。
- `locked=True` の visual port は移動開始しない（ログ 1 行）。

### 3-2. 位置の決め方（辺拘束）

- マウス scene 座標を対象 PartNode のローカル座標へ変換。
- 最も近い辺で `side`（left/right/top/bottom）を決定、辺に沿った距離を `offset` に。
- `offset` はノードサイズ範囲内に clamp。保存値は **side + offset** のまま（scene 絶対座標は持たない）。
- サイズは現状固定（`_NODE_W` / `_NODE_H`）。将来のサイズ変更に備え `PartNode.node_size()` を用意（中身は固定値）。

### 3-3. 既存 port-drag connect との衝突回避

- 左クリック on visual port: Alt なし→ port-drag connect、Alt あり→ port move。
- `_port_drag` と `_port_move` を別状態として扱う。
- port move 中は wire 選択 / node 移動を起こさない。右クリックはメニューを出さずキャンセル。

### 3-4. locked visual port

- Alt + drag しても移動開始しない。ログ "Visual port is locked" を 1 行のみ。連続ログ禁止。
- locked port の既存 wire はそのまま。

### 3-5. 移動中の wire 追従

- `_update_port_move()` で vp の side/offset を更新し `update_connections()` を呼ぶ。
- curved wire の端点が新しい visual port 位置に一致。
- **fan-out**（共有 vp）を動かすと、その vp を参照する全 wire が追従する（端点は vp 位置参照のため自動）。

### 3-6. キャンセル復元

- `_port_move` 開始時に `original_side` / `original_offset` を保持。
- cancel で元の side/offset へ戻し、`update_connections()` で wire も戻す。highlight 解除・状態クリア。

### 3-7. 保存導線

- visual port の side/offset は system.json に保存され、export/import round-trip で維持。
- ノード移動・wire 削除と同じく **自動 persist はしない**（保存時 `export_parts`/`export_canvas` に委ねる）。
  保存仕様は変更しない。

### 3-8. 表示

- 移動中 visual port は hover より強い強調（`PartNode.paint()`、専用色 `_PORT_MOVE_COLOR`）。
- selected/active/hover wire・drop target highlight とは別状態。z-order 調整はしない。

## 4. 今回やらないこと

- visual port の通常左ドラッグ移動 / 複数選択 / 削除 UI / rename / logical port 選択 UI
- Port Detail 本実装 / wire 色変更 UI / wire ラベル / connection constraint 本実装
- Undo・Redo / Part Visual サイズ変更 / `ui/canvas.py` 分割リファクタ / PHASE COMPLETE / commit / push

## 5. 後方互換の担保

- 既存の port-drag connect（Alt なし）/ wire 選択・削除 / 右クリック接続 / curved wire /
  hover feedback / export-import は無改変。
- `set_visual_port_offset` / `set_visual_port_side`（プログラム API）は維持。
- port move は side/offset の更新のみ。connection データ構造・vp スキーマは変更しない。

## 6. 完了条件

- 3-1〜3-8 が実装され `PATCH_VISUAL_PORT_MOVE_V05_CHECKLIST.md` が全 `[x]`。
- `pytest tests/` 全件通過（既存 + 新規）。
- 既存接続フロー・hover・選択削除・export/import が回帰していない。
