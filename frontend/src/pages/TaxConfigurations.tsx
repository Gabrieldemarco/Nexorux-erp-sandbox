import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { useEntityCrud } from '../hooks/useEntityCrud'
import Modal from '../components/Modal'
import FormField, { inputClass } from '../components/FormField'
import EntityListRow from '../components/EntityListRow'
import {
  taxConfigurationsApi,
  TaxConfigurationCreate,
  TaxConfigurationResponse,
  TaxConfigurationUpdate,
} from '../services/taxConfigurations'

const defaultForm = {
  tax_code: '',
  description: '',
  rate: 22,
  effective_from: new Date().toISOString().slice(0, 16),
  effective_to: '',
}

const toIsoOrUndefined = (value: string) => (value ? new Date(value).toISOString() : undefined)

const TaxConfigurations = () => {
  const { user } = useAuth()
  const crud = useEntityCrud<TaxConfigurationResponse, TaxConfigurationCreate, TaxConfigurationUpdate>(
    taxConfigurationsApi,
    'No se pudieron cargar las configuraciones de impuestos',
    '¿Eliminar esta configuración de impuestos?'
  )
  const [form, setForm] = useState(defaultForm)

  useEffect(() => {
    if (!crud.modalOpen) return
    if (crud.editing) {
      setForm({
        tax_code: crud.editing.tax_code,
        description: crud.editing.description || '',
        rate: Number(crud.editing.rate),
        effective_from: crud.editing.effective_from ? crud.editing.effective_from.slice(0, 16) : '',
        effective_to: crud.editing.effective_to ? crud.editing.effective_to.slice(0, 16) : '',
      })
    } else {
      setForm(defaultForm)
    }
  }, [crud.modalOpen, crud.editing])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) return

    const payload = {
      tax_code: form.tax_code,
      description: form.description || undefined,
      rate: form.rate,
      effective_from: toIsoOrUndefined(form.effective_from),
      effective_to: toIsoOrUndefined(form.effective_to),
    }
    const createData: TaxConfigurationCreate = {
      ...payload,
      tenant_id: user.tenant_id,
      company_id: user.company_id,
    }
    await crud.handleSave(createData, payload)
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Impuestos</h2>
        <button onClick={crud.openCreate} className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
          Agregar impuesto
        </button>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        {crud.loading && <div className="p-4 text-gray-500">Cargando...</div>}
        {crud.error && <div className="p-4 text-red-600">{crud.error}</div>}
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Código</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descripción</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tasa %</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vigencia</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {crud.items.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                  No hay configuraciones de impuestos. Creá la primera para empezar.
                </td>
              </tr>
            ) : (
              crud.items.map((row) => (
                <EntityListRow
                  key={row.id}
                  onOpen={() => crud.openEdit(row)}
                  actions={
                    <>
                      <button type="button" onClick={() => crud.openEdit(row)} className="text-blue-600 hover:text-blue-900 mr-4">
                        Abrir
                      </button>
                      <button type="button" onClick={() => crud.handleDelete(row.id)} className="text-red-600 hover:text-red-900">
                        Eliminar
                      </button>
                    </>
                  }
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{row.tax_code}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{row.description || '—'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{row.rate}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {row.effective_from || row.effective_to
                      ? `${row.effective_from?.slice(0, 10) || '—'} → ${row.effective_to?.slice(0, 10) || '—'}`
                      : '—'}
                  </td>
                </EntityListRow>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Modal
        open={crud.modalOpen}
        title={crud.editing ? `Impuesto · ${crud.editing.tax_code}` : 'Agregar impuesto'}
        onClose={crud.closeModal}
        footer={
          <>
            <button type="button" onClick={crud.closeModal} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">
              Cancelar
            </button>
            <button
              type="submit"
              form="tax-form"
              disabled={crud.saving}
              className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {crud.saving ? 'Guardando...' : 'Guardar'}
            </button>
          </>
        }
      >
        {crud.modalError && <div className="mb-4 rounded-md bg-red-50 p-3 text-red-700 text-sm">{crud.modalError}</div>}
        <form id="tax-form" onSubmit={handleSubmit} className="space-y-4">
          <FormField label="Código">
            <input
              className={inputClass}
              required
              value={form.tax_code}
              onChange={(e) => setForm({ ...form, tax_code: e.target.value })}
            />
          </FormField>
          <FormField label="Descripción">
            <input
              className={inputClass}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </FormField>
          <FormField label="Tasa (%)">
            <input
              className={inputClass}
              type="number"
              min={0}
              step="0.01"
              required
              value={form.rate}
              onChange={(e) => setForm({ ...form, rate: Number(e.target.value) })}
            />
          </FormField>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Vigente desde">
              <input
                className={inputClass}
                type="datetime-local"
                value={form.effective_from}
                onChange={(e) => setForm({ ...form, effective_from: e.target.value })}
              />
            </FormField>
            <FormField label="Vigente hasta">
              <input
                className={inputClass}
                type="datetime-local"
                value={form.effective_to}
                onChange={(e) => setForm({ ...form, effective_to: e.target.value })}
              />
            </FormField>
          </div>
        </form>
      </Modal>
    </div>
  )
}

export default TaxConfigurations
