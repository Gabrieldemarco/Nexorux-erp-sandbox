import { useEffect, useMemo, useState } from 'react'
import { invoicesApi, InvoiceResponse } from '../services/invoices'
import { fiscalDocumentsApi, FiscalDocumentResponse } from '../services/fiscalDocuments'
import { paymentsApi, PaymentResponse } from '../services/payments'
import { getErrorMessage } from '../utils/errors'
import { documentTypeLabel } from '../utils/documentTypes'
import { invoiceStatusLabel, fiscalStateLabel } from '../utils/statusLabels'
import { downloadCsv } from '../utils/csv'
import { useCatalog } from '../hooks/useCatalog'
import {
  invoiceStatusLabel as catalogInvoiceStatusLabel,
  fiscalStateLabel as catalogFiscalStateLabel,
  documentTypeLabelFromCatalog,
} from '../services/catalog'

const isToday = (iso: string) => {
  const d = new Date(iso)
  const now = new Date()
  return (
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  )
}

const Reports = () => {
  const { catalog } = useCatalog()
  const statusLabel = (code?: string | null) =>
    catalog ? catalogInvoiceStatusLabel(catalog, code) : invoiceStatusLabel(code)
  const fiscalLabel = (code?: string | null) =>
    catalog ? catalogFiscalStateLabel(catalog, code) : fiscalStateLabel(code)
  const typeLabel = (code: string) =>
    catalog ? documentTypeLabelFromCatalog(catalog, code) : documentTypeLabel(code)
  const [invoices, setInvoices] = useState<InvoiceResponse[]>([])
  const [fiscalDocs, setFiscalDocs] = useState<FiscalDocumentResponse[]>([])
  const [payments, setPayments] = useState<PaymentResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const [inv, fiscal, pay] = await Promise.all([
          invoicesApi.list(),
          fiscalDocumentsApi.list(),
          paymentsApi.list(),
        ])
        setInvoices(inv)
        setFiscalDocs(fiscal)
        setPayments(pay)
      } catch (err) {
        setError(getErrorMessage(err, 'No se pudieron cargar los reportes'))
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const todaySales = useMemo(() => {
    return invoices
      .filter((inv) => isToday(inv.issue_date) && inv.status !== 'cancelled')
      .reduce((sum, inv) => sum + Number(inv.total || 0), 0)
  }, [invoices])

  const invoicesByStatus = useMemo(() => {
    const map: Record<string, number> = {}
    for (const inv of invoices) {
      map[inv.status] = (map[inv.status] || 0) + 1
    }
    return Object.entries(map).sort((a, b) => b[1] - a[1])
  }, [invoices])

  const fiscalByState = useMemo(() => {
    const map: Record<string, number> = {}
    for (const doc of fiscalDocs) {
      map[doc.state] = (map[doc.state] || 0) + 1
    }
    return Object.entries(map).sort((a, b) => b[1] - a[1])
  }, [fiscalDocs])

  const todayPayments = useMemo(() => {
    return payments
      .filter((p) => isToday(p.payment_date))
      .reduce((sum, p) => sum + Number(p.amount || 0), 0)
  }, [payments])

  const exportInvoicesCsv = () => {
    const rows: string[][] = [
      ['id', 'series', 'number', 'document_type', 'status', 'issue_date', 'total', 'currency', 'customer_id'],
      ...invoices.map((inv) => [
        inv.id,
        inv.series,
        inv.number,
        inv.document_type,
        inv.status,
        inv.issue_date,
        String(inv.total),
        inv.currency,
        inv.customer_id || '',
      ]),
    ]
    downloadCsv('facturas.csv', rows)
  }

  const exportPaymentsCsv = () => {
    const rows: string[][] = [
      ['id', 'payment_date', 'amount', 'currency', 'payment_method', 'status', 'reference', 'invoice_id', 'customer_id'],
      ...payments.map((p) => [
        p.id,
        p.payment_date,
        String(p.amount),
        p.currency,
        p.payment_method,
        p.status || '',
        p.reference || '',
        p.invoice_id || '',
        p.customer_id || '',
      ]),
    ]
    downloadCsv('pagos.csv', rows)
  }

  const exportFiscalCsv = () => {
    const rows: string[][] = [
      ['id', 'document_type', 'series', 'number', 'state', 'invoice_id', 'issued_at', 'sent_at', 'is_contingency'],
      ...fiscalDocs.map((d) => [
        d.id,
        d.document_type,
        d.series,
        d.number,
        d.state,
        d.invoice_id,
        d.issued_at || '',
        d.sent_at || '',
        String(d.is_contingency),
      ]),
    ]
    downloadCsv('documentos_fiscales.csv', rows)
  }

  return (
    <div>
      <div className="flex flex-wrap justify-between items-center gap-3 mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Reportes</h2>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={exportInvoicesCsv}
            disabled={loading || invoices.length === 0}
            className="bg-white border border-gray-300 text-gray-700 px-3 py-2 rounded-md text-sm hover:bg-gray-50 disabled:opacity-50"
          >
            Exportar facturas CSV
          </button>
          <button
            type="button"
            onClick={exportPaymentsCsv}
            disabled={loading || payments.length === 0}
            className="bg-white border border-gray-300 text-gray-700 px-3 py-2 rounded-md text-sm hover:bg-gray-50 disabled:opacity-50"
          >
            Exportar pagos CSV
          </button>
          <button
            type="button"
            onClick={exportFiscalCsv}
            disabled={loading || fiscalDocs.length === 0}
            className="bg-white border border-gray-300 text-gray-700 px-3 py-2 rounded-md text-sm hover:bg-gray-50 disabled:opacity-50"
          >
            Exportar documentos fiscales CSV
          </button>
        </div>
      </div>

      {loading && <div className="text-gray-500 mb-4">Cargando...</div>}
      {error && <div className="mb-4 rounded-md bg-red-50 p-3 text-red-700 text-sm">{error}</div>}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-white shadow rounded-lg p-4">
          <div className="text-sm text-gray-500">Ventas de hoy</div>
          <div className="text-2xl font-semibold text-gray-900">${todaySales.toFixed(2)}</div>
        </div>
        <div className="bg-white shadow rounded-lg p-4">
          <div className="text-sm text-gray-500">Pagos de hoy</div>
          <div className="text-2xl font-semibold text-gray-900">${todayPayments.toFixed(2)}</div>
        </div>
        <div className="bg-white shadow rounded-lg p-4">
          <div className="text-sm text-gray-500">Facturas totales</div>
          <div className="text-2xl font-semibold text-gray-900">{invoices.length}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-200 font-medium text-gray-900">Facturas por estado</div>
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Cantidad</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {invoicesByStatus.length === 0 ? (
                <tr>
                  <td colSpan={2} className="px-4 py-3 text-sm text-gray-500 text-center">
                    Sin datos
                  </td>
                </tr>
              ) : (
                invoicesByStatus.map(([status, count]) => (
                  <tr key={status}>
                    <td className="px-4 py-2 text-sm text-gray-900">{statusLabel(status)}</td>
                    <td className="px-4 py-2 text-sm text-gray-500 text-right">{count}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-200 font-medium text-gray-900">Documentos fiscales por estado</div>
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Cantidad</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {fiscalByState.length === 0 ? (
                <tr>
                  <td colSpan={2} className="px-4 py-3 text-sm text-gray-500 text-center">
                    Sin datos
                  </td>
                </tr>
              ) : (
                fiscalByState.map(([state, count]) => (
                  <tr key={state}>
                    <td className="px-4 py-2 text-sm text-gray-900">{fiscalLabel(state)}</td>
                    <td className="px-4 py-2 text-sm text-gray-500 text-right">{count}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-200 font-medium text-gray-900">Últimas facturas</div>
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Número</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
              <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Total</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {invoices.slice(0, 15).map((inv) => (
              <tr key={inv.id}>
                <td className="px-4 py-2 text-sm text-gray-900">
                  {inv.series}-{inv.number}
                </td>
                <td className="px-4 py-2 text-sm text-gray-500">{typeLabel(inv.document_type)}</td>
                <td className="px-4 py-2 text-sm text-gray-500">{statusLabel(inv.status)}</td>
                <td className="px-4 py-2 text-sm text-gray-500 text-right">
                  {inv.total} {inv.currency}
                </td>
              </tr>
            ))}
            {invoices.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-3 text-sm text-gray-500 text-center">
                  Sin facturas
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default Reports
