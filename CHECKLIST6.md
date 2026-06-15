# AKDev CHECKLIST 6

> v0.5 UI Polish & Usability の進捗管理チェックリスト。
> 設計詳細は `ROADMAP6.md` を参照。
> UI 仕様は `UI_SPEC_V05.md` を参照。
>
> 個別パッチの進捗は別ファイル:
> `PATCH_WIRING_V05_CHECKLIST.md` / `PATCH_PART_VISUAL_V05_CHECKLIST.md` /
> `PATCH_WIRING_PORTS_V05_CHECKLIST.md` /
> `PATCH_PORT_DRAG_CONNECT_V05_CHECKLIST.md`（Port Drag Connect）/
> `PATCH_WIRE_HOVER_FEEDBACK_V05_CHECKLIST.md`（Hover Feedback）/
> `PATCH_WIRE_SELECT_DELETE_V05_CHECKLIST.md`（Wire Select & Delete）/
> `PATCH_VISUAL_PORT_MOVE_V05_CHECKLIST.md`（Visual Port Move）/
> `PATCH_WIRE_STYLE_V05_CHECKLIST.md`（Wire Style）/
> `PATCH_PART_PROGRAM_ASSIGN_V05_CHECKLIST.md`（Program / Sources 割り当て）/
> `PATCH_CIRCUIT_WRITE_RUN_HELLO_V05_CHECKLIST.md`（Write Program to Circuit）/
> `PATCH_VIRTUAL_CPU_STEP_TRACE_V05_CHECKLIST.md`（Virtual CPU Step & Trace）/
> `PATCH_VIRTUAL_CIRCUIT_RUNTIME_V05_CHECKLIST.md`（Virtual Circuit Runtime）。

---

# 0. 事前確認

* [x] ROADMAP6.md / CHECKLIST6.md が作成されている
  - 完了条件: このファイルと ROADMAP6.md が存在し、v0.5 テーマが明記されている
* [x] pytest 518 件全通過を確認する
  - 完了条件: `pytest tests/` が 518 PASSED で通過する（v0.4.1 完了時点の基準）
  - 2026-06-03 確認済み: 518 件 PASSED（2.47s）
* [x] v0.5 テーマ（UI Polish & Usability）が確定している
  - 完了条件: ROADMAP6.md のテーマ・設計方針・作業一覧が記載されている

---

═══════════════════════════════════════════════════════════
# UI Prototype Patch（v0.5 最初の実装）
═══════════════════════════════════════════════════════════

> 設計根拠: `UI_SPEC_V05.md` セクション 0 / 11-A / 11-B / 11-C。
> 完成版 UI ではなく方向性確認用プロトタイプ。

## P0. 事前確認

* [x] 既存ドキュメント（CLAUDE.md / ROADMAP6.md / CHECKLIST6.md / HANDOFF.md / UI_SPEC_V05.md）を確認した
* [x] 変更予定ファイルと作業範囲をユーザーへ提示した
* [x] 既存テスト（test_ribbon / test_toolbar / test_dock_visibility）の依存を確認した

## P1. UI_SPEC_V05.md 更新

* [x] v0.5 の目的・プロトタイプ方針を追記
* [x] 現在 UI の問題点に Hub 入口欠如・ブランド・Debug 前面の項目を追記
* [x] Hub 画面方針（11-A）を追記
* [x] Visual Identity 方針（11-B）を追記
* [x] Prototype Patch 実装範囲・今回やらないこと（11-C）を追記

## P2. Hub 画面プロトタイプ

* [x] `ui/hub.py` を新規作成（HubWindow）
* [x] AKDev タイトル + サブタイトル表示
* [x] New Project / Open Project ボタン
* [x] Recent Projects 枠（空表示でよい）
* [x] Templates カード枠（実機能は後回し）
* [x] Documentation / Quick Start 導線
* [x] New / Open はシグナルで既存処理へつなぐ
* [x] `main.py` で Hub 先行表示、実行後 Workspace へ遷移

## P3. Workspace 初期表示整理

* [x] 下部タブを Log / Console 前面化（Memory ではなく）
* [x] 右側パネルを Properties 前面化（Register View ではなく）
* [x] Canvas の表示領域をできるだけ広く（splitter 比率）
* [x] Register / Memory / Bus Trace / UART は削除せず残す

## P4. Ribbon 再構成

* [x] Project タブ（New / Open / Save / Save As）
* [x] Parts タブ（Add Part / Clone / Delete / Properties）
* [x] Wiring タブ（Wire Mode / Cancel Wire）
* [x] Run タブ（Build / Run / Step / Reset / Pause）
* [x] View タブ（Grid / Snap / Zoom / Fit / パネルトグル）
* [x] Debug タブ（Register / Memory / Bus Trace / UART / Log）
* [x] 実装できない操作は disabled / TODO 扱い
* [x] `tests/test_ribbon.py` を新構成へ更新

