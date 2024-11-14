import os
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("未設置 OPENAI_API_KEY 環境變量")
        self.client = OpenAI(api_key=api_key)

    def summarize_transcript(self, transcript):
        """生成視頻內容摘要"""
        try:
            logger.info("開始生成摘要")
            if not transcript or transcript == "無字幕內容":
                return "無法生成摘要：未找到字幕內容"

            # 限制輸入長度
            max_length = 12000
            if len(transcript) > max_length:
                transcript = transcript[:max_length] + "..."

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-16k",
                messages=[
                    {"role": "system", "content": """你是一個專業的影片摘要助手。請使用以下格式生成摘要，確保使用emoji和markdown格式：

## 🎯 主要主題
用一句話描述視頻的核心主題

## 📝 內容重點
1. **重點一**：[相關描述]
2. **重點二**：[相關描述]
3. **重點三**：[相關描述]
（根據內容可以有3-5個重點）

## 💡 關鍵見解
• [第一個見解]
• [第二個見解]
（列出2-3個重要見解）

## 🔍 結論
總結視頻的主要觀點和結論

請確保：
- 每個部分都使用適當的emoji
- 重要內容使用粗體標記
- 保持條理清晰的格式
                    """},
                    {"role": "user", "content": transcript}
                ],
                temperature=0.7,
                max_tokens=800
            )
            summary = response.choices[0].message.content
            logger.info("摘要生成完成")
            return summary
        except Exception as e:
            logger.error(f"生成摘要時發生錯誤: {str(e)}")
            raise Exception(f"生成摘要失敗: {str(e)}")