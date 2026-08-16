import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './hooks/useAuth'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import GuestRoute from './components/GuestRoute'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Register from './pages/Register'
import Profile from './pages/Profile'
import RecoverPassword from './pages/RecoverPassword'
import Tenants from './pages/Tenants'
import Companies from './pages/Companies'
import Products from './pages/Products'
import Customers from './pages/Customers'
import Suppliers from './pages/Suppliers'
import Invoices from './pages/Invoices'
import FiscalDocuments from './pages/FiscalDocuments'
import Branches from './pages/Branches'
import Warehouses from './pages/Warehouses'
import StockMovements from './pages/StockMovements'
import PurchaseReceipts from './pages/PurchaseReceipts'
import Payments from './pages/Payments'
import CurrentAccounts from './pages/CurrentAccounts'
import Certificates from './pages/Certificates'
import Reports from './pages/Reports'
import Roles from './pages/Roles'
import PriceLists from './pages/PriceLists'
import TaxConfigurations from './pages/TaxConfigurations'
import AuditLogs from './pages/AuditLogs'
import WooCommerce from './pages/WooCommerce'
import Pos from './pages/Pos'
import FiscalEngine from './pages/FiscalEngine'

function App() {
  return (
    <AuthProvider>
      <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          <Route path="/login" element={<GuestRoute><Login /></GuestRoute>} />
          <Route path="/register" element={<GuestRoute><Register /></GuestRoute>} />
          <Route path="/recover-password" element={<GuestRoute><RecoverPassword /></GuestRoute>} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout>
                  <Dashboard />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <Layout>
                  <Profile />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/tenants"
            element={
              <ProtectedRoute>
                <Layout>
                  <Tenants />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/companies"
            element={
              <ProtectedRoute>
                <Layout>
                  <Companies />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/products"
            element={
              <ProtectedRoute>
                <Layout>
                  <Products />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/customers"
            element={
              <ProtectedRoute>
                <Layout>
                  <Customers />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/suppliers"
            element={
              <ProtectedRoute>
                <Layout>
                  <Suppliers />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/branches"
            element={
              <ProtectedRoute>
                <Layout>
                  <Branches />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/warehouses"
            element={
              <ProtectedRoute>
                <Layout>
                  <Warehouses />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/purchase-receipts"
            element={
              <ProtectedRoute>
                <Layout>
                  <PurchaseReceipts />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/stock-movements"
            element={
              <ProtectedRoute>
                <Layout>
                  <StockMovements />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/pos"
            element={
              <ProtectedRoute>
                <Layout>
                  <Pos />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/invoices"
            element={
              <ProtectedRoute>
                <Layout>
                  <Invoices />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/payments"
            element={
              <ProtectedRoute>
                <Layout>
                  <Payments />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/current-accounts"
            element={
              <ProtectedRoute>
                <Layout>
                  <CurrentAccounts />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/fiscal-documents"
            element={
              <ProtectedRoute>
                <Layout>
                  <FiscalDocuments />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/certificates"
            element={
              <ProtectedRoute>
                <Layout>
                  <Certificates />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/fiscal-engine"
            element={
              <ProtectedRoute>
                <Layout>
                  <FiscalEngine />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/reports"
            element={
              <ProtectedRoute>
                <Layout>
                  <Reports />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/roles"
            element={
              <ProtectedRoute>
                <Layout>
                  <Roles />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/price-lists"
            element={
              <ProtectedRoute>
                <Layout>
                  <PriceLists />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/tax-configurations"
            element={
              <ProtectedRoute>
                <Layout>
                  <TaxConfigurations />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/audit-logs"
            element={
              <ProtectedRoute>
                <Layout>
                  <AuditLogs />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/woocommerce"
            element={
              <ProtectedRoute>
                <Layout>
                  <WooCommerce />
                </Layout>
              </ProtectedRoute>
            }
          />
        </Routes>
      </Router>
    </AuthProvider>
  )
}

export default App
