from yt_dlp import YoutubeDL
import logging
import time
import re
import os
import requests
import glob
from threading import Lock, Timer
import unicodedata
import subprocess

logger = logging.getLogger(__name__)

# 全局變量用於追踪下載狀態
download_lock = Lock()
current_download = None
merge_process = None

def extract_video_id(url):
    """從各種可能的YouTube URL格式中提取視頻ID"""
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([^&?/]+)',  # 標準和短網址格式
        r'(?:embed/|v%3D|vi%2F)([^%&?/]+)',  # 嵌入式格式
        r'(?:watch\?|youtube\.com/user/[^/]+/)([^&?/]+)'  # 用戶上傳格式
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_cookies():
    """獲取 YouTube cookies"""
    return {
        'CONSENT': 'YES+',
        'VISITOR_INFO1_LIVE': 'random_string',
    }

def extract_audio(url, output_path='temp_audio'):
    """提取視頻的音頻"""
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    video_id = extract_video_id(url)
    if not video_id:
        raise Exception("無法從URL中提取視頻ID")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
        'outtmpl': f'{output_path}/%(id)s.%(ext)s',
        'quiet': False,
        'no_warnings': False,
        'extract_flat': False,
        'no_playlist': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        },
        'socket_timeout': 30,
        'retries': 10,
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.cache.remove()  # 清除緩存
            info = ydl.extract_info(url, download=False)
            
            # 選擇最佳音頻格式
            formats = info['formats']
            audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
            
            if not audio_formats:
                raise Exception("無法找到合適的音頻格式")
            
            # 按比特率排序
            best_audio = max(audio_formats, key=lambda x: x.get('abr', 0))
            
            # 設置具體的格式
            ydl_opts['format'] = best_audio['format_id']
            
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            audio_path = f"{output_path}/{video_id}.wav"
            if os.path.exists(audio_path):
                return audio_path
            raise Exception("音頻文件未生成")
            
    except Exception as e:
        logger.error(f"音頻提取失敗: {str(e)}")
        raise Exception(f"音頻提取失敗: {str(e)}")

def clean_temp_files(directory='downloads'):
    """清理臨時文件"""
    patterns = ['*.f*.m4a', '*.f*.mp4', '*.part', '*.temp']
    for pattern in patterns:
        for file in glob.glob(os.path.join(directory, pattern)):
            try:
                os.remove(file)
                logger.info(f"已刪除臨時文件: {file}")
            except Exception as e:
                logger.error(f"刪除臨時文件失敗: {str(e)}")

def get_merge_progress(stderr):
    """從 FFmpeg 輸出解析合併進度"""
    try:
        line = stderr.readline().decode('utf-8', errors='ignore')
        if 'frame=' in line:
            # 從輸出中提取進度信息
            match = re.search(r'time=(\d+):(\d+):(\d+)', line)
            if match:
                hours, minutes, seconds = map(int, match.groups())
                total_seconds = hours * 3600 + minutes * 60 + seconds
                # 假設總時長為視頻時長
                progress = min(100, int((total_seconds / total_duration) * 100))
                if progress % 5 == 0:  # 每5%報告一次
                    logger.info(f"合併進度: {progress}%")
                return progress
    except Exception as e:
        logger.error(f"解析合併進度失敗: {str(e)}")
    return None

def sanitize_filename(filename):
    """清理文件名，移除不安全字符並限制長度"""
    # 移除不安全字符
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    # 將空格替換為下劃線
    filename = filename.replace(' ', '_')
    # 限制文件名長度（考慮 .mp4 副檔名）
    max_length = 200 - 4  # 預留 .mp4 的長度
    if len(filename) > max_length:
        filename = filename[:max_length]
    return filename

def find_downloaded_file(directory, title):
    """查找下載的文件，支持部分匹配"""
    try:
        for file in os.listdir(directory):
            if file.endswith('.mp4') and title.lower() in file.lower():
                return os.path.join(directory, file)
    except Exception as e:
        logger.error(f"查找文件時出錯: {str(e)}")
    return None

