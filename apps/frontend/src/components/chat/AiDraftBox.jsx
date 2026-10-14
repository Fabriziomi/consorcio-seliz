import React, { useState } from 'react';
import { Edit2, X, Send } from 'lucide-react';
import { Button } from '../ui/Button.jsx';

export function AiDraftBox({
  initialDraft,
  onApprove,
  onReject,
}) {
  const [draftText, setDraftText] = useState(initialDraft);
  const [isEditing, setIsEditing] = useState(false);

  return (
    <div className="border border-border bg-white rounded-lg p-4 space-y-3.5 shadow-card">
      {/* Encabezado */}
      <div className="flex items-center justify-between border-b border-border pb-2.5">
        <span className="text-sm font-semibold text-brand-ink">
          Respuesta sugerida
        </span>
      </div>

      {/* Cuerpo */}
      {isEditing ? (
        <textarea
          value={draftText}
          onChange={(e) => setDraftText(e.target.value)}
          rows={4}
          className="w-full bg-white border border-border rounded-base p-3.5 text-sm text-brand-ink outline-none transition-colors focus:border-brand-ink focus:ring-1 focus:ring-brand-ink leading-relaxed"
        />
      ) : (
        <div className="bg-surface-soft p-4 rounded-base border border-border/80 text-sm text-brand-ink leading-relaxed whitespace-pre-line">
          {draftText}
        </div>
      )}

      {/* Botonera de Acciones */}
      <div className="flex items-center justify-between pt-1">
        <Button variant="ghost" size="sm" onClick={onReject}>
          <X className="w-3.5 h-3.5" />
          <span>Descartar</span>
        </Button>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setIsEditing(!isEditing)}
          >
            <Edit2 className="w-3.5 h-3.5" />
            <span>{isEditing ? 'Listo' : 'Editar'}</span>
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => onApprove(draftText)}
          >
            <Send className="w-3.5 h-3.5" />
            <span>Aprobar y Enviar</span>
          </Button>
        </div>
      </div>
    </div>
  );
}
