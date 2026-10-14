import React, { useState } from 'react';
import { RotateCcw, Send, Users, ChevronDown, ChevronUp, CheckCircle, Clock, AlertTriangle } from 'lucide-react';
import { Card, CardHeader, CardContent } from '../ui/Card.jsx';
import { Badge } from '../ui/Badge.jsx';
import { Button } from '../ui/Button.jsx';
import { ScrollableTableContainer } from '../ui/ScrollableTableContainer.jsx';
import { SelectField } from '../ui/SelectField.jsx';

const ESTADOS_EXPEDIENTE = [
  { value: 'ABIERTO', label: 'Abierto' },
  { value: 'EN_CURSO', label: 'En Curso' },
  { value: 'EN_ESPERA_PROVEEDOR', label: 'En Espera Proveedor' },
  { value: 'RESUELTO', label: 'Resuelto' },
  { value: 'CERRADO', label: 'Cerrado' },
];

const ESTADO_BADGE_MAP = {
  ABIERTO: 'neutral',
  EN_CURSO: 'info',
  EN_ESPERA_PROVEEDOR: 'warning',
  RESUELTO: 'success',
  CERRADO: 'neutral',
};

const CATEGORIA_LABELS = {
  ASCENSORES: 'Ascensores',
  PLOMERIA: 'Plomería / Agua',
  ELECTRICIDAD: 'Electricidad',
  GAS_CALEFACCION: 'Gas & Calefacción',
  PORTON_ACCESO: 'Portón & Accesos',
  LIMPIEZA_AREAS_COMUNES: 'Limpieza Palieres',
  SEGURIDAD: 'Seguridad',
  ADMINISTRACION_CONSULTA: 'Administración',
  OTRO: 'General',
};

