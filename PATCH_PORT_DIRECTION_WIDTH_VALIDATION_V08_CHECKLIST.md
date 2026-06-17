# PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08 — CHECKLIST（設計資料）

> 設計詳細は `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08_ROADMAP.md` を参照。
> 本書は**実装時に使うチェックリスト**。現時点では実装未着手（設計資料のみ）。
> コード変更・テスト追加・part.json 変更・commit/push は本タスクでは行わない。

---

## 0. 事前確認

* [ ] `git status --short` がクリーンであることを確認
* [ ] `python -m pytest tests/` が全通過（着手時ベースライン取得）
* [ ] `PATCH_PORT_SCHEMA_V08` が完了・コミット済みであることを確認
* [ ] ports schema v2 を確認（各 port に `role` / `direction` / `width` / `required` / `description`）
* [ ] `core/ports.py` の `base_port_type` / `normalize_part` を確認（検証で再利用）
* [ ] 既存 wiring/接続テストを確認（`test_wiring_ports_v05` / `test_port_drag_connect_v05` / `test_wire_select_delete_v05` / `test_wire_style_v05` / `test_port_detail_v07`）
* [ ] `ui/canvas.py:add_connection` と connection データ構造（from/to の `port`/`logical_port`）を確認

## 1. 設計

* [ ] **warning only** 方針の確定（接続ブロックはしない）
* [ ] validation issue 構造の確定（severity / code / message / from_* / to_* / conn_id / details）
* [ ] direction 判定ルールの確定（out↔in OK / inout 系 OK / out↔out・in↔in は warning / 不明は skip）
* [ ] width 判定ルールの確定（一致 OK / 不一致 warning / None は skip）
* [ ] role 判定ルールの確定（master↔slave OK / 同一は warning / null は skip）
* [ ] kind 判定（bus↔clock 等）を warning にするか info にするか確定
* [ ] required 未接続 / self / duplicate を node レベルで扱う範囲の確定
* [ ] UI 表示方針の確定（Log + Port Detail まで・wire 色/アイコン/Diagnostics は次以降）
* [ ] 接続ブロックを今回はしない方針の確認

## 2. 実装予定（今回は未実装）

* [ ] `core/port_validation.py` 新規（Qt 非依存・純粋関数 + code 定数）
* [ ] `find_port(part, name)` 追加
* [ ] `validate_port_pair(port_a, port_b)` 追加（対称・None 安全）
* [ ] `validate_connection(from_part, from_port, to_part, to_port, conn_id=)` 追加
* [ ] `validate_node_connections(nodes, connections)` 追加（self/duplicate/required 集約）
* [ ] `ui/canvas.py:add_connection` で validation 実行 → `conn["validation"]` 保持 + Log warning（**接続は作成**）
* [ ] `ui/port_detail.py` に「Validation」セクション表示（wire / node・issue 無しは "(none)"）
* [ ] 既存接続互換（無検証で作っていた既存テストが通る）

## 3. テスト予定（今回は未追加）

* [ ] direction: out→in / inout↔inout / inout↔in / inout↔out が OK
* [ ] direction: out↔out / in↔in が warning
* [ ] width: 一致 OK / 不一致 warning / None skip
* [ ] role: master↔slave OK / master↔master・slave↔slave warning / null skip
* [ ] kind 不一致（bus↔clock）の扱い
* [ ] unknown port 名・None port でも crash しない（`PORT_NOT_FOUND`）
* [ ] **warning only**: issue が出ても接続は作成される
* [ ] Port Detail に validation issue が表示される / 無しは "(none)"
* [ ] 既存 wiring 系・port_detail テストが壊れない

## 4. 検証予定

* [ ] `python -m pytest tests/` が全件通過
* [ ] GUI 目視: 不整合接続を作ると Log に warning、Port Detail に Validation が出る
* [ ] 既存プロジェクト（system.json）を開いて接続が従来どおり作れる（ブロックされない）

## 5. 完了条件

* [ ] warning only で接続妥当性（direction/width/role）が見える
* [ ] 既存接続・既存テストを壊さない（接続はブロックされない）
* [ ] Port Detail に validation 結果が表示される
* [ ] validation 結果が構造化データとして取得できる
* [ ] 次の `PATCH_BUS_PROTOCOL_VALIDATION_V08` に進める土台ができている
