import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth.jsx";
import Navbar from "./components/Navbar.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Diagnosis from "./pages/Diagnosis.jsx";
import Advisory from "./pages/Advisory.jsx";
import News from "./pages/News.jsx";
import Marketplace from "./pages/Marketplace.jsx";
import Community from "./pages/Community.jsx";
import Chat from "./pages/Chat.jsx";
import Profile from "./pages/Profile.jsx";

function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="loader">Loading…</div>;
  return user ? children : <Navigate to="/login" replace />;
}

export default function App() {
  const { user } = useAuth();
  return (
    <div className="app-shell">
      {user && <Navbar />}
      <main className={user ? "app-main" : ""}>
        <Routes>
          <Route path="/login" element={user ? <Navigate to="/" /> : <Login />} />
          <Route path="/" element={<Protected><Dashboard /></Protected>} />
          <Route path="/diagnosis" element={<Protected><Diagnosis /></Protected>} />
          <Route path="/advisory" element={<Protected><Advisory /></Protected>} />
          <Route path="/news" element={<Protected><News /></Protected>} />
          <Route path="/marketplace" element={<Protected><Marketplace /></Protected>} />
          <Route path="/community" element={<Protected><Community /></Protected>} />
          <Route path="/chat" element={<Protected><Chat /></Protected>} />
          <Route path="/profile" element={<Protected><Profile /></Protected>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
