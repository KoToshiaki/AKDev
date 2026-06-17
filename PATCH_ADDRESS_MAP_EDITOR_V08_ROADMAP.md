# PATCH_ADDRESS_MAP_EDITOR_V08 — ROADMAP（設計資料）

> v0.8（Device Expansion & Connection Validation）の **7 番目の候補パッチ**の設計資料。
> 本書は設計のみ。**実装・テスト追加・part.json 変更・挙動変更・commit/push は行わない。**
> 親計画: `ROADMAP8.md` / `CHECKLIST8.md`。所見: `V08_CODEBASE_REVIEW.md`。
> 前提: `PATCH_PORT_SCHEMA_V08` / `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08` /
> `PATCH_BUS_PROTOCOL_VALIDATION_V08` / `PATCH_DEVICE_REGISTRY_REFACTOR_V08` /
> `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08` / `PATCH_CODE_REGION_MMIO_RELOCATION_V08` 完了
> （`pytest tests/` 988 passed）。

---

## 1. 目的

- 自動配置された Address Map を **GUI で確認・編集**できるようにする。
- device spec の `base` / `size` を **ユーザーが override**できるようにする（auto → manual）。
- **MemoryLayout（自動配置の既定）と手動 override の関係**を整理する。
- 編集時に **overlap / 範囲外 / size 0** などを検出して表示する。
- 複数 UART/MMIO・複数 RAM・将来の ROM/VRAM/Input 配置に備えた編集土台を作る。
- **今回は設計のみ**。実装・既定挙動変更はしない。**override が無ければ完全に現行の自動配置**。

### スコープ（明確化）

「**Address Map を表形式で確認 + per-device base/size override + auto/manual + Reset to Auto +
編集時 validation + Apply で runtime 再構築**」を設計する。layout mode 切替 UI・game16 実行・新デバイス
runtime は対象外。override の永続化（system.json）は最小 or 次段分離を提案。

---

## 2. 現在の問題

- Address Map は **自動配置のみ**（`build_address_map_from_devices` + `assign_mmio_bases`）。
- device ごとの `base` / `size` を **GUI で編集できない**。
- `MemoryLayout` はあるが、ユーザーが layout や per-device override を選べない。
- 複数 RAM は warning までで、**手動で領域分割できない**（`MULTI_RAM_UNSUPPORTED`）。
- `game16` layout は定義だけで実行に使っていない。
- overlap 検出（`validate_address_map`）はあるが、**GUI 編集時の validation 表示が無い**。
- project 保存時に Address Map override をどう持つか未定（system.json は `{chips, parts, links,
  memory_map}` 形・canvas は `{parts, connections}`）。
- Run Status Panel / Address Map summary は**表示中心**で、編集 UI ではない。

---

## 3. UI 方針

### 配置（推奨）

- **右側 Dock の「Address Map」Editor パネル**（Run Status / Port Detail と並ぶ read+edit ドック）を推奨。
  - 既存ドック作法（`ui/run_status.py` / `ui/port_detail.py`、`tabifyDockWidget`、Debug リボンの
    `toggleViewAction()`）に合わせる。
  - 代替: Dialog（OK/Cancel）。最小実装では Dock の方が既存パターンに乗りやすい。Run Status 内への内蔵は
    表示と編集の責務が混ざるため非推奨。

### 表示項目（read-only 含む）

- node_id / part name / kind / role / base / size / end / runtime_backed / overlay / **validation status**

### 編集可能項目

- `base` / `size` / **auto⇔manual 切替**（per device）/ **Reset to Auto**（全体 or per device）
- （layout mode 切替は**表示のみ**、または次段）

### 編集不可（read-only）

- kind / role / node_id / runtime_id（device spec の同一性・分類は不変）

---

## 4. データ構造方針

### override の保持先（推奨）

- **MainWin runtime state**（`self._address_overrides`）+ **system.json への任意保存**。
  - 編集中・実行は runtime state を使う。保存は project 永続化（次段分離可）。
