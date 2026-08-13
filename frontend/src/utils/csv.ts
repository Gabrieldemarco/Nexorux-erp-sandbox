/** Download CSV with UTF-8 BOM so Excel opens Spanish characters correctly. */
export function downloadCsv(filename: string, rows: string[][]): void {
  const escapeCell = (value: string) => {
    const needsQuotes = /[",\n\r]/.test(value)
    const escaped = value.replace(/"/g, '""')
    return needsQuotes ? `"${escaped}"` : escaped
  }

  const body = rows.map((row) => row.map((cell) => escapeCell(String(cell ?? ''))).join(',')).join('\r\n')
  const blob = new Blob(['\uFEFF' + body], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
