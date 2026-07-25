# AKDev ROADMAP 9

> v0.9 開発計画（**候補整理のみ**。実装は未着手。ユーザー指示後に着手する）。
> **現行の管理ファイルは `ROADMAP9.md` / `CHECKLIST9.md`。**
> v0.8（Device Expansion & Connection Validation）の到達点は
> `old/ROADMAP8.md`（✅ v0.8 PHASE COMPLETE）/ `old/CHECKLIST8.md` を参照。
> v0.7 以前の計画書・チェックリストも `old/` に収納済み。
> 進捗管理は実装開始時に `CHECKLIST9.md` で行う。

---

## v0.8 からの引き継ぎ状況

v0.8 で、接続検証（ports schema v2 / direction・width / bus protocol — いずれも warning only）と
デバイス拡張（Input / ROM / Timer / VRAM）、`MemoryLayout`（LEGACY / CIRCUIT_COMPAT / GAME16）、
Address Map Editor（per-device override）、program target RAM / ROM 切替、AK32 Bitwise
（`AND`/`OR`/`XOR`/`NOT`・opcode 0x0B–0x0E）、ROM+Input+Timer+VRAM の最小ゲーム runtime と
32×32 グレースケール VRAM Viewer まで到達した。

- 終了時テスト: `python -m pytest tests/` = **1182 passed**（21 warnings は PySide6 Deprecation のみ）
- 終了前基準コミット: `be98d65 docs: expand README in English and Japanese`
- 既知の制約: GUI 目視確認はヘッドレス環境のため未実施（ロジックは pytest で検証済み）

---

## v0.9 テーマ（候補・未確定）

方向性はユーザー決定待ち。大きくは「CPU 命令拡張」「ゲーム実行環境の強化」
「エクスポート・プロジェクト基盤」の 3 系統が候補。

---

## v0.9 作業候補（未確定・優先順位は今後決定）

> いずれも**実装未着手**。着手時に `PATCH_*_V09_ROADMAP.md` / `..._CHECKLIST.md` を作成してから始める。

### A. AK32 branch 拡張
- `BNE` / `BEQZ` / `BNEZ` 等の分岐命令追加（v0.8 の `PATCH_AK32_INSTRUCTION_EXPANSION_V08` 設計資料参照）。

### B. AK32 shift / immediate bitwise
- `SHL` / `SHR` / `ANDI` / `ORI` 等。

### C. AK32 stack / CALL / RET
- スタックポインタ・サブルーチン呼び出し。

### D. VRAM Viewer 拡張
- palette / 色表示 / 拡大率 UI（現状は 32×32 グレースケール固定・scale 6x）。

### E. Game Runtime 拡張
- フレーム同期 / 入力エッジ検出 / ゲームループ。sprite / tile / palette の本格実装もこの系統。

### F. HDL / FPGA export 準備
- v0.8 から繰越（未着手のまま）。

### G. project template / sample project
- プロジェクトひな形・サンプル同梱。

### H. save / load 強化
- `loaded_program` 永続化拡張・移植性改善。

### I. 複数 RAM の真の共存
- 16bit アドレス制約により現状は先頭 RAM のみ runtime 実体化（`MULTI_RAM_UNSUPPORTED` warning）。
  v0.8 ROADMAP 候補 F の繰越。

### J. 繰越課題: `tests/test/system.json` 差分の扱い
- テスト実行で差分が出る場合の方針（破棄 / コミット / .gitignore 化）を**ユーザーが決定**する。
  v0.6 からの繰越。勝手に処理しない。

---

## v0.9 ではまだ確定でないこと

- 候補 A〜J の優先順位・採否（ユーザー決定待ち）。
- v0.9 の正式テーマ名。

---

## 今回（v0.8 PHASE COMPLETE 整理）でやらないこと

- 上記候補の実装（計画整理のみ）。
- コード・テスト・依存環境・Git 履歴の変更。
