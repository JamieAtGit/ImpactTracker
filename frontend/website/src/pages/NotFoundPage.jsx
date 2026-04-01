import React from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import ModernLayout, { ModernCard, ModernSection } from "../components/ModernLayout";
import Header from "../components/Header";

export default function NotFoundPage() {
  return (
    <ModernLayout>
      {{
        nav: <Header />,
        content: (
          <ModernSection className="text-center">
            <motion.div
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <ModernCard className="max-w-md mx-auto">
                <div className="space-y-5 py-4">
                  <div className="text-6xl">🌿</div>
                  <h1 className="text-4xl font-display font-bold text-slate-100">404</h1>
                  <p className="text-slate-300 font-medium">Page not found</p>
                  <p className="text-slate-500 text-sm">
                    This page doesn't exist. Try heading back to the home page.
                  </p>
                  <Link to="/">
                    <button className="btn-primary px-6 py-2 mt-2">Go home</button>
                  </Link>
                </div>
              </ModernCard>
            </motion.div>
          </ModernSection>
        ),
      }}
    </ModernLayout>
  );
}
