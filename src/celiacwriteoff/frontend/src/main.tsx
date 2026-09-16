import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './index.css'
import Home from './home.tsx'
import AddItems from './pages/AddItems.tsx'
import ReviewItems from './pages/ReviewItems.tsx'
import TaxInformation from './pages/TaxInformation.tsx'
import Login from './pages/Login.tsx'
import Signup from './pages/Signup.tsx'
import ForgotPassword from './pages/ForgotPassword.tsx'
import ResetPassword from './pages/ResetPassword.tsx'
import AdminLoginActivity from './pages/AdminLoginActivity.tsx'
import RequireAuth from './components/RequireAuth.tsx'
import RequireAdmin from './components/RequireAdmin.tsx'
import { AuthProvider } from './context/AuthContext.tsx'
import { ItemsProvider } from './context/ItemsContext.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route element={<RequireAuth />}>
            <Route
              path="/"
              element={
                <ItemsProvider>
                  <Home />
                </ItemsProvider>
              }
            >
              <Route index element={<Navigate to="/add-items" replace />} />
              <Route path="add-items" element={<AddItems />} />
              <Route path="review-items" element={<ReviewItems />} />
              <Route path="tax-information" element={<TaxInformation />} />
              <Route element={<RequireAdmin />}>
                <Route path="admin/login-activity" element={<AdminLoginActivity />} />
              </Route>
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  </StrictMode>,
)
