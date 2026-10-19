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
  async login(email, password, pin = null) {
    const payload = { email, password };
    if (pin) payload.pin = pin;
    const res = await apiClient.post('/api/v1/auth/login', payload);

    if (res.data?.requires_pin) {
      return {
        requires_pin: true,
        temp_token: res.data.temp_token,
        user_email: res.data.user_email,
        user_nombre: res.data.user_nombre,
      };
    }

    const { access_token, user } = res.data;
    try {
      localStorage.setItem('seliz_auth_token', access_token);
      localStorage.setItem('seliz_user', JSON.stringify(user));
    } catch {}
    return { token: access_token, user };
  },

  async verifyPin(temp_token, pin) {
    const res = await apiClient.post('/api/v1/auth/verify-pin', { temp_token, pin });
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

  // ==========================================
  // CONVERSACIONES & INBOX OMNICANAL
  // ==========================================
  async getConversaciones(filters = {}) {
    const res = await apiClient.get('/api/v1/conversaciones', { params: filters });
    return res.data || [];
  },

  async createConversacion(data) {
    const res = await apiClient.post('/api/v1/conversaciones', data);
    return res.data;
  },

  async getConversacion(id) {
    const res = await apiClient.get(`/api/v1/conversaciones/${id}`);
    return res.data;
  },

  async getConversacionMessages(id, params = {}) {
    const res = await apiClient.get(`/api/v1/conversaciones/${id}/messages`, { params });
    return res.data || [];
  },

  async sendConversacionMessage(id, content, isPrivate = false) {
    const res = await apiClient.post(`/api/v1/conversaciones/${id}/messages`, {
      contenido: content,
      privado: isPrivate,
    });
    return res.data;
  },

  async updateConversacionStatus(id, nuevoEstado) {
    const res = await apiClient.patch(`/api/v1/conversaciones/${id}/status`, null, {
      params: { nuevo_estado: nuevoEstado },
    });
    return res.data;
  },

  async assignConversacion(id, agenteId = null) {
    const res = await apiClient.patch(`/api/v1/conversaciones/${id}/assign`, null, {
      params: { agente_id: agenteId },
    });
    return res.data;
  },

  async updateConversacionLabels(id, labels = []) {
    const res = await apiClient.post(`/api/v1/conversaciones/${id}/labels`, labels);
    return res.data;
  },

  async markConversacionRead(id) {
    const res = await apiClient.post(`/api/v1/conversaciones/${id}/read`);
    return res.data;
  },

  async getLabels() {
    const res = await apiClient.get('/api/v1/conversaciones/labels/all');
    return res.data || [];
  },

  async createLabel(data) {
    const res = await apiClient.post('/api/v1/conversaciones/labels/create', data);
    return res.data;
  },

  // ==========================================
  // FAQS & BASE DE CONOCIMIENTO
  // ==========================================
  async getFaqs(filters = {}) {
    const res = await apiClient.get('/api/v1/faqs', { params: filters });
    return res.data || [];
  },

  async getFaq(id) {
    const res = await apiClient.get(`/api/v1/faqs/${id}`);
    return res.data;
  },

  async createFaq(data) {
    const res = await apiClient.post('/api/v1/faqs', data);
    return res.data;
  },

  async updateFaq(id, data) {
    const res = await apiClient.put(`/api/v1/faqs/${id}`, data);
    return res.data;
  },

  async toggleFaq(id) {
    const res = await apiClient.patch(`/api/v1/faqs/${id}/toggle`);
    return res.data;
  },

  async deleteFaq(id) {
    await apiClient.delete(`/api/v1/faqs/${id}`);
    return true;
  },

  // ==========================================
  // CONSORCIOS & ATRIBUTOS DINÁMICOS
  // ==========================================
  async getConsorcios() {
    const res = await apiClient.get('/api/v1/consorcios');
    return res.data || [];
  },

  async getConsorcio(id) {
    const res = await apiClient.get(`/api/v1/consorcios/${id}`);
    return res.data;
  },

  async createConsorcio(data) {
    const res = await apiClient.post('/api/v1/consorcios', data);
    return res.data;
  },

  async updateConsorcio(id, data) {
    const res = await apiClient.put(`/api/v1/consorcios/${id}`, data);
    return res.data;
  },

  async deleteConsorcio(id) {
    await apiClient.delete(`/api/v1/consorcios/${id}`);
    return true;
  },

  async getAtributos(consorcioId) {
    const res = await apiClient.get(`/api/v1/consorcios/${consorcioId}/atributos`);
    return res.data || [];
  },

  async createAtributo(consorcioId, data) {
    const res = await apiClient.post(`/api/v1/consorcios/${consorcioId}/atributos`, data);
    return res.data;
  },

  async updateAtributo(consorcioId, attrId, data) {
    const res = await apiClient.put(`/api/v1/consorcios/${consorcioId}/atributos/${attrId}`, data);
    return res.data;
  },

  async deleteAtributo(consorcioId, attrId) {
    await apiClient.delete(`/api/v1/consorcios/${consorcioId}/atributos/${attrId}`);
    return true;
  },

  // ==========================================
  // DIRECTORIO DE CONTACTOS
  // ==========================================
  async getContactos(filters = {}) {
    const res = await apiClient.get('/api/v1/contactos', { params: filters });
    return res.data || [];
  },

  async getContacto(id) {
    const res = await apiClient.get(`/api/v1/contactos/${id}`);
    return res.data;
  },

  async createContacto(data) {
    const res = await apiClient.post('/api/v1/contactos', data);
    return res.data;
  },

  async updateContacto(id, data) {
    const res = await apiClient.put(`/api/v1/contactos/${id}`, data);
    return res.data;
  },

  async deleteContacto(id) {
    await apiClient.delete(`/api/v1/contactos/${id}`);
    return true;
  },
};
