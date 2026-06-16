# PATCH_ADDRESS_MAP_V07 — ROADMAP

> v0.7（Plan-driven Virtual Devices & Address Map）2 番目のパッチ。
> 親計画: `ROADMAP7.md` / 進捗: `PATCH_ADDRESS_MAP_V07_CHECKLIST.md`。
> 前提: `PATCH_PLAN_DRIVEN_DEVICES_V07`（circuit mode 64KB RAM + UART MMIO 窓）完了。

---

## 目的

RAM/UART などの仮想デバイスのアドレス範囲を、ハードコードされた bus attach 処理だけでなく、
**明示的な Address Map として管理・検証・表示**できるようにする。今後の RAM/ROM/VRAM/
Storage/Input/Display 追加に備えた土台を作る。

## 現在の問題

- circuit mode のメモリ構成（RAM 64KB / UART 0x0100–0x0107 / RAM が UART 窓を避けて 2 レンジ
  attach）は `_make_sim` 内のハードコードで、構造化データとして取り出せない。
- overlap 検出の仕組みがない。
- 現在の構成を Log や外部から確認できない。

## 実装方針

1. **builder/validator/formatter を `core/circuit.py` に追加（純関数・単体テスト可能）**
   - `build_address_map(...)` — base/size から logical device + bus attach ranges を構築。
   - `validate_address_map(amap)` — **bus attach ranges のみ**で意図しない overlap を検出。
   - `format_address_map_summary(amap)` — Log 用サマリ行を生成。
2. **`_make_sim(plan)` を Address Map 駆動にする**
   - devices 構築後に `build_address_map` で amap を作り、**amap の attach_ranges どおりに bus へ
     attach**（bus と Address Map の一致を保証）。
   - `self._runtime.address_map = amap` に保持（`win.address_map()` でも参照可）。
3. **Write Program / Run 時に Address Map summary を Log 出力**
   - `_bind_circuit_runtime`（Write/Build）で "Circuit built:" の後にサマリ＋検証 issue を出す。
   - circuit mode の Run 開始時にもサマリを出す（legacy mode は出さない＝従来ログ維持）。

## Address Map のデータ構造（案A: logical device + attach ranges）

```python
{
  "mode": "circuit",                 # "circuit" | "legacy"
  "devices": [
    {
      "kind": "ram", "node_id": "node_0002", "device_id": "sim_ram",
      "base": 0x0000, "size": 0x10000, "end": 0xFFFF, "label": "RAM",
      "role": "memory", "readable": True, "writable": True,
      "attach_ranges": [(0x0000, 0x00FF), (0x0108, 0xFFFF)],  # 実 bus レンジ
      "reserved":      [(0x0100, 0x0107)],                    # MMIO 窓として除外
    },
    {
      "kind": "uart", "node_id": "node_0003", "device_id": "sim_uart",
      "base": 0x0100, "size": 0x0008, "end": 0x0107, "label": "UART",
      "role": "mmio", "readable": True, "writable": True,
      "attach_ranges": [(0x0100, 0x0107)],
      "overlay": "ram",                                       # RAM 内 MMIO 窓
    },
  ],
}
```

- **logical range**（base/size/end）と **bus attach ranges** を分離（案A）。
- UART が RAM の logical 範囲内にある場合は `role="mmio"` / `overlay="ram"`、RAM 側は `reserved` に窓を記録。
- これにより「RAM logical が UART を内包する」のは意図的な MMIO overlay として表現し、**unintended
  overlap とは区別**する。

## circuit mode / legacy mode の扱い

| モード | RAM | UART | overlay |
|---|---|---|---|
| circuit | base 0x0000 / size 0x10000 / end 0xFFFF、attach [(0x0000,0x00FF),(0x0108,0xFFFF)] | base 0x0100 / size 8 / end 0x0107、attach [(0x0100,0x0107)] | UART = RAM 内 MMIO 窓 |
| legacy | base 0x0000 / size 0x0100 / end 0x00FF、attach [(0x0000,0x00FF)] | base 0x0100 / size 8 / end 0x0107 | overlay なし（隣接）|

legacy も Address Map を持つ（メタデータのみ・挙動は不変）。

## UI / Log 表示方針

本格的な Address Map Editor は作らない。Write Program / Run 時に Log へサマリを出す。

```text
Circuit built: CPU=node_0001 RAM=['node_0002'] UART=['node_0003']
Address Map:
  RAM  node_0002  0x0000-0xffff  64KB
  UART node_0003  0x0100-0x0107  8B MMIO
```

Properties / Run Status Panel の本格表示は後続パッチ。

## テスト方針（`tests/test_address_map_v07.py` 新規）

- circuit mode で Address Map が作られる / RAM・UART の base/size/end が正しい
- UART が 0x0100–0x0107 に残っている
- 既定の RAM+UART 構成が valid（issue 空）
- 意図しない overlap を `validate_address_map` が検出する（単体）
- Write Program 後に `win._runtime.address_map` を参照できる / Run 後も維持
- legacy mode の Address Map（RAM 256B / overlay なし）
- bus attach ranges が Address Map と一致（高位 read/write・UART 窓）
- 既存 Plan-driven / Step Trace テストが壊れない

## 今回やらないこと

Address Map Editor / 高度な編集 UI / 複数 RAM・UART 本格対応 / VRAM・Storage・Input・Display /
MMU / 割り込み / CPU-RAM selftest / Fibonacci / Target CPU Selection / Run Status Panel 本体 /
Port Detail 本体 / commit / push。

## 既存互換性の注意点

- `self._address_map`（アセンブラの addr→line マップ）と名前衝突しないよう、Address Map は
  `self._runtime.address_map`（と `win.address_map()`）に保持する。
- circuit mode の bus attach は従来と同一レンジ（amap 経由で再現）。挙動不変。
- legacy mode の挙動（RAM 256B / UART 0x0100 / "Hi" / 既存テスト）は不変。Run の追加ログは
  circuit mode のみ。
