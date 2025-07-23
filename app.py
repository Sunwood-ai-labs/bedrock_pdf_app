import gradio as gr
import boto3
import json
import os
import socket
import logging
from botocore.exceptions import ClientError

# ログ設定
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class BedrockPDFProcessor:
    """AWS BedrockでPDF処理を行うクラス（記事準拠版）"""
    
    def __init__(self, region="us-east-1"):  # 記事と同じリージョンに変更
        # IAM認証を優先して使用
        try:
            # デフォルトの認証情報チェーン（IAMロール、環境変数、~/.aws/credentials）を使用
            self.bedrock_client = boto3.client("bedrock-runtime", region_name=region)
            
            # 認証テスト
            sts_client = boto3.client('sts', region_name=region)
            identity = sts_client.get_caller_identity()
            logger.info(f"AWS認証成功: {identity['Arn']}")
            
        except Exception as e:
            logger.error(f"AWS認証エラー: {str(e)}")
            raise
            
        # 記事と同じモデルIDを使用
        self.model_id = "us.anthropic.claude-sonnet-4-20250514-v1:0"
    
    def generate_message(self, input_text, input_document_path):
        """
        記事準拠のドキュメント処理メソッド（Citations有効）
        """
        logger.info(f"Generating message with model {self.model_id}")
        
        try:
            # ファイル形式を取得
            input_document_format = input_document_path.split(".")[-1]
            
            # ドキュメントを読み込み
            with open(input_document_path, 'rb') as input_document_file:
                input_document = input_document_file.read()
            
            # ファイル名をサニタイズ（記事では単純に"PDF"を使用）
            base_name = os.path.splitext(os.path.basename(input_document_path))[0]
            sanitized_name = ''.join(c for c in base_name if c.isalnum())
            if not sanitized_name:
                sanitized_name = "PDF"  # 記事と同じ名前を使用
            
            # メッセージを構築（記事と完全に同じ構造）
            message = {
                "role": "user",
                "content": [
                    {"text": input_text},
                    {
                        "document": {
                            "name": sanitized_name,
                            "format": input_document_format,
                            "source": {"bytes": input_document},
                            "citations": {"enabled": True},  # 記事通りここに配置
                        }
                    },
                ],
            }
            
            messages = [message]
            
            # 記事準拠でConverse APIを呼び出し
            response = self.bedrock_client.converse(
                modelId=self.model_id,
                messages=messages
            )
            
            return response
            
        except ClientError as e:
            logger.error(f"AWS APIエラー: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"処理エラー: {str(e)}")
            raise
    
    def process_pdf(self, pdf_file, question):
        """
        PDFファイルを処理して質問に回答（Gradio用のラッパー）
        """
        try:
            # generate_message メソッドを使用
            response = self.generate_message(question, pdf_file)
            
            # レスポンスから結果を抽出（記事準拠）
            output_message = response['output']['message']
            
            # 記事通りにcontentを処理（複数のtextブロックに対応）
            result_text = ""
            content_blocks = output_message['content']
            
            # 記事のように全てのtextブロックを結合
            for content in content_blocks:
                if 'text' in content:
                    result_text += content['text']
            
            # デバッグ用：レスポンス構造をログ出力
            logger.info("レスポンス構造:")
            logger.info(json.dumps(content_blocks, indent=2, ensure_ascii=False))
            
            # トークン使用量をログ出力
            if 'usage' in response:
                token_usage = response['usage']
                logger.info(f"Input tokens: {token_usage.get('inputTokens', 'N/A')}")
                logger.info(f"Output tokens: {token_usage.get('outputTokens', 'N/A')}")
                logger.info(f"Total tokens: {token_usage.get('totalTokens', 'N/A')}")
                
                # トークン情報を結果に追加
                token_info = f"\n\n---\n📊 トークン使用量: 入力 {token_usage.get('inputTokens', 'N/A')}, 出力 {token_usage.get('outputTokens', 'N/A')}, 合計 {token_usage.get('totalTokens', 'N/A')}"
                result_text += token_info
            
            # 停止理由をログ出力
            logger.info(f"Stop reason: {response.get('stopReason', 'N/A')}")
            
            # Citations機能が有効であることを明示
            result_text += f"\n🔗 Citations機能: 有効 (PDF画像認識対応)"
            
            return result_text
            
        except ClientError as e:
            error_msg = str(e)
            
            # 特定のエラーメッセージに対する詳細な対処法
            if "Extra inputs are not permitted" in error_msg and "citations" in error_msg:
                return f"""❌ Citations機能エラー: {error_msg}

🔧 考えられる原因:
1. リージョンでCitations機能がまだ利用できない
2. モデルがCitations機能をサポートしていない  
3. AWSアカウントでの機能有効化が必要

💡 対処法:
1. リージョンを ap-northeast-1 に変更してください
2. モデルIDを apac.anthropic.claude-sonnet-4-20250514-v1:0 に変更してください
3. AWSサポートに機能の利用可能性を確認してください

現在使用中:
- リージョン: {self.bedrock_client.meta.region_name}
- モデルID: {self.model_id}"""
            
            elif "ValidationException" in error_msg and "file name" in error_msg:
                return f"ファイル名エラー: ファイル名に使用できない文字が含まれています。\n詳細: {error_msg}\n\n対処法: ファイル名を英数字のみに変更してください。"
            
            return f"AWS APIエラー: {error_msg}"
            
        except Exception as e:
            return f"エラーが発生しました: {str(e)}"


def find_available_port(start_port=7860, max_port=7870):
    """利用可能なポートを見つける"""
    for port in range(start_port, max_port + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('', port))
                return port
        except OSError:
            continue
    return None


def create_app():
    """Gradioアプリを作成"""
    processor = BedrockPDFProcessor()
    
    def handle_pdf_upload(pdf_file, question):
        """PDF処理のハンドラー"""
        if not pdf_file:
            return "PDFファイルを選択してください。"
        
        if not question.strip():
            return "質問を入力してください。"
        
        return processor.process_pdf(pdf_file, question)
    
    def show_filename_info(pdf_file):
        """ファイル名の情報を表示"""
        if not pdf_file:
            return "ファイルが選択されていません"
        
        original = os.path.basename(pdf_file)
        # 英数字のみに変換
        base_name = os.path.splitext(original)[0]
        sanitized = ''.join(c for c in base_name if c.isalnum())
        if not sanitized:
            sanitized = "PDF"  # デフォルト名
        
        if base_name == sanitized:
            return f"✅ ファイル名: {original} (問題なし)"
        else:
            return f"⚠️ 元の名前: {original}\n✅ 使用される名前: {sanitized}.pdf"
    
    # Gradioインターフェース作成
    with gr.Blocks(title="AWS Bedrock PDF処理 (記事準拠版)") as app:
        gr.Markdown("# 🤖 AWS Bedrock PDF処理アプリ (記事準拠版)")
        gr.Markdown("Qiita記事で検証済みのCitations実装パターンを使用。PDF画像認識に対応。")
        
        with gr.Row():
            with gr.Column():
                pdf_input = gr.File(
                    label="📄 PDFファイル",
                    file_types=[".pdf"],
                    type="filepath"
                )
                filename_info = gr.Textbox(
                    label="📝 ファイル名情報",
                    lines=2,
                    interactive=False
                )
                question_input = gr.Textbox(
                    label="❓ 質問",
                    placeholder="PDFの内容について質問してください...",
                    lines=3
                )
                submit_btn = gr.Button("🚀 処理開始", variant="primary")
            
            with gr.Column():
                output = gr.Textbox(
                    label="🤖 AI回答",
                    lines=15,
                    max_lines=20
                )
        
        # イベント設定
        pdf_input.change(
            fn=show_filename_info,
            inputs=pdf_input,
            outputs=filename_info
        )
        
        submit_btn.click(
            fn=handle_pdf_upload,
            inputs=[pdf_input, question_input],
            outputs=output
        )
        
        # 使用例と注意事項
        gr.Markdown(f"""
        ## 📚 使用方法
        1. **PDFファイルをアップロード** - 対応形式: PDF
        2. **質問を入力** - 例：「この文書の要約を教えて」「主なポイントは？」
        3. **処理開始ボタンをクリック** - Claude Sonnet 4がPDFを分析して回答
        
        ## ⚙️ 技術仕様（記事準拠版）
        - **リージョン**: ap-northeast-1 (記事と同じ)
        - **モデル**: apac.anthropic.claude-sonnet-4-20250514-v1:0 (記事と同じ)
        - **API**: Converse API + Citations機能
        - **実装**: Qiita記事で検証済みのパターンを使用
        
        ## 🔗 Citations実装（記事準拠）
        ```python
        {{
            "document": {{
                "name": "PDF",
                "format": "pdf", 
                "source": {{"bytes": pdf_data}},
                "citations": {{"enabled": True}},  # ← 記事通りここに配置
            }}
        }}
        ```
        
        ## 📋 重要な注意
        - **リージョン**: ap-northeast-1 を使用（記事と同じ）
        - **Citations機能**: まだ全リージョンで利用できない可能性
        - **PDF画像認識**: Converse APIの基本機能とは処理方法が異なる
        - **トークン使用量**: 画像認識により使用量が増加
        
        ## 🔧 エラー対処
        `Extra inputs are not permitted` エラーが出る場合：
        1. リージョンを ap-northeast-1 に変更
        2. AWSアカウントでCitations機能が有効か確認
        3. 機能のロールアウト完了まで待機
        
        現在の設定: リージョン {processor.bedrock_client.meta.region_name}, モデル {processor.model_id}
        """)
    
    return app


if __name__ == "__main__":
    # AWS認証方法の説明
    print("🔐 AWS認証方法:")
    print("1. IAMロール (推奨) - EC2/ECS/Lambda等")
    print("2. 環境変数 - AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")  
    print("3. AWS CLI設定 - ~/.aws/credentials")
    print("4. IAM Identity Center (SSO)")
    print("")
    
    # 認証情報の確認
    try:
        session = boto3.Session()
        sts_client = session.client('sts', region_name="ap-northeast-1")  # 記事と同じリージョン
        identity = sts_client.get_caller_identity()
        
        print(f"✅ 現在の認証情報:")
        print(f"   User/Role ARN: {identity['Arn']}")
        print(f"   Account ID: {identity['Account']}")
        print(f"   リージョン: ap-northeast-1 (記事準拠)")
        print("")
        
    except Exception as e:
        print(f"❌ AWS認証エラー: {str(e)}")
        print("")
        print("🔧 認証設定のヒント:")
        print("• EC2の場合: インスタンスにIAMロールをアタッチ")
        print("• ローカルの場合: aws configure または環境変数を設定")
        print("• SSO使用の場合: aws sso login")
        print("")
    
    # 利用可能なポートを検索
    available_port = find_available_port()
    
    if not available_port:
        print("エラー: 利用可能なポートが見つかりません (7860-7870)")
        print("既存のGradioアプリを停止するか、別のポート範囲を指定してください")
        exit(1)
    
    print(f"🚀 ポート {available_port} でアプリを起動します...")
    print("📖 記事準拠のCitations実装を使用")
    
    # アプリ起動
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=available_port,
        share=False
    )