## P5. Debug パネル表示整理

* [x] デバッグパネルのトグルを Debug タブへ集約
* [x] 既存パネル機能を壊さない（hide ではなく前面化で初期表示を整理）

## P6. Visual Identity 土台

* [x] `ui/theme.py` を新規作成（ACCENT + QSS）
* [x] アクセントカラーを 1 色決めて適用
* [x] ボタン枠線を弱める
* [x] hover / selected / active 状態を表現
* [x] アプリ名 AKDev を Hub / Workspace で表示
* [x] 外部ライブラリ・素材は追加していない

## P7. テスト

* [x] `pytest tests/` 全通過
* [x] Hub 生成テスト（tests/test_hub.py）追加
* [x] theme テスト（tests/test_theme.py）追加
* [x] Ribbon テスト更新

## P8. 手動確認

* [x] hello.asm headless 検証（UART "Hi"）
* [ ] GUI 起動の目視確認（ヘッドレス環境のため未実施 — 理由を報告に記載）

## P9. 実装後レビュー

* [x] 変更ドキュメントを読み返す（見出し・リンク・矛盾）
* [x] HANDOFF.md 更新
* [x] 作業報告（変更ファイル・テスト結果・未確認事項）

═══════════════════════════════════════════════════════════

# 1. UI_SPEC_V05.md 作成

* [x] `UI_SPEC_V05.md` を新規作成する
  - 完了条件: ファイルが存在し、以下のセクションが含まれている
    - 現在の UI の問題点
    - v0.5 UI 設計方針
    - 初期表示パネル一覧
    - 非表示・表示切替パネル一覧
    - リボンタブ構成（案）
    - マウス操作割り当て（案）
    - ショートカット方針（案）
    - Canvas 表示方針
    - Debug パネル整理方針
    - ユーザー UI ラフ反映欄

---

# 2. 現在 UI の問題点整理

* [x] 現在の UI で迷いやすい操作・探しにくい機能を列挙する
  - 完了条件: `UI_SPEC_V05.md` の「現在の問題点」セクションに 5 件以上記載されている
* [x] リボンに機能が集中しすぎている箇所を特定する
  - 完了条件: 現行リボンタブの問題点が `UI_SPEC_V05.md` に記載されている
* [x] 常時表示しなくてよいパネルを特定する
  - 完了条件: 非表示候補パネルが `UI_SPEC_V05.md` に列挙されている

---

# 3. 初期表示パネルの整理

* [x] 起動時に常時表示するパネルを確定する
  - 完了条件: 初期表示パネル 5 件（Ribbon / Parts Library / Canvas / Properties / Log）が `UI_SPEC_V05.md` に記載されている
  - 完了条件: 各パネルの表示理由が明記されている

---

# 4. パネル表示/非表示ルール整理

* [x] 非表示・表示切替できるパネルを列挙する
  - 完了条件: Register View / Memory Viewer / Bus Trace / UART Console / Port Detail / Signal Overlay 設定が列挙されている
* [x] 各パネルを「いつ表示するか」のルールを決める
  - 完了条件: 表示タイミングの目安が各パネルに記載されている
* [ ] 現行の View Ribbon トグルをリボン整理と合わせて見直す方針を記載する
  - 完了条件: 現行トグルの移設先（Debug タブ等）の方針が `UI_SPEC_V05.md` に記載されている

---

# 5. リボンタブ構成整理

* [x] 新しいリボンタブ構成（案）を作成する
  - 完了条件: Project / Parts / Wiring / Run / View / Debug の 6 タブ構成案が `UI_SPEC_V05.md` に記載されている
* [x] 各タブに入れるボタン・機能を割り当てる（案）
  - 完了条件: 各タブの主要ボタン一覧が記載されている
* [ ] 現行リボンから新構成への移行差分を整理する
  - 完了条件: 「現行 → 移設先」の対応表が `UI_SPEC_V05.md` に記載されている
* [ ] ユーザーが UI ラフで最終確認する
  - 完了条件: UI ラフとの差分がない、またはユーザーが承認している

---

# 6. マウス操作・ショートカット整理

* [x] Canvas でのマウス操作割り当てを確定する（案）
  - 完了条件: 左クリック / 右クリック / 中ボタン / ホイールの役割が `UI_SPEC_V05.md` に記載されている
* [x] よく使う操作のショートカット一覧（案）を作成する
  - 完了条件: Build / Run / Step / Reset / Save / Zoom / Wire Mode などの推奨ショートカットが記載されている
