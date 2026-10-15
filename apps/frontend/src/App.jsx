import React, { useState, useEffect, useCallback } from 'react';
import {
  Building2,
  MessageSquare,
  CheckSquare,
  Terminal,
  Minus,
  Plus,
  RotateCcw,
  LogOut,
  PanelLeftClose,
  PanelLeftOpen,
  Pin,
  PinOff,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Layers,
  HelpCircle,
  Users,
} from 'lucide-react';
import { LoginForm } from './components/auth/LoginForm.jsx';
import { ChatInbox } from './components/chat/ChatInbox.jsx';
import { MessageThread } from './components/chat/MessageThread.jsx';
import { AiDraftBox } from './components/chat/AiDraftBox.jsx';
import { TicketsTable } from './components/tables/TicketsTable.jsx';
import { ExpedientesTable } from './components/tables/ExpedientesTable.jsx';
import { DebugSimulator } from './components/debug/DebugSimulator.jsx';
import { FaqsManager } from './components/faqs/FaqsManager.jsx';
import { ConsorciosManager } from './components/consorcios/ConsorciosManager.jsx';
import { ContactosManager } from './components/contactos/ContactosManager.jsx';
import { Card, CardHeader, CardContent } from './components/ui/Card.jsx';
import { Badge } from './components/ui/Badge.jsx';
import { Button } from './components/ui/Button.jsx';
import { ApiService, formatDateTime } from './lib/api-client.js';

const INITIAL_CONSORCIOS = [
  {
    id: 'cons-corrientes-lavalle',
    nombre: 'Consorcio Corrientes y Lavalle (Torres, Cochera y Galería)',
    direccion: 'Av. Corrientes 1240 / Lavalle 1241, CABA',
    cuit: '30-71122334-5',
    cbu_bancario: '0140000000000000000001',
    alias_bancario: 'CONSORCIO.LAVALLE.OFICIAL',
    email_cobranzas: 'cobranzas.lavalle@selizadministraciones.com.ar',
    telefono_porteria: '+54 9 11 4371-0001',
    emergencia_ascensores: '+54 9 11 4444-1111',
    emergencia_plomeria: '+54 9 11 4444-2222',
    pautas_mudanza: 'Lunes a Viernes de 9 a 17 hs y Sábados de 9 a 13 hs. Presentar seguro flete 48hs antes.',
  },
  {
    id: 'cons-callao-2334',
    nombre: 'Consorcio Callao 2334',
    direccion: 'Av. Callao 2334, Recoleta, CABA',
    cuit: '30-71998877-6',
    cbu_bancario: '0140000000000000000002',
    alias_bancario: 'CALLAO.2334.EXPENSAS',
    email_cobranzas: 'callao2334@selizadministraciones.com.ar',
    telefono_porteria: '+54 9 11 4801-9999',
    emergencia_ascensores: '+54 9 11 4444-3333',
    emergencia_plomeria: '+54 9 11 4444-4444',
    pautas_mudanza: 'Lunes a Viernes de 10 a 16 hs exclusivamente.',
  },
];

const INITIAL_TICKETS = [
  {
    id: 'TICK-1042',
    rawId: 'tick-1042',
    consorcio: 'Consorcio Corrientes y Lavalle',
    unidad: 'Torre Corrientes 4° B',
    contacto: 'Carlos Méndez',
    intencion: 'RECLAMO',
    descripcion: 'Corte de luz en palier del piso 4 Torre Corrientes.',
    prioridad: 'ALTA',
    estado: 'EN_REVISION',
    creado_el: '13/10 18:42',
  },
  {
    id: 'TICK-1041',
    rawId: 'tick-1041',
    consorcio: 'Consorcio Callao 2334',
    unidad: '7° A',
    contacto: 'Lucía Rossi',
    intencion: 'EXPENSAS',
    descripcion: 'Consulta de CBU y datos de pago de expensas.',
    prioridad: 'NORMAL',
    estado: 'NUEVO',
    creado_el: '13/10 18:15',
  },
  {
    id: 'TICK-1040',
    rawId: 'tick-1040',
    consorcio: 'Consorcio Corrientes y Lavalle',
    unidad: 'Cochera 14',
    contacto: 'Mariano Gómez',
    intencion: 'EMERGENCIA',
    descripcion: 'Personas atrapadas en ascensor Torre Lavalle.',
    prioridad: 'CRITICA',
    estado: 'DERIVADO',
    creado_el: '13/10 17:50',
  },
];

const INITIAL_CONVERSATIONS = [
  {
    id: 'conv-1',
    senderName: 'Carlos Méndez',
    phone: '+5491144558899',
    consorcio: 'Torre Corrientes',
    unidad: '4° B (Propietario)',
    lastMessage: 'Hola, se cortó la luz en el palier del piso 4. ¿Podrán mandar al electricista?',
    timestamp: '18:42',
    unreadCount: 1,
    status: 'open',
  },
  {
    id: 'conv-2',
    senderName: 'Lucía Rossi',
    phone: '+5491166778899',
    consorcio: 'Callao 2334',
    unidad: '7° A (Inquilina)',
    lastMessage: 'Buenas tardes, me podrían confirmar el CBU para transferir las expensas?',
    timestamp: '18:15',
    unreadCount: 0,
    status: 'open',
  },
  {
    id: 'conv-3',
    senderName: 'Mariano Gómez',
    phone: '+5491133221100',
    consorcio: 'Torre Lavalle',
    unidad: 'Cochera 14 (Propietario)',
    lastMessage: 'Urgente, hay dos personas atrapadas en el ascensor!',
    timestamp: '17:50',
    unreadCount: 0,
    status: 'emergency',
  },
];

