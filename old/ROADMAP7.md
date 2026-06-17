# AKDev ROADMAP 7

> v0.7 開発計画。
> v0.6（UI Polish & Usability + Virtual Circuit Runtime 基盤）の計画と到達点は
> `ROADMAP6.md` / `CHECKLIST6.md`（v0.6 終了扱い・削除せず保管）を参照。
> 進捗管理は `CHECKLIST7.md` で行う。
>
> 注: AKDev の ROADMAP ファイル番号とバージョン表記は歴史的にずれている
> （`ROADMAP6.md` の見出しは「v0.5」表記のまま runtime 作業を取り込んだ）。
> v0.7 からはファイル番号（7）とバージョン（v0.7）を一致させる。
> 過去ファイルのバージョン表記の正規化はユーザー判断事項として保留する。

---

# ✅ v0.7 PHASE COMPLETE — 2026-06-17

- **完了日**: 2026-06-17
- **最終テスト結果**: `python -m pytest tests/` → **860 passed**, 21 warnings
  （PySide6 Deprecation のみ・失敗なし）
- **v0.7 テーマ**: Plan-driven Virtual Devices & Address Map
  （Canvas に描いた回路を「実行時仮想デバイス」として動かす実行基盤の確立）

## 達成した主要機能

| 領域 | 内容 |
|---|---|
| Plan-driven Devices | CircuitPlan から実 RAM/UART/CPU を生成。circuit mode RAM 64KB / UART MMIO 窓 0x0100–0x0107 / legacy mode（256B）維持 |
| Address Map | デバイス単位の base/size/end・attach ranges 管理、unintended overlap 検出（MMIO 窓は除外）、summary 表示、`runtime.address_map` 保持 |
| CPU/RAM Validation | `ram_selftest.asm` で ST/LD/BEQ 検証 → UART `PASS`、Fibonacci を Canvas 由来 runtime で検証 |
| Target CPU Selection | 複数 CPU 時に選択中 CPU を target 化、target の `sources.asm` のみ使用、未選択は ambiguous ブロック、非選択 CPU 未接続は target 実行を妨げない |
| Run Status Panel | target CPU / RAM / UART / Address Map / loaded program / PC / cycle / halted / trace / UART 出力を集約表示 |
| Port Detail Panel | logical ports / visual ports / direction / width / connection / wire detail 表示、Canvas read-only API + 接続変更時更新 |

## 完了した PATCH 一覧（資料は `old/` へ収納）

1. `PATCH_PLAN_DRIVEN_DEVICES_V07`
2. `PATCH_ADDRESS_MAP_V07`
3. `PATCH_CPU_RAM_VALIDATION_V07`
4. `PATCH_TARGET_CPU_SELECTION_V07`
5. `PATCH_RUN_STATUS_PANEL_V07`
6. `PATCH_PORT_DETAIL_V07`

各 `PATCH_*_V07_ROADMAP.md` / `..._CHECKLIST.md`（計 12 ファイル）は `old/` へ収納（削除せず保管）。
`ROADMAP7.md` / `CHECKLIST7.md` は root に残す。

## v0.8 以降へ送る課題

詳細・候補整理は `ROADMAP8.md` / `CHECKLIST8.md` を参照。

- Port direction / width validation（接続可否チェックの土台は Port Detail で確認可能になった）
- Bus protocol validation
- 複数 RAM / UART の本格対応（現状は単一前提）
- ROM / VRAM / Storage / Input デバイス拡張
- Address Map Editor（任意アドレス編集 UI）
- コード領域の拡張設計 / UART MMIO 窓の再配置・可変化
- CPU 命令拡張（CALL / RET / IN 等。スタック設計が必要）
- ゲーム runtime 準備
- HDL / FPGA export 準備
- `tests/test/system.json` テスト差分の扱い（ユーザー判断保留・v0.6 繰越）

## GUI 目視確認が必要な項目（ヘッドレス環境のため自動テスト外）

- CPU+RAM+UART 配線 → Write → Run で UART Console に Hello World、Run Status に集約表示。
- Debug リボンの「Run Status」「Port Detail」トグルでパネル表示/非表示。
- 複数 CPU で選択を切り替えると target CPU 表示が追従、未選択でブロック表示。
- ノード/wire 選択で Port Detail が追従、接続作成/削除/visual port 移動で崩れない。
- legacy（CPU 未配置）エディタタブ Build→Run が従来どおり "Hi"。

