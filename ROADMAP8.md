# AKDev ROADMAP 8

> v0.8 開発計画（**候補整理のみ**。実装は未着手。ユーザー指示後に着手する）。
> **現行の管理ファイルは `ROADMAP8.md` / `CHECKLIST8.md`。**
> v0.7（Plan-driven Virtual Devices & Address Map）の到達点は
> `old/ROADMAP7.md`（✅ v0.7 PHASE COMPLETE）/ `old/CHECKLIST7.md` を参照。
> v0.6 以前の計画書・チェックリスト（`ROADMAP6.md`〜・`CHECKLIST6.md`〜）も `old/` に収納済み。
> 進捗管理は実装開始時に `CHECKLIST8.md` で行う。

---

## v0.7 からの引き継ぎ状況

v0.7 で、Canvas に描いた CPU+RAM+UART 回路を CircuitPlan から実デバイス化して実行し、
Address Map・実行状態（Run Status Panel）・ポート/接続（Port Detail Panel）を確認できる
ところまで到達した。`pytest tests/` = 860 passed。

v0.8 は、この実行基盤の上で **接続の妥当性検証** と **デバイス種別の拡張**、そして
**ゲーム runtime / HDL・FPGA export への準備**を進めるフェーズと位置づける。

---

## v0.8 テーマ（候補）

**Device Expansion & Connection Validation**
（接続検証とデバイス拡張 — 実行基盤から「正しく組めるか」を検証し、デバイス種別を増やす）

---

## v0.8 作業候補（未確定・優先順位は今後決定）

> **進捗**: `PATCH_PORT_SCHEMA_V08` 実装完了（ports schema v2・`core/ports.py`）。
> 次候補は `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08`（候補 A 本体）。**初手は warning only**
> （接続ブロックはせず Log + Port Detail に診断表示）。
> 設計資料: `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08_ROADMAP.md` / `..._CHECKLIST.md`（実装は未着手）。

### A. Port direction / width validation
- part.json の `ports` に direction / width を明示し、接続時に整合を検証。
- 前段の ports schema 正規化（`PATCH_PORT_SCHEMA_V08`）は完了。
- 本体 `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08` は **warning only** で開始（ブロックは次以降）。
- master↔slave / out↔in / width 一致などの接続可否ルール。

### B. Bus protocol validation
- bus.master ↔ bus.slave の対応、1 master 制約などの検証。
- Address Map と組み合わせた到達性チェック。
- **次候補として `PATCH_BUS_PROTOCOL_VALIDATION_V08` を検討中**（`PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08`
  の次）。初手は **warning only**（bus group の master/slave 数診断。到達性本対応は次段）。
  設計資料: `PATCH_BUS_PROTOCOL_VALIDATION_V08_ROADMAP.md` / `..._CHECKLIST.md`（実装は未着手）。

### C. 複数 RAM / UART handling
- 現状は単一前提。複数 RAM/UART を Address Map 上で共存させる。
- target CPU から見た複数スレーブのアドレス割当・選択。
- **前段として `PATCH_DEVICE_REGISTRY_REFACTOR_V08` を検討中**（`PATCH_BUS_PROTOCOL_VALIDATION_V08`
  の次）。実行デバイス生成・Address Map を **device list driven** に整理してから複数対応へ進む方針
  （挙動不変・VRAM≠RAM の土台）。設計資料: `PATCH_DEVICE_REGISTRY_REFACTOR_V08_ROADMAP.md` /
  `..._CHECKLIST.md`（実装は未着手）。

### D. ROM / VRAM / Storage / Input device expansion
- 新デバイス種別の plan-driven 生成（v0.7 の RAM/UART と同方式）。
- それぞれの MMIO 窓・Address Map 統合。

### E. Address Map Editor
- ユーザーによる base/size の任意編集 UI（v0.7 は固定既定）。
- overlap 検出（既存）と連動した編集時バリデーション。

### F. コード領域の拡張設計 / UART MMIO 窓の再配置・可変化
- 現状コードは 0x0000 開始・UART 窓 0x0100–0x0107 固定。
- 大きめプログラム/ゲーム向けにコード領域・MMIO 配置を見直す。

### G. CPU 命令拡張
- CALL / RET / IN 等（スタック設計が必要）。
- 既存 11 命令（NOP/HALT/LDI/OUT/ADD/SUB/LD/ST/JMP/BEQ/ADDI）の上に追加。

### H. ゲーム runtime 準備
- 最終目標「自作 CPU 上でゲーム 1 本を起動・操作」に向けた実行環境の整備。
- 入力・表示・タイミングの最小ループ設計。

### I. HDL / FPGA export 準備
- 回路 → HDL 出力、合成（iverilog / Yosys）、FPGA 実機書き込みの準備。

---

## v0.8 ではまだ確定でないこと

- 上記候補の取捨選択・順序はユーザー判断で確定する。
- 1 パッチ = 1 機能の運用（`PATCH_*_V08_*` の ROADMAP/CHECKLIST を着手前に作成）。

---

## 今回（v0.7 完了整理）でやらないこと

- 上記の実装。新機能・挙動変更・テスト追加・commit / push は行わない。
- 本ファイルは候補整理のみ。実装はユーザーが最初のパッチを指示してから着手する。
