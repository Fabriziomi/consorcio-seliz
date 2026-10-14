import React, { useState } from 'react';
import {
  Building2,
  MessageSquare,
  CheckSquare,
  Terminal,
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
    <div className="min-h-screen bg-surface-soft text-brand-ink flex">
      {/* Sidebar Fijo al estilo Contino CRM */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 lg:w-72 flex-col border-r border-border bg-white shadow-card lg:flex">
        {/* Marca y Encabezado */}
        <div className="flex min-h-20 items-center border-b border-border px-6">
          <span className="text-sm font-bold tracking-tight text-brand-ink">
            Dra. Ivana Seliz
          </span>
        </div>

        {/* Navegación Principal */}
        <nav className="min-h-0 flex-1 overflow-y-auto px-4 py-6" aria-label="Secciones del CRM">
          <p className="mb-2 px-3 text-xs font-medium text-text-muted">
            Gestión de Consorcios
          </p>
          <div className="grid gap-1">
            {navigationItems.map(({ id, label, icon: Icon }) => {
              const isActive = id === activeTab;
              return (
                <button
                  key={id}
                  onClick={() => setActiveTab(id)}
                  className={`flex min-h-11 w-full items-center gap-3 rounded-base px-3 text-sm font-semibold transition-all cursor-pointer ${
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
        <div className="border-t border-border p-4 bg-surface-soft/60">
          <div className="flex items-center gap-3 px-2">
            <div className="grid size-9 place-items-center rounded-full bg-brand-ink text-white text-xs font-bold shadow-sm">
              IS
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-bold text-brand-ink truncate">Dra. Ivana Seliz</p>
              <p className="text-[11px] text-text-secondary truncate">Administradora Legal</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Contenedor Principal (con padding izquierdo para sidebar en lg) */}
      <div className="flex-1 min-w-0 lg:pl-72 flex flex-col h-screen overflow-hidden">
        {/* Barra Superior Sticky al estilo Contino CRM */}
        <header className="sticky top-0 z-20 flex min-h-16 items-center justify-between border-b border-border bg-white/95 px-4 backdrop-blur sm:min-h-20 sm:px-6 lg:px-8 shrink-0">
          <div className="flex items-center gap-3">
            {/* Selector Móvil de Pestañas */}
            <div className="flex items-center gap-2 lg:hidden">
              <select
                value={activeTab}
                onChange={(e) => setActiveTab(e.target.value)}
                className="text-xs font-semibold py-1.5 px-2.5 rounded-base border border-border bg-white text-brand-ink"
              >
                {navigationItems.map((n) => (
                  <option key={n.id} value={n.id}>{n.label}</option>
                ))}
              </select>
            </div>

            {/* Breadcrumb de escritorio */}
            <div className="hidden min-w-0 items-center gap-2 text-sm text-text-secondary lg:flex font-medium">
              <span className="font-semibold text-brand-ink">Consorcios</span>
              <span aria-hidden="true">/</span>
              <span className="truncate">{activeLabel}</span>
            </div>
          </div>

        </header>

        {/* Área de Contenido Dinámico */}
        <main className="flex-1 overflow-hidden p-4 sm:p-6 lg:p-8">
          {activeTab === 'inbox' && (
            <Card className="h-full flex overflow-hidden border border-border bg-white shadow-card">
              {/* Columna Izquierda: Inbox */}
              <div className="w-80 lg:w-96 h-full border-r border-border overflow-hidden shrink-0">
                <ChatInbox
                  conversations={conversations}
                  selectedId={selectedConvId}
                  onSelect={setSelectedConvId}
                />
              </div>

              {/* Columna Derecha: Hilo de Mensajes & Borrador IA */}
              <div className="flex-1 h-full flex flex-col overflow-hidden bg-surface-soft">
                <div className="flex-1 overflow-hidden">
                  <MessageThread
                    conversationId={currentConv.id}
                    senderName={currentConv.senderName}
                    phone={currentConv.phone}
                    consorcio={currentConv.consorcio}
                    unidad={currentConv.unidad}
                    messages={currentMessages}
                    onSendMessage={handleSendMessage}
                  />
                </div>

                {/* Panel de Borrador IA */}
                {currentDraft && (
                  <div className="p-4 border-t border-border bg-white shrink-0">
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
            <div className="h-full overflow-y-auto space-y-6">
              <Card>
                <CardHeader>
                  <div>
                    <h2 className="text-base font-bold tracking-tight text-brand-ink">
                      Directorio de Consorcios Administrados
                    </h2>
                    <p className="text-xs text-text-secondary mt-0.5">
                      Cuentas bancarias homologadas para cobranzas y teléfonos oficiales de guardia
                    </p>
                  </div>
                </CardHeader>

                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card className="p-5 space-y-3 border border-border shadow-subtle">
                      <div>
                        <h3 className="text-sm font-bold text-brand-ink">
                          Consorcio Corrientes y Lavalle
                        </h3>
                        <p className="text-xs text-text-secondary mt-0.5">
                          Av. Corrientes 1240 / Lavalle 1241, CABA
                        </p>
                      </div>

                      <div className="text-xs text-text-secondary space-y-1.5 pt-3 border-t border-border bg-surface-soft p-3 rounded-base">
                        <div>CBU: <span className="font-semibold text-brand-ink">0140000000000000000001</span></div>
                        <div>Alias: <span className="font-semibold text-brand-ink">CONSORCIO.LAVALLE.OFICIAL</span></div>
                        <div>Guardia Ascensores: <span className="font-semibold text-brand-ink">+54 9 11 4444-1111</span></div>
                      </div>
                    </Card>

                    <Card className="p-5 space-y-3 border border-border shadow-subtle">
                      <div>
                        <h3 className="text-sm font-bold text-brand-ink">
                          Consorcio Callao 2334
                        </h3>
                        <p className="text-xs text-text-secondary mt-0.5">
                          Av. Callao 2334, Recoleta, CABA
                        </p>
                      </div>

                      <div className="text-xs text-text-secondary space-y-1.5 pt-3 border-t border-border bg-surface-soft p-3 rounded-base">
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
    </div>
  );
}
