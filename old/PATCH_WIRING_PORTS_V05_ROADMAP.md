# PATCH_WIRING_PORTS_V05 — Dynamic Visual Port（設計書）

> v0.5 の別パッチ。Wiring UI を既存ノードエディタに近づけ、**Dynamic Visual Port**
> を導入する。進捗管理は `PATCH_WIRING_PORTS_V05_CHECKLIST.md`。
> 親フェーズは `ROADMAP6.md` / `CHECKLIST6.md`（v0.5）。
> 関連: `PATCH_WIRING_V05_ROADMAP.md`（armed/drawing 整理・削除同期・端点追従）。

---

## 1. 背景

PATCH_WIRING_V05 で wire モードの状態整理・キャンセル統一・削除同期・端点追従は
完了した。しかし接続のモデルは「ノード端の固定 1 点」に接続するだけで、既存の
ノードエディタ（Unity Shader Graph / Unreal Blueprint / Node-RED / LabVIEW /
Max/MSP / Rete.js / Drawflow / Qt Diagram Scene 等）と比べると素朴である。

これらに共通する挙動:

- 接続はポート / ピン / ソケットから開始する
- 接続中は preview wire を表示する
- 接続先候補を hover で示す
- 接続確定時は wire 端点を実ポート座標へ合わせる
- ノード削除時は関連 wire も自動削除する
- ノード移動時は wire が追従する
- Esc / 右クリック / Cancel で preview wire を破棄できる

このうち preview・端点追従・削除同期・キャンセルは既に対応済み。本パッチでは
**接続点（ポート）をデータとして持つ** ための基盤を入れる。

---

## 2. 方針: Dynamic Visual Port

### 用語

| 用語 | 意味 |
|---|---|
| **logical port** | part.json / シミュレーション上の意味を持つポート（bus / signal / clock / reset 等）|
| **visual port** | Canvas 上で wire が接続される見た目上の接点。ノードインスタンスごとに作られ、system.json に保存される。最初は 0 個 |

logical port と visual port を混同しない。本パッチではまず **visual port** を導入する。

### 採用する接続フロー（v0.5 最小）

1. Wire Mode で始点ノードを選ぶ（既存 armed → drawing）。
2. 接続先ノードで「ここに接続」。
3. **接続確定時に、両端ノードの wire 接点に visual port を自動生成**する。
4. 接続は visual port を参照する（`visual_port_id`）。
5. wire 端点は visual port の実座標に一致する。
6. ノード移動で visual port も追従し、wire も追従する。
7. ノード削除で visual port と関連 wire も削除する。

### Dynamic Visual Port の仕様

- 見た目上のポートは **最初は 0 個**。接続したときに作られる。
- visual port はパーツ（ノードインスタンス）ごとに持つ。
- visual port は `side`（left/right/top/bottom）と `offset`（その辺に沿った位置）を持つ。
- visual port は後から **移動**できる（本パッチは API + 整列。対話ドラッグは将来）。
- visual port は辺ごとに **整列**できる（均等配置）。
- visual port は接続に紐づく。接続が消えると visual port も prune される。

### 既存互換

- 既存の `_port_dot`（右中央の単一 dot）は **コード上は残すが Canvas 上は非表示**にする
  （`setVisible(False)`）。理由: シミュレーション互換の `_on_port_click` 2 ステップ接続
  フローと既存テスト（`test_canvas_port_connect.py`）が `node._port_dot` を参照するため、
  クラスとインスタンスは保持する。ただし **「見た目ポートは初期 0 個」方針**に合わせ、
  単一 dot を表示し続けることはしない。
- `visual_port_id` を持たない既存接続は、従来どおりノード端の座標に接続する。
- part.json の既存 ports はすぐ削除しない。
- 内部の接続 kind は当面 bus / signal など既存値を使う。

---

## 3. logical port と visual port の違い

| 観点 | logical port | visual port |
|---|---|---|
| 定義元 | part.json / sim | Canvas 操作（接続時生成）|
| 個数 | パーツ種別で固定 | インスタンスごと・可変（初期 0）|
| 保存先 | part.json | system.json（ノードエントリ内）|
| 役割 | 機能的意味 | 見た目の接点 |
| 例 | bus, clock | vp_0001（side=right, offset=12, kind=bus）|

visual port は `logical_port` を 1 つ参照する（どの logical port を表すか）。

---

## 4. system.json 保存形式

> 既存の保存は最上位キー `"parts"` を使うため、本パッチでもそれを維持する
> （ユーザー提示の `"nodes"` は説明用。実体は `parts` に `visual_ports` を入れ子）。

