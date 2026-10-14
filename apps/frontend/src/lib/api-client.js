import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
// Timeout amplio (90 segundos por defecto) pensado para servidores VPS con latencia de red o procesos de IA
const API_TIMEOUT_MS = parseInt(import.meta.env.VITE_API_TIMEOUT_MS || '90000', 10);

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: API_TIMEOUT_MS,
});

/**
 * Formatea fechas ISO a un formato legible y conciso: "13/10 18:42"
 */
export function formatDateTime(isoString) {
  if (!isoString) return '';
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    return `${day}/${month} ${hours}:${minutes}`;
  } catch {
    return isoString;
  }
}

/**
 * Normaliza un ticket de la API para garantizar compatibilidad con la UI
 */
export function normalizeTicket(t) {
  if (!t) return null;
  return {
    ...t,
    id: t.id ? t.id.toUpperCase() : '',
    rawId: t.id,
    consorcio: t.consorcio_nombre || t.consorcio || 'Consorcio General',
    contacto: t.contacto_nombre || t.contacto || 'Vecino No Identificado',
    unidad: t.contacto_unidad || t.unidad || 'Unidad S/E',
    descripcion: t.descripcion || '',
    prioridad: t.prioridad || 'NORMAL',
    estado: t.estado || 'NUEVO',
    intencion: t.intencion || 'CONSULTA',
    creado_el: formatDateTime(t.creado_el),
    raw_creado_el: t.creado_el,
  };
}

export const ApiService = {
  /**
   * Health check del backend
   */
  async checkHealth() {
    try {
      const res = await apiClient.get('/health');
      return res.data;
    } catch (err) {
      console.warn('[API] Health check falló o backend desconectado:', err.message);
      return null;
    }
  },

  /**
   * Obtiene la lista de consorcios activos
   */
  async getConsorcios() {
    const res = await apiClient.get('/api/v1/consorcios/');
    return res.data || [];
  },

  /**
   * Obtiene detalle de un consorcio
   */
  async getConsorcio(consorcioId) {
    const res = await apiClient.get(`/api/v1/consorcios/${consorcioId}`);
    return res.data;
  },

  /**
   * Obtiene la lista de tickets con filtros opcionales
   */
  async getTickets(params = {}) {
    const res = await apiClient.get('/api/v1/tickets/', { params });
    const list = res.data || [];
    return list.map(normalizeTicket);
  },

  /**
   * Obtiene el detalle de un ticket
   */
  async getTicket(ticketId) {
    const res = await apiClient.get(`/api/v1/tickets/${ticketId.toLowerCase()}`);
    return normalizeTicket(res.data);
  },

  /**
   * Actualiza el estado o atributos de un ticket
   */
  async updateTicket(ticketId, data) {
    const res = await apiClient.patch(`/api/v1/tickets/${ticketId.toLowerCase()}`, data);
    return normalizeTicket(res.data);
  },

  /**
   * Crea un nuevo ticket
   */
  async createTicket(payload) {
    const res = await apiClient.post('/api/v1/tickets/', payload);
    return normalizeTicket(res.data);
  },

  /**
   * Obtiene la lista de contactos de vecinos
   */
  async getContactos(params = {}) {
    const res = await apiClient.get('/api/v1/contactos/', { params });
    return res.data || [];
  },

  /**
   * Obtiene detalle de un contacto
   */
  async getContacto(contactoId) {
    const res = await apiClient.get(`/api/v1/contactos/${contactoId}`);
    return res.data;
  },

  /**
   * Genera una sugerencia de borrador con IA para una conversación
   */
  async generateAiSuggestion(message, phone, userName) {
    const res = await this.simulateChat({
      message,
      phone,
      user_name: userName,
    });
    return {
      text: res.response_text,
      intent: res.intent,
      isEmergency: res.is_emergency,
      ticketCreated: res.ticket_created,
      raw: res,
    };
  },

  /**
   * Ejecuta el simulador de chat / TEV1 router
   */
  async simulateChat(payload) {
    const res = await apiClient.post('/api/v1/debug/chat', payload);
    return res.data;
  },

  /**
   * Consulta el estado de takeover humano para un número
   */
  async getTakeoverStatus(phone) {
    const res = await apiClient.get(`/api/v1/takeover/${encodeURIComponent(phone)}/status`);
    return res.data;
  },

  /**
   * Activa el silencio/takeover humano para pausar el bot
   */
  async lockTakeover(phone, durationSeconds = 43200) {
    const res = await apiClient.post(`/api/v1/takeover/${encodeURIComponent(phone)}/lock`, null, {
      params: { duration_seconds: durationSeconds },
    });
    return res.data;
  },

  /**
   * Reactiva las respuestas automáticas del bot
   */
  async releaseTakeover(phone) {
    const res = await apiClient.post(`/api/v1/takeover/${encodeURIComponent(phone)}/release`);
    return res.data;
  },
};
