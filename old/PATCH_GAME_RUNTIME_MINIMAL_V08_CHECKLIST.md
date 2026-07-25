# PATCH_GAME_RUNTIME_MINIMAL_V08 — CHECKLIST

> v0.8 の最終到達点候補。ROM + Input + Timer + VRAM を組み合わせた最小ゲーム実行環境。
> 本書は**設計資料**。**実装・UI 実装・Game Runtime 実装・VRAM Viewer 実装・CPU 命令追加・ASM 変更・テスト追加・既存挙動変更・commit/push は行わない。**
> 設計詳細: `PATCH_GAME_RUNTIME_MINIMAL_V08_ROADMAP.md`。親計画: `ROADMAP8.md` / `CHECKLIST8.md`。

---

## 0. 事前確認（設計時点で確認済み）

- [x] `git status --short` を確認（途中差分は本パッチの ROADMAP のみ・範囲内）
- [x] `git branch --show-current` = `dev`
- [x] baseline test 確認: `python -m pytest tests/` → **1164 passed**
- [x] VRAM 完了確認: `PATCH_VRAM_DEVICE_V08` コミット済み（`b7b7a35 feat: add vram device`）・`VramPart` 実装済み（`core/dev.py:326`）
- [x] Timer / Input / ROM / Program Target / Bitwise 完了確認（git log・各 device test 緑）
- [x] game16 layout 確認: ROM 0x0000/0x8000・RAM 0x8000/0x4000・VRAM 0xC000/0x0400・MMIO 0xE000（`core/devices.py:75-80`）
- [x] Run/Step 確認: `_do_step`/`_do_run`/`_refresh_run_panels`（`ui/win.py:1466`/`1483`/`1415`）
- [x] `tests/test/system.json` 差分なし確認
- [x] `ROADMAP8.md` 見出し重複なし確認（`# AKDev ROADMAP 8` は 1 箇所）

---

## 1. 設計（本パッチで決定済み）

- [x] **Game Runtime Minimal 仕様**: 新 runtime class を足さず、既存 Run/Step の上に「demo 構成 + sample program + VRAM 表示 + refresh hook」の薄い層を載せる（ROADMAP §3）
- [x] **Viewer を含めるか**: **含める（案 B 第一候補）**。32×32 framebuffer・グレースケール・`_refresh_run_panels()` で更新。**UI が肥大化したら `PATCH_VRAM_VIEWER_V08` に分離**（ROADMAP §4 のフォールバック条件）
- [x] **Sample Program 方針**: 既存命令のみ。Demo 1（固定値）/ 2（Input）/ 3（Timer）/ 4（最小ループ）（ROADMAP §5）
- [x] **Memory Layout 方針**: game16 標準（ROM 0x0000 / RAM 0x8000 / VRAM 0xC000 / MMIO 0xE000）。circuit_compat + override 経路も互換維持。MMIO 実番地は配置順依存（`assign_mmio_bases`）（ROADMAP §6）
- [x] **UI 方針**: VRAM viewer 1 個・Run Status は最小追記まで・既存 UI を大きく壊さない（ROADMAP §7）
- [x] **CPU/ASM 方針**: 命令追加なし・ASM 変更なし・既存命令のみ（ROADMAP §9）
- [x] **テスト方針**: ROM+Input+Timer+VRAM 同時配置・VRAM 更新・viewer refresh・既存互換（ROADMAP §10）
- [x] **既存互換方針**: VRAM 未配置で無害・system.json 差分なし・全 test 通過（ROADMAP §11）

---

## 2. 実装済み（2026-06-23）

