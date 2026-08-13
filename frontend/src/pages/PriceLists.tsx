import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { useEntityCrud } from '../hooks/useEntityCrud'
import Modal from '../components/Modal'
import FormField, { inputClass } from '../components/FormField'
import { priceListsApi, PriceListCreate, PriceListResponse, PriceListUpdate } from '../services/priceLists'

const defaultForm = {
  name: '',
  currency: 'UYU',
  is_default: false,
  valid_from: '',
  valid_to: '',
}

const toIsoOrUndefined = (value: string) => (value ? new Date(value).toISOString() : undefined)

const PriceLists = () => {
  const { user } = useAuth()
  const crud = useEntityCrud<PriceListResponse, PriceListCreate, PriceListUpdate>(
    priceListsApi,
    'No se pudieron cargar las listas de precios',
    '¿Eliminar esta lista de precios?'
  )
  const [form, setForm] = useState(defaultForm)

  useEffect(() => {
    if (!crud.modalOpen) return
    if (crud.editing) {
      setForm({
        name: crud.editing.name,
        currency: crud.editing.currency,
        is_default: Boolean(crud.editing.is_default),
        valid_from: crud.editing.valid_from ? crud.editing.valid_from.slice(0, 16) : '',
        valid_to: crud.editing.valid_to ? crud.editing.valid_to.slice(0, 16) : '',
      })
    } else {
      setForm(defaultForm)
    }
  }, [crud.modalOpen, crud.editing])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) return

    const payload = {
      name: form.name,
      currency: form.currency,
      is_default: form.is_default,
      valid_from: toIsoOrUndefined(form.valid_from),
      valid_to: toIsoOrUndefined(form.valid_to),
    }
    const createData: PriceListCreate = {
      ...payload,
      tenant_id: user.tenant_id,
      company_id: user.company_id,
    }
    await crud.handleSave(createData, payload)
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Listas de precios</h2>
        <button onClick={crud.openCreate} className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
          Agregar lista
        </button>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        {crud.loading && <div className="p-4 text-gray-500">Cargando...</div>}
        {crud.error && <div className="p-4 text-red-600">{crud.error}</div>}
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Moneda</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Por defecto</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vigencia</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {crud.items.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                  No hay listas de precios. Creá la primera para empezar.
                </td>
              </tr>
            ) : (
              crud.items.map((row) => (
                <tr key={row.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{row.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{row.currency}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{row.is_default ? 'Sí' : 'No'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {row.valid_from || row.valid_to
                      ? `${row.valid_from?.slice(0, 10) || '—'} → ${row.valid_to?.slice(0, 10) || '—'}`
                      : '—'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button onClick={() => crud.openEdit(row)} className="text-blue-600 hover:text-blue-900 mr-4">
                      Editar
                    </button>
                    <button onClick={() => crud.handleDelete(row.id)} className="text-red-600 hover:text-red-900">
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
        title={crud.editing ? 'Editar lista' : 'Agregar lista'}
        onClose={crud.closeModal}
        footer={
          <>
            <button type="button" onClick={crud.closeModal} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">
              Cancelar
            </button>
            <button
              type="submit"
              form="price-list-form"
              disabled={crud.saving}
              className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {crud.saving ? 'Guardando...' : 'Guardar'}
            </button>
          </>
        }
      >
        {crud.modalError && <div className="mb-4 rounded-md bg-red-50 p-3 text-red-700 text-sm">{crud.modalError}</div>}
        <form id="price-list-form" onSubmit={handleSubmit} className="space-y-4">
          <FormField label="Nombre">
            <input className={inputClass} required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </FormField>
          <FormField label="Moneda">
            <input
              className={inputClass}
              required
              maxLength={3}
              value={form.currency}
              onChange={(e) => setForm({ ...form, currency: e.target.value.toUpperCase() })}
            />
          </FormField>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Válida desde">
              <input
                className={inputClass}
                type="datetime-local"
                value={form.valid_from}
                onChange={(e) => setForm({ ...form, valid_from: e.target.value })}
              />
            </FormField>
            <FormField label="Válida hasta">
              <input
                className={inputClass}
                type="datetime-local"
                value={form.valid_to}
                onChange={(e) => setForm({ ...form, valid_to: e.target.value })}
              />
            </FormField>
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={form.is_default}
              onChange={(e) => setForm({ ...form, is_default: e.target.checked })}
            />
            Lista por defecto
          </label>
        </form>
      </Modal>
    </div>
  )
}

export default PriceLists
