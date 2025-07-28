import gradio as gr
import boto3
import json
import os
import socket
import logging
import time
import pandas as pd
from botocore.exceptions import ClientError

# タブ機能をインポート
from tabs.pdf_to_yaml_tab import create_pdf_to_yaml_tab
from tabs.pdf_to_markdown_tab import create_pdf_to_markdown_tab
from utils.file_loader import load_ui_text

# カスタムテーマをインポート
from theme import create_custom_theme

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


def create_pdf_qa_tab():
    """PDF Q&Aタブを作成（元の機能）"""
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
    
    with gr.Column():
        gr.Markdown("## 📄❓ PDF Q&A")
        gr.Markdown("PDFファイルをアップロードしてAIに質問できます")
        
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
        with gr.Accordion("📖 PDF Q&A機能について", open=False):
            help_text = load_ui_text("pdf_qa_help")
            gr.Markdown(help_text)


def create_comprehensive_demo():
    """包括的なデモアプリケーションを作成"""
    theme = create_custom_theme()
    
    # サンプルデータ
    sample_data = pd.DataFrame({
        "ファイル名": ["document1.pdf", "report2.pdf", "manual3.pdf", "guide4.pdf"],
        "サイズ": ["2.5MB", "1.8MB", "4.2MB", "3.1MB"],
        "ページ数": [15, 25, 8, 12],
        "処理状況": ["完了", "処理中", "待機", "完了"]
    })
    
    # カスタムCSS
    css = """
    /* ヘッダー */
    h1 {
        text-align: center !important;
        color: #2C3540 !important;
    }
    
    /* タブのスタイリング */
    .tab-nav {
        margin-bottom: 20px;
    }
    
    /* カスタムボタンスタイル */
    .custom-button {
        background: linear-gradient(135deg, #F2CA80 0%, #732922 100%) !important;
        border: none !important;
        color: #F2E9D8 !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(115, 41, 34, 0.3) !important;
    }
    """
    
    # Gradioアプリ作成
    with gr.Blocks(
        css=css,
        title="AWS Bedrock PDF Processor",
        theme=theme
    ) as app:
        
        # ヘッダー
        gr.HTML(f"""
        <div style='text-align: center; margin-bottom: 2rem; padding: 2rem; 
                    background: linear-gradient(135deg, #F2CA80 0%, #732922 100%); 
                    color: #F2E9D8; border-radius: 12px; 
                    box-shadow: 0 8px 32px rgba(115, 41, 34, 0.3);'>
            <h1 style='font-size: 3rem; margin-bottom: 0.5rem; 
                       text-shadow: 2px 2px 4px rgba(44, 53, 64, 0.5); 
                       color: #F2E9D8;'>📄 AWS Bedrock PDF Processor</h1>
            <p style='font-size: 1.2rem; margin: 0; opacity: 0.9; 
                      color: #F2E9D8;'>〜 Claude Sonnet 4を使用したPDF処理アプリケーション 〜</p>
        </div>
        """)
        
        # タブ機能を追加
        with gr.Tabs():
            with gr.Tab("📄❓ PDF Q&A"):
                create_pdf_qa_tab()
            
            with gr.Tab("📄➡️📋 PDF→YAML変換"):
                create_pdf_to_yaml_tab()
            
            with gr.Tab("📄➡️📝 PDF→マークダウン変換"):
                create_pdf_to_markdown_tab()
            
            # 新しいデモタブを追加
            with gr.Tab("🎨 テーマデモ"):
                create_theme_demo_tab(sample_data)
        
        # 全体的な情報
        with gr.Accordion("ℹ️ アプリケーション情報", open=False):
            app_info = load_ui_text("app_info")
            gr.Markdown(app_info)
    
    return app


