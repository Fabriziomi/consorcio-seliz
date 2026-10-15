import React, { useState } from 'react';
import { Search, Tag } from 'lucide-react';
import { Badge } from '../ui/Badge.jsx';

export function ChatInbox({ conversations = [], selectedId, onSelect }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');

  const filtered = conversations.filter((c) => {
    const name = c.senderName || c.contacto_nombre || 'Vecino';
    const phone = c.phone || c.contacto_telefono || '';
    const consorcio = c.consorcio || c.consorcio_nombre || '';
    const unidad = c.unidad || c.contacto_unidad || '';
    const lastMsg = c.lastMessage || c.ultimo_mensaje || '';

    const q = searchTerm.toLowerCase();
    const matchesSearch =
      name.toLowerCase().includes(q) ||
      phone.includes(q) ||
      consorcio.toLowerCase().includes(q) ||
      unidad.toLowerCase().includes(q) ||
      lastMsg.toLowerCase().includes(q);

    if (filterStatus === 'all') return matchesSearch;
    const currentStatus = c.status || c.estado || 'open';
    return matchesSearch && currentStatus === filterStatus;
  });

  const getStatusBadge = (status) => {
    switch (status) {
      case 'emergency':
        return <Badge variant="danger" className="text-[10px] min-h-5 px-1.5 py-0">Emergencia</Badge>;
      case 'pending':
        return <Badge variant="warning" className="text-[10px] min-h-5 px-1.5 py-0">Pendiente</Badge>;
      case 'resolved':
        return <Badge variant="success" className="text-[10px] min-h-5 px-1.5 py-0">Resuelto</Badge>;
      default:
        return <Badge variant="neutral" className="text-[10px] min-h-5 px-1.5 py-0">Abierto</Badge>;
    }
  };

  return (
    <div className="h-full flex flex-col bg-white border-b md:border-b-0 md:border-r border-border min-w-0">
      {/* Cabecera del Inbox */}
      <div className="p-3 sm:p-4 border-b border-border space-y-2.5 sm:space-y-3 shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-xs sm:text-sm font-bold tracking-tight text-brand-ink">
              Bandeja de Conversaciones
            </h2>
            <span className="text-[11px] font-semibold text-text-muted bg-surface-muted px-2 py-0.5 rounded-full border border-border/60">
              {filtered.length}
            </span>
          </div>
        </div>

        {/* Buscador */}
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none" />
          <input
            type="text"
            placeholder="Buscar vecino, teléfono o unidad…"
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
            { id: 'pending', label: 'Pendientes' },
            { id: 'resolved', label: 'Resueltos' },
          ].map((f) => (
            <button
              key={f.id}
              onClick={() => setFilterStatus(f.id)}
              className={`text-[11px] sm:text-xs font-semibold px-2.5 py-1 rounded-full transition-colors whitespace-nowrap cursor-pointer touch-manipulation ${
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
        {filtered.length === 0 ? (
          <div className="p-8 text-center text-xs text-text-muted">
            No hay conversaciones para mostrar.
          </div>
        ) : (
          filtered.map((c) => {
            const isSelected = c.id === selectedId;
            const name = c.senderName || c.contacto_nombre || 'Vecino';
            const phone = c.phone || c.contacto_telefono || '';
            const consorcio = c.consorcio || c.consorcio_nombre || 'Consorcio General';
            const unidad = c.unidad || c.contacto_unidad || '';
            const lastMsg = c.lastMessage || c.ultimo_mensaje || 'Sin mensajes';
            const timestamp = c.timestamp || c.ultimo_mensaje_el || '';
            const unread = c.unreadCount || c.no_leidos_count || 0;
            const status = c.status || c.estado || 'open';
            const etiquetas = c.etiquetas || [];

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
                  <div className="flex items-center gap-1.5 min-w-0">
                    <span className="text-xs sm:text-sm font-bold text-brand-ink truncate">
                      {name}
                    </span>
                    {unread > 0 && (
                      <span className="size-4 rounded-full bg-brand-ink text-white text-[9px] font-bold flex items-center justify-center shrink-0">
                        {unread}
                      </span>
                    )}
                  </div>
                  <span className="text-[10px] sm:text-[11px] text-text-muted shrink-0 font-medium">
                    {timestamp}
                  </span>
                </div>

                <div className="flex items-center justify-between gap-2 text-[11px] text-text-secondary">
                  <span className="truncate max-w-[200px]">
                    {consorcio} {unidad ? `— ${unidad}` : ''}
                  </span>
                  {getStatusBadge(status)}
                </div>

                <p className="text-xs text-text-secondary line-clamp-2 leading-relaxed">
                  {lastMsg}
                </p>

                {/* Etiquetas */}
                {etiquetas.length > 0 && (
                  <div className="flex flex-wrap gap-1 pt-1">
                    {etiquetas.map((tag) => (
                      <span
                        key={tag}
                        className="text-[9px] font-bold tracking-wider uppercase px-1.5 py-0.5 rounded bg-surface-muted text-text-secondary border border-border/60"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
