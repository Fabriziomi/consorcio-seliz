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

// Interceptor para inyectar token JWT automáticamente
apiClient.interceptors.request.use((config) => {
  try {
    const token = localStorage.getItem('seliz_auth_token');
    if (token && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  } catch {}
  return config;
});

// Interceptor de respuesta para manejar tokens expirados (401)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const isLoginRequest = error.config?.url?.includes('/api/v1/auth/login');
      if (!isLoginRequest) {
        try {
          localStorage.removeItem('seliz_auth_token');
          localStorage.removeItem('seliz_user');
          window.dispatchEvent(new Event('seliz_auth_logout'));
        } catch {}
      }
    }
    return Promise.reject(error);
  }
);

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
    expediente_id: t.expediente_id,
    expediente_codigo: t.expediente_codigo,
    creado_el: formatDateTime(t.creado_el),
    raw_creado_el: t.creado_el,
  };
}

/**
 * Normaliza un expediente edilicio de la API
 */
export function normalizeExpediente(exp) {
  if (!exp) return null;
  return {
    ...exp,
    id: exp.id,
    codigo: exp.codigo || exp.id,
    consorcio: exp.consorcio_nombre || 'Consorcio General',
    consorcio_id: exp.consorcio_id,
    titulo: exp.titulo || 'Incidencia General',
    categoria: exp.categoria || 'OTRO',
    prioridad: exp.prioridad || 'NORMAL',
    estado: exp.estado || 'ABIERTO',
    descripcion: exp.descripcion_consolidada || '',
    proveedor: exp.proveedor_asignado || 'Sin asignar',
    ticketsCount: exp.tickets_count || (exp.tickets ? exp.tickets.length : 0),
    tickets: (exp.tickets || []).map(normalizeTicket),
    creado_el: formatDateTime(exp.creado_el),
    actualizado_el: formatDateTime(exp.actualizado_el),
    resuelto_el: exp.resuelto_el ? formatDateTime(exp.resuelto_el) : null,
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
   * Obtiene la lista de expedientes edilicios
   */
  async getExpedientes(params = {}) {
    const res = await apiClient.get('/api/v1/expedientes/', { params });
    const list = res.data || [];
    return list.map(normalizeExpediente);
  },

  /**
   * Obtiene el detalle de un expediente con sus tickets vinculados
   */
  async getExpediente(expedienteId) {
    const res = await apiClient.get(`/api/v1/expedientes/${expedienteId}`);
    return normalizeExpediente(res.data);
  },

  /**
   * Actualiza el estado o notas de un expediente
   */
  async updateExpediente(expedienteId, data) {
    const res = await apiClient.patch(`/api/v1/expedientes/${expedienteId}`, data);
    return normalizeExpediente(res.data);
  },

  /**
   * Envía una notificación por WhatsApp a todos los vecinos del expediente
   */
  async notificarVecinosExpediente(expedienteId, mensaje) {
    const res = await apiClient.post(`/api/v1/expedientes/${expedienteId}/notificar-vecinos`, { mensaje });
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

  /**
   * Métodos de Autenticación y Control de Sesión
   */
  async login(email, password) {
    const res = await apiClient.post('/api/v1/auth/login', { email, password });
    const { access_token, user } = res.data;
    try {
      localStorage.setItem('seliz_auth_token', access_token);
      localStorage.setItem('seliz_user', JSON.stringify(user));
    } catch {}
    return { token: access_token, user };
  },

  async getMe() {
    const res = await apiClient.get('/api/v1/auth/me');
    return res.data;
  },

  async getUsuarios() {
    const res = await apiClient.get('/api/v1/auth/usuarios');
    return res.data || [];
  },

  async createUsuario(data) {
    const res = await apiClient.post('/api/v1/auth/usuarios', data);
    return res.data;
  },

  logout() {
    try {
      localStorage.removeItem('seliz_auth_token');
      localStorage.removeItem('seliz_user');
      window.dispatchEvent(new Event('seliz_auth_logout'));
    } catch {}
  },

  getStoredUser() {
    try {
      const u = localStorage.getItem('seliz_user');
      return u ? JSON.parse(u) : null;
    } catch {
      return null;
    }
  },

  isAuthenticated() {
    try {
      return !!localStorage.getItem('seliz_auth_token');
    } catch {
      return false;
    }
  },
};
