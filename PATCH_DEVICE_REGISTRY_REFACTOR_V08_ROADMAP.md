# PATCH_DEVICE_REGISTRY_REFACTOR_V08 — ROADMAP（設計資料）

> v0.8（Device Expansion & Connection Validation）の **4 番目の候補パッチ**の設計資料。
> 本書は設計のみ。**実装・テスト追加・part.json 変更・挙動変更・commit/push は行わない。**
> 親計画: `ROADMAP8.md` / `CHECKLIST8.md`。所見: `V08_CODEBASE_REVIEW.md`。
> 前提: `PATCH_PORT_SCHEMA_V08` / `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08` /
> `PATCH_BUS_PROTOCOL_VALIDATION_V08` 完了（`pytest tests/` 937 passed）。

---

## 1. 目的

- 現在の **RAM/UART 固定寄り**の実行デバイス生成・Address Map 生成を **device list driven** に整理する。
- Address Map 生成を `ram_node` / `uart_node` 固定引数ではなく **device spec のリスト**から作れる形へ寄せる。
- `_make_sim()` / `build_address_map()`（/ 必要なら `resolve_circuit()`）の責務を整理する。
- RAM / UART に加えて将来 ROM / VRAM / Input / Storage を追加しやすい土台を作る。
- `mem.vram` を RAM と誤認しうる **category 依存判定**を、**part_id / device kind ベース**へ移行する土台を作る。
- ただし **複数 RAM/UART の本対応・新デバイスの runtime 実装はしない**。既存 RAM/UART/CPU 挙動は完全維持。

### スコープ（明確化）

本パッチは「**device spec 構造の定義 + 分類器 + Address Map をリスト駆動化 + `_make_sim` の分割（挙動不変）+ VRAM≠RAM の土台**」まで。複数デバイス実行・新デバイス runtime・resolve_circuit の分類変更は**次パッチ以降**。

---

## 2. 現在の問題

- `ui/win.py:_make_sim()` は **単一 RAM/UART 前提**（`plan["rams"][0]` / `plan["uarts"][0]` のみ、`RamPart("sim_ram")` と `UartPart("sim_uart")` を各 1 個だけ生成）。
- `core/circuit.py:build_address_map()` が **RAM/UART 専用シグネチャ**（`ram_node`/`uart_node`/`ram_base`/...）。N デバイスに開いていない。
- `resolve_circuit()` の `_is_ram` は **`category == "mem"`** 判定。`mem.vram` も category "mem" のため **VRAM を RAM と誤認**しうる。ROM/Input には判定が無い。
- Address Map に載る device の **kind / base / size / attach range を共通形式**で扱う仕組みがない（RAM/UART がハードコード）。
- `PATCH_BUS_PROTOCOL_VALIDATION_V08` で bus group は可視化されたが、**runtime 生成側（`_make_sim`）には未反映**。
- 複数 RAM/UART・新デバイス追加へ進む前に、**device registry の考え方**（「placed part → 分類された device spec → runtime/Address Map」）を整理する必要がある。

---

## 3. device registry / device spec 方針

### device spec（実行デバイスを表す共通構造）案

```python
{
    "node_id":        "node_0002",
    "part_id":        "mem.ram",
    "category":       "mem",
    "kind":           "ram",          # ram|rom|vram|uart|gpio|timer|video|bridge|fpga|cpu|unsupported
    "role":           "memory",       # memory|mmio|io|cpu|none （アドレス空間上の役割）
    "addressable":    True,           # bus / Address Map に載るか（CPU は False）
    "runtime_backed": True,           # 今 runtime Part があるか（RAM/UART/CPU=True、他=False）
    "runtime_id":     "sim_ram",      # bus トレース/overlay の安定 id（sim_ram/sim_uart/sim_cpu）
    "base":           0x0000,
    "size":           0x10000,
    "end":            0xFFFF,
    "attach_ranges":  [(0x0000, 0x00FF), (0x0108, 0xFFFF)],
    "reserved":       [(0x0100, 0x0107)],   # carve-out（MMIO 窓など）
    "overlay":        None,                 # "ram" 等（窓が別 device の中にある場合）
    "part":           {...},                # 正規化済み part dict
}
```

検討項目の整理:

