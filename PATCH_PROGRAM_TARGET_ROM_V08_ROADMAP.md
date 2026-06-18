# PATCH_PROGRAM_TARGET_ROM_V08 — ROADMAP（設計資料）

> v0.8（Device Expansion & Connection Validation）の次パッチ候補。
> `PATCH_ROM_DEVICE_V08` で追加した ROM device を、実際の **program target（プログラム格納先）** として使うための設計。
> 本書は設計のみ。**実装・テスト追加・part.json 追加・system.json 変更・Program loader 変更・既存挙動変更・commit/push は行わない。**
> 親計画: `ROADMAP8.md` / `CHECKLIST8.md`。所見: `V08_CODEBASE_REVIEW.md`。
> 前提: v0.8 の `PATCH_PORT_SCHEMA_V08` 〜 `PATCH_ROM_DEVICE_V08` 完了（`python -m pytest tests/` 1059 passed）。

---

## 1. 目的

- Write Program のロード先を **RAM / ROM** で選べるようにする（program target）。
- `PATCH_ROM_DEVICE_V08` で追加した ROM device を、実際の program target として使えるようにする。
- ROM target 時は `RomPart.load_bytes()` でプログラムを ROM に書き込む（CPU/bus 経由ではない）。
- CPU/bus からの ROM write は引き続き **no-op**（read-only を維持）。
- ROM target 時の `reset_pc` を **ROM base** に合わせ、ROM からの fetch を可能にする。
- **既定は RAM target** のままにして既存互換を維持する（既存 project / Hello World / ram_selftest / legacy 不変）。
- 今回は **設計のみ**。実装・既存挙動変更・loader 変更はしない。

### スコープ（明確化）

`program_target`（`ram` / `rom`）の選択・永続化・loader 分岐・reset_pc 連動・最小 UI/API・error handling まで。
CPU 命令拡張・ASM 拡張・`ORG` / section / linker・game16 自動切替・ROM-only 実行の本格化・VRAM/Timer は対象外。

---

## 2. 現在の到達点

- **ROM device は実装済み**（`PATCH_ROM_DEVICE_V08`）。`parts/mem/rom/part.json` / `RomPart` / `sim_rom` / Address Map 統合まで完了。
- `RomPart`（`core/dev.py`）は **read-only**:
  - `read(addr)`: 32bit LE word（RAM 同様の `_offset` ベース・範囲外は `BusError`）。
  - `write(addr, value)`: **no-op**（例外なし）。
  - `reset()`: **内容を保持**（RAM は 0 クリア、ROM は不変）。
  - `load_bytes(data, offset=0)`: ROM image を設定（サイズ超過は `ValueError`）。`dump()` あり。
  - `base` / `size` を持つ。
- `MemoryLayout`（`core/devices.py`）に `rom_base` / `rom_size`（既定 None）がある。
  - `GAME16`: `rom_base=0x0000` / `rom_size=0x8000`（RAM 0x8000–0xBFFF）。
  - `CIRCUIT_COMPAT` / `LEGACY`: `rom_base=None`（ROM 領域なし。Editor override で配置）。
- `MainWin._build_runtime_devices`（`ui/win.py`）は **base がある ROM のみ** `self._sim_rom` / `self._sim_rom_node` として runtime 化する。
  circuit_compat で override が無いと ROM は未配置（`_sim_rom` は None）。
- **CPU 構築は `AK32Part("sim_cpu", "AK32", self._sim_bus, reset_pc=layout.reset_pc)`**（`ui/win.py:276`）。
  `AK32Part`（`core/cpu.py`）は `reset_pc` を構築時に固定し、`reset()` で `_pc=_reset_pc` に戻す。**reset_pc を変える setter は無い**。
- **Write Program は今も RAM ロード**:
  - `write_program()` → `_bind_circuit_runtime(plan)`（= `_make_sim` → `_build_runtime_devices` で device 再構築）→
    `_assemble_and_load(text, name, root)` → `assemble_ex(text)` → **`self._runtime.load_program(binary)`**。
  - `VirtualCircuitRuntime.load_program`（`core/runtime.py:91`）は **`self.ram.reset()` + `self.ram.load_bytes(binary)` + `self.cpu.reset()` を hardcode**。ROM には触れない。
