// src/App.jsx
import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage";
import LearnPage from "./pages/LearnPage";
import PredictPage from "./pages/PredictPage"; 
import AdminPage from "./pages/AdminPage";
import LogOnPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import ExtensionPage from "./pages/ExtensionPage";
import ContactPage from "./pages/ContactPage";
import TermsPage from "./pages/TermsPage";
import PrivacyPage from "./pages/PrivacyPage";


export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/learn" element={<LearnPage />} />
        <Route path="/predict" element={<PredictPage />} /> 
        <Route path="/admin" element={<AdminPage />} /> 
        <Route path="/login" element={<LogOnPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/extension" element={<ExtensionPage />} />
        <Route path="/contact" element={<ContactPage />} />
        <Route path="/terms" element={<TermsPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
      </Routes>
    </Router>
  );
}
