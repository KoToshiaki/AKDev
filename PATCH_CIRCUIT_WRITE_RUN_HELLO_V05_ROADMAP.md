# PATCH_CIRCUIT_WRITE_RUN_HELLO_V05 — ROADMAP

> v0.5 UI Polish & Usability の一部。Canvas 上の CPU パーツに割り当てた ASM を**仮想回路へ書き込み**、
> Run 後に UART Console へ `Hello World !` を表示する。
> 進捗管理は `PATCH_CIRCUIT_WRITE_RUN_HELLO_V05_CHECKLIST.md`。
> 仕様の親文書は `ROADMAP6.md` / `UI_SPEC_V05.md`（11-L）。

---

## 0. 位置づけ（重要）

- ここでいう**「書き込み」は FPGA 実機書き込みではない**。AKDev 内の**仮想 CPU / 仮想 RAM /
  仮想回路へ ASM を assemble してロード**する意味。
- **テスト用の最小実装**だが、将来の正式な **Build Graph / ROM イメージ / 実機書き込み** へ
  差し替えやすい構造（`loaded_program` を dict で整理）にする。
- **固定 hello_world.asm 専用ではない**。`sources.asm` 割り当て（PATCH_PART_PROGRAM_ASSIGN_V05）を
  優先順位で解決して読む。テストには `tests/test/hello_world.asm` を使う。

## 1. 目的

CPU パーツに `tests/test/hello_world.asm` を割り当て → `Write Program`（仮想回路へロード）→ `Run`
→ UART Console に `Hello World !` を表示する一連を成立させる。

## 2. テスト用 ASM

- `tests/test/hello_world.asm` を新規作成。既存 `src/hello.asm` と同じ命令体系・同じ UART 出力方式
  （UART base 0x100 へ LDI+OUT で 1 文字ずつ送出）で `Hello World !\n` を出力する。
- 既存アセンブラ（`asm/asm.py`: LDI/OUT/HALT 等）で assemble でき、既存 CPU emulator で Run できる。
- テストは emulator を通した UART 出力に `Hello World !` が含まれることを確認する
  （文字列を直接差し込まない）。

## 3. Write Program / Load to Circuit

- Run リボンタブに `Write Program` ボタンを追加（ショートカットは今回不要）。
- 実行時: Canvas から ASM source を**優先順位**で解決 → 存在チェック → assemble → 既存 RAM/CPU へロード。
- 成功: ログ `Program written to circuit: <node_id> <- <path>`。
- 失敗: `No ASM source assigned` / `Program source not found: ...` / assemble 失敗ログ。

### ASM source 解決の優先順位（既存を流用）

1. 選択中 PartNode の `sources.asm`
2. Canvas 内の CPU カテゴリ part の `sources.asm`
3. Canvas 内で最初に見つかった `sources.asm`
4. 無ければ既存エディタタブ Build 経路（フォールバック）

`Canvas.resolve_program_node()` を追加し node_id も返す（`resolve_program_source` はこれを使う形に
リファクタし後方互換を維持）。

## 4. loaded_program 状態（セッション中）

```json
{ "loaded_program": { "source_type": "asm", "path": "tests/test/hello_world.asm",
                      "target_node_id": "node_0001", "status": "loaded" } }
```

- 今回は system.json へ**永続保存しない**（セッション中の runtime 状態、MainWin が保持）。
- 将来保存できるよう dict 形式で整理。既存 Build/Run と矛盾させない。

## 5. Run 接続

- `Write Program` 成功で既存 RAM/CPU にロード済みになる（`_assemble_and_load` を再利用）。
- その後 `Run`（既存 `_do_run`）を押すとロード済みプログラムが実行され UART に出力。
- 既存の `Build → Run` 経路・hello.asm headless 検証（UART "Hi"）は不変。

## 6. Properties 表示

- Program / Sources セクションに Loaded 状態を最小表示: `Loaded: Yes/No` / `Loaded Target` /
  `Loaded Program`。未ロードは `Loaded: No`。Wire Properties / Part Visual パレットは不変。

## 7. 右クリック

- 可能なら PartNode 右クリックに「Write Program to Circuit」を追加（Run タブのボタンを優先）。

## 8. 今回やらないこと

FPGA 実機書き込み / ROM イメージ生成 / Build Graph 本実装 / Canvas 配線からの CPU・RAM・ROM・UART
自動解決 / 複数 CPU の厳密な選択 UI / 内蔵エディタ / ブレークポイント / ステップ UI 改修 /
C コンパイラ / HDL 合成 / source watcher / Port Detail 本実装 / Part Visual サイズ変更 /
`ui/canvas.py` 分割 / Undo・Redo / PHASE COMPLETE / commit / push。

## 9. 後方互換の担保

- `resolve_program_source` は `resolve_program_node` 経由に変えても戻り値（path）は同一。
- `_assemble_and_load` は bool を返すよう拡張（`_build` は戻り値を使わないので不変）。
- 既存 Program/Sources 割り当て・Build/Run・hello.asm headless・Wire Style・Wiring は無改変。

## 10. 将来課題

`loaded_program` の system.json 永続化 / Build Graph（Canvas 配線解決）/ ROM イメージ生成 /
実機書き込み / 複数 CPU・複数プログラム。

## 11. 完了条件

- 上記 2〜7 が実装され `..._CHECKLIST.md` が全 `[x]`。
- `pytest tests/` 全件通過。`Write Program` → `Run` → UART `Hello World !`、hello.asm の UART "Hi" 維持。