- `_bind_circuit_runtime` は Write/Build の度に device を作り直す（Run/Step は作り直さない）。
  → **ROM target の reset_pc は「CPU を作り直す時に `reset_pc=rom.base` で構築する」方式が自然**（既存の rebuild 導線に乗る）。
- 永続化は `_persist_system`（`ui/win.py:959`）→ system.json に `parts` と `address_map_overrides` を書く。
  `load_project(root)` が `(project, system)` を返し、`self._address_overrides = system.get("address_map_overrides")`。
  → **`program_target` は同じ仕組み（`self._program_target` ↔ `system["program_target"]`）で扱える**。
- つまり「ROM にプログラムを入れて reset_pc を ROM base にすれば ROM 実行できる」**土台は既に揃っている**。
  足りないのは loader 分岐・reset_pc 連動・target 選択/永続化・UI/API・error handling。

---

## 3. program target 仕様

| target | 動作 | reset_pc | 有効条件 |
|---|---|---|---|
| `ram`（既定） | Write Program は `RamPart.load_bytes()`（現行 `runtime.load_program`） | 現行どおり `layout.reset_pc`（既定 0x0000） | 常に有効（現行互換） |
| `rom` | Write Program は `RomPart.load_bytes()` | `self._sim_rom.base`（ROM base） | ROM runtime が存在し base/size 確定時のみ |
| `auto`（後続候補） | ROM runtime ありなら ROM、無ければ RAM | target に応じる | 今回はやらない（将来検討） |

- **既定は `ram`**。
- **`ram`**:
  - 現行互換。Write Program は RAM へロード（`runtime.load_program`）。
  - reset_pc は現行どおり。RAM が作業領域 兼 program 領域。
- **`rom`**:
  - **ROM runtime（`self._sim_rom`）が存在し、base/size が確定しているときのみ有効**。
  - Write Program は `RomPart.load_bytes()` で ROM image を設定。
  - reset_pc は ROM base（`self._sim_rom.base`）。
  - **RAM は作業領域として残す**（RAM device は引き続き必要。ROM-only 実行は今回扱わない）。
- **`auto`**: 後続候補。今回は **やらない案**を採る（仕様の余地だけ残す）。

---

## 4. Project 設定 / 永続化方針

- **system.json に `program_target` を追加**（`address_map_overrides` と同じ仕組み）。
  - `program_target: "ram" | "rom"`。
  - キーが無い既存 project は **`ram` 扱い**（完全互換）。
  - 不正値（`"rom2"` 等）は **`ram` にフォールバック**（ログに warning）。
- MainWin 側に `self._program_target`（既定 `"ram"`）を持ち、`_persist_system` で `system["program_target"]` に書く。
- `_open_project` 復元時: `self._program_target = _normalize_target(system.get("program_target"))`（無 / 不正 → `ram`）。
- `_new_project` / `_save_project_as`: `self._program_target = "ram"`（新規は RAM 既定）。
- round-trip 互換: 既存 project（`program_target` 無し）を開いて保存しても挙動は RAM。保存後に `program_target: "ram"` が増えるが、
  **既存テストの system.json fixture（`tests/test/system.json`）は触らない**（保存導線を通さない限り差分は出ない）。
- 将来 `auto` を入れる場合も、`_normalize_target` の許容集合を広げるだけで後方互換に済む設計にする。

> 注: 現行の `_persist_system` は load→update→save 方式なので、未知キー（将来追加）は基本保持される。`program_target` も同様に明示 set する。

---

## 5. UI 方針

- **最小実装では MainWin に状態（`self._program_target`）+ API を追加し、UI は小さく**。
- 可能なら Run/Debug 付近（Run panel / Debug ribbon / toolbar）に `Program Target: RAM / ROM` の ComboBox を置く。
  - 既定は **RAM**。
  - ROM が無い、または ROM base/size が未配置（`self._sim_rom is None`）なら **ROM 選択を無効化 or warning 表示**。
  - 現在の effective target を status（Run Status / `_program_target_status()`）に出す。
- ComboBox 変更 → `set_program_target("rom")` → 永続化（`_persist_system`）+ status 更新。
- Write Program ボタン横の small selector でも可（実装簡便な側を選ぶ）。
- **UI が無くても API（`set_program_target` / `program_target`）だけでテスト可能**にしておく（テスト容易性優先）。

---

## 6. loader 方針

現行 Write Program の流れ（§2 参照）を踏まえ、**分岐点は 2 つ**:

