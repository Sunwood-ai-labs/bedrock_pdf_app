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
    """AWS BedrockでPDF処理を行うクラス"""
    
    def __init__(self, region="ap-northeast-1"):
        try:
            self.bedrock_client = boto3.client("bedrock-runtime", region_name=region)
            sts_client = boto3.client('sts', region_name=region)
            identity = sts_client.get_caller_identity()
            logger.info(f"AWS認証成功: {identity['Arn']}")
        except Exception as e:
            logger.error(f"AWS認証エラー: {str(e)}")
            raise
            
        self.model_id = "apac.anthropic.claude-sonnet-4-20250514-v1:0"
    
    def process_pdf(self, pdf_file, question):
        """PDFファイルを処理して質問に回答"""
        if not pdf_file:
            return "PDFファイルを選択してください。"
        
        if not question.strip():
            return "質問を入力してください。"
        
        try:
            # ファイル形式を取得
            input_document_format = pdf_file.split(".")[-1]
            
            # ドキュメントを読み込み
            with open(pdf_file, 'rb') as f:
                input_document = f.read()
            
            # ファイル名をサニタイズ
            base_name = os.path.splitext(os.path.basename(pdf_file))[0]
            sanitized_name = ''.join(c for c in base_name if c.isalnum()) or "PDF"
            
            # メッセージを構築
            message = {
                "role": "user",
                "content": [
                    {"text": question},
                    {
                        "document": {
                            "name": sanitized_name,
                            "format": input_document_format,
                            "source": {"bytes": input_document},
                            "citations": {"enabled": True},  
                        }
                    },
                ],
            }
            
            # Converse APIを呼び出し
            response = self.bedrock_client.converse(
                modelId=self.model_id,
                messages=[message]
            )
            
            # レスポンスから結果を抽出
            output_message = response['output']['message']
            result_text = ""
            
            for content in output_message['content']:
                if 'text' in content:
                    result_text += content['text']
            
            # トークン使用量を追加
            if 'usage' in response:
                token_usage = response['usage']
                result_text += f"\n\n---\n📊 トークン使用量: 入力 {token_usage.get('inputTokens', 'N/A')}, 出力 {token_usage.get('outputTokens', 'N/A')}, 合計 {token_usage.get('totalTokens', 'N/A')}"
            
            result_text += f"\n🔗 Citations機能: 有効"
            return result_text
            
        except ClientError as e:
            error_msg = str(e)
            if "Extra inputs are not permitted" in error_msg and "citations" in error_msg:
                return f"❌ Citations機能エラー: {error_msg}\n\n対処法: リージョンを ap-northeast-1 に変更し、AWSサポートに機能の利用可能性を確認してください。"
            return f"AWS APIエラー: {error_msg}"
        except Exception as e:
            return f"エラー: {str(e)}"


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
    
    def handle_upload(pdf_file, question):
        return processor.process_pdf(pdf_file, question)
    
    def show_file_info(pdf_file):
        if not pdf_file:
            return "ファイルが選択されていません"
        
        original = os.path.basename(pdf_file)
        base_name = os.path.splitext(original)[0]
        sanitized = ''.join(c for c in base_name if c.isalnum()) or "PDF"
        
        if base_name == sanitized:
            return f"✅ ファイル名: {original}"
        else:
            return f"⚠️ 元の名前: {original}\n✅ 使用される名前: {sanitized}.pdf"
    
    # カスタムCSS - シンプルで実用的
    css = """
    
    /* ヘッダー */
    h1 {
        text-align: center !important;
    }

    """
    
    # Gradioアプリ作成
    with gr.Blocks(
        css=css,
        title="AWS Bedrock PDF Processor",
        theme=gr.themes.Soft()  # シンプルなベーステーマ
    ) as app:
        
        gr.Markdown("# 🤖 AWS Bedrock PDF Processor")
        gr.Markdown("Claude Sonnet 4でPDFを分析します")
        
        with gr.Row():
            with gr.Column():
                pdf_input = gr.File(
                    label="📄 PDFファイル",
                    file_types=[".pdf"],
                    type="filepath"
                )
                file_info = gr.Textbox(
                    label="📋 ファイル情報",
                    lines=2,
                    interactive=False
                )
                question_input = gr.Textbox(
                    label="❓ 質問",
                    placeholder="PDFについて質問してください...",
                    lines=3
                )
                submit_btn = gr.Button("🚀 分析開始", variant="primary")
            
            with gr.Column():
                output = gr.Textbox(
                    label="🤖 AI回答",
                    lines=15,
                    show_copy_button=True
                )
        
        # イベント設定
        pdf_input.change(show_file_info, pdf_input, file_info)
        submit_btn.click(handle_upload, [pdf_input, question_input], output)
        
        # 使用方法
        with gr.Accordion("📖 使用方法", open=False):
            gr.Markdown("""
            ## 使い方
            1. **PDFファイルをアップロード**
            2. **質問を入力**
            3. **分析開始ボタンをクリック**
            
            ## 技術仕様
            - **リージョン**: ap-northeast-1
            - **モデル**: Claude Sonnet 4
            - **機能**: Citations対応、PDF画像認識
            """)
    
    return app


if __name__ == "__main__":
    print("🚀 AWS Bedrock PDF Processor を起動中...")
    
    # AWS認証確認
    try:
        session = boto3.Session()
        sts = session.client('sts', region_name="ap-northeast-1")
        identity = sts.get_caller_identity()
        print(f"✅ AWS認証: {identity['Arn']}")
    except Exception as e:
        print(f"❌ AWS認証エラー: {e}")
        exit(1)
    
    # ポート検索・起動
    port = find_available_port()
    if not port:
        print("❌ 利用可能なポートがありません")
        exit(1)
    
    print(f"🌐 ポート {port} で起動中...")
    
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False
    )