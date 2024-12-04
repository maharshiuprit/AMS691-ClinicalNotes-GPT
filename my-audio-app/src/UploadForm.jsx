// src/UploadForm.jsx

import React, { useState } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { saveAs } from 'file-saver';
import CircularProgress from '@mui/material/CircularProgress';

const UploadForm = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!selectedFile) {
      toast.error('Please select an audio file to upload.');
      return;
    }

    const formData = new FormData();
    formData.append('audio_file', selectedFile);

    setIsUploading(true);
    toast.info('Uploading and processing the audio file...');

    try {
      const response = await axios.post(
        'http://localhost:8000/process-audio',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          responseType: 'blob', // Important for handling binary data
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            // You can use this to display upload progress
          },
        }
      );

      // Create a Blob from the response
      const blob = new Blob([response.data], {
        type: response.headers['content-type'],
      });
      const fileName = response.headers['content-disposition']
        ? response.headers['content-disposition'].split('filename=')[1]
        : 'generated_report.docx';

      // Use FileSaver to save the file
      saveAs(blob, fileName);

      toast.success('Report generated successfully!');
    } catch (error) {
      console.error(error);
      toast.error('An error occurred while processing the audio file.');
    } finally {
      setIsUploading(false);
      setSelectedFile(null);
    }
  };

  return (
    <div className="upload-form">
      <h2>Upload Audio File</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="file"
          accept=".mp3, .wav, .m4a, .aac"
          onChange={handleFileChange}
          disabled={isUploading}
        />
        <button type="submit" disabled={isUploading}>
          {isUploading ? 'Processing...' : 'Upload and Generate Report'}
        </button>
        {isUploading && (
          <div style={{ marginTop: '20px', textAlign: 'center' }}>
            <CircularProgress />
          </div>
        )}
      </form>
    </div>
  );
};

export default UploadForm;
