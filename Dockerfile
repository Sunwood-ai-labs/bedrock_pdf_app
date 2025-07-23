FROM ghcr.io/astral-sh/uv:python3.12-bookworm

WORKDIR /workspace
COPY . /workspace

# 依存関係インストール
RUN uv sync

# デフォルトコマンド（ポートは環境変数で上書き可）
ENV PORT=7860
CMD ["uv", "run", "python", "app.py", "--port", "7860"]