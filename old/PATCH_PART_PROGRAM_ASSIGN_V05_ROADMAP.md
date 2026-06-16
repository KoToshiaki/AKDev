# PATCH_PART_PROGRAM_ASSIGN_V05 — ROADMAP

> v0.5 UI Polish & Usability の一部。Canvas 上のパーツに**外部ソースファイルを割り当て**、
> Build / Run がその割り当てを参照できるようにする。
> 進捗管理は `PATCH_PART_PROGRAM_ASSIGN_V05_CHECKLIST.md`。
> 仕様の親文書は `ROADMAP6.md` / `UI_SPEC_V05.md`（11-K）。

---

## 0. 位置づけ（重要）

- **今回はテスト用の最小実装である。** 完成版のプログラム管理ではない。
- ただし**保存形式と API は将来の正式実装に拡張しやすい構造**にする。
- **固定で hello.asm を読むだけの実装にはしない**（割り当てを優先順位で解決する）。
- 将来は **内蔵エディタ / Build Graph / Canvas からの CPU・ROM・RAM 自動解決 / 実機書き込み**
  へ拡張する。今回はその「入口」だけを作る。

## 1. 目的

Canvas 上の CPU 系パーツに asm を割り当て、その asm で既存 hello.asm と同等の Run ができる
状態にする。割り当ては system.json に保存・復元し、Properties / 右クリックから操作できる。

## 2. sources データ構造

PartNode は既に `_sources`（既定 `{"asm": None, "hdl": None}`）を持つ。これを土台に拡張する。

最小保存形式（今回は**文字列 path 形式**）:

```json
{ "sources": { "asm": "src/hello.asm", "hdl": null } }
```

- `asm` / `hdl` / `rom` のキーを想定（`rom` は設定時のみ出現。既定には**追加しない** ＝
  既存の `{"asm":None,"hdl":None}` 既定・round-trip テストを壊さない）。
- 既存プロジェクトに sources が無くても読める（import で既定補完）。
- **将来拡張**: 値を文字列 path から dict（`{"path","entry","target","top"}` 等）へ拡張可能。
  読み出しは `_source_path()` が文字列 / dict 両対応で path を取り出すため、移行時に壊れにくい。

```json
{ "sources": { "asm": { "path": "src/hello.asm", "entry": "main", "target": "ak32_cpu" } } }
```

## 3. Canvas / PartNode API

- `set_node_source(node_id, source_type, path) -> bool`（path 空 / None でクリア、node 無しは False）
- `clear_node_source(node_id, source_type) -> bool`
- `node_sources(node_id) -> dict`
- `node_source(node_id, source_type) -> str | None`（dict 形式も path を返す）
- `resolve_program_source(source_type="asm", prefer_node_id=None) -> str | None`（優先順位解決）
- `selected_node_id() -> str | None`
- 既存 `PartNode.sources()` / `set_source()` を土台に使用。`instance_color` / `visual_ports` と独立。

## 4. export / import

- 既存どおり `export_parts` が `"sources": dict(item.sources())` を出力（rom は設定時のみ含む）。
- `import_parts` が復元（sources 無しは既定補完）。round-trip 維持。
- **path 方針**: 可能ならプロジェクトルートからの相対パスで保存（`_rel_to_root`）。
  相対化できない場合は絶対パス（**将来課題**: プロジェクト外参照の扱い・移植性を ROADMAP に残す）。

## 5. Properties（Program / Sources セクション）

- node 選択時のみ表示（wire 選択時は Wire 優先、未選択は従来どおり）。
- 表示: asm / hdl / rom の現在値。
- 操作: Set ASM… / Clear ASM / Open ASM（hdl も同様、rom は表示＋Clear のみ最小）。
- ファイル選択は `QFileDialog`。Open は既存 `_on_open_tab`（割り当て済みは直接開く）に委譲。
- ファイル未設定で Open → ログ "No ASM source assigned"。

## 6. 右クリックメニュー

- 既存「プログラムを開く」（`tab_open_requested` → `_on_open_tab`）は維持（割り当て済み asm を直接開く）。
- design メニューに「Set ASM Source…」を追加（Properties の Set と同じ流れ＝`set_source_requested`）。
- Properties / HDL を開く / 複製 / 削除 / 接続開始 / wire mode 中メニューは不変。

## 7. Build / Run 接続（優先順位）

`_resolve_assigned_asm_path()` が以下の優先順位で asm を解決し、`_build()` が**割り当てを優先**する。
割り当てが無ければ**既存のエディタタブ Build 経路を維持**（後方互換）。

1. 選択中 PartNode の `sources.asm`
2. Canvas 内の CPU カテゴリ part の `sources.asm`
3. Canvas 内で最初に見つかった `sources.asm`
4. 上記が無ければ既存のエディタタブ Build 経路（割り当て不在時のフォールバック）

- 解決した path はプロジェクトルート基準で絶対化し、**存在チェック**。存在しなければログを出し、
  割り当て無し扱い → 既存経路へフォールバック（既存 hello.asm 検証を壊さない）。
- Run は Build が RAM へロードした内容を実行する既存経路（`_do_run`）をそのまま使う。

## 8. path 解決

- プロジェクトルートあり: 相対パスをルート基準で解決。絶対パスはそのまま。
- 存在しなければログ。拡張子チェックは最小（asm: .asm/.s、hdl: .v/.sv/.vhdl/.vh）。
  不一致でも警告程度（強制拒否しない）。

## 9. 今回やらないこと

内蔵エディタ本実装 / 複数ファイル管理 / Build Graph 本実装 / Canvas 配線からの自動解決 /
C コンパイラ / HDL 合成 / FPGA 実機書き込み / ROM イメージ生成 / source watcher /
rename・duplicate / asset 管理 / Port Detail 本実装 / Part Visual サイズ変更 /
`ui/canvas.py` 分割 / Undo・Redo / PHASE COMPLETE / commit / push。

## 10. 後方互換の担保

- PartNode の既定 sources（`{"asm":None,"hdl":None}`）は変更しない（既存 round-trip テスト維持）。
- `_build` は割り当てが無いとき従来どおり（既存 build テスト・hello.asm 検証を壊さない）。
- 既存の Wiring / Properties(Part Visual / Wire Style) / 右クリック / export-import は無改変。

## 11. 将来課題

- 値を dict 形式（entry/target/top）へ拡張。
- Canvas 配線から CPU/ROM/RAM 構成を自動解決し Build Graph を構築。
- 内蔵エディタ・source watcher・ROM イメージ生成・実機書き込み。
- プロジェクト外パス参照の移植性・絶対パス保存の扱い。

## 12. 完了条件

- 上記 2〜8 が実装され `PATCH_PART_PROGRAM_ASSIGN_V05_CHECKLIST.md` が全 `[x]`。
- `pytest tests/` 全件通過（既存 + 新規）。hello.asm headless で UART "Hi" 維持。
