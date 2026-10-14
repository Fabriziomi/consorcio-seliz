import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, ArrowLeft, Sparkles, MessageCirclePlus } from 'lucide-react';
import { Button } from '../ui/Button.jsx';

export function MessageThread({
  senderName,
  phone,
  consorcio,
  unidad,
  messages = [],
  onSendMessage,
  onGenerateAiDraft,
  onSimulateNeighborMessage,
  generatingDraft = false,
  onBack,
}) {
  const [inputText, setInputText] = useState('');
  const [showSimulateModal, setShowSimulateModal] = useState(false);
  const [customNeighborMsg, setCustomNeighborMsg] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    onSendMessage(inputText.trim());
    setInputText('');
  };

  const quickSimulations = [
    { label: 'CBU / Expensas', text: 'Buenas tardes, ¿me confirman el CBU y alias para pagar las expensas?' },
    { label: 'Corte de luz', text: 'Hola, se cortó la luz en el palier de mi piso. ¿Podrán enviar electricista?' },
    { label: 'Emergencia Ascensor', text: 'Urgente, se trabó el ascensor con dos personas adentro!' },
    { label: 'Pautas de Mudanza', text: 'Hola, quería consultar qué días y horarios están permitidas las mudanzas.' },
    { label: 'Saludo Simple', text: 'Hola, buenos días.' },
  ];

  const handleTriggerSimulate = (text) => {
    if (!text.trim() || !onSimulateNeighborMessage) return;
    onSimulateNeighborMessage(text.trim());
    setCustomNeighborMsg('');
    setShowSimulateModal(false);
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
          <div className="size-8 sm:size-9 rounded-full bg-brand-ink text-white flex items-center justify-center text-xs font-bold shadow-subtle shrink-0">
            {senderName ? senderName.charAt(0) : 'V'}
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
              <span className="text-xs sm:text-sm font-bold text-brand-ink truncate">{senderName}</span>
              <span className="text-[11px] sm:text-xs text-text-muted truncate">{phone}</span>
            </div>
            <div className="flex items-center gap-1.5 text-[11px] sm:text-xs text-text-secondary mt-0.5 truncate">
              <span className="truncate">{consorcio}</span>
              <span>•</span>
              <span className="font-medium text-brand-ink shrink-0">{unidad}</span>
            </div>
          </div>
        </div>

        {/* Acciones de Cabecera (Sugerir IA y Simular) */}
        <div className="flex items-center gap-1.5 shrink-0">
          {onSimulateNeighborMessage && (
            <div className="relative">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setShowSimulateModal(!showSimulateModal)}
                className="h-8 px-2 sm:px-2.5 text-xs text-text-secondary hover:text-brand-ink"
                title="Simular mensaje entrante de vecino"
              >
                <MessageCirclePlus className="w-3.5 h-3.5" />
                <span className="hidden lg:inline">Simular Vecino</span>
              </Button>

              {showSimulateModal && (
                <div className="absolute right-0 top-10 w-72 sm:w-80 bg-white border border-border/80 rounded-base shadow-card p-3 z-30 space-y-2">
                  <div className="flex items-center justify-between border-b border-border/60 pb-1.5">
                    <span className="text-xs font-bold text-brand-ink">Simular WhatsApp de {senderName}</span>
                    <button
                      type="button"
                      onClick={() => setShowSimulateModal(false)}
                      className="text-text-muted hover:text-brand-ink text-xs p-1"
                    >
                      ✕
                    </button>
                  </div>

                  <p className="text-[11px] text-text-secondary">
                    Envía un mensaje como si proviniera del WhatsApp del vecino para probar la IA:
                  </p>

                  <div className="grid gap-1">
                    {quickSimulations.map((qs, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => handleTriggerSimulate(qs.text)}
                        className="text-left text-[11px] text-brand-ink hover:bg-surface-soft p-1.5 rounded transition-colors border border-border/40 truncate"
                      >
                        <span className="font-semibold block">{qs.label}:</span>
                        <span className="text-text-muted truncate block">{qs.text}</span>
                      </button>
                    ))}
                  </div>

                  <div className="pt-1.5 border-t border-border/60 flex gap-1.5">
                    <input
                      type="text"
                      placeholder="Mensaje personalizado..."
                      value={customNeighborMsg}
                      onChange={(e) => setCustomNeighborMsg(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleTriggerSimulate(customNeighborMsg);
                      }}
                      className="flex-1 text-[11px] bg-surface-soft border border-border rounded px-2 py-1 outline-none text-brand-ink focus:border-brand-ink"
                    />
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => handleTriggerSimulate(customNeighborMsg)}
                      disabled={!customNeighborMsg.trim()}
                      className="h-7 px-2 text-[11px]"
                    >
                      Enviar
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}

          {onGenerateAiDraft && (
            <Button
              variant="secondary"
              size="sm"
              onClick={onGenerateAiDraft}
              disabled={generatingDraft}
              className="h-8 px-2 sm:px-2.5 text-xs text-brand-ink hover:border-brand-ink font-semibold"
              title="Generar propuesta de respuesta con IA basada en el último mensaje"
            >
              <Sparkles className={`w-3.5 h-3.5 text-brand-ink ${generatingDraft ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">{generatingDraft ? 'Generando...' : 'Sugerir con IA'}</span>
            </Button>
          )}
        </div>
      </div>

      {/* Lista de Mensajes */}
      <div className="flex-1 overflow-y-auto p-3 sm:p-4 lg:p-5 space-y-2.5 sm:space-y-3">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center text-xs text-text-muted">
            No hay mensajes registrados en este hilo de conversación.
          </div>
        ) : (
          messages.map((m) => {
            if (m.isStatusNote) {
              return (
                <div key={m.id} className="text-center my-2">
                  <span className="text-[11px] sm:text-xs text-text-muted">{m.text}</span>
                </div>
              );
            }

            const isMe = m.sender === 'ivana' || m.sender === 'bot';

            return (
              <div
                key={m.id}
                className={`flex flex-col ${isMe ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-[88%] sm:max-w-[78%] p-3 sm:p-3.5 rounded-lg text-xs sm:text-sm leading-relaxed ${
                    isMe
                      ? 'bg-brand-ink text-white shadow-subtle'
                      : 'bg-white border border-border/70 text-brand-ink shadow-subtle'
                  }`}
                >
                  <div
                    className={`flex items-center justify-between gap-3 sm:gap-4 mb-1 text-[11px] sm:text-xs ${
                      isMe ? 'text-surface-muted' : 'text-text-muted'
                    }`}
                  >
                    <span className="font-semibold">
                      {m.sender === 'bot'
                        ? 'Dra. Ivana Seliz (Auto)'
                        : m.sender === 'ivana'
                        ? 'Dra. Ivana Seliz'
                        : senderName}
                    </span>
                    <span className="shrink-0">{m.timestamp}</span>
                  </div>
                  <p className="whitespace-pre-line text-xs sm:text-sm leading-relaxed">{m.text}</p>
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Formulario de Envío de Mensaje */}
      <form
        onSubmit={handleSend}
        className="p-2.5 sm:p-3 border-t border-border/70 bg-white flex items-center gap-2 shrink-0 min-w-0"
      >
        <button
          type="button"
          aria-label="Adjuntar archivo"
          className="grid size-9 sm:size-10 place-items-center rounded-base border border-border/70 text-text-secondary hover:bg-surface-muted hover:text-brand-ink transition-colors cursor-pointer shrink-0"
        >
          <Paperclip className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
        </button>
        <input
          type="text"
          placeholder="Escribir mensaje en representación de la administración..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          className="flex-1 min-w-0 min-h-9 sm:min-h-10 bg-white border border-border/70 text-brand-ink text-xs sm:text-sm rounded-base px-3 sm:px-3.5 outline-none transition-colors focus:border-brand-ink focus:ring-1 focus:ring-brand-ink"
        />
        <Button type="submit" size="sm" className="min-h-9 sm:min-h-10 px-3 sm:px-3.5 shrink-0">
          <Send className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Enviar</span>
        </Button>
      </form>
    </div>
  );
}
