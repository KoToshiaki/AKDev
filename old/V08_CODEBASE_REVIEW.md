# V08 Codebase Review — AKDev v0.8 計画のためのコードベースレビュー

> 作成日: 2026-06-17 / 対象: v0.7 PHASE COMPLETE 時点（`pytest tests/` 860 passed）。
> 本書は**レビューと提案のみ**。コード変更・実装・テスト追加は行っていない。
> 現行管理ファイル: `ROADMAP8.md` / `CHECKLIST8.md`。完了フェーズ資料は `old/`。

---

## 1. 現状要約

### v0.7 終了時点でできること

Canvas に CPU+RAM+UART を置いて配線すると、その接続（CircuitPlan）から**実行用の仮想デバイス**
（64KB RAM・UART MMIO 窓 `0x0100–0x0107`・AK32 CPU）が生成され、割り当てた ASM を Write→Run/Step
できる。実行は 1 命令ずつ trace され、Address Map・実行状態（Run Status Panel）・選択ノード/wire の
ポートと接続（Port Detail Panel）を UI で確認できる。複数 CPU では選択 CPU を実行対象にでき、CPU 未配置
の legacy mode（固定 256B RAM）は従来どおり動く。

### 内部実行基盤の状態（core/）

| モジュール | 役割 | 状態 |
|---|---|---|
| `core/sim.py` | `Part` / `Port` / `Bus`（flat address map・overlap 検出）/ `Chip` / `Sim` | 安定。Bus は (base,end,part) 線形リスト。`Port` に direction はあるが runtime Part は ports 未投入 |
| `core/dev.py` | `RamPart`（32bit LE word）/ `UartPart`（TX only） | 安定。UART は受信なし。ports 未定義 |
| `core/cpu.py` | `AK32Part`（11 命令 ISA） | 安定。SP/スタック無し、JMP/LDI は imm16（16bit アドレス上限） |
| `core/runtime.py` | `VirtualCircuitRuntime`（step/trace/disasm） | 安定。単一 bus/ram/uart/cpu を wrap。`disasm` が 11 命令表を独自保持 |
| `core/circuit.py` | `resolve_circuit` / `build_address_map` / `validate_address_map` / `format_address_map_summary` | v0.7 の主役。**RAM+UART 固定前提**（後述） |
| `asm/asm.py` | 2-pass アセンブラ（ラベル対応） | 安定。11 命令表を独自保持 |

### UI / Debug 基盤の状態（ui/）

- Canvas（`ui/canvas.py` 2058 行）= 配置・配線・visual port・wire style・選択。大きいが機能は揃う。
- Debug パネル: Run Status / Port Detail（v0.7 新規・read-only）+ Register / Memory / Bus Trace /
  UART Console / Log / Properties。情報の可視化はかなり充実。
- `ui/win.py`（1326 行）= 統合点。`_make_sim(plan)` が plan→実デバイス生成を担うが**単一 RAM/UART 固定**。

### テストの状態

- `tests/` 38 ファイル・約 10,854 行・**860 passed**。core とヘッドレス GUI を広くカバー。
- `resolve_circuit` / `build_address_map` / runtime step / plan-driven / target CPU / run status /
  port detail は単体・統合テストあり。GUI の目視確認のみ手動（ヘッドレス環境）。

---

## 2. コードベース視点の評価

| 観点 | 評価 | 短評 |
|---|---|---|
| Runtime / Bus / Device 構造の拡張性 | ★★★☆☆ | Bus/Part は素直で拡張余地あり。ただし**実体生成（`_make_sim`）が RAM/UART 各1個ハードコード**で、ここが律速 |
| Address Map 構造の拡張性 | ★★☆☆☆ | `build_address_map(ram_node, uart_node, ...)` が **2 デバイス固定シグネチャ**。N デバイス化には作り直しが必要。検証ロジック（`validate_address_map`）は list ベースで汎用的・良い |
| Port / Connection 構造の拡張性 | ★★★☆☆ | connection/visual port のデータは十分。だが **part.json ports に direction/width が無く**、接続時検証が一切ない。direction は Port Detail で type から推定しているだけ（単一の真実源がない） |
| UI Debug Panel の拡張性 | ★★★★☆ | Run Status / Port Detail が read-only テキストで素直。検証結果の表示先として十分。重複は Properties(Wire) と軽微 |
| Test 基盤の強さ | ★★★★☆ | 数・カバレッジとも良好。難点は**フィクスチャ重複**（各テストが `_CPU/_RAM/_UART` と `_wire_full` を再定義）と、検証系テストの置き場が未定 |
| v0.8 で先に直すべき設計上の弱点 | — | (1) 単一 RAM/UART ハードコード、(2) Address Map の 2 デバイス固定、(3) part.json に direction/width 無し、(4) ロール判定が category 依存（VRAM=mem 誤判定）、(5) opcode 表が asm/cpu/runtime の 3 箇所に重複 |

