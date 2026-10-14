import React from 'react';
import { RotateCcw } from 'lucide-react';
import { Card, CardHeader, CardContent } from '../ui/Card.jsx';
import { Badge } from '../ui/Badge.jsx';
import { Button } from '../ui/Button.jsx';

const ESTADOS_DISPONIBLES = [
  { value: 'NUEVO', label: 'Nuevo' },
  { value: 'EN_REVISION', label: 'En Revisión' },
  { value: 'DERIVADO', label: 'Derivado' },
  { value: 'RESUELTO', label: 'Resuelto' },
];

export function TicketsTable({
  tickets = [],
  onSelectTicket,
  onUpdateStatus,
  onRefresh,
  loading = false,
}) {
  const getBadgeVariant = (prioridad) => {
    switch (prioridad) {
      case 'CRITICA':
        return 'danger';
      case 'ALTA':
        return 'warning';
      default:
        return 'neutral';
    }
  };

  const getStatusBadge = (estado) => {
    switch (estado) {
      case 'RESUELTO':
        return <Badge variant="success">Resuelto</Badge>;
      case 'EN_REVISION':
        return <Badge variant="info">En Revisión</Badge>;
      case 'DERIVADO':
        return <Badge variant="warning">Derivado</Badge>;
      default:
        return <Badge variant="neutral">Nuevo</Badge>;
    }
  };

  return (
    <Card className="min-w-0">
      <CardHeader>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-sm sm:text-base font-bold tracking-tight text-brand-ink">
              Tickets & Solicitudes de Vecinos
            </h2>
            <p className="text-[11px] sm:text-xs text-text-secondary mt-0.5">
              Registro operativo en tiempo real de reclamos edilicios, cobranzas y emergencias
            </p>
          </div>
          <div className="flex items-center gap-2 self-start sm:self-auto">
            {onRefresh && (
              <Button
                variant="secondary"
                size="sm"
                onClick={onRefresh}
                disabled={loading}
                className="h-7 px-2.5 text-xs text-text-secondary hover:text-brand-ink"
                title="Actualizar tickets desde la base de datos"
              >
                <RotateCcw size={12} className={loading ? 'animate-spin' : ''} />
                <span>Actualizar</span>
              </Button>
            )}
            <span className="text-xs text-text-muted font-medium bg-surface-muted px-2 py-0.5 rounded-full border border-border/60">
              {tickets.length} registros
            </span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {tickets.length === 0 ? (
          <div className="p-8 text-center text-xs text-text-muted">
            No hay tickets registrados en el sistema.
          </div>
        ) : (
          <>
            {/* Vista Móvil / Tablet: Mosaico Orgánico de Tarjetas */}
            <div className="md:hidden grid grid-cols-1 sm:grid-cols-2 gap-2.5 p-2.5 sm:p-3 bg-surface-soft/30">
              {tickets.map((t) => (
                <div
                  key={t.id}
                  className="bg-white border border-border/70 rounded-base p-3 space-y-2 shadow-subtle hover:border-brand-ink/40 transition-colors"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-text-secondary">{t.id}</span>
                    <span className="text-[11px] text-text-muted">{t.creado_el}</span>
                  </div>

                  <div>
                    <h3 className="text-xs sm:text-sm font-bold text-brand-ink">
                      {t.consorcio || t.consorcio_nombre}
                    </h3>
                    <p className="text-[11px] text-text-secondary">
                      {t.unidad || t.contacto_unidad} —{' '}
                      <span className="font-medium text-brand-ink">
                        {t.contacto || t.contacto_nombre}
                      </span>
                    </p>
                  </div>

                  <p className="text-xs text-brand-ink leading-relaxed">
                    {t.descripcion}
                  </p>

                  <div className="flex items-center justify-between pt-2 border-t border-border/50 text-xs">
                    <div className="flex items-center gap-1.5">
                      <Badge variant={getBadgeVariant(t.prioridad)}>
                        {t.prioridad === 'CRITICA' ? 'Crítica' : t.prioridad === 'ALTA' ? 'Alta' : 'Normal'}
                      </Badge>
                      {getStatusBadge(t.estado)}
                    </div>

                    {onUpdateStatus && (
                      <select
                        value={t.estado}
                        onChange={(e) => onUpdateStatus(t.rawId || t.id, e.target.value)}
                        className="text-[11px] bg-surface-muted border border-border rounded px-1.5 py-0.5 text-brand-ink font-medium focus:outline-none focus:border-brand-ink cursor-pointer"
                        title="Cambiar estado del ticket"
                      >
                        {ESTADOS_DISPONIBLES.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Vista Desktop / Pantalla Grande: Tabla Clásica */}
            <div className="hidden md:block overflow-x-auto">
              <table className="w-full min-w-[700px] text-left text-xs sm:text-sm">
                <thead className="bg-surface-muted text-[11px] uppercase tracking-[0.08em] text-text-muted border-b border-border/70">
                  <tr>
                    <th scope="col" className="px-3.5 py-2.5 font-semibold">ID</th>
                    <th scope="col" className="px-3.5 py-2.5 font-semibold">Consorcio & Unidad</th>
                    <th scope="col" className="px-3.5 py-2.5 font-semibold">Contacto</th>
                    <th scope="col" className="px-3.5 py-2.5 font-semibold">Descripción</th>
                    <th scope="col" className="px-3.5 py-2.5 font-semibold">Prioridad</th>
                    <th scope="col" className="px-3.5 py-2.5 font-semibold">Estado</th>
                    <th scope="col" className="px-3.5 py-2.5 font-semibold">Fecha</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/70">
                  {tickets.map((t) => (
                    <tr
                      key={t.id}
                      className="hover:bg-surface-muted/60 transition-colors"
                    >
                      <td className="px-3.5 py-2.5 text-xs font-semibold text-text-secondary whitespace-nowrap">
                        {t.id}
                      </td>
                      <td className="px-3.5 py-2.5">
                        <div className="font-semibold text-brand-ink">
                          {t.consorcio || t.consorcio_nombre}
                        </div>
                        <div className="text-[11px] text-text-secondary">
                          {t.unidad || t.contacto_unidad}
                        </div>
                      </td>
                      <td className="px-3.5 py-2.5 text-brand-ink font-medium whitespace-nowrap">
                        {t.contacto || t.contacto_nombre}
                      </td>
                      <td className="px-3.5 py-2.5 max-w-xs text-text-secondary">
                        <span className="truncate block">
                          {t.descripcion}
                        </span>
                      </td>
                      <td className="px-3.5 py-2.5 whitespace-nowrap">
                        <Badge variant={getBadgeVariant(t.prioridad)}>
                          {t.prioridad === 'CRITICA' ? 'Crítica' : t.prioridad === 'ALTA' ? 'Alta' : 'Normal'}
                        </Badge>
                      </td>
                      <td className="px-3.5 py-2.5 whitespace-nowrap">
                        {onUpdateStatus ? (
                          <div className="flex items-center gap-2">
                            {getStatusBadge(t.estado)}
                            <select
                              value={t.estado}
                              onChange={(e) => onUpdateStatus(t.rawId || t.id, e.target.value)}
                              className="text-[11px] bg-surface-muted border border-border/80 rounded px-1.5 py-0.5 text-brand-ink font-medium hover:border-brand-ink focus:outline-none cursor-pointer"
                              title="Cambiar estado del ticket"
                            >
                              {ESTADOS_DISPONIBLES.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                  {opt.label}
                                </option>
                              ))}
                            </select>
                          </div>
                        ) : (
                          getStatusBadge(t.estado)
                        )}
                      </td>
                      <td className="px-3.5 py-2.5 text-[11px] text-text-muted whitespace-nowrap">
                        {t.creado_el}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
