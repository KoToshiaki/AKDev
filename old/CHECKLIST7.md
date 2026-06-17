# AKDev CHECKLIST 7

> v0.7 (Plan-driven Virtual Devices & Address Map) の進捗管理チェックリスト。
> 設計詳細は `ROADMAP7.md` を参照。
> v0.6 の進捗は `CHECKLIST6.md`（終了扱い・削除せず保管）を参照。
>
> 個別パッチ CHECKLIST（`PATCH_*_V07_CHECKLIST.md` × 6）は v0.7 PHASE COMPLETE 時に
> `old/` へ収納済み（削除せず保管）。このファイルは履歴として root に残す。

---

# ✅ v0.7 PHASE COMPLETE — 2026-06-17

**v0.7 は完了扱い。** このファイルは履歴として残す（削除しない）。

- **最終テスト**: `python -m pytest tests/` → **860 passed**, 21 warnings（PySide6 Deprecation のみ）
- **テーマ**: Plan-driven Virtual Devices & Address Map
- **主要達成項目**:
  - CircuitPlan から実 RAM/UART/CPU を生成（circuit mode 64KB RAM / UART MMIO 窓 0x0100–0x0107）
  - Address Map（base/size/end・attach ranges・overlap 検出・summary 表示）
  - CPU↔RAM の ST/LD 検証（`ram_selftest.asm` PASS / Fibonacci）
  - 複数 CPU 時の target CPU 選択（選択 CPU のみ実行・asm 限定・ambiguous ブロック）
  - Run Status Panel（実行状態の集約表示）
  - Port Detail Panel（logical/visual ポート・direction/width・connection 表示）
- **未達・保留項目**:
  - §0 `tests/test/system.json` 差分の扱い（破棄/コミット/.gitignore）はユーザー判断保留（v0.6 繰越）
- **v0.8 以降へ送る課題**: `ROADMAP8.md` / `CHECKLIST8.md` を参照
  （Port direction/width 検証・Bus protocol 検証・複数 RAM/UART・ROM/VRAM/Storage/Input・
  Address Map Editor・コード領域拡張・MMIO 再配置・命令拡張・ゲーム runtime・HDL/FPGA export）。
- **収納**: 完了済み `PATCH_*_V07_ROADMAP.md` / `..._CHECKLIST.md`（12 ファイル）を `old/` へ収納。
  `ROADMAP7.md` / `CHECKLIST7.md` は root に残す。

---

# 0. v0.6 終了確認

* [x] `pytest tests/` が全件通過することを確認した
  - 2026-06-16 確認: **779 passed**（5.83s）
* [x] v0.6 の到達点を `ROADMAP6.md` / `HANDOFF.md` に整理した
  - Virtual CPU Step & Trace / Virtual Circuit Runtime（最小）/ 未接続ブロック / Hello World
* [x] v0.6 を終了扱いにし、`ROADMAP6.md` / `CHECKLIST6.md` に終了マークを付けた（内容は削除しない）
* [x] v0.6 で残った課題を v0.7 へ引き継ぐ項目として整理した
  - 実デバイス生成・RAM 拡張・Address Map・複数デバイス・Canvas 上の validation
* [ ] `tests/test/system.json` のテスト実行差分の扱いをユーザーが決定する
  - 完了条件: 差分を破棄 / コミット / .gitignore 化 のいずれかをユーザーが選ぶ（勝手に破棄しない）

---

# 1. v0.7 開始準備

* [x] `ROADMAP7.md` を作成した
* [x] `CHECKLIST7.md` を作成した
* [x] v0.7 テーマ（Plan-driven Virtual Devices & Address Map）を確定した
* [x] v0.7 作業候補を優先順位付きで整理した
* [x] 最初のパッチ `PATCH_PLAN_DRIVEN_DEVICES_V07` の実装範囲をユーザーが承認する
  - 完了条件: ユーザーから実装開始の明示的な指示がある（承認済み・実装完了）
