# PATCH_BUS_PROTOCOL_VALIDATION_V08 — CHECKLIST（設計資料）

> 設計詳細は `PATCH_BUS_PROTOCOL_VALIDATION_V08_ROADMAP.md` を参照。
> 本書は**実装時に使うチェックリスト**。現時点では実装未着手（設計資料のみ）。
> コード変更・テスト追加・part.json 変更・commit/push は本タスクでは行わない。

---

## 0. 事前確認

* [ ] `git status --short` がクリーンであることを確認
* [ ] `python -m pytest tests/` が全通過（着手時ベースライン取得）
* [ ] `PATCH_PORT_SCHEMA_V08` が完了・コミット済みであることを確認
* [ ] `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08` が完了・コミット済みであることを確認
* [ ] ports schema v2 を確認（各 port に `role` / `direction` / `width`）
* [ ] `core/port_validation.py` の issue 構造（severity/code/message/details + from_*/conn_id）を確認
* [ ] `core/ports.base_port_type` を確認（bus 判定で再利用）
* [ ] 既存 bus / address map / target cpu テストを確認（`test_address_map_v07` / `test_target_cpu_selection_v07` / `test_virtual_circuit_runtime_v05`）
* [ ] connection データ構造（from/to の `port`/`logical_port`）と `ui/canvas.py` の接続フローを確認

## 1. 設計

* [ ] **warning only** 方針の確定（接続ブロックはしない）
* [ ] bus group の定義確定（bus edge の連結成分・port 単位・bus 以外は無視・未接続単独 port は対象外）
* [ ] bus group 構造の確定（id / nodes / ports / masters / slaves / connections）
* [ ] master/slave 判定ルール確定（0 master=`BUS_NO_MASTER` / ≥2 master=`BUS_MULTIPLE_MASTERS` / 0 slave=`BUS_NO_SLAVE`）
* [ ] role null な bus port の扱い確定（役割集計から除外）
* [ ] target CPU 到達性を今回どこまでやるか確定（**group 所属まで・本格到達性は次段**）
* [ ] Address Map との関係確定（overlap は既存任せ・突き合わせは次段）
* [ ] bridge の扱い確定（master/slave 両ポート・port 単位で別 group・橋渡し routing は次段）
* [ ] issue 構造を port validation と互換にする（severity/code/message/details + group_id/nodes）
* [ ] UI 表示方針確定（Log + Port Detail まで・Run Status summary は任意・色/アイコン/Diagnostics は次以降）
* [ ] 接続ブロックを今回はしない方針の確認

## 2. 実装予定（今回は未実装）

* [ ] `core/bus_validation.py` 新規（Qt 非依存・純粋関数 + code 定数）
* [ ] `is_bus_port(port)` 追加
* [ ] `build_bus_groups(nodes, connections)` 追加（連結成分・bus 以外無視）
* [ ] `validate_bus_group(group)` 追加（master/slave 数診断）
* [ ] `validate_bus_protocol(nodes, connections, *, target_cpu_id=, address_map=)` 追加
* [ ] `ui/canvas.py` に `bus_validation()` read-only API + `connections_changed` 後の Log warning
* [ ] `ui/port_detail.py` に node（必要なら wire）の bus group issue 表示（port issue と合算）
* [ ] （任意）`ui/win.py` Run Status に bus warning 件数 summary
* [ ] 既存 port validation（per-connection）と併用（別レイヤ・干渉しない）

## 3. テスト予定（今回は未追加）

* [ ] bus group が連結成分として正しく構築される（複数 group・bridge で port 単位に分かれる）
* [ ] CPU master + RAM slave → issue なし
* [ ] CPU master + RAM slave + UART slave → issue なし
* [ ] slave のみ（slave 同士配線）→ `BUS_NO_MASTER`
* [ ] master のみ（slave 不在）→ `BUS_NO_SLAVE`
* [ ] master 2 個以上 → `BUS_MULTIPLE_MASTERS`
* [ ] bus 以外の connection は無視される
* [ ] role null / unknown / missing port / None part でもクラッシュしない
* [ ] **warning only**: bus warning が出ても接続は作成される
* [ ] Port Detail に bus issue が表示される / valid group は OK
* [ ] 既存 v0.7 / v0.8 テストが壊れない

## 4. 検証予定

* [ ] `python -m pytest tests/` が全件通過
* [ ] GUI 目視: 不正 bus 構成（複数 master 等）で Log に warning / Port Detail に表示
* [ ] 既存プロジェクト（system.json）を開いて接続が従来どおり作れる（ブロックされない）

## 5. 完了条件

* [ ] bus group 診断ができる（連結成分の master/slave 数）
* [ ] `BUS_MULTIPLE_MASTERS` / `BUS_NO_MASTER` / `BUS_NO_SLAVE` が warning として見える
* [ ] 既存接続・既存テストを壊さない（接続はブロックされない）
* [ ] Port Detail に bus protocol issue が表示される
* [ ] issue が構造化データ（port validation 互換）として取得できる
* [ ] 次の `PATCH_DEVICE_REGISTRY_REFACTOR_V08` / `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08` へ進める土台ができている