### 特に重要な構造的弱点（詳細）

1. **単一 RAM/UART ハードコード** — `ui/win.py:_make_sim()` は `plan["rams"][0]` / `plan["uarts"][0]`
   のみを使い、`RamPart("sim_ram")` と `UartPart("sim_uart")` を各 1 個だけ生成する。複数 RAM/UART/
   新デバイスは**実行に反映されない**。多デバイス対応の前にここを「デバイスリスト駆動」へ一般化すべき。
2. **Address Map が 2 デバイス固定** — `build_address_map` は ram/uart 専用引数。N デバイス（ROM/VRAM/
   Input…）を載せるには `[{node, kind, base, size, role}]` のリスト駆動ビルダーへ作り替える必要がある。
3. **ロール判定が category 依存** — `resolve_circuit` の `_is_ram` は `category=="mem"`。**`mem.vram` も
   "mem"** なので VRAM を RAM と誤認する。ROM/Input には判定が無い。part.json に明示 `role` を持たせるか、
   type ベース判定へ移すのが安全。
4. **16bit アドレス空間 + UART 窓固定** — `LDI`/`JMP` は imm16（最大 `0xFFFF`）。全コード/データ/MMIO が
   64KB に同居し、UART は低位 `0x0100` に居座る。小規模プログラムでは問題ないが、ゲーム級では
   「コード領域」「MMIO 再配置/可変化」が必要になる。今は**足かせ予備軍**（まだ実害は小）。
5. **opcode 表の三重管理** — 命令の真実源が `asm/asm.py`・`core/cpu.py`・`core/runtime.py:disasm()` に
   分散。CALL/RET/IN 追加時に**3 箇所**を整合させる必要があり、命令拡張の前に共通化したい。
6. **schema/永続化のドリフト** — `create_project` の system.json 雛形は `{chips, parts, links, memory_map}`
   だが `canvas.export_canvas()` は `{parts, connections}`（"links" ではなく "connections"）。schema
   version も無い。多デバイス化で system.json に Address Map を永続化するなら、版管理と整合が要る。

---

## 3. v0.8 で優先すべき候補ランキング

> 凡例 — 難易度/リスク/効果は ★1〜5。「先にやらないと困る」= これを飛ばすと後続が手戻りする度合い。

### #1 PATCH_PORT_SCHEMA_V08 — part.json ports スキーマ拡張（direction / width / role）
- **目的**: ports に `direction`（in/out/inout）・`width`・任意 `role` を明示し、direction/width の
  **単一の真実源**を作る。Port Detail は推定をやめ実値表示に。
- **なぜ今**: ユーザー案 #1（direction/width validation）も #2（bus protocol）も**この schema が前提**。
  推定 direction のままでは検証の根拠が脆い。
- **依存**: なし（最上流）。
- **難易度 ★★☆☆☆ / リスク ★★☆☆☆**（全 part.json の更新 + ロード後方互換）。
- **効果 ★★★★☆**: 以降の検証・多デバイス判定・ロール判定すべての土台。
- **先にやらないと困る**: Validation 全般・ロール判定の正規化。
- **補足**: ロール判定（VRAM=mem 誤認）も `role` フィールドでここで同時に解消できる。

### #2 PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08 — 接続時の direction/width 検証（ユーザー案1）
- **目的**: 接続作成時に out→in / master→slave / width 一致を検証し、不可なら警告/ブロック。Port Detail に
  検証結果表示。
- **なぜ今**: schema が入れば最小コストで「正しく組めているか」を可視化でき、配線品質が一段上がる。
- **依存**: #1（schema）。
- **難易度 ★★★☆☆ / リスク ★★★☆☆**（既存テストは無検証で配線しているため、ブロックでなく**警告**から入るのが安全）。
- **効果 ★★★★☆**。
- **今はまだ早い理由（部分的）**: 「ブロック」は既存テスト・既存プロジェクトを壊しうる。初手は**警告のみ**にして
  ブロックは段階導入が無難。

### #3 PATCH_DEVICE_REGISTRY_REFACTOR_V08 — Address Map / _make_sim のデバイスリスト駆動化（Claude 提案）
- **目的**: `build_address_map(ram,uart)` を `[{node,kind,base,size,role}]` 駆動へ一般化し、
  `_make_sim` を「plan のデバイス一覧から Part を生成して attach」する形に作り替える（挙動は現状維持）。
