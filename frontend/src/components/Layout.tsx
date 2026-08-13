import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { canAccessTenantsNav, resetAccessCache } from '../utils/access'
import { hasAnyPermission, hasPermission } from '../utils/permissions'
import BrandLogo from './BrandLogo'

type NavItem = {
  path: string
  label: string
  permission?: string
  always?: boolean
  anyOf?: string[]
}

type NavGroup = {
  id: string
  label?: string
  items: NavItem[]
}

const Layout = ({ children }: { children: React.ReactNode }) => {
  const location = useLocation()
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [showTenantsProbe, setShowTenantsProbe] = useState(true)
  const [mobileOpen, setMobileOpen] = useState(false)

  const codesLoaded = Boolean(user?.permission_codes && user.permission_codes.length > 0)

  useEffect(() => {
    if (codesLoaded) return
    let cancelled = false
    canAccessTenantsNav().then((ok) => {
      if (!cancelled) setShowTenantsProbe(ok)
    })
    return () => {
      cancelled = true
    }
  }, [codesLoaded])

  useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  const isActive = (path: string) => location.pathname === path

  const canSee = (item: NavItem): boolean => {
    if (item.always) return true
    if (item.path === '/tenants') {
      if (codesLoaded) return hasPermission(user, 'tenants.read')
      return showTenantsProbe
    }
    if (!codesLoaded) return true
    if (item.anyOf?.length) return hasAnyPermission(user, ...item.anyOf)
    if (!item.permission) return true
    return hasPermission(user, item.permission)
  }

  const navGroups: NavGroup[] = useMemo(
    () => [
      {
        id: 'main',
        items: [
          { path: '/', label: 'Panel', always: true },
          { path: '/reports', label: 'Reportes', permission: 'invoices.read' },
        ],
      },
      {
        id: 'ventas',
        label: 'Ventas',
        items: [
          { path: '/pos', label: 'Caja rápida', anyOf: ['invoices.create', 'invoices.read'] },
          { path: '/invoices', label: 'Facturas', permission: 'invoices.read' },
          { path: '/payments', label: 'Pagos', permission: 'payments.read' },
          { path: '/fiscal-documents', label: 'Docs. fiscales', permission: 'fiscal_documents.read' },
          { path: '/customers', label: 'Clientes', permission: 'customers.read' },
          { path: '/woocommerce', label: 'WooCommerce', anyOf: ['invoices.read', 'products.read'] },
        ],
      },
      {
        id: 'inventario',
        label: 'Inventario',
        items: [
          { path: '/products', label: 'Productos', permission: 'products.read' },
          { path: '/suppliers', label: 'Proveedores', permission: 'suppliers.read' },
          {
            path: '/purchase-receipts',
            label: 'Entradas proveedor',
            anyOf: ['stock_movements.read', 'suppliers.read'],
          },
          { path: '/stock-movements', label: 'Stock', permission: 'stock_movements.read' },
          { path: '/warehouses', label: 'Depósitos', permission: 'warehouses.read' },
          { path: '/branches', label: 'Sucursales', permission: 'branches.read' },
          { path: '/price-lists', label: 'Listas de precios', permission: 'price_lists.read' },
        ],
      },
      {
        id: 'fiscal',
        label: 'Fiscal',
        items: [
          { path: '/certificates', label: 'Certificados', permission: 'certificates.read' },
          { path: '/tax-configurations', label: 'Impuestos', permission: 'tax_configurations.read' },
        ],
      },
      {
        id: 'admin',
        label: 'Administración',
        items: [
          { path: '/tenants', label: 'Tenants', permission: 'tenants.read' },
          { path: '/companies', label: 'Razones sociales', permission: 'companies.read' },
          { path: '/roles', label: 'Roles', permission: 'roles.read' },
          { path: '/audit-logs', label: 'Auditoría', permission: 'audit_logs.read' },
        ],
      },
    ],
    []
  )

  const visibleGroups = navGroups
    .map((group) => ({
      ...group,
      items: group.items.filter(canSee),
    }))
    .filter((group) => group.items.length > 0)

  const handleLogout = () => {
    resetAccessCache()
    logout()
    navigate('/login')
  }

  const sidebar = (
    <nav className="flex h-full flex-col">
      <div className="px-4 py-4">
        <Link to="/" className="block" title="Inicio">
          <BrandLogo size="sm" className="max-h-10" />
        </Link>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-4">
        {visibleGroups.map((group) => (
          <div key={group.id} className="mb-4">
            {group.label && (
              <div className="px-3 mb-1 text-[11px] font-semibold uppercase tracking-wide text-gray-400">
                {group.label}
              </div>
            )}
            <ul className="space-y-0.5">
              {group.items.map((item) => (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`block rounded-md px-3 py-2 text-sm ${
                      isActive(item.path)
                        ? 'bg-blue-50 font-medium text-blue-700'
                        : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="border-t border-gray-200 px-4 py-3 space-y-1">
        <div className="text-xs text-gray-500 truncate">{user?.full_name || 'Usuario'}</div>
        <div className="flex items-center gap-3 text-sm">
          <Link to="/profile" className="text-blue-600 hover:text-blue-800">
            Perfil
          </Link>
          <button type="button" onClick={handleLogout} className="text-red-600 hover:text-red-800">
            Salir
          </button>
        </div>
      </div>
    </nav>
  )

  return (
    <div className="min-h-screen bg-gray-50 lg:flex">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex lg:w-56 lg:flex-shrink-0 lg:flex-col border-r border-gray-200 bg-white">
        {sidebar}
      </aside>

      {/* Mobile top bar */}
      <div className="lg:hidden sticky top-0 z-30 border-b border-gray-200 bg-white">
        <div className="flex h-14 items-center justify-between px-4">
          <Link to="/" className="flex items-center" title="Inicio">
            <BrandLogo size="sm" className="max-h-9" />
          </Link>
          <button
            type="button"
            className="rounded-md px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100"
            onClick={() => setMobileOpen((v) => !v)}
            aria-expanded={mobileOpen}
          >
            Menú
          </button>
        </div>
        {mobileOpen && (
          <div className="max-h-[70vh] overflow-y-auto border-t border-gray-100 bg-white">
            {sidebar}
          </div>
        )}
      </div>

      <main className="min-w-0 flex-1 py-6 px-4 sm:px-6 lg:px-8">{children}</main>
    </div>
  )
}

export default Layout
