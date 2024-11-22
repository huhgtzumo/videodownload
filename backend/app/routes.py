from flask import jsonify, request, send_file
from app import app
from .services.youtube_service import get_video_info, get_video_transcript, download_video
from .services.ai_service import AIService
import logging
import os

# 設置日誌
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ai_service = AIService()

# 全局變量來追踪進度
processing_status = {}

@app.route('/api/video/info', methods=['POST', 'OPTIONS'])
def video_info():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        logger.info("收到視頻信息請求")
        data = request.get_json()
        url = data.get('url')
        logger.info(f"處理URL: {url}")
        
        if not url:
            return jsonify({'error': '請提供視頻URL'}), 400
            
        video_info = get_video_info(url)
        logger.info(f"獲取到視頻信息: {video_info}")
        return jsonify(video_info)
    except Exception as e:
        logger.error(f"處理視頻信息時出錯: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/transcript', methods=['POST', 'OPTIONS'])
def get_transcript():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        logger.info("收到字幕請求")
        data = request.get_json()
        url = data.get('url')
        logger.info(f"獲取字幕URL: {url}")
        
        if not url:
            return jsonify({'error': '請提供視頻URL'}), 400
            
        # 首先嘗試獲取字幕
        transcript = get_video_transcript(url)
        
        # 如果無法獲取字幕，返回錯誤信息
        if transcript in ["無法獲取字幕", "無字幕內容"]:
            return jsonify({
                'error': '無法獲取視頻字幕，請稍後再試',
                'status': 'error'
            }), 404
        
        logger.info("成功獲取文字內容")
        return jsonify({'transcript': transcript})
    except Exception as e:
        logger.error(f"獲取文字內容時出錯: {str(e)}", exc_info=True)
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/summary', methods=['POST'])
def generate_summary():
    try:
        data = request.get_json()
        transcript = data.get('transcript')
        video_duration = data.get('duration', 0)  # 從請求中獲取視頻時長
        
        if not transcript:
            return jsonify({'error': '請提供字幕內容'}), 400
            
        ai_service = AIService()
        ai_service.set_video_duration(video_duration)  # 設置視頻時長
        summary = ai_service.summarize_transcript(transcript)
        
        return jsonify({'summary': summary})
    except Exception as e:
        logger.error(f"生成摘要失敗: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/video/download', methods=['POST'])
def download_video_endpoint():
    try:
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({'error': '請提供視頻URL'}), 400
        
        logger.info(f"開始下載視頻: {url}")
        video_info = download_video(url)
        
        if video_info.get('status') == 'error':
            logger.error(f"下載失敗: {video_info.get('message')}")
            return jsonify({'error': video_info.get('message')}), 500
            
        try:
            file_path = video_info['path']
            logger.info(f"準備發送文件: {file_path}")
            
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                return jsonify({'error': '視頻文件不存在'}), 404
                
            file_size = os.path.getsize(file_path)
            logger.info(f"文件大小: {file_size} bytes")
            
            return send_file(
                file_path,
                as_attachment=True,
                download_name=video_info['filename'],
                mimetype='video/quicktime'
            )
            
        except Exception as e:
            logger.error(f"發送文件失敗: {str(e)}", exc_info=True)
            return jsonify({'error': f'文件發送失敗: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"下載處理失敗: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/process/status', methods=['GET'])
def get_process_status():
    video_id = request.args.get('video_id')
    if video_id in processing_status:
        return jsonify(processing_status[video_id])
    return jsonify({'status': 'unknown'})