1. **device 構築時の reset_pc**（`_build_runtime_devices`）— §7。
2. **binary のロード先**（`_assemble_and_load` → loader）。

### RAM target（既定・現行維持）

- 既存どおり `self._runtime.load_program(binary)`（RAM へロード・CPU reset）。**一切変更しない**。

### ROM target

- `self._sim_rom.load_bytes(binary)` で ROM image を設定。
- その後 CPU/UART/bus を reset（RAM は作業領域なので 0 クリアでよい）。
- **`runtime.load_program` は RAM 前提なので、ROM 用の別経路が要る**。案:
  - (A) MainWin 側に `_load_program_to_rom(binary)` を作り、`load_bytes` → `cpu.reset()` / `uart.reset()` / `bus.clear_trace()` 等を呼ぶ。
    `runtime.load_program` には手を入れず、`_assemble_and_load` で target により呼び分け（**推奨・既存 RAM 経路を完全保全**）。
  - (B) `runtime.load_program(binary, target="rom")` に引数を足す。runtime が ROM を知る必要があり結合が増える。
  - → **推奨は (A)**: loader 分岐は MainWin（`_assemble_and_load`）に閉じ、`runtime.load_program` は RAM 専用のまま温存。
- ROM サイズ超過は **error**（`RomPart.load_bytes` が `ValueError` を投げる → 捕捉して Log/status）。
- ROM runtime が無い / base 未確定なら **error**（後述 §11）。RAM へ勝手に fallback しない（明示 error で気付ける）。

### target 変更時の rebuild

- Write Program は毎回 `_bind_circuit_runtime` で device を作り直すので、**target 変更後の次 Write Program で reset_pc は自動的に反映**できる。
- target 変更だけで即 CPU を作り直す必要は無い（次の Write Program 時に確定で十分）。ただし status 表示は即更新する。

### 重要（不変条件）

- CPU/bus の ROM write は **no-op のまま**（ST/OUT で ROM に書いても黙って無視）。
- **IDE loader（`load_bytes`）だけ ROM 内容を入れられる**。
- RAM target 時の既存挙動は **1 命令も変えない**。

---

## 7. reset_pc 方針

- CPU 作成は `AK32Part("sim_cpu", "AK32", bus, reset_pc=...)`（`_build_runtime_devices`）。`reset_pc` は構築時固定。
- 方針:
  - `program_target == "rom"` かつ ROM runtime（base 確定）あり → **`reset_pc = self._sim_rom.base`**。
  - それ以外（`ram` / ROM 未確定） → 現行どおり **`reset_pc = layout.reset_pc`**。
- 実装上の選択肢:
  - (A) `_build_runtime_devices` で ROM spec の base を見て CPU の reset_pc を決める（**推奨・rebuild 導線に自然に乗る**）。
    - ただし ROM spec は CPU spec より後に来ることがあるため、ROM base を**先に確定**してから CPU を構築する（2 パス、または ROM base を先に走査）。
  - (B) `AK32Part` に `set_reset_pc(pc)` を足し、ロード時に更新 + reset。CPU は再構築しない案。結合は小さいが CPU API 追加。
  - → **推奨は (A)**。CPU API を増やさず、既存 rebuild 内で reset_pc を決める。
- ROM target なのに ROM base が無い場合: **RAM fallback はしない**。ロード時に **error**（target 設定と配置の不整合を明示）。
- tests で「ROM base からプログラムが fetch される（CPU.pc() が ROM base で始まり ROM の命令を実行）」ことを確認する。
- 既存 RAM target は `reset_pc=layout.reset_pc`（既定 0x0000）で完全互換。

---

## 8. Address Map / Layout との関係

- **circuit_compat で ROM を program target にするには Editor override が必須**（layout に rom 領域が無く、RAM が 64KB 全域 →
  override で ROM base/size を与え、RAM を縮小して overlap を避ける）。
  - override が無く ROM 未配置のまま ROM target を選んだら **error**（ROM 配置を促す）。
- **game16 では ROM 0x0000 / RAM 0x8000** で自然に program target=ROM が成立（reset_pc=0x0000＝ROM base）。
- **ROM/RAM overlap がある構成では Program Target=ROM を許可しない**（既存の `ADDRESS_OVERLAP` error と連動）。
  Address Map validation が error の間は ROM ロードをブロックする。