const INITIAL_MESSAGES = {
  'conv-1': [
    {
      id: 'm-1',
      sender: 'vecino',
      text: 'Hola, se cortó la luz en el palier del piso 4. ¿Podrán mandar al electricista?',
      timestamp: '18:42',
    },
  ],
  'conv-2': [
    {
      id: 'm-2',
      sender: 'vecino',
      text: 'Buenas tardes, me podrían confirmar el CBU para transferir las expensas?',
      timestamp: '18:15',
    },
  ],
  'conv-3': [
    {
      id: 'm-3',
      sender: 'vecino',
      text: 'Urgente, hay dos personas atrapadas en el ascensor!',
      timestamp: '17:50',
    },
    {
      id: 'm-4',
      sender: 'bot',
      text: 'Hola Mariano. Si estás ante una emergencia con riesgo en el edificio, por favor comunicate urgente con la guardia al +54 9 11 4444-1111 o con los servicios de auxilio (Bomberos 100 / SAME 107).\n\nDejamos asentado el aviso de forma prioritaria para la administración.',
      timestamp: '17:50',
    },
  ],
};

const INITIAL_DRAFTS = {
  'conv-1': {
    text:
      'Hola Carlos, ¿cómo estás? Tomamos conocimiento del corte de luz en el palier de Torre Corrientes.\n' +
      'El reclamo quedó registrado bajo el ticket #1042 y lo evaluamos a primera hora mañana a partir de las 10:00 hs con el electricista.',
    source: 'Asistente de Reclamos',
    confidence: 0.94,
  },
  'conv-2': {
    text:
      'Hola Lucía, te paso los datos para la transferencia de expensas de Callao 2334:\n\n' +
      '• CBU: 0140000000000000000002\n' +
      '• Alias: CALLAO.2334.EXPENSAS\n' +
      '• CUIT: 30-71998877-6\n\n' +
      'Una vez hecho el pago, envianos por favor el comprobante a callao2334@selizadministraciones.com.ar indicando tu unidad (7° A). Saludos.',
    source: 'Mesa de Cobranzas',
    confidence: 0.98,
  },
  'conv-3': null,
};

