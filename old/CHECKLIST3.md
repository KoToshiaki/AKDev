# AKDev CHECKLIST 3

> v0.2 用チェックリスト。v0.1 の完了を前提に、UI/UX 改善の作業を管理する。
> 詳細な旧チェックリストは `old/CHECKLIST2.md` を参照。

---

# 0. v0.1 完了状態（基盤）

* [x] GUI 骨組み（QMainWindow / メニュー / ツールバー / Dock）
* [x] Parts Library（`parts/` スキャン・カテゴリ表示・11 パーツ定義）
* [x] System Canvas（配置・移動・選択・削除・右クリックメニュー）
* [x] node_id インスタンス管理（`node_0001` 形式）
* [x] Properties パネル（名前・ID・カテゴリ・説明・ポート・resources 表示）
* [x] タブエディタ（`.asm` / `.v`、dirty マーク、`build/edit/` 仮保存・再読み込み）
* [x] シンタックスハイライト（.asm / .v）
* [x] プロジェクト保存／読み込み（`project.json` / `system.json`）
* [x] アセンブラ（`asm/asm.py` — NOP/HALT/LDI/OUT、ラベル 1-pass）
* [x] Build パイプライン（F5 → アセンブル → RAM ロード）
* [x] シミュレータ基盤（`core/sim.py` — tracing 付き Bus）
* [x] AK32Part（NOP/HALT/LDI/OUT、r0 固定ゼロ — `core/cpu.py`）
* [x] Run / Step / Reset（Ctrl+R / F10 / Ctrl+Shift+R）
* [x] UART Console（QDockWidget 下部タブ、UartPart 出力を表示）
* [x] Register View（QTableWidget 右側タブ、pc / cycle / halted / r0〜r15）
* [x] Bus Trace（QDockWidget 下部タブ、READ/WRITE ログ）
* [x] サンプル `src/hello.asm`（UART に "Hi" 出力）
* [x] 統合テスト `tests/test_v01_flow.py`（9 件通過）

---

# 1. View メニュー改善

**目標**: 閉じた Dock を View メニューから再表示できるようにする。

## 1.1 View メニューにトグルアクションを追加する

* [x] `View > Parts Library` トグル
  - 完了条件: チェック ON で Dock が表示され、チェック OFF で非表示になる
* [x] `View > Properties` トグル
  - 完了条件: チェック ON で Dock が表示され、チェック OFF で非表示になる
* [x] `View > Register View` トグル
  - 完了条件: チェック ON で Dock が表示され、チェック OFF で非表示になる
* [x] `View > Log / Console` トグル
  - 完了条件: チェック ON で Dock が表示され、チェック OFF で非表示になる
* [x] `View > UART Console` トグル
  - 完了条件: チェック ON で Dock が表示され、チェック OFF で非表示になる
* [x] `View > Bus Trace` トグル
  - 完了条件: チェック ON で Dock が表示され、チェック OFF で非表示になる

## 1.2 Dock の表示状態とメニューのチェック状態を同期する

* [x] Dock を × で閉じたときにメニューのチェックが外れる
  - 完了条件: `toggleViewAction()` の組み込みシグナルで自動同期（`test_hide_dock_directly_syncs_action` 通過）
* [x] メニューのチェックを外すと Dock が非表示になる
  - 完了条件: `toggleViewAction()` の組み込み接続で `dock.setVisible()` が呼ばれる（`test_hide_dock_via_toggle_action` 通過）

---

# 2. コマンドバー整理（Ribbon 風 UI へ移行）

**v0.2 の最終 UI 方針: Ribbon 風コマンドバー（カテゴリタブ切り替え型）を導入する。**
**通常ツールバーは Ribbon 移行前の中間状態として完了済み。**

## 2.1 ツールバーを分割または再編する（完了済み・中間状態）

* [x] Project 系ボタンを左側にまとめる（Open / Save）
  - 完了条件: Project 操作が 1 グループに集約されている（New Project はメニューのみ）
* [x] Execution 系ボタンを右側にまとめる（Build / Reset / Run / Step）
  - 完了条件: 実行操作が 1 グループに集約されている
* [x] 重複・未使用ボタンを削除する
  - 完了条件: New Project / Pause をツールバーから除去（File / Run メニューには保持）

## 2.2 Pause ボタンの扱いを決める（完了済み）

* [x] Pause をメニュー側に寄せる（ツールバーからは除去）
  - 完了条件: Pause の配置方針が決定し UI に反映済み（`_a_pause` は Run メニューに残存、F6 ショートカット保持）

## 2.3 Ribbon 風コマンドバーの実装

**目標**: カテゴリタブ + ボタンパネルで操作をまとめた Ribbon 風コマンドバーを実装する。

* [x] `ui/ribbon.py` を作成する
  - 完了条件: `RibbonBar(QWidget)` クラスが定義されており、カテゴリタブを持つ
* [x] Project タブを実装する（File タブに変更済み）
  - 完了条件: New Project / Open Project / Save Project / Save Project As... ボタンが並んで表示される
* [x] Build / Run タブを実装する
  - 完了条件: Build / Reset / Run / Step / Pause ボタンが並んで表示される
