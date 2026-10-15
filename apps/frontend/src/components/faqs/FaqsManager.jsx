import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  HelpCircle,
  Search,
  Plus,
  Trash2,
  Edit3,
  CheckCircle2,
  XCircle,
  RotateCcw,
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

export function FaqsManager({ consorcios = [] }) {
  const [faqs, setFaqs] = useState([]);
  const [loading, setLoading] = useState(false);
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
    } catch (err) {
      console.error('[FAQS] Error al cambiar estado:', err);
      setFaqs(original);
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
      } else {
        const created = await ApiService.createFaq(payload);
        setFaqs((prev) => [created, ...prev]);
      }
      handleCloseModal();
    } catch (err) {
      console.error('[FAQS] Error al guardar FAQ:', err);
      alert('Error al guardar la FAQ en el servidor.');
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
    } catch (err) {
      console.error('[FAQS] Error al eliminar FAQ:', err);
      alert('No se pudo eliminar la FAQ.');
    }
  };

  return (
    <div className="h-full flex flex-col space-y-3.5 sm:space-y-4">
      <Card className="flex-1 flex flex-col min-h-0 bg-white border border-border shadow-subtle overflow-hidden">
        {/* Cabecera Principal */}
        <CardHeader className="border-b border-border bg-white px-4 py-3 sm:px-6 sm:py-4 shrink-0">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm sm:text-base font-bold tracking-tight text-brand-ink">
                  Base de Conocimiento & FAQs Homologadas
                </h2>
                <Badge variant="neutral" className="text-[10px] uppercase font-bold tracking-wider">
                  Respuestas Automáticas
                </Badge>
              </div>
              <p className="text-xs text-text-secondary mt-0.5">
                Respuestas oficiales aprobadas por la Dra. Ivana Seliz que el chatbot utiliza para resolver consultas de vecinos.
              </p>
            </div>

            <div className="flex items-center gap-2 self-start sm:self-auto">
              <Button
                variant="secondary"
                size="sm"
                onClick={loadFaqs}
                disabled={loading}
                className="h-8 px-2.5 text-xs text-text-secondary hover:text-brand-ink"
                title="Recargar FAQs"
              >
                <RotateCcw size={13} className={loading ? 'animate-spin' : ''} />
                <span className="hidden sm:inline">Actualizar</span>
              </Button>

              <Button
                variant="primary"
                size="sm"
                onClick={handleOpenCreateModal}
                className="h-8 px-3 text-xs bg-brand-ink text-white font-semibold flex items-center gap-1.5"
              >
                <Plus size={14} />
                <span>Nueva FAQ</span>
              </Button>
            </div>
          </div>

          {/* Barra de Búsqueda y Filtros */}
          <div className="mt-3.5 pt-3 border-t border-border/70 flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3">
            {/* Buscador */}
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none" />
              <input
                type="text"
                placeholder="Buscar por pregunta, respuesta o consorcio…"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full h-8 sm:h-9 bg-surface-soft border border-border text-brand-ink text-xs rounded-base pl-9 pr-3 outline-none transition-colors focus:border-brand-ink focus:bg-white"
              />
            </div>

            {/* Selector de Consorcio */}
            <select
              value={filterConsorcio}
              onChange={(e) => setFilterConsorcio(e.target.value)}
              className="h-8 sm:h-9 bg-surface-soft border border-border text-brand-ink text-xs rounded-base px-2.5 outline-none transition-colors focus:border-brand-ink"
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
            <div className="flex items-center gap-1 bg-surface-soft p-0.5 rounded-base border border-border shrink-0">
              {[
                { id: 'all', label: 'Todas' },
                { id: 'active', label: 'Activas' },
                { id: 'inactive', label: 'Inactivas' },
              ].map((f) => (
                <button
                  key={f.id}
                  type="button"
                  onClick={() => setFilterStatus(f.id)}
                  className={`text-[11px] font-semibold px-2.5 py-1 rounded transition-colors cursor-pointer ${
                    filterStatus === f.id
                      ? 'bg-brand-ink text-white shadow-sm'
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
        <CardContent className="flex-1 p-0 overflow-hidden relative">
          {errorMsg && (
            <div className="p-3 bg-danger-soft text-danger text-xs flex items-center gap-2 border-b border-border">
              <AlertCircle size={14} />
              <span>{errorMsg}</span>
            </div>
          )}

          <ScrollableTableContainer className="h-full">
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
                          {faq.es_activa ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
                        </button>
                      </td>

                      {/* Pregunta */}
                      <td className="py-3 px-4 font-semibold text-brand-ink align-top">
                        <p className="leading-snug">{faq.pregunta}</p>
                      </td>

                      {/* Respuesta Oficial */}
                      <td className="py-3 px-4 text-text-secondary whitespace-pre-line leading-relaxed align-top">
                        <div className="bg-surface-soft p-2.5 rounded-base border border-border/70 text-brand-ink text-xs">
                          {faq.respuesta}
                        </div>
                      </td>

                      {/* Consorcio */}
                      <td className="py-3 px-4 align-top">
                        {faq.consorcio_nombre ? (
                          <div className="flex items-center gap-1.5 text-brand-ink font-medium">
                            <Building2 size={13} className="text-text-muted shrink-0" />
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
                            className="size-7 rounded-base flex items-center justify-center text-text-secondary hover:text-brand-ink hover:bg-surface-muted transition-colors cursor-pointer"
                          >
                            <Edit3 size={13} />
                          </button>

                          {deleteConfirmId === faq.id ? (
                            <div className="flex items-center gap-1">
                              <button
                                type="button"
                                onClick={() => handleDelete(faq.id)}
                                title="Confirmar eliminación"
                                className="size-7 rounded-base flex items-center justify-center bg-danger text-white hover:bg-rose-700 transition-colors cursor-pointer"
                              >
                                <Check size={13} />
                              </button>
                              <button
                                type="button"
                                onClick={() => setDeleteConfirmId(null)}
                                title="Cancelar"
                                className="size-7 rounded-base flex items-center justify-center border border-border text-text-secondary hover:text-brand-ink transition-colors cursor-pointer"
                              >
                                <X size={13} />
                              </button>
                            </div>
                          ) : (
                            <button
                              type="button"
                              onClick={() => setDeleteConfirmId(faq.id)}
                              title="Eliminar FAQ"
                              className="size-7 rounded-base flex items-center justify-center text-text-muted hover:text-danger hover:bg-danger-soft transition-colors cursor-pointer"
                            >
                              <Trash2 size={13} />
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
        </CardContent>
      </Card>

      {/* Modal de Crear / Editar FAQ */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-brand-ink/40 backdrop-blur-xs animate-in fade-in duration-150">
          <div className="bg-white rounded-base border border-border shadow-2xl w-full max-w-lg overflow-hidden flex flex-col max-h-[90dvh]">
            {/* Cabecera del Modal */}
            <div className="flex items-center justify-between border-b border-border px-5 py-3.5 bg-surface-soft">
              <div className="flex items-center gap-2">
                <HelpCircle size={16} className="text-brand-ink" />
                <h3 className="text-sm font-bold text-brand-ink">
                  {editingFaq ? 'Editar Pregunta Frecuente' : 'Nueva Pregunta Frecuente'}
                </h3>
              </div>
              <button
                type="button"
                onClick={handleCloseModal}
                className="size-7 rounded-base flex items-center justify-center text-text-muted hover:text-brand-ink hover:bg-surface-muted transition-colors cursor-pointer"
              >
                <X size={15} />
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
                  className="w-full h-9 bg-white border border-border text-brand-ink text-xs rounded-base px-3 outline-none transition-colors focus:border-brand-ink focus:ring-1 focus:ring-brand-ink"
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
                  className="w-full bg-white border border-border text-brand-ink text-xs rounded-base p-3 outline-none transition-colors focus:border-brand-ink focus:ring-1 focus:ring-brand-ink leading-relaxed"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                <div>
                  <label className="block text-xs font-bold text-brand-ink mb-1">
                    Consorcio Vinculado
                  </label>
                  <select
                    value={formData.consorcio_id}
                    onChange={(e) => setFormData({ ...formData, consorcio_id: e.target.value })}
                    className="w-full h-9 bg-white border border-border text-brand-ink text-xs rounded-base px-2.5 outline-none transition-colors focus:border-brand-ink"
                  >
                    <option value="">General (Todos los consorcios)</option>
                    {consorcios.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.nombre}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex flex-col justify-end">
                  <label className="flex items-center gap-2 cursor-pointer select-none text-xs font-semibold text-brand-ink py-2">
                    <input
                      type="checkbox"
                      checked={formData.es_activa}
                      onChange={(e) => setFormData({ ...formData, es_activa: e.target.checked })}
                      className="size-4 rounded border-border text-brand-ink focus:ring-brand-ink cursor-pointer"
                    />
                    <span>FAQ Activa para el Bot</span>
                  </label>
                </div>
              </div>

              <div className="pt-3 border-t border-border flex items-center justify-end gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  type="button"
                  onClick={handleCloseModal}
                  disabled={submitting}
                  className="h-9 px-3 text-xs"
                >
                  Cancelar
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  type="submit"
                  disabled={submitting}
                  className="h-9 px-4 text-xs bg-brand-ink text-white font-semibold flex items-center gap-1.5"
                >
                  {submitting ? 'Guardando...' : editingFaq ? 'Guardar Cambios' : 'Crear FAQ'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
