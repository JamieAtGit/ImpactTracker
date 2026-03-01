import React, { useState } from "react";
import { motion } from "framer-motion";
import ModernLayout, { ModernCard, ModernSection, ModernButton, ModernInput } from "../components/ModernLayout";
import Header from "../components/Header";
import ProductImpactCard from "../components/ProductImpactCard";
import InsightsDashboard from "../components/InsightsDashboard";
import EcoLogTable from "../components/EcoLogTable";
import Footer from "../components/Footer";
const BASE_URL = import.meta.env.VITE_API_BASE_URL;

export default function HomePage() {
  const [url, setUrl] = useState("");
  const [postcode, setPostcode] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [showML, setShowML] = useState(false); // Default to comparison mode

  const handleSearch = async () => {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const res = await fetch(`${BASE_URL}/estimate_emissions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          amazon_url: url,
          postcode: postcode || "SW1A 1AA",
          include_packaging: true,
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Unknown error");

      // Include the product title from the top level
      console.log("🐛 DEBUG HomePage - Raw API response:", data);
      console.log("🐛 DEBUG HomePage - data.data:", data.data);
      console.log("🐛 DEBUG HomePage - data.data.attributes:", data.data?.attributes);
      console.log("🐛 DEBUG HomePage - data.data.attributes.materials:", data.data?.attributes?.materials);
      
      const resultWithTitle = {
        ...data.data,
        title: data.title || "Unknown Product"
      };
      
      console.log("🐛 DEBUG HomePage - resultWithTitle:", resultWithTitle);
      setResult(resultWithTitle);
    } catch (err) {
      setError(err.message || "Failed to contact backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <ModernLayout>
      {{
        nav: <Header />,
        content: (
          <div className="space-y-12">
            {/* Hero Section */}
            <ModernSection className="text-center">
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className="space-y-6"
              >
                <h1 className="text-4xl md:text-6xl font-display font-bold leading-tight">
                  <span className="text-slate-100">Discover your product's</span>
                  <br />
                  <span className="bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 bg-clip-text text-transparent">
                    environmental impact
                  </span>
                </h1>
                <motion.p
                  className="text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.6, delay: 0.4 }}
                >
                  Enter an Amazon product URL and postcode to get comprehensive environmental analysis 
                  powered by our advanced AI sustainability assessment.
                </motion.p>
              </motion.div>
            </ModernSection>

            {/* Search Interface */}
            <ModernSection>
              <ModernCard className="max-w-4xl mx-auto" solid hover>
                <div className="space-y-6">
                  <div className="text-center">
                    <h2 className="text-xl font-display text-slate-200 mb-2">
                      Product Impact Analysis
                    </h2>
                    <p className="text-slate-400 text-sm">
                      Get detailed environmental insights in seconds
                    </p>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                    <div className="lg:col-span-2">
                      <ModernInput
                        label="Product URL"
                        type="text"
                        placeholder="https://amazon.com/product-url"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        icon="🔗"
                      />
                    </div>
                    <div>
                      <ModernInput
                        label="Postcode (Optional)"
                        type="text"
                        placeholder="SW1A 1AA"
                        value={postcode}
                        onChange={(e) => setPostcode(e.target.value)}
                        icon="📍"
                      />
                    </div>
                  </div>

                  <div className="flex justify-center pt-2">
                    <ModernButton
                      variant="accent"
                      size="lg"
                      onClick={handleSearch}
                      disabled={loading || !url}
                      loading={loading}
                      icon={loading ? null : "🔍"}
                      className="min-w-48"
                    >
                      {loading ? "Analyzing..." : "Analyze Impact"}
                    </ModernButton>
                  </div>

                  {/* Error Message */}
                  {error && (
                    <motion.div
                      className="text-center p-4 bg-red-900/20 border border-red-500/30 rounded-lg"
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ duration: 0.3 }}
                    >
                      <p className="text-red-400 flex items-center justify-center gap-2">
                        <span>⚠️</span>
                        <span>{error}</span>
                      </p>
                    </motion.div>
                  )}
                </div>
              </ModernCard>
            </ModernSection>

            {/* Result Card */}
            {result && (
              <ModernSection delay={0.2}>
                <ProductImpactCard
                  result={result}
                  showML={showML}
                  toggleShowML={() => setShowML(!showML)}
                />
              </ModernSection>
            )}

            {/* Dashboard */}
            <ModernSection 
              title="Analytics Dashboard" 
              icon={true}
              delay={0.4}
            >
              <InsightsDashboard />
            </ModernSection>

            {/* Product Log */}
            <ModernSection 
              title="Product Impact Database" 
              icon={true}
              delay={0.6}
            >
              <EcoLogTable />
            </ModernSection>

            {/* Footer */}
            <Footer />
          </div>
        ),
      }}
    </ModernLayout>
  );
}
