# PATCH_V08_STABILIZE_AND_DOCS — ROADMAP（v0.8 最終整理）

> v0.8（**Device Expansion & Connection Validation**）を閉じるための **安定化・ドキュメント整理・最終検証**パッチ。
> **新機能追加・CPU 命令追加・ASM 変更・Game Runtime 拡張・VRAM Viewer 拡張・sprite/tile/palette・HDL/FPGA export は行わない。**
> **大規模リファクタ・テスト期待値の無意味な変更・`tests/test/system.json` 変更・commit/push も行わない。**
> 親計画: `ROADMAP8.md` / `CHECKLIST8.md`。前 PHASE: `old/ROADMAP7.md`（✅ v0.7 PHASE COMPLETE）。

---

## 1. 目的

- v0.8 で実装した一連のパッチ（接続検証 + デバイス拡張 + 最小ゲーム runtime）を整理し、**v0.8 を完了状態**にする。
- ドキュメント（`ROADMAP8.md` / `CHECKLIST8.md` / `HANDOFF.md` / `README.md`）を現状と一致させる。
- 全体テストを最終実行し、`tests/test/system.json` に差分がないことを確認する。
- v0.9 以降へ送る候補を明文化する。
- **本パッチはコードを変更しない**（ドキュメントと検証のみ）。PHASE COMPLETE の下準備に相当するが、`PHASE COMPLETE` 宣言自体はユーザーが行う。

---

## 2. v0.8 で完了したパッチ一覧（実装順）

| # | パッチ | 内容 | 完了時 pytest |
|---|---|---|---|
| 1 | `PATCH_PORT_SCHEMA_V08` | part.json ports schema v2 正規化 | 878 |
| 2 | `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08` | 接続時 direction/width 検証（warning only） | 913 |
| 3 | `PATCH_BUS_PROTOCOL_VALIDATION_V08` | bus master/slave 数診断（warning only） | 937 |
| 4 | `PATCH_DEVICE_REGISTRY_REFACTOR_V08` | device spec/list 駆動化・VRAM≠RAM 土台（挙動不変） | 957 |
| 5 | `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08` | 複数 UART/MMIO 配置・複数 RAM warning・`resolve_circuit` を kind ベースへ | 973 |
| 6 | `PATCH_CODE_REGION_MMIO_RELOCATION_V08` | `MemoryLayout`（LEGACY/CIRCUIT_COMPAT/GAME16）・layout aware 化 | 988 |
| 7 | `PATCH_ADDRESS_MAP_EDITOR_V08` | per-device base/size override UI・auto/manual・persist | （+） |
| 8 | `PATCH_INPUT_DEVICE_V08` | MMIO Input・`sim_input`・既存 `LD` で読む | （+） |
| 9 | `PATCH_ROM_DEVICE_V08` | read-only memory・`RomPart`・`MemoryLayout.rom_*` | （+） |
| 10 | `PATCH_PROGRAM_TARGET_ROM_V08` | program target RAM/ROM 切替・ROM target は `reset_pc=rom.base` | 1080 |
| 11 | `PATCH_AK32_BITWISE_INSTRUCTIONS_V08` | `AND`/`OR`/`XOR`/`NOT`（opcode 0x0B–0x0E）・Input bit 判定 | 1111 |
| 12 | `PATCH_TIMER_DEVICE_V08` | MMIO Timer・deterministic tick・既存 `LD`/`ST` | 1136 |
| 13 | `PATCH_VRAM_DEVICE_V08` | writable framebuffer・`VramPart`・32×32/1B/px・既存 `LD`/`ST` | 1164 |
| 14 | `PATCH_GAME_RUNTIME_MINIMAL_V08` | ROM+Input+Timer+VRAM 最小ゲーム runtime + 32×32 VRAM Viewer | **1182** |

設計のみ（実装は分割パッチが担当）: `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08`（ROM/Input 親設計）、`PATCH_AK32_INSTRUCTION_EXPANSION_V08`（AK32 ISA 拡張 親設計）。

---

## 3. v0.8 の到達点

v0.7 の実行基盤（Plan-driven Devices / Address Map / Run Status / Port Detail）の上に、以下が積み上がった。

- **接続検証**: ports schema v2、direction/width 検証、bus protocol 検証（いずれも warning only — 接続はブロックしない）。
- **デバイス拡張**: Input / ROM / Timer / VRAM を plan-driven で追加（v0.7 の RAM/UART と同方式）。VRAM は RAM とは別 kind として正しく分類される。
- **メモリ構成**: `MemoryLayout`（LEGACY / CIRCUIT_COMPAT 既定 / GAME16）で RAM/ROM/VRAM/MMIO の base/size を可変化。Address Map Editor で per-device override。
- **実行**: program target を RAM / ROM で切替（ROM target は ROM から fetch）。
- **CPU**: AK32 に Bitwise（`AND`/`OR`/`XOR`/`NOT`）を追加。Input bit 判定が可能に。
- **最小ゲーム実行環境**: ROM + Input + Timer + VRAM を同時配置し、ROM target から実行して Input/Timer を `LD` で読み VRAM へ `ST` で描画。**32×32 グレースケール VRAM Viewer** が Step/Run/Reset/Write 後に更新。
- **互換**: 新デバイスを置かない既存 project は完全互換。legacy mode（CPU 未配置）は従来動作維持。

