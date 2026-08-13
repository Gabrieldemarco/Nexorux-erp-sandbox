import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { useEntityCrud } from '../hooks/useEntityCrud'
import Modal from '../components/Modal'
import FormField, { inputClass } from '../components/FormField'
import { companiesApi, CompanyCreate, CompanyResponse, CompanyUpdate } from '../services/companies'

const defaultForm = {
  legal_name: '',
  trade_name: '',
  rut: '',
  fiscal_address: '',
  phone: '',
  email: '',
  country: 'Uruguay',
  currency: 'UYU',
  tax_regime: '',
}

const Companies = () => {
  const { user } = useAuth()
  const crud = useEntityCrud<CompanyResponse, CompanyCreate, CompanyUpdate>(
    companiesApi,
    'No se pudieron cargar las razones sociales',
    '¿Eliminar esta razón social?'
  )
  const [form, setForm] = useState(defaultForm)

  useEffect(() => {
    if (!crud.modalOpen) return
    if (crud.editing) {
      setForm({
        legal_name: crud.editing.legal_name,
        trade_name: crud.editing.trade_name ?? '',
        rut: crud.editing.rut,
        fiscal_address: crud.editing.fiscal_address ?? '',
        phone: crud.editing.phone ?? '',
        email: crud.editing.email ?? '',
        country: crud.editing.country,
        currency: crud.editing.currency,
        tax_regime: crud.editing.tax_regime ?? '',
      })
    } else {
      setForm(defaultForm)
    }
  }, [crud.modalOpen, crud.editing])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) return

    const payload = {
      ...form,
      trade_name: form.trade_name || undefined,
      fiscal_address: form.fiscal_address || undefined,
      phone: form.phone || undefined,
      email: form.email || undefined,
      tax_regime: form.tax_regime || undefined,
    }
    const createData: CompanyCreate = {
      ...payload,
      tenant_id: user.tenant_id,
    }
    await crud.handleSave(createData, payload)
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Razones sociales</h2>
        <button onClick={crud.openCreate} className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
          Agregar razón social
        </button>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        {crud.loading && <div className="p-4 text-gray-500">Cargando...</div>}
        {crud.error && <div className="p-4 text-red-600">{crud.error}</div>}
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre legal</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">RUT</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">País</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {crud.items.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                  No hay razones sociales cargadas. Creá la primera para empezar.
                </td>
              </tr>
            ) : (
              crud.items.map((company) => (
                <tr key={company.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{company.legal_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{company.rut}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{company.email || '-'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{company.country}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button onClick={() => crud.openEdit(company)} className="text-blue-600 hover:text-blue-900 mr-4">
                      Editar
                    </button>
                    <button onClick={() => crud.handleDelete(company.id)} className="text-red-600 hover:text-red-900">
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
        title={crud.editing ? 'Editar razón social' : 'Agregar razón social'}
        onClose={crud.closeModal}
        footer={
          <>
            <button type="button" onClick={crud.closeModal} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">
              Cancelar
            </button>
            <button type="submit" form="company-form" disabled={crud.saving} className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50">
              {crud.saving ? 'Guardando...' : 'Guardar'}
            </button>
          </>
        }
      >
        {crud.modalError && <div className="mb-4 rounded-md bg-red-50 p-3 text-red-700 text-sm">{crud.modalError}</div>}
        <form id="company-form" onSubmit={handleSubmit} className="space-y-4">
          <FormField label="Nombre legal">
            <input className={inputClass} required value={form.legal_name} onChange={(e) => setForm({ ...form, legal_name: e.target.value })} />
          </FormField>
          <FormField label="Nombre comercial">
            <input className={inputClass} value={form.trade_name} onChange={(e) => setForm({ ...form, trade_name: e.target.value })} />
          </FormField>
          <FormField label="RUT">
            <input className={inputClass} required value={form.rut} onChange={(e) => setForm({ ...form, rut: e.target.value })} />
          </FormField>
          <FormField label="Dirección fiscal">
            <input className={inputClass} value={form.fiscal_address} onChange={(e) => setForm({ ...form, fiscal_address: e.target.value })} />
          </FormField>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Email">
              <input className={inputClass} type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </FormField>
            <FormField label="Teléfono">
              <input className={inputClass} value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
            </FormField>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="País">
              <input className={inputClass} value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })} />
            </FormField>
            <FormField label="Moneda">
              <input className={inputClass} value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} />
            </FormField>
          </div>
          <FormField label="Régimen tributario">
            <input className={inputClass} value={form.tax_regime} onChange={(e) => setForm({ ...form, tax_regime: e.target.value })} />
          </FormField>
        </form>
      </Modal>
    </div>
  )
}

export default Companies
