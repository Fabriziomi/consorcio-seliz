import React, { useState } from 'react';
import { RotateCw, ChevronDown, ChevronUp } from 'lucide-react';
import { Card, CardHeader, CardContent } from '../ui/Card.jsx';
import { Badge } from '../ui/Badge.jsx';
import { Button } from '../ui/Button.jsx';
import { ScrollableTableContainer } from '../ui/ScrollableTableContainer.jsx';
import { SelectField } from '../ui/SelectField.jsx';
import { useToast } from '../ui/ToastNotification.jsx';

const ESTADOS_DISPONIBLES = [
  { value: 'NUEVO', label: 'Nuevo' },
  { value: 'EN_REVISION', label: 'En Revisión' },
  { value: 'DERIVADO', label: 'Derivado' },
  { value: 'RESUELTO', label: 'Resuelto' },
];

const ESTADO_BADGE_MAP = {
  NUEVO: 'neutral',
  EN_REVISION: 'info',
  DERIVADO: 'warning',
  RESUELTO: 'success',
};

export function TicketsTable({
  tickets = [],
  onSelectTicket,
  onUpdateStatus,
  onRefresh,
  loading = false,
}) {
  const toast = useToast();
  const [expandedRows, setExpandedRows] = useState(new Set());
  const [refreshConfirmed, setRefreshConfirmed] = useState(false);

  const handleRefresh = async () => {
    if (!onRefresh) return;
    await onRefresh();
    setRefreshConfirmed(true);
    toast.success('Tickets actualizados');
    setTimeout(() => setRefreshConfirmed(false), 1800);
  };

  const toggleRow = (id) =>
    setExpandedRows((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

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
            <h2 className="text-lg sm:text-xl font-bold tracking-tight text-brand-ink">
              Tickets &amp; Solicitudes de Vecinos
            </h2>
          </div>
          <div className="flex items-center gap-2 self-start sm:self-auto">
            {onRefresh && (
              <Button
                variant="secondary"
                size="icon-sm"
                onClick={handleRefresh}
                loading={loading}
                confirmed={refreshConfirmed}
                title="Actualizar tickets desde la base de datos"
                aria-label="Actualizar tickets"
              >
                <RotateCw size={18} strokeWidth={2} />
              </Button>
            )}
            <span className="text-xs text-text-muted font-medium bg-surface-muted px-2.5 py-1 rounded-full border border-border/60">
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
          <ScrollableTableContainer>
            <table className="w-full text-left text-xs sm:text-sm" style={{ minWidth: '1280px' }}>
              <thead className="bg-surface-muted text-[11px] uppercase tracking-[0.08em] text-text-muted border-b border-border/70">
                <tr>
                  <th scope="col" className="px-3.5 py-2.5 font-semibold whitespace-nowrap" style={{ minWidth: '144px' }}>ID</th>
                  <th scope="col" className="px-3.5 py-2.5 font-semibold" style={{ minWidth: '252px' }}>Consorcio &amp; Unidad</th>
                  <th scope="col" className="px-3.5 py-2.5 font-semibold whitespace-nowrap" style={{ minWidth: '156px' }}>Contacto</th>
                  <th scope="col" className="px-3.5 py-2.5 font-semibold" style={{ minWidth: '300px' }}>Descripción</th>
                  <th scope="col" className="px-3.5 py-2.5 font-semibold text-center whitespace-nowrap" style={{ minWidth: '108px' }}>Prioridad</th>
                  <th scope="col" className="px-3.5 py-2.5 font-semibold text-center whitespace-nowrap" style={{ minWidth: '192px' }}>Estado</th>
                  <th scope="col" className="px-3.5 py-2.5 font-semibold whitespace-nowrap" style={{ minWidth: '121px' }}>Fecha</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/70">
                {tickets.map((t) => (
                  <tr
                    key={t.id}
                    className="hover:bg-surface-muted/60 transition-colors"
                  >
                    <td className="px-3.5 py-2.5 text-xs font-semibold text-text-secondary whitespace-nowrap">
                      <div>{t.id}</div>
                      {t.expediente_codigo && (
                        <span className="inline-block mt-0.5 text-[10px] font-medium px-1.5 py-0.5 rounded bg-brand-sand/70 text-brand-navy border border-brand-sand">
                          #{t.expediente_codigo}
                        </span>
                      )}
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
                    <td className="px-3.5 py-2.5 text-text-secondary leading-relaxed">
                      <div
                        className={`text-xs sm:text-sm leading-relaxed ${
                          expandedRows.has(t.id) ? '' : 'line-clamp-2'
                        }`}
                      >
                        {t.descripcion}
                      </div>
                      {t.descripcion && t.descripcion.length > 80 && (
                        <button
                          type="button"
                          onClick={() => toggleRow(t.id)}
                          className="mt-1 text-[11px] font-semibold text-brand-ink/70 hover:text-brand-ink transition-colors cursor-pointer flex items-center gap-1"
                        >
                          {expandedRows.has(t.id) ? (
                            <>
                              <span>Ver menos</span>
                              <ChevronUp size={14} strokeWidth={2} />
                            </>
                          ) : (
                            <>
                              <span>Ver descripción completa</span>
                              <ChevronDown size={14} strokeWidth={2} />
                            </>
                          )}
                        </button>
                      )}
                    </td>
                    <td className="px-3.5 py-2.5 text-center whitespace-nowrap">
                      <Badge variant={getBadgeVariant(t.prioridad)}>
                        {t.prioridad}
                      </Badge>
                    </td>
                    <td className="px-3.5 py-2.5 text-center whitespace-nowrap">
                      {onUpdateStatus ? (
                        <div className="flex items-center justify-center">
                          <SelectField
                            variant="badge"
                            size="xs"
                            value={t.estado}
                            badgeVariantMap={ESTADO_BADGE_MAP}
                            onChange={(e) => onUpdateStatus(t.id, e.target.value)}
                            options={ESTADOS_DISPONIBLES}
                            aria-label="Cambiar estado del ticket"
                          />
                        </div>
                      ) : (
                        getStatusBadge(t.estado)
                      )}
                    </td>
                    <td className="px-3.5 py-2.5 text-xs text-text-muted whitespace-nowrap">
                      {t.creado_el}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </ScrollableTableContainer>
        )}
      </CardContent>
    </Card>
  );
}
