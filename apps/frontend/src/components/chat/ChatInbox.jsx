import React, { useState } from 'react';
import {
  Search,
  Tag,
  User,
  CheckCircle2,
  Clock,
  AlertCircle,
} from 'lucide-react';

export function ChatInbox({ conversations = [], selectedId, onSelect }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [failedImages, setFailedImages] = useState({});

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
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-white bg-brand-ink px-2 py-0.5 rounded-full">
            <AlertCircle size={13} strokeWidth={2} />
            <span>Emergencia</span>
          </span>
        );
      case 'pending':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-brand-ink bg-surface-muted border border-border px-2 py-0.5 rounded-full">
            <Clock size={13} strokeWidth={2} />
            <span>Pendiente</span>
          </span>
        );
      case 'resolved':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-brand-ink bg-surface-soft border border-border px-2 py-0.5 rounded-full">
            <CheckCircle2 size={13} strokeWidth={2} />
            <span>Resuelto</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-text-secondary bg-surface-muted/60 border border-border/70 px-2 py-0.5 rounded-full">
            <span>Abierto</span>
          </span>
        );
    }
  };

  const handleImageError = (id) => {
    setFailedImages((prev) => ({ ...prev, [id]: true }));
  };

  return (
    <div className="h-full flex flex-col bg-white border-b md:border-b-0 md:border-r border-border min-w-0">
      {/* Cabecera del Inbox */}
      <div className="p-3.5 sm:p-4 border-b border-border/80 space-y-3 shrink-0 bg-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-lg sm:text-xl font-bold tracking-tight text-brand-ink">
              Bandeja de Conversaciones
            </h2>
            <span className="text-xs font-bold text-text-muted bg-surface-muted px-2 py-0.5 rounded-full border border-border/60">
              {filtered.length}
            </span>
          </div>
        </div>

        {/* Buscador con Phosphor MagnifyingGlass */}
        <div className="relative">
          <Search size={18} strokeWidth={1.8} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none" />
          <input
            type="text"
            placeholder="Buscar por vecino, teléfono o unidad…"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full h-10 sm:h-11 bg-surface-soft border border-border/80 text-brand-ink text-sm rounded-xl pl-10 pr-4 outline-none transition-all focus:border-brand-ink focus:bg-white focus:ring-1 focus:ring-brand-ink/20 shadow-2xs"
          />
        </div>

        {/* Filtros Monocromáticos */}
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
              className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors duration-150 whitespace-nowrap cursor-pointer touch-manipulation shadow-2xs border ${
                filterStatus === f.id
                  ? 'bg-brand-ink text-white font-bold shadow-xs border-brand-ink'
                  : 'bg-surface-muted text-text-secondary hover:bg-surface-soft hover:text-brand-ink border-border/70'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Lista de Conversaciones con Avatar Original */}
      <div className="flex-1 overflow-y-auto divide-y divide-border/60">
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
            const avatar = c.avatarUrl || c.foto_url || c.contacto_foto_url;
            const hasBrokenImg = failedImages[c.id];

            return (
              <div
                key={c.id}
                onClick={() => onSelect(c.id)}
                className={`p-3 sm:px-3.5 sm:py-3 cursor-pointer transition-colors duration-150 flex items-start gap-3 touch-manipulation border-l-2 ${
                  isSelected
                    ? 'bg-surface-soft border-brand-ink'
                    : 'border-transparent hover:bg-surface-soft/60'
                }`}
              >
                {/* Avatar con prioridad a imagen original */}
                <div className="size-10 sm:size-11 rounded-full shrink-0 overflow-hidden bg-brand-ink text-white flex items-center justify-center font-bold text-xs sm:text-sm shadow-2xs relative border border-border/60">
                  {avatar && !hasBrokenImg ? (
                    <img
                      src={avatar}
                      alt={name}
                      onError={() => handleImageError(c.id)}
                      className="size-full object-cover rounded-full"
                      loading="lazy"
                    />
                  ) : name ? (
                    <span>{name.charAt(0).toUpperCase()}</span>
                  ) : (
                    <User size={20} strokeWidth={1.8} />
                  )}
                </div>

                <div className="flex-1 min-w-0 flex flex-col gap-1">
                  <div className="flex items-center justify-between gap-1.5">
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
                    <span className="truncate max-w-[190px]">
                      {consorcio} {unidad ? `— ${unidad}` : ''}
                    </span>
                    {getStatusBadge(status)}
                  </div>

                  <p className="text-xs text-text-secondary line-clamp-2 leading-relaxed">
                    {lastMsg}
                  </p>

                  {/* Etiquetas monocromáticas */}
                  {etiquetas.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-0.5">
                      {etiquetas.map((tag) => (
                        <span
                          key={tag}
                          className="text-[9px] font-bold tracking-wider uppercase px-1.5 py-0.5 rounded-md bg-surface-muted text-text-secondary border border-border/60 flex items-center gap-1"
                        >
                          <Tag size={11} strokeWidth={1.8} className="text-text-muted" />
                          <span>{tag}</span>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
