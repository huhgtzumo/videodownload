import os
from pathlib import Path

# 獲取項目根目錄
ROOT_DIR = Path(__file__).parent.parent.parent

class Config:
    # 基本配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # 文件路徑配置
    TEMP_AUDIO_DIR = os.path.join(ROOT_DIR, 'backend', 'temp_audio')
    DOWNLOAD_DIR = os.path.join(ROOT_DIR, 'backend', 'downloads')
    
    # 確保必要的目錄存在
    @classmethod
    def init_app(cls, app):
        os.makedirs(cls.TEMP_AUDIO_DIR, exist_ok=True)
        os.makedirs(cls.DOWNLOAD_DIR, exist_ok=True)
        
        # 配置日誌
        if not app.debug:
            import logging
            file_handler = logging.FileHandler('app.log')
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
 