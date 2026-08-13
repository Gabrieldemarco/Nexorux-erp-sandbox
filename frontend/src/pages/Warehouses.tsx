import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { useEntityCrud } from '../hooks/useEntityCrud'
import Modal from '../components/Modal'
import FormField, { inputClass } from '../components/FormField'
import { warehousesApi, WarehouseCreate, WarehouseResponse, WarehouseUpdate } from '../services/warehouses'
import { branchesApi, BranchResponse } from '../services/branches'

const defaultForm = {
  name: '',
  code: '',
  branch_id: '',
  description: '',
  is_active: true,
}

const Warehouses = () => {
  const { user } = useAuth()
  const crud = useEntityCrud<WarehouseResponse, WarehouseCreate, WarehouseUpdate>(
    warehousesApi,
    'No se pudieron cargar los depósitos',
    '¿Eliminar este depósito?'
  )
  const [form, setForm] = useState(defaultForm)
  const [branches, setBranches] = useState<BranchResponse[]>([])

  useEffect(() => {
    branchesApi.list().then(setBranches).catch(() => setBranches([]))
  }, [])

  useEffect(() => {
    if (!crud.modalOpen) return
    if (crud.editing) {
      setForm({
        name: crud.editing.name,
        code: crud.editing.code,
        branch_id: crud.editing.branch_id || '',
        description: crud.editing.description || '',
        is_active: crud.editing.is_active,
      })
    } else {
      setForm({
        ...defaultForm,
        branch_id: branches[0]?.id || '',
      })
    }
  }, [crud.modalOpen, crud.editing, branches])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) return

    const payload = {
      name: form.name,
      code: form.code,
      branch_id: form.branch_id || undefined,
      description: form.description || undefined,
      is_active: form.is_active,
    }
    const createData: WarehouseCreate = {
      ...payload,
      tenant_id: user.tenant_id,
      company_id: user.company_id,
    }
    await crud.handleSave(createData, payload)
  }

  const branchName = (id?: string) => branches.find((b) => b.id === id)?.name || '—'

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Depósitos</h2>
        <button onClick={crud.openCreate} className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
          Agregar depósito
        </button>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        {crud.loading && <div className="p-4 text-gray-500">Cargando...</div>}
        {crud.error && <div className="p-4 text-red-600">{crud.error}</div>}
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Código</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sucursal</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {crud.items.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                  No hay depósitos cargados. Creá el primero para empezar.
                </td>
              </tr>
            ) : (
              crud.items.map((wh) => (
                <tr key={wh.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{wh.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{wh.code}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{branchName(wh.branch_id)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{wh.is_active ? 'Activo' : 'Inactivo'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button onClick={() => crud.openEdit(wh)} className="text-blue-600 hover:text-blue-900 mr-4">
                      Editar
                    </button>
                    <button onClick={() => crud.handleDelete(wh.id)} className="text-red-600 hover:text-red-900">
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
        title={crud.editing ? 'Editar depósito' : 'Agregar depósito'}
        onClose={crud.closeModal}
        footer={
          <>
            <button type="button" onClick={crud.closeModal} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">
              Cancelar
            </button>
            <button
              type="submit"
              form="warehouse-form"
              disabled={crud.saving}
              className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {crud.saving ? 'Guardando...' : 'Guardar'}
            </button>
          </>
        }
      >
        {crud.modalError && <div className="mb-4 rounded-md bg-red-50 p-3 text-red-700 text-sm">{crud.modalError}</div>}
        <form id="warehouse-form" onSubmit={handleSubmit} className="space-y-4">
          <FormField label="Nombre">
            <input className={inputClass} required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </FormField>
          <FormField label="Código">
            <input className={inputClass} required value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
          </FormField>
          <FormField label="Sucursal">
            <select className={inputClass} value={form.branch_id} onChange={(e) => setForm({ ...form, branch_id: e.target.value })}>
              <option value="">Sin sucursal</option>
              {branches.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Descripción">
            <input className={inputClass} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
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

export default Warehouses
