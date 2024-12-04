// src/ListReports.jsx

import React, { useState, useEffect } from "react";
import axios from "axios";
import Button from "@mui/material/Button";
import { format } from "date-fns";

const ListReports = () => {
  const [reports, setReports] = useState([]);

  useEffect(() => {
    // Fetch the list of reports from the backend API
    const fetchReports = async () => {
      try {
        const response = await axios.get("http://localhost:8000/list-reports");
        setReports(response.data.reports);
      } catch (error) {
        console.error("Error fetching reports:", error);
      }
    };

    fetchReports();
  }, []);

  const handleDownload = (report) => {
    // Implement the download functionality
    const url = `http://localhost:8000/download-report/${encodeURIComponent(
      report.name
    )}`;
    window.open(url, "_blank");
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
              <th>Date Modified</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {reports.map((report, index) => (
              <tr key={index}>
                <td>{report.name}</td>
                <td>
                  {format(
                    new Date(report.modified_time * 1000),
                    "yyyy-MM-dd HH:mm:ss"
                  )}
                </td>
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
