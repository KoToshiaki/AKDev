# AKDev ERROR LOG

> エラー・既知の不具合の記録。CLAUDE.md ルール 5 に従う。

---

## KI-1: Wire Mode トグルで右クリックが占有され接続できない

- **Date**: 2026-06-06
- **Error Summary**: リボンの Wire Mode トグルを ON にすると、Canvas が wire モードに
  入るが「開始ポート」（`_wire_from`）が設定されない。この状態で PartNode を右クリック
  すると「ここに接続 / キャンセル」メニューが出るが、`_finish_wire()` が
  `_wire_from is None` のため接続が作成されない。さらに wire モード中は右クリックが
  wire 用メニューに占有され、通常の右クリック操作（複製・削除・プログラムを開く等）が
  できなくなる。
- **Cause**: 接続フローが 2 系統に分かれている。
  1. 正規フロー: PartNode 右クリック →「接続を開始」→ `_start_wire(node_id)` が
     `_wire_from` を設定してから wire モードに入る（接続可能）。
  2. リボン Wire Mode トグル: `set_mode("wire")` のみを呼び、`_wire_from` を設定しない
     （接続不可・右クリック占有）。
  リボントグルは「開始ポート未指定の wire モード」という不完全な状態を作る。
- **Solved or Not**: **解決済み（2026-06-06, PATCH_WIRING_V05）**。
- **Solution (PATCH_WIRING_V05)**:
  - wire モードを **armed（始点未選択）/ drawing（始点選択済）** の 2 サブ状態に整理。
  - `_begin_wire_from(node_id, port_name)` を新設し、始点設定・preview 生成・装飾・
    `mode_changed` 発火を集約。`_start_wire()` はこれへ委譲（既存テスト互換）。
  - リボントグル ON は armed。右クリック「ここから接続を開始」で drawing に入り、
    「ここに接続」で接続作成 → design へ戻る（1 始点 1 接続）。
  - wire モード中の右クリックメニューに **通常操作（Properties / プログラムを開く /
    HDLを開く / 複製 / 削除）を併設**。通常操作が死なないようにした。
  - Cancel Wire（リボン）/ Escape / メニュー「Wire Cancel」を `_cancel_wire()` 経由で
    統一し、preview / waypoints / handles / pending / Canvas 装飾を確実にクリア。
  - 状態可視化: ステータスバー + Wiring トグル checked + Canvas 枠のアクセント色。
- **Prevention**: wire モードの開始点設定を `_begin_wire_from()` に一本化し、入口が
  どこでも同じ状態遷移になるようにした。トグル単独では armed 止まりで「接続できない
  drawing 状態」を作らない。wire モード中も通常操作を常に右クリックから到達可能にする。
- **Test**: `tests/test_wiring_v05.py`（17 件）でフロー・キャンセル・装飾・Escape・
  MainWin 連携を検証。`pytest tests/` 551 件全通過。

---

## B1: パーツ削除後に接続 wire が残る

- **Date**: 2026-06-06
- **Error Summary**: PartNode を削除しても接続線（ConnectionLine）と接続データ
  (`_connections`) が残り、存在しないノードへ向かう孤立 wire が Canvas/保存に残った。
- **Cause**: 削除経路が分散（Delete キー / 右クリック削除 / `delete_selected`）し、
  いずれも PartNode のみ scene から除去して接続データ・線を同期削除していなかった。
- **Solved or Not**: **解決済み（2026-06-06, PATCH_WIRING_V05 追加修正）**。
- **Solution**: `_remove_node(node_id)` を単一の削除窓口にし、ノード本体・from/to に
  該当する接続データ・ConnectionLine・wire/pending 状態をまとめて削除。全削除経路
  （`_delete_node` / `delete_selected` / 右クリック design・wire）をこれに集約。
- **Prevention**: ノード削除は必ず `_remove_node()` を通す。scene から PartNode を
  直接 removeItem する旧コードを廃止。`tests/test_canvas_delete.py` で全経路を検証。

---

## B2: wire とパーツの間に隙間ができる

- **Date**: 2026-06-06
- **Error Summary**: snap OFF（自由座標）のパーツで、wire がポートに届かず手前で
  止まって見えた。
- **Cause**: `update_connections` が端点を grid に丸めていたため、ポートが grid 上に
  無い場合に端点がずれた。
- **Solved or Not**: **解決済み（2026-06-06）**。
- **Solution**: BFS/waypoint は grid のまま、ルート生成後に**最初と最後の点だけ実ポート
  座標で上書き**。snap ON/OFF いずれもポートに接し、移動にも追従する。
- **Prevention**: 端点は常に `_from_port_pos` / `_to_port_pos`（実座標）を使う。
  `tests/test_canvas_routing.py` に端点一致・移動追従テストを追加。

---

## B3: 中ボタン Pan 初回で画面が動かず未読込に見える

- **Date**: 2026-06-06
- **Error Summary**: 起動直後に中ボタンドラッグしても Canvas が動かず、エラー/未読込に
  見えた。
- **Cause**: `sceneRect` 未設定で、空シーンでは scrollbar の可動域がゼロ → Pan の
  `setValue` が効かず無反応。grid OFF で背景も無地のため移動が視認できなかった。
- **Solved or Not**: **解決済み（2026-06-06）**。
- **Solution**: 広い `setSceneRect(-2000,-2000,4000,4000)` を初期化、起動時
  `center_origin()`、grid OFF でも原点十字を常時描画、"Canvas ready" を Log/ステータス
  バーに表示。
- **Prevention**: Canvas は固定 sceneRect を持たせ、初期表示で原点中心＋視覚的手がかりを
  入れる。`tests/test_canvas_routing.py` に sceneRect/center テストを追加。

---