- ROM size を超えるプログラム: `RomPart.load_bytes` の `ValueError` を error として扱う（§11）。
- Address Map validation 結果と loader を連動: validation error 時は Write Program（ROM target）を実行しない。

---

## 9. CPU / ASM との関係

- **CPU 命令追加はしない**。ROM fetch は既存 `bus.read(pc)` で可能。
- **ASM 拡張はしない**。`ORG` / section / linker は後続（`PATCH_AK32_INSTRUCTION_EXPANSION_V08` 以降）。
- ROM target 時も **現行アセンブル結果（`assemble_ex`）を ROM base + 0 へロード**する（binary の先頭を ROM base に置く）。
  - `address_map`（行 → PC マップ）の扱い: 現行は RAM base=0x0000 前提で PC=オフセット。ROM base が 0x0000 の game16 ではそのまま整合。
  - circuit_compat で ROM base を 0x2000 等にした場合、`LDI/JMP` の絶対アドレスや `address_map` のキー（PC）が ROM base ずれと
    食い違う可能性がある。**今回は base=0x0000 ケース（game16）を主対象**とし、非ゼロ base は「reset_pc は合わせるが絶対アドレスは
    アセンブラ任せ」である旨を明記（linker は後続）。
- game16 ではコードは 0x0000 開始なので現状の絶対 JMP/LDI と相性が良い。
- circuit_compat で ROM base を 0x2000 等にした場合は **reset_pc と絶対 JMP に注意**（ユーザーが ORG 相当をコードで意識する必要。
  本パッチでは linker を入れないので「非ゼロ ROM base は実験的」とドキュメントに残す）。

---

## 10. runtime / API 設計

MainWin（`ui/win.py`）に以下を追加（候補・命名は既存に倣う）:

- `self._program_target: str`（既定 `"ram"`）。
- `set_program_target(target: str) -> None`: 正規化して set・永続化・status 更新（UI/テストの入口）。
- `program_target() -> str`: 現在の生 target を返す。
- `_program_target_effective() -> str`: ROM 不成立なら `"ram"` 扱いを返す（または error 判定用）。実際のロードに使う実効値。
- `_program_target_status() -> str`: 表示用文字列（例 `"RAM"` / `"ROM @0x0000"` / `"ROM (unplaced)"`）。
- `_load_program_to_ram(binary)`: 現行 `runtime.load_program` を呼ぶ薄いラッパ（既存挙動）。
- `_load_program_to_rom(binary)`: `self._sim_rom.load_bytes(binary)` + reset 系（§6 案 A）。
- `_normalize_target(value) -> str`: 無 / 不正 → `"ram"`。
- 既存の `self._sim_rom` / `self._sim_rom_node` を利用（`PATCH_ROM_DEVICE_V08` で追加済み）。
- error / 不成立は Log（`self._log.append`）+ status に出す。

> runtime（`VirtualCircuitRuntime`）には ROM を渡さない案（loader 分岐は MainWin 側）。runtime API は温存（§6 案 A）。

---

## 11. エラー / 診断方針

| 状況 | 扱い | 出力先 |
|---|---|---|
| ROM device がない（canvas に ROM 無し） | ROM target 選択不可 / ロード時 error | status（無効化）+ Log |
| ROM が Address Map 未配置（`_sim_rom is None`・base 無し） | ロード時 error（配置を促す） | Log + message box |
| ROM/RAM overlap がある（`ADDRESS_OVERLAP`） | ROM target ロードをブロック | Log（既存 validation） |
| ROM size 超過（`load_bytes` ValueError） | error・ロード中止 | Log + message box |
| ROM runtime が無い | error・ロード中止 | Log |
| `program_target` 不正値 | `ram` フォールバック・warning | Log |
| assembler error（`AsmError`） | 現行どおり Build FAILED | Log（既存） |
| reset_pc が ROM range 外 | 不整合 error（base 確定なら通常起きない） | Log |

- 致命的でない設定系（不正値）は **Log warning + 既定動作**。
- ロード不能（ROM 未配置 / size 超過）は **error 表示してロードを中止**（黙って RAM に書かない）。
- message box は「ユーザー操作で ROM target を選んだのにロード不能」な場面のみ（テストはヘッドレスなので API/Log で検証）。

---

## 12. 既存互換方針（必須）