| 項目 | 方針 |
|---|---|
| node_id / part_id / category | placed node から取得 |
| **kind** | **part_id ベースで分類**（category 依存をやめる第一歩）。`mem.ram`→ram / `mem.vram`→vram / `io.uart`→uart … |
| **role** | アドレス空間上の役割: `memory`（RAM/VRAM/ROM）/ `mmio`（UART 等の窓）/ `io` / `cpu` / `none`（video.out 等 非バス）|
| base / size / end | addressable な device のみ。既定は現行（RAM 0x0000/64KB、UART 0x0100/8B）|
| attach_ranges / reserved / overlay | Address Map と同じ表現。MMIO 窓のくり抜きを表す |
| mmio / memory / device 区別 | `role` で表現（memory / mmio / io）|
| runtime_id | RAM=sim_ram / UART=sim_uart / CPU=sim_cpu（**現行 id 維持**＝bus トレース・overlay・既存テスト互換）|
| addressable | CPU=False（master）、RAM/UART=True |
| **runtime_backed** | 今 runtime 化されているか。RAM/UART/CPU のみ True。他は spec は作るが**生成しない** |
| target CPU から見た到達性 | 本パッチでは spec に持たせない（次段）。bus_validation / 次パッチへ |
| legacy mode 互換 | legacy は固定 256B RAM + UART 0x0100 の spec を同じ構造で作る |

---

## 4. 対象デバイスの分類方針

`device_kind(part)` を **part_id ベース**で分類（category はフォールバック）。今回 **runtime 化するのは RAM/UART/CPU のみ**。

| part_id | kind | role | addressable | runtime_backed（今回）|
|---|---|---|---|---|
| `cpu.ak32` | cpu | cpu | False | ✅（sim_cpu）|
| `mem.ram` | ram | memory | True | ✅（sim_ram）|
| `io.uart` | uart | mmio | True | ✅（sim_uart）|
| `mem.vram` | **vram** | memory | True | ❌（**RAM として扱わない**・次段で runtime 化）|
| `io.gpio` | gpio | mmio | True | ❌ |
| `io.timer` | timer | mmio | True | ❌ |
| `video.regs` | video | mmio | True | ❌ |
| `video.out` | video | none | False | ❌（非バス・映像出力）|
| `bus.bridge` | bridge | none | —（橋渡し）| ❌ |
| `fpga.generic` / `fpga.ecp5_85f` | fpga | none | False | ❌（プレースホルダ）|
| その他 | unsupported | none | False | ❌ |

重要:
- 今回は **全 device を runtime 化しない**。RAM/UART/CPU の既存挙動維持を最優先。
- ただし上表の分類器は将来追加しやすい形（part_id → kind/role/addressable/runtime_backed）で先に入れる。
- **`mem.vram` の kind は `vram`**（`ram` ではない）= VRAM≠RAM の土台。

---

## 5. Address Map refactor 方針

現状: RAM 64KB / UART MMIO 窓 `0x0100–0x0107` / RAM attach は窓を避ける / overlap は `validate_address_map` / legacy 維持。

案:
- `core/circuit.py` に **`build_address_map_from_devices(mode, device_specs)`** を追加し、addressable な device spec のリスト（base/size/role）から `{"mode", "devices":[...]}` を生成する。
- 既存 **`build_address_map(ram_node, uart_node, ...)` は薄いラッパとして維持**（内部で RAM/UART 2 spec を作り新関数へ委譲）。→ `tests/test_address_map_v07.py` は無改変で通る。
- device spec ごとに base/size/attach_ranges/reserved/overlay を持つ。MMIO 窓（UART が RAM の中）のくり抜きロジックは現行を**一般化**（「memory device の中に mmio device の窓がある」ケースとして表現）。
- 本パッチでは **対象は従来どおり 1 memory（RAM）+ 1 mmio（UART 窓）**。真の N device くり抜き・複数 memory は**次パッチ送り**（内部構造だけ list 駆動にしておく）。
- overlap validation は既存 `validate_address_map`（attach_ranges ベース）を**そのまま活用**。
- summary（`format_address_map_summary`）の出力は**既存と一致**させる（RAM/UART 行・MMIO タグ）。

---

## 6. `_make_sim()` refactor 方針

`ui/win.py:_make_sim(plan)` を、**挙動を変えずに**段階分割する案:

1. `_resolve_device_specs(plan)` … plan（circuit）または legacy から **device spec リスト**を作る
   （CPU/RAM/UART のみ。RAM/UART の base/size/attach は現行値）。
2. `_build_runtime_devices(specs)` … `runtime_backed` な spec から `RamPart`/`UartPart`/`AK32Part` を生成し、
   `runtime_id`（sim_ram/sim_uart/sim_cpu）でひも付け、`attach_ranges` どおり bus に attach。
3. Address Map は `build_address_map_from_devices(mode, addressable_specs)` で生成し `runtime.address_map` へ。

維持する不変条件:
- `self._sim_ram` / `self._sim_uart` / `self._sim_cpu` と `self._sim_*_node` 属性は**そのまま残す**
  （`tests/test_plan_driven_devices_v07.py` 等が直接参照）。
