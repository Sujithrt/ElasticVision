import React, { useState } from 'react';
import axios from 'axios';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Paper,
  Box,
  Button,
  Alert,
  CircularProgress,
  Grid
} from '@mui/material';
import { styled } from '@mui/material/styles';

const Input = styled('input')({
  display: 'none',
});

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [result, setResult] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    setError('');
    const file = e.target.files[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        setError('Please select a valid image file.');
        setSelectedFile(null);
      } else {
        setSelectedFile(file);
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!selectedFile) {
      setError('No valid file selected.');
      return;
    }
    setLoading(true);
    const formData = new FormData();
    formData.append('inputFile', selectedFile);
    try {
      const response = await axios.post('http://3.228.226.5:8000/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResult(response.data);
    } catch (err) {
      setError('Error processing the image. Please try again.');
    }
    setLoading(false);
  };

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div">
            Elastic Vision
          </Typography>
        </Toolbar>
      </AppBar>
      <Container maxWidth="sm" sx={{ mt: 4 }}>
        <Paper elevation={4} sx={{ p: 4 }}>
          <Typography variant="h5" align="center" gutterBottom>
            Face Recognition
          </Typography>
          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <label htmlFor="upload-file">
                  <Input accept="image/*" id="upload-file" type="file" onChange={handleFileChange} />
                  <Button variant="contained" component="span" fullWidth>
                    {selectedFile ? 'Change Image' : 'Choose Image'}
                  </Button>
                </label>
              </Grid>
              {selectedFile && (
                <Grid item xs={12}>
                  <Typography variant="body1" align="center">
                    Selected File: {selectedFile.name}
                  </Typography>
                </Grid>
              )}
              <Grid item xs={12}>
                <Button variant="contained" type="submit" fullWidth disabled={loading}>
                  {loading ? <CircularProgress size={24} color="inherit" /> : 'Upload and Recognize'}
                </Button>
              </Grid>
            </Grid>
          </Box>
          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
          {result && (
            <Alert severity="success" sx={{ mt: 2 }}>
              {result}
            </Alert>
          )}
        </Paper>
      </Container>
    </>
  );
}

export default App;