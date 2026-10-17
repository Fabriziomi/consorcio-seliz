import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  HelpCircle,
  Search,
  Plus,
  Trash2,
  Pencil,
  CheckCircle2,
  XCircle,
  RotateCw,
  Building2,
  Sparkles,
  Check,
  X,
  AlertCircle,
} from 'lucide-react';
import { Card, CardHeader, CardContent } from '../ui/Card.jsx';
import { Badge } from '../ui/Badge.jsx';
import { Button } from '../ui/Button.jsx';
import { ScrollableTableContainer } from '../ui/ScrollableTableContainer.jsx';
import { ApiService } from '../../lib/api-client.js';
import { useToast } from '../ui/ToastNotification.jsx';

export function FaqsManager({ consorcios = [] }) {
  const toast = useToast();
  const [faqs, setFaqs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refreshConfirmed, setRefreshConfirmed] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterConsorcio, setFilterConsorcio] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');

  // Modal de Crear / Editar
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingFaq, setEditingFaq] = useState(null);
  const [formData, setFormData] = useState({
    pregunta: '',
    respuesta: '',
    consorcio_id: '',
    es_activa: true,
  });
  const [submitting, setSubmitting] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  const loadFaqs = useCallback(async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const data = await ApiService.getFaqs();
      if (Array.isArray(data)) {
        setFaqs(data);
      }
    } catch (err) {
      console.error('[FAQS] Error cargando base de conocimiento:', err);
      setErrorMsg('No se pudieron cargar las FAQs desde la API.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFaqs();
  }, [loadFaqs]);

  const handleRefresh = async () => {
    await loadFaqs();
    setRefreshConfirmed(true);
    toast.success('Base de conocimiento actualizada');
    setTimeout(() => setRefreshConfirmed(false), 1800);
  };

  // Filtrado reactivo en memoria
  const filteredFaqs = useMemo(() => {
    return faqs.filter((faq) => {
      const matchesSearch =
        faq.pregunta.toLowerCase().includes(searchTerm.toLowerCase()) ||
        faq.respuesta.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (faq.consorcio_nombre && faq.consorcio_nombre.toLowerCase().includes(searchTerm.toLowerCase()));

      const matchesConsorcio =
        filterConsorcio === 'all'
          ? true
          : filterConsorcio === 'general'
          ? !faq.consorcio_id
          : faq.consorcio_id === filterConsorcio;

      const matchesStatus =
        filterStatus === 'all'
          ? true
          : filterStatus === 'active'
          ? faq.es_activa
          : !faq.es_activa;

      return matchesSearch && matchesConsorcio && matchesStatus;
    });
  }, [faqs, searchTerm, filterConsorcio, filterStatus]);

  // Manejo de Modal
  const handleOpenCreateModal = () => {
    setEditingFaq(null);
    setFormData({
      pregunta: '',
      respuesta: '',
      consorcio_id: '',
      es_activa: true,
    });
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (faq) => {
    setEditingFaq(faq);
    setFormData({
      pregunta: faq.pregunta || '',
      respuesta: faq.respuesta || '',
      consorcio_id: faq.consorcio_id || '',
      es_activa: faq.es_activa !== false,
    });
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingFaq(null);
  };

  // Toggle activo directo desde la tabla
  const handleToggleActive = async (faq) => {
    const original = [...faqs];
    setFaqs((prev) =>
      prev.map((f) => (f.id === faq.id ? { ...f, es_activa: !f.es_activa } : f))
    );
    try {
      await ApiService.toggleFaq(faq.id);
      toast.info(faq.es_activa ? 'FAQ desactivada' : 'FAQ activada');
    } catch (err) {
      console.error('[FAQS] Error al cambiar estado:', err);
      setFaqs(original);
      toast.error('Error al actualizar estado');
    }
  };

  // Guardar (Crear o Editar)
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.pregunta.trim() || !formData.respuesta.trim()) {
      alert('La pregunta y la respuesta son obligatorias.');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        pregunta: formData.pregunta.trim(),
        respuesta: formData.respuesta.trim(),
        consorcio_id: formData.consorcio_id || null,
        es_activa: formData.es_activa,
      };

      if (editingFaq) {
        const updated = await ApiService.updateFaq(editingFaq.id, payload);
        setFaqs((prev) => prev.map((f) => (f.id === editingFaq.id ? updated : f)));
        toast.success('FAQ actualizada correctamente');
      } else {
        const created = await ApiService.createFaq(payload);
        setFaqs((prev) => [created, ...prev]);
        toast.success('Nueva FAQ registrada');
      }
      handleCloseModal();
    } catch (err) {
      console.error('[FAQS] Error al guardar FAQ:', err);
      toast.error('Error al guardar la FAQ en el servidor');
    } finally {
      setSubmitting(false);
    }
  };

  // Eliminar
  const handleDelete = async (id) => {
    try {
      await ApiService.deleteFaq(id);
      setFaqs((prev) => prev.filter((f) => f.id !== id));
      setDeleteConfirmId(null);
      toast.success('FAQ eliminada correctamente');
    } catch (err) {
      console.error('[FAQS] Error al eliminar FAQ:', err);
      toast.error('No se pudo eliminar la FAQ');
    }
  };

  return (
    <div className="w-full space-y-3.5 sm:space-y-4">
      <Card className="flex flex-col bg-white border border-border shadow-subtle overflow-hidden max-h-[calc(100dvh-6.5rem)]">
        {/* Cabecera Principal */}
        <CardHeader className="border-b border-border bg-white px-4 py-3 sm:px-6 sm:py-4 shrink-0">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-2">
              <h2 className="text-lg sm:text-xl font-bold tracking-tight text-brand-ink">
                Base de Conocimiento &amp; FAQs Homologadas
              </h2>
              <Badge variant="neutral" className="text-[10px] uppercase font-bold tracking-wider">
                Automático
              </Badge>
            </div>

            <div className="flex items-center gap-2 self-start sm:self-auto">
              <Button
                variant="secondary"
                size="icon-sm"
                onClick={handleRefresh}
                loading={loading}
                confirmed={refreshConfirmed}
                title="Actualizar FAQs desde el servidor"
                aria-label="Actualizar FAQs"
              >
                <RotateCw size={18} strokeWidth={2} />
              </Button>

              <Button
                variant="primary"
                size="icon-sm"
                onClick={handleOpenCreateModal}
                className="bg-brand-ink text-white"
                title="Nueva FAQ"
                aria-label="Nueva FAQ"
              >
                <Plus size={18} strokeWidth={2} />
              </Button>
            </div>
          </div>

          {/* Barra de Búsqueda y Filtros */}
          <div className="mt-3.5 pt-3 border-t border-border/70 flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3">
            {/* Buscador */}
            <div className="relative flex-1">
              <Search size={18} strokeWidth={1.8} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none" />
              <input
                type="text"
                placeholder="Buscar por pregunta, respuesta o consorcio…"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full h-10 sm:h-11 bg-surface-soft border border-border/80 text-brand-ink text-sm rounded-xl pl-10 pr-4 outline-none transition-colors focus:border-brand-ink focus:bg-white shadow-2xs"
              />
            </div>

            {/* Selector de Consorcio */}
            <select
              value={filterConsorcio}
              onChange={(e) => setFilterConsorcio(e.target.value)}
              className="h-10 sm:h-11 bg-surface-soft border border-border/80 text-brand-ink text-xs sm:text-sm font-medium rounded-xl px-3 outline-none transition-colors focus:border-brand-ink shadow-2xs"
            >
              <option value="all">Todos los consorcios</option>
              <option value="general">Generales (Sin consorcio asignado)</option>
              {consorcios.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nombre}
                </option>
              ))}
            </select>

            {/* Filtro de Estado */}
            <div className="flex items-center gap-1 bg-surface-soft p-0.5 rounded-lg border border-border shrink-0">
              {[
                { id: 'all', label: 'Todas' },
                { id: 'active', label: 'Activas' },
                { id: 'inactive', label: 'Inactivas' },
              ].map((f) => (
                <button
                  key={f.id}
                  type="button"
                  onClick={() => setFilterStatus(f.id)}
                  className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
                    filterStatus === f.id
                      ? 'bg-brand-ink text-white shadow-sm font-bold'
                      : 'text-text-secondary hover:text-brand-ink'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>
        </CardHeader>

        {/* Tabla de Contenido */}
        <CardContent className="p-0 overflow-hidden relative">
          {errorMsg && (
            <div className="p-3 bg-danger-soft text-danger text-xs flex items-center gap-2 border-b border-border">
              <AlertCircle size={14} strokeWidth={2} />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Vista Móvil / Tablet Estrecha: Tarjetas Compactas */}
          <div className="md:hidden max-h-[calc(100dvh-15rem)] overflow-y-auto p-2.5 space-y-2.5">
            {filteredFaqs.length === 0 ? (
              <div className="py-12 text-center text-text-muted text-xs">
                {loading
                  ? 'Cargando preguntas frecuentes...'
                  : 'No se encontraron FAQs con los criterios de búsqueda seleccionados.'}
              </div>
            ) : (
              filteredFaqs.map((faq) => (
                <div
                  key={faq.id}
                  className={`p-3.5 bg-white border border-border/80 rounded-xl space-y-2.5 shadow-2xs hover:border-brand-ink/40 transition-colors ${
                    !faq.es_activa ? 'opacity-70 bg-surface-muted/30' : ''
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-start gap-2.5 min-w-0">
                      <button
                        type="button"
                        onClick={() => handleToggleActive(faq)}
                        title={faq.es_activa ? 'Desactivar FAQ' : 'Activar FAQ'}
                        className={`size-6 rounded-full inline-flex items-center justify-center transition-colors cursor-pointer shrink-0 mt-0.5 ${
                          faq.es_activa
                            ? 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'
                            : 'bg-zinc-200 text-zinc-500 hover:bg-zinc-300'
                        }`}
                      >
                        {faq.es_activa ? <CheckCircle2 size={16} strokeWidth={2} className="text-emerald-600" /> : <XCircle size={16} strokeWidth={2} className="text-zinc-400" />}
                      </button>
                      <p className="text-sm font-bold text-brand-ink leading-snug">{faq.pregunta}</p>
                    </div>

                    <div className="shrink-0">
                      {faq.consorcio_nombre ? (
                        <span className="text-[10px] font-semibold text-text-secondary bg-surface-muted px-2 py-0.5 rounded border border-border/60">
                          {faq.consorcio_nombre}
                        </span>
                      ) : (
                        <Badge variant="neutral" className="text-[10px]">
                          General
                        </Badge>
                      )}
                    </div>
                  </div>

                  <div className="bg-surface-soft p-3 rounded-lg border border-border/70 text-brand-ink text-xs whitespace-pre-line leading-relaxed">
                    {faq.respuesta}
                  </div>

                  <div className="flex items-center justify-between text-xs pt-1 border-t border-border/60">
                    <span className={`text-[11px] font-semibold ${faq.es_activa ? 'text-emerald-700' : 'text-zinc-500'}`}>
                      {faq.es_activa ? 'Activa en bot' : 'Inactiva (Pausada)'}
                    </span>

                    <div className="flex items-center gap-1.5 shrink-0">
                      <button
                        type="button"
                        onClick={() => handleOpenEditModal(faq)}
                        title="Editar FAQ"
                        aria-label="Editar FAQ"
                        className="size-9 rounded-xl border border-border/80 bg-white flex items-center justify-center text-text-secondary hover:text-brand-ink hover:bg-surface-muted transition-colors cursor-pointer shadow-2xs"
                      >
                        <Pencil size={17} strokeWidth={1.8} />
                      </button>

                      {deleteConfirmId === faq.id ? (
                        <div className="flex items-center gap-1">
                          <button
                            type="button"
                            onClick={() => handleDelete(faq.id)}
                            title="Confirmar eliminación"
                            aria-label="Confirmar eliminación"
                            className="size-9 rounded-xl flex items-center justify-center bg-danger text-white hover:bg-rose-700 transition-colors cursor-pointer shadow-2xs"
                          >
                            <Check size={17} strokeWidth={2.2} />
                          </button>
                          <button
                            type="button"
                            onClick={() => setDeleteConfirmId(null)}
                            title="Cancelar"
                            aria-label="Cancelar"
                            className="size-9 rounded-xl flex items-center justify-center border border-border/80 bg-white text-text-secondary hover:text-brand-ink transition-colors cursor-pointer shadow-2xs"
                          >
                            <X size={17} strokeWidth={2} />
                          </button>
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={() => setDeleteConfirmId(faq.id)}
                          title="Eliminar FAQ"
                          aria-label="Eliminar FAQ"
                          className="size-9 rounded-xl border border-border/80 bg-white flex items-center justify-center text-text-muted hover:text-danger hover:border-danger/30 hover:bg-danger-soft transition-colors cursor-pointer shadow-2xs"
                        >
                          <Trash2 size={17} strokeWidth={1.8} />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Vista Escritorio / Tablet Apaisada: Tabla Completa */}
          <div className="hidden md:block max-h-[calc(100dvh-15rem)] overflow-y-auto">
            <ScrollableTableContainer>
              <table className="w-full text-left border-collapse">
                <thead className="sticky top-0 z-10 bg-surface-soft border-b border-border text-[11px] font-bold uppercase tracking-wider text-text-muted">
                  <tr>
                    <th className="py-2.5 px-4 w-12 text-center">Estado</th>
                    <th className="py-2.5 px-4 min-w-[220px]">Pregunta Frecuente</th>
                    <th className="py-2.5 px-4 min-w-[300px]">Respuesta Oficial Homologada</th>
                    <th className="py-2.5 px-4 w-48">Consorcio</th>
                    <th className="py-2.5 px-4 w-24 text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border text-xs">
                  {filteredFaqs.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-12 text-center text-text-muted text-xs">
                        {loading
                          ? 'Cargando preguntas frecuentes...'
                          : 'No se encontraron FAQs con los criterios de búsqueda seleccionados.'}
                      </td>
                    </tr>
                  ) : (
                    filteredFaqs.map((faq) => (
                      <tr
                        key={faq.id}
                        className={`hover:bg-surface-soft/60 transition-colors ${
                          !faq.es_activa ? 'opacity-60 bg-surface-muted/20' : ''
                        }`}
                      >
                        {/* Switch Activo / Inactivo */}
                        <td className="py-3 px-4 text-center">
                          <button
                            type="button"
                            onClick={() => handleToggleActive(faq)}
                            title={faq.es_activa ? 'Desactivar FAQ' : 'Activar FAQ'}
                            className={`size-6 rounded-full inline-flex items-center justify-center transition-colors cursor-pointer ${
                              faq.es_activa
                                ? 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'
                                : 'bg-zinc-200 text-zinc-500 hover:bg-zinc-300'
                            }`}
                          >
                            {faq.es_activa ? <CheckCircle2 size={16} strokeWidth={2} className="text-emerald-600" /> : <XCircle size={16} strokeWidth={2} className="text-zinc-400" />}
                          </button>
                        </td>

                        {/* Pregunta */}
                        <td className="py-3 px-4 font-semibold text-brand-ink align-top">
                          <p className="leading-snug">{faq.pregunta}</p>
                        </td>

                        {/* Respuesta Oficial */}
                        <td className="py-3 px-4 text-text-secondary whitespace-pre-line leading-relaxed align-top">
                          <div className="bg-surface-soft p-2.5 rounded-lg border border-border/70 text-brand-ink text-xs">
                            {faq.respuesta}
                          </div>
                        </td>

                        {/* Consorcio */}
                        <td className="py-3 px-4 align-top">
                          {faq.consorcio_nombre ? (
                            <div className="flex items-center gap-1.5 text-brand-ink font-medium">
                              <Building2 size={14} strokeWidth={1.8} className="text-text-muted shrink-0" />
                              <span className="truncate">{faq.consorcio_nombre}</span>
                            </div>
                          ) : (
                            <Badge variant="neutral" className="text-[10px]">
                              General (Todos)
                            </Badge>
                          )}
                        </td>

                        {/* Acciones */}
                        <td className="py-3 px-4 text-right align-top">
                          <div className="flex items-center justify-end gap-1">
                            <button
                              type="button"
                              onClick={() => handleOpenEditModal(faq)}
                              title="Editar FAQ"
                              aria-label="Editar FAQ"
                              className="size-9 rounded-xl border border-border/80 bg-white flex items-center justify-center text-text-secondary hover:text-brand-ink hover:bg-surface-muted transition-colors cursor-pointer shadow-2xs"
                            >
                              <Pencil size={18} strokeWidth={1.8} />
                            </button>

                            {deleteConfirmId === faq.id ? (
                              <div className="flex items-center gap-1">
                                <button
                                  type="button"
                                  onClick={() => handleDelete(faq.id)}
                                  title="Confirmar eliminación"
                                  aria-label="Confirmar eliminación"
                                  className="size-9 rounded-xl flex items-center justify-center bg-danger text-white hover:bg-rose-700 transition-colors cursor-pointer shadow-2xs"
                                >
                                  <Check size={18} strokeWidth={2.2} />
                                </button>
                                <button
                                  type="button"
                                  onClick={() => setDeleteConfirmId(null)}
                                  title="Cancelar"
                                  aria-label="Cancelar"
                                  className="size-9 rounded-xl flex items-center justify-center border border-border/80 bg-white text-text-secondary hover:text-brand-ink transition-colors cursor-pointer shadow-2xs"
                                >
                                  <X size={18} strokeWidth={2} />
                                </button>
                              </div>
                            ) : (
                              <button
                                type="button"
                                onClick={() => setDeleteConfirmId(faq.id)}
                                title="Eliminar FAQ"
                                aria-label="Eliminar FAQ"
                                className="size-9 rounded-xl border border-border/80 bg-white flex items-center justify-center text-text-muted hover:text-danger hover:border-danger/30 hover:bg-danger-soft transition-colors cursor-pointer shadow-2xs"
                              >
                                <Trash2 size={18} strokeWidth={1.8} />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </ScrollableTableContainer>
          </div>
        </CardContent>
      </Card>

      {/* Modal de Crear / Editar FAQ */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-brand-ink/40 backdrop-blur-xs animate-in fade-in duration-150">
          <div className="bg-white rounded-xl border border-border shadow-2xl w-full max-w-lg overflow-hidden flex flex-col max-h-[90dvh]">
            {/* Cabecera del Modal */}
            <div className="flex items-center justify-between border-b border-border px-5 py-3.5 bg-surface-soft">
              <div className="flex items-center gap-2">
                <HelpCircle size={18} strokeWidth={1.8} className="text-brand-ink" />
                <h3 className="text-sm font-bold text-brand-ink">
                  {editingFaq ? 'Editar Pregunta Frecuente' : 'Nueva Pregunta Frecuente'}
                </h3>
              </div>
              <button
                type="button"
                onClick={handleCloseModal}
                title="Cerrar modal"
                aria-label="Cerrar modal"
                className="size-9 sm:size-10 rounded-xl border border-border/80 bg-white flex items-center justify-center text-text-muted hover:text-brand-ink hover:bg-surface-muted transition-colors cursor-pointer shadow-2xs"
              >
                <X size={18} strokeWidth={2} />
              </button>
            </div>

            {/* Formulario */}
            <form onSubmit={handleSubmit} className="p-5 space-y-4 overflow-y-auto">
              <div>
                <label className="block text-xs font-bold text-brand-ink mb-1">
                  Pregunta o Consulta Frecuente *
                </label>
                <input
                  type="text"
                  required
                  placeholder="Ej: ¿Cuáles son las pautas de mudanza para el edificio?"
                  value={formData.pregunta}
                  onChange={(e) => setFormData({ ...formData, pregunta: e.target.value })}
                  className="w-full h-10 sm:h-11 bg-white border border-border text-brand-ink text-sm sm:text-xs rounded-xl px-3 outline-none transition-colors focus:border-brand-ink shadow-2xs"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-brand-ink mb-1">
                  Respuesta Oficial Homologada (Dra. Ivana Seliz) *
                </label>
                <textarea
                  required
                  rows={5}
                  placeholder="Escribí aquí la respuesta oficial aprobada. El asistente virtual utilizará este texto para responder de forma directa y fehaciente a los vecinos."
                  value={formData.respuesta}
                  onChange={(e) => setFormData({ ...formData, respuesta: e.target.value })}
                  className="w-full bg-white border border-border text-brand-ink text-sm sm:text-xs rounded-xl p-3 outline-none transition-colors focus:border-brand-ink leading-relaxed shadow-2xs"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-brand-ink mb-1">
                  Ámbito de Aplicación
                </label>
                <select
                  value={formData.consorcio_id}
                  onChange={(e) => setFormData({ ...formData, consorcio_id: e.target.value })}
                  className="w-full h-10 sm:h-11 bg-white border border-border text-brand-ink text-sm sm:text-xs rounded-xl px-3 outline-none transition-colors focus:border-brand-ink shadow-2xs"
                >
                  <option value="">Consorcio General (Aplica a todos los edificios)</option>
                  {consorcios.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nombre}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="es_activa"
                  checked={formData.es_activa}
                  onChange={(e) => setFormData({ ...formData, es_activa: e.target.checked })}
                  className="size-4 rounded border-border text-brand-ink focus:ring-brand-ink"
                />
                <label htmlFor="es_activa" className="text-xs font-medium text-brand-ink cursor-pointer select-none">
                  FAQ activa para respuestas automáticas
                </label>
              </div>

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-border">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCloseModal}
                  disabled={submitting}
                  className="h-8 text-xs text-text-secondary"
                >
                  Cancelar
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  type="submit"
                  loading={submitting}
                  className="h-8 text-xs bg-brand-ink text-white"
                >
                  <span>{editingFaq ? 'Guardar Cambios' : 'Crear FAQ'}</span>
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