* [ ] ユーザーが UI ラフで最終確認する
  - 完了条件: ユーザーがショートカット方針を承認している

---

# 7. Debug パネルの役割整理

* [x] Register View / Memory Viewer / Bus Trace / UART Console の役割・表示タイミングを整理する
  - 完了条件: 各パネルの役割・表示トリガーが `UI_SPEC_V05.md` に記載されている
* [x] Debug タブを新設して Debug パネルのトグルをまとめる方針を確定する
  - 完了条件: Debug タブへの集約方針が `UI_SPEC_V05.md` に記載されている
* [ ] 実装時の変更範囲（ui/win.py への影響）を概算する
  - 完了条件: 影響ファイルと変更量の見積もりが記載されている

---

# 8. Canvas 視認性改善方針整理

* [x] Canvas 上で視認性を妨げている問題を列挙する
  - 完了条件: 問題点（ノード色・接続線の見分けにくさ等）が `UI_SPEC_V05.md` に記載されている
* [x] 改善方針（案）を記載する
  - 完了条件: ノード色・接続線色・文字サイズ・グリッドの改善方針が記載されている
* [ ] ユーザーが UI ラフで最終確認する
  - 完了条件: ユーザーが Canvas 視認性の方針を承認している

---

# 9. Port Detail 方針整理

* [x] Port Detail の表示方法（ダブルクリック / コンテキストメニュー）を確定する
  - 完了条件: 表示トリガーと表示内容の方針が `UI_SPEC_V05.md` に記載されている
  - 参照: `old/ROADMAP5.md` セクション 7-3 の Port Detail 方針
* [ ] 実装優先度を決める（v0.5 で実装するか、v0.6 以降か）
  - 完了条件: 優先度が `UI_SPEC_V05.md` に記載されている

---

# 10. 配線表示方針整理

* [x] 接続線の kind 別表示（色・太さ）の現状と方針を整理する
  - 完了条件: bus / signal / clock / reset の表示方針が `UI_SPEC_V05.md` に記載されている
* [x] 配線色変更 UI の方針（右クリックメニュー / Properties パネル）を決める
  - 完了条件: 配線色変更の操作フローが `UI_SPEC_V05.md` に記載されている
* [ ] 実装優先度を決める（v0.5 で実装するか、v0.6 以降か）
  - 完了条件: 優先度が `UI_SPEC_V05.md` に記載されている

---

# 11. ユーザーの UI ラフ反映

* [ ] ユーザーが UI ラフ画像を作成する（ユーザー担当）
  - 完了条件: UI ラフが `UI_SPEC_V05.md` の「UI ラフ反映欄」に添付または記録されている
* [ ] UI ラフとの差分を確認する
  - 完了条件: ラフとの差分がない、または差分がある場合は理由が記載されている
* [ ] ラフをもとに `UI_SPEC_V05.md` を更新する
  - 完了条件: 最終的な UI 方針がラフと一致している

---

# 12. 実装範囲の確定

* [ ] UI ラフとユーザー確認をもとに、v0.5 で実装する項目を確定する
  - 完了条件: 実装する項目と実装しない項目が `UI_SPEC_V05.md` に記載されている
* [ ] 実装対象ファイル一覧を作成する
  - 完了条件: `ui/win.py` / `ui/canvas.py` 等の変更予定ファイルが記載されている
* [ ] 実装量の見積もりを確認する
  - 完了条件: 実装量が大きすぎる場合は分割方針を記載する

---

# 13. 実装前レビュー

* [ ] `UI_SPEC_V05.md` の内容を通読し、矛盾がないか確認する
  - 完了条件: 矛盾がない、または矛盾があれば解消済み
* [ ] ユーザーが実装開始を承認する
  - 完了条件: ユーザーから実装開始の明示的な指示がある

---

# 14. 実装（実装前レビュー完了後に開始）

* [ ] 実装チェック項目を追加する（実装前レビュー完了後に追記）

---

# v0.5 完了条件

* [ ] `UI_SPEC_V05.md` が作成されている
* [ ] 初期表示と表示切替対象が整理されている
* [ ] リボンタブ構成が決まっている
* [ ] よく使う操作の配置方針が決まっている
* [ ] マウス操作・ショートカット方針が決まっている
* [ ] Debug パネルの役割が整理されている
* [ ] Canvas 視認性改善方針が決まっている
* [ ] ユーザー作成の UI ラフが反映されている
* [ ] 実装範囲が明確になっている
* [ ] 実装前にユーザー確認を挟む
* [ ] CHECKLIST6.md の実装項目が全て `[x]` になっている
* [ ] pytest が全件通過している
* [ ] HANDOFF.md が次フェーズを指している