* [x] View タブを実装する
  - 完了条件: 各 Dock のトグルボタンが並んで表示される（既存 `toggleViewAction()` を再利用）
* [x] Tools タブを実装する（プレースホルダ）
  - 完了条件: Tools タブが存在し、後で連携アクションを `add_page()` で追加できる構造
* [x] `MainWin` に `RibbonBar` を組み込む
  - 完了条件: 既存 QToolBar を `RibbonBar` に置き換え、全ショートカットが保持される
* [x] 既存テストが全件通過する
  - 完了条件: `pytest tests/` 120 件 PASSED

## 2.4 メニューバーと Ribbon の重複整理

**目標**: Build / Run / View メニューを削除し、操作を Ribbon に集約する。

* [x] メニューバーから Build / Run / View メニューを削除する
  - 完了条件: menuBar().actions() が `["File"]` のみになる
* [x] Build / Run アクションをウィンドウに直接登録してショートカットを維持する
  - 完了条件: F5 / Ctrl+R / F10 / Ctrl+Shift+R / F6 が引き続き動作する（`self.addAction()` で登録済み）
* [x] Ribbon の "Project" タブを "File" タブに変更する
  - 完了条件: Ribbon 先頭タブが "File" になり、New / Open / Save / Save As ボタンが含まれる

## 2.5 Ribbon サイズ調整

**目標**: Ribbon ボタンを押しやすいサイズにし、高さをコードで調整できるようにする。

* [x] `RibbonBar` に `button_min_width` / `button_min_height` / `ribbon_min_height` パラメータを追加する
  - 完了条件: `RibbonBar(button_min_width=120, button_min_height=56)` のように上書き可能
* [x] 各ボタンに `setMinimumSize` を適用する
  - 完了条件: `button_min_size()` が (96, 48) 以上を返す（デフォルト値）
* [x] `button_min_size()` インスペクタメソッドを追加する
  - 完了条件: テストから `win._ribbon.button_min_size()` で取得できる

---

# 3. Parts Library 改善

**目標**: Parts Library を常時表示しなくても運用できる形にする。

## 3.1 Dock 再表示対応

* [x] View メニューから Parts Library を再表示できる（1.1 の Parts Library 項目と同一）
  - 完了条件: 1.1 完了をもって達成

## 3.2 ダイアログ化の検討（v0.2 では見送り）

* [ ] Parts Library を別ウィンドウ / ダイアログとして呼び出せるか検討する
  - **v0.2 では見送り。** Dock 再表示対応（3.1）で十分と判断。
  - v0.3 以降または必要になったときの候補として残す。
  - 実施する場合は実装・動作確認済みを完了条件とする。

---

# 4. VS Code 連携（v0.3 以降に延期）

> **この節は v0.3 以降に延期。v0.2 では実装しない。**
> 外部アプリ連携は別バージョンで扱う方針に変更。

~~**目標**: 現在のプロジェクト / ファイルを VS Code で開けるメニュー項目を追加する。~~

## 4.1 メニュー項目（v0.3 以降）

* [ ] `Tools > Open Project in VS Code` — v0.3 以降
* [ ] `Tools > Open Current ASM in VS Code` — v0.3 以降
* [ ] `Tools > Open Current HDL in VS Code` — v0.3 以降

## 4.2 エラーハンドリング（v0.3 以降）

* [ ] `code` コマンドが見つからない場合は Log にエラーを出す — v0.3 以降
* [ ] プロジェクト未設定時は Log に案内を出す — v0.3 以降

---

# 5. 初期レイアウト改善（現状で許容）

**目標**: 起動直後から System Canvas が中心になる配置にする。

**確認結果（2026-05-24）**: Canvas 幅 760px / ウィンドウ幅 1280px = 59%。
目安の 60% にほぼ到達しており、現在の配置で十分と判断。追加実装は行わない。

## 5.1 初期 Dock 配置

* [x] Canvas 領域が十分な幅を持つ（現状: 59%、目安 60% にほぼ到達）
  - 現状で許容。大幅な改善が必要な場合のみ v0.3 で対応。

## 5.2 View メニューで戻せることを確認する

* [x] 初期非表示にした Dock を View メニューから再表示できる
  - 完了条件: 1.1 完了をもって達成

---

# 6. v0.1 回帰テスト（完了）

**目標**: v0.2 の変更で v0.1 フローが壊れていないことを確認する。

## 6.1 手動フロー確認（headless 駆動で検証、2026-05-24）

* [x] New Project → AK32 CPU 配置 → Open Program（main.asm）→ hello.asm 書き込み
* [x] Build（F5）でバイナリが生成される（24 bytes, main.bin）
* [x] Reset → Run で CPU が実行される（HALT で停止）
* [x] UART Console に "Hi" が表示される（uart_out == 'Hi'）
* [x] Register View が更新される（halted=True, pc=0x0014, r1=105）
* [x] Bus Trace に UART write が表示される（WRITE 0x0100 × 2 件）

## 6.2 自動テスト（2026-05-24）

* [x] `pytest tests/test_v01_flow.py` が全件通過する（9 件 PASSED）
* [x] `pytest tests/` が全件通過する（120 件 PASSED、0 件 FAILED）
