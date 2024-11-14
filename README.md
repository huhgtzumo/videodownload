# YouTube Video Downloader & Summarizer

一個基於 Flask 和 React 的 YouTube 視頻下載和 AI 摘要生成工具。

## 功能特點

- 支持 YouTube 視頻下載（MP4 格式，QuickTime 兼容）
- 自動獲取視頻字幕
- 使用 GPT-3.5 生成視頻內容摘要（包含 emoji 和格式化顯示）
- 實時顯示下載和合併進度
- 支持視頻播放預覽

## 技術棧

### 後端
- Flask
- yt-dlp (YouTube 下載工具)
- OpenAI API (GPT-3.5)
- FFmpeg (視頻處理)

### 前端
- React
- Axios
- react-markdown (格式化顯示)

## 環境要求

- Docker Desktop
- Docker Compose
- OpenAI API Key

## 快速開始

1. 克隆倉庫：