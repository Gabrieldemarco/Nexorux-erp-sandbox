import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { tenantsApi } from '../services/tenants'
import { companiesApi } from '../services/companies'
import { productsApi } from '../services/products'
import { customersApi } from '../services/customers'
import { invoicesApi } from '../services/invoices'
import { fiscalDocumentsApi } from '../services/fiscalDocuments'
import { paymentsApi } from '../services/payments'
import { useAuth } from '../hooks/useAuth'
import { getErrorMessage } from '../utils/errors'

interface Stats {
  tenants: number
  companies: number
  products: number
  customers: number
  invoices: number
  fiscalDocuments: number
  payments: number
}

interface StatCard {
  key: keyof Stats
  label: string
  letter: string
  color: string
  to: string
}

const cards: StatCard[] = [
  { key: 'tenants', label: 'Total empresas', letter: 'T', color: 'bg-sky-600', to: '/tenants' },
  { key: 'companies', label: 'Razones sociales', letter: 'C', color: 'bg-emerald-600', to: '/companies' },
  { key: 'products', label: 'Productos', letter: 'P', color: 'bg-violet-600', to: '/products' },
  { key: 'customers', label: 'Clientes', letter: 'U', color: 'bg-amber-500', to: '/customers' },
  { key: 'invoices', label: 'Facturas', letter: 'I', color: 'bg-rose-600', to: '/invoices' },
  { key: 'fiscalDocuments', label: 'Documentos fiscales', letter: 'F', color: 'bg-indigo-600', to: '/fiscal-documents' },
  { key: 'payments', label: 'Pagos', letter: '$', color: 'bg-teal-600', to: '/payments' },
]

const quickGroups = [
  {
    title: 'Ventas',
    links: [
      { to: '/pos', label: 'Caja rápida' },
      { to: '/invoices', label: 'Facturas' },
      { to: '/payments', label: 'Pagos' },
      { to: '/current-accounts', label: 'Cuenta corriente' },
      { to: '/customers', label: 'Clientes' },
      { to: '/fiscal-documents', label: 'Documentos fiscales' },
    ],
  },
  {
    title: 'Inventario',
    links: [
      { to: '/products', label: 'Productos' },
      { to: '/purchase-receipts', label: 'Entradas proveedor' },
      { to: '/stock-movements', label: 'Stock' },
      { to: '/warehouses', label: 'Depósitos' },
    ],
  },
  {
    title: 'Administración',
    links: [
      { to: '/reports', label: 'Reportes' },
      { to: '/certificates', label: 'Certificados' },
      { to: '/tax-configurations', label: 'Impuestos' },
      { to: '/roles', label: 'Roles' },
      { to: '/audit-logs', label: 'Auditoría' },
      { to: '/price-lists', label: 'Listas de precios' },
      { to: '/branches', label: 'Sucursales' },
    ],
  },
]

const emptyStats = (): Stats => ({
  tenants: 0,
  companies: 0,
  products: 0,
  customers: 0,
  invoices: 0,
  fiscalDocuments: 0,
  payments: 0,
})

const Dashboard = () => {
  const [stats, setStats] = useState<Stats>(emptyStats())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [failedKeys, setFailedKeys] = useState<Set<keyof Stats>>(new Set())
  const { user } = useAuth()

  useEffect(() => {
    const loadStats = async () => {
      try {
        const probes: Array<{ key: keyof Stats; run: () => Promise<unknown[]> }> = [
          { key: 'tenants', run: () => tenantsApi.list() },
          { key: 'companies', run: () => companiesApi.list() },
          { key: 'products', run: () => productsApi.list() },
          { key: 'customers', run: () => customersApi.list() },
          { key: 'invoices', run: () => invoicesApi.list() },
          { key: 'fiscalDocuments', run: () => fiscalDocumentsApi.list() },
          { key: 'payments', run: () => paymentsApi.list() },
        ]
        const results = await Promise.allSettled(probes.map((p) => p.run()))
        const next = emptyStats()
        const failed = new Set<keyof Stats>()
        results.forEach((result, idx) => {
          const key = probes[idx].key
          if (result.status === 'fulfilled') {
            next[key] = result.value.length
          } else {
            failed.add(key)
          }
        })
        setStats(next)
        setFailedKeys(failed)

        const businessKeys: Array<keyof Stats> = [
          'companies',
          'products',
          'customers',
          'invoices',
          'fiscalDocuments',
          'payments',
        ]
        const criticalFailed = businessKeys.filter((k) => failed.has(k))
        if (criticalFailed.length === businessKeys.length) {
          const firstIdx = probes.findIndex((p) => p.key === criticalFailed[0])
          const first = results[firstIdx] as PromiseRejectedResult
          setError(getErrorMessage(first.reason, 'No se pudo cargar el panel'))
        } else if (criticalFailed.length > 0) {
          setError('Algunos datos del panel no se pudieron cargar')
        } else if (failed.has('tenants')) {
          setError(null)
        } else {
          setError(null)
        }
      } catch (err: unknown) {
        console.error('Failed to load stats:', err)
        setError(getErrorMessage(err, 'No se pudo cargar el panel'))
      } finally {
        setLoading(false)
      }
    }
    loadStats()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-slate-500">Cargando panel...</div>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-900">Panel</h2>
        <p className="mt-1 text-sm text-slate-600">
          Bienvenido, {user?.full_name || 'Usuario'}. Resumen de tu operación.
        </p>
      </div>

      {error && (
        <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 p-4">
          <p className="text-sm text-amber-800">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {cards.map((card) => (
          <Link
            key={card.key}
            to={card.to}
            className="group bg-white overflow-hidden shadow rounded-lg hover:border-teal-200 focus:outline-none focus:ring-2 focus:ring-teal-600/30"
          >
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className={`w-10 h-10 ${card.color} rounded-xl flex items-center justify-center shadow-sm`}>
                    <span className="text-white font-semibold">{card.letter}</span>
                  </div>
                </div>
                <div className="ml-4 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-slate-500 truncate">{card.label}</dt>
                    <dd className="text-2xl font-semibold tracking-tight text-slate-900">
                      {failedKeys.has(card.key) ? '—' : stats[card.key]}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>

      <div className="mt-8 bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-semibold text-slate-900">Atajos</h3>
        <p className="mt-1 mb-5 text-sm text-slate-600">
          ERP multicompañía con facturación electrónica para Uruguay.
        </p>
        <div className="grid gap-5 sm:grid-cols-3">
          {quickGroups.map((group) => (
            <div key={group.title}>
              <div className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                {group.title}
              </div>
              <div className="flex flex-wrap gap-2">
                {group.links.map((link) => (
                  <Link
                    key={link.to}
                    to={link.to}
                    className="inline-flex rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-sm text-slate-700 hover:border-teal-600 hover:bg-teal-50 hover:text-teal-800"
                  >
                    {link.label}
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Dashboard
