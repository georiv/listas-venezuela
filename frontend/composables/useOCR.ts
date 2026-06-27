export function useOCR() {
  const apiBase = useRuntimeConfig().public.apiUrl

  async function uploadAndProcess(
    files: File[],
    centroHint: string = '',
  ): Promise<{ records: Record<string, string>[]; errores: string[] }> {
    const form = new FormData()
    for (const file of files) form.append('files', file)
    form.append('centro_hint', centroHint)

    const resp = await fetch(`${apiBase}/upload`, {
      method: 'POST',
      body: form,
    })

    if (!resp.ok) {
      const data = await resp.json().catch(() => ({}))
      throw new Error(data.detail ?? `HTTP ${resp.status}`)
    }

    const data = await resp.json()
    return {
      records: (data.records ?? []) as Record<string, string>[],
      errores: (data.errores ?? []) as string[],
    }
  }

  return { uploadAndProcess }
}