- [x] viewer 表示（`ui/vram_viewer.py` 新規・`VramViewer(QDockWidget)`・32×32 グレースケール・`snapshot()`/`pixel()`/`is_active()`）
- [x] MainWin 連携（`_setup_vram_viewer` で dock 生成・Memory Viewer とタブ化・`self._sim_vram` を viewer に渡す）
- [x] Step/Run/Reset/Write 後 refresh（`_refresh_run_panels()` + `_do_reset` + `write_program` に `_update_vram_viewer()` を追加）
- [x] demo / sample program（テスト内に Demo 1〜4 を ASM 文字列で保持・Input/Timer の実番地は `self._sim_input.base`/`self._sim_timer.base` から取得して焼く）
- [x] Run Status 最小追記（`Game: ROM+Input+Timer+VRAM` 行・`_collect_run_status` の `game` キー + `render_status`）
- [x] tests 追加（`tests/test_game_runtime_minimal_v08.py`・18 件）
- [x] docs 更新（本 CHECKLIST・`ROADMAP8.md`/`CHECKLIST8.md` 最小追記・`HANDOFF.md`）

---

## 3. テスト結果（2026-06-23・全 18 件 green）

- [x] ROM + Input + Timer + VRAM を同時配置できる（`test_rom_input_timer_vram_coexist`）
- [x] game16 layout で overlap しない（`test_game16_*_non_overlapping`・`validate_address_map == []`）
- [x] game16 MMIO base = UART 0xE000 / Input 0xE010 / Timer 0xE020（`test_game16_mmio_bases_uart_input_timer`）
- [x] ROM target から実行して VRAM に書ける（`test_rom_target_writes_vram`）
- [x] Timer 値を VRAM に書ける（`test_timer_value_written_to_vram`）
- [x] Input 値を VRAM に書ける（`set_input_keys` + `test_input_value_written_to_vram`）
- [x] Run 後に VRAM 内容が変わる（`test_run_changes_vram_loop`・JMP 無限ループ → 1000 cycle cap）
- [x] viewer refresh で VRAM 内容が反映される（`test_viewer_refreshes_after_run`・`snapshot()==dump()`）
- [x] viewer は VRAM 本体を変更しない（`test_vram_viewer_does_not_mutate_vram`）
- [x] VRAM 未配置時は既存互換（`test_plain_circuit_unaffected`・`test_legacy_window_viewer_inactive`）
- [x] 既存 tests（Hello World / Input / Timer / VRAM / ROM / Program Target / Bitwise）が壊れない

---

## 4. 検証結果（2026-06-23）

- [x] `python -m pytest tests/` 全通過（**1182 passed**・1164 + 新規 18）
- [x] sample program 動作（Run 後に VRAM が想定値: 固定 0xAA / Input 0x05 / Timer 非ゼロ / loop 変化）
- [x] `tests/test/system.json` 差分なし
- [ ] GUI 目視（viewer の見た目）— **ヘッドレス環境のため未実施**。表示ロジックは `snapshot()`/`pixel()` で検証済み

---

## 5. 完了条件（設計資料として）

- [x] Game Runtime Minimal の範囲が明確（構成 + sample + 最小表示・新 runtime class なし）
- [x] Viewer を含めるか分離するか明確（**含める案 B が第一候補・肥大化時は分離**）
- [x] v0.8 を閉じる直前の状態が明確（VRAM device → Game Runtime Minimal → Stabilize）
- [x] 次の実装指令に進める（ROADMAP §8 の実装スコープが具体的）

---

## メモ

- 本パッチは**既存命令だけで成立**した（`BNE`/shift/`CALL`/`RET` は未使用・後続パッチ）。CPU 命令追加・ASM 変更なし。
- viewer は **VramPart.dump()/pixel() を読むだけ**で VRAM 本体に触れない（`test_vram_viewer_does_not_mutate_vram` で保証）。
- **viewer は本パッチに含めた（案 B）**。実装は `QDockWidget + QLabel + QImage` の薄い層で肥大化しなかったため分離不要と判断。
- 新 `GameRuntime` class は追加せず、既存 `VirtualCircuitRuntime` / `_do_run` / `_do_step` をそのまま使用。
- MainWin は circuit_compat を自動選択するため、統合テストは **circuit_compat + Address Map override** で配置（game16 は unit レベルで検証）。
- **commit / push は行っていない**（報告のみ）。
