// src/App.jsx

import React from "react";
import UploadForm from "./UploadForm";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import "./App.css";

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Audio Report Generator</h1>
      </header>
      <main>
        <UploadForm />
      </main>
      <ToastContainer />
    </div>
  );
}

export default App;
