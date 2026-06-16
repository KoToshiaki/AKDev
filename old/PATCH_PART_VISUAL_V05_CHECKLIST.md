# PATCH_PART_VISUAL_V05 — Part Visual 第1段階（チェックリスト）

> 設計書: `PATCH_PART_VISUAL_V05_ROADMAP.md`。
> 親フェーズ: `ROADMAP6.md` / `CHECKLIST6.md`（v0.5）。
> 設計根拠: `UI_SPEC_V05.md` 11-D。

---

## V0. 事前確認

* [x] 既存ドキュメント（CLAUDE / ROADMAP6 / CHECKLIST6 / HANDOFF / UI_SPEC_V05）を確認
* [x] 現状コード（PartNode.paint / _CAT_COLOR / export_parts / import_parts / PropPanel）を精査
* [x] パッチ ROADMAP / CHECKLIST を先に作成

## V1. PartNode の色保持

* [x] `_color` インスタンス変数を追加（空 = 既定）
* [x] `set_color(hex)`（QColor.isValid 検証、空で既定へ戻す）
* [x] `color()` アクセサ
* [x] `paint()` で instance_color 優先（無ければカテゴリ色）

## V2. Canvas の色 API と永続化

* [x] `set_node_color(node_id, hex) -> bool`
* [x] `export_parts()` で色設定時のみ `instance_color` を保存
* [x] `import_parts()` で `instance_color` を復元

## V3. PropPanel の Color Palette

* [x] 「Visual」セクションを追加
* [x] 約 100 色（10×10）のパレットをコード内生成
* [x] スウォッチクリックで `color_changed(node_id, hex)` 発火
* [x] 「Default」で既定色へ戻す（`color_changed(node_id, "")`）
* [x] 選択中 node_id を保持／複数・未選択でパレットを隠す
* [x] 外部素材・外部ライブラリを追加していない

## V4. MainWin 接続

* [x] `PropPanel.color_changed` を接続
* [x] `canvas.set_node_color()` を呼ぶ
* [x] プロジェクトが開いていれば `_persist_system()` で保存

## V5. テスト

* [x] PartNode set_color / color / 無効値拒否
* [x] Canvas.set_node_color
* [x] export/import の instance_color round-trip
* [x] 既定パーツに余計な色キーが入らない
* [x] PropPanel: パレット数・color_changed 発火・Default
* [x] MainWin: color_changed → ノード色反映
* [x] `pytest tests/` 全通過

## V6. 手動確認

* [x] hello.asm headless 検証（UART "Hi"）維持
* [x] 色変更 → export → import の round-trip を headless 確認
* [ ] GUI 目視確認（ヘッドレス環境のため未実施 — 報告に記載）

## V7. ドキュメント / レビュー

* [x] `UI_SPEC_V05.md` 11-D を第1段階実装済みに更新
* [x] `HANDOFF.md` 更新
* [x] 作業報告
