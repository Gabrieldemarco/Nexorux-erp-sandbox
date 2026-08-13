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

const initialsOf = (name?: string | null) => {
  const parts = (name || 'Usuario').trim().split(/\s+/).filter(Boolean)
  const letters = (parts[0]?.[0] || 'U') + (parts[1]?.[0] || '')
  return letters.toUpperCase()
}

const Layout = ({ children }: { children: React.ReactNode }) => {
  const location = useLocation()
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [showTenantsProbe, setShowTenantsProbe] = useState(true)
  const [mobileOpen, setMobileOpen] = useState(false)

  const codesLoaded = Boolean(user?.permission_codes && user.permission_codes.length > 0)
  const isPos = location.pathname === '/pos'

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
          { path: '/current-accounts', label: 'Cuenta corriente', permission: 'payments.read' },
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
            anyOf: ['stock_movements.read', 'stock_movements.create', 'suppliers.read'],
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
      <div className="border-b border-slate-100 px-4 py-4">
        <Link to="/" className="block" title="Inicio">
          <BrandLogo size="sm" className="max-h-10" />
        </Link>
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-3">
        {visibleGroups.map((group) => (
          <div key={group.id} className="mb-4">
            {group.label && (
              <div className="px-3 mb-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
                {group.label}
              </div>
            )}
            <ul className="space-y-0.5">
              {group.items.map((item) => (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`block rounded-lg px-3 py-2 text-sm transition-colors ${
                      isActive(item.path)
                        ? 'bg-teal-50 font-medium text-teal-800'
                        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
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

      <div className="border-t border-slate-100 px-3 py-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-teal-800 text-[11px] font-semibold text-white">
            {initialsOf(user?.full_name)}
          </div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-medium text-slate-800">{user?.full_name || 'Usuario'}</div>
            <div className="flex items-center gap-2 text-xs">
              <Link to="/profile" className="text-teal-800 hover:text-teal-950">
                Perfil
              </Link>
              <span className="text-slate-300">·</span>
              <button type="button" onClick={handleLogout} className="text-red-600 hover:text-red-800">
                Salir
              </button>
            </div>
          </div>
        </div>
      </div>
    </nav>
  )

  return (
    <div className="min-h-screen bg-slate-50 lg:flex">
      <aside className="hidden lg:flex lg:w-60 lg:flex-shrink-0 lg:flex-col border-r border-slate-200 bg-white">
        {sidebar}
      </aside>

      <div className="lg:hidden sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="flex h-14 items-center justify-between px-4">
          <Link to="/" className="flex items-center" title="Inicio">
            <BrandLogo size="sm" className="max-h-9" />
          </Link>
          <button
            type="button"
            className="rounded-lg px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-100"
            onClick={() => setMobileOpen((v) => !v)}
            aria-expanded={mobileOpen}
          >
            Menú
          </button>
        </div>
        {mobileOpen && (
          <div className="max-h-[70vh] overflow-y-auto border-t border-slate-100 bg-white">
            {sidebar}
          </div>
        )}
      </div>

      <main className={`min-w-0 flex-1 ${isPos ? 'px-3 py-3' : 'px-4 py-6 sm:px-6 lg:px-8'}`}>
        {isPos ? children : <div className="mx-auto max-w-7xl">{children}</div>}
      </main>
    </div>
  )
}

export default Layout
