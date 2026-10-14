import React, { useState } from 'react';
import {
  Building2,
  MessageSquare,
  CheckSquare,
  Terminal,
  Minus,
  Plus,
} from 'lucide-react';
import { ChatInbox } from './components/chat/ChatInbox.jsx';
import { MessageThread } from './components/chat/MessageThread.jsx';
import { AiDraftBox } from './components/chat/AiDraftBox.jsx';
import { TicketsTable } from './components/tables/TicketsTable.jsx';
import { DebugSimulator } from './components/debug/DebugSimulator.jsx';
import { Card, CardHeader, CardContent } from './components/ui/Card.jsx';

export default function App() {
  const [activeTab, setActiveTab] = useState('inbox');
  const [selectedConvId, setSelectedConvId] = useState('conv-1');
  const [mobileChatOpen, setMobileChatOpen] = useState(false);
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

  const [conversations, setConversations] = useState([
    {
      id: 'conv-1',
      senderName: 'Carlos Méndez',
      phone: '+54 9 11 4455-8899',
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
      phone: '+54 9 11 6677-8899',
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
      phone: '+54 9 11 3322-1100',
      consorcio: 'Torre Lavalle',
      unidad: 'Cochera 14',
      lastMessage: 'Urgente, hay dos personas atrapadas en el ascensor!',
      timestamp: '17:50',
      unreadCount: 0,
      status: 'emergency',
    },
  ]);

  const [messagesByConv, setMessagesByConv] = useState({
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
  });

  const [aiDrafts, setAiDrafts] = useState({
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
  });

  const tickets = [
    {
      id: 'TICK-1042',
      consorcio: 'Torre Corrientes',
      unidad: '4° B',
      contacto: 'Carlos Méndez',
      intencion: 'RECLAMO',
      descripcion: 'Corte de luz en palier del piso 4',
      prioridad: 'ALTA',
      estado: 'EN_REVISION',
      creado_el: '13/10 18:42',
    },
    {
      id: 'TICK-1041',
      consorcio: 'Callao 2334',
      unidad: '7° A',
      contacto: 'Lucía Rossi',
      intencion: 'EXPENSAS',
      descripcion: 'Consulta de CBU y datos de pago',
      prioridad: 'NORMAL',
      estado: 'NUEVO',
      creado_el: '13/10 18:15',
    },
    {
      id: 'TICK-1040',
      consorcio: 'Torre Lavalle',
      unidad: 'Cochera 14',
      contacto: 'Mariano Gómez',
      intencion: 'EMERGENCIA',
      descripcion: 'Personas atrapadas en ascensor',
      prioridad: 'CRITICA',
      estado: 'DERIVADO',
      creado_el: '13/10 17:50',
    },
  ];

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

  const handleSendMessage = (text) => {
    const newMsg = {
      id: `m-${Date.now()}`,
      sender: 'ivana',
      text,
      timestamp: 'Ahora',
    };
    setMessagesByConv({
      ...messagesByConv,
      [selectedConvId]: [...currentMessages, newMsg],
    });
  };

  const handleApproveDraft = (text) => {
    handleSendMessage(text);
    setAiDrafts({
      ...aiDrafts,
      [selectedConvId]: null,
    });
  };

  return (
    <div className="h-[100dvh] min-h-[100dvh] bg-surface-soft text-brand-ink flex flex-col lg:flex-row overflow-hidden">
      {/* Sidebar Fijo para Desktop y Laptops Grandes */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 xl:w-72 flex-col border-r border-border bg-white shadow-card lg:flex">
        {/* Marca y Encabezado */}
        <div className="flex min-h-16 xl:min-h-20 items-center border-b border-border px-5 xl:px-6">
          <span className="text-sm font-bold tracking-tight text-brand-ink">
            Dra. Ivana Seliz
          </span>
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
              <TicketsTable tickets={tickets} />
            </div>
          )}

          {activeTab === 'consorcios' && (
            <div className="h-full overflow-y-auto space-y-4 sm:space-y-6">
              <Card>
                <CardHeader>
                  <div>
                    <h2 className="text-sm sm:text-base font-bold tracking-tight text-brand-ink">
                      Directorio de Consorcios Administrados
                    </h2>
                    <p className="text-[11px] sm:text-xs text-text-secondary mt-0.5">
                      Cuentas bancarias homologadas para cobranzas y teléfonos oficiales de guardia
                    </p>
                  </div>
                </CardHeader>

                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3.5 sm:gap-4 lg:gap-5">
                    <Card className="p-4 sm:p-5 space-y-3 border border-border shadow-subtle hover:border-brand-ink/40 transition-colors">
                      <div>
                        <h3 className="text-xs sm:text-sm font-bold text-brand-ink">
                          Consorcio Corrientes y Lavalle
                        </h3>
                        <p className="text-[11px] sm:text-xs text-text-secondary mt-0.5">
                          Av. Corrientes 1240 / Lavalle 1241, CABA
                        </p>
                      </div>

                      <div className="text-[11px] sm:text-xs text-text-secondary space-y-1.5 pt-3 border-t border-border bg-surface-soft p-3 rounded-base">
                        <div>CBU: <span className="font-semibold text-brand-ink">0140000000000000000001</span></div>
                        <div>Alias: <span className="font-semibold text-brand-ink">CONSORCIO.LAVALLE.OFICIAL</span></div>
                        <div>Guardia Ascensores: <span className="font-semibold text-brand-ink">+54 9 11 4444-1111</span></div>
                      </div>
                    </Card>

                    <Card className="p-4 sm:p-5 space-y-3 border border-border shadow-subtle hover:border-brand-ink/40 transition-colors">
                      <div>
                        <h3 className="text-xs sm:text-sm font-bold text-brand-ink">
                          Consorcio Callao 2334
                        </h3>
                        <p className="text-[11px] sm:text-xs text-text-secondary mt-0.5">
                          Av. Callao 2334, Recoleta, CABA
                        </p>
                      </div>

                      <div className="text-[11px] sm:text-xs text-text-secondary space-y-1.5 pt-3 border-t border-border bg-surface-soft p-3 rounded-base">
                        <div>CBU: <span className="font-semibold text-brand-ink">0140000000000000000002</span></div>
                        <div>Alias: <span className="font-semibold text-brand-ink">CALLAO.2334.EXPENSAS</span></div>
                        <div>Guardia Plomería: <span className="font-semibold text-brand-ink">+54 9 11 4444-4444</span></div>
                      </div>
                    </Card>
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
