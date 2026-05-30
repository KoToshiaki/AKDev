# AKDev CHECKLIST 4

> v0.3 Project & Target Foundation 用チェックリスト。
> v0.2 完了（pytest 120 件 PASSED）を前提とする。
> 詳細な設計は `ROADMAP4.md` を参照。

---

# 0. v0.3 方針確定

* [x] v0.3 名称を **Project & Target Foundation** にする
* [x] v0.3 は v0.4 VS Code Companion の下準備と位置づける
* [x] AKDev と VS Code の関係を **Unity と VS Code のような関係**として定義する
* [x] VS Code 拡張本体は v0.4 以降に回す
* [x] KiCad 連携は v0.5 以降に回す

---

# 1. target.json 仕様

* [x] target.json の基本構造を決める
  - 完了条件: `name / isa / cpu / runtime / entry / output / load_address / entry_point` の意味と型が定義されている
* [x] AK32 Baremetal を既定ターゲットにする
  - 完了条件: target.json の初期値として AK32 Baremetal 設定が定義されている（`default_target_config()` で実装済み）
* [x] `isa / cpu / runtime / entry / output / load_address / entry_point` を定義する
  - 完了条件: 各フィールドの説明が ROADMAP4.md に記載されている
* [x] 将来の自作 ISA / 自作 OS 対応を考慮する
  - 完了条件: `isa` / `runtime` フィールドが拡張可能な文字列として定義されている
* [x] 既存 Build / Run フローを壊さない方針を確認する
  - 完了条件: `load_json_or_default()` により target.json 未存在でも AK32 Baremetal デフォルトで動作する

---

# 2. tools.json 仕様

* [x] tools.json の基本構造を決める
  - 完了条件: `tools` オブジェクトの構造（`command` / `args`）が定義されている
* [x] vscode tool 設定を定義する
  - 完了条件: `tools.vscode.command` / `tools.vscode.args` の仕様が決まっている（`default_tools_config()` で実装済み）
* [x] kicad tool 設定は将来用として定義だけ検討する
  - 完了条件: kicad 設定枠を `enabled: false` で生成済み
* [x] ユーザー環境ごとの command path の違いを考慮する
  - 完了条件: Windows / macOS / Linux でのコマンド差異への対処方針が決まっている
  - `command` は PATH 上のコマンド名またはフルパスを許可する。既定値は `"code"`。Windows では `code.cmd` / `code.exe`、macOS/Linux では `code` を想定。ユーザーが `tools.json` の `command` を上書きすることで OS 差異を吸収できる。OS 自動検出・設定 UI は v0.5 以降。
* [x] v0.3 では外部ツール連携を最小限に留める
  - 完了条件: v0.3 スコープが "VS Code を開く程度" に限定されていることが明記されている

---

# 3. .vscode/ 生成方針

* [x] .vscode/settings.json の生成方針を決める
  - 完了条件: `{"akdev.project": true}` の最小構成で生成済み（v0.4 拡張導入後に settings を拡張予定）
* [x] .vscode/extensions.json の生成方針を決める
  - 完了条件: `akdev.akdev-companion` を recommendations に含む構成で生成済み
* [x] .vscode/tasks.json の生成方針を検討する
  - 完了条件: v0.3 では **生成しない** と決定。Build / Run タスクは v0.5 AKDev VS Code Companion 側で扱う。v0.3 では settings.json / extensions.json のみ生成済みで十分。
* [x] AKDev Companion 拡張を recommended extension として扱える構造にする
  - 完了条件: extensions.json に `akdev.akdev-companion` が含まれる
* [x] 拡張本体は v0.4 以降と明記する
  - 完了条件: ROADMAP4.md に v0.4 スコープとして記載されている

---

# 4. 標準プロジェクト構造

* [x] project.json / system.json / target.json / tools.json の役割を整理する
  - 完了条件: 各ファイルの責務が ROADMAP4.md に明記されている
* [x] `src/ hdl/ board/ asset/ build/out/ build/rom/ build/export/ docs/ .vscode/` の構成を決める
  - 完了条件: 標準ディレクトリ構造が ROADMAP4.md に定義されており、create_project() で生成済み
* [x] create_project() の拡張方針を決める
  - 完了条件: 新規作成時に target.json / tools.json / .vscode/ が生成される（実装済み）
* [x] 既存プロジェクトとの互換方針を決める
  - 完了条件: `load_json_or_default()` により target.json 未存在時のフォールバック動作を定義済み

---

# 5. Source Type 方針

* [x] `asm / hdl / c / cpp / linker / binary / custom` を source type 候補にする
  - 完了条件: source type の一覧と各 type の対象ファイル拡張子が定義されている
  - `src_type(path)` 関数を `core/project.py` に実装済み。`.asm/.v/.vhd/.c/.cpp/.ld/.bin/.hex` → 各 type、その他 → `custom`
