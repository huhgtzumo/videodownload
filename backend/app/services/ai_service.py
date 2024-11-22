import os
from openai import OpenAI
import logging
import re

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("未設置 OPENAI_API_KEY 環境變量")
        self.client = OpenAI(api_key=api_key)

    def generate_toc(self, transcript):
        """生成目錄"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-16k",
                messages=[
                    {"role": "system", "content": """你是一個專業的視頻分析助手。請仔細閱讀視頻內容，並按照以下要求生成目錄：

要求：
1. 從視頻內容中選擇3-8個關鍵時間點
2. 每個時間點必須代表內容的重要轉折
3. 忽略所有廣告、業配等無關內容
4. 時間點應均勻分布在視頻中

格式：
- 段落主題：簡要說明本段內容 ........[MM:SS]
- 段落主題：簡要說明本段內容 ........[MM:SS]
- 段落主題：簡要說明本段內容 ........[MM:SS]

注意：
- 每個條目必須以 "- " 開頭
- 時間格式必須是 [分鐘:秒鐘]
- 使用點號(.)來對齊右側時間戳
- 確保所有時間戳都在同一垂直線上
- 總共不超過8個時間點
- 每個條目必須換行
                """},
                    {"role": "user", "content": transcript}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"生成目錄時發生錯誤: {str(e)}")
            raise Exception(f"生成目錄失敗: {str(e)}")

    def generate_notes(self, transcript):
        """生成學習筆記"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-16k",
                messages=[
                    {"role": "system", "content": """你是一個專業的筆記整理助手。請按照以下格式生成學習筆記：

## 📝 學習筆記

### 🎯 核心主旨
用一段話準確概括本視頻的核心價值

### 💡 重要概念
分點列出本視頻介紹的關鍵概念：
• **概念一**：清晰的解釋
• **概念二**：具體的說明
（列出3-5個重要概念）

### 📌 內容重點
按照邏輯順序詳細說明：

#### 1️⃣ [主題一]
- 核心論述
- 實例說明
- 應用建議

#### 2️⃣ [主題二]
...

### 🔍 總結
簡明扼要地總結本視頻的實用價值和應用場景

注意事項：
1. 忽略所有廣告和業配內容
2. 重要概念使用粗體標記
3. 保持內容的實用性和可操作性
4. 使用清晰的層級結構
                """},
                    {"role": "user", "content": transcript}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"生成筆記時發生錯誤: {str(e)}")
            raise Exception(f"生成筆記失敗: {str(e)}")

    def summarize_transcript(self, transcript):
        """整合目錄和筆記"""
        try:
            logger.info("開始生成目錄和筆記")
            if not transcript or transcript == "無字幕內容":
                return "無法生成摘要：未找到字幕內容"

            # 限制輸入長度
            max_length = 12000
            if len(transcript) > max_length:
                transcript = transcript[:max_length] + "..."

            # 分別生成目錄和筆記
            toc = self.generate_toc(transcript)
            notes = self.generate_notes(transcript)

            # 組合結果
            result = f"""## 📋 目錄

{toc}

{notes}"""

            logger.info("目錄和筆記生成完成")
            return result
        except Exception as e:
            logger.error(f"生成摘要時發生錯誤: {str(e)}")
            raise Exception(f"生成摘要失敗: {str(e)}")