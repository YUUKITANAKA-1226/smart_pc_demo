# Android Native App Plan (Kotlin)

このフォルダは Android 専用アプリ化の実装メモです。

## 技術候補

- Kotlin + Jetpack Compose
- WebRTC: `org.webrtc:google-webrtc`
- 通信: `ktor-client` or `okhttp`

## 最小実装項目

1. ペアコード入力画面
2. PCホストURL入力（例: `http://192.168.1.20:9000`）
3. `/api/webrtc/offer` とのSDP交換
4. 受信VideoTrack表示（SurfaceViewRenderer）
5. DataChannel `input` へ以下送信
   - `mouse_abs` `{x,y}`
   - `mouse_click` `{button}`
   - `key` `{key}`
   - `text` `{text}`
6. IME連携入力（Enter対応）

## 備考

- 音声は WebRTC で MediaStreamTrack を追加すると実装可能。
- まずは video + input で安定化し、次段で audio を追加。