## 注意事項

- commit / push はユーザー操作（本整理では未実施）。
- `tests/test/system.json` の差分は勝手に破棄/コミット対象化しない。
- v0.8 は本ファイル下部および `ROADMAP8.md` の候補整理のみ。実装はユーザー指示後。

---

## v0.6 到達点（終了扱い・2026-06-16 整理）

v0.6 は「UI Polish & Usability」として始まり、後半で **Virtual Circuit Runtime の基盤**まで到達した。

| カテゴリ | 到達内容 |
|---|---|
| Wiring / Visual Port | Dynamic Visual Port・port-drag connect・hover・select/delete・port move・wire style |
| Program / Sources | パーツへの asm/hdl/rom 割り当て（優先順位解決・round-trip）|
| Write Program | 割り当て asm を仮想回路へロード（接続 RAM へ）|
| Virtual CPU Step & Trace | `core/runtime.py` `VirtualCircuitRuntime`、1 命令 Step + trace dict、最小 disassembler |
| Virtual Circuit Runtime | `core/circuit.py` `resolve_circuit()`、CPU/RAM/UART 接続解析、未接続時の Write/Build/Run/Step ブロック |
| テスト | `pytest tests/` **779 passed**（2026-06-16 確認）|

詳細・残課題は `ROADMAP6.md` 末尾と `HANDOFF.md` を参照。

---

## v0.7 テーマ

**Plan-driven Virtual Devices & Address Map**

---

## v0.7 の目的

Canvas 上の CPU / RAM / UART／将来の VRAM / Storage / Input などを、
**単なる見た目や接続チェックではなく、実際の実行時仮想デバイスとして扱えるようにする。**

v0.6 までで「接続されているかどうか」を判定して実行可否を決めるところまでは到達した。
v0.7 では、その接続構成（CircuitPlan）から **実行デバイスそのものを生成**し、
描いた回路の上でプログラムが動く状態にする。これは最終目標
「自作 CPU 上でゲーム実行環境を動かし、1 本のゲームを起動・操作できる状態」
へ向けた実行基盤の確立フェーズである。

---

## v0.6 から引き継ぐ課題

* **CircuitPlan はあるが、まだ実デバイス生成が弱い。**
  `resolve_circuit()` は CPU/RAM/UART の接続解析とログ表示・実行ゲートが中心で、
  解決した RAM/UART ノードを実行デバイスとして構築していない。
* **RAM/UART が固定 runtime 寄り。**
  `ui/win.py:_make_sim()` は plan に関係なく固定の `_sim_ram` / `_sim_uart` / `_sim_cpu` を
  毎回生成し、`_runtime.plan = plan` を付与するだけ。実行は固定内部デバイスで行われる。
* **RAM サイズが小さい。**
  固定 256 バイト（`_SIM_RAM_SIZE = 0x0100`）。中規模プログラム・将来のゲームには不足。
* **アドレスマップ管理がない。**
  RAM 0x0000 / UART 0x0100 のハードコード。base/size をデバイス単位で管理していない。
* **複数 CPU / 複数 RAM / 複数 UART の扱いが未整理。**
  複数 CPU は `cpus[0]` 固定（issue 扱い）。複数 RAM/UART は単一前提。
* **RAM selftest / Fibonacci が Canvas 実行基盤上で検証されていない。**
  `src/fib.asm` は単体では動くが、Canvas で組んだ回路の runtime 上での検証はない。

---

## v0.7 作業候補（優先順位付き）

### 1. PATCH_PLAN_DRIVEN_DEVICES_V07 ★最優先（最初に実装）

* **目的**: CircuitPlan から RAM/UART の実デバイスを生成し、runtime をそれに束ねる。
* **範囲**:
  * `resolve_circuit()` の plan に各デバイスの base/size 情報を持たせる（最小でよい）
  * `_make_sim(plan)` を plan 駆動にする（plan の RAM/UART ノードから実デバイスを構築）
  * circuit mode の RAM サイズ拡張（例: 256B → 64KB 程度。要・上限検討）
  * Write Program は **plan に紐づく接続 RAM** へロード
  * Run/Step は **plan に紐づくデバイス**で実行
  * legacy mode（CPU 未配置）は従来の固定 runtime を維持
