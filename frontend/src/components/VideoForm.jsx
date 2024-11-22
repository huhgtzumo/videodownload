import React, { useState, useRef } from 'react';
import axios from 'axios';
import './VideoForm.css';
import ReactMarkdown from 'react-markdown';

const VideoForm = () => {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [summary, setSummary] = useState('');
  const [videoInfo, setVideoInfo] = useState(null);
  const [processStatus, setProcessStatus] = useState('');
  const [isGeneratingNotes, setIsGeneratingNotes] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [downloadStage, setDownloadStage] = useState('');
  const [mergeProgress, setMergeProgress] = useState(0);
  const mergeInterval = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSummary('');
    setVideoInfo(null);
    setIsGeneratingNotes(true);
    
    // 設置進度更新定時器，每秒增加5%
    let progress = 0;
    const progressInterval = setInterval(() => {
      if (progress < 90) {
        progress += 5;
        setProcessStatus(`生成AI筆記中：${progress}%`);
      }
    }, 1000);
    
    try {
      // 獲取視頻信息
      const infoResponse = await axios.post('http://localhost:5001/api/video/info', { url });
      setVideoInfo(infoResponse.data);
      
      // 獲取字幕並生成摘要
      const transcriptResponse = await axios.post('http://localhost:5001/api/transcript', { url });
      const summaryResponse = await axios.post('http://localhost:5001/api/summary', {
        transcript: transcriptResponse.data.transcript,
        duration: infoResponse.data.duration
      });
      
      // 清除進度定時器
      clearInterval(progressInterval);
      
      // 設置最終進度為100%
      setProcessStatus('AI筆記生成完成：100%');
      setSummary(summaryResponse.data.summary);
      
    } catch (err) {
      clearInterval(progressInterval);
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
        setDownloadProgress(0);
        setDownloadStage('準備下載...');
        
        // 清理之前的合併進度計時器
        if (mergeInterval.current) {
            clearInterval(mergeInterval.current);
        }
        
        const response = await axios.post(
            'http://localhost:5001/api/video/download', 
            { url },
            { 
                responseType: 'blob',
                onDownloadProgress: (progressEvent) => {
                    if (progressEvent.total) {
                        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                        let stage = '';
                        let progress = 0;
                        
                        if (percent <= 10) {
                            // 音頻下載階段 (10%)
                            stage = '音頻文件下載中';
                            progress = percent;
                        } else if (percent <= 50) {
                            // 視頻下載階段 (40%)
                            stage = '影片文件下載中';
                            progress = 10 + ((percent - 10) * 40/40);
                        } else {
                            // 合併階段 (50%)
                            stage = '影片文件處理中';
                            if (!mergeInterval.current) {
                                progress = 50;
                                setDownloadProgress(50);
                                // 每秒增加1%，直到99%
                                mergeInterval.current = setInterval(() => {
                                    setDownloadProgress(prev => {
                                        if (prev < 99) return prev + 1;
                                        return 99;
                                    });
                                }, 1000);
                            }
                        }
                        
                        if (progress <= 50) {
                            setDownloadStage(`${stage}：${Math.round(progress)}%`);
                            setDownloadProgress(progress);
                        }
                    }
                }
            }
        );
        
        // 清理合併進度計時器
        if (mergeInterval.current) {
            clearInterval(mergeInterval.current);
            mergeInterval.current = null;
        }
        
        // 檢查響應類型
        const contentType = response.headers['content-type'];
        if (contentType && contentType.includes('application/json')) {
            // 處理錯誤響應
            const reader = new FileReader();
            reader.onload = () => {
                const error = JSON.parse(reader.result);
                setError(error.error || '下載失敗');
                setDownloadStage('下載失敗');
            };
            reader.readAsText(response.data);
            return;
        }
        
        // 處理下載
        const blob = new Blob([response.data], { type: 'video/mp4' });
        const downloadUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = `${videoInfo?.title || 'video'}.mp4`;
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(downloadUrl);
        
        setDownloadStage('下載完成：100%');
        setDownloadProgress(100);
        
    } catch (error) {
        console.error('下載失敗:', error);
        setError('下載失敗，請稍後再試');
        setDownloadStage('下載失敗');
        setDownloadProgress(0);
    } finally {
        setIsDownloading(false);
        if (mergeInterval.current) {
            clearInterval(mergeInterval.current);
            mergeInterval.current = null;
        }
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

      {isGeneratingNotes && (
        <div className="process-status">
          <div className="status-message">
            {processStatus}
          </div>
          <div className="progress-bar">
            <div 
              className="progress-bar-fill generating"
              style={{ 
                width: processStatus.includes('%') 
                  ? processStatus.match(/\d+/)[0] + '%' 
                  : '0%' 
              }}
            />
          </div>
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
          
          {/* 下載區域 */}
          <div className="download-section">
            <button 
              onClick={handleDownload} 
              disabled={isDownloading}
              className="download-button"
            >
              {isDownloading ? '下載中...' : '下載視頻'}
            </button>
            
            {isDownloading && (
              <div className="download-progress">
                <div className="status-message">
                  {downloadStage}
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress-bar-fill downloading"
                    style={{ width: `${downloadProgress}%` }}
                  />
                </div>
              </div>
            )}
          </div>
          
          {/* AI 筆記部分 */}
          {summary && (
            <div className="summary">
              <div className="markdown-content">
                <ReactMarkdown>{summary}</ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default VideoForm;
