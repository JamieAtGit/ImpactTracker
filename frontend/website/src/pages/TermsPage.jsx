import React from "react";
import { motion } from "framer-motion";
import ModernLayout, { ModernCard, ModernSection } from "../components/ModernLayout";
import Header from "../components/Header";
import Footer from "../components/Footer";

export default function TermsPage() {
  const sections = [
    {
      title: "1. Introduction and Acceptance",
      content: [
        "These Terms of Service ('Terms') govern your access to and use of the EcoSmart Environmental Impact Prediction Platform ('Platform'), including all related websites, applications, and services provided by the University College London Computer Science Department ('UCL', 'we', 'us', or 'our').",
        "By accessing or using our Platform, you agree to be bound by these Terms and our Privacy Policy. If you disagree with any part of these Terms, you may not access the Platform.",
        "These Terms constitute a legally binding agreement between you and UCL regarding your use of the Platform."
      ]
    },
    {
      title: "2. Description of Service",
      content: [
        "The Platform provides environmental impact predictions for consumer products using advanced machine learning algorithms and data science techniques. Our services include:",
        "• Product carbon footprint estimation using XGBoost and Random Forest models",
        "• Material analysis and recyclability assessment",
        "• Transportation impact calculations based on origin and destination data",
        "• Packaging environmental impact evaluation",
        "• Browser extension for real-time product analysis",
        "The Platform is designed for research, educational, and informational purposes as part of ongoing academic research at UCL."
      ]
    },
    {
      title: "3. Research and Academic Use",
      content: [
        "This Platform is part of a university dissertation project and ongoing research in environmental data science. By using the Platform, you acknowledge that:",
        "• The Platform is primarily designed for research and academic purposes",
        "• Predictions are based on machine learning models trained on available data and may not reflect actual environmental impacts with 100% accuracy",
        "• The research is ongoing and methodologies may be updated as new data becomes available",
        "• You may be contributing to academic research by using the Platform (anonymized usage data may be collected for research purposes)"
      ]
    },
    {
      title: "4. User Responsibilities and Acceptable Use",
      content: [
        "You agree to use the Platform responsibly and in accordance with all applicable laws and regulations. You must not:",
        "• Use the Platform for any unlawful purpose or in violation of any local, state, national, or international law",
        "• Attempt to gain unauthorized access to any part of the Platform, other accounts, computer systems, or networks",
        "• Use automated scripts, bots, or other automated means to access the Platform without express written permission",
        "• Interfere with or disrupt the Platform's functionality or servers",
        "• Reverse engineer, decompile, or disassemble any part of the Platform",
        "• Use the Platform in a way that could damage, disable, overburden, or impair the Platform"
      ]
    },
    {
      title: "5. Data Collection and Privacy",
      content: [
        "We collect and process data in accordance with our Privacy Policy and applicable data protection laws, including GDPR. This includes:",
        "• Product URLs and metadata for environmental analysis",
        "• Location data (postcodes) for transportation impact calculations",
        "• Usage analytics for research and Platform improvement",
        "• Technical information about your device and browser for functionality purposes",
        "All data collection is performed in compliance with university research ethics guidelines and UK data protection regulations."
      ]
    },
    {
      title: "6. Intellectual Property Rights",
      content: [
        "The Platform and its original content, features, and functionality are owned by UCL and are protected by international copyright, trademark, patent, trade secret, and other intellectual property laws.",
        "The machine learning models, algorithms, and research methodologies used in the Platform are the result of academic research and remain the intellectual property of UCL and the research team.",
        "You may not reproduce, distribute, modify, create derivative works of, publicly display, publicly perform, republish, download, store, or transmit any of the material on our Platform without our prior written consent."
      ]
    },
    {
      title: "7. Disclaimers and Limitations",
      content: [
        "ACADEMIC RESEARCH DISCLAIMER: The Platform provides predictions based on machine learning models developed for research purposes. These predictions are estimates and should not be considered as absolute or guaranteed environmental impact assessments.",
        "NO WARRANTY: The Platform is provided 'as is' and 'as available' without any warranties of any kind, whether express or implied, including but not limited to warranties of merchantability, fitness for a particular purpose, or non-infringement.",
        "LIMITATION OF LIABILITY: UCL and the research team shall not be liable for any indirect, incidental, special, consequential, or punitive damages resulting from your use of the Platform.",
        "The Platform is developed and maintained by students and researchers as part of academic work and may contain errors or inaccuracies."
      ]
    },
    {
      title: "8. Third-Party Services and Links",
      content: [
        "The Platform may integrate with third-party services including:",
        "• Amazon product databases for product information retrieval",
        "• External APIs for environmental data and carbon footprint calculations",
        "• Browser extension platforms and stores",
        "We are not responsible for the content, privacy policies, or practices of any third-party websites or services. You acknowledge and agree that we shall not be liable for any damage or loss caused by your use of any third-party services."
      ]
    },
    {
      title: "9. Research Ethics and Data Handling",
      content: [
        "This research project adheres to UCL's research ethics guidelines and has been approved by the relevant ethics committee where required.",
        "All research data is handled in accordance with academic research standards and GDPR requirements.",
        "Participants' rights include the right to withdraw from the research and request deletion of their data.",
        "Research findings may be published in academic journals, conferences, and dissertations, but all published data will be anonymized and aggregated."
      ]
    },
    {
      title: "10. Modifications to Terms",
      content: [
        "We reserve the right to modify these Terms at any time, in our sole discretion. If we make material changes to these Terms, we will notify users by posting the updated Terms on the Platform.",
        "Your continued use of the Platform after any such changes constitutes your acceptance of the new Terms.",
        "It is your responsibility to check these Terms periodically for changes."
      ]
    },
    {
      title: "11. Termination",
      content: [
        "We may terminate or suspend your access to the Platform immediately, without prior notice or liability, for any reason whatsoever, including without limitation if you breach the Terms.",
        "Upon termination, your right to use the Platform will cease immediately.",
        "As this is a research platform, access may also be terminated at the conclusion of the research project or academic program."
      ]
    },
    {
      title: "12. Governing Law and Jurisdiction",
      content: [
        "These Terms shall be governed by and construed in accordance with the laws of England and Wales, without regard to its conflict of law provisions.",
        "Any disputes arising from these Terms or your use of the Platform shall be subject to the exclusive jurisdiction of the courts of England and Wales.",
        "If you are accessing the Platform from outside the United Kingdom, you are responsible for compliance with local laws."
      ]
    },
    {
      title: "13. Contact Information",
      content: [
        "If you have any questions about these Terms, please contact us at:",
        "Email: legal@ecosmart.ai",
        "Address: Department of Computer Science, University College London, Gower Street, London WC1E 6BT, United Kingdom",
        "For academic inquiries: research@ecosmart.ai",
        "For technical support: support@ecosmart.ai"
      ]
    }
  ];

  return (
    <ModernLayout>
      {{
        nav: <Header />,
        content: (
          <div className="space-y-16">
            {/* Hero Section */}
            <ModernSection className="text-center">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="space-y-6"
              >
                <h1 className="text-5xl font-bold bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-500 bg-clip-text text-transparent">
                  Terms of Service
                </h1>
                <p className="text-xl text-slate-300 max-w-4xl mx-auto">
                  These terms govern your use of the EcoSmart Environmental Impact Prediction Platform.
                  Please read them carefully before using our research platform.
                </p>
                <div className="flex items-center justify-center space-x-4 text-sm text-slate-400">
                  <span>Last Updated: January 2025</span>
                  <span>•</span>
                  <span>Version 1.0</span>
                  <span>•</span>
                  <span>Academic Research Platform</span>
                </div>
              </motion.div>
            </ModernSection>

            {/* Quick Summary */}
            <ModernSection>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
              >
                <ModernCard className="p-8 border-l-4 border-cyan-500">
                  <h2 className="text-2xl font-semibold text-cyan-400 mb-4">
                    Quick Summary
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-slate-300">
                    <div>
                      <h3 className="font-medium text-slate-200 mb-2">What This Platform Does</h3>
                      <ul className="space-y-1 text-sm text-slate-400">
                        <li>• Provides environmental impact predictions for products</li>
                        <li>• Uses machine learning models for carbon footprint estimation</li>
                        <li>• Supports academic research in environmental data science</li>
                        <li>• Offers browser extension for real-time analysis</li>
                      </ul>
                    </div>
                    <div>
                      <h3 className="font-medium text-slate-200 mb-2">Your Responsibilities</h3>
                      <ul className="space-y-1 text-sm text-slate-400">
                        <li>• Use the platform responsibly and legally</li>
                        <li>• Respect intellectual property rights</li>
                        <li>• Understand this is a research platform</li>
                        <li>• Comply with these terms and privacy policy</li>
                      </ul>
                    </div>
                  </div>
                  <div className="mt-6 p-4 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                    <p className="text-amber-400 text-sm font-medium">
                      <span className="mr-2">⚠️</span>
                      Important: This is an academic research platform. Predictions are estimates for research purposes and should not be considered as absolute environmental impact assessments.
                    </p>
                  </div>
                </ModernCard>
              </motion.div>
            </ModernSection>

            {/* Detailed Terms */}
            <ModernSection>
              <div className="space-y-8 max-w-5xl mx-auto">
                {sections.map((section, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.1 * index }}
                  >
                    <ModernCard className="p-8">
                      <h2 className="text-xl font-semibold text-cyan-400 mb-4">
                        {section.title}
                      </h2>
                      <div className="space-y-4">
                        {section.content.map((paragraph, pIndex) => (
                          <p key={pIndex} className="text-slate-300 leading-relaxed">
                            {paragraph}
                          </p>
                        ))}
                      </div>
                    </ModernCard>
                  </motion.div>
                ))}
              </div>
            </ModernSection>

            {/* Footer Information */}
            <ModernSection>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.8 }}
              >
                <ModernCard className="p-8 bg-gradient-to-r from-slate-800/50 to-slate-700/50">
                  <div className="text-center space-y-4">
                    <h3 className="text-lg font-semibold text-slate-200">
                      Academic Research Platform
                    </h3>
                    <p className="text-slate-300 max-w-3xl mx-auto">
                      This platform is developed as part of a Computer Science dissertation at University College London.
                      It represents ongoing research in environmental data science and machine learning applications for sustainability.
                    </p>
                    <div className="flex items-center justify-center space-x-8 text-sm text-slate-400">
                      <div className="flex items-center space-x-2">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                        </svg>
                        <span>Academic Research</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>GDPR Compliant</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                        </svg>
                        <span>Research Ethics Approved</span>
                      </div>
                    </div>
                  </div>
                </ModernCard>
              </motion.div>
            </ModernSection>
            
            <Footer />
          </div>
        ),
      }}
    </ModernLayout>
  );
}