- device spec に直接 `base_override` を埋めるより、**node_id キーの override dict** が疎結合で安全。

### override 構造案

```json
{
  "address_map_overrides": {
    "node_0002": {"base": 512,  "size": 32768, "mode": "manual"},
    "node_0003": {"base": 4096, "size": 8,     "mode": "manual"}
  }
}
```

- `mode`: `"auto"`（override 無効・自動配置）/ `"manual"`（base/size を適用）。
- **system.json に新規キー `address_map_overrides` を追加**（任意・無ければ全 auto）。

### パイプラインへの組み込み（案）

- 自動配置（`make_device_spec` → `assign_mmio_bases`）の**後**に
  `apply_address_overrides(specs, overrides)` を挟み、`mode=="manual"` の node の base/size/end/
  attach_ranges を上書きしてから `build_address_map_from_devices` へ渡す。
- override が空なら**完全に現行と同一**（no-op）。

### 互換

- 既存 project（`address_map_overrides` 無し）は全 auto = 現行挙動。
- 古い project を開いてもエラーにならない（キー欠如は空 dict 扱い）。
- override 保存は**今回は設計のみ or 次の実装で**（runtime state 先行、永続化は分離可）。

---

## 5. MemoryLayout との関係

- **MemoryLayout = 自動配置の既定値**（circuit_compat / legacy / game16）。
- **Editor = layout の自動配置を device 単位で上書き**（per-device manual override）。
- layout mode 切替と manual override の衝突: **override が優先**（manual な device は layout を無視して
  指定 base/size を使う。auto な device は layout に従う）。
- 既定は `circuit_compat`（既存互換）。`game16` は**実行に使わない**（layout 切替 UI も今回は表示のみ/次段）。
- 最小実装は「**layout は表示のみ + per-device base/size override**」を推奨。

---

## 6. validation 方針

- 個々の編集値:
  - `base >= 0` / `size > 0` / `end (= base+size-1) <= 0xFFFF`（imm16 / 64KB 制約）。
  - MMIO は 16byte アライン**推奨**（warning）。UART size 8B 推奨（warning。固定強制はしない）。
- 領域整合:
  - RAM 同士の overlap → **error**。
  - RAM と MMIO の overlap:
    - `mmio_inside_ram=True` → overlay として**許容**（現行の窓くり抜き）。
    - `mmio_inside_ram=False` → overlap は **error**。
  - 既存 **`validate_address_map()`**（attach_ranges 同士）を活用 + Editor 専用 issue を追加。
- **warning と error の区別**:
  - error: 範囲外 / size 0 / 非 overlay overlap → **Apply / Run をブロック**。
  - warning: アライン外 / UART size≠8 / 複数 RAM（`MULTI_RAM_UNSUPPORTED`）→ 表示のみ（ブロックしない）。
- issue 構造は port/bus validation と同形（severity/code/message/details）を踏襲。

---

## 7. 反映タイミング

- **Apply ボタンで反映**（live 反映ではない）を推奨（編集途中の無効状態で再構築しない）。
- Apply 時: validation → error 無しなら `_make_sim()`（device spec パイプライン）を **再構築** →
  Run Status / Address Map summary / Port Detail を更新。
- **invalid（error）状態では Apply 不可**（ボタン無効化 + issue 表示）。
- 実行中（runtime loaded）の場合: Apply は runtime を作り直す（現状 Write/Build と同様の再生成）。
  実行中の停止要求は最小実装では「Apply で再構築 = Reset 相当」を明示。
- **Reset to Auto**: override をクリアして自動配置に戻し、再構築。

---

## 8. 既存互換方針（必須）