export function ExpedientesTable({
  expedientes = [],
  loading = false,
  onRefresh,
  onUpdateStatus,
  onNotifyNeighbors,
}) {
  const [expandedRows, setExpandedRows] = useState(new Set());
  const [selectedExpedienteForNotify, setSelectedExpedienteForNotify] = useState(null);
  const [broadcastMessage, setBroadcastMessage] = useState('');
  const [sendingBroadcast, setSendingBroadcast] = useState(false);
  const [broadcastSuccess, setBroadcastSuccess] = useState(null);

  const toggleRow = (id) =>
    setExpandedRows((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

  const getPriorityBadgeVariant = (prioridad) => {
    switch (prioridad) {
      case 'CRITICA':
        return 'danger';
      case 'ALTA':
        return 'warning';
      default:
        return 'neutral';
    }
  };

  const handleOpenNotifyModal = (exp) => {
    setSelectedExpedienteForNotify(exp);
    setBroadcastMessage(
      `Estimados vecinos de ${exp.consorcio}: les informamos que respecto a la incidencia de ${exp.titulo} (Expediente #${exp.codigo}), la administración se encuentra gestionando el servicio técnico correspondiente. Les mantendremos informados.`
    );
    setBroadcastSuccess(null);
  };

  const handleSendBroadcast = async () => {
    if (!selectedExpedienteForNotify || !broadcastMessage.trim()) return;
    setSendingBroadcast(true);
    try {
      if (onNotifyNeighbors) {
        const res = await onNotifyNeighbors(selectedExpedienteForNotify.id, broadcastMessage);
        setBroadcastSuccess(`Notificación enviada a ${res.enviados_ok || 0} vecinos vinculados.`);
        setTimeout(() => {
          setSelectedExpedienteForNotify(null);
          setBroadcastSuccess(null);
        }, 2200);
      }
    } catch (err) {
      console.error('[EXPEDIENTES] Error al notificar vecinos:', err);
    } finally {
      setSendingBroadcast(false);
    }
  };

  return (
    <Card className="min-w-0">
      <CardHeader>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-sm sm:text-base font-bold tracking-tight text-brand-ink">
              Expedientes &amp; Incidentes Edilicios
            </h2>
            <p className="text-xs text-text-secondary mt-0.5">
              Casos consolidados por edificio para evitar duplicar informes técnicos y reclamos repetitivos.
            </p>
          </div>
          <div className="flex items-center gap-2 self-start sm:self-auto">
            {onRefresh && (
              <Button
                variant="secondary"
                size="sm"
                onClick={onRefresh}
                disabled={loading}
                className="h-8 px-3 text-xs text-text-secondary hover:text-brand-ink"
                title="Actualizar expedientes desde el servidor"
              >
                <RotateCcw size={13} className={loading ? 'animate-spin' : ''} />
                <span>Actualizar</span>
              </Button>
            )}
            <span className="text-xs text-text-muted font-medium bg-surface-muted px-2.5 py-1 rounded-full border border-border/60">
              {expedientes.length} casos
            </span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {expedientes.length === 0 ? (
          <div className="p-10 text-center text-xs text-text-muted">
            No hay expedientes activos registrados en el sistema. Los reclamos edilicios entrantes se agruparán automáticamente aquí.
          </div>
        ) : (
          <ScrollableTableContainer>
            <table className="w-full text-left text-xs sm:text-sm" style={{ minWidth: '1280px' }}>
              <thead className="bg-surface-muted text-[11px] uppercase tracking-[0.08em] text-text-muted border-b border-border/70">
                <tr>
                  <th scope="col" className="px-3.5 py-2.5 font-semibold whitespace-nowrap" style={{ minWidth: '130px' }}>Código</th>
                  <th scope="col" className="px-3.5 py-2.5 font-semibold" style={{ minWidth: '220px' }}>Consorcio</th>
                  <th scope="col" className="px-3.5 py-2.5 font-semibold whitespace-nowrap" style={{ minWidth: '140px' }}>Categoría</th>
                  <th scope="col" className="px-3.5 py-2.5 font-semibold" style={{ minWidth: '320px' }}>Título &amp; Notas Consolidadas</th>
                  <th scope="col" className="px-3.5 py-2.5 font-semibold text-center whitespace-nowrap" style={{ minWidth: '110px' }}>Reclamos</th>
                  <th scope="col" className="px-3.5 py-2.5 font-semibold text-center whitespace-nowrap" style={{ minWidth: '100px' }}>Prioridad</th>
                  <th scope="col" className="px-3.5 py-2.5 font-semibold text-center whitespace-nowrap" style={{ minWidth: '180px' }}>Estado</th>
                  <th scope="col" className="px-3.5 py-2.5 font-semibold text-center whitespace-nowrap" style={{ minWidth: '130px' }}>Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/70">
                {expedientes.map((exp) => (
                  <tr key={exp.id} className="hover:bg-surface-muted/60 transition-colors">
                    <td className="px-3.5 py-2.5 text-xs font-bold text-brand-ink whitespace-nowrap">
                      {exp.codigo}
                    </td>
                    <td className="px-3.5 py-2.5">
                      <div className="font-semibold text-brand-ink">
                        {exp.consorcio}
                      </div>
                      <div className="text-[11px] text-text-muted">
                        Proveedor: {exp.proveedor || 'Sin asignar'}
                      </div>
                    </td>
                    <td className="px-3.5 py-2.5 whitespace-nowrap">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-brand-sand/70 text-brand-navy border border-brand-sand">
                        {CATEGORIA_LABELS[exp.categoria] || exp.categoria}
                      </span>
                    </td>
                    <td className="px-3.5 py-2.5 text-text-secondary leading-relaxed">
                      <div className="font-medium text-brand-ink text-xs mb-1">
                        {exp.titulo}
                      </div>
                      <div
                        className={`text-xs text-text-secondary whitespace-pre-line leading-relaxed ${
                          expandedRows.has(exp.id) ? '' : 'line-clamp-2'
                        }`}
                      >
                        {exp.descripcion}
                      </div>
                      {exp.descripcion && exp.descripcion.length > 80 && (
                        <button
                          type="button"
                          onClick={() => toggleRow(exp.id)}
                          className="mt-1 text-[11px] font-semibold text-brand-ink/70 hover:text-brand-ink transition-colors cursor-pointer flex items-center gap-1"
                        >
                          {expandedRows.has(exp.id) ? (
                            <>
                              <span>Ver menos</span>
                              <ChevronUp size={12} />
                            </>
                          ) : (
                            <>
                              <span>Ver todos los reportes</span>
                              <ChevronDown size={12} />
                            </>
                          )}
                        </button>
                      )}
                    </td>
                    <td className="px-3.5 py-2.5 text-center">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-surface-muted border border-border text-brand-ink">
                        <Users size={11} />
                        <span>{exp.ticketsCount} reportes</span>
                      </span>
                    </td>
                    <td className="px-3.5 py-2.5 text-center">
                      <Badge variant={getPriorityBadgeVariant(exp.prioridad)}>
                        {exp.prioridad === 'CRITICA' ? 'Crítica' : exp.prioridad === 'ALTA' ? 'Alta' : 'Normal'}
                      </Badge>
                    </td>
                    <td className="px-3.5 py-2.5 text-center">
                      {onUpdateStatus ? (
                        <div className="flex items-center justify-center">
                          <SelectField
                            variant="badge"
                            size="xs"
                            value={exp.estado}
                            badgeVariantMap={ESTADO_BADGE_MAP}
                            onChange={(e) => onUpdateStatus(exp.id, e.target.value)}
                            options={ESTADOS_EXPEDIENTE}
                            aria-label="Cambiar estado del expediente"
                          />
                        </div>
                      ) : (
                        <Badge variant={ESTADO_BADGE_MAP[exp.estado] || 'neutral'}>
                          {exp.estado}
                        </Badge>
                      )}
                    </td>
                    <td className="px-3.5 py-2.5 text-center">
                      <Button
                        variant="secondary"
                        size="xs"
                        onClick={() => handleOpenNotifyModal(exp)}
                        className="h-7 px-2.5 text-[11px] text-text-secondary hover:text-brand-ink whitespace-nowrap"
                        title="Enviar mensaje masivo por WhatsApp a todos los vecinos que reportaron"
                      >
                        <Send size={11} />
                        <span>Avisar Vecinos</span>
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </ScrollableTableContainer>
        )}
      </CardContent>

      {/* Modal de Notificación a Vecinos */}
      {selectedExpedienteForNotify && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-surface rounded-xl shadow-xl border border-border max-w-lg w-full p-5 flex flex-col gap-4 animate-in fade-in duration-150">
            <div>
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-brand-ink flex items-center gap-2">
                  <Send size={14} className="text-brand-burgundy" />
                  <span>Notificar a Vecinos Involucrados</span>
                </h3>
                <span className="text-xs font-mono font-semibold bg-surface-muted px-2 py-0.5 rounded border border-border">
                  #{selectedExpedienteForNotify.codigo}
                </span>
              </div>
              <p className="text-xs text-text-secondary mt-1">
                Se enviará este mensaje por WhatsApp a los {selectedExpedienteForNotify.ticketsCount} vecinos que reportaron en este expediente de {selectedExpedienteForNotify.consorcio}.
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-text-secondary mb-1.5">
                Mensaje a despachar:
              </label>
              <textarea
                value={broadcastMessage}
                onChange={(e) => setBroadcastMessage(e.target.value)}
                rows={4}
                className="w-full text-xs p-2.5 rounded-lg border border-border bg-surface-muted/30 focus:outline-none focus:ring-1 focus:ring-brand-burgundy text-brand-ink leading-relaxed"
              />
            </div>

            {broadcastSuccess && (
              <div className="p-2.5 bg-emerald-50 text-emerald-800 text-xs rounded-lg border border-emerald-200 flex items-center gap-1.5">
                <CheckCircle size={14} />
                <span>{broadcastSuccess}</span>
              </div>
            )}

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-border/60">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedExpedienteForNotify(null)}
                disabled={sendingBroadcast}
                className="h-8 text-xs text-text-secondary"
              >
                Cancelar
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleSendBroadcast}
                disabled={sendingBroadcast || !broadcastMessage.trim()}
                className="h-8 text-xs"
              >
                <Send size={12} className={sendingBroadcast ? 'animate-pulse' : ''} />
                <span>{sendingBroadcast ? 'Enviando...' : 'Despachar WhatsApp'}</span>
              </Button>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}
