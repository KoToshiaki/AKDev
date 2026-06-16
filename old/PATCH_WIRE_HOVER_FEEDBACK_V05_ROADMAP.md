# PATCH_WIRE_HOVER_FEEDBACK_V05 — ROADMAP

> v0.5 UI Polish & Usability の一部。Wiring / Port Drag Connect に **hover feedback** を追加する。
> 進捗管理は `PATCH_WIRE_HOVER_FEEDBACK_V05_CHECKLIST.md`。
> 仕様の親文書は `ROADMAP6.md` / `UI_SPEC_V05.md`（11-J 配下）。

---

## 1. 目的

接続操作（visual port / wire / port-drag）で、**いま何が操作対象になっているか**を
マウスホバーで分かるようにする。クリックや接続を実行する前に対象を視認できる状態にし、
誤接続・迷いを減らす。

完成版の選択 UI ではなく、**視覚フィードバックのみ**を足す小さなパッチ。

## 2. 前提（着手時点）

- `pytest tests/` 630 件全通過。
- visual port からドラッグして別ノードへ接続できる（PATCH_PORT_DRAG_CONNECT_V05）。
- Dynamic Visual Port 接続は curved wire で描画される（PATCH_WIRING_PORTS_V05）。
- GitHub へのチェックポイント push 済み。

## 3. スコープ

### 3-1. visual port hover

- visual port にマウスを近づけると、その port を強調表示する（明るく + 白枠 + 少し拡大）。
- hover 中の visual port を Canvas 内部状態 `_hover_vp = {"node_id", "vp_id"}` で保持。
- `mouseMoveEvent`（ボタン非押下時）で `_visual_port_at(scene_pos)` を使って更新。
- マウスが離れたら通常表示へ戻す（別 port へ移る / port 外 / Canvas 外 = `leaveEvent`）。
- 反映は `PartNode.paint()` の visual port 描画ループ内で行う。

### 3-2. wire hover

- wire にマウスを近づけると、その wire を強調表示する（少し太く + 明るく）。
- `ConnectionLine.set_hovered(bool)` を追加。pen は `_apply_pen()` で集中管理し、
  active（signal overlay）と hover を両立させる（active 優先）。
- `mouseMoveEvent` で `_connection_at(scene_pos)` により対象 wire を距離判定で特定。
- hover 解除で通常表示へ戻す。
- **wire 選択 / Delete Wire は今回やらない。**

### 3-3. port-drag 中の接続先候補ハイライト

- port-drag 中、カーソル下の **別ノード**を接続先候補として薄くハイライトする。
- 同一ノード（ドラッグ元）は接続不可なのでハイライトしない。
- 接続可能/不可能の厳密な型判定はしない（別ノードなら候補扱い）。
- `Canvas._hover_drop_node_id` で保持。`PartNode.set_drop_highlight(bool)` で表現。
- 表現は `PartNode.paint()`（アクセント色の外枠）。
- port-drag 終了 / キャンセルで必ず解除する（`_cancel_port_drag()` に集約）。

### 3-4. ステータス/ログ補助（軽量）

- port-drag 開始時に 1 行だけログ補助を出す（"Wire: drag to another part to connect"）。
- mouseMove での連続ログは出さない（スパム防止）。statusBar 連携は今回省略可。

## 4. 今回やらないこと

- wire 選択 / Delete Wire
- visual port の対話ドラッグ移動
- hover valid target の厳密な型判定 / Connection constraint 本実装
- Undo / Redo
- Port Detail 本実装 / Part Visual サイズ変更
- PHASE COMPLETE / commit / push

## 5. 後方互換の担保

- `set_active` の挙動は `_apply_pen()` リファクタ後も同一（base 復元・active=lighter160/+1.5）。
  既存 `test_canvas_signal_overlay.py` の pen 復元テストを壊さない。
- 既存の右クリック接続 / port-drag 接続 / export-import は無改変。
- hover 状態はすべて描画・内部状態のみ。接続データ構造には触れない。

## 6. 完了条件

- 上記 3-1〜3-4 が実装され、`PATCH_WIRE_HOVER_FEEDBACK_V05_CHECKLIST.md` が全 `[x]`。
- `pytest tests/` 全件通過（既存 630 + 新規）。
- 既存接続フロー・export/import が回帰していない。
