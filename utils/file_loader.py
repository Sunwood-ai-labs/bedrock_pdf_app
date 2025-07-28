"""
ファイル読み込みユーティリティ
プロンプトやUIテキストを外部ファイルから読み込む
"""

import os
import logging

logger = logging.getLogger(__name__)


def load_text_file(file_path):
    """テキストファイルを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"ファイルが見つかりません: {file_path}")
        return f"ファイルが見つかりません: {file_path}"
    except Exception as e:
        logger.error(f"ファイル読み込みエラー: {file_path} - {str(e)}")
        return f"ファイル読み込みエラー: {str(e)}"


def load_prompt(prompt_name):
    """プロンプトファイルを読み込む"""
    file_path = os.path.join("prompts", f"{prompt_name}.md")
    return load_text_file(file_path)


def load_ui_text(text_name):
    """UIテキストファイルを読み込む"""
    file_path = os.path.join("ui_texts", f"{text_name}.md")
    return load_text_file(file_path)