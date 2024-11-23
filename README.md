# YouTube 影片下載與 AI 摘要工具

一個基於 Flask 和 React 的 YouTube 影片下載和 AI 摘要生成工具。

## 功能特點

- 支持 YouTube 影片下載（MP4 格式）
- 自動獲取影片字幕
- 使用 GPT-3.5 生成影片內容摘要（包含 emoji 和格式化顯示）
- 實時顯示下載進度
- 支持影片播放預覽
- 響應式設計，支持各種設備瀏覽器

## 技術棧

### 後端
- Flask (Python Web 框架)
- yt-dlp (YouTube 下載工具)
- OpenAI API (GPT-3.5)
- FFmpeg (影片處理)

### 前端
- React
- Axios (HTTP 請求)
- react-markdown (格式化顯示)
- CSS3 (響應式設計)

## 環境要求

- Docker Desktop
- Docker Compose
- OpenAI API Key

## 快速開始

1. 克隆倉庫：