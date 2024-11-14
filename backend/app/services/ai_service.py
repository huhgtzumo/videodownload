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

            # 限制輸入長度，取前 12000 個字符
            max_length = 12000
            if len(transcript) > max_length:
                transcript = transcript[:max_length] + "..."

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-16k",  # 使用 16k 版本
                messages=[
                    {"role": "system", "content": """你是一個專業的影片摘要助手。請按照以下格式總結視頻內容：
                    1. 主要主題：（一句話描述視頻主題）
                    2. 關鍵重點：（使用項目符號列出3-5個要點）
                    3. 結論或總結：（總結視頻的主要觀點或結論）
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