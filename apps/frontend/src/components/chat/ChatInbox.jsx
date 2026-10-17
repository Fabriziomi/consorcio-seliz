import React, { useState } from 'react';
import {
  Search,
  Tag,
  User,
} from 'lucide-react';
import { Badge } from '../ui/Badge.jsx';

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
          <Badge variant="danger" size="xs" className="font-semibold shadow-2xs">
            <span className="size-1.5 rounded-full bg-rose-500 shrink-0 animate-pulse" />
            <span>Emergencia</span>
          </Badge>
        );
      case 'pending':
        return (
          <Badge variant="warning" size="xs" className="font-medium shadow-2xs">
            <span className="size-1.5 rounded-full bg-amber-500 shrink-0" />
            <span>Pendiente</span>
          </Badge>
        );
      case 'resolved':
        return (
          <Badge variant="success" size="xs" className="font-medium shadow-2xs">
            <span className="size-1.5 rounded-full bg-emerald-500 shrink-0" />
            <span>Resuelto</span>
          </Badge>
        );
      default:
        return (
          <Badge variant="neutral" size="xs" className="font-medium shadow-2xs">
            <span className="size-1.5 rounded-full bg-zinc-400 shrink-0" />
            <span>Abierto</span>
          </Badge>
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
          <Search size={18} strokeWidth={1.8} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none transition-transform duration-500" />
          <input
            type="text"
            placeholder="Buscar por vecino, teléfono o unidad…"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full h-10 sm:h-11 bg-surface-soft border border-border/80 text-brand-ink text-sm rounded-xl pl-10 pr-4 outline-none transition-all duration-500 focus:border-brand-ink focus:bg-white focus:ring-1 focus:ring-brand-ink/20 shadow-2xs"
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
              className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-all duration-500 whitespace-nowrap cursor-pointer touch-manipulation shadow-2xs border hover:scale-105 active:scale-95 ${
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
            const isSelected = Boolean(selectedId != null && (c.id === selectedId || String(c.id) === String(selectedId)));
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
                role="button"
                tabIndex={0}
                aria-selected={isSelected}
                onClick={() => onSelect(c.id)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onSelect(c.id);
                  }
                }}
                className={`group p-3 sm:px-3.5 sm:py-3 cursor-pointer transition-all duration-150 ease-out flex items-start gap-3 touch-manipulation border-l-4 active:scale-[0.99] outline-none ${
                  isSelected
                    ? 'bg-zinc-100 border-brand-ink shadow-2xs'
                    : 'border-transparent hover:bg-zinc-100/70 hover:translate-x-0.5 focus-visible:bg-zinc-100/70'
                }`}
              >
                {/* Avatar con prioridad a imagen original y zoom en hover */}
                <div
                  className={`size-10 sm:size-11 rounded-full shrink-0 overflow-hidden bg-brand-ink text-white flex items-center justify-center font-bold text-xs sm:text-sm shadow-2xs relative border transition-transform duration-200 group-hover:scale-105 ${
                    isSelected ? 'border-brand-ink ring-2 ring-brand-ink/20' : 'border-border/60'
                  }`}
                >
                  {avatar && !hasBrokenImg ? (
                    <img
                      src={avatar}
                      alt={name}
                      onError={() => handleImageError(c.id)}
                      className="size-full object-cover rounded-full transition-transform duration-200 group-hover:scale-105"
                      loading="lazy"
                    />
                  ) : name ? (
                    <span>{name.charAt(0).toUpperCase()}</span>
                  ) : (
                    <User size={20} strokeWidth={1.8} />
                  )}
                </div>

                <div className="flex-1 min-w-0 flex flex-col gap-1.5">
                  {/* Fila 1: Remitente y Hora/Fecha */}
                  <div className="flex items-center justify-between gap-2">
                    <span
                      className={`text-xs sm:text-sm truncate transition-colors duration-150 ${
                        isSelected
                          ? 'font-bold text-brand-ink'
                          : unread > 0
                          ? 'font-bold text-brand-ink'
                          : 'font-semibold text-brand-ink/90'
                      }`}
                    >
                      {name}
                    </span>
                    <span
                      className={`text-[10px] sm:text-[11px] shrink-0 ${
                        isSelected || unread > 0
                          ? 'text-brand-ink font-semibold'
                          : 'text-text-muted font-normal'
                      }`}
                    >
                      {timestamp}
                    </span>
                  </div>

                  {/* Fila 2: Consorcio & Unidad a la izquierda, Estado y Unread Badge a la derecha */}
                  <div className="flex items-center justify-between gap-2 min-w-0">
                    <div className="flex items-center gap-1.5 text-[11px] text-text-secondary truncate min-w-0">
                      <span className="truncate font-medium">{consorcio}</span>
                      {unidad && <span className="text-zinc-300 shrink-0">•</span>}
                      {unidad && <span className="truncate text-text-muted">{unidad}</span>}
                    </div>

                    <div className="flex items-center gap-1.5 shrink-0">
                      {getStatusBadge(status)}
                      {unread > 0 && (
                        <span className="min-w-4.5 h-4.5 px-1.5 rounded-full bg-brand-ink text-white text-[10px] font-bold flex items-center justify-center shrink-0 shadow-2xs transition-transform duration-200 group-hover:scale-110">
                          {unread}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Fila 3: Último mensaje */}
                  <p
                    className={`text-xs line-clamp-2 leading-relaxed ${
                      isSelected
                        ? 'text-zinc-800 font-medium'
                        : unread > 0
                        ? 'text-brand-ink font-medium'
                        : 'text-text-secondary'
                    }`}
                  >
                    {lastMsg}
                  </p>

                  {/* Fila 4: Etiquetas monocromáticas sutiles */}
                  {etiquetas.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-0.5">
                      {etiquetas.map((tag) => (
                        <span
                          key={tag}
                          className="text-[9px] sm:text-[10px] font-medium tracking-wide px-2 py-0.5 rounded-full bg-surface-muted text-text-secondary border border-border/70 flex items-center gap-1 shadow-2xs"
                        >
                          <Tag size={10} strokeWidth={1.8} className="text-text-muted shrink-0" />
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
