# PATCH_WIRE_SELECT_DELETE_V05 — ROADMAP

> v0.5 UI Polish & Usability の一部。作成済みの wire を **選択・削除**できるようにする。
> 進捗管理は `PATCH_WIRE_SELECT_DELETE_V05_CHECKLIST.md`。
> 仕様の親文書は `ROADMAP6.md` / `UI_SPEC_V05.md`（11-J 配下）。

---

## 1. 目的

接続済み wire を選び、不要な接続を削除できるようにする。
hover feedback（PATCH_WIRE_HOVER_FEEDBACK_V05）の上に **選択状態**と**削除導線**を足す。

完成版の編集 UI ではなく、選択・削除に限定した小さなパッチ。

## 2. 前提（着手時点）

- `pytest tests/` 全通過（直近 649 件）。
- visual port からドラッグして接続でき、Dynamic Visual Port 接続は curved wire で描画。
- wire / visual port / drop target の hover feedback 実装済み（`ConnectionLine._apply_pen()` で pen 集中管理）。

## 3. スコープ

### 3-1. wire 選択

- wire を左クリックすると選択（`_selected_conn_id`）。別 wire クリックで移動、空白で解除。
- 選択中 wire は通常 / hover より強く強調。表示優先度 **selected > active > hover > normal**。
- visual port クリック / port-drag 開始時は wire 選択しない。PartNode クリックはノード選択優先。
- `ConnectionLine.set_selected(bool)` / `is_selected()` を追加し pen は既存 `_apply_pen()` に統合。

### 3-2. wire 削除 API

- `Canvas._remove_connection(conn_id)` を単一削除 API として新設。
  - `_connections` から対象を削除、`_conn_items` の ConnectionLine を scene から除去。
  - selected / hovered がその conn を指していれば解除。
  - `_prune_orphan_visual_ports()` を呼ぶ（**fan-out 元の vp が他 conn から参照されていれば残す**。
    prune は残存 connection 群から referenced を作り直すため共有 vp は安全）。
  - `update_connections()` を呼ぶ。
  - 保存は既存導線（保存時 `export_parts`/`export_canvas`）に委ねる。ノード削除と同じ方針。

### 3-3. Delete キー

- wire 選択中に Delete → その wire のみ削除。選択なし → 従来のノード削除。
- 優先順位: port-drag 中 / wire mode の Esc・Cancel は従来どおり。Delete は
  `selected wire（かつ port-drag でない）→ wire 削除`、それ以外 → `delete_selected()`。

### 3-4. wire 右クリックメニュー

- wire 近くで右クリック → その wire を選択し「Delete Wire」メニュー表示 → `_remove_connection`。
- wire でない場所 / PartNode 上 / port-drag 中 / wire mode は従来の挙動を維持。
- z-order 調整はしない。PartNode 上なら PartNode メニュー優先。

### 3-5. 選択解除タイミング

- 空白左クリック / ノード左クリック / wire 削除後 / import（canvas clear）/ 接続データ消失時。
- hover 解除とは独立した状態として扱う（`_set_hover_conn()` は selected を解除しない）。

### 3-6. hover との統合

- hover 中 wire は軽く、selected wire は強く強調。active と selected が重なっても破綻しない
  （`_apply_pen()` で selected を最優先）。selected wire を hover しても表示が戻らない。

## 4. 今回やらないこと

- wire Properties パネル / 色変更 UI / ラベル表示 / connection constraint 本実装
- visual port の対話ドラッグ移動 / Undo・Redo / 複数 wire 選択 / wire z-order 調整
- Port Detail 本実装 / Part Visual サイズ変更 / PHASE COMPLETE / commit / push

## 5. 後方互換の担保

- `set_active` / `set_hovered` の挙動は `_apply_pen` 優先度追加後も維持（既存 pen テストを壊さない）。
- 既存の右クリック接続 / port-drag 接続 / curved wire / export-import は無改変。
- ノード削除（`_remove_node`）の既存挙動は維持。選択中 wire がノード削除で消えた場合は選択を解除。

## 6. 完了条件

- 3-1〜3-6 が実装され `PATCH_WIRE_SELECT_DELETE_V05_CHECKLIST.md` が全 `[x]`。
- `pytest tests/` 全件通過（既存 + 新規）。
- 既存接続フロー・hover・export/import が回帰していない。
