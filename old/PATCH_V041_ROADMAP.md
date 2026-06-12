# v0.4.1 Patch — ROADMAP

> **注意:** このパッチは CLAUDE.md Rule 3（「実装前に ROADMAP / CHECKLIST を作成する」）に反して、
> 実装後に後追いで記録したものです。
> 次回以降のパッチでは必ず実装前に ROADMAP / CHECKLIST を作成してください。

---

## パッチ名

**v0.4.1 Patch — Canvas Routing Polish & Pre-Release Docs**

---

## 実施日

2026-05-30（セッション 40）

---

## 目的

v0.4 Visual Debug Canvas の公開前に、以下の 3 点を修正・整備する。

1. 配線ルートの曲がり角が不自然な問題を修正する
2. Canvas Pan の操作系を整理し、右クリック操作との競合を解消する
3. 公開前ドキュメント（QUICKSTART / USER_GUIDE）を追加する

---

## 背景

### v0.4 検査時に見つかった問題

#### 問題 1: 配線の角が不自然

- `ConnectionLine.update_route()` が「H-V 二重描画」を行っていた
  - BFS が返す経路点列（すでにコーナー点のみ）に対して、さらに H-V エルボーを挿入していた
  - 結果として、コーナー付近に余分な短い折れ線が発生していた
- 接続線の始端・終端がノード中心（140/2, 56/2）から出ていた
  - 視覚的に「パーツの中央から線が出る」不自然な形になっていた

#### 問題 2: 右クリック Pan がコンテキストメニュー・wire mode と競合

- Canvas Pan が右ドラッグで動作していた
- 右クリックはコンテキストメニューと wire mode waypoint 追加にも使うため競合していた
- `_panned` フラグで短押し（メニュー）と長押し（パン）を分離していたが、
  完全な分離はできておらず、wire mode 中の右クリックと干渉していた

#### 問題 3: 公開前ドキュメントが不足

- README.md が v0.1 時点の内容のままだった
- 初見ユーザーが 5 分で動かせるクイックスタートドキュメントがなかった
- 機能別の詳細説明ドキュメントがなかった

---

## 修正方針

### P1. 配線ルートの角修正

#### ConnectionLine.update_route の責務整理

**変更前:**

```python
def update_route(self, points: list) -> None:
    path = QPainterPath(points[0])
    for i in range(1, len(points)):
        mid = QPointF(points[i].x(), points[i - 1].y())
        path.lineTo(mid)
        path.lineTo(points[i])
    self.setPath(path)
```

各点ペア間で H-V エルボーを挿入していた。
BFS が返す経路点列はすでにコーナー点のみなので、二重にエルボーが発生していた。

**変更後:**

```python
def update_route(self, points: list) -> None:
    """BFS コーナー点をそのまま直線で繋ぐ。"""
    path = QPainterPath(points[0])
    for p in points[1:]:
        path.lineTo(p)
    self.setPath(path)
```

#### ConnectionLine.update_line の責務整理

`update_line(p1, p2)` は 2 点間の H-V 折れ線を描くシンプルな用途向け。
`update_route` の変更に合わせ、明示的にコーナー点を挿入するよう変更する。

**変更後:**

```python
def update_line(self, p1: QPointF, p2: QPointF) -> None:
    mid = QPointF(p2.x(), p1.y())
    self.update_route([p1, mid, p2])
```

#### ポート位置からの配線

`Canvas._from_port_pos(node_id)` / `_to_port_pos(node_id)` ヘルパーを追加する。

| ヘルパー | 返す位置 |
|---|---|
| `_from_port_pos` | ノード右端中央 `(node.x + _NODE_W, node.y + _NODE_H/2)` |
| `_to_port_pos` | ノード左端中央 `(node.x, node.y + _NODE_H/2)` |

`update_connections()` でノード中心 → ポート位置（グリッドスナップ）に変更する。

```
# 変更前
p1 = self._node_center(from_node_id)   # (node.x + 70, node.y + 28)

# 変更後
p1_raw = self._from_port_pos(from_node_id)  # (node.x + 140, node.y + 28)
p1 = QPointF(round(p1_raw.x()/g)*g, round(p1_raw.y()/g)*g)  # グリッドスナップ
```

グリッドスナップにより、BFS が生成する H/V セグメントが p1/p2 に自然に接続される。

#### Wire Mode Preview の更新

`_update_wire_preview()` も `_node_center` → `_from_port_pos` に変更し、
プレビュー線がポート位置から出るよう統一する。

### P2. Canvas Pan の中ボタン化

#### イベントハンドラの変更

| イベント | 変更前 | 変更後 |
|---|---|---|
| `mousePressEvent` | `RightButton` でパン開始 | `MiddleButton` でパン開始 |
| `mouseMoveEvent` | `RightButton` 保持で移動 | `MiddleButton` 保持で移動 |
| `mouseReleaseEvent` | `RightButton` 離でパン終了 | `MiddleButton` 離でパン終了 |

#### contextMenuEvent の変更

`_panned` ガードを削除する。

```python
# 変更前
def contextMenuEvent(self, event):
    if self._panned:
        self._panned = False
        return
    ...

# 変更後
def contextMenuEvent(self, event):
    # _panned チェック削除 — Pan は MiddleButton のため干渉しない
    ...
```

