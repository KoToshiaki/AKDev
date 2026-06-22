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

## 2. 実装予定（**今回は未実装**）

- [ ] viewer または dump 表示（`ui/vram_viewer.py` 新規 / 案 A 縮退時は dump テストのみ）
- [ ] MainWin 連携（viewer dock 生成・`self._sim_vram` を viewer に渡す）
- [ ] Step/Run/Reset 後 refresh（`_refresh_run_panels()` に viewer render を 1 行追加）
- [ ] demo / sample program（ROADMAP §5 の Demo 1〜4・実番地を Address Map で確認後に焼く）
- [ ] tests 追加（`tests/test_game_runtime_minimal_v08.py`）
- [ ] docs 更新（本 CHECKLIST・`ROADMAP8.md`/`CHECKLIST8.md` 最小追記・`HANDOFF.md`）

---

## 3. テスト予定（**今回は未追加**）

- [ ] ROM + Input + Timer + VRAM を同時配置できる（game16・4 device）
- [ ] game16 layout で overlap しない（`validate_address_map(amap) == []`）
- [ ] ROM target から実行して VRAM に書ける
- [ ] Timer 値を VRAM に書ける（Demo 3）
- [ ] Input 値を VRAM に書ける（`set_keys` + Demo 2）
- [ ] Run 後に VRAM 内容が変わる（Demo 4 雛形）
- [ ] Viewer を入れるなら viewer refresh 確認（render 後に viewer が VRAM と一致）
- [ ] VRAM 未配置時は既存互換（viewer 空・Hello World 従来通り）
- [ ] 既存 tests（Hello World / Input / Timer / VRAM / ROM / Program Target / Bitwise）が壊れない

---

## 4. 検証予定（**今回は未実施**）

- [ ] `python -m pytest tests/` 全通過
- [ ] sample program 動作（Run 後に VRAM が想定値）
- [ ] `tests/test/system.json` 差分なし
- [ ] GUI 目視（viewer の見た目）— ヘッドレス環境では**未実施として記録**する

---

## 5. 完了条件（設計資料として）

- [x] Game Runtime Minimal の範囲が明確（構成 + sample + 最小表示・新 runtime class なし）
- [x] Viewer を含めるか分離するか明確（**含める案 B が第一候補・肥大化時は分離**）
- [x] v0.8 を閉じる直前の状態が明確（VRAM device → Game Runtime Minimal → Stabilize）
- [x] 次の実装指令に進める（ROADMAP §8 の実装スコープが具体的）

---

## メモ

- 本パッチは**既存命令だけで成立**する（`BNE`/shift/`CALL`/`RET` は不要・後続パッチ）。
- viewer は **VramPart.dump()/pixel() を読むだけ**で VRAM 本体に触れない。
- **commit / push は行わない**（設計資料のみ）。
