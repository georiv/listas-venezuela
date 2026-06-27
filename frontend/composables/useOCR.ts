export function useOCR() {
  const apiBase = useRuntimeConfig().public.apiUrl

  async function uploadAndProcess(
    files: File[],
    centroHint: string = '',
  ): Promise<Record<string, string>[]> {
    const form = new FormData()
    for (const file of files) form.append('files', file)
    form.append('centro_hint', centroHint)
    // No voluntario_id in the open MVP (no login). Add it back once
    // Supabase Auth is wired up.

    const resp = await fetch(`${apiBase}/upload`, {
      method: 'POST',
      body: form,
    })

    if (!resp.ok) {
      const data = await resp.json().catch(() => ({}))
      throw new Error(data.detail ?? `HTTP ${resp.status}`)
    }

    const data = await resp.json()
    return data.records as Record<string, string>[]
  }

  return { uploadAndProcess }
}
