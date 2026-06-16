# PATCH_WIRE_STYLE_V05 — ROADMAP

> v0.5 UI Polish & Usability の一部。選択中 wire の **色・表示情報を編集**できるようにする。
> 進捗管理は `PATCH_WIRE_STYLE_V05_CHECKLIST.md`。
> 仕様の親文書は `ROADMAP6.md` / `UI_SPEC_V05.md`（11-J 配下）。

---

## 1. 目的

接続済み wire ごとに見た目（色・太さ）を設定できるようにする。
wire 選択時に Properties パネルへ wire 情報を表示し、色パレットと太さ・Reset で編集する。
kind（bus/signal/clock/reset）の意味は変えず、**表示だけ**を上書きする小さなパッチ。

## 2. 前提（着手時点）

- `pytest tests/` 全通過（直近 685 件）。
- wire は選択・削除でき、`ConnectionLine._apply_pen()` で selected/active/hover を集中管理。
- visual port は Alt+ドラッグで移動、Dynamic Visual Port 接続は curved wire。
- PartNode 色変更（Properties の color パレット + `color_changed` signal）が実装済み。

## 3. スコープ

### 3-1. wire style データ構造

- connection に任意キー `style`（`{"color": "#hex", "width": float}`）を追加。
- style 未設定時は既存 kind 色/幅を使う。kind の意味は不変。
- 後方互換: 既存 connection（style 無し）も読み込める。export/import round-trip で style 維持。
- style が空なら保存に出さない（余計なキーを書かない）。

### 3-2. ConnectionLine 描画対応

- `apply_style(color="", width=None)`: color/width 指定で base pen を作る。無指定は kind 既定。
- 表示優先度: **selected > active > hover > custom style(color/width) > kind default**。
  selected/active/hover は base pen（custom 含む）の上に重ねる（既存 `_apply_pen()` を活用）。

### 3-3. Canvas API

- `set_connection_style(conn_id, color=None, width=None) -> bool`（None は当該属性を変更しない、
  color="" は color をクリア）。
- `reset_connection_style(conn_id) -> bool`（style を消す）。
- `get_connection(conn_id) -> dict | None`。
- 存在しない conn_id は False。変更後に ConnectionLine 表示を更新。selected/hover は維持。

### 3-4. Properties 表示

- wire 選択時、Properties を **Wire セクション**に切替（node 選択時の表示は不変）。
- 表示: connection id / kind / from(node・logical port・vp id) / to(...) / color / width。
- 編集: color（パレット + Default）/ width（プリセット）/ Reset Style。
- Canvas → MainWin へ wire 選択通知（`wire_selected(dict)` / `wire_selection_cleared()`）。
  既存の node 選択通知（`selection_changed`）と衝突しない。

### 3-5. Color Palette

- PartVisual の生成処理を参考に、wire 用の小さめパレット（〜12 色）+ Default。外部素材なし。
- part 用パレットと wire 用パレットは別 swatch・別ハンドラ（誤動作防止）。

### 3-6. 右クリックメニュー

- wire 右クリックに「Delete Wire」（既存維持）+「Reset Wire Style」を追加。
- 色変更は Properties 主導。PartNode 右クリック / port-drag / port-move / wire mode は不変。

### 3-7. 保存形式

- export/connections に style を含める（未設定は出さない）。import で復元。
- 既存プロジェクト（style 無し）でも読める。round-trip で維持。

## 4. 今回やらないこと

- connection kind の本格編集 / signal/bus/clock/reset の意味変更 / wire label / wire rename
- connection constraint 本実装 / Port Detail 本実装 / visual port 削除 UI・rename
- Part Visual サイズ変更 / `ui/canvas.py` 分割 / Undo・Redo / PHASE COMPLETE / commit / push

## 5. 後方互換の担保

- 既存の port-drag connect / wire 選択・削除 / visual port move / 右クリック接続 / curved wire /
  hover / signal overlay / export-import は無改変。
- `conn["width"]`（論理バス幅 bits）と `style.width`（描画ペン幅）は別物として扱う。
- node 選択 Properties（show_part / Visual color）の挙動は維持。

## 6. 完了条件

- 3-1〜3-7 が実装され `PATCH_WIRE_STYLE_V05_CHECKLIST.md` が全 `[x]`。
- `pytest tests/` 全件通過（既存 + 新規）。
- 既存接続フロー・選択削除・port move・Properties(node)・export/import が回帰していない。
