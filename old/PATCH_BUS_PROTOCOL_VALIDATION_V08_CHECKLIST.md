# PATCH_BUS_PROTOCOL_VALIDATION_V08 — CHECKLIST（設計資料）

> 設計詳細は `PATCH_BUS_PROTOCOL_VALIDATION_V08_ROADMAP.md` を参照。
> 本書は**実装時に使うチェックリスト**。現時点では実装未着手（設計資料のみ）。
> コード変更・テスト追加・part.json 変更・commit/push は本タスクでは行わない。

---

## 0. 事前確認

* [x] `git status --short` がクリーンであることを確認
* [x] `python -m pytest tests/` が全通過（着手時ベースライン **913 passed**）
* [x] `PATCH_PORT_SCHEMA_V08` が完了・コミット済み（`a3050a3`）
* [x] `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08` が完了・コミット済み（`9b0a589`）
* [x] ports schema v2 を確認（各 port に `role` / `direction` / `width`）
* [x] `core/port_validation.py` の issue 構造（severity/code/message/details + from_*/conn_id）を確認
* [x] `core/ports.base_port_type` を確認（bus 判定で再利用）
* [x] 既存 bus / address map / target cpu テストを確認（log/conn 全等価アサート無しを確認）
* [x] connection データ構造（from/to の `port`/`logical_port`）と `ui/canvas.py` の接続フローを確認

## 1. 設計

* [x] **warning only** 方針の確定（接続ブロックはしない）
* [x] bus group の定義確定（bus edge の連結成分・port 単位・bus 以外は無視・未接続単独 port は対象外）
* [x] bus group 構造の確定（id / nodes / ports / masters / slaves / connections）
* [x] master/slave 判定ルール確定（0 master=`BUS_NO_MASTER` / ≥2 master=`BUS_MULTIPLE_MASTERS` / 0 slave=`BUS_NO_SLAVE`）
* [x] role null な bus port の扱い確定（役割集計から除外）
* [x] target CPU 到達性を今回どこまでやるか確定（**group 所属を details に付与・本格到達性は次段**）
* [x] Address Map との関係確定（overlap は既存任せ・突き合わせは次段。引数のみ用意）
* [x] bridge の扱い確定（master/slave 両ポート・port 単位で別 group・橋渡し routing は次段）
* [x] issue 構造を port validation と互換にする（severity/code/message/details + group_id/nodes/connections）
* [x] UI 表示方針確定（Log + Port Detail まで・色/アイコン/Diagnostics は次以降。Run Status summary は今回見送り）
* [x] 接続ブロックを今回はしない方針の確認

## 2. 実装

* [x] `core/bus_validation.py` 新規（Qt 非依存・純粋関数 + code 定数）
* [x] `is_bus_port(port)` 追加
* [x] `build_bus_groups(nodes, connections)` 追加（union-find の連結成分・bus 以外無視・port 単位）
* [x] `validate_bus_group(group)` 追加（master/slave 数診断）
* [x] `validate_bus_protocol(nodes, connections, *, target_cpu_id=, address_map=)` 追加
* [x] `ui/canvas.py` に `bus_validation()` / `node_bus_validation_issues()` / `connection_bus_validation_issues()` + `add_connection` で Log warning
* [x] `ui/port_detail.py` に node / wire の bus group issue 表示（port issue と合算）+ `_render_validation` に group_id 表示
* [x] 既存 port validation（per-connection）と併用（別レイヤ・干渉しない）

## 3. テスト（`tests/test_bus_protocol_validation_v08.py` — 24 件）

* [x] `is_bus_port` 判定（bus/非bus/None/{}）
* [x] bus group 連結成分構築（CPU-RAM / 複数 group / bridge で port 単位に分離）
* [x] CPU master + RAM slave → issue なし / + UART slave → issue なし
* [x] slave 同士 → `BUS_NO_MASTER`
* [x] master 同士 → `BUS_MULTIPLE_MASTERS` + `BUS_NO_SLAVE`
* [x] master 複数 + slave 有り → `BUS_MULTIPLE_MASTERS`（`BUS_NO_SLAVE` なし）
* [x] bus 以外の connection は無視される
* [x] role null / missing port / None part / 空入力でもクラッシュしない
* [x] target_cpu_id 指定で details に `target_cpu_in_group`
* [x] **warning only**: bus warning が出ても接続は作成される（canvas）
* [x] Canvas `bus_validation` / `node_*` / `connection_*` API + Log warning
* [x] port validation と bus validation の共存
* [x] Port Detail（node / wire）に bus issue 表示・valid は OK
* [x] 既存 v0.7 / v0.8 テストが壊れない

## 4. 検証

* [x] `python -m pytest tests/` 全件通過 — **937 passed**（913 + 24）
* [ ] GUI 目視: 不正 bus 構成で Log に warning / Port Detail に表示（ヘッドレスのため未実施）
* [x] 既存プロジェクト互換: 接続は従来どおり作成され**ブロックされない**（既存テスト通過で実証）

## 5. 完了条件

* [x] bus group 診断ができる（連結成分の master/slave 数）
* [x] `BUS_MULTIPLE_MASTERS` / `BUS_NO_MASTER` / `BUS_NO_SLAVE` が warning として見える
* [x] 既存接続・既存テストを壊さない（接続はブロックされない）
* [x] Port Detail に bus protocol issue が表示される
* [x] issue が構造化データ（port validation 互換）として取得できる
* [x] 次の `PATCH_DEVICE_REGISTRY_REFACTOR_V08` / `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08` へ進める土台ができている
