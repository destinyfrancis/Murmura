import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export function createWorkflow(seedText, scenarioQuestion = '', preset = 'research') {
  return api.post('/workflow/quick-start', {
    seed_text: seedText,
    scenario_question: scenarioQuestion,
    preset,
  })
}

export function createWorkflowWithFile(file, scenarioQuestion = '', preset = 'research') {
  const form = new FormData()
  form.append('file', file)
  form.append('scenario_question', scenarioQuestion)
  form.append('preset', preset)
  return api.post('/workflow/quick-start/upload', form)
}

export function getWorkflow(workflowId) {
  return api.get(`/workflow/${workflowId}`)
}
