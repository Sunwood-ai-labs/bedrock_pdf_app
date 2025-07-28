import gradio as gr

def create_custom_theme():
    """
    カスタムテーマの作成
    カラーパレット: #2C3540, #5D6973, #F2CA80, #ffffff, #732922
    """
    return gr.Theme(
        primary_hue="orange",
        secondary_hue="gray", 
        neutral_hue="slate",
        text_size="md",
        spacing_size="lg",
        radius_size="sm",
        font=["Hiragino Sans", "Noto Sans JP", "Yu Gothic", "system-ui", "sans-serif"],
        font_mono=["SF Mono", "Monaco", "monospace"]
    ).set(
        # 背景色
        body_background_fill="#ffffff",                  # ベージュ系の背景
        body_text_color="#2C3540",                       # ダークグレーのテキスト
        
        # プライマリボタン
        button_primary_background_fill="#732922",        # ダークレッド
        button_primary_background_fill_hover="#5D6973",  # グレーホバー
        button_primary_text_color="#ffffff",             # ベージュテキスト
        
        # セカンダリボタン
        button_secondary_background_fill="#5D6973",      # グレー
        button_secondary_background_fill_hover="#2C3540", # ダークグレーホバー
        button_secondary_text_color="#ffffff",           # ベージュテキスト
        
        # 入力フィールド
        input_background_fill="#ffffff",                 # ベージュ背景
        input_border_color="#5D6973",                    # グレーボーダー
        input_border_color_focus="#F2CA80",              # ゴールドフォーカス
        
        # ブロック・パネル
        block_background_fill="#ffffff",                 # ベージュ背景
        block_border_color="#5D6973",                    # グレーボーダー
        panel_background_fill="#ffffff",                 # ベージュ背景
        panel_border_color="#5D6973",                    # グレーボーダー
        
        # その他のコンポーネント
        slider_color="#F2CA80",                          # ゴールドスライダー
        
        # タブ
        block_title_text_color="#2C3540",                # タブタイトル
        block_label_text_color="#2C3540",                # ラベルテキスト
    )