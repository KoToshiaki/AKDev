# PATCH_VIRTUAL_CIRCUIT_RUNTIME_V05 — ROADMAP

> v0.5 進行中のパッチ。**PHASE COMPLETE ではない。**
> 進捗管理は `PATCH_VIRTUAL_CIRCUIT_RUNTIME_V05_CHECKLIST.md`。
> 親フェーズ: `ROADMAP6.md`（v0.5）。仕様: `UI_SPEC_V05.md` 11-M。

---

## 目的

固定の内部 `_sim_cpu/_sim_ram/_sim_uart` で Hello World を出すだけの構造から、
**Canvas 由来の CircuitPlan をもとに VirtualCircuitRuntime を生成する構造**へ移行する。
AKDev の目的（Canvas のパーツ構成を接続し、Run で仮想回路全体を実行する）に実装を一致させる。

最小ゴール構成: **CPU + RAM + UART**。

## 現状（固定内部回路依存）

| 箇所 | 依存 |
|---|---|
| `win.py:_setup_sim()` | `_sim_*` を固定アドレス（RAM 0x0000-0x00FF / UART 0x0100）で生成。Canvas 非参照 |
| `core/runtime.py` | 既存デバイスを包むだけ。Canvas を見ない |
| `write_program`/`_build` | Canvas から asm 割り当てのみ解決。実行は固定 runtime |
| `_do_run`/`_do_step` | `_has_program()` のみ。接続検証なし |

## 必須条件（今回）

- CPU/RAM/UART パーツを Canvas から検出する。
- CPU–RAM、CPU–UART の wire 接続を解析する。
- 未接続なら **Write Program / Run を失敗させる**。
- 接続済みなら、その構成から VirtualCircuitRuntime を作る。
- Write Program は**接続された RAM** へプログラムを書き込む。
- Run/Step は**接続された CPU** を動かす（RAM から fetch、PC 更新、命令実行）。
- OUT 命令は**接続された UART** デバイスへ出力する。
- UART Console は**接続された UART** の出力だけを表示する。
- 既存 Hello World テストは **CPU+RAM+UART を配置・接続した正しい回路**で成功する形へ更新する。

## 設計

### 1. CircuitPlan（`core/circuit.py` 新規）

`resolve_circuit(nodes, connections) -> dict`

- `nodes`: `[{"node_id","category","part_id","name"}]`
- `connections`: `[{"from_node","to_node"}]`（無向隣接）
- 判定:
  - CPU = `category == "cpu"`
  - RAM = `category == "mem"`
  - UART = `category == "io"` かつ name/part_id に `uart`
- 接続: CPU と RAM/UART 間に wire があるか（ノード隣接）。
- 返値: `{ "ok", "issues":[str], "cpu":node_id|None, "rams":[node_id], "uarts":[node_id], "cpu_present":bool }`
- issues 例: CPU 不在 / 複数 CPU / RAM 不在 / CPU が RAM 未接続 / UART 不在 / CPU が UART 未接続。

### 2. Runtime 生成（`win.py`）

- `_make_sim()` を factory 化（startup と再生成で共用）。`_sim_bus/ram/uart/cpu` と `_runtime` を生成。
- **circuit mode**（`cpu_present == True`）:
  - plan を解決。`ok` でなければブロック（Write/Build/Run/Step）。
  - `ok` なら Write/Build 時に `_make_sim()` で runtime を作り直し、`runtime.plan = plan` をバインド。
  - asm は CPU ノードの `sources.asm` を優先解決。接続 RAM へロード。
- **legacy mode**（`cpu_present == False`）:
  - 従来どおり固定 runtime（既存の非 Canvas テスト・エディタタブ Build/Run を保持）。
- gate ヘルパ `_circuit_guard(action) -> plan|None`（不正なら None + ブロックログ）。
  - Write/Build: guard → ok なら runtime 再生成 → ロード。
  - Run/Step: guard のみ（runtime は再生成しない＝ロード済み状態を保持）。

### 3. アドレスマップ

- 当面デフォルト固定（RAM 0x0000 / UART 0x0100）。アドレスエディタは対象外（将来）。
- 「どのパーツが・接続されているか」を plan が決め、実行を gate/bind する。

### 4. ログ例

- `Circuit built: CPU=node_0001 RAM=['node_0002'] UART=['node_0003']`
- `Write Program blocked — CPU node_0001 is not wired to any RAM`
- `Run blocked — no UART part on canvas`

## 既存を壊さないための注意点

- **legacy mode（CPU なし）は従来動作を完全維持**（`test_v01_flow` / `test_target_build_config` /
  `test_gui_sim_run` / signal overlay の MainWin no-crash 等は Canvas に CPU を置かない＝不変）。
- `_make_sim()` 再生成は Write/Build 時のみ（直後にロード）。Run/Step では再生成しない。
- `core/runtime.py` の `VirtualCircuitRuntime` API は不変（`plan` 属性のみ追加）。
- `Bus.on_access` / `tracing` / `last_transactions` は不変。

## 今回やらないこと

- Storage / Video・VRAM / Input 実装
- 厳密なバスプロトコル / 複雑なアドレスマップエディタ
- Fibonacci / RAM selftest
- FPGA 実機書き込み / HDL 合成
- 複数 CPU 対応の本実装（今回は複数 CPU は issue 扱い）
- git commit / push / PHASE COMPLETE

## 完了条件

- `core/circuit.py` の resolver が存在し、CPU+RAM+UART 接続を解決・検証する。
- circuit mode で未接続なら Write/Run がブロックされる。
- 接続済みなら Canvas 由来 runtime で Write→Run→UART `Hello World !`。
- 既存 Hello World テストが正しい回路構成で成功する形へ更新済み。
- `pytest tests/` 全件通過。