* [x] `PATCH_PLAN_DRIVEN_DEVICES_V07_ROADMAP.md` / `..._CHECKLIST.md` を作業前に作成する
  - 完了条件: 実装着手前に 2 ファイルが存在し、作業範囲・今回やらないことが明記されている
  - v0.7 PHASE COMPLETE 時に `old/` へ収納済み

---

# 2. Plan-driven Devices（PATCH_PLAN_DRIVEN_DEVICES_V07）

* [x] `resolve_circuit()` の plan に RAM/UART の base/size 情報を持たせる
  - 完了条件: plan から各デバイスの base/size が取得できる
* [x] `_make_sim(plan)` を plan 駆動にする
  - 完了条件: plan の RAM/UART ノードから実デバイスを構築し、runtime に束ねる
* [x] circuit mode の RAM サイズを拡張する
  - 完了条件: 256B 固定をやめ、拡張サイズで生成される（`_CIRCUIT_RAM_SIZE = 0x10000` = 64KB）
* [x] Write Program が plan に紐づく接続 RAM へロードする
  - 完了条件: 接続 RAM のメモリにプログラムがロードされる
* [x] Run/Step が plan に紐づくデバイスで実行する
  - 完了条件: 実行 RAM/UART が plan のデバイスである
* [x] legacy mode（CPU 未配置）が従来の固定 runtime を維持する
  - 完了条件: 既存の非 Canvas / エディタタブ Build/Run が不変
* [x] テストを追加する（plan RAM=実行 RAM / RAM 拡張ロード / Write→Run Hello / legacy 不変）
  - `tests/test_plan_driven_devices_v07.py`
* [x] `pytest tests/` 全通過
* [x] GUI 目視確認項目を `HANDOFF.md` に記載する

---

# 3. Address Map（PATCH_ADDRESS_MAP_V07）

* [x] plan / runtime にデバイス単位の base/size を保持する
  - 完了条件: RAM/UART それぞれの base/size が管理される（`build_address_map` / `runtime.address_map`）
* [x] overlap 検出を Address Map レベルで行う
  - 完了条件: 重複アドレスが検出・通知される（`validate_address_map`、MMIO 窓は除外）
* [x] Address Map を UI で表示する
  - 完了条件: Debug パネルでアドレス割当が見える（Log + Run Status Panel）
* [x] 既定マップ（RAM 0x0000 / UART 0x0100 等）の互換を維持する
* [x] テストを追加する（overlap 検出 / base・size 保持 / 表示）
  - `tests/test_address_map_v07.py`
* [x] `pytest tests/` 全通過

---

# 4. CPU/RAM Validation（PATCH_CPU_RAM_VALIDATION_V07）

* [x] RAM read/write selftest を用意する
  - 完了条件: 書いて読み戻す最小プログラムが Canvas 由来 runtime 上で成功する（`ram_selftest.asm` → UART `PASS`）
* [x] Fibonacci を Canvas 由来 runtime 上で実行・検証する
  - 完了条件: 期待するフィボナッチ数列が RAM/出力で確認できる（RAM 0x0040–0x005C = 0,1,1,2,3,5,8,13）
* [x] LD/ST/ADD/分岐の到達性を検証する
  - 完了条件: 主要命令が接続 RAM 上で正しく動作する（selftest の ST/LD/BEQ + Fibonacci）
* [x] テストを追加する（selftest / Fibonacci 期待値 / 命令到達性）
  - `tests/test_cpu_ram_validation_v07.py`
* [x] `pytest tests/` 全通過

---

# 5. Target CPU Selection（PATCH_TARGET_CPU_SELECTION_V07）

* [x] `resolve_circuit()` の「cpus[0] 固定」を選択 CPU 優先へ変更する
  - 完了条件: 選択中 CPU が実行対象になる
  - `resolve_circuit(..., target_cpu_id=)` + `target_cpu` キー。単一 CPU は選択非依存
* [x] 未選択時のデフォルト挙動を整理する
  - 完了条件: 選択がない場合の挙動が定義・テストされている
  - 複数 CPU + 未選択 = ambiguous（`multiple CPU parts (N). Select one CPU to run.`）でブロック
