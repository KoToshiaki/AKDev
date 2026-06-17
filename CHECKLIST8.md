# AKDev CHECKLIST 8

> v0.8 進捗管理チェックリスト（**候補整理のみ**。実装は未着手）。
> **現行の管理ファイルは `ROADMAP8.md` / `CHECKLIST8.md`。**
> 設計詳細・候補は `ROADMAP8.md` を参照。
> v0.7 の進捗は `old/CHECKLIST7.md`（✅ v0.7 PHASE COMPLETE・履歴保管）を参照。
> v0.6 以前（`old/ROADMAP6.md`〜・`old/CHECKLIST6.md`〜）も `old/` に収納済み。

---

# 0. v0.8 開始準備

* [x] `ROADMAP8.md` を作成した（候補整理）
* [x] `CHECKLIST8.md` を作成した
* [x] 前フェーズ資料を `old/` へ整理した（2026-06-17）
  - `git mv` で `ROADMAP6.md` / `CHECKLIST6.md` / `ROADMAP7.md` / `CHECKLIST7.md` を `old/` へ収納
  - root の現行管理ファイルは `ROADMAP8.md` / `CHECKLIST8.md` のみ（v0.6 / v0.7 は完了済み履歴）
* [ ] v0.8 テーマを確定する（候補: Device Expansion & Connection Validation）
  - 完了条件: ユーザーがテーマと最初のパッチを決定する
* [ ] 最初のパッチの実装範囲をユーザーが承認する
  - 完了条件: ユーザーから実装開始の明示的な指示がある
* [ ] 最初のパッチの `PATCH_*_V08_ROADMAP.md` / `..._CHECKLIST.md` を作業前に作成する

---

# 1. v0.8 作業候補（未確定・着手時に個別 CHECKLIST 化）

> 以下は候補。優先順位・取捨選択はユーザー判断で確定する。実装項目化は着手時に行う。

* [ ] A. Port direction / width validation
* [ ] B. Bus protocol validation
* [ ] C. 複数 RAM / UART handling
* [ ] D. ROM / VRAM / Storage / Input device expansion
* [ ] E. Address Map Editor
* [ ] F. コード領域拡張 / UART MMIO 窓の再配置・可変化
* [ ] G. CPU 命令拡張（CALL / RET / IN）
* [ ] H. ゲーム runtime 準備
* [ ] I. HDL / FPGA export 準備

---

# 2. 繰越課題（v0.6 → v0.7 → v0.8）

* [ ] `tests/test/system.json` のテスト実行差分の扱いをユーザーが決定する
  - 完了条件: 破棄 / コミット / .gitignore 化 のいずれかをユーザーが選ぶ（勝手に破棄しない）

---

# 3. 注意事項

* このフェーズは候補整理のみ。新機能実装・挙動変更・テスト追加・commit / push は未実施。
* 実装は、ユーザーが最初のパッチを指示してから着手する。
