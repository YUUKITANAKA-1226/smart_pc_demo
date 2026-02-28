# Native Remote Suite (separate track)

このディレクトリは、既存の `lan_remote_bridge`（HTML版）を残したまま、
**専用アプリ化**を進める別トラックです。

## 目的

- 低遅延（MJPEGより滑らか）
- 音声転送対応
- タッチ入力の安定性向上
- UI/UXをネイティブで改善

## 方針

- 映像・音声: WebRTC
- 入力制御: 専用 DataChannel (`input`)
- 認証: ペアリングコード + セッショントークン
- ネットワーク: ローカルWi-Fi限定（同一LAN）

## 構成

- `pc_host_native/`: PC側ホスト（FastAPI + aiortc）
- `android_native_app/`: Android側ネイティブアプリ仕様（Kotlin想定）

## まず動かす（PCホスト）

```bash
cd native_remote_suite/pc_host_native
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py --host 0.0.0.0 --port 9000
```

## 次ステップ

1. Androidで `libwebrtc` / `org.webrtc` を使って offer 作成
2. `/api/webrtc/offer` へ投げて answer を適用
3. DataChannel `input` でマウス/キーボードイベント送信
4. 音声出力のルーティング調整（Androidスピーカー/BT）
