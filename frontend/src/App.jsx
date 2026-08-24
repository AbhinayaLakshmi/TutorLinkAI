import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import OtpVerificationPage from "./pages/OtpVerificationPage";
import StudentOnboarding from "./pages/StudentOnboarding";
import TutorOnboarding from "./pages/TutorOnboarding";
import StudentDashboard from "./pages/StudentDashboard";
import TutorDashboard from "./pages/TutorDashboard";
import TutorVerificationPage from "./pages/TutorVerificationPage";
import { isAuthenticated } from "./services/auth";

// Route protection wrapper for authenticated pages
function ProtectedRoute({ children, requiredRole }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  const user = JSON.parse(localStorage.getItem("user"));
  if (requiredRole && user.role !== requiredRole) {
    return <Navigate to={user.role === "STUDENT" ? "/dashboard/student" : "/dashboard/tutor"} replace />;
  }

  return children;
}

export default function App() {
  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/verify-otp" element={<OtpVerificationPage />} />

        {/* Protected Onboarding Routes */}
        <Route
          path="/onboard/student"
          element={
            <ProtectedRoute requiredRole="STUDENT">
              <StudentOnboarding />
            </ProtectedRoute>
          }
        />
        <Route
          path="/onboard/tutor"
          element={
            <ProtectedRoute requiredRole="TUTOR">
              <TutorOnboarding />
            </ProtectedRoute>
          }
        />

        {/* Protected Dashboard Routes */}
        <Route
          path="/dashboard/student"
          element={
            <ProtectedRoute requiredRole="STUDENT">
              <StudentDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/tutor"
          element={
            <ProtectedRoute requiredRole="TUTOR">
              <TutorDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/tutor/verify"
          element={
            <ProtectedRoute requiredRole="TUTOR">
              <TutorVerificationPage />
            </ProtectedRoute>
          }
        />

        {/* Catch-all Redirect */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}
