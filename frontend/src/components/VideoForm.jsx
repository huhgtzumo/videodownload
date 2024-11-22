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
  const [isNotesCompleted, setIsNotesCompleted] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [downloadStage, setDownloadStage] = useState('');
  const [downloadCompleted, setDownloadCompleted] = useState(false);
  const [mergeProgress, setMergeProgress] = useState(0);
  const downloadRef = useRef({ progress: 0, stage: '' });
  const mergeInterval = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSummary('');
    setVideoInfo(null);
    setIsGeneratingNotes(true);
    setIsNotesCompleted(false);
    
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
      
      // 設置最終進度為100%並保持顯示
      setProcessStatus('AI筆記生成完成：100%');
      setIsNotesCompleted(true);
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
        setDownloadCompleted(false);
        downloadRef.current = { progress: 0, stage: '' };
        
        // 清理之前的計時器
        if (mergeInterval.current) {
            clearInterval(mergeInterval.current);
            mergeInterval.current = null;
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
                        
                        // 更新下載進度
                        if (percent <= 20) {
                            stage = '音頻文件下載中';
                            progress = percent * 0.5;  // 10%
                        } else if (percent <= 90) {
                            stage = '影片文件下載中';
                            progress = 10 + ((percent - 20) * 0.8);  // 40%
                        } else {
                            stage = '影片文件處理中';
                            progress = 50;
                            
                            // 開始合併進度模擬
                            if (!mergeInterval.current) {
                                mergeInterval.current = setInterval(() => {
                                    downloadRef.current.progress += 1;
                                    if (downloadRef.current.progress < 99) {
                                        setDownloadProgress(downloadRef.current.progress);
                                        setDownloadStage(`影片文件處理中：${downloadRef.current.progress}%`);
                                    } else {
                                        clearInterval(mergeInterval.current);
                                    }
                                }, 1000);
                            }
                        }
                        
                        // 更新進度顯示
                        if (progress <= 50) {
                            downloadRef.current.progress = progress;
                            downloadRef.current.stage = stage;
                            setDownloadProgress(progress);
                            setDownloadStage(`${stage}：${Math.round(progress)}%`);
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
        
        // 設置完成狀態
        setDownloadStage('下載完成：100%');
        setDownloadProgress(100);
        setDownloadCompleted(true);
        
    } catch (error) {
        console.error('下載失敗:', error);
        setError('下載失敗，請稍後再試');
        setDownloadStage('下載失敗');
        setDownloadProgress(0);
        setDownloadCompleted(false);
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

      {(isGeneratingNotes || isNotesCompleted) && (
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
            
            {(isDownloading || downloadCompleted) && (
                <div className="download-progress">
                    <div className="status-message">
                        {downloadStage}
                    </div>
                    <div className="progress-bar">
                        <div 
                            className={`progress-bar-fill ${downloadCompleted ? 'completed' : 'downloading'}`}
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
