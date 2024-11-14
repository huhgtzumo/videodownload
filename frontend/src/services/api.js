import axios from 'axios';

const API_URL = 'http://localhost:5001/api';

export const getVideoInfo = async (url) => {
  const response = await axios.post(`${API_URL}/video/info`, { url });
  return response.data;
};

export const downloadAudio = async (url) => {
  const response = await axios.post(`${API_URL}/download/audio`, { url });
  return response.data;
};

export const downloadVideo = async (url) => {
  const response = await axios.post(`${API_URL}/download/video`, { url });
  return response.data;
};

export const getTranscript = async (url) => {
  const response = await axios.post(`${API_URL}/transcript`, { url });
  return response.data;
};

export const getSummary = async (transcript) => {
  const response = await axios.post(`${API_URL}/summary`, { transcript });
  return response.data;
}; 