* [x] C 前提にしないことを明記する
  - 完了条件: ROADMAP4.md に "C 前提にしない" と明記されている
* [x] 自作言語は custom source type として扱う方針にする
  - 完了条件: `custom` type の位置づけが定義されている（`src_type()` のデフォルト戻り値）
* [x] v0.3 では分類構造の設計までに留める
  - 完了条件: 実装は v0.5 以降と決まっている（C コンパイラ / 自作言語対応は除外）
  - `src_type()` 関数は分類のみ。Build パイプラインへの接続は v0.5 以降。

---

# 6. Build 設定分離

* [x] internal_assembler の設定形式を決める
  - 完了条件: `build.type = "internal_assembler"` の JSON 形式が定義されている
  - `default_target_config()` に定義済み。`_build()` で `build.type` を確認して内蔵アセンブラを呼ぶ。
* [x] external_command の設定形式を決める
  - 完了条件: `build.type = "external_command"` の JSON 形式（将来用）が ROADMAP4.md に記載されている
  - ROADMAP4.md に JSON 例を記載済み。`_build()` で "not implemented yet" ログを出して中断。
* [x] build output を target.json / build 設定から参照できるようにする方針を決める
  - 完了条件: `build.output` フィールドの役割と Build パイプラインとの関係が定義されている
  - ROADMAP4.md に方針を追記: active tab ビルド時は `<stem>.bin` を優先。`build.output` は Project Build モードで完全利用（v0.4 以降）。
* [x] 既存の F5 Build フローとの互換を考慮する
  - 完了条件: target.json が存在しない場合の F5 Build 動作が定義されている
  - `load_target()` が target.json 未存在時に `default_target_config()` を返す。AK32 Baremetal デフォルトで動作。
* [x] AK32 hello.asm フローを壊さない方針を明記する
  - 完了条件: ROADMAP4.md に "既存フローを壊さない" と明記されている
  - pytest 159 件全通過（test_v01_flow.py 9 件含む）で確認済み。

---

# 7. v0.5 AKDev VS Code Companion への橋渡し

> **方針変更（2026-05-24）**: VS Code Companion は v0.4 から v0.5 に移動。v0.4 は Visual Debug Canvas になる。

* [x] VS Code Companion の将来機能を整理する
  - 完了条件: ROADMAP4.md の v0.5 節に機能一覧が記載されている
* [x] localhost HTTP / WebSocket 連携案を記載する
  - 完了条件: ROADMAP4.md セクション 7 に localhost HTTP / WebSocket エンドポイント構想を記載済み
* [x] Build / Run / Reset / Step 要求の将来 API 案を記載する
  - 完了条件: ROADMAP4.md セクション 7 に将来 API（POST /build / /run / /step / /reset、GET /registers）を記載済み
* [x] target.json / isa.json を使った補完構想を記載する
  - 完了条件: ROADMAP4.md セクション 7 に isa.json の役割と補完構想を記載済み
* [x] v0.3 では実装しない範囲を明確にする
  - 完了条件: ROADMAP4.md セクション 7 "v0.3 では実装しないこと" に VS Code 拡張本体・localhost 通信・補完・Problems 連携を v0.3 ではやらないと明記済み

---

# 8. v0.3 でやらないこと

> これらはすべて「実装しないことを確認した」として完了扱い。

* [x] VS Code 拡張本体は作らない（→ v0.5）
* [x] KiCad 基板自動生成はしない（→ v0.6）
* [x] 自作 OS 本体は作らない（→ v0.6 以降）
* [x] C コンパイラ本格対応はしない（→ v0.6 以降）
* [x] 複数 ISA 完全対応はしない（→ v0.6 以降）
* [x] HDL 合成はしない（→ v0.6 以降）
* [x] 実機書き込みはしない（→ v0.6 以降）
* [x] .vscode/tasks.json は生成しない（→ v0.5 Companion 側）
* [x] Open in VS Code の OS 自動検出 UI は実装しない（→ v0.5）

---

# 9. HANDOFF 更新

* [x] HANDOFF.md に v0.3 の方針を追加する（セッション 18）
* [x] 現在の優先作業を v0.3 Project & Target Foundation にする（セッション 18）
* [x] v0.2 は完了整理フェーズであることを書く（セッション 18）
* [x] 次回は CHECKLIST4.md のセクション 0 から始めるように書く（セッション 18）
* [x] v0.3 完了として HANDOFF.md を最終更新する
  - 完了条件: v0.3 完了・pytest 159 件通過・次は v0.4 Visual Debug Canvas が明記されている
