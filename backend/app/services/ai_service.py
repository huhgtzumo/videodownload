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
        self.video_duration = 0
    
    def set_video_duration(self, duration):
        """設置視頻時長（秒）"""
        self.video_duration = duration
    
    def parse_timestamp(self, text):
        """從字幕文本中提取時間戳"""
        timestamps = []
        pattern = r'\[(\d{2}):(\d{2})\]'
        matches = re.finditer(pattern, text)
        for match in matches:
            minutes, seconds = map(int, match.groups())
            total_seconds = minutes * 60 + seconds
            if total_seconds <= self.video_duration:
                timestamps.append((total_seconds, match.group()))
        return sorted(timestamps)
    
    def format_toc_line(self, title, description, timestamp):
        """格式化目錄行，確保時間戳右對齊"""
        line_width = 80
        content = f"{title}：{description}"
        padding = line_width - len(content) - len(timestamp)
        padding = max(1, padding)  # 確保至少有一個空格
        return f"{content}{' ' * padding}{timestamp}"
    
    def process_toc(self, raw_toc):
        """處理目錄格式"""
        lines = []
        raw_lines = raw_toc.strip().split('\n')
        
        for line in raw_lines:
            line = line.strip()
            if not line or ':' not in line or '[' not in line:
                continue
            
            try:
                # 分離標題、描述和時間戳
                content, timestamp = line.rsplit('[', 1)
                timestamp = f"[{timestamp.rstrip(']')}]"
                
                if ':' in content:
                    title, description = content.split(':', 1)
                    title = title.strip()
                    description = description.strip()
                    
                    # 驗證時間格式
                    if re.match(r'^\[\d{2}:\d{2}\]$', timestamp):
                        formatted_line = self.format_toc_line(title, description, timestamp)
                        lines.append(formatted_line)
            
            except Exception as e:
                logger.error(f"處理目錄行時出錯: {str(e)}")
                continue
        
        return '\n'.join(lines) if lines else "無法生成目錄，請重試"
    
    def generate_toc(self, transcript):
        """生成目錄"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-16k",
                messages=[
                    {"role": "system", "content": f"""你是一個專業的視頻分析助手。請按照以下格式生成視頻目錄：

格式示例：
1、[02:15] 開場介紹：視頻主要內容概述

2、[05:30] 核心論述：詳細分析和討論

3、[12:45] 案例說明：具體實例和應用

4、[18:20] 總結歸納：重點內容回顧

要求：
1. 每個條目必須包含序號、時間戳和主題說明
2. 條目之間必須有空行
3. 時間點必須按順序排列
4. 時間點不能超過視頻總長度 {self.video_duration} 秒
5. 忽略廣告和贊助內容
6. 生成3-8個時間點
7. 主題說明要準確概括該時間點的內容
8. 使用實際的視頻內容時間點
                """},
                    {"role": "user", "content": transcript}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            # 直接返回 AI 生成的內容
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
1. 忽略所有廣告業配內容
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