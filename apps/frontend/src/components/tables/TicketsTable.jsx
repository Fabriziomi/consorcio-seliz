import React from 'react';
import { Card, CardHeader, CardContent } from '../ui/Card.jsx';
import { Badge } from '../ui/Badge.jsx';

export function TicketsTable({ tickets, onSelectTicket }) {
  return (
    <Card className="min-w-0">
      <CardHeader>
        <div className="flex flex-col gap-1.5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-sm sm:text-base font-bold tracking-tight text-brand-ink">
              Tickets & Solicitudes de Vecinos
            </h2>
            <p className="text-[11px] sm:text-xs text-text-secondary mt-0.5">
              Registro operativo de reclamos edilicios, cobranzas y consultas administrativas
            </p>
          </div>
          <span className="text-xs text-text-muted font-medium">{tickets.length} registros</span>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {/* Vista Móvil / Tablet: Mosaico Orgánico de Tarjetas */}
        <div className="md:hidden grid grid-cols-1 sm:grid-cols-2 gap-2.5 p-2.5 sm:p-3 bg-surface-soft/30">
          {tickets.map((t) => (
            <div
              key={t.id}
              onClick={() => onSelectTicket && onSelectTicket(t.id)}
              className="bg-white border border-border/70 rounded-base p-3 space-y-2 shadow-subtle hover:border-brand-ink/40 transition-colors cursor-pointer"
            >
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-text-secondary">{t.id}</span>
                <span className="text-[11px] text-text-muted">{t.creado_el}</span>
              </div>

              <div>
                <h3 className="text-xs sm:text-sm font-bold text-brand-ink">{t.consorcio}</h3>
                <p className="text-[11px] text-text-secondary">{t.unidad} — <span className="font-medium text-brand-ink">{t.contacto}</span></p>
              </div>

              <p className="text-xs text-brand-ink leading-relaxed">
                {t.descripcion}
              </p>

              <div className="flex items-center gap-1.5 pt-1 border-t border-border/50">
                {t.prioridad === 'CRITICA' ? (
                  <Badge variant="danger">Crítica</Badge>
                ) : t.prioridad === 'ALTA' ? (
                  <Badge variant="warning">Alta</Badge>
                ) : (
                  <Badge variant="neutral">Normal</Badge>
                )}

                {t.estado === 'RESUELTO' ? (
                  <Badge variant="success">Resuelto</Badge>
                ) : t.estado === 'EN_REVISION' ? (
                  <Badge variant="info">En Revisión</Badge>
                ) : t.estado === 'DERIVADO' ? (
                  <Badge variant="warning">Derivado</Badge>
                ) : (
                  <Badge variant="neutral">Nuevo</Badge>
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
                  onClick={() => onSelectTicket && onSelectTicket(t.id)}
                  className="hover:bg-surface-muted/60 cursor-pointer transition-colors"
                >
                  <td className="px-3.5 py-2.5 text-xs font-semibold text-text-secondary">
                    {t.id}
                  </td>
                  <td className="px-3.5 py-2.5">
                    <div className="font-semibold text-brand-ink">{t.consorcio}</div>
                    <div className="text-[11px] text-text-secondary">{t.unidad}</div>
                  </td>
                  <td className="px-3.5 py-2.5 text-brand-ink font-medium">{t.contacto}</td>
                  <td className="px-3.5 py-2.5 max-w-xs text-text-secondary">
                    <span className="truncate block sm:inline">
                      {t.descripcion}
                    </span>
                  </td>
                  <td className="px-3.5 py-2.5">
                    {t.prioridad === 'CRITICA' ? (
                      <Badge variant="danger">Crítica</Badge>
                    ) : t.prioridad === 'ALTA' ? (
                      <Badge variant="warning">Alta</Badge>
                    ) : (
                      <Badge variant="neutral">Normal</Badge>
                    )}
                  </td>
                  <td className="px-3.5 py-2.5">
                    {t.estado === 'RESUELTO' ? (
                      <Badge variant="success">Resuelto</Badge>
                    ) : t.estado === 'EN_REVISION' ? (
                      <Badge variant="info">En Revisión</Badge>
                    ) : t.estado === 'DERIVADO' ? (
                      <Badge variant="warning">Derivado</Badge>
                    ) : (
                      <Badge variant="neutral">Nuevo</Badge>
                    )}
                  </td>
                  <td className="px-3.5 py-2.5 text-[11px] text-text-muted">
                    {t.creado_el}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