- **既定 target は RAM**。
- 既存 project に `program_target` が無くても **RAM 扱い**。
- **Hello World は RAM ロードのまま通る**。
- **ram_selftest は RAM ロードのまま通る**（RAM テストなので RAM 必須）。
- **legacy mode は壊さない**（CPU 無し構成・固定 runtime は不変）。
- **ROM 非配置なら既存 Address Map dict 完全一致**（`PATCH_ROM_DEVICE_V08` の互換を維持）。
- RAM target 時の `runtime.load_program` 経路は 1 命令も変えない。
- `tests/test/system.json` に差分を出さない（保存導線を新規に通さない）。
- `python -m pytest tests/` 全通過。

---

## 13. 実装スコープ案（次に実装するなら・安全な範囲）

推奨実装範囲:

- project / system.json に `program_target` を保存（`_persist_system` / `_open_project` / `_new_project` / `_save_project_as`）。
- MainWin に `self._program_target`（既定 `"ram"`）+ `_normalize_target`。
- `set_program_target` / `program_target` / `_program_target_effective` / `_program_target_status`。
- minimal UI（Run/Debug 付近の RAM/ROM ComboBox）または API のみ（最小は API + status）。
- `_assemble_and_load` を RAM/ROM 分岐（`_load_program_to_ram` / `_load_program_to_rom`）。
- ROM target 時は `RomPart.load_bytes()`。
- `_build_runtime_devices` で ROM target かつ base 確定時に CPU の `reset_pc=rom.base`（§7 案 A）。
- ROM target validation（ROM 無し / 未配置 / overlap / size 超過）→ error handling（§11）。
- tests 追加（§14）。
- **既定 RAM 互換維持**。

やらないこと: CPU 命令拡張 / ASM 拡張 / ORG・linker / game16 自動切替 / ROM-only（RAM 廃止）/ VRAM・Timer / `auto` target。

---

## 14. テスト方針（実装時に追加するテスト）

- 既存 project に `program_target` が無い場合 **RAM 扱い**。
- system.json に `program_target` が保存される（save → load round-trip）。
- 不正 `program_target` は **RAM fallback**（warning）。
- RAM target では既存 Write Program 挙動（`runtime.load_program` 経路・RAM に binary・reset_pc=layout）。
- ROM target で `RomPart` に `load_bytes` される（ROM image == binary）。
- ROM target で CPU `reset_pc` が **ROM base** になる（`cpu.pc()` が ROM base 始まり）。
- ROM 無しで ROM target は **error**（RAM に勝手に書かない）。
- ROM 未配置（circuit_compat override 無し）で ROM target は **error**。
- ROM size 超過で **error**（`ValueError` 由来）。
- RAM target の Hello World は壊れない。
- ROM target の簡単なプログラム（game16 想定 ROM 0x0000）が **ROM から fetch** され実行される。
- ram_selftest / legacy / input / rom 既存テストが壊れない。
- ROM 非配置構成の Address Map dict 完全一致。
- `python -m pytest tests/` 全通過。

---

## 15. 今回やらないこと

- 実装
- Program loader 変更（`runtime.load_program` / `_assemble_and_load`）
- system.json 変更
- UI 追加
- CPU 命令追加
- ASM 拡張
- ORG / section / linker
- game16 自動切替
- ROM-only 実行の本格化（RAM 廃止）
- `auto` target
- VRAM / Timer / GPIO / Storage 実装
- HDL / FPGA export
- commit
- push

---

## 16. 次に続くパッチ（候補順）

1. `PATCH_PROGRAM_TARGET_ROM_V08`（本パッチ — program target: RAM/ROM 選択 + ROM ロード導線 + reset_pc 連動・既定 RAM）
2. `PATCH_AK32_INSTRUCTION_EXPANSION_V08`（CALL / RET / IN / AND 等・stack・将来 ORG/linker の前提）
3. `PATCH_TIMER_DEVICE_V08`（タイマ device・割込みは別途）
4. `PATCH_VRAM_DEVICE_V08`（VRAM device・簡易描画の受け皿）
5. `PATCH_GAME_RUNTIME_MINIMAL_V08`（ROM + Input + Timer + VRAM の最小ゲームループ）
6. `PATCH_V08_STABILIZE_AND_DOCS`（v0.8 安定化・ドキュメント・PHASE COMPLETE 準備）

> 横断候補（`V08_CODEBASE_REVIEW.md` §4）: Diagnostics Panel / Project Validation / opcode 単一化 / テストフィクスチャ整理。
