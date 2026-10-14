import React, { useState } from 'react';
import {
  Send,
  Terminal,
  Clock,
  ShieldAlert,
  Bot,
  User,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Zap,
  Info,
} from 'lucide-react';
import { Card, CardHeader, CardContent } from '../ui/Card.jsx';
import { Button } from '../ui/Button.jsx';
import { Badge } from '../ui/Badge.jsx';

export function DebugSimulator() {
  const [message, setMessage] = useState('');
  const [phone, setPhone] = useState('+5491144558899');
  const [userName, setUserName] = useState('Carlos Méndez');
  const [scheduleOverride, setScheduleOverride] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([
    {
      timestamp: '18:42:01',
      request: {
        message: 'Hola, ¿cuál es el CBU o alias para abonar las expensas?',
        phone: '+5491144558899',
        override_schedule: 'BOT_ACTIVE_OFF_HOURS',
      },
      response: {
        phone: '+5491144558899',
        user_message: 'Hola, ¿cuál es el CBU o alias para abonar las expensas?',
        contact: {
          nombre: 'Carlos Méndez',
          unidad: 'Torre Corrientes 4° B',
          rol: 'PROPIETARIO',
        },
        consorcio: {
          nombre: 'Consorcio Corrientes y Lavalle',
          cbu: '0140000000000000000001',
          alias: 'CONSORCIO.LAVALLE.OFICIAL',
        },
        schedule_status: 'BOT_ACTIVE_OFF_HOURS',
        is_emergency: false,
        emergency_reasons: [],
        is_cordial_close: false,
        is_pure_greeting: false,
        is_noise: false,
        rag_matched: false,
        tev1_decision: 'B',
        intent: 'EXPENSAS_DATOS_PAGO',
        should_respond: true,
        response_text:
          'Hola Carlos, te paso los datos para la transferencia de expensas de Consorcio Corrientes y Lavalle:\n\n• CBU: 0140000000000000000001\n• Alias: CONSORCIO.LAVALLE.OFICIAL\n• CUIT: 30-71122334-5\n\nUna vez realizado el pago, envianos por favor el comprobante a cobranzas@selizadministraciones.com.ar indicando tu unidad funcional (Torre Corrientes 4° B). Saludos.',
        silent_reason: null,
        latency_metrics: {
          tev1_router_ms: 1.42,
          rag_faq_ms: 4.88,
        },
        total_pipeline_ms: 14.2,
        ticket_created: null,
      },
    },
  ]);

  const quickMessages = [
    { label: 'CBU Expensas', text: 'Hola, me pasan el CBU y alias para pagar las expensas?' },
    { label: 'Urgencia Gas', text: 'Urgente, hay un olor a gas muy fuerte en el palier!' },
    { label: 'Ascensor Traspasado', text: 'Se trabó el ascensor y hay una vecina adentro!' },
    { label: 'Reclamo Luz', text: 'No hay luz en las cocheras desde anoche.' },
    { label: 'Saludo Simple', text: 'hola' },
    { label: 'Cierre Cordial', text: 'Muchas gracias por todo, buen finde!' },
  ];

  const handleSend = async (e) => {
    if (e) e.preventDefault();
    if (!message.trim() || loading) return;

    setLoading(true);
    setError(null);

    const payload = {
      message: message.trim(),
      phone: phone.trim(),
      user_name: userName.trim(),
    };
    if (scheduleOverride) {
      payload.override_schedule = scheduleOverride;
    }

    try {
      const res = await fetch('http://localhost:8000/api/v1/debug/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error(`Error HTTP ${res.status}: ${res.statusText}`);
      }

      const data = await res.json();
      const now = new Date();
      const timeStr = now.toTimeString().split(' ')[0];

      setHistory((prev) => [
        {
          timestamp: timeStr,
          request: payload,
          response: data,
        },
        ...prev,
      ]);
      setMessage('');
    } catch (err) {
      setError(err.message || 'No se pudo conectar con la API en http://localhost:8000');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col gap-6 overflow-hidden">
      {/* Panel Superior: Formulario de Simulación HTTP */}
      <Card className="shrink-0">
        <CardHeader>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-2.5">
              <Terminal className="w-5 h-5 text-brand-ink" />
              <div>
                <h2 className="text-base font-bold tracking-tight text-brand-ink">
                  Simulador de Conversación HTTP Local
                </h2>
                <p className="text-xs text-text-secondary mt-0.5">
                  Prueba de guardrails, RAG FAQs, Tev1 Router y respuesta personalizada sin WhatsApp
                </p>
              </div>
            </div>

            <Button
              variant="secondary"
              size="sm"
              onClick={() => setHistory([])}
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Limpiar Historial</span>
            </Button>
          </div>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSend} className="space-y-4">
            <div className="grid grid-cols-12 gap-3.5">
              {/* Teléfono */}
              <div className="col-span-12 sm:col-span-3">
                <label className="block text-xs font-semibold uppercase tracking-[0.08em] text-text-secondary mb-1">
                  Teléfono WhatsApp
                </label>
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="min-h-11 w-full rounded-base border border-border bg-white px-3 text-sm outline-none transition-colors focus:border-brand-ink focus:ring-1 focus:ring-brand-ink"
                  placeholder="+5491144558899"
                />
              </div>

              {/* Nombre Vecino */}
              <div className="col-span-12 sm:col-span-3">
                <label className="block text-xs font-semibold uppercase tracking-[0.08em] text-text-secondary mb-1">
                  Vecino Remitente
                </label>
                <input
                  type="text"
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                  className="min-h-11 w-full rounded-base border border-border bg-white px-3 text-sm outline-none transition-colors focus:border-brand-ink focus:ring-1 focus:ring-brand-ink"
                  placeholder="Carlos Méndez"
                />
              </div>

              {/* Guardrail Horario */}
              <div className="col-span-12 sm:col-span-4">
                <label className="block text-xs font-semibold uppercase tracking-[0.08em] text-text-secondary mb-1">
                  Guardrail Horario (Override)
                </label>
                <select
                  value={scheduleOverride}
                  onChange={(e) => setScheduleOverride(e.target.value)}
                  className="min-h-11 w-full rounded-base border border-border bg-white px-3 text-sm outline-none transition-colors focus:border-brand-ink focus:ring-1 focus:ring-brand-ink"
                >
                  <option value="">Automático (Evaluar hora actual)</option>
                  <option value="BOT_ACTIVE_OFF_HOURS">BOT_ACTIVE_OFF_HOURS (Fuera de horario - Bot Activo)</option>
                  <option value="HUMAN_OFFICE_HOURS">HUMAN_OFFICE_HOURS (Horario Oficina - Bot Silencio)</option>
                  <option value="QUIET_HOURS">QUIET_HOURS (Madrugada 00-07:30 - Silencio)</option>
                </select>
              </div>

              {/* Botón Enviar */}
              <div className="col-span-12 sm:col-span-2 flex items-end">
                <Button
                  type="submit"
                  size="md"
                  disabled={loading || !message.trim()}
                  className="w-full"
                >
                  <Send className="w-4 h-4" />
                  <span>{loading ? 'Procesando…' : 'Enviar HTTP'}</span>
                </Button>
              </div>
            </div>

            {/* Input Mensaje y Atajos */}
            <div>
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1.5 mb-1.5">
                <label className="text-xs font-semibold uppercase tracking-[0.08em] text-text-secondary">
                  Mensaje del Vecino
                </label>
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="text-xs text-text-muted font-medium">Ejemplos:</span>
                  {quickMessages.map((qm, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setMessage(qm.text)}
                      className="text-xs px-2.5 py-0.5 rounded-full border border-border bg-surface-muted text-text-secondary hover:border-brand-ink hover:text-brand-ink transition-colors cursor-pointer"
                    >
                      {qm.label}
                    </button>
                  ))}
                </div>
              </div>
              <textarea
                rows={2}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                className="w-full rounded-base border border-border bg-white p-3 text-sm text-brand-ink outline-none transition-colors focus:border-brand-ink focus:ring-1 focus:ring-brand-ink resize-none placeholder:text-text-muted"
                placeholder="Escribe el mensaje a simular... (Presiona Enter para enviar)"
              />
            </div>
          </form>

          {error && (
            <div className="mt-4 rounded-base border border-danger/20 bg-danger-soft p-3.5 text-xs text-danger flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Panel Inferior: Feed de Conversación e Inspección Técnica */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1">
        {history.length === 0 ? (
          <Card className="p-8 text-center text-text-muted">
            <Terminal className="w-8 h-8 mx-auto mb-2 opacity-40 text-brand-ink" />
            <p className="text-sm font-medium text-brand-ink">No hay mensajes en esta sesión de debug.</p>
            <p className="text-xs text-text-secondary mt-1">
              Ingresa un texto arriba o ejecuta el script CLI <code className="text-brand-ink">./scripts/chat_debug.sh "..."</code>
            </p>
          </Card>
        ) : (
          history.map((item, idx) => (
            <Card key={idx} className="p-4 sm:p-5 space-y-3.5">
              {/* Header de la interacción */}
              <div className="flex items-center justify-between text-xs border-b border-border pb-3">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs text-text-muted">[{item.timestamp}]</span>
                  <span className="font-bold text-brand-ink">
                    {item.response.contact?.nombre || item.request.phone}
                  </span>
                  {item.response.contact?.unidad && (
                    <Badge variant="neutral">{item.response.contact.unidad}</Badge>
                  )}
                  {item.response.consorcio && (
                    <span className="text-xs text-text-secondary">
                      ({item.response.consorcio.nombre})
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-xs text-text-secondary">
                    Latencia: <span className="font-bold text-brand-ink">{item.response.total_pipeline_ms} ms</span>
                  </span>
                  {item.response.is_emergency ? (
                    <Badge variant="danger">Emergencia</Badge>
                  ) : item.response.is_noise ? (
                    <Badge variant="neutral">Silencio (Ruido)</Badge>
                  ) : item.response.is_pure_greeting ? (
                    <Badge variant="info">Saludo</Badge>
                  ) : item.response.should_respond ? (
                    <Badge variant="success">Respuesta Despachada</Badge>
                  ) : (
                    <Badge variant="warning">Silencio</Badge>
                  )}
                </div>
              </div>

              {/* Mensaje del Vecino */}
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-surface-muted border border-border flex items-center justify-center shrink-0 mt-0.5 text-text-secondary">
                  <User className="w-4 h-4" />
                </div>
                <div className="flex-1 bg-surface-soft border border-border rounded-base p-3.5 text-sm text-brand-ink leading-relaxed">
                  {item.response.user_message}
                </div>
              </div>

              {/* Respuesta del Bot o Motivo de Silencio */}
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-brand-ink text-white flex items-center justify-center shrink-0 mt-0.5 shadow-sm">
                  <Bot className="w-4 h-4" />
                </div>
                <div
                  className={`flex-1 rounded-base p-4 text-sm leading-relaxed ${
                    item.response.should_respond
                      ? 'bg-brand-ink bg-[image:var(--gradient-action-primary)] text-white shadow-card whitespace-pre-wrap'
                      : 'bg-surface-muted border border-border text-text-secondary italic'
                  }`}
                >
                  {item.response.should_respond ? (
                    item.response.response_text
                  ) : (
                    <div className="flex items-center gap-2 not-italic">
                      <Info className="w-4 h-4 text-warning shrink-0" />
                      <span className="font-medium">{item.response.silent_reason || 'Sin respuesta despachada.'}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Telemetría y Métricas del Pipeline */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-2 border-t border-border text-xs">
                <div className="bg-surface-soft p-2.5 rounded-base border border-border">
                  <span className="text-text-muted block text-[10px] uppercase font-semibold">Horario</span>
                  <span className="text-brand-ink font-medium">{item.response.schedule_status}</span>
                </div>

                <div className="bg-surface-soft p-2.5 rounded-base border border-border">
                  <span className="text-text-muted block text-[10px] uppercase font-semibold">RAG FAQs</span>
                  <span className="text-brand-ink font-medium">
                    {item.response.rag_matched ? `Match (${item.response.rag_score})` : 'No match'}
                  </span>
                </div>

                <div className="bg-surface-soft p-2.5 rounded-base border border-border">
                  <span className="text-text-muted block text-[10px] uppercase font-semibold">Tev1 Decisión</span>
                  <span className="text-brand-ink font-medium">
                    {item.response.tev1_decision ? `Opción [${item.response.tev1_decision}]` : 'N/A'}
                  </span>
                </div>

                <div className="bg-surface-soft p-2.5 rounded-base border border-border">
                  <span className="text-text-muted block text-[10px] uppercase font-semibold">Ticket Asignado</span>
                  <span className="text-brand-ink font-medium">
                    {item.response.ticket_created ? (
                      <span>
                        #{item.response.ticket_created.id}{' '}
                        <span className="text-[10px] text-text-muted">
                          ({item.response.ticket_created.accion === 'CONSOLIDADO_EN_TICKET_EXISTENTE' ? 'Consolidado' : 'Nuevo'})
                        </span>
                      </span>
                    ) : (
                      'Ninguno'
                    )}
                  </span>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
