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
    <div className="border border-border/80 bg-white rounded-base p-2.5 sm:p-3 space-y-2 sm:space-y-2.5 shadow-subtle">
      {/* Encabezado */}
      <div className="flex items-center justify-between border-b border-border/60 pb-1.5">
        <span className="text-xs sm:text-sm font-semibold text-brand-ink">
          Respuesta sugerida
        </span>
      </div>

      {/* Cuerpo */}
      {isEditing ? (
        <textarea
          value={draftText}
          onChange={(e) => setDraftText(e.target.value)}
          rows={3}
          className="w-full bg-white border border-border rounded-base p-2.5 sm:p-3.5 text-xs sm:text-sm text-brand-ink outline-none transition-colors focus:border-brand-ink focus:ring-1 focus:ring-brand-ink leading-relaxed max-h-32 sm:max-h-44"
        />
      ) : (
        <div className="bg-surface-soft p-3 sm:p-3.5 rounded-base border border-border/80 text-xs sm:text-sm text-brand-ink leading-relaxed whitespace-pre-line max-h-28 sm:max-h-40 overflow-y-auto">
          {draftText}
        </div>
      )}

      {/* Botonera de Acciones */}
      <div className="flex items-center justify-between pt-1 gap-2 flex-wrap">
        <Button variant="ghost" size="sm" onClick={onReject} className="h-8 sm:h-9 px-2 sm:px-3 text-xs">
          <X className="w-3.5 h-3.5" />
          <span>Descartar</span>
        </Button>

        <div className="flex items-center gap-1.5 sm:gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setIsEditing(!isEditing)}
            className="h-8 sm:h-9 px-2.5 sm:px-3 text-xs"
          >
            <Edit2 className="w-3.5 h-3.5" />
            <span>{isEditing ? 'Listo' : 'Editar'}</span>
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => onApprove(draftText)}
            className="h-8 sm:h-9 px-3 sm:px-3.5 text-xs"
          >
            <Send className="w-3.5 h-3.5" />
            <span>
              <span className="inline sm:hidden">Aprobar</span>
              <span className="hidden sm:inline">Aprobar y Enviar</span>
            </span>
          </Button>
        </div>
      </div>
    </div>
  );
}
