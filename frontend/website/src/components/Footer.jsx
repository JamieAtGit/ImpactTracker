// src/components/Footer.jsx
import React from "react";
import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="w-full border-t border-slate-700 bg-slate-900/50 py-8 text-sm mt-auto">
      <div className="max-w-7xl mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand Section */}
          <div className="col-span-1 md:col-span-2">
            <h3 className="text-lg font-semibold text-cyan-400 mb-3">
              EcoSmart Platform
            </h3>
            <p className="text-slate-400 leading-relaxed mb-4">
              Advanced environmental impact prediction using machine learning and data science. 
              Developed as part of academic research at University College London.
            </p>
            <div className="flex items-center space-x-4 text-slate-500">
              <span className="flex items-center space-x-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                <span>Academic Research</span>
              </span>
              <span className="flex items-center space-x-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>GDPR Compliant</span>
              </span>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="font-semibold text-slate-200 mb-3">Platform</h4>
            <ul className="space-y-2">
              <li>
                <Link to="/predict" className="text-slate-400 hover:text-cyan-400 transition-colors">
                  Carbon Prediction
                </Link>
              </li>
              <li>
                <Link to="/learn" className="text-slate-400 hover:text-cyan-400 transition-colors">
                  Learn & Research
                </Link>
              </li>
              <li>
                <Link to="/extension" className="text-slate-400 hover:text-cyan-400 transition-colors">
                  Browser Extension
                </Link>
              </li>
              <li>
                <Link to="/admin" className="text-slate-400 hover:text-cyan-400 transition-colors">
                  Admin Dashboard
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal & Support */}
          <div>
            <h4 className="font-semibold text-slate-200 mb-3">Legal & Support</h4>
            <ul className="space-y-2">
              <li>
                <Link to="/contact" className="text-slate-400 hover:text-cyan-400 transition-colors">
                  Contact Us
                </Link>
              </li>
              <li>
                <Link to="/privacy" className="text-slate-400 hover:text-cyan-400 transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link to="/terms" className="text-slate-400 hover:text-cyan-400 transition-colors">
                  Terms of Service
                </Link>
              </li>
              <li>
                <a href="mailto:support@ecosmart.ai" className="text-slate-400 hover:text-cyan-400 transition-colors">
                  Technical Support
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="border-t border-slate-700 pt-6 flex flex-col md:flex-row justify-between items-center">
          <div className="text-slate-400 mb-4 md:mb-0">
            © 2025 University of The West of England. Built with 💚 for a sustainable future.
          </div>
          <div className="flex items-center space-x-6 text-slate-500">
            <span className="text-xs">Computer Science Department</span>
            <span className="text-xs">•</span>
            <span className="text-xs">Environmental Data Science Research</span>
            <span className="text-xs">•</span>
            <span className="text-xs">Machine Learning Applications</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
