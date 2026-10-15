import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Paperclip,
  ArrowLeft,
  MessageSquareDot,
  PanelLeftClose,
  PanelLeftOpen,
  Lock,
  Globe,
  Bot,
  UserCheck,
  CheckCircle2,
  Clock,
  AlertTriangle,
  ChevronDown,
} from 'lucide-react';
import { Button } from '../ui/Button.jsx';
import { Badge } from '../ui/Badge.jsx';

export function MessageThread({
  conversationId,
  senderName,
  phone,
  consorcio,
  unidad,
  status = 'open',
  botActive = true,
  messages = [],
  onSendMessage,
  onUpdateStatus,
  onGenerateAiDraft,
  generatingDraft = false,
  onBack,
  inboxListCollapsed = false,
  onToggleInboxList,
}) {
  const [inputText, setInputText] = useState('');
  const [isPrivateNote, setIsPrivateNote] = useState(false);
  const [statusDropdownOpen, setStatusDropdownOpen] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    onSendMessage(inputText.trim(), isPrivateNote);
    setInputText('');
  };

  const handleStatusSelect = (newStatus) => {
    if (onUpdateStatus) {
      onUpdateStatus(newStatus);
    }
    setStatusDropdownOpen(false);
  };

  return (
    <div className="h-full flex flex-col bg-surface-soft min-w-0">
      {/* Cabecera del Hilo */}
      <div className="p-2.5 sm:p-3 border-b border-border/70 flex items-center justify-between bg-white shrink-0 min-w-0">
        <div className="flex items-center gap-2.5 sm:gap-3 min-w-0">
          {onBack && (
            <button
              type="button"
              onClick={onBack}
              aria-label="Volver a conversaciones"
              className="md:hidden grid size-8 place-items-center rounded-base border border-border/70 bg-white text-text-secondary hover:text-brand-ink hover:bg-surface-muted transition-colors shrink-0 cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
            </button>
          )}
          {onToggleInboxList && (
            <button
              type="button"
              onClick={onToggleInboxList}
              aria-label={inboxListCollapsed ? 'Mostrar lista de conversaciones' : 'Maximizar espacio de chat'}
              title={inboxListCollapsed ? 'Mostrar lista de conversaciones' : 'Maximizar espacio de chat'}
              className="hidden md:grid size-8 place-items-center rounded-base border border-border/70 bg-white text-text-secondary hover:text-brand-ink hover:bg-surface-muted transition-colors shrink-0 cursor-pointer"
            >
              {inboxListCollapsed ? <PanelLeftOpen className="w-4 h-4" /> : <PanelLeftClose className="w-4 h-4" />}
            </button>
          )}
          <div className="size-8 sm:size-9 rounded-full bg-brand-ink text-white flex items-center justify-center text-xs font-bold shadow-subtle shrink-0">
            {senderName ? senderName.charAt(0).toUpperCase() : 'V'}
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
              <span className="text-xs sm:text-sm font-bold text-brand-ink truncate">{senderName}</span>
              <span className="text-[11px] sm:text-xs text-text-muted truncate font-mono">{phone}</span>
            </div>
            <div className="flex items-center gap-1.5 text-[11px] sm:text-xs text-text-secondary mt-0.5 truncate">
              <span className="truncate">{consorcio}</span>
              <span>•</span>
              <span className="font-medium text-brand-ink shrink-0">{unidad || 'Unidad S/E'}</span>
            </div>
          </div>
        </div>

        {/* Acciones de Cabecera: Selector de Estado + Sugerir con IA */}
        <div className="flex items-center gap-2 shrink-0">
          {/* Takeover Indicator */}
          {!botActive && (
            <div
              title="El asistente automático está pausado para este contacto por atención personalizada."
              className="hidden xl:flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-50 border border-amber-200 text-amber-800 text-[10px] font-bold"
            >
              <UserCheck size={11} />
              <span>Atención Personalizada</span>
            </div>
          )}

          {/* Selector de Estado */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setStatusDropdownOpen((prev) => !prev)}
              className="h-8 px-2 sm:px-2.5 rounded-base border border-border bg-white text-brand-ink text-xs font-semibold flex items-center gap-1.5 hover:bg-surface-muted cursor-pointer transition-colors"
            >
              <span className="capitalize">{status === 'open' ? 'Abierto' : status === 'pending' ? 'Pendiente' : status === 'resolved' ? 'Resuelto' : status}</span>
              <ChevronDown size={13} className="text-text-muted" />
            </button>

            {statusDropdownOpen && (
              <div className="absolute right-0 mt-1 w-36 bg-white border border-border rounded-base shadow-lg z-30 py-1 text-xs divide-y divide-border/60">
                <button
                  type="button"
                  onClick={() => handleStatusSelect('open')}
                  className="w-full text-left px-3 py-1.5 hover:bg-surface-soft flex items-center justify-between text-brand-ink font-medium cursor-pointer"
                >
                  <span>Abierto</span>
                  {status === 'open' && <CheckCircle2 size={13} className="text-brand-ink" />}
                </button>
                <button
                  type="button"
                  onClick={() => handleStatusSelect('pending')}
                  className="w-full text-left px-3 py-1.5 hover:bg-surface-soft flex items-center justify-between text-amber-700 font-medium cursor-pointer"
                >
                  <span>Pendiente</span>
                  {status === 'pending' && <CheckCircle2 size={13} className="text-amber-700" />}
                </button>
                <button
                  type="button"
                  onClick={() => handleStatusSelect('resolved')}
                  className="w-full text-left px-3 py-1.5 hover:bg-surface-soft flex items-center justify-between text-emerald-700 font-medium cursor-pointer"
                >
                  <span>Resuelto</span>
                  {status === 'resolved' && <CheckCircle2 size={13} className="text-emerald-700" />}
                </button>
              </div>
            )}
          </div>

          {/* Acción de Sugerencia con IA */}
          {onGenerateAiDraft && (
            <Button
              variant="secondary"
              size="sm"
              onClick={onGenerateAiDraft}
              disabled={generatingDraft}
              className="h-8 px-2 sm:px-2.5 text-xs text-brand-ink hover:border-brand-ink font-semibold"
              title="Generar propuesta de respuesta con IA basada en el último mensaje"
            >
              <MessageSquareDot className={`w-3.5 h-3.5 text-brand-ink ${generatingDraft ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">{generatingDraft ? 'Generando...' : 'Sugerir con IA'}</span>
            </Button>
          )}
        </div>
      </div>

      {/* Lista de Mensajes */}
      <div className="flex-1 overflow-y-auto p-3 sm:p-4 lg:p-5 space-y-3">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center text-xs text-text-muted">
            No hay mensajes registrados en este hilo de conversación.
          </div>
        ) : (
          messages.map((m) => {
            // Nota interna
            if (m.privado || m.isPrivateNote) {
              return (
                <div key={m.id} className="flex justify-center my-2">
                  <div className="max-w-[90%] sm:max-w-[80%] bg-amber-50 border border-amber-200/90 rounded-base p-3 text-amber-900 shadow-xs">
                    <div className="flex items-center justify-between gap-2 text-[10px] sm:text-[11px] font-bold text-amber-800 mb-1">
                      <div className="flex items-center gap-1.5">
                        <Lock size={12} />
                        <span>Nota Interna (Solo visible para la administración)</span>
                      </div>
                      <span className="text-amber-700/80 font-normal">{m.timestamp || m.creado_el}</span>
                    </div>
                    <p className="text-xs sm:text-sm whitespace-pre-line leading-relaxed text-amber-950 font-medium">
                      {m.text || m.contenido}
                    </p>
                  </div>
                </div>
              );
            }

            // Mensaje de sistema o actividad
            if (m.tipo === 'activity' || m.isStatusNote) {
              return (
                <div key={m.id} className="text-center my-2">
                  <span className="text-[11px] text-text-muted bg-surface-muted px-2.5 py-0.5 rounded-full border border-border/60">
                    {m.text || m.contenido}
                  </span>
                </div>
              );
            }

            // Mensaje enviado por el bot
            const isBot = m.enviado_por === 'bot' || m.sender === 'bot';
            // Mensaje enviado por un agente / Ivana
            const isAgent = m.enviado_por === 'agente' || m.sender === 'ivana' || m.sender === 'agent';
            // Mensaje enviado por el vecino
            const isNeighbor = !isBot && !isAgent;

            if (isBot) {
              return (
                <div key={m.id} className="flex flex-col items-start my-1 max-w-[88%] sm:max-w-[78%]">
                  <div className="bg-surface-soft border border-border rounded-lg p-3 text-brand-ink shadow-subtle">
                    <div className="flex items-center justify-between gap-3 mb-1 text-[11px] text-text-muted">
                      <div className="flex items-center gap-1.5 font-bold text-brand-ink">
                        <Bot size={13} className="text-text-secondary" />
                        <span>Respuesta Automática</span>
                      </div>
                      <span className="shrink-0">{m.timestamp || m.creado_el}</span>
                    </div>
                    <p className="whitespace-pre-line text-xs sm:text-sm leading-relaxed text-brand-ink">
                      {m.text || m.contenido}
                    </p>
                  </div>
                </div>
              );
            }

            if (isAgent) {
              return (
                <div key={m.id} className="flex flex-col items-end my-1">
                  <div className="max-w-[88%] sm:max-w-[78%] p-3 sm:p-3.5 rounded-lg bg-brand-ink text-white shadow-subtle leading-relaxed">
                    <div className="flex items-center justify-between gap-3 mb-1 text-[11px] text-surface-muted">
                      <span className="font-semibold">
                        {m.agente_nombre || 'Dra. Ivana Seliz (Administración)'}
                      </span>
                      <span className="shrink-0">{m.timestamp || m.creado_el}</span>
                    </div>
                    <p className="whitespace-pre-line text-xs sm:text-sm leading-relaxed">
                      {m.text || m.contenido}
                    </p>
                  </div>
                </div>
              );
            }

            // Mensaje del vecino (Incoming)
            return (
              <div key={m.id} className="flex flex-col items-start my-1">
                <div className="max-w-[88%] sm:max-w-[78%] p-3 sm:p-3.5 rounded-lg bg-white border border-border/80 text-brand-ink shadow-subtle leading-relaxed">
                  <div className="flex items-center justify-between gap-3 mb-1 text-[11px] text-text-muted">
                    <span className="font-semibold text-brand-ink">{senderName}</span>
                    <span className="shrink-0">{m.timestamp || m.creado_el}</span>
                  </div>
                  <p className="whitespace-pre-line text-xs sm:text-sm leading-relaxed">
                    {m.text || m.contenido}
                  </p>
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Barra de Redacción de Mensaje / Nota Interna */}
      <div className="border-t border-border/80 bg-white p-2.5 sm:p-3 shrink-0">
        {/* Toggle Modo: WhatsApp vs Nota Interna */}
        <div className="flex items-center gap-2 mb-2">
          <button
            type="button"
            onClick={() => setIsPrivateNote(false)}
            className={`text-xs font-semibold px-2.5 py-1 rounded transition-colors flex items-center gap-1.5 cursor-pointer ${
              !isPrivateNote
                ? 'bg-brand-ink text-white shadow-sm'
                : 'text-text-secondary hover:text-brand-ink bg-surface-muted'
            }`}
          >
            <Globe size={13} />
            <span>Respuesta WhatsApp</span>
          </button>

          <button
            type="button"
            onClick={() => setIsPrivateNote(true)}
            className={`text-xs font-semibold px-2.5 py-1 rounded transition-colors flex items-center gap-1.5 cursor-pointer ${
              isPrivateNote
                ? 'bg-amber-100 text-amber-900 border border-amber-300 font-bold'
                : 'text-text-secondary hover:text-brand-ink bg-surface-muted'
            }`}
          >
            <Lock size={13} />
            <span>Nota Interna (Privado)</span>
          </button>
        </div>

        {/* Formulario */}
        <form onSubmit={handleSend} className="flex items-center gap-2 min-w-0">
          <button
            type="button"
            aria-label="Adjuntar archivo"
            className="grid size-9 sm:size-10 place-items-center rounded-base border border-border/70 text-text-secondary hover:bg-surface-muted hover:text-brand-ink transition-colors cursor-pointer shrink-0"
          >
            <Paperclip className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
          </button>

          <input
            type="text"
            placeholder={
              isPrivateNote
                ? 'Escribir nota interna (visible únicamente para el equipo de administración)...'
                : 'Escribir mensaje oficial para despachar por WhatsApp al vecino...'
            }
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            className={`flex-1 min-w-0 min-h-9 sm:min-h-10 border text-brand-ink text-xs sm:text-sm rounded-base px-3 sm:px-3.5 outline-none transition-colors ${
              isPrivateNote
                ? 'bg-amber-50/50 border-amber-300 focus:border-amber-500 focus:ring-1 focus:ring-amber-500'
                : 'bg-white border-border/70 focus:border-brand-ink focus:ring-1 focus:ring-brand-ink'
            }`}
          />

          <Button
            type="submit"
            size="sm"
            variant={isPrivateNote ? 'secondary' : 'primary'}
            className={`min-h-9 sm:min-h-10 px-3 sm:px-4 shrink-0 font-semibold ${
              isPrivateNote ? 'border-amber-400 bg-amber-100 text-amber-900 hover:bg-amber-200' : ''
            }`}
          >
            {isPrivateNote ? <Lock className="w-3.5 h-3.5" /> : <Send className="w-3.5 h-3.5" />}
            <span className="hidden sm:inline">{isPrivateNote ? 'Guardar Nota' : 'Enviar'}</span>
          </Button>
        </form>
      </div>
    </div>
  );
}
