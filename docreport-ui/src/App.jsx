import React, { useState } from "react";
import axios from "axios";
import { saveAs } from "file-saver";
import { FaUpload, FaHome, FaCog } from "react-icons/fa";

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [message, setMessage] = useState("");

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file && file.type.startsWith("audio/")) {
      setSelectedFile(file);
      setMessage("");
    } else {
      setSelectedFile(null);
      setMessage("Please select a valid audio file.");
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setMessage("Please select a file first.");
      return;
    }

    setIsProcessing(true);
    setMessage("Processing your file. Please wait...");

    const formData = new FormData();
    formData.append("audio_file", selectedFile);

    try {
      const response = await axios.post(
        "http://localhost:8000/process-audio",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
          responseType: "blob",
        }
      );

      if (response.status === 200) {
        const blob = new Blob([response.data], {
          type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        });
        saveAs(blob, "generated_report.docx");
        setMessage(
          "File processed successfully! Your document is ready for download."
        );
      } else {
        setMessage("An error occurred during processing.");
      }
    } catch (error) {
      console.error("Error uploading file:", error);
      setMessage("An error occurred during processing. Please try again.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <nav className="w-64 bg-gray-800 text-white flex flex-col p-6">
        <h2 className="text-2xl font-bold mb-8">MyApp</h2>
        <ul className="space-y-4">
          <li className="flex items-center space-x-3 p-2 hover:bg-gray-700 rounded cursor-pointer">
            <FaUpload />
            <span>Upload Recording</span>
          </li>
          <li className="flex items-center space-x-3 p-2 hover:bg-gray-700 rounded cursor-pointer">
            <FaHome />
            <span>Home</span>
          </li>
          <li className="flex items-center space-x-3 p-2 hover:bg-gray-700 rounded cursor-pointer">
            <FaCog />
            <span>Settings</span>
          </li>
        </ul>
      </nav>

      {/* Main Content */}
      <div className="flex flex-col flex-1">
        {/* Top Navigation */}
        <header className="bg-gray-700 text-white text-center py-4">
          <h1 className="text-2xl font-semibold">
            Audio to Document Processor
          </h1>
        </header>

        {/* Content Area */}
        <div className="flex-1 flex items-center justify-center bg-gray-100">
          <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-md">
            <input
              type="file"
              accept="audio/*"
              onChange={handleFileChange}
              disabled={isProcessing}
              className="block w-full p-2 mb-4 border border-gray-300 rounded"
            />
            <button
              onClick={handleUpload}
              disabled={isProcessing || !selectedFile}
              className={`w-full py-2 px-4 text-white rounded ${
                isProcessing || !selectedFile
                  ? "bg-gray-400 cursor-not-allowed"
                  : "bg-blue-500 hover:bg-blue-600"
              }`}
            >
              {isProcessing ? "Processing..." : "Upload and Process"}
            </button>
            <p className="mt-4 text-center text-gray-700">{message}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
