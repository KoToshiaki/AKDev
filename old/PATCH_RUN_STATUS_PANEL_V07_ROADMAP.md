# PATCH_RUN_STATUS_PANEL_V07 — ROADMAP

> v0.7（Plan-driven Virtual Devices & Address Map）5 番目のパッチ。
> 親計画: `ROADMAP7.md` / 進捗: `PATCH_RUN_STATUS_PANEL_V07_CHECKLIST.md`。
> 前提: `PATCH_PLAN_DRIVEN_DEVICES_V07` / `PATCH_ADDRESS_MAP_V07` /
> `PATCH_CPU_RAM_VALIDATION_V07` / `PATCH_TARGET_CPU_SELECTION_V07` 完了
> （`pytest tests/` 829 passed）。

---

## 目的

Run / Step / Write Program / Build / Reset 後の実行状態を、1 つの **Run Status Panel**
にまとめて確認できるようにする。target CPU・接続 RAM/UART・Address Map・loaded program・
PC/cycle/halted・last trace・UART 出力など、現状 Log や個別パネルに分散している情報を
集約して概要表示する。

## 現在の問題

- 実行状態（target CPU / 接続デバイス / loaded program / PC / trace / UART）が
  Log・Register View・Memory・Bus Trace・UART Console に分散し、一目で把握しにくい。
- 複数 CPU 時の target CPU や ambiguous 状態が Log を遡らないと分からない。
- legacy / circuit のどちらで動いているかが UI で即座に分からない。

## 実装方針

- **新規状態は増やさない**。既存の `self._runtime` / `self._sim_*` / `_resolve_circuit_plan()` /
  `address_map()` / `_loaded_program` を読み取って表示するだけの read-only パネルにする。
- `ui/run_status.py` に `RunStatusPanel(QDockWidget)` を新規作成（monospace QPlainTextEdit）。
  - `update_status(status: dict)` で受け取った dict を整形して表示。
  - `status_text()` で現在の表示文字列を返す（テスト用）。
- `MainWin` 側:
  - `_setup_run_status()` でパネルを生成し右側 Dock（Register View とタブ化）へ追加。
  - `_collect_run_status()` で既存状態から status dict を構築。
  - `_update_run_status()` で `_collect_run_status()` → `panel.update_status()`。
  - Debug リボンに `toggleViewAction()` を追加。
- 既存 Log 出力（Target CPU / Circuit built / Address Map / Step Trace / Run finished）は維持。

## Run Status Panel に表示する項目

### Target / Circuit
- mode（`legacy` / `circuit`）
- target CPU node id（複数 CPU でも現在の target が分かる）
- connected RAM node id / connected UART node id
- issues（ambiguous / 未接続などがあれば簡易表示）

### Program
- loaded 状態（Yes/No）
- loaded program path
- loaded target node id
- source type / status / size

### Runtime
- PC / cycle / halted / step count
- last instruction / last PC before → after

### Address Map
- RAM range / UART range（`format_address_map_summary` の各行）
- overlap などの issue（`validate_address_map`）

### UART
- UART output summary（直近出力。全文でなくてよい。例 `Hello World !` / `PASS` / `Hi`）

### Trace Summary
- last trace の memory read/write / io write / register changes（簡易）

## 更新タイミング

- 起動時（初期表示）
- Write Program 後
- Build 後
- Run 後（pause 含む）
- Step 後
- Reset 後

（`_refresh_run_panels` 経由で Run/Step、`_assemble_and_load` 経由で Build/Write、
`_do_reset` / `write_program` 末尾でも明示更新。selection / 接続変化時の自動更新は次段。）

## circuit mode / legacy mode の扱い

### circuit mode（Canvas に CPU あり）
- Target CPU / connected RAM / connected UART / Address Map / loaded program / runtime 状態。

### legacy mode（Canvas に CPU なし）
- mode: legacy / target CPU: None
- RAM: sim_ram（256B）/ UART: sim_uart（0x0100）
- loaded program / PC / cycle / halted / UART output
- パネルが壊れないこと（plan 解決が legacy でも例外を出さない）。

## テスト方針（`tests/test_run_status_panel_v07.py` 新規）

- パネル生成: MainWin 作成時に存在・初期表示でクラッシュしない・legacy でも表示可。
- Write Program 後: target CPU / connected RAM,UART / loaded path / Address Map が出る。
- Run 後: PC/cycle/halted 更新・UART summary（`Hello World !` / `PASS`）が出る。
- Step 後: last instruction / PC before→after / register changes か trace summary が出る。
- Reset 後: PC/cycle/step count が初期へ戻る・UART の扱いが既存仕様と矛盾しない。
- Target CPU Selection 連携: 複数 CPU で選択 CPU が target 表示・ambiguous / 未接続でも壊れない。
- 既存互換: Plan-driven / Address Map / CPU RAM Validation / Target CPU Selection /
  Step Trace / Program-Sources / legacy Build→Run が壊れない。

## 今回やらないこと

高度なデバッガ / ブレークポイント本格実装 / source-level debug / Trace タイムライン /
Address Map Editor / Port Detail 本体 / Port direction・width 検証 /
複数 CPU 同時実行 / マルチコア / VRAM・Storage・Input・Display 本実装 /
MMU / 割り込み / C コンパイラ / HDL 合成 / FPGA 実機書き込み / ゲーム実行 / commit / push。

## 既存互換性の注意点

- 既存パネル（Register View / Memory / Bus Trace / UART Console / Log / Properties /
  Canvas Signal Overlay）を置き換えず、概要パネルとして追加するだけ。
- 既存 Log 出力は維持する。
- パネルは read-only。runtime / win の実行ロジックは変更しない（更新フックの追加のみ）。
- `_collect_run_status()` は legacy / ambiguous / 未接続 / 未ロードでも例外を出さない。