これにより、右クリックは**常に**コンテキストメニューを表示する。

#### 操作まとめ（変更後）

| 操作 | 動作 |
|---|---|
| 左クリック / 左ドラッグ | 選択・移動・ラバーバンド選択 |
| 右クリック | コンテキストメニュー / wire mode 操作 |
| 中ボタンドラッグ | Canvas Pan |
| ホイール | Zoom In / Out |

### P3. 公開前ドキュメント追加

#### docs/QUICKSTART.md

5 分で hello.asm を動かす手順書。

含める内容:
- 環境準備（Python 3.11+ / pip install）
- 起動方法
- New Project 作成手順
- パーツ配置（AK32 CPU / RAM / UART）
- hello.asm の記述と Build
- Run → UART に "Hi" が出る確認
- よくある詰まり

#### docs/USER_GUIDE.md

全機能の詳細説明。

含める内容:
- 画面構成（全パネルの説明）
- Parts Library の使い方
- Canvas 操作（選択・移動・削除・右クリックメニュー）
- Zoom / Grid / Snap
- Wire Mode（接続の作成・waypoint・RouteHandle）
- Build / Run / Step / Reset
- UART Console / Register View / Bus Trace / Memory Viewer
- PC ハイライト / Canvas Signal Overlay
- プロジェクト保存・読み込み
- 既知の制限

#### README.md の更新

- QUICKSTART.md / USER_GUIDE.md へのリンクを追加
- v0.4.1 時点でできることを整理
- v0.1 時点のクイックスタートを削除

---

## 今回やらないこと

| 項目 | 理由 |
|---|---|
| UI デザイン刷新 | v0.5 以降の計画 |
| GUI Designer 構想 | v0.5 以降 |
| 配線色変更 UI | v0.5 以降 |
| 設定画面 | v0.5 以降 |
| v0.5 計画作成 | 別セッションで実施 |
| 新しい CPU 命令追加 | v0.5 以降 |
| KiCad / VS Code 連携 | v0.5 以降 |

---

## 完了条件

| 条件 | 状態 |
|---|---|
| pytest 518 件全通過 | ✅ 達成 |
| 配線がパーツ端から自然な H/V 形で表示される | ✅ 達成 |
| 中ボタンドラッグで Canvas Pan できる | ✅ 達成 |
| 右クリックメニューが中ボタンパン後も正常に動作する | ✅ 達成 |
| wire mode 右クリック waypoint 追加が正常に動作する | ✅ 達成 |
| docs/QUICKSTART.md が存在する | ✅ 達成 |
| docs/USER_GUIDE.md が存在する | ✅ 達成 |
| README.md が QUICKSTART / USER_GUIDE にリンクしている | ✅ 達成 |
| 既存 route / export_canvas / import_canvas の保存形式が壊れていない | ✅ 達成 |
| BFS 障害物回避・RouteHandle 頂点編集が正常に動作する | ✅ 達成 |

---

## 影響ファイル一覧

### 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `ui/canvas.py` | update_route / update_line / update_connections / _from_port_pos / _to_port_pos / mousePressEvent / mouseMoveEvent / mouseReleaseEvent / contextMenuEvent / _update_wire_preview |

### 新規ファイル

| ファイル | 内容 |
|---|---|
| `docs/QUICKSTART.md` | 5 分クイックスタート |
| `docs/USER_GUIDE.md` | 全機能ユーザーガイド |

### 更新ファイル（ドキュメント）

| ファイル | 変更内容 |
|---|---|
| `README.md` | v0.4.1 対応・ドキュメントリンク追加 |
| `CHECKLIST5.md` | v0.4.1 Patch セクション追加 |
| `HANDOFF.md` | v0.4.1 作業内容・pytest 件数更新 |

### 更新ファイル（テスト）

| ファイル | 変更内容 |
|---|---|
| `tests/test_canvas_pan.py` | RightButton → MiddleButton 対応 |
| `tests/test_canvas_connection_lines.py` | center → port_pos テスト更新 |
| `tests/test_canvas_routing.py` | 新規テスト 9 件追加 |
| `tests/test_canvas_wire_mode.py` | update_route / update_line テスト更新 |

---

## テスト結果

| 時点 | pytest 件数 |
|---|---|
| v0.4 完了時 | 505 件 |
| v0.4.1 完了時 | **518 件**（+13 件） |

追加テスト内訳:

| テストファイル | 追加件数 | 内容 |
|---|---|---|
| `test_canvas_routing.py` | +9 | update_route 直線確認・update_line H-V 確認・_from/_to_port_pos・port edge テスト |
| `test_canvas_pan.py` | +1 | _panned が contextMenuEvent をブロックしないことの確認 |
| `test_canvas_wire_mode.py` | 既存 2 件更新 | update_route / update_line の新挙動に合わせてリネーム・修正 |

---

## 関連ファイル

- `PATCH_V041_CHECKLIST.md` — 実装チェックリスト
- `CHECKLIST5.md` — v0.4 チェックリスト（v0.4.1 セクション追記済み）
- `HANDOFF.md` — セッション 40 記録