- **override が無い場合は現行挙動と完全一致**（パイプラインに no-op で挟む）。
- 既存単一 RAM/UART の **Address Map dict を壊さない**。
- Hello World / ram_selftest / legacy mode を壊さない。
- 保存済み project が古い形式（`address_map_overrides` 無し）でも開ける。
- `tests/test/system.json` の差分を勝手に作らない。
- **Address Map Editor を開かない限り既存動作は変わらない**。
- `self._sim_ram` / `_sim_uart` / `_sim_cpu`・runtime_id 互換を維持。

---

## 9. 実装スコープ案（次に実装するなら）

推奨（安全順）:
1. `ui/address_map_editor.py`（新規）に **Dock パネル + 表（QTableWidget）**。Address Map を読み取り表示
   （read-only 表示が先・既存 summary と同データ）。
2. `base` / `size` の編集 + auto/manual トグル + **Reset to Auto**。
3. **validation preview**（編集値に対し `validate_address_map` + Editor チェックを実行し行/ステータス表示）。
4. **Apply** で `self._address_overrides` を更新 → `apply_address_overrides` をパイプラインに挟み
   `_make_sim()` 再構築。error 時は Apply 不可。
5. project 保存/読込（`address_map_overrides`）は**最小限 or 次段に分離**。
6. layout mode 切替・game16 実行は**やらない**（表示のみ）。

`core` 側追加（案）: `core/devices.py` に `apply_address_overrides(specs, overrides)`（純粋関数）。

---

## 10. テスト方針（実装時に追加するテスト）

- override 無しで既存 Address Map dict が完全一致（回帰）。
- `base` override が device spec / Address Map に反映される。
- `size` override が反映される。
- Reset to Auto で自動配置に戻る。
- invalid range（end>0xFFFF / size 0 / base<0）を検出する。
- overlap（RAM 同士 / 非 overlay RAM-MMIO）を error 検出する。
- `mmio_inside_ram=True` の overlay は許容（error にしない）。
- `mmio_inside_ram=False` の overlap は error。
- 古い project（override 無し）を開ける。
- override 付き project を保存/読込できる（永続化を実装する場合）。
- Hello World / ram_selftest が壊れない。
- legacy mode が壊れない。
- 既存 v07/v08（address map / device registry / multi RAM-UART / code region）が壊れない。
- `python -m pytest tests/` 全通過。

---

## 11. GUI 目視確認項目

- CPU+RAM+UART を置く。
- Address Map Editor（Debug リボンのトグル）を開く。
- RAM/UART の base/size/end/role が表示される。
- UART base を変更して Apply できる。
- overlap / 範囲外時に warning/error 行が表示され Apply がブロックされる。
- Reset to Auto で元（自動配置）に戻る。
- Run Status Panel の Address Map summary が Apply 後に更新される。
- （永続化実装時）保存/読込後に override が維持される。

---

## 12. 今回やらないこと

- Address Map Editor の実装
- project 保存形式の変更（設計のみ。実装は次段分離可）
- runtime 挙動変更（既定）
- game16 layout への切替実装
- ROM / VRAM / Input / Storage runtime
- CPU 命令拡張 / CALL・RET・stack
- HDL / FPGA export
- コード実装 / テスト追加 / part.json 変更
- commit / push

---

## 13. 次に続くパッチ（候補順）

1. `PATCH_ADDRESS_MAP_EDITOR_V08`（本パッチ — GUI で base/size override・既定は現行互換）
2. `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08`（ROM / Input などの runtime 追加・game16 layout 活用）
3. `PATCH_AK32_INSTRUCTION_EXPANSION_V08`（CALL / RET / IN・stack — `stack_top` を layout から）
4. `PATCH_GAME_RUNTIME_MINIMAL_V08`（最小ゲーム runtime）
5. `PATCH_V08_STABILIZE_AND_DOCS`（v0.8 安定化・ドキュメント・PHASE COMPLETE 準備）

> 横断候補（`V08_CODEBASE_REVIEW.md` §4）: Diagnostics Panel / Project Validation / opcode 単一化 /
> テストフィクスチャ整理。