- **なぜ今**: 複数 RAM/UART・ROM・VRAM・Input の**すべての前提**。これを先に通さないと、各デバイス追加が
  毎回ハードコードへ割り込み、手戻りが累積する。
- **依存**: #1 のロール明示があると安全。
- **難易度 ★★★★☆ / リスク ★★★☆☆**（中核リファクタ。挙動不変を回帰テストで担保）。
- **効果 ★★★★★**: 多デバイス系（#4,#5,#7）の難易度を大幅に下げる。
- **先にやらないと困る**: 複数 RAM/UART・新デバイス全般。

### #4 PATCH_BUS_PROTOCOL_VALIDATION_V08 — bus master/slave・1 master・到達性（ユーザー案2）
- **目的**: bus.master↔bus.slave 整合・1 master 制約・Address Map 到達性（CPU から各 slave へ届くか）を検証。
- **なぜ今**: #1/#2 の延長で、回路としての妥当性を保証できる。
- **依存**: #1（schema）, できれば #3（多デバイス前提の到達性）。
- **難易度 ★★★☆☆ / リスク ★★☆☆☆ / 効果 ★★★★☆**。

### #5 PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08 — 複数 RAM/UART 対応（ユーザー案3）
- **目的**: 複数 slave を Address Map 上で共存させ、target CPU から見た複数 slave を解決。
- **なぜ今**: ゲーム/デバイス拡張に必須だが、**#3 の後**が圧倒的に楽。
- **依存**: #3（必須に近い）, #1。
- **難易度 ★★★★☆ / リスク ★★★☆☆ / 効果 ★★★★☆**。
- **今はまだ早い理由**: #3 を飛ばすと `_make_sim`/`build_address_map` を二重に作り替えることになる。

### #6 PATCH_ADDRESS_MAP_EDITOR_V08 — base/size の UI 編集（ユーザー案4）
- **目的**: Address Map の base/size を UI で編集し、overlap 検出と連動。MMIO 位置変更の準備。
- **なぜ今**: 多デバイスが入ると固定既定では足りなくなる。
- **依存**: #3, #5。
- **難易度 ★★★★☆ / リスク ★★★☆☆ / 効果 ★★★☆☆**。
- **今はまだ早い理由**: 多デバイスの土台（#3/#5）が固まってから。鏡なので対象を先に。

### #7 PATCH_CODE_REGION_MMIO_RELOCATION_V08 — コード領域拡張 / UART MMIO 再配置・可変化（ユーザー案5）
- **目的**: UART 窓 `0x0100` 固定問題を整理し、コード領域を拡張、MMIO を高位/可変に。
- **なぜ今**: 中規模プログラム以上で効く。Address Map（#3/#6）と密結合。
- **依存**: #3, #6。**imm16 アドレス上限（64KB）の制約**も併せて設計判断が要る。
- **難易度 ★★★★☆ / リスク ★★★★☆ / 効果 ★★★☆☆**。
- **今はまだ早い理由**: 小規模では実害が小さく、Address Map Editor と一緒に設計するのが効率的。

### #8 PATCH_AK32_INSTRUCTION_EXPANSION_V08 — CALL / RET / IN + スタック（ユーザー案7）
- **目的**: スタック（SP 規約 + push/pop PC）と CALL/RET、入力用 IN を追加。
- **なぜ今**: ゲーム runtime（#案8）の前提。ただし**opcode 表の共通化（下記独自提案）を先に**やると安全。
- **依存**: opcode 共通化（独自提案 D）、IN は入力デバイス（#案6）。
- **難易度 ★★★★★ / リスク ★★★★☆**（ISA 変更・3 箇所の opcode 表・RET 用 register-indirect jump 設計）。
- **効果 ★★★★☆**。
- **今はまだ早い理由**: ISA を変える前に、検証基盤（#1〜#4）と opcode 単一化で足場を固めるべき。

> ユーザー案 #6（ROM/Input/Storage/VRAM 追加）と #8（Game runtime prep）は、上記 #1/#3/#5/#8 が
> 整うまで**着手保留**を推奨（土台先行）。Device expansion は #3 完了後に 1 デバイスずつが安全。

---

## 4. Claude Code 独自提案（ユーザー案にないが必要なもの）

- **A. part.json schema versioning + 正規化** — `schema_version` を付与し、`ports` の必須/任意フィールドを
  定義。#1 と一体で行うと将来の migration が安全。
- **B. system.json format versioning + import/export 整合** — 雛形の `links` と export の `connections` の
  ドリフトを解消し、`schema_version` を付与。Address Map を永続化する前提づくり。
