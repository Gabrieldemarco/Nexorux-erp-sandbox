import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { useEntityCrud } from '../hooks/useEntityCrud'
import Modal from '../components/Modal'
import FormField, { inputClass } from '../components/FormField'
import EntityListRow from '../components/EntityListRow'
import { rolesApi, RoleCreate, RoleResponse, RoleUpdate } from '../services/roles'
import { permissionsApi, PermissionResponse } from '../services/permissions'
import { getErrorMessage } from '../utils/errors'

const defaultForm = {
  name: '',
  key: '',
  description: '',
  is_default: false,
}

const groupByPrefix = (perms: PermissionResponse[]) => {
  const groups: Record<string, PermissionResponse[]> = {}
  for (const p of perms) {
    const prefix = p.code.includes('.') ? p.code.split('.')[0] : p.code
    if (!groups[prefix]) groups[prefix] = []
    groups[prefix].push(p)
  }
  return Object.entries(groups).sort(([a], [b]) => a.localeCompare(b))
}

const Roles = () => {
  const { user } = useAuth()
  const crud = useEntityCrud<RoleResponse, RoleCreate, RoleUpdate>(
    rolesApi,
    'No se pudieron cargar los roles',
    '¿Eliminar este rol?'
  )
  const [form, setForm] = useState(defaultForm)
  const [allPermissions, setAllPermissions] = useState<PermissionResponse[]>([])
  const [permModalOpen, setPermModalOpen] = useState(false)
  const [permRole, setPermRole] = useState<RoleResponse | null>(null)
  const [selectedPermIds, setSelectedPermIds] = useState<string[]>([])
  const [permSaving, setPermSaving] = useState(false)
  const [permError, setPermError] = useState<string | null>(null)

  useEffect(() => {
    if (!crud.modalOpen) return
    if (crud.editing) {
      setForm({
        name: crud.editing.name,
        key: crud.editing.key,
        description: crud.editing.description || '',
        is_default: crud.editing.is_default,
      })
    } else {
      setForm(defaultForm)
    }
  }, [crud.modalOpen, crud.editing])

  useEffect(() => {
    permissionsApi
      .list()
      .then(setAllPermissions)
      .catch(() => setAllPermissions([]))
  }, [])

  const permissionGroups = useMemo(() => groupByPrefix(allPermissions), [allPermissions])

  const openPermissions = (role: RoleResponse) => {
    setPermRole(role)
    setSelectedPermIds((role.permissions || []).map((p) => p.id))
    setPermError(null)
    setPermModalOpen(true)
  }

  const closePermissions = () => {
    setPermModalOpen(false)
    setPermRole(null)
    setSelectedPermIds([])
    setPermError(null)
  }

  const togglePermission = (id: string) => {
    setSelectedPermIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  const toggleGroup = (groupPerms: PermissionResponse[], checked: boolean) => {
    const ids = groupPerms.map((p) => p.id)
    setSelectedPermIds((prev) => {
      if (checked) {
        const set = new Set([...prev, ...ids])
        return Array.from(set)
      }
      return prev.filter((id) => !ids.includes(id))
    })
  }

  const savePermissions = async () => {
    if (!permRole) return
    setPermSaving(true)
    setPermError(null)
    try {
      const updated = await rolesApi.setPermissions(permRole.id, selectedPermIds)
      await crud.reload()
      setPermRole(updated)
      closePermissions()
    } catch (err) {
      setPermError(getErrorMessage(err, 'No se pudieron guardar los permisos'))
    } finally {
      setPermSaving(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) return

    const payload = {
      name: form.name,
      key: form.key,
      description: form.description || undefined,
      is_default: form.is_default,
    }
    const createData: RoleCreate = {
      ...payload,
      tenant_id: user.tenant_id,
    }
    await crud.handleSave(createData, payload)
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Roles</h2>
        <button onClick={crud.openCreate} className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
          Agregar rol
        </button>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        {crud.loading && <div className="p-4 text-gray-500">Cargando...</div>}
        {crud.error && <div className="p-4 text-red-600">{crud.error}</div>}
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Clave</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descripción</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Permisos</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Por defecto</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {crud.items.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                  No hay roles cargados. Creá el primero para empezar.
                </td>
              </tr>
            ) : (
              crud.items.map((role) => (
                <EntityListRow
                  key={role.id}
                  onOpen={() => crud.openEdit(role)}
                  actions={
                    <>
                      <button type="button" onClick={() => openPermissions(role)} className="text-indigo-600 hover:text-indigo-900 mr-4">
                        Permisos
                      </button>
                      <button type="button" onClick={() => crud.openEdit(role)} className="text-blue-600 hover:text-blue-900 mr-4">
                        Abrir
                      </button>
                      <button type="button" onClick={() => crud.handleDelete(role.id)} className="text-red-600 hover:text-red-900">
                        Eliminar
                      </button>
                    </>
                  }
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{role.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{role.key}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{role.description || '—'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {(role.permissions || []).length}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{role.is_default ? 'Sí' : 'No'}</td>
                </EntityListRow>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Modal
        open={crud.modalOpen}
        title={crud.editing ? `Rol · ${crud.editing.name}` : 'Agregar rol'}
        onClose={crud.closeModal}
        footer={
          <>
            <button type="button" onClick={crud.closeModal} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">
              Cancelar
            </button>
            <button
              type="submit"
              form="role-form"
              disabled={crud.saving}
              className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {crud.saving ? 'Guardando...' : 'Guardar'}
            </button>
          </>
        }
      >
        {crud.modalError && <div className="mb-4 rounded-md bg-red-50 p-3 text-red-700 text-sm">{crud.modalError}</div>}
        <form id="role-form" onSubmit={handleSubmit} className="space-y-4">
          <FormField label="Nombre">
            <input className={inputClass} required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </FormField>
          <FormField label="Clave">
            <input className={inputClass} required value={form.key} onChange={(e) => setForm({ ...form, key: e.target.value })} />
          </FormField>
          <FormField label="Descripción">
            <input
              className={inputClass}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </FormField>
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={form.is_default}
              onChange={(e) => setForm({ ...form, is_default: e.target.checked })}
            />
            Rol por defecto
          </label>
        </form>
      </Modal>

      <Modal
        open={permModalOpen}
        title={permRole ? `Permisos — ${permRole.name}` : 'Permisos'}
        onClose={closePermissions}
        size="xl"
        footer={
          <>
            <button type="button" onClick={closePermissions} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">
              Cancelar
            </button>
            <button
              type="button"
              onClick={savePermissions}
              disabled={permSaving}
              className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {permSaving ? 'Guardando...' : 'Guardar permisos'}
            </button>
          </>
        }
      >
        {permError && <div className="mb-4 rounded-md bg-red-50 p-3 text-red-700 text-sm">{permError}</div>}
        {allPermissions.length === 0 ? (
          <div className="text-sm text-gray-500">No hay permisos disponibles en el tenant.</div>
        ) : (
          <div className="space-y-4 max-h-[60vh] overflow-y-auto">
            {permissionGroups.map(([prefix, groupPerms]) => {
              const allChecked = groupPerms.every((p) => selectedPermIds.includes(p.id))
              return (
                <div key={prefix} className="border border-gray-200 rounded-md p-3">
                  <label className="flex items-center gap-2 text-sm font-medium text-gray-900 mb-2">
                    <input
                      type="checkbox"
                      checked={allChecked}
                      onChange={(e) => toggleGroup(groupPerms, e.target.checked)}
                    />
                    {prefix}
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pl-1">
                    {groupPerms.map((p) => (
                      <label key={p.id} className="flex items-start gap-2 text-sm text-gray-700">
                        <input
                          type="checkbox"
                          className="mt-0.5"
                          checked={selectedPermIds.includes(p.id)}
                          onChange={() => togglePermission(p.id)}
                        />
                        <span>
                          <span className="font-medium">{p.name}</span>
                          <span className="block text-xs text-gray-500">{p.code}</span>
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default Roles
