import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useEntityCrud } from '../hooks/useEntityCrud'
import Modal from '../components/Modal'
import FormField, { inputClass } from '../components/FormField'
import { customersApi, CustomerCreate, CustomerResponse, CustomerUpdate } from '../services/customers'
import { useCatalog } from '../hooks/useCatalog'

const defaultForm = {
  customer_type: 'final_consumer',
  legal_name: '',
  trade_name: '',
  rut: '00000000',
  email: '',
  phone: '',
  currency: '',
  credit_limit: 0,
  is_active: true,
}

const Customers = () => {
  const { user } = useAuth()
  const { currency: companyCurrency } = useCatalog()
  const crud = useEntityCrud<CustomerResponse, CustomerCreate, CustomerUpdate>(
    customersApi,
    'No se pudieron cargar los clientes',
    '¿Eliminar este cliente?'
  )
  const [form, setForm] = useState(defaultForm)

  useEffect(() => {
    if (!crud.modalOpen) return
    if (crud.editing) {
      setForm({
        customer_type: crud.editing.customer_type,
        legal_name: crud.editing.legal_name,
        trade_name: crud.editing.trade_name ?? '',
        rut: crud.editing.rut,
        email: crud.editing.email ?? '',
        phone: crud.editing.phone ?? '',
        currency: crud.editing.currency,
        credit_limit: crud.editing.credit_limit,
        is_active: crud.editing.is_active,
      })
    } else {
      setForm({ ...defaultForm, currency: companyCurrency })
    }
  }, [crud.modalOpen, crud.editing, companyCurrency])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) return

    const payload = {
      ...form,
      trade_name: form.trade_name || undefined,
      email: form.email || undefined,
      phone: form.phone || undefined,
    }
    const createData: CustomerCreate = {
      ...payload,
      tenant_id: user.tenant_id,
      company_id: user.company_id,
    }
    await crud.handleSave(createData, payload)
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Clientes</h2>
        <button onClick={crud.openCreate} className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
          Agregar cliente
        </button>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        {crud.loading && <div className="p-4 text-gray-500">Cargando...</div>}
        {crud.error && <div className="p-4 text-red-600">{crud.error}</div>}
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">RUT</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Crédito</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {crud.items.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                  No hay clientes cargados. Creá el primero para empezar.
                </td>
              </tr>
            ) : (
              crud.items.map((customer) => (
                <tr key={customer.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{customer.legal_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{customer.rut}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{customer.email || '-'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{customer.customer_type}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{customer.credit_limit || 0}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <Link
                      to={`/current-accounts?customer=${customer.id}`}
                      className="text-blue-600 hover:text-blue-900 mr-4"
                    >
                      Cuenta
                    </Link>
                    <button onClick={() => crud.openEdit(customer)} className="text-blue-600 hover:text-blue-900 mr-4">
                      Editar
                    </button>
                    <button onClick={() => crud.handleDelete(customer.id)} className="text-red-600 hover:text-red-900">
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
        title={crud.editing ? 'Editar cliente' : 'Agregar cliente'}
        onClose={crud.closeModal}
        footer={
          <>
            <button type="button" onClick={crud.closeModal} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">
              Cancelar
            </button>
            <button type="submit" form="customer-form" disabled={crud.saving} className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50">
              {crud.saving ? 'Guardando...' : 'Guardar'}
            </button>
          </>
        }
      >
        {crud.modalError && <div className="mb-4 rounded-md bg-red-50 p-3 text-red-700 text-sm">{crud.modalError}</div>}
        <form id="customer-form" onSubmit={handleSubmit} className="space-y-4">
          <FormField label="Tipo">
            <select className={inputClass} value={form.customer_type} onChange={(e) => setForm({ ...form, customer_type: e.target.value, rut: e.target.value === 'final_consumer' ? '00000000' : form.rut })}>
              <option value="final_consumer">Consumidor final</option>
              <option value="person">Persona</option>
              <option value="company">Empresa</option>
            </select>
          </FormField>
          <FormField label="Nombre legal">
            <input className={inputClass} required value={form.legal_name} onChange={(e) => setForm({ ...form, legal_name: e.target.value })} />
          </FormField>
          <FormField label="Nombre comercial">
            <input className={inputClass} value={form.trade_name} onChange={(e) => setForm({ ...form, trade_name: e.target.value })} />
          </FormField>
          <FormField label={form.customer_type === 'final_consumer' ? 'Documento (opcional)' : 'RUT / CI'}>
            <input
              className={inputClass}
              required={form.customer_type !== 'final_consumer'}
              value={form.rut}
              placeholder={form.customer_type === 'final_consumer' ? 'No requerido para e-Ticket' : ''}
              onChange={(e) => setForm({ ...form, rut: e.target.value })}
            />
          </FormField>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Email">
              <input className={inputClass} type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </FormField>
            <FormField label="Teléfono">
              <input className={inputClass} value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
            </FormField>
          </div>
          <FormField label="Límite de crédito">
            <input className={inputClass} type="number" step="0.01" value={form.credit_limit} onChange={(e) => setForm({ ...form, credit_limit: Number(e.target.value) })} />
          </FormField>
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
            Activo
          </label>
        </form>
      </Modal>
    </div>
  )
}

export default Customers
