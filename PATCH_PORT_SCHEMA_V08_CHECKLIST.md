# PATCH_PORT_SCHEMA_V08 — CHECKLIST（設計資料）

> 設計詳細は `PATCH_PORT_SCHEMA_V08_ROADMAP.md` を参照。
> 本書は**実装時に使うチェックリスト**。現時点では実装未着手（設計資料のみ）。
> コード変更・part.json 変更・テスト追加・commit/push は本タスクでは行わない。

---

## 0. 事前確認

* [x] `git status --short` がクリーン（または想定どおりの未コミットのみ）であることを確認
  - v0.8 設計資料（`V08_CODEBASE_REVIEW.md` / `PATCH_PORT_SCHEMA_V08_*` / `ROADMAP8`/`CHECKLIST8`）が未コミット。ユーザー承認のうえ実装続行
* [x] `python -m pytest tests/` が全通過（着手時のベースライン取得） — **860 passed**
* [x] 対象 part.json 一覧を確認（実体は `parts/**/part.json` で 11 種: cpu/ak32, mem/ram, io/uart, io/gpio, io/timer, mem/vram, video/out, video/regs, bus/bridge, fpga/generic, **fpga/ecp5_85f**）
* [x] 既存 ports schema を確認（各 port が `{name,type}` のみ・`schema_version` 無し）
* [x] `ui/lib.py:load_parts()` の `_REQUIRED` 検証と読み込み経路を確認
* [x] `ui/port_detail.py` の `direction_from_type` / `build_node_info` の現挙動を確認

## 1. 設計

* [x] 新 ports schema（v2）の確定（フィールド: name/type/role/direction/width/required/description）
* [x] `schema_version` 方針の確定（無し=v1 とみなす / 正規化後は常に v2）
* [x] **案 B 採択**（type 維持 + フィールド追加）
* [x] legacy 互換方針の確定（v1→v2 正規化規則・unknown→inout/None・width None 許容）
* [x] **irq の part 固有 direction**（CPU=in / Timer・UART・Video=out）の明示方針を確定
* [x] 正規化関数の配置決定（`core/ports.py` 新規）
* [x] Port Detail との連携方針確定（明示値優先・無ければ従来推定にフォールバック・`role`/`description` 表示追加）
* [x] `core/circuit.py` のロール判定は本パッチで変更しない方針を確認（VRAM=mem 正確化は別パッチ）

## 2. 実装

* [x] `core/ports.py` に正規化関数を追加（`normalize_part` / `normalize_port` / `normalize_ports` / `base_port_type` / `derive_role` / `derive_direction` / `derive_width` / `is_legacy_part`）
* [x] `parts/**/part.json` を v2 へ migration（11 種・`schema_version:2` + 各 port に明示フィールド）
* [x] `ui/lib.py:load_parts()` で `normalize_part()` を適用（library 全 part を v2 化・`_REQUIRED` 検証維持）
* [x] `ui/port_detail.py` を明示 direction/width/role 優先表示に更新（フォールバック維持・role/description 行追加）
* [x] 旧形式（v1）互換の維持（正規化層で救済・直接 dict も可）
* [x] import/export（system.json）互換の確認（part 定義は埋め込まれず `part_id` 参照のため非影響）

## 3. テスト（`tests/test_port_schema_v08.py` — 18 件）

* [x] schema 正規化の単体（v1 port → v2 補完）
* [x] 旧形式 part dict を直接 `normalize_part()` に渡しても壊れない
* [x] 新形式（v2）明示値が推定で上書きされない（width None 保持含む）
* [x] part 固有 direction（CPU irq=in / UART・Timer・Video regs irq=out）の保持
* [x] unknown type で安全な既定（role None / direction inout / width None）
* [x] `load_parts()` 全 part に `schema_version:2` と各 port の 7 フィールド
* [x] Port Detail 表示（direction/width/role の明示値が出る・旧 part はフォールバック）
* [x] 既存テスト全通過（v0.7 系 / wiring 系 / port_detail / import-export）

## 4. 検証

* [x] `python -m pytest tests/` が全件通過 — **878 passed**（860 + 18）
* [ ] GUI 目視: パーツ選択時に Port Detail で direction/width/role が明示値で見える（ヘッドレスのため未実施）
* [x] 既存 project（system.json）round-trip が不変（save/load・import/export 系テスト通過）
* [x] 旧形式 part dict でもクラッシュしない（フォールバックテストで実証）

## 5. 完了条件

* [x] ports schema（v2）が明確化されている（フィールド定義 + 規約）
* [x] 旧形式（v1）互換がある（正規化層で救済）
* [x] Port Detail で新 schema（direction/width/role）が見える
* [x] part 固有 direction（irq の in/out）が表現できている
* [x] 既存テストが全通過し、保存フォーマット互換が保たれている
* [x] 次の `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08` に進める土台ができている
