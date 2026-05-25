import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'sonner'
import { AuthProvider } from '@/hooks/useAuth'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'

// Layout
import MainLayout from '@/components/layout/MainLayout'
import AuthLayout from '@/components/layout/AuthLayout'

// Pages - Public
import HomePage from '@/pages/public/HomePage'
import LoginPage from '@/pages/auth/LoginPage'
import RegisterPage from '@/pages/auth/RegisterPage'
import ForgotPasswordPage from '@/pages/auth/ForgotPasswordPage'

// Pages - Employee
import EmployeeDashboard from '@/pages/employee/Dashboard'
import EmployeeProfile from '@/pages/employee/Profile'
import EmployeeJobsRecommended from '@/pages/employee/JobsRecommended'
import EmployeeApplications from '@/pages/employee/Applications'
import EmployeeSettings from '@/pages/employee/Settings'
import EmployeeMessages from '@/pages/employee/Messages'

// Pages - Employer
import EmployerDashboard from '@/pages/employer/Dashboard'
import EmployerProfile from '@/pages/employer/Profile'
import EmployerJobs from '@/pages/employer/Jobs'
import EmployerJobCreate from '@/pages/employer/JobCreate'
import EmployerApplications from '@/pages/employer/Applications'
import EmployerSettings from '@/pages/employer/Settings'
import EmployerMessages from '@/pages/employer/Messages'

// Pages - Superuser
import SuperuserDashboard from '@/pages/superuser/Dashboard'
import SuperuserUsers from '@/pages/superuser/Users'
import SuperuserFeedback from '@/pages/superuser/Feedback'
import SuperuserIssues from '@/pages/superuser/Issues'

// Pages - Misc
import JobsBrowse from '@/pages/public/JobsBrowse'
import JobDetail from '@/pages/public/JobDetail'
import NotFoundPage from '@/pages/NotFoundPage'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<MainLayout />}>
            <Route index element={<HomePage />} />
            <Route path="jobs" element={<JobsBrowse />} />
            <Route path="jobs/:id" element={<JobDetail />} />
          </Route>

          {/* Auth Routes */}
          <Route element={<AuthLayout />}>
            <Route path="login" element={<LoginPage />} />
            <Route path="register" element={<RegisterPage />} />
            <Route path="forgot-password" element={<ForgotPasswordPage />} />
          </Route>

          {/* Employee Routes */}
          <Route
            path="/employee/*"
            element={
              <ProtectedRoute requiredRole="employee">
                <Routes>
                  <Route element={<MainLayout />}>
                    <Route path="dashboard" element={<EmployeeDashboard />} />
                    <Route path="profile" element={<EmployeeProfile />} />
                    <Route path="jobs/recommended" element={<EmployeeJobsRecommended />} />
                    <Route path="applications" element={<EmployeeApplications />} />
                    <Route path="messages" element={<EmployeeMessages />} />
                    <Route path="settings" element={<EmployeeSettings />} />
                  </Route>
                </Routes>
              </ProtectedRoute>
            }
          />

          {/* Employer Routes */}
          <Route
            path="/employer/*"
            element={
              <ProtectedRoute requiredRole="employer">
                <Routes>
                  <Route element={<MainLayout />}>
                    <Route path="dashboard" element={<EmployerDashboard />} />
                    <Route path="profile" element={<EmployerProfile />} />
                    <Route path="jobs" element={<EmployerJobs />} />
                    <Route path="jobs/create" element={<EmployerJobCreate />} />
                    <Route path="applications" element={<EmployerApplications />} />
                    <Route path="messages" element={<EmployerMessages />} />
                    <Route path="settings" element={<EmployerSettings />} />
                  </Route>
                </Routes>
              </ProtectedRoute>
            }
          />

          {/* Superuser Routes */}
          <Route
            path="/admin/*"
            element={
              <ProtectedRoute requiredRole="superuser">
                <Routes>
                  <Route element={<MainLayout />}>
                    <Route path="dashboard" element={<SuperuserDashboard />} />
                    <Route path="users" element={<SuperuserUsers />} />
                    <Route path="feedback" element={<SuperuserFeedback />} />
                    <Route path="issues" element={<SuperuserIssues />} />
                  </Route>
                </Routes>
              </ProtectedRoute>
            }
          />

          {/* Not Found */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </BrowserRouter>

      <Toaster position="top-right" />
    </AuthProvider>
  )
}

export default App