def download_video(url, output_path='downloads'):
    """下載視頻為 MP4 格式"""
    global current_download, total_duration
    
    if not download_lock.acquire(blocking=False):
        logger.warning("另一個下載正在進行中")
        return {
            'status': 'error',
            'message': '另一個下載正在進行中，請稍後再試'
        }
    
    try:
        # 清理之前的臨時文件
        clean_temp_files(output_path)
        current_download = url
        
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        full_output_path = os.path.join(base_path, output_path)
        
        if not os.path.exists(full_output_path):
            os.makedirs(full_output_path)
        
        def progress_hook(d):
            if d['status'] == 'downloading':
                progress = float(d.get('_percent_str', '0%').replace('%', ''))
                if progress % 5 == 0:  # 每5%報告一次
                    logger.info(f"下載進度: {progress}%")
            elif d['status'] == 'finished':
                logger.info("下載完成，開始合併...")
            elif d['status'] == 'merging formats':
                logger.info("正在合併文件...")
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(full_output_path, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'postprocessor_args': [
                '-c:v', 'h264',
                '-c:a', 'aac',
                '-movflags', '+faststart',
                '-progress', 'pipe:1'  # 輸出進度信息
            ],
            'noplaylist': True,
            'progress_hooks': [progress_hook],
            'force_overwrites': True,
            'ignoreerrors': True,
            'no_warnings': True,
            'quiet': False,
        }
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                # 獲取視頻信息
                logger.info("獲取視頻信息...")
                info = ydl.extract_info(url, download=False)
                expected_filename = f"{info['title']}.mp4"
                expected_path = os.path.join(full_output_path, expected_filename)
                total_duration = info.get('duration', 0)  # 獲取視頻總時長
                
                # 如果文件已存在，先刪除
                if os.path.exists(expected_path):
                    try:
                        os.remove(expected_path)
                        logger.info(f"已刪除已存在的文件: {expected_path}")
                    except Exception as e:
                        logger.error(f"刪除已存在文件失敗: {str(e)}")
                
                # 開始下載和合併
                logger.info("開始下載和合併...")
                ydl.download([url])
                
                # 等待文件系統同步
                time.sleep(2)
                
                # 檢查文件是否存在
                if os.path.exists(expected_path):
                    logger.info(f"視頻已成功下載到: {expected_path}")
                    return {
                        'status': 'success',
                        'filename': expected_filename,
                        'path': expected_path
                    }
                else:
                    raise Exception("無法找到下載的視頻文件")
                    
        except Exception as e:
            logger.error(f"下載或合併過程出錯: {str(e)}")
            raise
            
    except Exception as e:
        logger.error(f"視頻下載失敗: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }
    finally:
        # 清理臨時文件
        clean_temp_files(output_path)
        
        # 重置下載狀態
        current_download = None
        download_lock.release()

def get_video_info(url):
    logger.info(f"開始獲取視頻信息: {url}")
    
    # 首先提取視頻ID
    video_id = extract_video_id(url)
    if not video_id:
        raise Exception("無法從URL中提取視頻ID")
    
    # 構建乾淨的視頻URL
    clean_url = f"https://www.youtube.com/watch?v={video_id}"
    logger.info(f"處理乾淨的URL: {clean_url}")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best',  # 使用最佳品質
        'extract_flat': False,
        'no_playlist': True,
        'retries': 10,
        'socket_timeout': 30,
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=False)
            
            if not info:
                raise Exception("無法獲取視頻信息")
            
            result = {
                'title': info.get('title'),
                'video_id': video_id,  # 返回視頻ID而不是直接URL
                'thumbnail': info.get('thumbnail'),
                'description': info.get('description'),
                'duration': info.get('duration'),
            }
            
            logger.info(f"成功獲取視頻信息: {result['title']}")
            return result
            
    except Exception as e:
        logger.error(f"獲取視頻信息失敗: {str(e)}")
        raise Exception(f"獲取視頻信息失敗: {str(e)}")

def get_video_transcript(url):
    """獲取視頻字幕"""
    video_id = extract_video_id(url)
    if not video_id:
        return "無法從URL中提取視頻ID"
    
    clean_url = f"https://www.youtube.com/watch?v={video_id}"
    logger.info(f"開始獲取視頻字幕: {clean_url}")
    
    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'skip_download': True,
        'subtitleslangs': ['zh-Hant', 'zh-TW', 'zh-HK', 'en'],
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'force_generic_extractor': False,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        }
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            logger.info("正在提取字幕信息...")
            info = ydl.extract_info(clean_url, download=False)
            
            # 檢查手動字幕
            if 'subtitles' in info:
                logger.info(f"找到手動字幕: {info['subtitles'].keys()}")
                for lang in ['zh-TW', 'zh-Hant', 'zh-HK', 'en']:
                    if lang in info['subtitles']:
                        subs = info['subtitles'][lang]
                        if isinstance(subs, list) and len(subs) > 0:
                            for sub in subs:
                                if 'data' in sub:
                                    return sub['data']
                                elif 'url' in sub:
                                    # 如果是URL，需要下載字幕內容
                                    response = requests.get(sub['url'])
                                    if response.status_code == 200:
                                        return response.text
            
            # 檢查自動字幕
            if 'automatic_captions' in info:
                logger.info(f"找到自動字幕: {info['automatic_captions'].keys()}")
                for lang in ['zh-TW', 'zh-Hant', 'zh-HK', 'en']:
                    if lang in info['automatic_captions']:
                        captions = info['automatic_captions'][lang]
                        if isinstance(captions, list) and len(captions) > 0:
                            for cap in captions:
                                if 'data' in cap:
                                    return cap['data']
                                elif 'url' in cap:
                                    response = requests.get(cap['url'])
                                    if response.status_code == 200:
                                        return response.text
            
            return "無字幕內容"
            
    except Exception as e:
        logger.error(f"獲取字幕失敗: {str(e)}")
        return "無法獲取字幕"

def process_subtitles(subtitle_list):
    """處理字幕格式"""
    try:
        # 提取純文本並移除時間戳
        text_lines = []
        for item in subtitle_list:
            if isinstance(item, dict):
                text = None
                if 'text' in item:
                    text = item['text'].strip()
                elif 'data' in item:
                    text = item['data'].strip()
                
                if text:
                    # 移除 HTML 標籤
                    text = re.sub(r'<[^>]+>', '', text)
                    # 移除方括號內的內容（通常是音效描述）
                    text = re.sub(r'\[[^\]]*\]', '', text)
                    # 移除多餘的空白
                    text = ' '.join(text.split())
                    if text:
                        text_lines.append(text)
        
        if not text_lines:
            logger.warning("字幕列表為空")
            return "無字幕內容"
            
        # 合併文本並清理格式
        full_text = '\n'.join(text_lines)  # 使用換行符分隔，保持段落結構
        
        # 如果文本太短，可能不是有效的字幕
        if len(full_text.strip()) < 10:
            logger.warning("字幕內容過短")
            return "無字幕內容"
            
        return full_text
    except Exception as e:
        logger.error(f"處理字幕時出錯: {str(e)}")
        return "字幕處理失敗" 