* **触る可能性が高いファイル**: `ui/win.py` / `core/circuit.py` /（必要なら）`core/runtime.py`
* **必要なテスト（実装時に追加）**:
  * plan の RAM ノードが実行 RAM として使われる
  * RAM 拡張後に大きめの asm がロード・実行できる
  * Write→Run で Hello World 維持
  * legacy mode 不変・hello.asm "Hi" 維持
* **今回やらないこと**: 複数 RAM/UART の本対応、VRAM/Video、アドレスマップ編集 UI
* **リスク**: 既存テストが `win._sim_ram` 等の固定属性を直接参照している箇所の退行。
  RAM 拡張に伴うメモリビューア・bus map の整合。

### 2. PATCH_ADDRESS_MAP_V07

* **目的**: RAM/UART などの base/size を管理し、overlap を検出、Address Map を表示する。
* **範囲**:
  * plan / runtime にデバイス単位の base/size を保持
  * `Bus.attach` の overlap 検出を Address Map レベルで活用
  * Address Map の表示（Properties か Debug パネル）
* **触るファイル**: `core/circuit.py` / `ui/win.py` /（表示先により）`ui/prop.py`
* **必要なテスト**: overlap 検出、base/size の保持・表示、既定マップの維持
* **今回やらないこと**: ユーザーによる任意アドレス編集 UI（次段）
* **リスク**: PATCH_PLAN_DRIVEN_DEVICES_V07 と密結合のため、順序・統合方針の確定が必要。

### 3. PATCH_CPU_RAM_VALIDATION_V07

* **目的**: CPU が接続 RAM に対して正しく LD/ST/ADD/分岐できることを検証する。
* **範囲**:
  * RAM read/write selftest（書いて読み戻す最小プログラム）
  * Fibonacci を Canvas 由来 runtime 上で実行・検証
  * LD/ST/ADD/分岐の到達性チェック
* **触るファイル**: `core/circuit.py` / `ui/win.py` / テスト用 asm（`tests/test/` 配下）
* **必要なテスト**: selftest 結果、Fibonacci の期待値、未到達アドレスの検出
* **今回やらないこと**: 命令追加（CALL/RET/IN）、breakpoint
* **リスク**: RAM サイズ・アドレスマップに依存するため 1・2 の後に行う。

### 4. PATCH_TARGET_CPU_SELECTION_V07

* **目的**: 複数 CPU がある場合に、選択中 CPU を実行対象にできるようにする。
* **範囲**:
  * `resolve_circuit()` の「cpus[0] 固定」を選択 CPU 優先へ
  * 選択 CPU の plan 解決・実行対象切替
  * 未選択時のデフォルト挙動の整理
* **触るファイル**: `core/circuit.py` / `ui/win.py` /（選択取得）`ui/canvas.py`
* **必要なテスト**: 複数 CPU で選択 CPU が実行される、未選択時の挙動
* **今回やらないこと**: 複数 CPU の同時実行（マルチコア）
* **リスク**: 「multiple CPU は issue」既存テストとの整合更新。

### 5. PATCH_RUN_STATUS_PANEL_V07

* **目的**: 実行状態を UI で一覧できるようにする。
* **範囲（表示項目）**:
  * 実行対象 CPU
  * 接続 RAM / UART
  * loaded program
  * PC / cycle / halted
  * trace summary
  * UART output
* **触るファイル**: `ui/win.py`（新ドック）/ Debug タブ /（必要なら）`ui/runtime` 参照
* **必要なテスト**: パネル生成、状態反映、Run/Step 後の更新
* **今回やらないこと**: trace の高度な可視化（タイムライン等）
* **リスク**: 1〜4 の状態モデルが固まってから作るのが安全（鏡なので対象を先に正す）。

### 6. PATCH_PORT_DETAIL_V07

* **目的**: ノードの論理ポート / visual port / direction / width / connection を確認できるようにする。
* **範囲**:
  * part.json `ports`（direction/type）と visual port を突き合わせて表示
  * connection 情報の表示
  * ダブルクリック or コンテキストメニューで起動（`old/ROADMAP5.md` 7-3 / `UI_SPEC_V05.md` 9 方針）
* **触るファイル**: `ui/win.py` / `ui/prop.py` /（必要なら）新パネル
* **必要なテスト**: ポート情報表示、選択切替での更新
* **今回やらないこと**: 接続可否の型判定（constraint）本実装
* **リスク**: part.json の `ports` 情報が表示に十分か（width 等が未定義のパーツあり）。

