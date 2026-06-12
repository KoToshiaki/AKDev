# Claude Code Rules

## 1. Required Documents

作業を始める前に、存在する場合は必ず以下のファイルを確認する。

- `CLAUDE.md`
- `ROADMAP.md`
- `CHECKLIST.md`
- `HANDOFF.md`
- `SPEC.md`
- `ERROR.md`

これらの内容を無視して作業を進めてはいけない。

`CLAUDE.md` はユーザー管理の開発ルールファイルである。
Claude Code は、ユーザーから明示的な指示がない限り、`CLAUDE.md` を編集してはいけない。
改善が必要だと判断した場合は、実装せず、ユーザーに提案だけ行う。
---

## 2. Work Scope

編集を始める前に、変更予定のファイルと作業内容を短く提示する。

ユーザーが許可した範囲を超えて、機能追加、UI変更、大規模なリファクタリングを行ってはいけない。

必要だと判断した改善案がある場合は、実装せず、先に提案する。

---

## 3. Roadmap and Checklist

どんなに小さいパッチでも、作業前に `ROADMAP.md` と `CHECKLIST.md` を更新する。

`ROADMAP.md` または `CHECKLIST.md` が存在しない場合は、実装前に作成する。

実装後に後追いで計画を書くことは禁止する。

---

## 4. Phase Completion

`PHASE COMPLETE` は、現在のフェーズを正式に終了し、次フェーズへ移るための下準備を行う専用コマンドである。

通常の作業指示やパッチ指示の先頭に `PHASE COMPLETE` を付ける必要はない。
`PHASE COMPLETE` は、フェーズを閉じる節目でのみ使用する。

フェーズ終了は、以下のどちらかを満たした状態と定義する。

1. `CHECKLIST.md` の現在フェーズに関する項目がすべて `[x]` になった
2. ユーザーが `PHASE COMPLETE` を単独で宣言した

フェーズ終了条件を満たしていない場合、Claude Code は勝手に次のフェーズへ進んではいけない。

一段階の作業が終わったら、Claude Code は作業結果を報告し、そこで停止する。

作業結果報告には、最低限以下を書く。

* 完了した段階名
* 変更したファイル一覧
* 実行したテスト
* テスト結果
* 未確認事項
* 次に行うべき作業

`CHECKLIST.md` の現在フェーズ項目がすべて `[x]` になった場合、Claude Code はフェーズ終了条件を満たしたことを報告し、ユーザーに `PHASE COMPLETE` を出すか確認する。

ユーザーがフェーズ終了を明示する場合は、以下の合図を単独で出す。

```text
PHASE COMPLETE
```

`PHASE COMPLETE` が出た場合、Claude Code はフェーズ完了処理を行う。

フェーズ完了処理では、最低限以下を行う。

1. 現在フェーズの関連ファイルを確認する

   * `ROADMAP.md`
   * `CHECKLIST.md`
   * `HANDOFF.md`
   * フェーズ用またはパッチ用の ROADMAP / CHECKLIST
   * 必要に応じて `SPEC.md` / `ERROR.md`

2. ここまでの全機能に対する総合確認を行う

   * 可能な範囲で全体テストを実行する
   * 実行したコマンドと結果を記録する
   * 確認できない項目がある場合は理由を書く

3. 完了したフェーズの ROADMAP / CHECKLIST を `old/` に収納する

   * 通常フェーズの場合は、使用済みの `ROADMAP.md` / `CHECKLIST.md`
   * 番号付きフェーズの場合は、使用済みの `ROADMAP*.md` / `CHECKLIST*.md`
   * パッチの場合は、使用済みの `PATCH_*_ROADMAP.md` / `PATCH_*_CHECKLIST.md`
   * 収納したファイル名を報告する

4. `HANDOFF.md` を更新する

   * 完了したフェーズ名
   * フェーズ全体の評価
   * 完了した主な機能
   * 実行した総合テスト
   * テスト結果
   * 既知の問題
   * `old/` に収納したファイル
   * 次フェーズの開始点

