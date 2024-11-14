from yt_dlp import YoutubeDL
import logging
import time
import re
import os
import requests

logger = logging.getLogger(__name__)

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

def download_video(url, output_path='downloads'):
    """下載視頻為 MP4 格式（QuickTime 兼容）"""
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    full_output_path = os.path.join(base_path, output_path)
    
    if not os.path.exists(full_output_path):
        os.makedirs(full_output_path)
    
    def progress_hook(d):
        if d['status'] == 'downloading':
            progress = float(d.get('_percent_str', '0%').replace('%', ''))
            if progress % 10 == 0:
                logger.info(f"下載進度: {progress}%")
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(full_output_path, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',  # 改用 mp4
        'postprocessor_args': [
            '-c:v', 'h264',     # 視頻編碼
            '-c:a', 'aac',      # 音頻編碼
            '-movflags', '+faststart'  # 優化播放
        ],
        'noplaylist': True,
        'progress_hooks': [progress_hook],
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = os.path.join(full_output_path, f"{info['title']}.mp4")
            
            if not os.path.exists(video_path):
                raise Exception("視頻下載失敗")
            
            logger.info(f"視頻已下載到: {video_path}")
            return {
                'status': 'success',
                'filename': f"{info['title']}.mp4",
                'path': video_path
            }
    except Exception as e:
        logger.error(f"視頻下載失敗: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }

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
                    # 移��方括號內的內容（通常是音效描述）
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