- runtime_id（sim_ram/sim_uart/sim_cpu）・UART 窓 `0x0100–0x0107`・RAM 64KB（circuit）/256B（legacy）は不変。
- circuit / legacy の分岐は `_resolve_device_specs` 内に閉じ込め、`_make_sim` は「specs を組み立てて build」に薄くする。
- 移行は**小さなリファクタ**として行い、各ステップで `pytest tests/` を緑に保つ。

---

## 7. `resolve_circuit()` との関係

- **本パッチでは `resolve_circuit()` の分類ロジック（category 依存）を変更しない**。
  - 理由: target CPU selection（`target_cpu`）・既存 v07 テスト・`cpu`/`rams`/`uarts` キーの互換を壊さないため。
- VRAM≠RAM の保証は **device spec 分類器（part_id ベース）レベル**で与える（`device_kind("mem.vram")=="vram"`）。
  - `_resolve_device_specs` は plan の node を part_id で再分類し、**kind=="ram" のものだけ RAM として runtime 化**する。
  - → VRAM 単独を「RAM」として runtime 化しない土台になる（plan が category で拾っても spec 層で弾く）。
- `resolve_circuit()` を part_id/kind/role ベースへ移行する本格対応は **次パッチ**（`PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08` か専用）。
  - category 依存を残すリスク（VRAM 誤認・新 mem 系の混同）は本書に明記し、次段で解消。
- bus_validation 結果（bus group）は本パッチでは runtime 生成に**まだ使わない**（spec 層の整備が先）。将来 spec 構築の入力にできる。

---

## 8. 実装スコープ案（今回は設計のみ）

推奨スコープ（実装する場合）:
- `core/devices.py`（新規）に device spec 構造 + `device_kind(part)` 分類器 + `build_device_specs(nodes, plan=None)` を定義。
- 既存 **RAM/UART/CPU のみ**を device spec 化（他 kind は spec を作るが runtime 生成しない）。
- `core/circuit.py` に `build_address_map_from_devices(mode, device_specs)` を追加、`build_address_map` は委譲。
- `ui/win.py:_make_sim()` を `_resolve_device_specs` / `_build_runtime_devices` に分割（**挙動完全維持**）。
- `mem.vram` を RAM として扱わない判定（spec 層）を入れる。
- **複数 RAM/UART 本対応・新デバイス runtime・resolve_circuit 分類変更はしない**。

やらないこと: 新 runtime Part（ROM/VRAM/GPIO/Timer/Video）の実装、N device の Address Map くり抜き本対応。

---

## 9. テスト方針（実装時に追加するテスト）

- device spec 生成: CPU/RAM/UART の spec が作れる（kind/role/addressable/runtime_backed/base/size）。
- `device_kind`: `mem.ram`→ram / `mem.vram`→**vram** / `io.uart`→uart / `cpu.ak32`→cpu / 未知→unsupported。
- **`mem.vram` が RAM spec / RAM runtime として扱われない**。
- Address Map: `build_address_map_from_devices` の結果が既存 `build_address_map` と一致（RAM/UART・MMIO 窓）。
- `format_address_map_summary` 出力が既存と一致。
- UART MMIO 窓 `0x0100–0x0107` 維持・RAM attach が窓を避ける・RAM 64KB（circuit）/256B（legacy）。
- `_make_sim` 後の `self._sim_ram`/`_sim_uart`/`_sim_cpu` と runtime_id が不変。
- legacy mode 維持（CPU 未配置）。
- 既存 v07/v08 が無改変で通過: plan-driven devices / address map / cpu-ram validation / target cpu / bus validation / port schema / port validation。
- `python -m pytest tests/` 全通過。

---

## 10. 今回やらないこと

- 複数 RAM/UART 本対応
- ROM / VRAM / Input / Storage の runtime 実装
- Address Map Editor
- MMIO 再配置 / UART 窓の変更
- CPU 命令拡張
- bus bridge routing
- 完全な target CPU 到達性解析
- 接続ブロック
- Diagnostics Panel
- HDL / FPGA export
- `resolve_circuit()` の分類ロジック変更（VRAM 誤認の**本修正**は次段）
- コード実装 / テスト追加 / part.json 変更
- commit / push

---

## 11. 次に続くパッチ（候補順）

1. `PATCH_DEVICE_REGISTRY_REFACTOR_V08`（本パッチ — device spec / list driven 化・挙動不変）
2. `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08`（複数 RAM/UART 共存・N device Address Map・resolve_circuit を kind ベースへ）
3. `PATCH_ADDRESS_MAP_EDITOR_V08`（base/size 編集 UI）
4. `PATCH_CODE_REGION_MMIO_RELOCATION_V08`（コード領域拡張 / UART 窓再配置・可変化）
5. `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08`（ROM / Input などの runtime 追加）

> 横断候補（`V08_CODEBASE_REVIEW.md` §4）: Diagnostics Panel / Project Validation /
> opcode 単一化 / テストフィクスチャ整理。
