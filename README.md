<div align="center">

![](header.png)

# 🤖 AWS Bedrock PDF処理アプリ

<p>
  <img src="https://img.shields.io/badge/Python-3.11-blue?logo=python">
  <img src="https://img.shields.io/badge/Gradio-5.22.0-orange?logo=gradio">
  <img src="https://img.shields.io/badge/AWS%20Bedrock-Enabled-yellow?logo=amazon-aws">
</p>

</div>

AWS BedrockのClaude PDFサポート機能を使用したGradioアプリです。PDFファイルをアップロードしてAIに質問できます。

## ✨ 機能

- 📄 PDFファイルのアップロード（最大4.5MB）
- 🧠 Claude AIによる高度な文書理解
- 📊 チャート・グラフ・表の視覚的分析
- 💬 自然言語での質問・回答

## 🚀 クイックスタート

```bash
# 1. 必要ツールのインストール
brew install just uv  # macOS
# または
scoop install just && curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. プロジェクトセットアップ
just setup

# 3. AWS認証情報設定
export AWS_ACCESS_KEY_ID="your_key"
export AWS_SECRET_ACCESS_KEY="your_secret"

# 4. アプリ起動
just run

# もしくは直接uvで起動
uv run python app.py

# ポートを指定したい場合
just run -- --port 8888
# または
uv run python app.py --port 8888

# 5. Docker Composeで起動（推奨: AWS認証情報は.envファイルで管理）
cp .env.example .env  # 認証情報を記入
docker compose up
```

## 📋 利用可能なコマンド

```bash
just           # コマンド一覧表示
just setup     # 初回セットアップ
just run       # アプリ実行
just start     # AWS認証チェック付き実行
just dev       # 開発環境セットアップ
just format    # コード整形
just lint      # リント実行
just fix       # 自動修正
just clean     # クリーンアップ
```

## 🔧 開発

```bash
# 開発環境セットアップ
just dev

# コード品質チェック
just check

# 自動修正
just fix
```

## 📚 使用例

1. PDFファイルをアップロード
2. 質問を入力（例：「この文書の要約を教えて」）
3. 「処理開始」をクリック
4. AI回答を確認


![alt text](image.png)

## ⚠️ 注意事項

- AWS Bedrockでクオードモデルへのアクセス許可が必要
- PDFサイズは4.5MB以下
- 日本語の質問・回答に対応
