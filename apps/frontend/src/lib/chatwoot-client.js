import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const CHATWOOT_BASE_URL = import.meta.env.VITE_CHATWOOT_URL || API_BASE_URL
const CHATWOOT_API_TOKEN = import.meta.env.VITE_CHATWOOT_API_TOKEN || ''
const ACCOUNT_ID = import.meta.env.VITE_CHATWOOT_ACCOUNT_ID || '1'
const CHATWOOT_TIMEOUT_MS = parseInt(import.meta.env.VITE_CHATWOOT_TIMEOUT_MS || '90000', 10)

export const chatwootApi = axios.create({
  baseURL: `${CHATWOOT_BASE_URL}/api/v1/accounts/${ACCOUNT_ID}`,
  headers: {
    api_access_token: CHATWOOT_API_TOKEN,
    'Content-Type': 'application/json',
  },
  timeout: CHATWOOT_TIMEOUT_MS,
})

export const ChatwootService = {
  async getConversations(status = 'open') {
    try {
      const response = await chatwootApi.get(`/conversations?status=${status}`)
      return response.data?.data?.payload || []
    } catch (error) {
      console.error('Error al obtener conversaciones de Chatwoot:', error)
      return []
    }
  },

  async getMessages(conversationId) {
    try {
      const response = await chatwootApi.get(`/conversations/${conversationId}/messages`)
      return response.data?.payload || []
    } catch (error) {
      console.error(`Error al obtener mensajes para conversación ${conversationId}:`, error)
      return []
    }
  },

  async sendMessage(conversationId, content, isPrivate = false) {
    return chatwootApi.post(`/conversations/${conversationId}/messages`, {
      content,
      private: isPrivate,
    })
  },

  async toggleStatus(conversationId, status) {
    return chatwootApi.post(`/conversations/${conversationId}/toggle_status`, {
      status,
    })
  },
}
