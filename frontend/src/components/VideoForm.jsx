import React, { useState } from 'react';
import axios from 'axios';
import './VideoForm.css';
import ReactMarkdown from 'react-markdown';

const VideoForm = () => {
  const [url, setUrl] = useState('');
  const [videoInfo, setVideoInfo] = useState(null);
  const [summary, setSummary] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [processStatus, setProcessStatus] = useState('');
  const [isGeneratingNotes, setIsGeneratingNotes] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSummary('');
    setVideoInfo(null);
    setIsGeneratingNotes(true);
    setProcessStatus('正在分析視頻內容...');
    
    try {
      // 獲取視頻信息
      const infoResponse = await axios.post('http://localhost:5001/api/video/info', { url });
      setVideoInfo(infoResponse.data);
      
      // 獲取字幕並生成摘要
      setProcessStatus('正在生成AI筆記...');
      const transcriptResponse = await axios.post('http://localhost:5001/api/transcript', { url });
      const summaryResponse = await axios.post('http://localhost:5001/api/summary', {
        transcript: transcriptResponse.data.transcript
      });
      
      setSummary(summaryResponse.data.summary);
      setProcessStatus('AI筆記生成完成');
    } catch (err) {
      console.error('錯誤詳情:', err);
      const errorMessage = err.response?.data?.error || '處理失敗，請檢查視頻連結是否正確';
      setError(errorMessage);
      setProcessStatus('');
    } finally {
      setLoading(false);
      setIsGeneratingNotes(false);
    }
  };

  const handleDownload = async () => {
    try {
      setIsDownloading(true);
      setProcessStatus('開始下載視頻...');
      
      const response = await axios.post(
        'http://localhost:5001/api/video/download', 
        { url },
        { 
          responseType: 'blob',
          onDownloadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              setProcessStatus(`下載進度: ${percentCompleted}%`);
            }
          }
        }
      );
      
      const blob = new Blob([response.data], { type: 'video/mp4' });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `${videoInfo?.title || 'video'}.mp4`;
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
      
      setProcessStatus('下載完成');
    } catch (error) {
      console.error('下載失敗:', error);
      setError('下載失敗，請稍後再試');
      setProcessStatus('');
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="container">
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="輸入YouTube視頻連結"
          className="url-input"
        />
        <button type="submit" disabled={loading}>
          {loading ? '處理中...' : '生成AI筆記'}
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      {processStatus && (
        <div className="process-status">
          <div className="status-message">
            {processStatus}
          </div>
          {(isGeneratingNotes || isDownloading) && (
            <div className="progress-bar">
              <div 
                className="progress-bar-fill" 
                style={{ 
                  width: processStatus.includes('%') 
                    ? processStatus.match(/\d+/)[0] + '%' 
                    : '0%' 
                }}
              />
            </div>
          )}
        </div>
      )}

      {videoInfo && (
        <div className="video-container">
          <div className="video-wrapper">
            <iframe
              width="100%"
              height="480"
              src={`https://www.youtube.com/embed/${videoInfo.video_id}`}
              title={videoInfo.title}
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            ></iframe>
          </div>
          
          <h2>{videoInfo.title}</h2>
          
          {summary && (
            <div className="summary">
              <div className="markdown-content">
                <ReactMarkdown>{summary}</ReactMarkdown>
              </div>
              <button 
                onClick={handleDownload} 
                disabled={isDownloading}
                className="download-button"
              >
                {isDownloading ? '下載中...' : '下載視頻'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default VideoForm;
