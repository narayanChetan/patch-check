import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import LedgerPage from "./pages/LedgerPage";
import LoginPage from "./pages/LoginPage";
import ScannerPage from "./pages/ScannerPage";

function ProtectedRoute({ children }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/scan" element={<ProtectedRoute><ScannerPage /></ProtectedRoute>} />
      <Route path="/ledger" element={<ProtectedRoute><LedgerPage /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/scan" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  );
}
