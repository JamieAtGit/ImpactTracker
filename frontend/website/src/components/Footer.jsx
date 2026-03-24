import React from "react";
import { Link } from "react-router-dom";

export default function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="w-full border-t border-slate-700/60 bg-slate-900/60 py-10 text-sm mt-auto">
      <div className="max-w-7xl mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">

          {/* Brand */}
          <div className="col-span-1 md:col-span-2 space-y-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-cyan-500 flex items-center justify-center">
                <span className="text-sm">🌿</span>
              </div>
              <span className="text-slate-200 font-semibold">Impact Tracker</span>
            </div>
            <p className="text-slate-400 text-sm leading-relaxed max-w-xs">
              AI-powered environmental impact prediction for everyday products.
              Built as academic research at the University of the West of England.
            </p>
            <div className="flex flex-wrap gap-2">
              {["GDPR Compliant", "Open Research", "Academic Project"].map(tag => (
                <span key={tag} className="text-xs bg-slate-800 border border-slate-700 text-slate-400 rounded-full px-2.5 py-1">
                  {tag}
                </span>
              ))}
            </div>
            {/* Tech stack — good for dissertation */}
            <div>
              <p className="text-slate-600 text-xs mb-1.5 uppercase tracking-wider">Built with</p>
              <div className="flex flex-wrap gap-1.5">
                {["Python", "Flask", "XGBoost", "PostgreSQL", "React", "Tailwind"].map(tech => (
                  <span key={tech} className="text-xs bg-slate-800/80 border border-slate-700/60 text-slate-500 rounded px-2 py-0.5 font-mono">
                    {tech}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Platform links */}
          <div>
            <h4 className="font-semibold text-slate-300 mb-3 text-xs uppercase tracking-wider">Platform</h4>
            <ul className="space-y-2">
              {[
                { to: "/",          label: "Home"              },
                { to: "/predict",   label: "Impact Explorer"   },
                { to: "/learn",     label: "Research & Learn"  },
                { to: "/extension", label: "Browser Extension" },
                { to: "/history",   label: "Your History"      },
              ].map(({ to, label }) => (
                <li key={to}>
                  <Link to={to} className="text-slate-400 hover:text-cyan-400 transition-colors">
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal & support */}
          <div>
            <h4 className="font-semibold text-slate-300 mb-3 text-xs uppercase tracking-wider">Legal & Support</h4>
            <ul className="space-y-2">
              {[
                { to: "/contact", label: "Contact Us"       },
                { to: "/privacy", label: "Privacy Policy"   },
                { to: "/terms",   label: "Terms of Service" },
              ].map(({ to, label }) => (
                <li key={to}>
                  <Link to={to} className="text-slate-400 hover:text-cyan-400 transition-colors">
                    {label}
                  </Link>
                </li>
              ))}
              <li>
                <a
                  href="mailto:impact-tracker@uwe.ac.uk"
                  className="text-slate-400 hover:text-cyan-400 transition-colors"
                >
                  Email Support
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-t border-slate-700/50 pt-6 flex flex-col md:flex-row justify-between items-center gap-3">
          <p className="text-slate-500 text-xs">
            © {year} University of the West of England · Computer Science Department
          </p>
          <div className="flex items-center gap-4 text-slate-600 text-xs">
            <span>Environmental Data Science</span>
            <span>·</span>
            <span>Machine Learning Applications</span>
            <span>·</span>
            <span>Academic Research</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
