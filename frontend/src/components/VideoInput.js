import React, { useState } from 'react';
import { TextField, Button, Box } from '@mui/material';

const VideoInput = ({ onSubmit }) => {
  const [url, setUrl] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(url);
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
      <TextField
        fullWidth
        label="YouTube URL"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        margin="normal"
      />
      <Button
        type="submit"
        variant="contained"
        color="primary"
        sx={{ mt: 2 }}
      >
        分析視頻
      </Button>
    </Box>
  );
};

export default VideoInput; 