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
        """格式化目錄行"""
        line_width = 80
        content = f"{title}：{description}"
        padding = line_width - len(content) - len(timestamp) - 2
        padding = max(1, padding)  # 確保至少有一個點
        dots = '.' * padding
        return f"{content}{dots}[{timestamp}]"
    
    def process_toc(self, raw_toc):
        """處理目錄格式，限制3-8個段落"""
        lines = []
        raw_lines = raw_toc.strip().split('\n')
        
        # 先收集所有有效的行
        for line in raw_lines:
            line = line.strip()
            if not line or ':' not in line or '[' not in line:
                continue
            
            try:
                # 分離標題、描述和時間戳
                main_part = line.split('[')[0].strip()
                timestamp = line.split('[')[1].rstrip(']').strip()
                
                if ':' in main_part:
                    title, description = main_part.split(':', 1)
                    title = title.strip()
                    description = description.strip()
                    
                    # 驗證時間格式
                    if re.match(r'^\d{2}:\d{2}$', timestamp):
                        minutes, seconds = map(int, timestamp.split(':'))
                        if minutes * 60 + seconds <= self.video_duration:
                            formatted_line = self.format_toc_line(title, description, timestamp)
                            lines.append(formatted_line)
            
            except Exception as e:
                logger.error(f"處理目錄行時出錯: {str(e)}")
                continue
        
        # 檢查段落數量
        if len(lines) < 3:
            logger.warning(f"目錄段落數不足: {len(lines)} < 3")
            return "目錄生成失敗：段落數不足，請重試"
        elif len(lines) > 8:
            logger.warning(f"目錄段落數過多，將截取前8段")
            lines = lines[:8]
        
        return '\n'.join(lines)
    
    def generate_toc(self, transcript):
        """生成目錄"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-16k",
                messages=[
                    {"role": "system", "content": f"""你是一個專業的視頻分析助手。請仔細理解整個視頻內容後，提取3-8個最重要的時間點作為目錄。

視頻總長度為 {self.video_duration} 秒，請確保時間點不超過視頻長度。

要求：
1. 必須先完整理解視頻內容
2. 選擇真正的內容轉折點作為段落分隔
3. 確保每個時間點都代表重要的主題轉換
4. 避免過於頻繁的分段
5. 時間點應該均勻分布在整個視頻中
6. 段落描述要簡潔但信息量充足
7. 忽略所有廣告和贊助內容

格式示例：
開場介紹：本集內容概述 [02:15]
核心概念：主要論點闡述 [05:30]
案例分析：具體實例說明 [12:45]
結論總結：重點內容回顧 [18:20]

注意：
- 時間格式必須是 [MM:SS]
- 總共不超過8個時間點
- 至少需要3個時間點
- 每個條目必須換行
- 時間點不能超過視頻總長度
                    """},
                    {"role": "user", "content": transcript}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            raw_toc = response.choices[0].message.content
            formatted_toc = self.process_toc(raw_toc)
            return formatted_toc
            
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