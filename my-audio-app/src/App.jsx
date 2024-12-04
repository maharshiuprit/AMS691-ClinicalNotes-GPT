// src/App.jsx

import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  NavLink,
} from "react-router-dom";
import UploadForm from "./UploadForm";
import ListReports from "./ListReports";
import "./App.css";

const App = () => {
  return (
    <Router>
      <div className="App">
        {/* Top Navigation Bar */}
        <header className="App-header">
          <h1>Medical Report Generator</h1>
        </header>

        {/* Body with Sidebar and Main Content */}
        <div className="App-body">
          {/* Left Navigation Sidebar */}
          <nav className="App-sidebar">
            <ul>
              <li>
                <NavLink
                  to="/upload"
                  className={({ isActive }) => (isActive ? "active" : "")}
                >
                  Upload Content
                </NavLink>
              </li>
              <li>
                <NavLink
                  to="/reports"
                  className={({ isActive }) => (isActive ? "active" : "")}
                >
                  List Reports
                </NavLink>
              </li>
            </ul>
          </nav>

          {/* Main Content Area */}
          <main className="App-content">
            <Routes>
              <Route path="/upload" element={<UploadForm />} />
              <Route path="/reports" element={<ListReports />} />
              {/* Default Route */}
              <Route path="/" element={<UploadForm />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
};

export default App;
