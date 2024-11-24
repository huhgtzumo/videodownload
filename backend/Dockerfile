FROM python:3.9-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 創建必要的目錄
RUN mkdir -p /app/temp_audio /app/downloads

# 複製後端代碼
COPY . .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

ENV FLASK_APP=app
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0

CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"] 