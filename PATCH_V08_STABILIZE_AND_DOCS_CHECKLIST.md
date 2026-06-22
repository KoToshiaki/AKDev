# PATCH_V08_STABILIZE_AND_DOCS — CHECKLIST（v0.8 最終整理）

> v0.8 を閉じるための安定化・ドキュメント整理・最終検証。**コード変更なし・新機能なし・commit/push なし。**
> 設計詳細: `PATCH_V08_STABILIZE_AND_DOCS_ROADMAP.md`。親計画: `ROADMAP8.md` / `CHECKLIST8.md`。

---

## 0. 事前確認（2026-06-23）

- [x] `git branch --show-current` = `dev`
- [x] 作業ツリー clean（STABILIZE 着手前）
- [x] `PATCH_GAME_RUNTIME_MINIMAL_V08` コミット済み（`11c312c feat: add minimal game runtime`）
- [x] `PATCH_VRAM_DEVICE_V08` コミット済み（`b7b7a35 feat: add vram device`）
- [x] baseline test: `python -m pytest tests/` → **1182 passed**
- [x] `tests/test/system.json` 差分なし
- [x] `ROADMAP8.md` 見出し重複なし（`# AKDev ROADMAP 8` は 1 個）

---

## 1. v0.8 完了パッチの確認

- [x] `PATCH_PORT_SCHEMA_V08`（ports schema v2）
- [x] `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08`（warning only）
- [x] `PATCH_BUS_PROTOCOL_VALIDATION_V08`（warning only）
- [x] `PATCH_DEVICE_REGISTRY_REFACTOR_V08`（挙動不変）
- [x] `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08`
- [x] `PATCH_CODE_REGION_MMIO_RELOCATION_V08`（MemoryLayout）
- [x] `PATCH_ADDRESS_MAP_EDITOR_V08`
- [x] `PATCH_INPUT_DEVICE_V08`
- [x] `PATCH_ROM_DEVICE_V08`
- [x] `PATCH_PROGRAM_TARGET_ROM_V08`
- [x] `PATCH_AK32_BITWISE_INSTRUCTIONS_V08`
- [x] `PATCH_TIMER_DEVICE_V08`
- [x] `PATCH_VRAM_DEVICE_V08`
- [x] `PATCH_GAME_RUNTIME_MINIMAL_V08`（+ 32×32 VRAM Viewer）

---

## 2. ドキュメント整理

- [x] `PATCH_V08_STABILIZE_AND_DOCS_ROADMAP.md` 作成
- [x] `PATCH_V08_STABILIZE_AND_DOCS_CHECKLIST.md` 作成（本書）
- [x] `ROADMAP8.md` を v0.8 完了状態に最小更新（STABILIZE 実施・テーマ完了・v0.9 候補）
- [x] `CHECKLIST8.md` を v0.8 完了状態に最小更新（STABILIZE 実施・古い計画項目を完了/送り整理）
- [x] `HANDOFF.md` に v0.8 完了直前の到達点を追記
- [x] `README.md` を必要最小限更新（v0.8 デバイス / 実行機能 / テスト方法・Status を v0.8 へ）
- [x] 既存のパッチ履歴を消していない（追記・状態更新のみ）
- [x] 見出し重複を作っていない

---

## 3. 最終検証（2026-06-23）

- [x] `python -m pytest tests/` → **1182 passed**（21 warnings は PySide6 Deprecation のみ）
- [x] `git diff -- tests/test/system.json` → 差分なし
- [x] `grep -c "# AKDev ROADMAP 8" ROADMAP8.md` → 1（重複なし）
- [x] `ROADMAP8.md` / `CHECKLIST8.md` / `HANDOFF.md` / `README.md` の記述が実装と矛盾しない
- [ ] GUI 目視（VRAM Viewer 表示・Run Status 行）— **ヘッドレスのため未実施**（ロジックは pytest で検証済み）
- [x] commit / push を行っていない

---

## 4. v0.9 へ送る候補

- [ ] `PATCH_AK32_BRANCH_EXPANSION_V08`（`BNE` / `BEQZ` / `BNEZ`）
- [ ] `PATCH_AK32_SHIFT_IMM_BITWISE_V08`（`SHL` / `SHR` / `ANDI` / `ORI`）
- [ ] `PATCH_AK32_STACK_CALL_RET_V08`（stack / `CALL` / `RET`）
- [ ] VRAM Viewer 拡張（palette / 色 / 拡大率 UI）
- [ ] Game Runtime 拡張（フレーム同期 / 入力エッジ / ゲームループ）
- [ ] sprite / tile / palette 本格実装
- [ ] HDL / FPGA export 準備
- [ ] project template / sample project
- [ ] save / load 強化（loaded_program 永続化拡張）
- [ ] 繰越: `tests/test/system.json` 差分の扱いをユーザーが決定（破棄 / コミット / .gitignore 化）
- [ ] 複数 RAM の真の共存（16bit アドレス制約・ROADMAP8 候補 F）

---

## 5. 完了条件

- [x] STABILIZE の ROADMAP / CHECKLIST を作成した
- [x] `ROADMAP8.md` / `CHECKLIST8.md` が v0.8 完了状態
- [x] `HANDOFF.md` が現在状態に更新
- [x] `README.md` を最小更新（または不要と判断）
- [x] v0.9 候補が整理されている
- [x] 全テスト green・system.json 差分なし・見出し重複なし
- [x] commit / push を行っていない
- [ ] ユーザーの `PHASE COMPLETE` 宣言を待つ（`old/` 収納・次フェーズ資料作成は宣言後）

---

## メモ

- 本パッチは **ドキュメントと検証のみ**。コード（core/ui/asm/tests）は一切変更していない。
- `PHASE COMPLETE` 処理（`old/` 収納・`ROADMAP9.md`/`CHECKLIST9.md` 作成）は**ユーザー宣言後**に行う（CLAUDE.md §4）。
- GUI 目視はヘッドレス環境のため未実施。表示ロジックは `tests/test_game_runtime_minimal_v08.py` 等で検証済み。
