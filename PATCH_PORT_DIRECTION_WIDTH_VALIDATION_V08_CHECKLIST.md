# PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08 — CHECKLIST（設計資料）

> 設計詳細は `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08_ROADMAP.md` を参照。
> 本書は**実装時に使うチェックリスト**。現時点では実装未着手（設計資料のみ）。
> コード変更・テスト追加・part.json 変更・commit/push は本タスクでは行わない。

---

## 0. 事前確認

* [x] `git status --short` がクリーンであることを確認
* [x] `python -m pytest tests/` が全通過（着手時ベースライン **878 passed**）
* [x] `PATCH_PORT_SCHEMA_V08` が完了・コミット済み（`a3050a3`）
* [x] ports schema v2 を確認（各 port に `role` / `direction` / `width` / `required` / `description`）
* [x] `core/ports.py` の `base_port_type` / `normalize_port` を確認（検証で再利用）
* [x] 既存 wiring/接続テストを確認（log/conn 全等価アサート無しを確認）
* [x] `ui/canvas.py:add_connection` と connection データ構造（from/to の `port`/`logical_port`）を確認

## 1. 設計

* [x] **warning only** 方針の確定（接続ブロックはしない）
* [x] validation issue 構造の確定（severity / code / message / details + from_*/to_*/conn_id）
* [x] direction 判定ルールの確定（out↔in OK / inout 系 OK / out↔out・in↔in は warning / 不明は skip）
* [x] width 判定ルールの確定（一致 OK / 不一致 warning / None は skip）
* [x] role 判定ルールの確定（master↔slave OK / 同一は warning / null は skip）
* [x] kind 判定（bus↔clock 等）= warning（`PORT_KIND_MISMATCH`）
* [x] self / duplicate を `validate_node_connections`（将来 Diagnostics 用）に集約。required 未接続は次段へ送り（本パッチ未実装）
* [x] UI 表示方針の確定（Log + Port Detail まで・wire 色/アイコン/Diagnostics は次以降）
* [x] 接続ブロックを今回はしない方針の確認

## 2. 実装

* [x] `core/port_validation.py` 新規（Qt 非依存・純粋関数 + code 定数）
* [x] `find_port(part, name)` 追加
* [x] `validate_port_pair(port_a, port_b)` 追加（対称・None 安全）
* [x] `validate_connection(...)`（port 解決 + normalize + 端点 augment + `PORT_NOT_FOUND`）
* [x] `validate_node_connections(nodes, connections)` 追加（self/duplicate + 各接続検証）
* [x] `ui/canvas.py:add_connection` で validation 実行 → `conn["validation"]` 保持 + Log warning（**接続は作成**）
* [x] `ui/canvas.py` read-only API `connection_validation` / `node_validation_issues` 追加
* [x] `ui/port_detail.py` に「Validation」セクション表示（wire / node・issue 無しは "OK"）
* [x] 既存接続互換（`validation` 無し conn は `connection_validation` で再計算）

## 3. テスト（`tests/test_port_direction_width_validation_v08.py` — 35 件）

* [x] direction: out→in / in→out / inout↔inout / inout↔in / inout↔out が OK
* [x] direction: out↔out=`PORT_MULTIPLE_DRIVERS` / in↔in=`PORT_NO_DRIVER` / 欠落は skip
* [x] width: 一致 OK / 不一致 warning / None skip
* [x] role: master↔slave OK / master↔master・slave↔slave=`PORT_ROLE_MISMATCH` / null skip
* [x] kind 同一 OK / 不一致=`PORT_KIND_MISMATCH`
* [x] unknown type / None port / `{}` でも crash しない・missing port=`PORT_NOT_FOUND`
* [x] irq 方向（CPU=in / 周辺=out）: 周辺2出力=`MULTIPLE_DRIVERS` / CPU↔周辺=OK
* [x] **warning only**: issue が出ても接続は作成される（canvas）
* [x] `conn["validation"]` 保持 / valid は空 / Log に warning / 旧 conn 再計算
* [x] Port Detail（wire / node）に Validation 表示・OK 表示
* [x] 既存 wiring 系・port_detail・schema_v08 テストが壊れない

## 4. 検証

* [x] `python -m pytest tests/` 全件通過 — **913 passed**（878 + 35）
* [ ] GUI 目視: 不整合接続で Log に warning / Port Detail に Validation（ヘッドレスのため未実施）
* [x] 既存プロジェクト互換: 接続は従来どおり作成され**ブロックされない**（既存テスト通過で実証）

## 5. 完了条件

* [x] warning only で接続妥当性（direction/width/role/kind）が見える
* [x] 既存接続・既存テストを壊さない（接続はブロックされない）
* [x] Port Detail に validation 結果が表示される
* [x] validation 結果が構造化データ（issue dict）として取得できる
* [x] 次の `PATCH_BUS_PROTOCOL_VALIDATION_V08` に進める土台ができている