def create_theme_demo_tab(sample_data):
    """テーマデモタブを作成"""
    with gr.Column():
        gr.Markdown("## 🎨 カスタムテーマデモ")
        gr.Markdown("指定されたカラーパレット（#2C3540, #5D6973, #F2CA80, #F2E9D8, #732922）を使用したUIコンポーネント")
        
        # カラーパレット表示
        gr.HTML("""
        <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                    gap: 1rem; margin: 2rem 0;'>
            <div style='padding: 1.5rem; background: #2C3540; border-radius: 12px; text-align: center;'>
                <h4 style='color: #F2E9D8; margin-top: 0;'>🌑 ダークグレー</h4>
                <p style='font-size: 0.9rem; color: #F2E9D8; margin: 0;'>#2C3540</p>
            </div>
            <div style='padding: 1.5rem; background: #5D6973; border-radius: 12px; text-align: center;'>
                <h4 style='color: #F2E9D8; margin-top: 0;'>🌫️ グレー</h4>
                <p style='font-size: 0.9rem; color: #F2E9D8; margin: 0;'>#5D6973</p>
            </div>
            <div style='padding: 1.5rem; background: #F2CA80; border-radius: 12px; text-align: center;'>
                <h4 style='color: #2C3540; margin-top: 0;'>✨ ゴールド</h4>
                <p style='font-size: 0.9rem; color: #2C3540; margin: 0;'>#F2CA80</p>
            </div>
            <div style='padding: 1.5rem; background: #F2E9D8; border: 2px solid #5D6973; border-radius: 12px; text-align: center;'>
                <h4 style='color: #2C3540; margin-top: 0;'>🤍 ベージュ</h4>
                <p style='font-size: 0.9rem; color: #2C3540; margin: 0;'>#F2E9D8</p>
            </div>
            <div style='padding: 1.5rem; background: #732922; border-radius: 12px; text-align: center;'>
                <h4 style='color: #F2E9D8; margin-top: 0;'>🍷 ダークレッド</h4>
                <p style='font-size: 0.9rem; color: #F2E9D8; margin: 0;'>#732922</p>
            </div>
        </div>
        """)
        
        # 基本入力コンポーネント
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 📝 入力コンポーネント")
                name_input = gr.Textbox(
                    label="📄 ファイル名", 
                    placeholder="document.pdf",
                    info="処理するファイル名を入力"
                )
                file_size = gr.Number(
                    label="📊 ファイルサイズ (MB)",
                    minimum=0,
                    maximum=100,
                    value=2.5
                )
                processing_mode = gr.Radio(
                    choices=["🚀 高速処理", "🎯 精密処理", "⚖️ バランス"],
                    label="⚙️ 処理モード",
                    value="⚖️ バランス"
                )
                enable_citations = gr.Checkbox(
                    label="📚 Citations機能を有効にする",
                    value=True
                )
            
            with gr.Column():
                gr.Markdown("### 🎛️ 設定オプション")
                output_format = gr.CheckboxGroup(
                    choices=["📝 Markdown", "📋 YAML", "📄 JSON", "📊 CSV"],
                    label="出力形式（複数選択可）",
                    value=["📝 Markdown"]
                )
                region_select = gr.Dropdown(
                    choices=["ap-northeast-1 (東京)", "us-east-1 (バージニア)", "eu-west-1 (アイルランド)"],
                    label="🌍 AWSリージョン",
                    value="ap-northeast-1 (東京)"
                )
                quality_level = gr.Slider(
                    minimum=1,
                    maximum=10,
                    value=7,
                    step=1,
                    label="🎯 処理品質レベル"
                )
        
        # ボタン群
        with gr.Row():
            process_btn = gr.Button("🚀 処理開始", variant="primary", size="lg")
            clear_btn = gr.Button("🗑️ クリア", variant="secondary")
            stop_btn = gr.Button("⛔ 停止", variant="stop")
        
        # 結果表示
        with gr.Row():
            with gr.Column():
                result_output = gr.Textbox(
                    label="📤 処理結果",
                    lines=8,
                    show_copy_button=True
                )
            
            with gr.Column():
                # データ表示
                data_display = gr.DataFrame(
                    value=sample_data,
                    label="📊 処理履歴",
                    interactive=True
                )
        
        # 処理状況表示
        status_display = gr.Label(
            value={
                "処理完了": 0.75,
                "処理中": 0.15,
                "待機中": 0.08,
                "エラー": 0.02
            },
            label="📈 システム状況"
        )
        
        # 簡単な処理関数
        def process_demo(name, size, mode, citations, formats, region, quality):
            if not name:
                return "ファイル名を入力してください。"
            
            result = f"📄 ファイル: {name}\n"
            result += f"📊 サイズ: {size}MB\n"
            result += f"⚙️ モード: {mode}\n"
            result += f"📚 Citations: {'有効' if citations else '無効'}\n"
            result += f"📝 出力形式: {', '.join(formats) if formats else '未選択'}\n"
            result += f"🌍 リージョン: {region}\n"
            result += f"🎯 品質レベル: {quality}/10\n\n"
            result += "✅ 処理が完了しました！"
            
            return result
        
        def clear_inputs():
            return ["", 2.5, "⚖️ バランス", True, ["📝 Markdown"], "ap-northeast-1 (東京)", 7, ""]
        
        # イベント設定
        process_btn.click(
            fn=process_demo,
            inputs=[name_input, file_size, processing_mode, enable_citations, 
                   output_format, region_select, quality_level],
            outputs=result_output
        )
        
        clear_btn.click(
            fn=clear_inputs,
            outputs=[name_input, file_size, processing_mode, enable_citations,
                    output_format, region_select, quality_level, result_output]
        )
        
        # テーマ情報
        with gr.Accordion("🎨 テーマ情報", open=False):
            gr.Markdown("""
            ### カスタムテーマの特徴
            
            **カラーパレット:**
            - **#2C3540** - ダークグレー（テキスト、ボーダー）
            - **#5D6973** - グレー（セカンダリボタン、ボーダー）
            - **#F2CA80** - ゴールド（アクセント、スライダー）
            - **#F2E9D8** - ベージュ（背景、ボタンテキスト）
            - **#732922** - ダークレッド（プライマリボタン）
            
            **デザイン原則:**
            - 温かみのあるベージュ背景で読みやすさを重視
            - ゴールドのアクセントで高級感を演出
            - ダークレッドのプライマリボタンで重要なアクションを強調
            - グレー系の色でバランスの取れた階層構造
            """)


def create_app():
    """アプリケーションのエントリーポイント"""
    return create_comprehensive_demo()


if __name__ == "__main__":
    import argparse

    print("🚀 AWS Bedrock PDF Processor を起動中...")

    parser = argparse.ArgumentParser(description="AWS Bedrock PDF Processor")
    parser.add_argument("--port", type=int, default=None, help="起動するポート番号 (例: 7860)")
    args = parser.parse_args()

    # AWS認証確認
    try:
        session = boto3.Session()
        sts = session.client('sts', region_name="ap-northeast-1")
        identity = sts.get_caller_identity()
        print(f"✅ AWS認証: {identity['Arn']}")
    except Exception as e:
        print(f"❌ AWS認証エラー: {e}")
        exit(1)

    # ポート決定
    if args.port:
        port = args.port
        print(f"🌐 指定ポート {port} で起動します")
    else:
        port = find_available_port()
        if not port:
            print("❌ 利用可能なポートがありません")
            exit(1)
        print(f"🌐 自動選択ポート {port} で起動します")

    app = create_comprehensive_demo()
    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False
    )