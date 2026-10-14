import React, { useState, useEffect, useCallback } from 'react';
import {
  Building2,
  MessageSquare,
  CheckSquare,
  Terminal,
  Minus,
  Plus,
  RotateCcw,
} from 'lucide-react';
import { ChatInbox } from './components/chat/ChatInbox.jsx';
import { MessageThread } from './components/chat/MessageThread.jsx';
import { AiDraftBox } from './components/chat/AiDraftBox.jsx';
import { TicketsTable } from './components/tables/TicketsTable.jsx';
import { DebugSimulator } from './components/debug/DebugSimulator.jsx';
import { Card, CardHeader, CardContent } from './components/ui/Card.jsx';
import { Badge } from './components/ui/Badge.jsx';
import { Button } from './components/ui/Button.jsx';
import { ApiService } from './lib/api-client.js';
import { ChatwootService } from './lib/chatwoot-client.js';

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
    source: 'LangGraph Reclamos',
    confidence: 0.94,
  },
  'conv-2': {
    text:
      'Hola Lucía, te paso los datos para la transferencia de expensas de Callao 2334:\n\n' +
      '• CBU: 0140000000000000000002\n' +
      '• Alias: CALLAO.2334.EXPENSAS\n' +
      '• CUIT: 30-71998877-6\n\n' +
      'Una vez hecho el pago, envianos por favor el comprobante a callao2334@selizadministraciones.com.ar indicando tu unidad (7° A). Saludos.',
    source: 'Tev1 Router (Cobranzas)',
    confidence: 0.98,
  },
  'conv-3': null,
};

