import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters.text_formatter import TextFormatter
import openai
from config import OPENAI_API_KEY
import re

class YouTubeDownloader:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

    def extract_video_id(self, url):
        # 從 URL 中提取視頻 ID
        video_id = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
        return video_id.group(1) if video_id else None

    def download_audio(self, url, output_path='downloads'):
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': f'{output_path}/%(title)s.%(ext)s',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    def download_video(self, url, output_path='downloads'):
        ydl_opts = {
            'format': 'best',
            'outtmpl': f'{output_path}/%(title)s.%(ext)s',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    def get_transcript(self, url):
        video_id = self.extract_video_id(url)
        if not video_id:
            return "無法提取視頻 ID"
        
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['zh-TW', 'zh-CN', 'en'])
            formatter = TextFormatter()
            return formatter.format_transcript(transcript)
        except Exception as e:
            return f"無法獲取字幕: {str(e)}"

    def generate_summary(self, transcript):
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一個專業的內容摘要助手。請幫忙整理以下視頻內容的重點筆記，以條列式呈現。"},
                    {"role": "user", "content": transcript}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"生成摘要時發生錯誤: {str(e)}"

def main():
    downloader = YouTubeDownloader()
    
    url = input("請輸入 YouTube 視頻 URL: ")
    print("\n請選擇操作：")
    print("1. 下載 MP3")
    print("2. 下載 MP4")
    print("3. 獲取字幕")
    print("4. 生成內容摘要")
    print("5. 執行所有操作")
    
    choice = input("請輸入選項數字: ")
    
    if choice in ['1', '5']:
        print("\n正在下載 MP3...")
        downloader.download_audio(url)
    
    if choice in ['2', '5']:
        print("\n正在下載 MP4...")
        downloader.download_video(url)
    
    if choice in ['3', '4', '5']:
        print("\n正在獲取字幕...")
        transcript = downloader.get_transcript(url)
        print("\n字幕內容：")
        print(transcript)
    
    if choice in ['4', '5']:
        print("\n正在生成內容摘要...")
        summary = downloader.generate_summary(transcript)
        print("\n視頻要點：")
        print(summary)

if __name__ == "__main__":
    main() 