export default function App() {
  // Estado de Autenticación y Sesión
  const [currentUser, setCurrentUser] = useState(() => ApiService.getStoredUser());
  const [isAuthenticated, setIsAuthenticated] = useState(() => ApiService.isAuthenticated());

  useEffect(() => {
    const handleLogout = () => {
      setCurrentUser(null);
      setIsAuthenticated(false);
    };
    window.addEventListener('seliz_auth_logout', handleLogout);
    return () => window.removeEventListener('seliz_auth_logout', handleLogout);
  }, []);

  const [activeTab, setActiveTab] = useState('inbox');
  const [selectedConvId, setSelectedConvId] = useState('conv-1');
  const [mobileChatOpen, setMobileChatOpen] = useState(false);
  const [apiConnected, setApiConnected] = useState(false);

  // Ergonomía de Layout: Sidebar con Apertura por Proximidad y Minimizado
  const [sidebarPinned, setSidebarPinned] = useState(() => {
    try {
      const saved = localStorage.getItem('crm_sidebar_pinned');
      return saved !== null ? saved === 'true' : true;
    } catch {
      return true;
    }
  });
  const [sidebarHovered, setSidebarHovered] = useState(false);
  const [inboxListCollapsed, setInboxListCollapsed] = useState(false);
  const [draftCollapsed, setDraftCollapsed] = useState(false);

  const toggleSidebarPin = () => {
    setSidebarPinned((prev) => {
      const next = !prev;
      try { localStorage.setItem('crm_sidebar_pinned', String(next)); } catch {}
      return next;
    });
  };

  const isSidebarExpanded = sidebarPinned || sidebarHovered;

  // Estados dinámicos de backend
  const [consorcios, setConsorcios] = useState(INITIAL_CONSORCIOS);
  const [tickets, setTickets] = useState(INITIAL_TICKETS);
  const [expedientes, setExpedientes] = useState([]);
  const [loadingTickets, setLoadingTickets] = useState(false);
  const [loadingConsorcios, setLoadingConsorcios] = useState(false);
  const [loadingExpedientes, setLoadingExpedientes] = useState(false);

  // Estados dinámicos del Inbox Omnicanal
  const [conversations, setConversations] = useState(INITIAL_CONVERSATIONS);
  const [messagesByConv, setMessagesByConv] = useState(INITIAL_MESSAGES);
  const [aiDrafts, setAiDrafts] = useState(INITIAL_DRAFTS);
  const [generatingDraft, setGeneratingDraft] = useState(false);

  // Controlador de zoom con persistencia en localStorage
  const [zoomLevel, setZoomLevel] = useState(() => {
    try {
      const saved = localStorage.getItem('crm_zoom_level');
      return saved ? parseFloat(saved) : 1;
    } catch {
      return 1;
    }
  });

  const handleZoomIn = () => {
    setZoomLevel((prev) => {
      const next = Math.min(Number((prev + 0.05).toFixed(2)), 1.25);
      try { localStorage.setItem('crm_zoom_level', next.toString()); } catch {}
      return next;
    });
  };

  const handleZoomOut = () => {
    setZoomLevel((prev) => {
      const next = Math.max(Number((prev - 0.05).toFixed(2)), 0.8);
      try { localStorage.setItem('crm_zoom_level', next.toString()); } catch {}
      return next;
    });
  };

  const handleZoomReset = () => {
    setZoomLevel(1);
    try { localStorage.setItem('crm_zoom_level', '1'); } catch {}
  };

  // Carga de expedientes edilicios desde la API
  const loadExpedientes = useCallback(async () => {
    setLoadingExpedientes(true);
    try {
      const data = await ApiService.getExpedientes();
      if (Array.isArray(data)) {
        setExpedientes(data);
      }
    } catch (err) {
      console.warn('[CRM] No se pudo cargar expedientes del backend:', err.message);
    } finally {
      setLoadingExpedientes(false);
    }
  }, []);

  // Actualización de estado de un expediente
  const handleUpdateExpedienteStatus = async (expedienteId, newStatus) => {
    const original = [...expedientes];
    setExpedientes((prev) =>
      prev.map((e) => (e.id === expedienteId ? { ...e, estado: newStatus } : e))
    );
    try {
      const updated = await ApiService.updateExpediente(expedienteId, { estado: newStatus });
      setExpedientes((prev) =>
        prev.map((e) => (e.id === expedienteId ? updated : e))
      );
    } catch (err) {
      console.error('[CRM] Error al actualizar estado del expediente:', err);
      setExpedientes(original);
    }
  };

  // Notificar por WhatsApp a todos los vecinos del expediente
  const handleNotifyNeighbors = async (expedienteId, mensaje) => {
    return await ApiService.notificarVecinosExpediente(expedienteId, mensaje);
  };

  // Carga de tickets desde la API
  const loadTickets = useCallback(async () => {
    setLoadingTickets(true);
    try {
      const data = await ApiService.getTickets();
      if (Array.isArray(data) && data.length > 0) {
        setTickets(data);
      }
      setApiConnected(true);
    } catch (err) {
      console.warn('[CRM] No se pudo cargar tickets del backend, usando datos locales:', err.message);
    } finally {
      setLoadingTickets(false);
    }
  }, []);

  // Carga de consorcios desde la API
  const loadConsorcios = useCallback(async () => {
    setLoadingConsorcios(true);
    try {
      const data = await ApiService.getConsorcios();
      if (Array.isArray(data) && data.length > 0) {
        setConsorcios(data);
      }
      setApiConnected(true);
    } catch (err) {
      console.warn('[CRM] No se pudo cargar consorcios del backend, usando datos locales:', err.message);
    } finally {
      setLoadingConsorcios(false);
    }
  }, []);

  // Carga de conversaciones desde la API
  const loadConversaciones = useCallback(async () => {
    try {
      const data = await ApiService.getConversaciones();
      if (Array.isArray(data) && data.length > 0) {
        const formatted = data.map((c) => ({
          id: c.id,
          senderName: c.contacto?.nombre_completo || 'Vecino',
          phone: c.contacto?.telefono_wa || '',
          consorcio: c.consorcio?.nombre || 'Consorcio General',
          unidad: c.contacto?.unidad_funcional
            ? `${c.contacto.unidad_funcional} (${c.contacto.rol || 'PROPIETARIO'})`
            : 'Unidad S/E',
          lastMessage: c.ultimo_mensaje || 'Sin mensajes recientes',
          timestamp: c.ultimo_mensaje_el ? formatDateTime(c.ultimo_mensaje_el) : 'Reciente',
          unreadCount: c.no_leidos_count || 0,
          status: c.estado || 'open',
          botActive: c.bot_activo,
          etiquetas: c.etiquetas || [],
          raw: c,
        }));
        setConversations(formatted);
        setSelectedConvId((prev) => {
          if (!prev || !formatted.some((f) => f.id === prev)) {
            return formatted[0].id;
          }
          return prev;
        });
      }
    } catch (err) {
      console.warn('[CRM] No se pudieron cargar conversaciones del backend:', err.message);
    }
  }, []);

  // Carga de mensajes de la conversación seleccionada
  const loadMessagesForConversation = useCallback(async (convId) => {
    if (!convId) return;
    try {
      const msgs = await ApiService.getConversacionMessages(convId);
      if (Array.isArray(msgs)) {
        const formatted = msgs.map((m) => ({
          id: m.id,
          sender: m.enviado_por === 'agente' ? 'ivana' : m.enviado_por === 'bot' ? 'bot' : 'vecino',
          text: m.contenido,
          privado: m.privado,
          isPrivateNote: m.privado,
          tipo: m.tipo,
          timestamp: m.creado_el ? formatDateTime(m.creado_el) : '',
          agente_nombre: m.agente_nombre,
        }));
        setMessagesByConv((prev) => ({
          ...prev,
          [convId]: formatted,
        }));
      }
    } catch (err) {
      console.warn(`[CRM] No se pudieron cargar mensajes para ${convId}:`, err.message);
    }
  }, []);

  useEffect(() => {
    if (selectedConvId) {
      loadMessagesForConversation(selectedConvId);
    }
  }, [selectedConvId, loadMessagesForConversation]);

  // WebSocket y sincronización en tiempo real
  useEffect(() => {
    let ws = null;
    let reconnectTimeout = null;

    const connectWs = () => {
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = import.meta.env.VITE_API_URL
          ? import.meta.env.VITE_API_URL.replace(/^http(s)?:\/\//, '')
          : window.location.host;
        const wsUrl = `${protocol}//${host}/ws/conversaciones`;

        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          setApiConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'new_message') {
              const { conversacion_id } = data.data || {};
              if (conversacion_id && conversacion_id === selectedConvId) {
                loadMessagesForConversation(selectedConvId);
              }
              loadConversaciones();
            } else if (data.type === 'status_changed' || data.type === 'labels_updated') {
              loadConversaciones();
            }
          } catch {}
        };

        ws.onclose = () => {
          reconnectTimeout = setTimeout(connectWs, 5000);
        };

        ws.onerror = () => {
          ws.close();
        };
      } catch {
        reconnectTimeout = setTimeout(connectWs, 5000);
      }
    };

    connectWs();

    const pollInterval = setInterval(() => {
      loadConversaciones();
      if (selectedConvId) {
        loadMessagesForConversation(selectedConvId);
      }
    }, 6000);

    return () => {
      if (ws) ws.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      clearInterval(pollInterval);
    };
  }, [selectedConvId, loadConversaciones, loadMessagesForConversation]);

  // Actualización de estado de un ticket
  const handleUpdateTicketStatus = async (ticketId, newStatus) => {
    const originalTickets = [...tickets];
    setTickets((prev) =>
      prev.map((t) => (t.id === ticketId || t.rawId === ticketId ? { ...t, estado: newStatus } : t))
    );

    try {
      const updated = await ApiService.updateTicket(ticketId, { estado: newStatus });
      setTickets((prev) =>
        prev.map((t) => (t.id === ticketId || t.rawId === ticketId ? updated : t))
      );
    } catch (err) {
      console.error('[CRM] Error al actualizar estado del ticket:', err);
      setTickets(originalTickets);
    }
  };

  // Carga inicial al montar el componente
  useEffect(() => {
    async function init() {
      const health = await ApiService.checkHealth();
      if (health && health.status === 'ok') {
        setApiConnected(true);
      }
      await Promise.allSettled([loadExpedientes(), loadTickets(), loadConsorcios(), loadConversaciones()]);
    }
    init();
  }, [loadExpedientes, loadTickets, loadConsorcios, loadConversaciones]);

  const navigationItems = [
    { id: 'inbox', label: 'Inbox Omnicanal', icon: MessageSquare },
    { id: 'expedientes', label: 'Expedientes & Incidentes', icon: Layers },
    { id: 'tickets', label: 'Tickets & Reclamos', icon: CheckSquare },
    { id: 'faqs', label: 'Base de Conocimiento', icon: HelpCircle },
    { id: 'consorcios', label: 'Consorcios & Atributos', icon: Building2 },
    { id: 'contactos', label: 'Directorio de Contactos', icon: Users },
    { id: 'debug', label: 'Simulador de Atención', icon: Terminal },
  ];

  const currentConv = conversations.find((c) => c.id === selectedConvId) || conversations[0];
  const currentMessages = messagesByConv[selectedConvId] || [];
  const currentDraft = aiDrafts[selectedConvId];
  const activeLabel = navigationItems.find((item) => item.id === activeTab)?.label || 'Inbox';

  // 1. Envío de mensaje (WhatsApp oficial o Nota Interna)
  const handleSendMessage = async (text, isPrivate = false) => {
    if (!text.trim() || !selectedConvId) return;
    const now = new Date();
    const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

    const newMsg = {
      id: `m-${Date.now()}`,
      sender: 'ivana',
      text: text.trim(),
      privado: isPrivate,
      isPrivateNote: isPrivate,
      timestamp: timeStr,
    };

    setMessagesByConv((prev) => ({
      ...prev,
      [selectedConvId]: [...(prev[selectedConvId] || []), newMsg],
    }));

    setConversations((prev) =>
      prev.map((c) =>
        c.id === selectedConvId
          ? {
              ...c,
              lastMessage: isPrivate ? c.lastMessage : text.trim(),
              timestamp: timeStr,
              unreadCount: 0,
            }
          : c
      )
    );

    setAiDrafts((prev) => ({
      ...prev,
      [selectedConvId]: null,
    }));

    try {
      await ApiService.sendConversacionMessage(selectedConvId, text.trim(), isPrivate);
      await loadMessagesForConversation(selectedConvId);
      await loadConversaciones();
    } catch (err) {
      console.warn('[CRM] Envío de mensaje a backend falló:', err.message);
    }
  };

  // Actualización de estado de la conversación (open, pending, resolved)
  const handleUpdateConversationStatus = async (newStatus) => {
    if (!selectedConvId) return;
    setConversations((prev) =>
      prev.map((c) => (c.id === selectedConvId ? { ...c, status: newStatus } : c))
    );
    try {
      await ApiService.updateConversacionStatus(selectedConvId, newStatus);
      await loadConversaciones();
    } catch (err) {
      console.error('[CRM] Error al actualizar estado de conversación:', err);
    }
  };

  // Apertura directa de chat desde el Directorio de Contactos
  const handleOpenChatFromContacto = async (contacto) => {
    let targetConv = conversations.find(
      (c) => c.phone === contacto.telefono_wa || c.raw?.contacto_id === contacto.id
    );

    if (!targetConv) {
      try {
        const created = await ApiService.createConversacion({ contacto_id: contacto.id });
        if (created) {
          await loadConversaciones();
          targetConv = { id: created.id };
        }
      } catch (err) {
        console.warn('[CRM] No se pudo crear conversación para contacto:', err);
      }
    }

    if (targetConv) {
      setSelectedConvId(targetConv.id);
    }
    setActiveTab('inbox');
    setMobileChatOpen(true);
  };

  // 2. Aprobación y despacho de borrador sugerido por IA
  const handleApproveDraft = (text) => {
    handleSendMessage(text);
  };

  // 3. Generación bajo demanda de sugerencia de respuesta con IA
  const handleGenerateAiDraft = async () => {
    if (!currentConv) return;
    setGeneratingDraft(true);
    try {
      const lastNeighborMsg = [...currentMessages].reverse().find((m) => m.sender === 'vecino');
      const messageToAnalyze = lastNeighborMsg ? lastNeighborMsg.text : currentConv.lastMessage;

      const suggestion = await ApiService.generateAiSuggestion(
        messageToAnalyze,
        currentConv.phone,
        currentConv.senderName
      );

      if (suggestion && suggestion.text) {
        setAiDrafts((prev) => ({
          ...prev,
          [selectedConvId]: {
            text: suggestion.text,
            source: suggestion.intent || 'Sugerencia Automática',
            confidence: 0.96,
          },
        }));
      }

      if (suggestion?.ticketCreated) {
        await loadTickets();
      }
    } catch (err) {
      console.error('[CRM] Error al generar propuesta IA:', err);
    } finally {
      setGeneratingDraft(false);
    }
  };

  // 4. Simulación de mensaje entrante de vecino en tiempo real
  const handleSimulateNeighborMessage = async (text) => {
    if (!currentConv || !text.trim()) return;

    const now = new Date();
    const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

    const newNeighborMsg = {
      id: `m-${Date.now()}`,
      sender: 'vecino',
      text: text.trim(),
      timestamp: timeStr,
    };

    setMessagesByConv((prev) => ({
      ...prev,
      [selectedConvId]: [...(prev[selectedConvId] || []), newNeighborMsg],
    }));

    setConversations((prev) =>
      prev.map((c) =>
        c.id === selectedConvId
          ? {
              ...c,
              lastMessage: text.trim(),
              timestamp: timeStr,
              unreadCount: (c.unreadCount || 0) + 1,
            }
          : c
      )
    );

    // Procesar con el motor LangGraph en backend
    setGeneratingDraft(true);
    try {
      const suggestion = await ApiService.generateAiSuggestion(
        text.trim(),
        currentConv.phone,
        currentConv.senderName
      );

      if (suggestion && suggestion.text) {
        if (suggestion.isEmergency) {
          // Si es emergencia con riesgo, el bot emite respuesta automática prioritaria
          const botMsg = {
            id: `m-${Date.now() + 1}`,
            sender: 'bot',
            text: suggestion.text,
            timestamp: timeStr,
          };
          setMessagesByConv((prev) => ({
            ...prev,
            [selectedConvId]: [...(prev[selectedConvId] || []), botMsg],
          }));
          setConversations((prev) =>
            prev.map((c) =>
              c.id === selectedConvId ? { ...c, status: 'emergency' } : c
            )
          );
        } else {
          // Dejar propuesta como borrador para aprobación de la Dra. Ivana Seliz
          setAiDrafts((prev) => ({
            ...prev,
            [selectedConvId]: {
              text: suggestion.text,
              source: suggestion.intent || 'Sugerencia Automática',
              confidence: 0.95,
            },
          }));
        }
      }

      if (suggestion?.ticketCreated || suggestion?.isEmergency) {
        await loadTickets();
      }
    } catch (err) {
      console.warn('[CRM] Error al procesar mensaje simulado con IA:', err);
    } finally {
      setGeneratingDraft(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <LoginForm
        onLoginSuccess={(user) => {
          setCurrentUser(user);
          setIsAuthenticated(true);
        }}
      />
    );
  }

  const userInitials = currentUser?.nombre_completo
    ? currentUser.nombre_completo.split(' ').map((n) => n[0]).slice(0, 2).join('').toUpperCase()
    : 'IS';

  return (
    <div className="h-[100dvh] min-h-[100dvh] bg-surface-soft text-brand-ink flex flex-col lg:flex-row overflow-hidden">
      {/* Zona Sensora de Proximidad en Margen Izquierdo (Desktop) */}
      {!sidebarPinned && (
        <div
          onMouseEnter={() => setSidebarHovered(true)}
          className="fixed left-0 top-0 bottom-0 w-3 z-30 hidden lg:block cursor-pointer"
          aria-hidden="true"
        />
      )}

      {/* Sidebar Desktop con Soporte de Pin y Apertura por Proximidad */}
      <aside
        onMouseEnter={() => !sidebarPinned && setSidebarHovered(true)}
        onMouseLeave={() => !sidebarPinned && setSidebarHovered(false)}
        className={`fixed inset-y-0 left-0 hidden flex-col border-r border-border bg-white lg:flex transition-all duration-200 ease-in-out ${
          sidebarPinned
            ? 'w-64 xl:w-72 z-30 shadow-card'
            : isSidebarExpanded
            ? 'w-64 xl:w-72 z-40 shadow-2xl border-r-brand-ink/20'
            : 'w-[68px] z-30 shadow-sm'
        }`}
      >
        {/* Marca, Encabezado y Control Pin/Unpin */}
        <div className="flex min-h-14 sm:min-h-16 items-center justify-between border-b border-border px-3.5 xl:px-4">
          {isSidebarExpanded ? (
            <>
              <div className="min-w-0 flex items-center gap-2">
                <span className="text-sm font-bold tracking-tight text-brand-ink truncate">
                  Dra. Ivana Seliz
                </span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-brand-ink text-white shrink-0">
                  {currentUser?.rol || 'ADMIN'}
                </span>
              </div>
              <button
                type="button"
                onClick={toggleSidebarPin}
                title={sidebarPinned ? 'Desanclar (Apertura por proximidad)' : 'Fijar menú expandido'}
                className="size-7 rounded-base flex items-center justify-center text-text-muted hover:text-brand-ink hover:bg-surface-muted transition-colors cursor-pointer shrink-0"
              >
                {sidebarPinned ? <Pin size={14} className="rotate-45" /> : <PinOff size={14} />}
              </button>
            </>
          ) : (
            <div className="w-full flex items-center justify-center">
              <button
                type="button"
                onClick={toggleSidebarPin}
                title="Fijar menú expandido"
                className="size-9 rounded-base flex items-center justify-center text-text-muted hover:text-brand-ink hover:bg-surface-muted transition-colors cursor-pointer"
              >
                <PinOff size={16} />
              </button>
            </div>
          )}
        </div>

        {/* Navegación Principal */}
        <nav className="min-h-0 flex-1 overflow-y-auto px-2 py-4" aria-label="Secciones del CRM">
          {isSidebarExpanded && (
            <p className="mb-2 px-3 text-[11px] font-semibold tracking-wider uppercase text-text-muted">
              Gestión
            </p>
          )}
          <div className="grid gap-1">
            {navigationItems.map(({ id, label, icon: Icon }) => {
              const isActive = id === activeTab;
              return (
                <button
                  key={id}
                  onClick={() => {
                    setActiveTab(id);
                    if (id === 'inbox') setMobileChatOpen(false);
                  }}
                  title={!isSidebarExpanded ? label : undefined}
                  className={`flex min-h-10 w-full items-center rounded-base text-xs font-semibold transition-all cursor-pointer ${
                    isSidebarExpanded
                      ? 'gap-3 px-3 xl:text-sm'
                      : 'justify-center px-0'
                  } ${
                    isActive
                      ? 'bg-brand-ink text-white shadow-sm'
                      : 'text-text-secondary hover:bg-surface-muted hover:text-brand-ink'
                  }`}
                >
                  <Icon size={18} aria-hidden="true" className="shrink-0" />
                  {isSidebarExpanded && <span className="truncate">{label}</span>}
                </button>
              );
            })}
          </div>
        </nav>

        {/* Perfil en la Base con Botón de Logout */}
        <div className="border-t border-border p-2.5 bg-surface-soft/60">
          {isSidebarExpanded ? (
            <div className="flex items-center justify-between gap-2 px-1">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="grid size-8 shrink-0 place-items-center rounded-full bg-brand-ink text-white text-xs font-bold shadow-sm">
                  {userInitials}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-bold text-brand-ink truncate">
                    {currentUser?.nombre_completo || 'Dra. Ivana Seliz'}
                  </p>
                  <p className="text-[10px] text-text-secondary truncate">
                    {currentUser?.email || 'admin@selizadministraciones.com.ar'}
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => ApiService.logout()}
                title="Cerrar sesión segura"
                className="size-8 rounded-base flex items-center justify-center text-text-muted hover:text-danger hover:bg-danger-soft transition-colors cursor-pointer shrink-0"
              >
                <LogOut size={15} />
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2">
              <div
                title={currentUser?.nombre_completo || 'Dra. Ivana Seliz'}
                className="grid size-8 place-items-center rounded-full bg-brand-ink text-white text-xs font-bold shadow-sm cursor-default"
              >
                {userInitials}
              </div>
              <button
                type="button"
                onClick={() => ApiService.logout()}
                title="Cerrar sesión segura"
                className="size-8 rounded-base flex items-center justify-center text-text-muted hover:text-danger hover:bg-danger-soft transition-colors cursor-pointer"
              >
                <LogOut size={15} />
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* Contenedor Principal (con compensación de ancho según sidebarPinned) */}
      <div className={`flex-1 min-w-0 ${sidebarPinned ? 'lg:pl-64 xl:pl-72' : 'lg:pl-[68px]'} flex flex-col h-[100dvh] overflow-hidden transition-all duration-200`}>
        {/* Barra Superior Minimalista */}
        <header className="sticky top-0 z-20 flex min-h-12 sm:min-h-14 items-center justify-between border-b border-border/80 bg-white/95 px-3 sm:px-5 lg:px-6 backdrop-blur shrink-0">
          <div className="flex items-center gap-2 sm:gap-3 min-w-0">
            {/* Branding Móvil */}
            <div className="lg:hidden flex items-center gap-1.5 shrink-0">
              <span className="text-xs sm:text-sm font-bold tracking-tight text-brand-ink">
                Dra. Ivana Seliz
              </span>
              <span className="text-text-muted text-xs">/</span>
            </div>

            {/* Breadcrumb */}
            <div className="min-w-0 flex items-center gap-1 text-xs sm:text-sm text-text-secondary font-medium">
              <span className="font-semibold text-brand-ink hidden sm:inline">Consorcios /</span>
              <span className="truncate font-semibold text-brand-ink">{activeLabel}</span>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            {/* Indicador de conexión en móvil / tablet */}
            <div className="flex lg:hidden items-center gap-1.5 px-2 py-0.5 rounded-full border border-border/70 text-[10px] text-text-secondary bg-surface-muted/50">
              <span className={`size-1.5 rounded-full ${apiConnected ? 'bg-success' : 'bg-text-muted'}`} />
              <span>{apiConnected ? 'En línea' : 'Desconectado'}</span>
            </div>

            {/* Controlador de Zoom Minimalista */}
            <div className="flex items-center gap-0.5 rounded-full border border-border/80 bg-surface-muted/60 p-0.5 text-xs">
              <button
                type="button"
                onClick={handleZoomOut}
                disabled={zoomLevel <= 0.8}
                aria-label="Reducir zoom"
                className="size-6 sm:size-7 rounded-full flex items-center justify-center text-text-secondary hover:text-brand-ink hover:bg-white transition-colors disabled:opacity-30 disabled:pointer-events-none cursor-pointer"
                title="Reducir zoom (-)"
              >
                <Minus className="w-3 h-3 sm:w-3.5 sm:h-3.5" />
              </button>
              <button
                type="button"
                onClick={handleZoomReset}
                aria-label="Restablecer zoom al 100%"
                className="px-1.5 py-0.5 text-[10px] sm:text-[11px] font-semibold text-brand-ink hover:text-black transition-colors cursor-pointer select-none"
                title="Click para restablecer zoom al 100%"
              >
                {Math.round(zoomLevel * 100)}%
              </button>
              <button
                type="button"
                onClick={handleZoomIn}
                disabled={zoomLevel >= 1.25}
                aria-label="Aumentar zoom"
                className="size-6 sm:size-7 rounded-full flex items-center justify-center text-text-secondary hover:text-brand-ink hover:bg-white transition-colors disabled:opacity-30 disabled:pointer-events-none cursor-pointer"
                title="Aumentar zoom (+)"
              >
                <Plus className="w-3 h-3 sm:w-3.5 sm:h-3.5" />
              </button>
            </div>

            {/* Logout en Móvil */}
            <button
              type="button"
              onClick={() => ApiService.logout()}
              title="Cerrar sesión"
              className="lg:hidden size-7 rounded-full flex items-center justify-center text-text-muted hover:text-danger hover:bg-danger-soft transition-colors cursor-pointer"
            >
              <LogOut size={14} />
            </button>
          </div>
        </header>

        {/* Área de Contenido Dinámico con Zoom */}
        <main
          style={{ zoom: zoomLevel }}
          className="flex-1 overflow-hidden p-2 sm:p-3 md:p-3.5 lg:p-4 pb-20 lg:pb-4"
        >
          {activeTab === 'inbox' && (
            <Card className="h-full flex overflow-hidden border border-border/80 bg-white shadow-subtle">
              {/* Columna Izquierda: Inbox (Master view en móvil, colapsable en desktop) */}
              <div
                className={`${
                  mobileChatOpen ? 'hidden md:flex' : 'flex'
                } ${
                  inboxListCollapsed ? 'hidden' : 'w-full md:w-[38%] lg:w-[32%] xl:w-[28%] min-w-[260px] max-w-[380px]'
                } h-full overflow-hidden shrink-0 flex-col transition-all duration-200`}
              >
                <ChatInbox
                  conversations={conversations}
                  selectedId={selectedConvId}
                  onSelect={(id) => {
                    setSelectedConvId(id);
                    setMobileChatOpen(true);
                  }}
                />
              </div>

              {/* Columna Derecha: Hilo de Mensajes & Borrador IA (Detail view en móvil, expandible al 100%) */}
              <div
                className={`${
                  mobileChatOpen ? 'flex' : 'hidden md:flex'
                } flex-1 h-full flex flex-col overflow-hidden bg-surface-soft min-w-0`}
              >
                <div className="flex-1 overflow-hidden min-w-0">
                  <MessageThread
                    conversationId={currentConv?.id}
                    senderName={currentConv?.senderName}
                    phone={currentConv?.phone}
                    consorcio={currentConv?.consorcio}
                    unidad={currentConv?.unidad}
                    status={currentConv?.status || 'open'}
                    botActive={currentConv?.botActive !== false}
                    messages={currentMessages}
                    onSendMessage={handleSendMessage}
                    onUpdateStatus={handleUpdateConversationStatus}
                    onGenerateAiDraft={handleGenerateAiDraft}
                    generatingDraft={generatingDraft}
                    onBack={() => setMobileChatOpen(false)}
                    inboxListCollapsed={inboxListCollapsed}
                    onToggleInboxList={() => setInboxListCollapsed((prev) => !prev)}
                  />
                </div>

                {/* Panel de Borrador IA Minimizable */}
                {currentDraft && (
                  <div className="border-t border-border bg-white shrink-0 transition-all duration-200">
                    <div
                      onClick={() => setDraftCollapsed((prev) => !prev)}
                      className="flex items-center justify-between px-3 sm:px-4 py-2 bg-surface-muted/70 hover:bg-surface-muted border-b border-border/60 text-xs font-semibold text-brand-ink cursor-pointer select-none transition-colors"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <Sparkles size={14} className="text-brand-ink shrink-0" />
                        <span className="truncate">Sugerencia inteligente de respuesta (IA)</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-text-secondary text-[11px] font-medium shrink-0">
                        <span>{draftCollapsed ? 'Desplegar borrador' : 'Minimizar'}</span>
                        {draftCollapsed ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      </div>
                    </div>

                    {!draftCollapsed && (
                      <div className="p-2.5 sm:p-3.5">
                        <AiDraftBox
                          key={currentDraft.text}
                          initialDraft={currentDraft.text}
                          onApprove={handleApproveDraft}
                          onReject={() =>
                            setAiDrafts({
                              ...aiDrafts,
                              [selectedConvId]: null,
                            })
                          }
                        />
                      </div>
                    )}
                  </div>
                )}
              </div>
            </Card>
          )}

          {activeTab === 'expedientes' && (
            <div className="h-full overflow-y-auto">
              <ExpedientesTable
                expedientes={expedientes}
                loading={loadingExpedientes}
                onRefresh={loadExpedientes}
                onUpdateStatus={handleUpdateExpedienteStatus}
                onNotifyNeighbors={handleNotifyNeighbors}
              />
            </div>
          )}

          {activeTab === 'tickets' && (
            <div className="h-full overflow-y-auto">
              <TicketsTable
                tickets={tickets}
                loading={loadingTickets}
                onRefresh={loadTickets}
                onUpdateStatus={handleUpdateTicketStatus}
              />
            </div>
          )}

          {activeTab === 'faqs' && (
            <div className="h-full overflow-hidden">
              <FaqsManager consorcios={consorcios} />
            </div>
          )}

          {activeTab === 'consorcios' && (
            <div className="h-full overflow-hidden">
              <ConsorciosManager
                consorcios={consorcios}
                onRefreshParent={loadConsorcios}
              />
            </div>
          )}

          {activeTab === 'contactos' && (
            <div className="h-full overflow-hidden">
              <ContactosManager
                consorcios={consorcios}
                onOpenChat={handleOpenChatFromContacto}
              />
            </div>
          )}

          {activeTab === 'debug' && (
            <div className="h-full overflow-hidden">
              <DebugSimulator />
            </div>
          )}
        </main>
      </div>

      {/* Barra de Navegación Inferior Fija para Móviles y Tablets */}
      <nav className="fixed bottom-0 inset-x-0 z-30 flex items-center justify-around border-t border-border bg-white/95 px-2 py-1 backdrop-blur lg:hidden pb-safe">
        {navigationItems.map(({ id, label, icon: Icon }) => {
          const isActive = id === activeTab;
          return (
            <button
              key={id}
              onClick={() => {
                setActiveTab(id);
                if (id === 'inbox') setMobileChatOpen(false);
              }}
              className={`flex flex-col items-center justify-center gap-1 min-h-[44px] flex-1 rounded-base px-1 py-1 text-[11px] font-semibold transition-all cursor-pointer ${
                isActive
                  ? 'text-brand-ink font-bold'
                  : 'text-text-secondary hover:text-brand-ink'
              }`}
            >
              <Icon size={19} className={isActive ? 'text-brand-ink stroke-[2.5]' : 'text-text-muted'} />
              <span className="truncate max-w-[76px]">{label.split(' ')[0]}</span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}
