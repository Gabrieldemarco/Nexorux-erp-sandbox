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
}

const cards: StatCard[] = [
  { key: 'tenants', label: 'Total empresas', letter: 'T', color: 'bg-blue-500' },
  { key: 'companies', label: 'Razones sociales', letter: 'C', color: 'bg-green-500' },
  { key: 'products', label: 'Productos', letter: 'P', color: 'bg-purple-500' },
  { key: 'customers', label: 'Clientes', letter: 'U', color: 'bg-yellow-500' },
  { key: 'invoices', label: 'Facturas', letter: 'I', color: 'bg-red-500' },
  { key: 'fiscalDocuments', label: 'Documentos fiscales', letter: 'F', color: 'bg-indigo-500' },
  { key: 'payments', label: 'Pagos', letter: '$', color: 'bg-teal-500' },
]

const quickLinks = [
  { to: '/invoices', label: 'Facturas' },
  { to: '/payments', label: 'Pagos' },
  { to: '/purchase-receipts', label: 'Entradas proveedor' },
  { to: '/stock-movements', label: 'Stock' },
  { to: '/fiscal-documents', label: 'Documentos fiscales' },
  { to: '/reports', label: 'Reportes' },
  { to: '/certificates', label: 'Certificados' },
  { to: '/branches', label: 'Sucursales' },
  { to: '/products', label: 'Productos' },
  { to: '/roles', label: 'Roles' },
  { to: '/price-lists', label: 'Listas de precios' },
  { to: '/tax-configurations', label: 'Impuestos' },
  { to: '/audit-logs', label: 'Auditoría' },
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
        <div className="text-lg text-gray-600">Cargando panel...</div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Panel</h2>
        <span className="text-sm text-gray-600">Bienvenido, {user?.full_name || 'Usuario'}</span>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-md">
          <p className="text-sm text-amber-800">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {cards.map((card) => (
          <div key={card.key} className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className={`w-8 h-8 ${card.color} rounded-full flex items-center justify-center`}>
                    <span className="text-white font-bold">{card.letter}</span>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">{card.label}</dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {failedKeys.has(card.key) ? '—' : stats[card.key]}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-2">Bienvenido a NEXORUX ERP</h3>
        <p className="text-gray-600 mb-4">
          ERP multicompañía con facturación electrónica para Uruguay. Este panel muestra
          estadísticas en tiempo real de tu cuenta.
        </p>
        <div className="flex flex-wrap gap-3 text-sm">
          {quickLinks.map((link) => (
            <Link key={link.to} to={link.to} className="text-blue-600 hover:text-blue-800">
              {link.label}
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Dashboard
