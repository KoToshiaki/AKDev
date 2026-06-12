# PATCH_PORT_DRAG_CONNECT_V05 — Port Drag Connect（設計書）

> v0.5 の別パッチ。**visual port からドラッグして別ノードへ接続**する操作を追加する。
> 進捗管理は `PATCH_PORT_DRAG_CONNECT_V05_CHECKLIST.md`。
> 親フェーズは `ROADMAP6.md` / `CHECKLIST6.md`（v0.5）。
> 前提: `PATCH_WIRING_PORTS_V05`（Dynamic Visual Port + curved wire）。

---

## 1. 背景

Dynamic Visual Port により、接続点はデータ化され curved wire で描画されるように
なった。次の段階として、既存ノードエディタ（Shader Graph / Blueprint 等）の中心操作
である「**ポートからドラッグして接続**」を最小実装する。

既存の右クリック接続（「ここから接続を開始」→「ここに接続」）は **残す**。
port-drag は追加の接続手段。

---

## 2. 採用する操作フロー

1. visual port の上で**左ボタン押下** → port-drag 開始。
2. ドラッグ中、押下した port から**カーソルへ向かう preview curved wire**（破線）を表示。
3. 別ノードの上で**離す** → 接続確定。
4. 同一ノード上 / 何も無い場所で離す、または Esc / 右クリック → **キャンセル**。

確定時:
- source は **既存の visual port** を参照（その port から複数本を fan-out できる）。
- target ノードに **新しい visual port を生成**（左辺）。
- `add_connection(from_vp=既存, to_vp=新)` で Dynamic Visual Port 接続として作成。
- 描画は既存の curved wire、保存は既存の export/import に乗る。

---

## 3. 設計方針

### visual port のヒットテスト

visual port は独立 QGraphicsItem にせず（現状どおり `PartNode.paint()` で描画）、
Canvas 側で **幾何ヒットテスト** `_visual_port_at(scene_pos)` を行う:

- 全 PartNode の visual port について `node.visual_port_pos(vp)` を計算し、
  press の scene 座標との距離が `半径 + slack` 以内なら hit。

### 状態

Canvas に右クリック wire 状態とは独立した軽量状態を持つ:

- `_port_drag`: `{node_id, vp_id, logical_port, side}` または None
- `_port_drag_preview`: 破線 cubic の `QGraphicsPathItem` または None

### イベント処理

| イベント | 動作 |
|---|---|
| 左 press on vp | `_start_port_drag` → preview 生成。`accept()` し super を呼ばない（ノード移動/選択を起こさない）|
| mouseMove（_port_drag 中）| preview を source port → カーソルの curved 破線に更新 |
| 左 release（_port_drag 中）| release 位置のノードを判定。別ノード → 確定、それ以外 → キャンセル |
| Esc（_port_drag 中）| キャンセル |
| 右クリック（_port_drag 中）| キャンセル（メニューは出さない）|

中ボタン pan・右クリック wire・Delete・既存 wire-mode は不変。

### 既存資産への接続

- 確定は `add_connection(..., from_vp=src_vp_id, to_vp=new_vp_id)`。
- 端点解決・curved 描画・移動追従・削除同期・export/import は
  `PATCH_WIRING_PORTS_V05` の実装をそのまま使う。

---

## 4. 変更範囲

| ファイル | 変更 |
|---|---|
| `ui/canvas.py` | `_visual_port_at` / `_start_port_drag` / `_update_port_drag_preview` / `_finish_port_drag` / `_cancel_port_drag` / mousePress・Move・Release・keyPress・contextMenu フック |
| `tests/test_port_drag_connect_v05.py` | 新規テスト |
| `UI_SPEC_V05.md` | 11-J に port-drag 操作を追記 |
| `ROADMAP6.md` / `CHECKLIST6.md` | 本パッチ参照 |
| `HANDOFF.md` | 状況更新 |

---

## 5. 今回やらないこと

- hover valid target の完全実装（接続可能ノードのハイライト）
- visual port の対話ドラッグ移動（port 自体を掴んで動かす）
- Undo / Redo
- Connection constraint 本実装（入力1本/出力複数 等）
- 空ポート（接続前）からのドラッグ開始（visual port は接続時生成のため、最初の接続は右クリック）
- PHASE COMPLETE / commit / push

---

## 6. 完了条件

- visual port 上の左ドラッグで port-drag が開始し preview が出る
- 別ノードで離すと接続が確定し、curved wire で描かれる
- source は既存 vp を参照、target に新 vp が作られる
- 同一ノード / 不正位置 / Esc / 右クリックでキャンセルできる
- 既存の右クリック接続が壊れていない
- 確定接続が export/import で round-trip する
- 既存テスト全通過 + hello.asm headless 維持
