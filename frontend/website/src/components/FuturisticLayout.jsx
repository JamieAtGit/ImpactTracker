import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";

const FuturisticBackground = () => {
  const [particles, setParticles] = useState([]);

  useEffect(() => {
    const newParticles = [];
    for (let i = 0; i < 50; i++) {
      newParticles.push({
        id: i,
        x: Math.random() * 100,
        y: Math.random() * 100,
        delay: Math.random() * 6,
      });
    }
    setParticles(newParticles);
  }, []);

  return (
    <>
      <div className="animated-bg" />
      <div className="particles">
        {particles.map((particle) => (
          <motion.div
            key={particle.id}
            className="particle"
            style={{
              left: `${particle.x}%`,
              top: `${particle.y}%`,
            }}
            animate={{
              y: [-20, -40, -20],
              x: [-10, 10, -10],
              opacity: [0, 0.8, 0],
            }}
            transition={{
              duration: 6 + particle.delay,
              repeat: Infinity,
              delay: particle.delay,
              ease: "easeInOut",
            }}
          />
        ))}
      </div>
    </>
  );
};

const FuturisticNav = ({ children }) => {
  return (
    <motion.header 
      className="glass-panel fixed top-4 left-4 right-4 z-50 p-4"
      initial={{ opacity: 0, y: -50 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      <div className="flex justify-between items-center max-w-7xl mx-auto">
        {children}
      </div>
    </motion.header>
  );
};

const FuturisticContainer = ({ children, className = "" }) => {
  return (
    <motion.div
      className={`relative z-10 min-h-screen pt-24 pb-8 px-4 ${className}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8, ease: "easeOut" }}
    >
      <div className="max-w-7xl mx-auto">
        {children}
      </div>
    </motion.div>
  );
};

const FuturisticCard = ({ children, className = "", glow = false, ...props }) => {
  return (
    <motion.div
      className={`glass-panel p-6 ${glow ? 'hover-glow' : ''} ${className}`}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      whileHover={{ scale: 1.02 }}
      {...props}
    >
      {children}
    </motion.div>
  );
};

const FuturisticSection = ({ children, title, icon, className = "" }) => {
  return (
    <motion.section
      className={`mb-12 ${className}`}
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      {title && (
        <motion.div
          className="flex items-center gap-3 mb-6"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          {icon && <span className="text-2xl">{icon}</span>}
          <h2 className="text-2xl font-futuristic font-bold text-glow">
            {title}
          </h2>
        </motion.div>
      )}
      {children}
    </motion.section>
  );
};

export default function FuturisticLayout({ children, showNav = true }) {
  return (
    <div className="relative min-h-screen overflow-hidden">
      <FuturisticBackground />
      {showNav && (
        <FuturisticNav>
          {children?.nav}
        </FuturisticNav>
      )}
      <FuturisticContainer>
        {children?.content || children}
      </FuturisticContainer>
    </div>
  );
}

export { FuturisticNav, FuturisticContainer, FuturisticCard, FuturisticSection };