```json
{
  "parts": [
    {
      "node_id": "node_0001",
      "part_id": "ak32_cpu",
      "x": 100, "y": 100,
      "sources": {"asm": null, "hdl": null},
      "visual_ports": [
        {"id": "vp_0001", "side": "right", "offset": 12.0,
         "kind": "bus", "label": "bus", "locked": false}
      ]
    }
  ],
  "connections": [
    {
      "id": "conn_0001",
      "from": {"node_id": "node_0001", "port": "bus",
               "visual_port_id": "vp_0001", "logical_port": "bus"},
      "to":   {"node_id": "node_0002", "port": "bus",
               "visual_port_id": "vp_0002", "logical_port": "bus"},
      "kind": "bus", "route": []
    }
  ]
}
```

- `visual_ports` は 0 個なら省略する（既定パーツのファイルを汚さない）。
- `from`/`to` は後方互換のため `port` を残しつつ `visual_port_id` / `logical_port` を追加。

---

## 5. 今回実装する範囲

| # | 内容 |
|---|---|
| 1 | PartNode に visual_ports（`add/get/remove/set/visual_port_pos`）+ paint 描画 |
| 2 | Canvas に vp ID 採番（`_next_vp_id`）と接続時生成（`_finish_wire`）|
| 3 | 接続 from/to に `visual_port_id` / `logical_port` を保存 |
| 4 | `update_connections` の端点を visual port 座標で解決（無ければ従来端へ fallback）|
| 5 | export_parts / import_parts で visual_ports を round-trip |
| 6 | ノード削除時に関連 wire + 端点 visual port を同期削除（orphan prune）|
| 7 | visual port 移動 API（`set_visual_port_offset` / `set_visual_port_side`）|
| 8 | visual port 整列 API（`arrange_visual_ports`）+ 右クリック「ポートを整列」|
| 9 | テスト・ドキュメント |

---

## 6. 今回やらないこと

- port-drag connect の完全実装（ポートからドラッグして接続開始）→ 将来
- hover valid target の完全実装（接続先候補ハイライト）→ 将来
- Undo / Redo
- legacy `_port_dot` の完全削除（今回は非表示化のみ）
- Part Visual 色変更（別パッチ済み）
- visual port の対話ドラッグ（つまんで移動）→ 将来。本パッチは移動 API + 整列のみ
- logical port 種別の選択 UI（当面 "bus" 固定で生成）
- PHASE COMPLETE
- commit / push

---

## 7. テスト方針

- PartNode: visual_port の追加・取得・削除・座標計算
- Canvas: `_finish_wire` で両端に visual port が生成され、接続が参照する
- 端点解決: visual port 座標で wire が描かれる（移動追従）
- export/import: visual_ports と接続の visual_port_id が round-trip、ID 衝突なし
- 削除同期: ノード削除で関連 wire と端点 visual port が消える
- 整列・移動 API
- 後方互換: visual_port_id の無い接続は従来どおり動く
- 既存テスト（wire mode / routing / connection lines / delete）が通る
- hello.asm headless 検証維持

---

## 8. 追加修正（実装後の目視確認で発見）

### B5. visual port dot がパーツ移動後に古い位置へ残る

- **原因**: visual port は `PartNode.paint()` で辺上に半径 `_VP_RADIUS` の小円を描くが、
  `boundingRect()` が `QRectF(0,0,_NODE_W,_NODE_H)` のままで、辺の dot が boundingRect の
  **外側**に描かれていた。ノード移動時に旧位置の外側領域が再描画/クリアされず、
  「丸の切れ端」がゴーストとして残った。
- **対応**: `boundingRect()` を `_NODE_PAD`（= `_VP_RADIUS` + 余白）分だけ四方に拡張し、
  dot が常に item の bounds 内に入るようにした。これで移動時に旧 dot がクリアされる。
- **方針確認**: visual port は scene 絶対座標で固定保持せず、`side/offset/kind/label/locked`
  を PartNode ローカル情報として持ち、scene 座標は `PartNode.pos() + ローカル位置` で
  都度計算する（既存実装どおり。今回の修正で描画範囲のみ是正）。

### B6. wire が grid / Manhattan routing の見た目で visual port から自然に伸びない

- **原因**: `update_connections` が全接続で BFS grid routing（`_route_grid` → `update_route`）
  を使い、Dynamic Visual Port 接続も角張った経路で描かれていた。
- **対応**: Dynamic Visual Port を使う接続（`visual_port_id` を持つ）では
  **curved wire**（`ConnectionLine.update_curve`、cubic bezier）で描画。各ポートの `side` の
  外向き方向に制御点を出し、ノードエディタ風に自然に伸びる。
- **維持するもの**: Dynamic Visual Port のデータ構造は不変。捨てるのは「Dynamic 接続に対する
  grid/Manhattan 表示方式」のみ。`visual_port_id` の無い legacy 接続は従来の grid routing を
  維持（後方互換・既存テスト）。
