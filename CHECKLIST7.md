# AKDev CHECKLIST 7

> v0.7 (Plan-driven Virtual Devices & Address Map) の進捗管理チェックリスト。
> 設計詳細は `ROADMAP7.md` を参照。
> v0.6 の進捗は `CHECKLIST6.md`（終了扱い・削除せず保管）を参照。
>
> 個別パッチの進捗は実装時に別ファイルで管理する:
> `PATCH_PLAN_DRIVEN_DEVICES_V07_CHECKLIST.md` /
> `PATCH_ADDRESS_MAP_V07_CHECKLIST.md` /
> `PATCH_CPU_RAM_VALIDATION_V07_CHECKLIST.md` /
> `PATCH_TARGET_CPU_SELECTION_V07_CHECKLIST.md` /
> `PATCH_RUN_STATUS_PANEL_V07_CHECKLIST.md` /
> `PATCH_PORT_DETAIL_V07_CHECKLIST.md`。

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
* [ ] 最初のパッチ `PATCH_PLAN_DRIVEN_DEVICES_V07` の実装範囲をユーザーが承認する
  - 完了条件: ユーザーから実装開始の明示的な指示がある
* [ ] `PATCH_PLAN_DRIVEN_DEVICES_V07_ROADMAP.md` / `..._CHECKLIST.md` を作業前に作成する
  - 完了条件: 実装着手前に 2 ファイルが存在し、作業範囲・今回やらないことが明記されている

---

# 2. Plan-driven Devices（PATCH_PLAN_DRIVEN_DEVICES_V07）

* [ ] `resolve_circuit()` の plan に RAM/UART の base/size 情報を持たせる
  - 完了条件: plan から各デバイスの base/size が取得できる
* [ ] `_make_sim(plan)` を plan 駆動にする
  - 完了条件: plan の RAM/UART ノードから実デバイスを構築し、runtime に束ねる
* [ ] circuit mode の RAM サイズを拡張する
  - 完了条件: 256B 固定をやめ、拡張サイズ（要・上限決定）で生成される
* [ ] Write Program が plan に紐づく接続 RAM へロードする
  - 完了条件: 接続 RAM のメモリにプログラムがロードされる
* [ ] Run/Step が plan に紐づくデバイスで実行する
  - 完了条件: 実行 RAM/UART が plan のデバイスである
* [ ] legacy mode（CPU 未配置）が従来の固定 runtime を維持する
  - 完了条件: 既存の非 Canvas / エディタタブ Build/Run が不変
* [ ] テストを追加する（plan RAM=実行 RAM / RAM 拡張ロード / Write→Run Hello / legacy 不変）
* [ ] `pytest tests/` 全通過
* [ ] GUI 目視確認項目を `HANDOFF.md` に記載する

---

# 3. Address Map（PATCH_ADDRESS_MAP_V07）

* [ ] plan / runtime にデバイス単位の base/size を保持する
  - 完了条件: RAM/UART それぞれの base/size が管理される
* [ ] overlap 検出を Address Map レベルで行う
  - 完了条件: 重複アドレスが検出・通知される
* [ ] Address Map を UI で表示する
  - 完了条件: Properties または Debug パネルでアドレス割当が見える
* [ ] 既定マップ（RAM 0x0000 / UART 0x0100 等）の互換を維持する
* [ ] テストを追加する（overlap 検出 / base・size 保持 / 表示）
* [ ] `pytest tests/` 全通過

---

# 4. CPU/RAM Validation（PATCH_CPU_RAM_VALIDATION_V07）

* [ ] RAM read/write selftest を用意する
  - 完了条件: 書いて読み戻す最小プログラムが Canvas 由来 runtime 上で成功する
* [ ] Fibonacci を Canvas 由来 runtime 上で実行・検証する
  - 完了条件: 期待するフィボナッチ数列が RAM/出力で確認できる
* [ ] LD/ST/ADD/分岐の到達性を検証する
  - 完了条件: 主要命令が接続 RAM 上で正しく動作する
* [ ] テストを追加する（selftest / Fibonacci 期待値 / 命令到達性）
* [ ] `pytest tests/` 全通過

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

* [ ] Port Detail の表示トリガーを実装する（ダブルクリック / コンテキストメニュー）
* [ ] 論理ポート（part.json `ports`）を表示する
* [ ] visual port を表示する
* [ ] direction を表示する
* [ ] width を表示する
* [ ] connection 情報を表示する
* [ ] 選択切替で内容が更新される
* [ ] テストを追加する（ポート情報表示 / 選択切替更新）
* [ ] `pytest tests/` 全通過

---

# 8. v0.7 完了条件

* [ ] CircuitPlan から RAM/UART の実デバイスが生成され、runtime がそれで実行する
* [ ] circuit mode の RAM サイズが拡張されている
* [ ] RAM/UART の base/size が管理され、overlap が検出できる
* [ ] Address Map が UI で確認できる
* [ ] CPU が接続 RAM に対して LD/ST できることが検証されている（selftest / Fibonacci）
* [ ] 複数 CPU 時に実行対象 CPU を選択できる
* [ ] Run/Step 時の状態が UI で見える
* [ ] Port Detail で論理/visual ポート・direction・width・connection が確認できる
* [ ] legacy mode（CPU 未配置）が従来どおり動作する
* [ ] `pytest tests/` が全件通過している
* [ ] CHECKLIST7.md の全項目が `[x]` になっている
* [ ] HANDOFF.md が v0.7 の状況・次フェーズを指している
* [ ] 各 PATCH の ROADMAP/CHECKLIST が作業前に作成され、実装後に内容が読み返されている
