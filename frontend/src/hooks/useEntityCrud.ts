import { useCallback, useEffect, useState } from 'react'
import { getErrorMessage } from '../utils/errors'

interface CrudApi<T, Create, Update> {
  list: () => Promise<T[]>
  create: (data: Create) => Promise<T>
  update: (id: string, data: Update) => Promise<T>
  delete: (id: string) => Promise<void>
}

export function useEntityCrud<T extends { id: string }, Create, Update>(
  api: CrudApi<T, Create, Update>,
  loadErrorMessage: string,
  deleteConfirmMessage: string
) {
  const [items, setItems] = useState<T[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<T | null>(null)
  const [saving, setSaving] = useState(false)
  const [modalError, setModalError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.list()
      setItems(data)
    } catch (err) {
      setError(getErrorMessage(err, loadErrorMessage))
    } finally {
      setLoading(false)
    }
  }, [api, loadErrorMessage])

  useEffect(() => {
    load()
  }, [load])

  const openCreate = () => {
    setEditing(null)
    setModalError(null)
    setModalOpen(true)
  }

  const openEdit = (item: T) => {
    setEditing(item)
    setModalError(null)
    setModalOpen(true)
  }

  const closeModal = () => {
    setModalOpen(false)
    setEditing(null)
    setModalError(null)
  }

  const handleSave = async (createData: Create, updateData: Update) => {
    setSaving(true)
    setModalError(null)
    try {
      if (editing) {
        await api.update(editing.id, updateData)
      } else {
        await api.create(createData)
      }
      closeModal()
      await load()
    } catch (err) {
      setModalError(getErrorMessage(err, 'Error al guardar'))
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!window.confirm(deleteConfirmMessage)) return
    setError(null)
    try {
      await api.delete(id)
      await load()
    } catch (err) {
      setError(getErrorMessage(err, 'Error al eliminar'))
    }
  }

  return {
    items,
    loading,
    error,
    modalOpen,
    editing,
    saving,
    modalError,
    openCreate,
    openEdit,
    closeModal,
    handleSave,
    handleDelete,
    reload: load,
  }
}
