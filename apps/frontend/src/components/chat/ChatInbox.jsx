import React, { useState } from 'react';
import { Search } from 'lucide-react';
import { Badge } from '../ui/Badge.jsx';

export function ChatInbox({ conversations, selectedId, onSelect }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');

  const filtered = conversations.filter((c) => {
    const matchesSearch =
      c.senderName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.phone.includes(searchTerm) ||
      c.consorcio.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.unidad.toLowerCase().includes(searchTerm.toLowerCase());

    if (filterStatus === 'all') return matchesSearch;
    return matchesSearch && c.status === filterStatus;
  });

  return (
    <div className="h-full flex flex-col bg-white border-b md:border-b-0 md:border-r border-border min-w-0">
      {/* Cabecera del Inbox */}
      <div className="p-3 sm:p-4 border-b border-border space-y-2.5 sm:space-y-3 shrink-0">
        <div className="flex items-center justify-between">
          <h2 className="text-xs sm:text-sm font-bold tracking-tight text-brand-ink">
            Conversaciones
          </h2>
          <span className="text-[11px] sm:text-xs text-text-muted">{filtered.length}</span>
        </div>

        {/* Buscador */}
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none" />
          <input
            type="text"
            placeholder="Buscar vecino o unidad…"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full min-h-9 sm:min-h-10 bg-surface-soft border border-border text-brand-ink text-xs rounded-base pl-9 pr-3 outline-none transition-colors focus:border-brand-ink focus:bg-white"
          />
        </div>

        {/* Filtros tipo pills */}
        <div className="flex gap-1.5 pt-0.5 overflow-x-auto pb-0.5 no-scrollbar">
          {[
            { id: 'all', label: 'Todos' },
            { id: 'open', label: 'Abiertos' },
            { id: 'emergency', label: 'Críticos' },
          ].map((f) => (
            <button
              key={f.id}
              onClick={() => setFilterStatus(f.id)}
              className={`text-[11px] sm:text-xs font-semibold px-3 py-1.5 rounded-full transition-colors whitespace-nowrap cursor-pointer touch-manipulation ${
                filterStatus === f.id
                  ? 'bg-brand-ink text-white shadow-sm'
                  : 'bg-surface-muted text-text-secondary hover:bg-surface-soft hover:text-brand-ink border border-border'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Lista de Mensajes */}
      <div className="flex-1 overflow-y-auto divide-y divide-border">
        {filtered.map((c) => {
          const isSelected = c.id === selectedId;
          return (
            <div
              key={c.id}
              onClick={() => onSelect(c.id)}
              className={`p-3 sm:p-3.5 lg:p-4 cursor-pointer transition-colors flex flex-col gap-1.5 touch-manipulation ${
                isSelected
                  ? 'bg-surface-soft border-l-4 border-brand-ink'
                  : 'hover:bg-surface-soft/60'
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs sm:text-sm font-bold text-brand-ink truncate">
                  {c.senderName}
                </span>
                <span className="text-[11px] sm:text-xs text-text-muted shrink-0">
                  {c.timestamp}
                </span>
              </div>

              <div className="flex items-center justify-between gap-2 text-[11px] sm:text-xs text-text-secondary">
                <span className="truncate max-w-[200px]">
                  {c.consorcio} — {c.unidad}
                </span>
                {c.status === 'emergency' && (
                  <Badge variant="danger" className="text-[10px] min-h-5 px-1.5 py-0 shrink-0">
                    Emergencia
                  </Badge>
                )}
              </div>

              <p className="text-xs text-text-secondary line-clamp-2 leading-relaxed">
                {c.lastMessage}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