**最終テスト**: `python -m pytest tests/` → **1182 passed**（21 warnings は PySide6 Deprecation のみ）。`tests/test/system.json` 差分なし。

### GUI 目視確認（ヘッドレスのため未実施・PHASE COMPLETE 後にユーザー確認推奨）

1. ROM+Input+Timer+VRAM を配線し override 配置 → ROM target で Write → Run で VRAM Viewer が更新される。
2. VRAM Viewer に 32×32 グレースケールが拡大表示される。
3. Run Status に `Timer:` / `VRAM:` / `Game:` 行が出る。
4. VRAM 非配置の既存 project で Viewer が `VRAM: None`・従来通り動く。
5. Address Map Editor で base/size override → overlap 検出。

---

## 4. v0.8 でやらないこと（本パッチの非対象）

- 新機能追加・CPU 命令追加・ASM/opcode 変更。
- Game Runtime 拡張・VRAM Viewer 拡張・sprite/tile・palette 本格実装・audio・DMA/GPU・physics・asset system。
- HDL / FPGA export・project template 本格実装。
- 大規模リファクタ・テスト期待値の無意味な変更・`tests/test/system.json` 変更。
- commit / push。

---

## 5. v0.9 以降へ送る候補

- **AK32 branch 拡張** `PATCH_AK32_BRANCH_EXPANSION_V08`（`BNE` / `BEQZ` / `BNEZ`）。
- **shift / immediate bitwise** `PATCH_AK32_SHIFT_IMM_BITWISE_V08`（`SHL` / `SHR` / `ANDI` / `ORI`）。
- **stack / CALL / RET** `PATCH_AK32_STACK_CALL_RET_V08`（stack 設計が必要）。
- **VRAM Viewer 拡張**（palette / 色 / 拡大率 UI / グリッド）。
- **Game Runtime 拡張**（フレーム同期・入力エッジ・スコア・本格ゲームループ・複数 VRAM）。
- **sprite / tile / palette**（本格グラフィクス）。
- **HDL / FPGA export 準備**（回路 → HDL 出力・合成・実機書き込み）。
- **project template / sample project**（ゲーム雛形・サンプル一式）。
- **save / load 強化**（loaded_program 永続化拡張・プロジェクト移植性）。
- **繰越**: `tests/test/system.json` のテスト実行差分の扱い（破棄 / コミット / .gitignore 化）をユーザーが決定。
- **複数 RAM の真の共存**（16bit アドレス制約のため設計要・ROADMAP8 候補 F）。

> v0.8 を閉じる方針のため、命令拡張（Branch/Shift/Stack）と本格グラフィクス・HDL は **v0.9 以降**に送る。

---

## 6. 最終検証項目

- [ ] `python -m pytest tests/` → 全件 green（期待 1182 passed）。
- [ ] `git diff -- tests/test/system.json` → 差分なし。
- [ ] `ROADMAP8.md` の `# AKDev ROADMAP 8` 見出しが 1 個（重複なし）。
- [ ] `ROADMAP8.md` / `CHECKLIST8.md` が v0.8 完了状態（最新パッチ + STABILIZE 反映）。
- [ ] `HANDOFF.md` に v0.8 完了直前の到達点が記録されている。
- [ ] `README.md` が現状と大きくズレていない（v0.8 デバイス / 実行機能 / テスト方法）。
- [ ] commit / push を行っていない。

---

## 7. 完了条件

- `PATCH_V08_STABILIZE_AND_DOCS_ROADMAP.md` / `..._CHECKLIST.md` を作成した。
- `ROADMAP8.md` / `CHECKLIST8.md` が v0.8 完了状態になっている。
- `HANDOFF.md` が現在状態に更新されている。
- `README.md` が必要最小限更新されている（または更新不要と判断・記録）。
- v0.9 へ送る候補が整理されている。
- 全テスト green・`tests/test/system.json` 差分なし・見出し重複なし。
- commit / push を行っていない。
- ユーザーの `PHASE COMPLETE` 宣言を待つ（`old/` への収納・次フェーズ ROADMAP/CHECKLIST 作成は宣言後）。

---

## 8. PHASE COMPLETE 後にユーザー / 次作業が行うこと（参考・本パッチでは未実施）

> CLAUDE.md §4 のフェーズ完了処理。**`PHASE COMPLETE` が出るまで実施しない。**

1. v0.8 関連ファイルの最終確認（ROADMAP8 / CHECKLIST8 / HANDOFF / 各 PATCH 資料）。
2. 全機能の総合確認（pytest 全件・GUI 目視）。
3. 完了した v0.8 の `ROADMAP8.md` / `CHECKLIST8.md` と `PATCH_*_V08_*` 資料を `old/` へ収納。
4. `HANDOFF.md` を v0.8 PHASE COMPLETE として更新。
5. 次フェーズ `ROADMAP9.md` / `CHECKLIST9.md` を作成（v0.9 候補整理・実装は未着手）。
6. commit / push（ユーザー操作）。
