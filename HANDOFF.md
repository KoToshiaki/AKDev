# AKDev 引き継ぎメモ

更新日: 2026-07-26

過去の詳細な引き継ぎ履歴は `old/HANDOFF_V08_COMPLETE.md`（v0.8 完了時点までの全履歴）を参照。

---

## 現在状態

- ✅ **v0.8（Device Expansion & Connection Validation）は PHASE COMPLETE**（2026-07-24 ユーザー宣言・処理済み）。
- **ブランチ = `dev`** / **終了前基準コミット = `be98d65 docs: expand README in English and Japanese`**。
- **総合テスト**: `python -m pytest tests/` → **1182 passed, 21 warnings**（warning は PySide6 Deprecation のみ）。
- `tests/test/system.json` はテスト実行前後とも**差分なし**。
- **Git 状態の区別**:
  - PHASE COMPLETE 整理の**開始時点**では作業ツリーは clean（`be98d65` と一致）だった。
  - **現在**は、本整理による**意図した文書差分のみ**が未コミットで存在する
    （`old/` への rename・`ROADMAP9.md`/`CHECKLIST9.md`/本ファイル新規・README 修正。コード・テストの差分はなし）。
- **`old/` へ収納済み（`git mv`・削除なし）**:
  - v0.8 フェーズ資料: **PATCH 文書 34 件 + `ROADMAP8.md`/`CHECKLIST8.md` の 2 件 = 合計 36 件**
  - 追加収納: `V08_CODEBASE_REVIEW.md`、旧 `HANDOFF.md` → `old/HANDOFF_V08_COMPLETE.md`
- **v0.9 は候補整理のみ**（`ROADMAP9.md` 候補 A〜J）。**実装・優先候補決定・PATCH 資料作成はすべて未着手**。

## 既知の制約

- **GUI 目視確認は未実施**（ヘッドレス環境のため。VRAM Viewer 表示・Run Status 行のロジックは pytest で検証済み）。
- `tests/test/system.json` に差分が出た場合の扱い（破棄 / コミット / .gitignore 化）は v0.6 からの繰越でユーザー判断待ち。

## 現行文書

- **`ROADMAP9.md` / `CHECKLIST9.md`**（現行の管理ファイル。root のフェーズ計画はこの 2 つのみ）。
- 完了済みフェーズの計画・パッチ資料は `old/` に履歴保管。

## 次に行うべきこと

1. **commit / push**（ユーザー操作）— 本 PHASE COMPLETE 整理の文書差分。
   推奨メッセージ例: `docs: complete v0.8 phase and prepare v0.9 planning`
2. **ユーザーによる v0.9 優先候補の決定**（`ROADMAP9.md` 候補 A〜J）。
   決定後に `PATCH_*_V09_ROADMAP.md` / `..._CHECKLIST.md` を作成してから実装に着手する。
