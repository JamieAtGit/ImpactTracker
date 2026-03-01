// src/hooks/useAuth.js
import { useEffect, useState } from "react";
const BASE_URL = import.meta.env.VITE_API_BASE_URL;

export default function useAuth() {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("user");
    return saved ? JSON.parse(saved) : null;
  });

  useEffect(() => {
    const checkSession = async () => {
      try {
        const res = await fetch(`${BASE_URL}/me`, {
          credentials: "include"
        });
        if (res.ok) {
          const data = await res.json();
          setUser(data);
          localStorage.setItem("user", JSON.stringify(data));
        } else {
          setUser(null);
          localStorage.removeItem("user");
        }
      } catch {
        setUser(null);
      }
    };
    checkSession();
  }, []);

  const logout = async () => {
    await fetch(`${BASE_URL}/logout`, {
      method: "POST",
      credentials: "include"
    });
    setUser(null);
    localStorage.removeItem("user");
  };

  return { user, setUser, logout };
}