- **C. device role 判定の正規化** — `resolve_circuit` の category 依存（VRAM=mem 誤認）を part.json の
  明示 `role` か type ベース判定へ。**多デバイスの正確さの前提**。
- **D. opcode/ISA 単一定義化** — `asm/asm.py`・`core/cpu.py`・`core/runtime.py:disasm()` の 3 重定義を
  1 つの ISA テーブル（mnemonic/opcode/operand 形式）へ集約。命令拡張（#8）前に必須級。
- **E. project validation / diagnostics コマンド（headless）** — overlap・未接続・direction 不一致・到達性を
  1 レポートにまとめる CLI/関数。**検証系テストの自然な置き場**になり、GUI 無しで CI 可能。
- **F. テストフィクスチャ整理** — `conftest.py` に「CPU+RAM+UART を配線した MainWin/Canvas」を共通
  フィクスチャ化。各 v05/v07 テストの `_CPU/_RAM/_UART`・`_wire_full` 重複を縮約。検証系は
  `tests/validation/` 等にグルーピング。
- **G. （任意）ui/canvas.py（2058 行）の分割** — port-drag / wire-style / visual-port など責務単位へ。
  緊急ではないが保守コスト低減。今フェーズでは見送り推奨。

---

## 5. 推奨 v0.8 ロードマップ案

```text
v0.8-1  PATCH_PORT_SCHEMA_V08                    # part.json に direction/width/role（+独自提案A,C）
v0.8-2  PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08# 接続時 direction/width 検証（初手は警告のみ）
v0.8-3  PATCH_DEVICE_REGISTRY_REFACTOR_V08       # Address Map/_make_sim をデバイスリスト駆動へ（挙動不変）
v0.8-4  PATCH_BUS_PROTOCOL_VALIDATION_V08        # master/slave・1 master・到達性
v0.8-5  PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08     # 複数 RAM/UART 共存（#3 の上で）
v0.8-6  PATCH_ADDRESS_MAP_EDITOR_V08             # base/size UI 編集（+ system.json versioning 独自提案B）
v0.8-7  PATCH_CODE_REGION_MMIO_RELOCATION_V08    # コード領域拡張 / MMIO 再配置・可変化
v0.8-8  PATCH_AK32_INSTRUCTION_EXPANSION_V08     # opcode 単一化（独自提案D）→ CALL/RET/IN + stack
（以降）Device expansion(ROM/Input/VRAM) / Game runtime prep は土台が固まってから 1 つずつ
```

横断タスク（どこかで早めに）: 独自提案 **E（diagnostics）** と **F（test 整理）** は #2〜#4 の検証実装と
同時に入れると、検証ロジックの置き場・CI 化・重複縮約が同時に進む。

---

## 6. 最初のパッチとして最もおすすめ

### → `PATCH_PORT_SCHEMA_V08`（part.json ports スキーマ拡張 + role 正規化）

**理由**: v0.8 の主軸「Connection Validation」も「Device Expansion」も、**direction/width/role の単一の
真実源**が無いと根拠が脆いまま積み上がる。現状 direction は Port Detail が type から推定しているだけで、
VRAM は category="mem" のため RAM と誤認される。ここを最初に正すと、以降の検証（#2,#4）・多デバイス
判定（#3,#5）が一気に素直になる。小さく・上流・後続全体の手戻りを防ぐ、最もコスパの良い起点。

**次に実装するなら（提案レベル・実装指令ではない）**:
- 全 `parts/**/*.json` の各 port に `direction`（"in"/"out"/"inout"）と `width`（bit 数 or null）を付与。
  既存 type から自然に決まる（bus.master→out、bus.slave→in、clock/reset/irq→in、video.rgb→out 等）。
- part.json に `schema_version` を追加し、ローダは旧形式（direction/width 無し）を後方互換で読む。
- `resolve_circuit` の RAM/UART/CPU 判定を category 依存から **part.json の明示ロール**（または type）
  ベースへ寄せ、`mem.vram` を RAM と誤認しないようにする。
- `ui/port_detail.py` の `direction_from_type` 推定を、part.json の実値があればそれを優先する形に。
- テスト: part.json ロードの後方互換、direction/width の読み出し、resolve_circuit が VRAM を RAM と
  しないこと、Port Detail が実値を表示すること。

> 本書は提案まで。実装指令文は含めない。次フェーズの最初のパッチ着手は、CLAUDE.md に従い
> `PATCH_PORT_SCHEMA_V08_ROADMAP.md` / `..._CHECKLIST.md` を**作業前に作成**してから。
