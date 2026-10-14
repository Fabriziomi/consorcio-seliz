import React from 'react';
import { Card, CardHeader, CardContent } from '../ui/Card.jsx';
import { Badge } from '../ui/Badge.jsx';

export function TicketsTable({ tickets, onSelectTicket }) {
  return (
    <Card className="min-w-0">
      <CardHeader>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-base font-bold tracking-tight text-brand-ink">
              Tickets & Solicitudes de Vecinos
            </h2>
            <p className="text-xs text-text-secondary mt-0.5">
              Registro operativo de reclamos edilicios, cobranzas y consultas administrativas
            </p>
          </div>
          <span className="text-xs text-text-muted font-medium">{tickets.length} registros</span>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[750px] text-left text-sm">
            <thead className="bg-surface-muted text-xs uppercase tracking-[0.08em] text-text-muted border-b border-border">
              <tr>
                <th scope="col" className="px-4 py-3.5 font-semibold">ID</th>
                <th scope="col" className="px-4 py-3.5 font-semibold">Consorcio & Unidad</th>
                <th scope="col" className="px-4 py-3.5 font-semibold">Contacto</th>
                <th scope="col" className="px-4 py-3.5 font-semibold">Descripción</th>
                <th scope="col" className="px-4 py-3.5 font-semibold">Prioridad</th>
                <th scope="col" className="px-4 py-3.5 font-semibold">Estado</th>
                <th scope="col" className="px-4 py-3.5 font-semibold">Fecha</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {tickets.map((t) => (
                <tr
                  key={t.id}
                  onClick={() => onSelectTicket && onSelectTicket(t.id)}
                  className="hover:bg-surface-muted/60 cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3.5 text-xs font-semibold text-text-secondary">
                    {t.id}
                  </td>
                  <td className="px-4 py-3.5">
                    <div className="font-semibold text-brand-ink">{t.consorcio}</div>
                    <div className="text-xs text-text-secondary">{t.unidad}</div>
                  </td>
                  <td className="px-4 py-3.5 text-brand-ink font-medium">{t.contacto}</td>
                  <td className="px-4 py-3.5 max-w-xs text-text-secondary">
                    <span className="truncate block sm:inline">
                      {t.descripcion}
                    </span>
                  </td>
                  <td className="px-4 py-3.5">
                    {t.prioridad === 'CRITICA' ? (
                      <Badge variant="danger">Crítica</Badge>
                    ) : t.prioridad === 'ALTA' ? (
                      <Badge variant="warning">Alta</Badge>
                    ) : (
                      <Badge variant="neutral">Normal</Badge>
                    )}
                  </td>
                  <td className="px-4 py-3.5">
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
                  <td className="px-4 py-3.5 text-xs text-text-muted">
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
