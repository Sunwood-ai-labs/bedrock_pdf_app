"""
PDFをマークダウンに変換するタブ
AWS Bedrock Claude Sonnet 4を使用してPDFを読みやすいマークダウン形式に変換
"""

import gradio as gr
import boto3
import os
import logging
from botocore.exceptions import ClientError
from utils.file_loader import load_prompt, load_ui_text

logger = logging.getLogger(__name__)


class PDFToMarkdownProcessor:
    """PDFをマークダウン形式に変換するクラス"""
    
    def __init__(self, region="ap-northeast-1"):
        try:
            self.bedrock_client = boto3.client("bedrock-runtime", region_name=region)
            logger.info("PDF→マークダウン変換機能用AWS認証成功")
        except Exception as e:
            logger.error(f"PDF→マークダウン変換機能AWS認証エラー: {str(e)}")
            raise
            
        self.model_id = "apac.anthropic.claude-sonnet-4-20250514-v1:0"
    
    def convert_pdf_to_markdown(self, pdf_file):
        """PDFファイルをマークダウン形式に変換"""
        if not pdf_file:
            return "PDFファイルを選択してください。"
        
        try:
            # ファイル形式を取得
            input_document_format = pdf_file.split(".")[-1]
            
            # ドキュメントを読み込み
            with open(pdf_file, 'rb') as f:
                input_document = f.read()
            
            # ファイル名をサニタイズ
            base_name = os.path.splitext(os.path.basename(pdf_file))[0]
            sanitized_name = ''.join(c for c in base_name if c.isalnum()) or "PDF"
            
            # マークダウン変換用のプロンプトを外部ファイルから読み込み
            conversion_prompt = load_prompt("pdf_to_markdown_prompt")
            
            # メッセージを構築
            message = {
                "role": "user",
                "content": [
                    {"text": conversion_prompt},
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
            
            return result_text
            
        except ClientError as e:
            error_msg = str(e)
            if "Extra inputs are not permitted" in error_msg and "citations" in error_msg:
                return f"❌ Citations機能エラー: {error_msg}\n\n対処法: リージョンを ap-northeast-1 に変更し、AWSサポートに機能の利用可能性を確認してください。"
            return f"AWS APIエラー: {error_msg}"
        except Exception as e:
            return f"エラー: {str(e)}"


def create_pdf_to_markdown_tab():
    """PDF→マークダウン変換タブを作成"""
    processor = PDFToMarkdownProcessor()
    
    def handle_conversion(pdf_file):
        return processor.convert_pdf_to_markdown(pdf_file)
    
    def show_file_info(pdf_file):
        if not pdf_file:
            return "ファイルが選択されていません"
        
        original = os.path.basename(pdf_file)
        base_name = os.path.splitext(original)[0]
        sanitized = ''.join(c for c in base_name if c.isalnum()) or "PDF"
        
        file_size = os.path.getsize(pdf_file) / (1024 * 1024)  # MB
        
        info = f"📄 ファイル名: {original}\n"
        info += f"📏 ファイルサイズ: {file_size:.2f} MB\n"
        
        if base_name != sanitized:
            info += f"⚠️ 使用される名前: {sanitized}.pdf"
        else:
            info += "✅ ファイル名は適切です"
            
        return info
    
    with gr.Column():
        gr.Markdown("## 📄➡️📝 PDF → マークダウン変換")
        gr.Markdown("PDFドキュメントを読みやすいマークダウン形式に変換します")
        
        with gr.Row():
            with gr.Column():
                pdf_input = gr.File(
                    label="📄 PDFファイル",
                    file_types=[".pdf"],
                    type="filepath"
                )
                file_info = gr.Textbox(
                    label="📋 ファイル情報",
                    lines=3,
                    interactive=False
                )
                convert_btn = gr.Button("🔄 マークダウン変換開始", variant="primary")
            
            with gr.Column():
                output = gr.Textbox(
                    label="📝 マークダウン出力",
                    lines=20,
                    show_copy_button=True,
                    placeholder="変換されたマークダウンがここに表示されます..."
                )
        
        # イベント設定
        pdf_input.change(show_file_info, pdf_input, file_info)
        convert_btn.click(handle_conversion, pdf_input, output)
        
        # 使用方法
        with gr.Accordion("📖 PDF→マークダウン変換について", open=False):
            help_text = load_ui_text("pdf_to_markdown_help")
            gr.Markdown(help_text)