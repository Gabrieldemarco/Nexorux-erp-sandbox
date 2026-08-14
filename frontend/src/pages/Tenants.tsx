import { useEffect, useState } from 'react'
import { useEntityCrud } from '../hooks/useEntityCrud'
import Modal from '../components/Modal'
import FormField, { inputClass } from '../components/FormField'
import EntityListRow from '../components/EntityListRow'
import { tenantsApi, TenantCreate, TenantResponse, TenantUpdate } from '../services/tenants'
import { TENANT_STATUS_OPTIONS, tenantStatusLabel } from '../utils/statusLabels'
import { useCatalog } from '../hooks/useCatalog'

const defaultForm = {
  name: '',
  status: 'active',
}

const Tenants = () => {
  const { catalog } = useCatalog()
  const statusOptions = catalog?.tenant_statuses?.length ? catalog.tenant_statuses : [...TENANT_STATUS_OPTIONS]
  const statusLabel = (code?: string | null) =>
    catalog?.tenant_statuses.find((s) => s.value === code)?.label || tenantStatusLabel(code)
  const crud = useEntityCrud<TenantResponse, TenantCreate, TenantUpdate>(
    tenantsApi,
    'No se pudieron cargar los tenants',
    '¿Eliminar este tenant?'
  )
  const [form, setForm] = useState(defaultForm)

  useEffect(() => {
    if (!crud.modalOpen) return
    if (crud.editing) {
      setForm({
        name: crud.editing.name,
        status: crud.editing.status || 'active',
      })
    } else {
      setForm(defaultForm)
    }
  }, [crud.modalOpen, crud.editing])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const payload = { ...form }
    await crud.handleSave(payload, payload)
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Tenants</h2>
        <button onClick={crud.openCreate} className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
          Agregar tenant
        </button>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        {crud.loading && <div className="p-4 text-gray-500">Cargando...</div>}
        {crud.error && <div className="p-4 text-red-600">{crud.error}</div>}
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Creado</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {crud.items.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-4 text-center text-gray-500">
                  No hay tenants cargados. Creá el primero para empezar.
                </td>
              </tr>
            ) : (
              crud.items.map((tenant) => (
                <EntityListRow
                  key={tenant.id}
                  onOpen={() => crud.openEdit(tenant)}
                  actions={
                    <>
                      <button type="button" onClick={() => crud.openEdit(tenant)} className="text-blue-600 hover:text-blue-900 mr-4">
                        Abrir
                      </button>
                      <button type="button" onClick={() => crud.handleDelete(tenant.id)} className="text-red-600 hover:text-red-900">
                        Eliminar
                      </button>
                    </>
                  }
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{tenant.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{statusLabel(tenant.status)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(tenant.created_at).toLocaleDateString()}
                  </td>
                </EntityListRow>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Modal
        open={crud.modalOpen}
        title={crud.editing ? `Tenant · ${crud.editing.name}` : 'Agregar tenant'}
        onClose={crud.closeModal}
        footer={
          <>
            <button type="button" onClick={crud.closeModal} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">
              Cancelar
            </button>
            <button type="submit" form="tenant-form" disabled={crud.saving} className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50">
              {crud.saving ? 'Guardando...' : 'Guardar'}
            </button>
          </>
        }
      >
        {crud.modalError && <div className="mb-4 rounded-md bg-red-50 p-3 text-red-700 text-sm">{crud.modalError}</div>}
        <form id="tenant-form" onSubmit={handleSubmit} className="space-y-4">
          <FormField label="Nombre">
            <input className={inputClass} required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </FormField>
          <FormField label="Estado">
            <select className={inputClass} value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              {statusOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </FormField>
        </form>
      </Modal>
    </div>
  )
}

export default Tenants
