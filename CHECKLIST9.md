# AKDev CHECKLIST 9

> v0.9 進捗管理チェックリスト（**候補整理のみ**。実装は未着手）。
> **現行の管理ファイルは `ROADMAP9.md` / `CHECKLIST9.md`。**
> 設計詳細・候補は `ROADMAP9.md` を参照。
> v0.8 の進捗は `old/CHECKLIST8.md`（✅ v0.8 PHASE COMPLETE・履歴保管）を参照。
> v0.7 以前（`old/ROADMAP7.md`〜・`old/CHECKLIST7.md`〜）も `old/` に収納済み。

---

# 0. v0.9 開始準備

* [x] `ROADMAP9.md` を作成した（候補整理・2026-07-24）
* [x] `CHECKLIST9.md` を作成した（2026-07-24）
* [x] 前フェーズ資料を `old/` へ整理した（2026-07-24）
  - `git mv` で `ROADMAP8.md` / `CHECKLIST8.md` / `PATCH_*_V08_*` 全資料
    （STABILIZE 含む 17 パッチ分 34 ファイル）を `old/` へ収納
  - root の現行管理ファイルは `ROADMAP9.md` / `CHECKLIST9.md` のみ
* [ ] v0.9 の優先候補をユーザーが決定する（`ROADMAP9.md` 候補 A〜J）
* [ ] 最初のパッチの `PATCH_*_V09_ROADMAP.md` / `..._CHECKLIST.md` を作成する（実装前）

---

# 1. v0.9 候補（未着手・採否未定）

* [ ] A. AK32 branch 拡張（`BNE` / `BEQZ` / `BNEZ`）
* [ ] B. AK32 shift / immediate bitwise（`SHL` / `SHR` / `ANDI` / `ORI`）
* [ ] C. AK32 stack / `CALL` / `RET`
* [ ] D. VRAM Viewer 拡張（palette / 色 / 拡大率 UI）
* [ ] E. Game Runtime 拡張（フレーム同期 / 入力エッジ / ゲームループ / sprite / tile / palette）
* [ ] F. HDL / FPGA export 準備
* [ ] G. project template / sample project
* [ ] H. save / load 強化（`loaded_program` 永続化拡張）
* [ ] I. 複数 RAM の真の共存（16bit アドレス制約・`MULTI_RAM_UNSUPPORTED` の解消）
* [ ] J. 繰越: `tests/test/system.json` 差分の扱いをユーザーが決定（破棄 / コミット / .gitignore 化）

---

# 2. v0.8 からの既知の制約（記録）

* [ ] GUI 目視確認（VRAM Viewer 表示・Run Status 行）— ヘッドレス環境のため v0.8 では未実施
  （ロジックは pytest で検証済み。実施できる環境が得られたら確認する）
