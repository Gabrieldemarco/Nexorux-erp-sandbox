import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { getErrorMessage } from '../utils/errors'
import { useCatalog } from '../hooks/useCatalog'
import {
  currentAccountsApi,
  CurrentAccountBalance,
  CurrentAccountStatement,
} from '../services/currentAccounts'
import {
  invoiceStatusLabel,
  paymentStatusLabel,
  documentTypeLabelFromCatalog,
} from '../services/catalog'

const money = (value: number, currency = 'UYU') =>
  new Intl.NumberFormat('es-UY', { style: 'currency', currency }).format(value)

const accountState = (row: CurrentAccountBalance) => {
  if (row.credit_limit > 0 && row.balance > row.credit_limit) {
    return { label: 'Sobre límite', className: 'bg-red-100 text-red-800' }
  }
  if (row.overdue > 0) {
    return { label: 'Vencido', className: 'bg-orange-100 text-orange-800' }
  }
  if (row.balance > 0) {
    return { label: 'Con saldo', className: 'bg-amber-100 text-amber-800' }
  }
  if (row.balance < 0) {
    return { label: 'A favor', className: 'bg-sky-100 text-sky-800' }
  }
  return { label: 'Al día', className: 'bg-emerald-100 text-emerald-800' }
}

const CurrentAccounts = () => {
  const { catalog, currency } = useCatalog()
  const [searchParams, setSearchParams] = useSearchParams()
  const [rows, setRows] = useState<CurrentAccountBalance[]>([])
  const [statement, setStatement] = useState<CurrentAccountStatement | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [onlyOpen, setOnlyOpen] = useState(false)

  const selectedId = searchParams.get('customer') || ''

  const loadList = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await currentAccountsApi.list()
      setRows(data)
    } catch (err) {
      setError(getErrorMessage(err, 'No se pudieron cargar las cuentas corrientes'))
      setRows([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadList()
  }, [])

  useEffect(() => {
    if (!selectedId) {
      setStatement(null)
      return
    }
    let cancelled = false
    setDetailLoading(true)
    currentAccountsApi
      .get(selectedId)
      .then((data) => {
        if (!cancelled) setStatement(data)
      })
      .catch((err) => {
        if (!cancelled) {
          setError(getErrorMessage(err, 'No se pudo cargar el detalle'))
          setStatement(null)
        }
      })
      .finally(() => {
        if (!cancelled) setDetailLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [selectedId])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return rows.filter((row) => {
      if (onlyOpen && row.balance <= 0) return false
      if (!q) return true
      return (
        row.legal_name.toLowerCase().includes(q) ||
        (row.trade_name || '').toLowerCase().includes(q) ||
        row.rut.toLowerCase().includes(q)
      )
    })
  }, [rows, query, onlyOpen])

  const totals = useMemo(() => {
    return filtered.reduce(
      (acc, row) => ({
        invoiced: acc.invoiced + row.invoiced,
        paid: acc.paid + row.paid,
        balance: acc.balance + row.balance,
        overdue: acc.overdue + row.overdue,
      }),
      { invoiced: 0, paid: 0, balance: 0, overdue: 0 }
    )
  }, [filtered])

  const selectCustomer = (id: string) => {
    setSearchParams(id ? { customer: id } : {})
  }

  const paymentHref = (customerId: string, invoiceId?: string) => {
    const params = new URLSearchParams({ customer_id: customerId })
    if (invoiceId) params.set('invoice_id', invoiceId)
    return `/payments?${params.toString()}`
  }

  const invLabel = (code?: string | null) => invoiceStatusLabel(catalog, code)
  const payLabel = (code?: string | null) => paymentStatusLabel(catalog, code)
  const typeLabel = (code: string) => documentTypeLabelFromCatalog(catalog, code)

  return (
    <div>
      <div className="flex flex-wrap justify-between items-start gap-4 mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Cuenta corriente</h2>
          <p className="text-sm text-gray-600 mt-1">
            Saldo por cliente = facturas emitidas − cobros registrados. Las notas de crédito restan.
          </p>
        </div>
        {selectedId && (
          <Link
            to={paymentHref(selectedId)}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            Registrar cobro
          </Link>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <div className="bg-white shadow rounded-lg p-4">
          <div className="text-xs uppercase text-gray-500">Facturado</div>
          <div className="text-lg font-semibold text-gray-900">{money(totals.invoiced, currency)}</div>
        </div>
        <div className="bg-white shadow rounded-lg p-4">
          <div className="text-xs uppercase text-gray-500">Cobrado</div>
          <div className="text-lg font-semibold text-gray-900">{money(totals.paid, currency)}</div>
        </div>
        <div className="bg-white shadow rounded-lg p-4">
          <div className="text-xs uppercase text-gray-500">Saldo</div>
          <div className={`text-lg font-semibold ${totals.balance > 0 ? 'text-amber-700' : 'text-emerald-700'}`}>
            {money(totals.balance, currency)}
          </div>
        </div>
        <div className="bg-white shadow rounded-lg p-4">
          <div className="text-xs uppercase text-gray-500">Vencido</div>
          <div className={`text-lg font-semibold ${totals.overdue > 0 ? 'text-red-700' : 'text-gray-900'}`}>
            {money(totals.overdue, currency)}
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-3 mb-4">
        <input
          className="border border-gray-300 rounded-md px-3 py-2 text-sm w-full md:w-72"
          placeholder="Buscar cliente, RUT…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input type="checkbox" checked={onlyOpen} onChange={(e) => setOnlyOpen(e.target.checked)} />
          Solo con saldo
        </label>
      </div>

      {error && <div className="mb-4 rounded-md bg-red-50 p-3 text-red-700 text-sm">{error}</div>}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="bg-white shadow rounded-lg overflow-hidden">
          {loading && <div className="p-4 text-gray-500">Cargando...</div>}
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cliente</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Saldo</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {!loading && filtered.length === 0 ? (
                <tr>
                  <td colSpan={3} className="px-4 py-4 text-center text-gray-500">
                    No hay cuentas para mostrar. Cargá clientes, emití facturas y registrá cobros.
                  </td>
                </tr>
              ) : (
                filtered.map((row) => {
                  const state = accountState(row)
                  const active = row.customer_id === selectedId
                  return (
                    <tr
                      key={row.customer_id}
                      className={`cursor-pointer ${active ? 'bg-blue-50' : 'hover:bg-gray-50'}`}
                      onClick={() => selectCustomer(row.customer_id)}
                    >
                      <td className="px-4 py-3">
                        <div className="text-sm font-medium text-gray-900">{row.legal_name}</div>
                        <div className="text-xs text-gray-500">{row.rut}</div>
                      </td>
                      <td className="px-4 py-3 text-right text-sm font-medium text-gray-900">
                        {money(row.balance, row.currency)}
                        {row.credit_limit > 0 && (
                          <div className="text-xs text-gray-500 font-normal">
                            Límite {money(row.credit_limit, row.currency)}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${state.className}`}>
                          {state.label}
                        </span>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>

        <div className="bg-white shadow rounded-lg p-4 min-h-[16rem]">
          {!selectedId && (
            <p className="text-sm text-gray-500">Elegí un cliente para ver facturas pendientes y el historial de cobros.</p>
          )}
          {detailLoading && <p className="text-sm text-gray-500">Cargando detalle...</p>}
          {statement && !detailLoading && (
            <div className="space-y-5">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{statement.legal_name}</h3>
                <p className="text-sm text-gray-500">
                  {statement.rut}
                  {statement.credit_limit > 0 && (
                    <>
                      {' '}
                      · Límite {money(statement.credit_limit, statement.currency)}
                      {statement.available_credit != null && (
                        <> · Disponible {money(statement.available_credit, statement.currency)}</>
                      )}
                    </>
                  )}
                </p>
                <div className="mt-2 flex flex-wrap gap-3 text-sm">
                  <span>Facturado {money(statement.invoiced, statement.currency)}</span>
                  <span>Cobrado {money(statement.paid, statement.currency)}</span>
                  <span className="font-semibold">Saldo {money(statement.balance, statement.currency)}</span>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-gray-800 mb-2">Facturas</h4>
                {statement.invoices.length === 0 ? (
                  <p className="text-sm text-gray-500">Sin documentos que afecten la cuenta.</p>
                ) : (
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="text-left text-xs uppercase text-gray-500">
                        <th className="py-1 pr-2">Documento</th>
                        <th className="py-1 pr-2">Estado</th>
                        <th className="py-1 pr-2 text-right">Saldo</th>
                        <th className="py-1"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {statement.invoices.map((inv) => (
                        <tr key={inv.invoice_id} className="border-t border-gray-100">
                          <td className="py-2 pr-2">
                            <div className="font-medium text-gray-900">
                              {inv.series}-{inv.number}
                            </div>
                            <div className="text-xs text-gray-500">{typeLabel(inv.document_type)}</div>
                          </td>
                          <td className="py-2 pr-2 text-gray-600">
                            {invLabel(inv.status)}
                            {inv.overdue && <span className="ml-1 text-xs text-red-600">vencida</span>}
                          </td>
                          <td className="py-2 pr-2 text-right font-medium">
                            {money(inv.balance, inv.currency)}
                          </td>
                          <td className="py-2 text-right">
                            {inv.balance > 0 && (
                              <Link
                                className="text-blue-600 hover:text-blue-800 text-xs"
                                to={paymentHref(statement.customer_id, inv.invoice_id)}
                              >
                                Cobrar
                              </Link>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              <div>
                <h4 className="text-sm font-semibold text-gray-800 mb-2">Cobros</h4>
                {statement.payments.length === 0 ? (
                  <p className="text-sm text-gray-500">Todavía no hay registros de pago.</p>
                ) : (
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="text-left text-xs uppercase text-gray-500">
                        <th className="py-1 pr-2">Fecha</th>
                        <th className="py-1 pr-2">Método</th>
                        <th className="py-1 pr-2">Estado</th>
                        <th className="py-1 text-right">Monto</th>
                      </tr>
                    </thead>
                    <tbody>
                      {statement.payments.map((pay) => (
                        <tr key={pay.payment_id} className="border-t border-gray-100">
                          <td className="py-2 pr-2 text-gray-600">{pay.payment_date.slice(0, 10)}</td>
                          <td className="py-2 pr-2 text-gray-600">
                            {catalog?.payment_methods.find((m) => m.value === pay.payment_method)?.label ||
                              pay.payment_method}
                            {pay.reference ? ` · ${pay.reference}` : ''}
                          </td>
                          <td className="py-2 pr-2 text-gray-600">{payLabel(pay.status)}</td>
                          <td className="py-2 text-right font-medium">{money(pay.amount, pay.currency)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default CurrentAccounts
