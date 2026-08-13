import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useEntityCrud } from '../hooks/useEntityCrud'
import Modal from '../components/Modal'
import FormField, { inputClass } from '../components/FormField'
import { paymentsApi, PaymentCreate, PaymentResponse, PaymentUpdate } from '../services/payments'
import { invoicesApi, InvoiceResponse } from '../services/invoices'
import { customersApi, CustomerResponse } from '../services/customers'
import { invoiceStatusLabel } from '../utils/statusLabels'
import { useCatalog } from '../hooks/useCatalog'
import { paymentStatusLabel } from '../services/catalog'

const todayIso = () => new Date().toISOString()

const defaultForm = {
  invoice_id: '',
  customer_id: '',
  payment_method: 'cash',
  amount: 0,
  currency: '',
  payment_date: todayIso().slice(0, 16),
  reference: '',
  status: 'completed',
}

const Payments = () => {
  const { user } = useAuth()
  const [searchParams] = useSearchParams()
  const prefillCustomer = searchParams.get('customer_id') || ''
  const prefillInvoice = searchParams.get('invoice_id') || ''
  const { catalog, currency: companyCurrency } = useCatalog()
  const paymentMethods = catalog?.payment_methods?.length
    ? catalog.payment_methods
    : [
        { value: 'cash', label: 'Efectivo' },
        { value: 'transfer', label: 'Transferencia' },
        { value: 'card', label: 'Tarjeta' },
        { value: 'check', label: 'Cheque' },
        { value: 'other', label: 'Otro' },
      ]
  const paymentMethodLabel = (code?: string | null) =>
    paymentMethods.find((m) => m.value === code)?.label || code || '—'
  const invStatusLabel = (code?: string | null) =>
    catalog?.invoice_statuses.find((s) => s.value === code)?.label || invoiceStatusLabel(code)
  const payStatusLabel = (code?: string | null) => paymentStatusLabel(catalog, code)
  const paymentStatuses = catalog?.payment_statuses?.length
    ? catalog.payment_statuses
    : [
        { value: 'pending', label: 'Pendiente' },
        { value: 'completed', label: 'Completado' },
        { value: 'failed', label: 'Fallido' },
        { value: 'cancelled', label: 'Anulado' },
      ]
  const completedStatus =
    catalog?.payment_statuses.find((s) => s.counts_as_paid)?.value ||
    catalog?.payment_statuses.find((s) => s.value === 'completed')?.value ||
    'completed'
  const crud = useEntityCrud<PaymentResponse, PaymentCreate, PaymentUpdate>(
    paymentsApi,
    'No se pudieron cargar los pagos',
    '¿Eliminar este pago?'
  )
  const [form, setForm] = useState(defaultForm)
  const [invoices, setInvoices] = useState<InvoiceResponse[]>([])
  const [customers, setCustomers] = useState<CustomerResponse[]>([])

  useEffect(() => {
    Promise.all([invoicesApi.list(), customersApi.list()])
      .then(([inv, cust]) => {
        setInvoices(inv)
        setCustomers(cust)
      })
      .catch(() => {
        setInvoices([])
        setCustomers([])
      })
  }, [])

  useEffect(() => {
    if (!crud.modalOpen) return
    if (crud.editing) {
      setForm({
        invoice_id: crud.editing.invoice_id || '',
        customer_id: crud.editing.customer_id || '',
        payment_method: crud.editing.payment_method,
        amount: Number(crud.editing.amount),
        currency: crud.editing.currency,
        payment_date: crud.editing.payment_date.slice(0, 16),
        reference: crud.editing.reference || '',
        status: crud.editing.status || 'completed',
      })
    } else {
      const invoice = invoices.find((i) => i.id === prefillInvoice)
      setForm({
        ...defaultForm,
        invoice_id: prefillInvoice,
        customer_id: invoice?.customer_id || prefillCustomer,
        amount: invoice ? Number(invoice.total) : 0,
        currency: invoice?.currency || companyCurrency,
        payment_date: todayIso().slice(0, 16),
        status: completedStatus,
      })
    }
  }, [crud.modalOpen, crud.editing, companyCurrency, catalog, prefillCustomer, prefillInvoice, invoices, completedStatus])

  const handleInvoiceChange = (invoiceId: string) => {
    const invoice = invoices.find((i) => i.id === invoiceId)
    setForm((prev) => ({
      ...prev,
      invoice_id: invoiceId,
      customer_id: invoice?.customer_id || prev.customer_id,
      amount: invoice ? Number(invoice.total) : prev.amount,
      currency: invoice?.currency || prev.currency,
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) return

    const payload = {
      invoice_id: form.invoice_id || undefined,
      customer_id: form.customer_id || undefined,
      payment_method: form.payment_method,
      amount: form.amount,
      currency: form.currency,
      payment_date: new Date(form.payment_date).toISOString(),
      reference: form.reference || undefined,
      status: form.status || undefined,
    }
    const createData: PaymentCreate = {
      ...payload,
      tenant_id: user.tenant_id,
      company_id: user.company_id,
    }
    await crud.handleSave(createData, payload)
  }

  const invoiceLabel = (id?: string | null) => {
    if (!id) return '—'
    const inv = invoices.find((i) => i.id === id)
    return inv ? `${inv.series}-${inv.number} · ${invStatusLabel(inv.status)}` : id.slice(0, 8)
  }

  const customerLabel = (id?: string | null) => {
    if (!id) return '—'
    return customers.find((c) => c.id === id)?.legal_name || id.slice(0, 8)
  }

  const visiblePayments = useMemo(() => {
    return crud.items.filter((payment) => {
      if (prefillCustomer && payment.customer_id !== prefillCustomer) return false
      if (prefillInvoice && payment.invoice_id !== prefillInvoice) return false
      return true
    })
  }, [crud.items, prefillCustomer, prefillInvoice])

  const invoiceOptions = useMemo(() => {
    const cancelled = catalog?.invoice_statuses.find((s) => s.value === 'cancelled')?.value || 'cancelled'
    return invoices.filter((inv) => {
      if (inv.status === cancelled) return false
      if (form.customer_id && inv.customer_id && inv.customer_id !== form.customer_id) return false
      return true
    })
  }, [invoices, form.customer_id, catalog])

  return (
    <div>
      <div className="flex flex-wrap justify-between items-center gap-3 mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Registros de pago</h2>
          <p className="text-sm text-gray-600 mt-1">
            Cada cobro queda en el historial y actualiza el saldo de la{' '}
            <Link to="/current-accounts" className="text-blue-600 hover:text-blue-800">
              cuenta corriente
            </Link>
            .
          </p>
        </div>
        <button onClick={crud.openCreate} className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
          Agregar pago
        </button>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        {crud.loading && <div className="p-4 text-gray-500">Cargando...</div>}
        {crud.error && <div className="p-4 text-red-600">{crud.error}</div>}
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Factura</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cliente</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Método</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Monto</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {visiblePayments.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-4 text-center text-gray-500">
                  No hay pagos cargados. Creá el primero para empezar.
                </td>
              </tr>
            ) : (
              visiblePayments.map((payment) => (
                <tr key={payment.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{payment.payment_date.slice(0, 10)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{invoiceLabel(payment.invoice_id)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {payment.customer_id ? (
                      <Link
                        className="text-blue-600 hover:text-blue-800"
                        to={`/current-accounts?customer=${payment.customer_id}`}
                      >
                        {customerLabel(payment.customer_id)}
                      </Link>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{paymentMethodLabel(payment.payment_method)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{payStatusLabel(payment.status)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {payment.amount} {payment.currency}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button onClick={() => crud.openEdit(payment)} className="text-blue-600 hover:text-blue-900 mr-4">
                      Editar
                    </button>
                    <button onClick={() => crud.handleDelete(payment.id)} className="text-red-600 hover:text-red-900">
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Modal
        open={crud.modalOpen}
        title={crud.editing ? 'Editar pago' : 'Agregar pago'}
        onClose={crud.closeModal}
        footer={
          <>
            <button type="button" onClick={crud.closeModal} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">
              Cancelar
            </button>
            <button
              type="submit"
              form="payment-form"
              disabled={crud.saving}
              className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {crud.saving ? 'Guardando...' : 'Guardar'}
            </button>
          </>
        }
      >
        {crud.modalError && <div className="mb-4 rounded-md bg-red-50 p-3 text-red-700 text-sm">{crud.modalError}</div>}
        <form id="payment-form" onSubmit={handleSubmit} className="space-y-4">
          <FormField label="Factura">
            <select className={inputClass} value={form.invoice_id} onChange={(e) => handleInvoiceChange(e.target.value)}>
              <option value="">Sin factura</option>
              {invoiceOptions.map((inv) => (
                <option key={inv.id} value={inv.id}>
                  {inv.series}-{inv.number} ({inv.total} {inv.currency}) · {invStatusLabel(inv.status)}
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Cliente">
            <select
              className={inputClass}
              value={form.customer_id}
              onChange={(e) => setForm({ ...form, customer_id: e.target.value })}
            >
              <option value="">Sin cliente</option>
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.legal_name}
                </option>
              ))}
            </select>
          </FormField>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Método">
              <select
                className={inputClass}
                required
                value={form.payment_method}
                onChange={(e) => setForm({ ...form, payment_method: e.target.value })}
              >
                {paymentMethods.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </select>
            </FormField>
            <FormField label="Monto">
              <input
                className={inputClass}
                type="number"
                min={0}
                step="0.01"
                required
                value={form.amount}
                onChange={(e) => setForm({ ...form, amount: Number(e.target.value) })}
              />
            </FormField>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Fecha">
              <input
                className={inputClass}
                type="datetime-local"
                required
                value={form.payment_date}
                onChange={(e) => setForm({ ...form, payment_date: e.target.value })}
              />
            </FormField>
            <FormField label="Moneda">
              <input
                className={inputClass}
                required
                value={form.currency}
                onChange={(e) => setForm({ ...form, currency: e.target.value })}
              />
            </FormField>
          </div>
          <FormField label="Referencia">
            <input
              className={inputClass}
              value={form.reference}
              onChange={(e) => setForm({ ...form, reference: e.target.value })}
            />
          </FormField>
          <FormField label="Estado">
            <select
              className={inputClass}
              value={form.status}
              onChange={(e) => setForm({ ...form, status: e.target.value })}
            >
              {paymentStatuses.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </FormField>
        </form>
      </Modal>
    </div>
  )
}

export default Payments
