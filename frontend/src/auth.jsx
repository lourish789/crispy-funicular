import { createContext, useContext, useEffect, useState } from "react";
import { api, setToken, getToken } from "./api.js";
import { googleSignIn } from "./firebase.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (getToken()) {
      api
        .me()
        .then(setUser)
        .catch(() => setToken(""))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  async function login(email, password) {
    const data = await api.login({ email, password });
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  }

  async function register(full_name, email, password, role = "farmer") {
    const data = await api.register({ full_name, email, password, role });
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  }

  async function firebaseLogin(role = "farmer") {
    const idToken = await googleSignIn();
    const data = await api.firebaseAuth(idToken, role);
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  }

  function logout() {
    setToken("");
    setUser(null);
  }

  async function refresh() {
    const u = await api.me();
    setUser(u);
    return u;
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, firebaseLogin, logout, refresh, setUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
