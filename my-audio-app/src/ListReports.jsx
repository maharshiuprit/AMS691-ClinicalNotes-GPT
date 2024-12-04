// src/ListReports.jsx

import React, { useState, useEffect } from 'react';
import Button from '@mui/material/Button';

const ListReports = () => {
  const [reports, setReports] = useState([]);

  useEffect(() => {
    // Fetch the list of reports from the backend API (mocked here)
    // You can replace this with an actual API call
    const fetchReports = async () => {
      // Mock data
      const data = [
        { id: 1, name: 'Report_2023-10-01.docx', date: '2023-10-01' },
        { id: 2, name: 'Report_2023-10-02.docx', date: '2023-10-02' },
        // Add more mock reports
      ];
      setReports(data);
    };

    fetchReports();
  }, []);

  const handleDownload = (report) => {
    // Implement the download functionality
    console.log(`Downloading report: ${report.name}`);
    // You can make an API call to download the report
  };

  return (
    <div className="list-reports">
      <h2>List of Reports</h2>
      {reports.length === 0 ? (
        <p>No reports available.</p>
      ) : (
        <table className="reports-table">
          <thead>
            <tr>
              <th>Report Name</th>
              <th>Date Generated</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {reports.map((report) => (
              <tr key={report.id}>
                <td>{report.name}</td>
                <td>{report.date}</td>
                <td>
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={() => handleDownload(report)}
                  >
                    Download
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default ListReports;
