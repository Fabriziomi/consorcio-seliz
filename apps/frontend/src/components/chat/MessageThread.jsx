import React, { useState } from 'react';
import { Send, Building, Paperclip } from 'lucide-react';
import { Button } from '../ui/Button.jsx';
import { Badge } from '../ui/Badge.jsx';

export function MessageThread({
  senderName,
  phone,
  consorcio,
  unidad,
  messages,
  onSendMessage,
}) {
  const [inputText, setInputText] = useState('');

  const handleSend = (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    onSendMessage(inputText.trim());
    setInputText('');
  };

  return (
    <div className="h-full flex flex-col bg-surface-soft">
      {/* Cabecera del Hilo */}
      <div className="p-4 border-b border-border flex items-center justify-between bg-white shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-brand-ink text-white flex items-center justify-center text-xs font-bold shadow-sm">
            {senderName ? senderName.charAt(0) : 'V'}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-brand-ink">{senderName}</span>
              <span className="text-xs font-mono text-text-muted">{phone}</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-text-secondary mt-0.5">
              <span className="flex items-center gap-1">
                <Building className="w-3.5 h-3.5 text-text-muted" />
                {consorcio}
              </span>
              <span>•</span>
              <span className="font-medium text-brand-ink">{unidad}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="neutral">Evolution API v2</Badge>
        </div>
      </div>

      {/* Lista de Mensajes */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
        {messages.map((m) => {
          if (m.isStatusNote) {
            return (
              <div key={m.id} className="text-center my-3">
                <Badge variant="neutral">{m.text}</Badge>
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
                className={`max-w-[78%] p-4 rounded-lg text-sm leading-relaxed ${
                  isMe
                    ? 'bg-brand-ink bg-[image:var(--gradient-action-primary)] text-white shadow-card'
                    : 'bg-white border border-border text-brand-ink shadow-subtle'
                }`}
              >
                <div
                  className={`flex items-center justify-between gap-4 mb-1.5 text-xs font-mono ${
                    isMe ? 'text-surface-muted' : 'text-text-muted'
                  }`}
                >
                  <span className="font-semibold uppercase tracking-wider text-[11px]">
                    {m.sender === 'bot'
                      ? 'Dra. Ivana Seliz (Auto)'
                      : m.sender === 'ivana'
                      ? 'Dra. Ivana Seliz'
                      : senderName}
                  </span>
                  <span>{m.timestamp}</span>
                </div>
                <p className="whitespace-pre-line text-sm leading-relaxed">{m.text}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Formulario de Envío de Mensaje */}
      <form
        onSubmit={handleSend}
        className="p-4 border-t border-border bg-white flex items-center gap-2.5 shrink-0"
      >
        <button
          type="button"
          aria-label="Adjuntar archivo"
          className="grid size-11 place-items-center rounded-base border border-border text-text-secondary hover:bg-surface-muted hover:text-brand-ink transition-colors cursor-pointer"
        >
          <Paperclip className="w-4 h-4" />
        </button>
        <input
          type="text"
          placeholder="Escribir mensaje en representación de la administración..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          className="flex-1 min-h-11 bg-white border border-border text-brand-ink text-sm rounded-base px-4 outline-none transition-colors focus:border-brand-ink focus:ring-1 focus:ring-brand-ink"
        />
        <Button type="submit" size="md">
          <Send className="w-4 h-4" />
          <span>Enviar</span>
        </Button>
      </form>
    </div>
  );
}