---

## v0.7 実装順序（推奨）

1. PATCH_PLAN_DRIVEN_DEVICES_V07（土台）
2. PATCH_ADDRESS_MAP_V07（1 と統合的に）
3. PATCH_CPU_RAM_VALIDATION_V07
4. PATCH_TARGET_CPU_SELECTION_V07
5. PATCH_RUN_STATUS_PANEL_V07
6. PATCH_PORT_DETAIL_V07

1 → 2 は密結合のため、設計時に統合 or 分割を確定する。

---

## v0.7 ではやらないこと

| 項目 | 理由 |
|---|---|
| VRAM / Video 本実装 | v0.7 の実デバイス基盤の上で v0.8 以降 |
| Storage 本実装 | 同上 |
| Input 本実装 | 同上 |
| FPGA 実機書き込み | v0.8 以降 |
| HDL 合成（iverilog / Yosys） | v0.8 以降 |
| C コンパイラ対応 | v0.8 以降 |
| 複数 CPU 同時実行（マルチコア） | 実行対象選択（候補 4）の次フェーズ |
| 完全なゲーム実行環境 | v1.0 目標 |
| CALL / RET / IN 命令追加 | 別フェーズ（スタック設計が必要）|
| breakpoint UI | 別フェーズ |

---

## 次に実装する最初のパッチ

```text
PATCH_PLAN_DRIVEN_DEVICES_V07
```

**理由**: 今のままでは、Canvas 上で接続した RAM/UART が本当に実行デバイスになっているとは
言い切れない（plan はメタデータ、実体は固定 `_sim_ram`/`_sim_uart`）。
まず CircuitPlan から実デバイスを生成する構造にしないと、CPU/RAM validation・Fibonacci・
VRAM・Video・Input へ進んでも土台がズレ、後から作り直しになる。

実装に入る前に CLAUDE.md のルールに従い、`PATCH_PLAN_DRIVEN_DEVICES_V07_ROADMAP.md` /
`PATCH_PLAN_DRIVEN_DEVICES_V07_CHECKLIST.md` を**作業前に**作成する。

---

## v0.7 完成条件

* [ ] CircuitPlan から RAM/UART の実デバイスが生成され、runtime がそれで実行する
* [ ] circuit mode の RAM サイズが拡張されている
* [ ] RAM/UART の base/size が管理され、overlap が検出できる
* [ ] Address Map が UI で確認できる
* [ ] CPU が接続 RAM に対して LD/ST できることが検証されている（selftest / Fibonacci）
* [ ] 複数 CPU 時に実行対象 CPU を選択できる
* [ ] Run/Step 時の状態（CPU/RAM/UART/loaded/PC/trace/UART 出力）が UI で見える
* [ ] Port Detail で論理/visual ポート・direction・width・connection が確認できる
* [ ] legacy mode（CPU 未配置）が従来どおり動作する
* [ ] `pytest tests/` が全件通過している
* [ ] CHECKLIST7.md の全項目が `[x]` になっている
* [ ] HANDOFF.md が v0.7 の状況・次フェーズを指している

---

## 命令エンコード仕様（参考・v0.6 時点と不変）

```
bits 31..24  opcode
bits 23..16  rd / rs（宛先または比較 reg 1）
bits 15..8   rs / rt（ソース reg または比較 reg 2）
bits  7..0   rt / imm8 / rel8
```

| opcode | ニーモニック | 動作 |
|---|---|---|
| 0x00 | NOP | なし |
| 0x01 | HALT | 実行停止 |
| 0x02 | LDI rd, imm16 | regs[rd] = imm16 |
| 0x03 | OUT [rd], rs | bus.write(regs[rd], regs[rs]) |
| 0x04 | ADD rd, rs, rt | regs[rd] = regs[rs] + regs[rt] |
| 0x05 | SUB rd, rs, rt | regs[rd] = regs[rs] - regs[rt] |
| 0x06 | LD rd, [rs] | regs[rd] = bus.read(regs[rs]) |
| 0x07 | ST [rd], rs | bus.write(regs[rd], regs[rs]) |
| 0x08 | JMP imm16 | pc = imm16 |
| 0x09 | BEQ rs, rt, rel8 | if regs[rs] == regs[rt]: pc += signed(rel8)*4 |
| 0x0A | ADDI rd, rs, imm8 | regs[rd] = regs[rs] + imm8 |
