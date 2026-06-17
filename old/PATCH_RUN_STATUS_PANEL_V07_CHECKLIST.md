# PATCH_RUN_STATUS_PANEL_V07 — CHECKLIST

> 設計詳細は `PATCH_RUN_STATUS_PANEL_V07_ROADMAP.md` を参照。
> 親計画: `ROADMAP7.md` / `CHECKLIST7.md`（6. Run Status Panel）。

---

## 実装項目

* [x] `ui/run_status.py` `RunStatusPanel(QDockWidget)` を新規作成
  - [x] monospace QPlainTextEdit（read-only）
  - [x] `update_status(status: dict)` で整形表示
  - [x] `status_text()` で現在表示文字列を返す
  - [x] None / 欠損キーでも例外を出さない（`render_status` 単体テストで確認）
* [x] `ui/win.py` `_setup_run_status()` を追加（右側 Dock・Register View とタブ化）
* [x] Debug リボンに `run_status.toggleViewAction()` を追加
* [x] `ui/win.py` `_collect_run_status()`（既存状態から status dict 構築）
* [x] `ui/win.py` `_update_run_status()`（collect → panel.update_status）
* [x] 更新フック: 起動時 / Write / Build / Run / Step / Reset
* [x] 既存 Log 出力（Target CPU / Circuit built / Address Map / Step Trace / Run finished）維持
* [x] 既存パネル（Register/Memory/Bus Trace/UART/Log/Properties/Signal Overlay）を壊さない

## 表示項目

* [x] mode（legacy / circuit）
* [x] target CPU / connected RAM / connected UART
* [x] loaded program（loaded / path / target / source type / status / size）
* [x] PC / cycle / halted / step count
* [x] last instruction / PC before→after
* [x] Address Map summary（RAM/UART range）+ issue
* [x] UART output summary
* [x] trace summary（mem / io / register changes）

## テスト項目（`tests/test_run_status_panel_v07.py` — 13 件）

### パネル生成
* [x] MainWin 作成時に Run Status Panel が存在
* [x] 初期状態でクラッシュしない
* [x] legacy mode でも表示できる

### Write Program 後
* [x] target CPU が表示される
* [x] connected RAM / UART が表示される
* [x] loaded program path が表示される
* [x] Address Map が表示される

### Run 後
* [x] PC / cycle / halted が更新される
* [x] UART output summary（`Hello World !` / `PASS`）が表示される

### Step 後
* [x] last instruction が表示される
* [x] PC before / after が表示される
* [x] register changes または trace summary が表示される

### Reset 後
* [x] PC / cycle / step count が初期状態へ戻る
* [x] UART output の扱いが既存仕様と矛盾しない（reset で空 → `(none)`）

### Target CPU Selection 連携
* [x] 複数 CPU で選択 CPU が target 表示
* [x] CPU 未選択 ambiguous でも壊れない
* [x] target CPU 未接続でも壊れない

### 既存互換
* [x] Plan-driven / Address Map / CPU RAM Validation / Target CPU Selection テストが壊れない
* [x] legacy mode Build→Run（"Hi"）が従来通り
* [x] Step Trace / Program-Sources が壊れない

## 検証項目

* [x] `python -m pytest tests/` 全件通過（**842 passed**）
* [x] commit / push を行っていない
* [x] 作業後にドキュメントを読み返した
