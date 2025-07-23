# AWS Bedrock PDF App - タスクランナー

# デフォルトタスク（just実行時）
default:
    @just --list

# 初回セットアップ
setup:
    @echo "🚀 プロジェクトをセットアップしています..."
    uv sync
    @echo "✅ セットアップ完了！"

# 依存関係の同期
sync:
    @echo "📦 依存関係を同期しています..."
    uv sync

# アプリ実行
run:
    @echo "🚀 アプリを起動しています..."
    uv run python app.py

# 開発環境セットアップ
dev:
    @echo "🔧 開発環境をセットアップしています..."
    uv sync --extra dev
    @echo "✅ 開発環境準備完了！"

# コード整形
format:
    @echo "🎨 コードを整形しています..."
    uv run black app.py
    @echo "✅ コード整形完了！"

# リント実行
lint:
    @echo "🔍 コードをチェックしています..."
    uv run ruff check app.py

# リントとフォーマット修正
fix:
    @echo "🔧 コードを自動修正しています..."
    uv run ruff check --fix app.py
    uv run black app.py
    @echo "✅ コード修正完了！"

# テスト実行（将来用）
test:
    @echo "🧪 テストを実行しています..."
    uv run pytest

# 全体チェック（CI用）
check: lint test
    @echo "✅ 全てのチェックが完了しました！"

# クリーンアップ
clean:
    @echo "🧹 クリーンアップしています..."
    rm -rf .venv __pycache__ *.pyc .pytest_cache .ruff_cache
    @echo "✅ クリーンアップ完了！"

# AWS認証確認
check-aws:
    @echo "🔐 AWS認証情報を確認しています..."
    @if [ -z "$AWS_ACCESS_KEY_ID" ]; then \
        echo "❌ AWS_ACCESS_KEY_IDが設定されていません"; \
        exit 1; \
    fi
    @if [ -z "$AWS_SECRET_ACCESS_KEY" ]; then \
        echo "❌ AWS_SECRET_ACCESS_KEYが設定されていません"; \
        exit 1; \
    fi
    @echo "✅ AWS認証情報が設定されています"

# 本番実行（AWS認証チェック付き）
start: check-aws
    @echo "🚀 本番モードでアプリを起動しています..."
    uv run python app.py
