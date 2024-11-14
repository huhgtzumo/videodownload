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
  const [downloadStatus, setDownloadStatus] = useState('');
  const [mergeStatus, setMergeStatus] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSummary('');
    setVideoInfo(null);
    setProcessStatus('');
    
    try {
        setProcessStatus('獲取視頻信息...');
        const infoResponse = await axios.post('http://localhost:5001/api/video/info', { url });
        setVideoInfo(infoResponse.data);
        
        setProcessStatus('獲取字幕...');
        const transcriptResponse = await axios.post('http://localhost:5001/api/transcript', { url });
        
        if (transcriptResponse.data.transcript === "無字幕內容") {
            setProcessStatus('無法找到字幕，嘗試生成摘要...');
        } else {
            setProcessStatus('正在生成摘要...');
        }
        
        const summaryResponse = await axios.post('http://localhost:5001/api/summary', {
            transcript: transcriptResponse.data.transcript
        });
        
        setSummary(summaryResponse.data.summary);
        setProcessStatus('處理完成');
    } catch (err) {
        console.error('錯誤詳情:', err);
        const errorMessage = err.response?.data?.error || '處理失敗，請檢查視頻連結是否正確';
        setError(errorMessage);
        setProcessStatus('處理失敗');
    } finally {
        setLoading(false);
    }
  };

  const handleDownload = async () => {
    try {
        setLoading(true);
        setDownloadStatus('準備下載...');
        setMergeStatus('');
        
        const response = await axios.post(
            'http://localhost:5001/api/video/download', 
            { url },
            { 
                responseType: 'blob',
                onDownloadProgress: (progressEvent) => {
                    if (progressEvent.total) {
                        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                        if (percentCompleted <= 100) {
                            setDownloadStatus(`下載進度: ${percentCompleted}%`);
                        } else {
                            setMergeStatus(`合併進度: ${percentCompleted - 100}%`);
                        }
                    }
                }
            }
        );
        
        // 檢查響應類型
        const contentType = response.headers['content-type'];
        if (contentType && contentType.includes('application/json')) {
            const reader = new FileReader();
            reader.onload = () => {
                const error = JSON.parse(reader.result);
                setError(error.error || '下載失敗');
            };
            reader.readAsText(response.data);
            return;
        }
        
        // 創建下載
        const blob = new Blob([response.data], { type: 'video/quicktime' });
        const downloadUrl = window.URL.createObjectURL(blob);
        
        // 創建臨時下載鏈接
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = `${videoInfo?.title || 'video'}.mov`;
        document.body.appendChild(link);
        
        // 觸發下載
        link.click();
        
        // 清理
        document.body.removeChild(link);
        window.URL.revokeObjectURL(downloadUrl);
        setProcessStatus('下載完成');
        console.log('下載完成');
        
    } catch (error) {
        console.error('下載失敗:', error);
        setError('下載失敗，請稍後再試');
        setDownloadStatus('');
        setMergeStatus('');
    } finally {
        setLoading(false);
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
        <button type="submit" disabled={loading || !url}>
          {loading ? '處理中...' : '視頻摘要'}
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      {videoInfo && (
        <div className="video-container">
          <div className="video-wrapper">
            <iframe
              width="100%"
              height="480"
              src={`https://www.youtube.com/embed/${videoInfo.video_id}`}
              title={videoInfo.title}
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
              allowFullScreen
            ></iframe>
          </div>
          
          <div className="controls">
            <button 
              onClick={handleDownload} 
              disabled={loading}
              className="download-button"
            >
              {loading ? '下載中...' : '下載 MOV'}
            </button>
          </div>
          
          {processStatus && (
            <div className="process-status">
              處理進度: {processStatus}
            </div>
          )}
          
          <h2>{videoInfo.title}</h2>
          
          {summary && (
            <div className="summary">
                <h3>📊 視頻摘要</h3>
                <div className="markdown-content">
                    <ReactMarkdown>{summary}</ReactMarkdown>
                </div>
            </div>
          )}
          
          {downloadStatus && <div className="status-message">{downloadStatus}</div>}
          {mergeStatus && <div className="status-message">{mergeStatus}</div>}
        </div>
      )}
    </div>
  );
};

export default VideoForm;
