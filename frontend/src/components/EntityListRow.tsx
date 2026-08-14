import type { KeyboardEvent, MouseEvent, ReactNode } from 'react'

const rowClass =
  'cursor-pointer hover:bg-slate-50 focus-visible:bg-blue-50/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-200'

type EntityListRowProps = {
  onOpen: () => void
  children: ReactNode
  /** Celda de acciones; los clics no abren el formulario. */
  actions?: ReactNode
  actionsClassName?: string
}

/**
 * Fila de lista: click / Enter / Space abre el formulario de detalle/edición.
 */
export function EntityListRow({
  onOpen,
  children,
  actions,
  actionsClassName = 'px-6 py-4 whitespace-nowrap text-right text-sm font-medium',
}: EntityListRowProps) {
  const handleKeyDown = (e: KeyboardEvent<HTMLTableRowElement>) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      onOpen()
    }
  }

  const stop = (e: MouseEvent | KeyboardEvent) => {
    e.stopPropagation()
  }

  return (
    <tr
      role="button"
      tabIndex={0}
      className={rowClass}
      onClick={onOpen}
      onKeyDown={handleKeyDown}
      title="Abrir detalle"
    >
      {children}
      {actions != null && (
        <td className={actionsClassName} onClick={stop} onKeyDown={stop}>
          {actions}
        </td>
      )}
    </tr>
  )
}

export default EntityListRow