5. 次フェーズ用の新しい ROADMAP / CHECKLIST を作成する

   * 次の番号の `ROADMAP*.md`
   * 次の番号の `CHECKLIST*.md`
   * 例: `ROADMAP5.md` / `CHECKLIST5.md` が完了した場合は `ROADMAP6.md` / `CHECKLIST6.md`
   * 次フェーズの目的、候補、作業範囲、今回やらないことを整理する
   * ただし、次フェーズの実装は開始しない

6. 作業後に停止し、ユーザー確認を待つ

`PHASE COMPLETE` が出ていない状態で、Claude Code が勝手に以下を行ってはいけない。

* `old/` への収納
* 次フェーズ用 ROADMAP / CHECKLIST の作成
* 次フェーズの実装開始

修正が必要な場合、ユーザーは以下の合図を単独で出す。

```text
PHASE FIX REQUESTED
```

`PHASE FIX REQUESTED` が出た場合、Claude Code は次フェーズへ進まず、現在のフェーズ内で修正を行う。

---

## 5. Error Handling

エラーが発生した場合は、`ERROR.md` に記録する。

`ERROR.md` には、最低限以下を書く。

- Date
- Error Summary
- Cause
- Solved or Not
- Solution
- Prevention

エラーを解決した場合も、解決方法と再発防止策を必ず残す。

---

## 6. File Safety

以下の操作を行う前に、必ずユーザー確認を取る。

- ファイル削除
- フォルダ削除
- 新規ダウンロード
- 外部依存関係の追加
- 既存ファイルの大規模上書き

`pip install`、`npm install`、外部ライブラリ導入も確認対象とする。

---

## 7. Git Safety

以下の Git 操作を行う前に、必ずユーザー確認を取る。

- `git commit`
- `git push`
- `git merge`
- `git rebase`
- `git reset`
- ブランチ作成
- ブランチ切り替え
- タグ作成

勝手にコミットや push をしてはいけない。

---

## 8. Verification

実装後は、可能な範囲で必ず動作確認を行う。

確認した内容、実行コマンド、結果を `CHECKLIST.md` または `HANDOFF.md` に記録する。

確認できない場合は、その理由を書く。

---

## 9. Naming

ファイル名、関数名、クラス名は必要以上に長くしない。

ただし、意味が分からなくなる短縮は避ける。

短く、意味が分かる名前を優先する。

---

## 10. Handoff

意味のある作業単位が終わったら、`HANDOFF.md` を更新する。

`HANDOFF.md` には、最低限以下を書く。

- Current Status
- Completed Work
- Remaining Work
- Known Issues
- Next Recommended Step

---

## 11. Existing Specification Priority

既存の `ROADMAP.md`、`CHECKLIST.md`、`HANDOFF.md`、`SPEC.md` の内容を優先する。

既存仕様と新しい指示が矛盾する場合は、勝手に判断せず、ユーザーに確認する。

---

## 12. No Unrequested Changes

指示されていない変更を勝手に行わない。

特に以下は禁止する。

- ついでの機能追加
- ついでの UI 改善
- ついでのファイル整理
- ついでのリファクタリング
- 仕様にないライブラリ追加

必要だと判断した場合は、実装前に提案だけ行う。

---

## 13. Patch Workflow

バグ修正や小規模修正でも、作業前に必ずパッチ名を決める。

例:

- `v0.4.1 Patch`
- `Save Fix Patch`
- `Canvas Routing Fix Patch`

パッチ作業では、実装前に以下を行う。

- `ROADMAP.md` に Patch セクションを追加する
- `CHECKLIST.md` に Patch セクションを追加する
- 作業範囲を明記する
- 今回やらないことを明記する

実装後に後追いで計画を書くことは禁止する。

---

## 15. Documentation Quality

`README.md`、`ROADMAP.md`、`CHECKLIST.md`、`HANDOFF.md`、`SPEC.md`、`ERROR.md`、`docs/*.md` を編集した場合は、作業後に内容を読み返す。

特に以下を確認する。

- 文章が途中で欠けていないか
- 古い内容と新しい内容が混ざっていないか
- 見出し構造が崩れていないか
- リンク先が存在するか
- 実装内容と記述が矛盾していないか

確認した結果を `HANDOFF.md` または作業報告に書く。
