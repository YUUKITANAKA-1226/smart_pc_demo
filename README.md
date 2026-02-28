# Smart PC Demo (Android → PC control)

ローカルWi-Fi上で Android 端末から PC を **ワイヤレスキーボード + タッチパッド** のように操作する最小構成プロトタイプです。

- PC側: FastAPI + WebSocket 受信サーバ
- Android側: ブラウザで開くコントローラーUI（インストール不要）

> まずは「android → PC の入力デバイス化」に絞って実装しています。

## 1. セットアップ（PC）

```bash
cd pc_receiver
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## 2. 起動

```bash
export CONTROL_TOKEN=change-me
python server.py --host 0.0.0.0 --port 8000
```

起動後、PCのIPアドレスを確認して Android で以下にアクセス:

- `http://<PCのIP>:8000/controller?token=change-me`

例: `http://192.168.1.20:8000/controller?token=change-me`

## 3. 使い方

- 上部の灰色エリア: タッチパッド（1本指でマウス移動）
- ボタン:
  - Left Click
  - Right Click
  - Enter
  - Backspace
- 下部入力欄:
  - スマホの通常キーボード（ローマ字入力/日本語IME含む）で入力
  - `送信` でまとめてPCへタイプ
  - 入力欄で Enter を押すと Enter キーとして送信

## セキュリティ注意

- 同一LAN利用を前提
- `CONTROL_TOKEN` を必ず変更してください
- 必要なら OS ファイアウォールで接続元を制限してください

## 制限事項

- 画面転送（PC→Android）は未実装
- 操作イベントは平文HTTP/WebSocket（LAN内の簡易利用向け）
- PC側でマウス/キーボード制御ライブラリの権限設定が必要な場合があります
