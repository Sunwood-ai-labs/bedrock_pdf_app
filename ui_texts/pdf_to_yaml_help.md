## 機能
- PDFドキュメントの構造化
- マークダウン形式のYAML出力
- 表・図・画像の説明も含む
- 日本語コンテンツ対応

## 出力形式
```yaml
document:
  title: "ドキュメントタイトル"
  type: "ドキュメント種類"
  language: "ja"
  pages: ページ数

metadata:
  author: "著者名"
  date: "作成日"
  keywords: ["キーワード"]

summary:
  overview: "概要"
  key_points: ["重要ポイント"]

sections:
  - title: "セクションタイトル"
    content: "マークダウン形式の内容"
```

## 使い方
1. **PDFファイルをアップロード**
2. **YAML変換開始ボタンをクリック**
3. **構造化されたYAMLを確認・コピー**

## 技術仕様
- **モデル**: Claude Sonnet 4
- **最大ファイルサイズ**: 4.5MB
- **対応言語**: 日本語・英語