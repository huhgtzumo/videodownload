from flask import Flask, jsonify
from flask_cors import CORS
import logging

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)

# 配置 CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://ai.zimogogo.com/"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# 錯誤處理
@app.errorhandler(Exception)
def handle_error(error):
    app.logger.error(f"Error occurred: {str(error)}")
    return jsonify({
        'error': str(error),
        'status': 'error'
    }), 500

# 註冊路由
from app import routes

def create_app():
    return app