import React from "react";
import { motion } from "framer-motion";
import ModernLayout, { ModernCard, ModernSection } from "../components/ModernLayout";
import Header from "../components/Header";
import Footer from "../components/Footer";

export default function PrivacyPage() {
  const dataTypes = [
    {
      type: "Product Information",
      description: "Amazon URLs, product titles, descriptions, and metadata",
      purpose: "Environmental impact analysis and carbon footprint calculation",
      retention: "24 months for research analysis",
      legal: "Legitimate research interest (GDPR Art. 6(1)(f))"
    },
    {
      type: "Location Data",
      description: "Postcodes for delivery location calculations",
      purpose: "Transportation impact assessment and distance calculations",
      retention: "Immediately processed, not stored permanently",
      legal: "Necessary for service provision (GDPR Art. 6(1)(b))"
    },
    {
      type: "Usage Analytics",
      description: "Platform interactions, feature usage, and performance metrics",
      purpose: "Research improvement and platform optimization",
      retention: "36 months for longitudinal research analysis",
      legal: "Legitimate research interest (GDPR Art. 6(1)(f))"
    },
    {
      type: "Technical Data",
      description: "Browser type, device information, and IP addresses",
      purpose: "Platform functionality and security",
      retention: "12 months in anonymized form",
      legal: "Necessary for service provision (GDPR Art. 6(1)(b))"
    }
  ];

  const sections = [
    {
      title: "1. Introduction and Scope",
      content: [
        "This Privacy Policy describes how University College London ('UCL', 'we', 'us', or 'our') collects, uses, and protects your personal information when you use the EcoSmart Environmental Impact Prediction Platform ('Platform').",
        "This policy applies to all users of the Platform, including the web application and browser extension components.",
        "We are committed to protecting your privacy and complying with applicable data protection laws, including the UK General Data Protection Regulation (UK GDPR), the Data Protection Act 2018, and other relevant privacy legislation.",
        "As an academic institution, UCL processes personal data for research purposes under specific legal frameworks and ethical guidelines."
      ]
    },
    {
      title: "2. Data Controller Information",
      content: [
        "The data controller for this Platform is University College London (UCL), a higher education institution incorporated by Royal Charter.",
        "Registered Address: University College London, Gower Street, London WC1E 6BT, United Kingdom",
        "Data Protection Officer: dpo@ucl.ac.uk",
        "Research Ethics Committee: UCL Computer Science Department Research Ethics Committee",
        "For privacy-related inquiries specifically about this Platform, contact: privacy@ecosmart.ai"
      ]
    },
    {
      title: "3. Legal Basis for Processing",
      content: [
        "We process your personal data under the following legal bases:",
        "• Legitimate Interest (Article 6(1)(f) UK GDPR): For academic research purposes and platform improvement",
        "• Performance of a Contract (Article 6(1)(b) UK GDPR): To provide the environmental impact prediction services",
        "• Consent (Article 6(1)(a) UK GDPR): Where explicitly requested for specific research participation",
        "• Public Task (Article 6(1)(e) UK GDPR): As part of UCL's public research mission in environmental science",
        "For research purposes, we rely on the exemption for scientific research under Schedule 2, Paragraph 28 of the Data Protection Act 2018."
      ]
    },
    {
      title: "4. Information We Collect",
      content: [
        "We collect information that you provide directly and information that is automatically collected when you use our Platform:",
        "INFORMATION YOU PROVIDE:",
        "• Product URLs and associated metadata for environmental analysis",
        "• Location information (postcodes) for transportation calculations",
        "• Contact information when you reach out to us",
        "• Feedback and survey responses (when voluntarily provided)",
        "AUTOMATICALLY COLLECTED INFORMATION:",
        "• Usage patterns and interaction data with the Platform",
        "• Technical information about your device and browser",
        "• Performance metrics and error logs",
        "• Anonymized analytics data for research purposes"
      ]
    },
    {
      title: "5. How We Use Your Information",
      content: [
        "We use the collected information for the following purposes:",
        "RESEARCH AND ACADEMIC PURPOSES:",
        "• Developing and improving machine learning models for environmental impact prediction",
        "• Conducting academic research in environmental data science",
        "• Publishing research findings in academic journals and conferences (anonymized data only)",
        "• Supporting dissertation and thesis research projects",
        "PLATFORM OPERATION:",
        "• Providing environmental impact predictions and analysis",
        "• Maintaining and improving Platform functionality",
        "• Ensuring Platform security and preventing misuse",
        "• Providing technical support and customer service"
      ]
    },
    {
      title: "6. Research Data Handling",
      content: [
        "As an academic research platform, we follow strict guidelines for research data handling:",
        "• All research data is anonymized and aggregated before analysis",
        "• Individual users cannot be identified in research outputs",
        "• Research data is stored securely on UCL-approved systems",
        "• Data access is restricted to authorized research team members",
        "• Research findings may be published but will never include identifiable information",
        "• The research has been approved by relevant ethics committees where required"
      ]
    },
    {
      title: "7. Data Sharing and Third Parties",
      content: [
        "We do not sell your personal data to third parties. We may share information in the following limited circumstances:",
        "RESEARCH COLLABORATION:",
        "• With other academic institutions for collaborative research (anonymized data only)",
        "• With research partners under appropriate data sharing agreements",
        "SERVICE PROVIDERS:",
        "• Cloud hosting providers (data processed within UK/EU)",
        "• Analytics services for platform improvement (anonymized data only)",
        "LEGAL REQUIREMENTS:",
        "• When required by law or to protect our legal rights",
        "• To investigate potential violations of our Terms of Service"
      ]
    },
    {
      title: "8. International Data Transfers",
      content: [
        "We primarily process data within the United Kingdom and European Union. When data is transferred internationally:",
        "• Transfers are made only to countries with adequate data protection laws",
        "• Appropriate safeguards such as Standard Contractual Clauses are implemented",
        "• Research data transfers follow UCL's international data transfer policies",
        "• You will be informed of any significant international transfers that may affect your data"
      ]
    },
    {
      title: "9. Data Security",
      content: [
        "We implement appropriate technical and organizational measures to protect your personal data:",
        "TECHNICAL MEASURES:",
        "• Encryption in transit and at rest",
        "• Secure cloud infrastructure with access controls",
        "• Regular security updates and vulnerability assessments",
        "• Secure development practices and code review processes",
        "ORGANIZATIONAL MEASURES:",
        "• Staff training on data protection principles",
        "• Access controls and need-to-know principles",
        "• Regular review of data processing activities",
        "• Incident response procedures for data breaches"
      ]
    },
    {
      title: "10. Your Rights Under UK GDPR",
      content: [
        "You have the following rights regarding your personal data:",
        "• Right of Access: Request copies of your personal data",
        "• Right to Rectification: Request correction of inaccurate data",
        "• Right to Erasure: Request deletion of your data (subject to research exemptions)",
        "• Right to Restrict Processing: Request limitation of how we process your data",
        "• Right to Data Portability: Request transfer of your data to another service",
        "• Right to Object: Object to processing based on legitimate interests",
        "• Right to Withdraw Consent: Where processing is based on consent",
        "Note: Some rights may be limited for research purposes under the scientific research exemption in the Data Protection Act 2018."
      ]
    },
    {
      title: "11. Cookies and Tracking Technologies",
      content: [
        "We use cookies and similar technologies to enhance your experience:",
        "ESSENTIAL COOKIES:",
        "• Required for Platform functionality and security",
        "• Cannot be disabled without affecting Platform operation",
        "ANALYTICS COOKIES:",
        "• Help us understand how the Platform is used",
        "• Used for research and improvement purposes",
        "• Can be disabled through browser settings",
        "You can manage cookie preferences through your browser settings. Note that disabling cookies may affect Platform functionality."
      ]
    },
    {
      title: "12. Children's Privacy",
      content: [
        "This Platform is not intended for use by children under the age of 16. We do not knowingly collect personal information from children under 16.",
        "If you are under 16, please do not use this Platform or provide any personal information.",
        "If we become aware that we have collected personal information from a child under 16, we will take steps to delete such information promptly.",
        "For users aged 16-18, we recommend obtaining parental guidance before using the Platform."
      ]
    },
    {
      title: "13. Changes to This Privacy Policy",
      content: [
        "We may update this Privacy Policy from time to time to reflect changes in our practices or applicable laws.",
        "Significant changes will be communicated through:",
        "• Platform notifications",
        "• Email notifications (where contact information is available)",
        "• Updates posted on our website",
        "Your continued use of the Platform after changes take effect constitutes acceptance of the updated Privacy Policy."
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
                  Privacy Policy
                </h1>
                <p className="text-xl text-slate-300 max-w-4xl mx-auto">
                  Your privacy is important to us. This policy explains how we collect, use, and protect your personal information
                  in compliance with UK GDPR and academic research ethics guidelines.
                </p>
                <div className="flex items-center justify-center space-x-4 text-sm text-slate-400">
                  <span>Last Updated: January 2025</span>
                  <span>•</span>
                  <span>GDPR Compliant</span>
                  <span>•</span>
                  <span>Academic Research Platform</span>
                </div>
              </motion.div>
            </ModernSection>

            {/* Privacy Rights Summary */}
            <ModernSection>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
              >
                <ModernCard className="p-8 border-l-4 border-green-500">
                  <h2 className="text-2xl font-semibold text-green-400 mb-6">
                    Your Privacy Rights at a Glance
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div className="text-center">
                      <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                        <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                      </div>
                      <h3 className="font-medium text-slate-200 mb-1">Access</h3>
                      <p className="text-xs text-slate-400">See what data we have about you</p>
                    </div>
                    <div className="text-center">
                      <div className="w-12 h-12 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                        <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </div>
                      <h3 className="font-medium text-slate-200 mb-1">Correct</h3>
                      <p className="text-xs text-slate-400">Update inaccurate information</p>
                    </div>
                    <div className="text-center">
                      <div className="w-12 h-12 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                        <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </div>
                      <h3 className="font-medium text-slate-200 mb-1">Delete</h3>
                      <p className="text-xs text-slate-400">Request data removal*</p>
                    </div>
                    <div className="text-center">
                      <div className="w-12 h-12 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                        <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                      <h3 className="font-medium text-slate-200 mb-1">Portability</h3>
                      <p className="text-xs text-slate-400">Export your data</p>
                    </div>
                  </div>
                  <p className="text-xs text-slate-500 mt-4 text-center">
                    *Some limitations apply for research data under UK GDPR scientific research exemption
                  </p>
                </ModernCard>
              </motion.div>
            </ModernSection>

            {/* Data Types Table */}
            <ModernSection>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.3 }}
              >
                <h2 className="text-3xl font-bold text-center text-slate-200 mb-8">
                  Data We Collect and Why
                </h2>
                <div className="space-y-4">
                  {dataTypes.map((data, index) => (
                    <ModernCard key={index} className="p-6">
                      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
                        <div>
                          <h3 className="font-semibold text-cyan-400 mb-2">{data.type}</h3>
                          <p className="text-sm text-slate-300">{data.description}</p>
                        </div>
                        <div>
                          <h4 className="font-medium text-slate-200 mb-1">Purpose</h4>
                          <p className="text-sm text-slate-400">{data.purpose}</p>
                        </div>
                        <div>
                          <h4 className="font-medium text-slate-200 mb-1">Retention</h4>
                          <p className="text-sm text-slate-400">{data.retention}</p>
                        </div>
                        <div>
                          <h4 className="font-medium text-slate-200 mb-1">Legal Basis</h4>
                          <p className="text-sm text-slate-400">{data.legal}</p>
                        </div>
                      </div>
                    </ModernCard>
                  ))}
                </div>
              </motion.div>
            </ModernSection>

            {/* Detailed Privacy Policy */}
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

            {/* Contact and Complaints */}
            <ModernSection>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.8 }}
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <ModernCard className="p-8">
                    <h3 className="text-xl font-semibold text-cyan-400 mb-4">
                      Exercise Your Rights
                    </h3>
                    <p className="text-slate-300 mb-4">
                      To exercise any of your privacy rights or if you have questions about this policy:
                    </p>
                    <div className="space-y-3">
                      <p className="text-sm text-slate-400">
                        <span className="font-medium text-slate-300">Privacy Inquiries:</span> privacy@ecosmart.ai
                      </p>
                      <p className="text-sm text-slate-400">
                        <span className="font-medium text-slate-300">UCL Data Protection Officer:</span> dpo@ucl.ac.uk
                      </p>
                      <p className="text-sm text-slate-400">
                        <span className="font-medium text-slate-300">Research Ethics:</span> research@ecosmart.ai
                      </p>
                    </div>
                  </ModernCard>

                  <ModernCard className="p-8">
                    <h3 className="text-xl font-semibold text-purple-400 mb-4">
                      Complaints and Concerns
                    </h3>
                    <p className="text-slate-300 mb-4">
                      If you're not satisfied with our response, you can complain to:
                    </p>
                    <div className="space-y-3">
                      <p className="text-sm text-slate-400">
                        <span className="font-medium text-slate-300">Information Commissioner's Office (ICO)</span><br />
                        ico.org.uk | 0303 123 1113
                      </p>
                      <p className="text-sm text-slate-400">
                        <span className="font-medium text-slate-300">UCL Academic Services</span><br />
                        For research-related concerns
                      </p>
                    </div>
                  </ModernCard>
                </div>
              </motion.div>
            </ModernSection>
            
            <Footer />
          </div>
        ),
      }}
    </ModernLayout>
  );
}