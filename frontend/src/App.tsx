import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { Toaster } from 'react-hot-toast'

// Layout components
import { Layout } from '@/components/layout/Layout'
import { Sidebar } from '@/components/layout/Sidebar'
import { Header } from '@/components/layout/Header'

// Page components
import { Dashboard } from '@/pages/Dashboard'
import { Reviews } from '@/pages/Reviews'
import { Analysis } from '@/pages/Analysis'
import { Reports } from '@/pages/Reports'
import { Settings } from '@/pages/Settings'
import { Login } from '@/pages/Auth/Login'
import { Register } from '@/pages/Auth/Register'

// Context providers
import { AuthProvider } from '@/contexts/AuthContext'
import { ThemeProvider } from '@/contexts/ThemeContext'

// Hooks
import { useAuth } from '@/hooks/useAuth'

// Styles
import '@/styles/globals.css'
import 'react-toastify/dist/ReactToastify.css'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

// Protected route component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

// Public route component (redirect if authenticated)
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return !isAuthenticated ? <>{children}</> : <Navigate to="/dashboard" replace />
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <Router>
            <div className="App">
              <Routes>
                {/* Public routes */}
                <Route
                  path="/login"
                  element={
                    <PublicRoute>
                      <Login />
                    </PublicRoute>
                  }
                />
                <Route
                  path="/register"
                  element={
                    <PublicRoute>
                      <Register />
                    </PublicRoute>
                  }
                />

                {/* Protected routes */}
                <Route
                  path="/*"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <Sidebar />
                        <div className="flex-1 flex flex-col overflow-hidden">
                          <Header />
                          <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50 dark:bg-gray-900">
                            <Routes>
                              <Route path="/dashboard" element={<Dashboard />} />
                              <Route path="/reviews" element={<Reviews />} />
                              <Route path="/analysis" element={<Analysis />} />
                              <Route path="/reports" element={<Reports />} />
                              <Route path="/settings" element={<Settings />} />
                              <Route path="/" element={<Navigate to="/dashboard" replace />} />
                            </Routes>
                          </main>
                        </div>
                      </Layout>
                    </ProtectedRoute>
                  }
                />
              </Routes>
            </div>
            
            {/* Global components */}
            <Toaster
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#363636',
                  color: '#fff',
                },
              }}
            />
            
            {/* Dev tools */}
            {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
          </Router>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default App
