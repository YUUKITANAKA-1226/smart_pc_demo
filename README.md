# Smart PC Demo (LAN Remote Desktop Lite)

ローカルWi-Fi上で Android 端末から次を同時に行うプロトタイプです。

1. **PC → Android**: PC画面の表示（MJPEGストリーム）
2. **Android → PC**: タッチ/キーボード入力の送信

> ファイルを分割し、受信・入力・画面配信を分離しています。

## 構成

- `pc_receiver/server.py`: FastAPIエントリポイント
- `pc_receiver/app/auth.py`: token認証ロジック
- `pc_receiver/app/input_control.py`: WebSocket入力制御
- `pc_receiver/app/screen_stream.py`: 画面キャプチャ配信
- `pc_receiver/templates/controller.html`: Android用UI

## 1. セットアップ（PC）

```bash
cd pc_receiver
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. 起動

```bash
export CONTROL_TOKEN=change-me
python server.py --host 0.0.0.0 --port 8000
```

Android で以下にアクセス:

- `http://<PCのIP>:8000/controller?token=change-me`

例: `http://192.168.1.20:8000/controller?token=change-me`

### 401 Unauthorized が出る場合

- URLの `token=` と `CONTROL_TOKEN` が一致していません。
- 例: `chage-me`（誤字）ではなく `change-me`（正）。

## 3. 操作

- 上部: PC画面のライブ表示
- 画面上のタッチ移動: PCマウス移動
- ダブルタップ: 左クリック
- ボタン: 左/右クリック、Enter、Backspace
- 下部入力欄: スマホの既存キーボード入力をPCへ送信

## 注意

- 同一LAN向けの簡易実装（TLSなし）
- 画質/遅延は `stream.mjpeg?fps=...` で調整可能（1〜20）
- OSにより、キーボード/マウス制御や画面キャプチャに権限が必要
