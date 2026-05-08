import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export function generateRealitySeed({
  topic,
  simulationRequirement,
  includeLatest = true,
  exportPdf = true,
  file = null,
}) {
  const form = new FormData()
  form.append('topic', topic)
  form.append('simulation_requirement', simulationRequirement)
  form.append('include_latest', includeLatest ? 'true' : 'false')
  form.append('export_pdf', exportPdf ? 'true' : 'false')
  if (file) form.append('file', file)
  return api.post('/reality-seed/generate', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
