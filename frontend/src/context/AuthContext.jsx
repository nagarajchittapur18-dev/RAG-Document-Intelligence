import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    try {
      const savedUser = localStorage.getItem('ragmate_user');
      return savedUser ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });

  const [token, setToken] = useState(() => localStorage.getItem('ragmate_token'));
  const [loading, setLoading] = useState(true);

  // Validate existing token on initial mount
  useEffect(() => {
    const verifyAuth = async () => {
      const storedToken = localStorage.getItem('ragmate_token');
      if (storedToken) {
        try {
          const profile = await api.getMe();
          setUser(profile);
          localStorage.setItem('ragmate_user', JSON.stringify(profile));
        } catch (err) {
          console.warn('Stored session invalid or expired:', err.message);
          localStorage.removeItem('ragmate_token');
          localStorage.removeItem('ragmate_user');
          setToken(null);
          setUser(null);
        }
      }
      setLoading(false);
    };

    verifyAuth();
  }, []);

  const login = async (email, password) => {
    const data = await api.login(email, password);
    const { access_token, user: userData } = data;
    localStorage.setItem('ragmate_token', access_token);
    localStorage.setItem('ragmate_user', JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
    return data;
  };

  const register = async (name, email, password) => {
    const data = await api.register(name, email, password);
    // Automatically log in upon successful registration
    return await login(email, password);
  };

  const logout = () => {
    localStorage.removeItem('ragmate_token');
    localStorage.removeItem('ragmate_user');
    setToken(null);
    setUser(null);
  };

  const value = {
    user,
    token,
    loading,
    isAuthenticated: Boolean(token && user),
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
