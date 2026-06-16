# PATCH_PART_VISUAL_V05 — Part Visual 第1段階（設計書）

> v0.5 の別パッチ。Part Visual 編集の **第1段階（色変更）** を実装する。
> 進捗管理は `PATCH_PART_VISUAL_V05_CHECKLIST.md`。
> 親フェーズは `ROADMAP6.md` / `CHECKLIST6.md`（v0.5）。
> 設計根拠は `UI_SPEC_V05.md` 11-D（Part Visual 編集方針）。

---

## 1. 背景

`UI_SPEC_V05.md` 11-D で、PowerPoint のようにパーツの色・サイズをマウス操作で
変更したいという要望を「段階実装」として記録した。

| 段階 | 内容 | 本パッチ |
|---|---|---|
| 1 | Properties の Color Palette で PartNode 色変更 + system.json 保存 | **対象** |
| 2 | Canvas のサイズ変更ハンドル | 次パッチ（大きいため分離）|

本パッチは **第1段階（色変更）のみ**を小さく実装する。

---

## 2. 目標

- パーツを選択し、Properties から色を選んで PartNode の色を変えられる。
- 選んだ色はインスタンスごとに保存され、再読み込みで復元される。
- 既定（カテゴリ色）へ戻せる。

---

## 3. 設計方針

### 3-1. 色の優先順位

`UI_SPEC_V05.md` 11-D に従う:

```
カテゴリ既定色  <  part.json の color  <  system.json の instance_color
```

本パッチでは **カテゴリ既定色 と instance_color** を扱う
（part.json の color フィールド対応は将来。今回は触らない）。

### 3-2. PartNode（`ui/canvas.py`）

- `self._color: str = ""`（空 = 既定色）を追加。
- `set_color(hex: str)`: `QColor(hex).isValid()` のときのみ採用。空文字で既定へ戻す。
- `color() -> str`: 現在の instance_color（未設定なら ""）。
- `paint()`: `_color` が有効ならその色、無ければ従来どおりカテゴリ色。

### 3-3. Canvas（`ui/canvas.py`）

- `set_node_color(node_id, hex) -> bool`: 対象 PartNode に色を適用し再描画。
- `export_parts()`: 色が設定されている場合のみ `"instance_color"` を保存。
- `import_parts()`: `instance_color` を読み、`set_color()` で復元。

### 3-4. PropPanel（`ui/prop.py`）

- 「Visual」セクションを追加し、**約 100 色のカラーパレット**（10×10）を表示。
- パレットはコード内生成（外部素材・外部ライブラリ不使用）。
- スウォッチクリックで `color_changed(node_id, hex)` シグナルを発火。
- 「Default」ボタンで既定色へ戻す（`color_changed(node_id, "")`）。
- 選択中ノードの `node_id` を保持。複数選択/未選択時はパレットを隠す。

### 3-5. MainWin（`ui/win.py`）

- `PropPanel.color_changed` を `_on_part_color_changed(node_id, hex)` に接続。
- ハンドラ: `canvas.set_node_color()` → プロジェクトが開いていれば `_persist_system()`。

---

## 4. 変更範囲

| ファイル | 変更 |
|---|---|
| `ui/canvas.py` | PartNode 色保持・`set_node_color`・export/import の instance_color |
| `ui/prop.py` | Visual セクション + Color Palette + `color_changed` シグナル |
| `ui/win.py` | `color_changed` 接続 + 保存 |
| `tests/test_part_visual_v05.py` | 新規テスト |
| `UI_SPEC_V05.md` | 11-D を第1段階実装済みに更新 |

---

## 5. やらないこと

- サイズ変更ハンドル（第2段階）
- part.json の color 既定値対応
- 配線色変更 UI
- Port Detail / Part Visual のそれ以外
- commit / push

---

## 6. 完了条件

- Properties から色を選ぶと PartNode の色が変わる
- Default で既定色へ戻る
- instance_color が export/import で round-trip する
- 既定（未設定）パーツの export に余計な色キーが入らない
- 既存テストが通る
- `pytest tests/` 全通過