* [x] 「multiple CPU は issue」既存テストとの整合を更新する
  - 既存テストは `"multiple CPU"` 部分一致のみで不変、新規 18 件で挙動を網羅
* [x] テストを追加する（複数 CPU で選択 CPU 実行 / 未選択時挙動）
  - `tests/test_target_cpu_selection_v07.py`（18 件）
* [x] `pytest tests/` 全通過
  - 2026-06-17 確認: **829 passed**（7.62s）

---

# 6. Run Status Panel（PATCH_RUN_STATUS_PANEL_V07）

* [x] Run Status パネルを新設する（Debug タブに集約）
  - `ui/run_status.py` `RunStatusPanel`、右側 Dock（Register View とタブ化）、Debug リボン登録
* [x] 実行対象 CPU を表示する（mode / target CPU）
* [x] 接続 RAM / UART を表示する
* [x] loaded program を表示する（loaded / path / target / source type / status / size）
* [x] PC / cycle / halted を表示する（+ step count）
* [x] trace summary を表示する（mem / io / register changes / last instruction / PC before→after）
* [x] UART output を表示する（summary）
* [x] Run/Step 後にパネルが更新される（+ Write / Build / Reset / 起動時）
* [x] テストを追加する（パネル生成 / 状態反映 / 更新）
  - `tests/test_run_status_panel_v07.py`（13 件）
* [x] `pytest tests/` 全通過
  - 2026-06-17 確認: **842 passed**（8.22s）

---

# 7. Port Detail（PATCH_PORT_DETAIL_V07）

* [x] Port Detail の表示トリガーを実装する（選択変更 / wire 選択 / 接続変更で更新・Debug リボンでトグル）
  - ダブルクリック/コンテキストメニュー起動ではなく、選択連動の read-only パネルとして実装
* [x] 論理ポート（part.json `ports`）を表示する（name / type / direction / width）
* [x] visual port を表示する（id / label / side / offset / kind / locked / connected）
* [x] direction を表示する（type から推定: master/slave/in/bidir）
* [x] width を表示する（part.json 未定義なら `-`）
* [x] connection 情報を表示する（conn id / from-to / peer node / peer part / direction / kind / width / style）
* [x] 選択切替で内容が更新される（+ wire 選択 / 接続作成・削除後）
* [x] テストを追加する（ポート情報表示 / 選択切替更新）
  - `tests/test_port_detail_v07.py`（18 件）
* [x] `pytest tests/` 全通過
  - 2026-06-17 確認: **860 passed**（8.85s）

---

# 8. v0.7 完了条件

* [x] CircuitPlan から RAM/UART の実デバイスが生成され、runtime がそれで実行する
* [x] circuit mode の RAM サイズが拡張されている（64KB）
* [x] RAM/UART の base/size が管理され、overlap が検出できる
* [x] Address Map が UI で確認できる（Log + Run Status Panel）
* [x] CPU が接続 RAM に対して LD/ST できることが検証されている（selftest / Fibonacci）
* [x] 複数 CPU 時に実行対象 CPU を選択できる
* [x] Run/Step 時の状態が UI で見える（Run Status Panel）
* [x] Port Detail で論理/visual ポート・direction・width・connection が確認できる
* [x] legacy mode（CPU 未配置）が従来どおり動作する
* [x] `pytest tests/` が全件通過している（**860 passed** / 2026-06-17）
* [x] CHECKLIST7.md の全機能項目が `[x]` になっている
  - 例外: §0 の `tests/test/system.json` 差分の扱いはユーザー判断保留（機能項目ではない・v0.6 からの繰越）
* [x] HANDOFF.md が v0.7 の状況・次フェーズを指している
* [x] 各 PATCH の ROADMAP/CHECKLIST が作業前に作成され、実装後に内容が読み返されている
  - v0.7 PHASE COMPLETE 時に `PATCH_*_V07_*` 12 ファイルを `old/` へ収納済み