export default function App() {
  const [activeTab, setActiveTab] = useState('inbox');
  const [selectedConvId, setSelectedConvId] = useState('conv-1');
  const [mobileChatOpen, setMobileChatOpen] = useState(false);
  const [apiConnected, setApiConnected] = useState(false);

  // Estados dinámicos de backend
  const [consorcios, setConsorcios] = useState(INITIAL_CONSORCIOS);
  const [tickets, setTickets] = useState(INITIAL_TICKETS);
  const [loadingTickets, setLoadingTickets] = useState(false);
  const [loadingConsorcios, setLoadingConsorcios] = useState(false);

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

  // Carga y sincronización de contactos desde la API
  const loadContactos = useCallback(async () => {
    try {
      const contactosList = await ApiService.getContactos();
      if (Array.isArray(contactosList) && contactosList.length > 0) {
        // Enriquecer conversaciones con datos oficiales de la base de datos
        setConversations((prev) => {
          const map = new Map(prev.map((c) => [c.phone, c]));
          contactosList.forEach((cont) => {
            if (map.has(cont.telefono_wa)) {
              const existing = map.get(cont.telefono_wa);
              map.set(cont.telefono_wa, {
                ...existing,
                senderName: cont.nombre_completo || existing.senderName,
                consorcio: cont.consorcio_nombre || existing.consorcio,
                unidad: `${cont.unidad_funcional || ''} (${cont.rol || ''})`.trim() || existing.unidad,
              });
            } else {
              const newId = `conv-${cont.id}`;
              map.set(cont.telefono_wa, {
                id: newId,
                senderName: cont.nombre_completo || 'Vecino',
                phone: cont.telefono_wa,
                consorcio: cont.consorcio_nombre || 'Consorcio General',
                unidad: cont.unidad_funcional || 'Unidad S/E',
                lastMessage: 'Sin mensajes recientes',
                timestamp: 'Reciente',
                unreadCount: 0,
                status: 'open',
              });
            }
          });
          return Array.from(map.values());
        });
      }
    } catch (err) {
      console.warn('[CRM] No se pudieron sincronizar contactos con backend:', err.message);
    }
  }, []);

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
      await Promise.allSettled([loadTickets(), loadConsorcios(), loadContactos()]);
    }
    init();
  }, [loadTickets, loadConsorcios, loadContactos]);

  const navigationItems = [
    { id: 'inbox', label: 'Inbox Omnicanal', icon: MessageSquare },
    { id: 'tickets', label: 'Tickets & Reclamos', icon: CheckSquare },
    { id: 'consorcios', label: 'Consorcios & CBU', icon: Building2 },
    { id: 'debug', label: 'Simulador Debug', icon: Terminal },
  ];

  const currentConv = conversations.find((c) => c.id === selectedConvId) || conversations[0];
  const currentMessages = messagesByConv[selectedConvId] || [];
  const currentDraft = aiDrafts[selectedConvId];
  const activeLabel = navigationItems.find((item) => item.id === activeTab)?.label || 'Inbox';

  // 1. Envío de mensaje en representación de la administración (Dra. Ivana Seliz)
  const handleSendMessage = async (text) => {
    if (!text.trim()) return;
    const now = new Date();
    const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

    const newMsg = {
      id: `m-${Date.now()}`,
      sender: 'ivana',
      text: text.trim(),
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
              lastMessage: text.trim(),
              timestamp: timeStr,
              unreadCount: 0,
            }
          : c
      )
    );

    // Limpiar borrador de IA si estaba abierto
    setAiDrafts((prev) => ({
      ...prev,
      [selectedConvId]: null,
    }));

    // Bloquear bot (Takeover humano) para este contacto automáticamente
    if (currentConv?.phone) {
      try {
        await ApiService.lockTakeover(currentConv.phone);
      } catch (err) {
        console.warn('[CRM] No se pudo activar takeover en backend:', err.message);
      }
    }

    // Integración opcional con Chatwoot
    try {
      if (import.meta.env.VITE_CHATWOOT_API_TOKEN) {
        await ChatwootService.sendMessage(selectedConvId, text.trim(), false);
      }
    } catch (err) {
      console.warn('[CRM] Envío opcional a Chatwoot no completado:', err.message);
    }
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
            source: suggestion.intent || 'LangGraph IA',
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
              source: suggestion.intent || 'LangGraph Engine',
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

  return (
    <div className="h-[100dvh] min-h-[100dvh] bg-surface-soft text-brand-ink flex flex-col lg:flex-row overflow-hidden">
      {/* Sidebar Fijo para Desktop y Laptops Grandes */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 xl:w-72 flex-col border-r border-border bg-white shadow-card lg:flex">
        {/* Marca y Encabezado */}
        <div className="flex min-h-16 xl:min-h-20 items-center justify-between border-b border-border px-5 xl:px-6">
          <span className="text-sm font-bold tracking-tight text-brand-ink">
            Dra. Ivana Seliz
          </span>
          <div className="flex items-center gap-1.5" title={apiConnected ? 'Backend FastAPI Conectado' : 'Modo Datos Locales'}>
            <span className={`size-2 rounded-full ${apiConnected ? 'bg-success animate-pulse' : 'bg-text-muted'}`} />
            <span className="text-[10px] font-semibold text-text-muted">{apiConnected ? 'ONLINE' : 'LOCAL'}</span>
          </div>
        </div>

        {/* Navegación Principal */}
        <nav className="min-h-0 flex-1 overflow-y-auto px-3 xl:px-4 py-5" aria-label="Secciones del CRM">
          <p className="mb-2 px-3 text-xs font-medium text-text-muted">
            Gestión de Consorcios
          </p>
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
                  className={`flex min-h-10 xl:min-h-11 w-full items-center gap-3 rounded-base px-3 text-xs xl:text-sm font-semibold transition-all cursor-pointer ${
                    isActive
                      ? 'bg-brand-ink bg-[image:var(--gradient-action-primary)] text-white shadow-sm'
                      : 'text-text-secondary hover:bg-surface-muted hover:text-brand-ink'
                  }`}
                >
                  <Icon size={18} aria-hidden="true" />
                  <span>{label}</span>
                </button>
              );
            })}
          </div>
        </nav>

        {/* Perfil en la Base */}
        <div className="border-t border-border p-3 xl:p-4 bg-surface-soft/60">
          <div className="flex items-center gap-3 px-1 xl:px-2">
            <div className="grid size-8 xl:size-9 place-items-center rounded-full bg-brand-ink text-white text-xs font-bold shadow-sm">
              IS
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-bold text-brand-ink truncate">Dra. Ivana Seliz</p>
              <p className="text-[11px] text-text-secondary truncate">Administradora Legal</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Contenedor Principal (con compensación de sidebar para lg+) */}
      <div className="flex-1 min-w-0 lg:pl-64 xl:pl-72 flex flex-col h-[100dvh] overflow-hidden">
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
            {/* Indicador de conexión API en móvil / tablet */}
            <div className="flex lg:hidden items-center gap-1.5 px-2 py-0.5 rounded-full border border-border/70 text-[10px] text-text-secondary bg-surface-muted/50">
              <span className={`size-1.5 rounded-full ${apiConnected ? 'bg-success' : 'bg-text-muted'}`} />
              <span>{apiConnected ? 'API OK' : 'Local'}</span>
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
          </div>
        </header>

        {/* Área de Contenido Dinámico con Zoom */}
        <main
          style={{ zoom: zoomLevel }}
          className="flex-1 overflow-hidden p-2 sm:p-3 md:p-3.5 lg:p-4 pb-20 lg:pb-4"
        >
          {activeTab === 'inbox' && (
            <Card className="h-full flex overflow-hidden border border-border/80 bg-white shadow-subtle">
              {/* Columna Izquierda: Inbox (Master view en móvil, proporcional en desktop) */}
              <div
                className={`${
                  mobileChatOpen ? 'hidden md:flex' : 'flex'
                } w-full md:w-[38%] lg:w-[32%] xl:w-[28%] min-w-[260px] max-w-[380px] h-full overflow-hidden shrink-0 flex-col`}
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

              {/* Columna Derecha: Hilo de Mensajes & Borrador IA (Detail view en móvil) */}
              <div
                className={`${
                  mobileChatOpen ? 'flex' : 'hidden md:flex'
                } flex-1 h-full flex flex-col overflow-hidden bg-surface-soft min-w-0`}
              >
                <div className="flex-1 overflow-hidden min-w-0">
                  <MessageThread
                    conversationId={currentConv.id}
                    senderName={currentConv.senderName}
                    phone={currentConv.phone}
                    consorcio={currentConv.consorcio}
                    unidad={currentConv.unidad}
                    messages={currentMessages}
                    onSendMessage={handleSendMessage}
                    onGenerateAiDraft={handleGenerateAiDraft}
                    generatingDraft={generatingDraft}
                    onBack={() => setMobileChatOpen(false)}
                  />
                </div>

                {/* Panel de Borrador IA */}
                {currentDraft && (
                  <div className="p-2.5 sm:p-3.5 border-t border-border bg-white shrink-0">
                    <AiDraftBox
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
            </Card>
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

          {activeTab === 'consorcios' && (
            <div className="h-full overflow-y-auto space-y-4 sm:space-y-6">
              <Card>
                <CardHeader>
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <h2 className="text-sm sm:text-base font-bold tracking-tight text-brand-ink">
                        Directorio de Consorcios Administrados
                      </h2>
                      <p className="text-[11px] sm:text-xs text-text-secondary mt-0.5">
                        Cuentas bancarias homologadas para cobranzas y teléfonos oficiales de guardia
                      </p>
                    </div>
                    <div className="flex items-center gap-2 self-start sm:self-auto">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={loadConsorcios}
                        disabled={loadingConsorcios}
                        className="h-7 px-2.5 text-xs text-text-secondary hover:text-brand-ink"
                        title="Actualizar consorcios desde la base de datos"
                      >
                        <RotateCcw size={12} className={loadingConsorcios ? 'animate-spin' : ''} />
                        <span>Actualizar</span>
                      </Button>
                      <span className="text-xs text-text-muted font-medium bg-surface-muted px-2 py-0.5 rounded-full border border-border/60">
                        {consorcios.length} consorcios
                      </span>
                    </div>
                  </div>
                </CardHeader>

                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3.5 sm:gap-4 lg:gap-5">
                    {consorcios.map((c) => (
                      <Card
                        key={c.id}
                        className="p-4 sm:p-5 space-y-3 border border-border shadow-subtle hover:border-brand-ink/40 transition-colors"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0">
                            <h3 className="text-xs sm:text-sm font-bold text-brand-ink leading-snug">
                              {c.nombre}
                            </h3>
                            <p className="text-[11px] sm:text-xs text-text-secondary mt-0.5">
                              {c.direccion}
                            </p>
                          </div>
                          {c.cuit && (
                            <Badge variant="neutral" className="text-[10px] shrink-0">
                              CUIT {c.cuit}
                            </Badge>
                          )}
                        </div>

                        <div className="text-[11px] sm:text-xs text-text-secondary space-y-1.5 pt-3 border-t border-border bg-surface-soft p-3 rounded-base">
                          {c.cbu_bancario && (
                            <div className="break-all">
                              CBU: <span className="font-semibold text-brand-ink">{c.cbu_bancario}</span>
                            </div>
                          )}
                          {c.alias_bancario && (
                            <div>
                              Alias: <span className="font-semibold text-brand-ink">{c.alias_bancario}</span>
                            </div>
                          )}
                          {c.email_cobranzas && (
                            <div className="truncate">
                              Cobranzas: <span className="font-semibold text-brand-ink">{c.email_cobranzas}</span>
                            </div>
                          )}
                          {c.telefono_porteria && (
                            <div>
                              Portería: <span className="font-semibold text-brand-ink">{c.telefono_porteria}</span>
                            </div>
                          )}
                          {c.emergencia_ascensores && (
                            <div>
                              Guardia Ascensores: <span className="font-semibold text-brand-ink">{c.emergencia_ascensores}</span>
                            </div>
                          )}
                          {c.emergencia_plomeria && (
                            <div>
                              Guardia Plomería: <span className="font-semibold text-brand-ink">{c.emergencia_plomeria}</span>
                            </div>
                          )}
                        </div>

                        {c.pautas_mudanza && (
                          <div className="text-[11px] text-text-secondary bg-surface-muted/40 p-2.5 rounded border border-border/50">
                            <span className="font-semibold text-brand-ink block mb-0.5">Pautas de Mudanza:</span>
                            <span className="text-text-muted">{c.pautas_mudanza}</span>
                          </div>
                        )}
                      </Card>
                    ))}
                  </div>
                </CardContent>
              </Card>
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
