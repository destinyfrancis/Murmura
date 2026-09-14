import axios from 'axios'

const api = axios.create({ baseURL: '/api' })
const AUTH_TOKEN_KEY = 'murmura_admin_token'

function readAuthToken() {
  try {
    return sessionStorage.getItem(AUTH_TOKEN_KEY) || ''
  } catch {
    return ''
  }
}

function storeAuthToken(token) {
  try {
    if (token) sessionStorage.setItem(AUTH_TOKEN_KEY, token)
    else sessionStorage.removeItem(AUTH_TOKEN_KEY)
  } catch {
    // Settings remains usable until this page is closed when storage is blocked.
  }
}

api.interceptors.request.use((config) => {
  const token = readAuthToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

async function authenticate(path, email, password) {
  const response = await api.post(path, { email, password })
  const data = response.data?.data || response.data
  storeAuthToken(data?.token)
  return data
}

export function loginForSettings(email, password) {
  return authenticate('/auth/login', email, password)
}

export function registerForSettings(email, password) {
  return authenticate('/auth/register', email, password)
}

export function clearSettingsAuth() {
  storeAuthToken('')
}

/**
 * Fetch all current settings (API keys are masked).
 * @returns {Promise<{llm, api_keys, simulation, data}>}
 */
export function getSettings() {
  return api.get('/settings')
}

/**
 * Update one or more settings.
 * @param {Object} payload - Partial settings object (any keys from SettingsUpdateRequest)
 * @returns {Promise<{success, updated, settings}>}
 */
export function updateSettings(payload) {
  return api.put('/settings', payload)
}

/**
 * Test whether an API key (and optionally a specific model) is valid.
 * @param {string} provider - e.g. 'openrouter', 'google', 'openai', 'anthropic'
 * @param {string|null} apiKey - Plain text key to test; null = use stored key
 * @param {string|null} model  - When set, also verifies this model is accessible
 * @returns {Promise<{success, provider, message}>}
 */
export function testApiKey(provider, apiKey = null, model = null) {
  return api.post('/settings/test-key', {
    provider,
    ...(apiKey ? { api_key: apiKey } : {}),
    ...(model  ? { model }          : {}),
  })
}

/**
 * Fetch a provider's currently available model catalog.
 * @param {string} provider - currently supports 'openrouter' and 'fireworks'
 * @param {string|null} apiKey - Plain text key to test; null = use stored key
 * @returns {Promise<{success, provider, models, message}>}
 */
export function listProviderModels(provider, apiKey = null) {
  return api.post('/settings/models', {
    provider,
    ...(apiKey ? { api_key: apiKey } : {}),
  })
}
