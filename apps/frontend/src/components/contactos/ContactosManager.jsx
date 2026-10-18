import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Users,
  Search,
  Plus,
  Trash2,
  Pencil,
  MessageSquare,
  Building2,
  RotateCw,
  Check,
  X,
  Phone,
  Home,
  UserCheck,
  AlertCircle,
} from 'lucide-react';
import { Card, CardHeader, CardContent } from '../ui/Card.jsx';
import { Badge } from '../ui/Badge.jsx';
import { Button } from '../ui/Button.jsx';
import { Modal } from '../ui/Modal.jsx';
import { ScrollableTableContainer } from '../ui/ScrollableTableContainer.jsx';
import { ApiService } from '../../lib/api-client.js';
import { useToast } from '../ui/ToastNotification.jsx';

const ROLES = [
  { id: 'PROPIETARIO', label: 'Propietario' },
  { id: 'INQUILINO', label: 'Inquilino' },
  { id: 'ENCARGADO', label: 'Portería / Encargado' },
  { id: 'PROVEEDOR', label: 'Proveedor' },
  { id: 'OTRO', label: 'Otro' },
];

export function ContactosManager({ consorcios = [], onOpenChat }) {
  const toast = useToast();
  const [contactos, setContactos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refreshConfirmed, setRefreshConfirmed] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterConsorcio, setFilterConsorcio] = useState('all');
  const [filterRol, setFilterRol] = useState('all');

  // Modal Crear / Editar
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingContacto, setEditingContacto] = useState(null);
  const [formData, setFormData] = useState({
    nombre_completo: '',
    telefono_wa: '',
    consorcio_id: '',
    unidad_funcional: '',
    rol: 'PROPIETARIO',
    notas: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  const loadContactos = useCallback(async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const data = await ApiService.getContactos();
      if (Array.isArray(data)) {
        setContactos(data);
      }
    } catch (err) {
      console.error('[CONTACTOS] Error cargando directorio:', err);
      setErrorMsg('No se pudo cargar la lista de contactos.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadContactos();
  }, [loadContactos]);

  const handleRefresh = async () => {
    await loadContactos();
    setRefreshConfirmed(true);
    toast.success('Directorio de contactos actualizado');
    setTimeout(() => setRefreshConfirmed(false), 1800);
  };

  const filteredContactos = useMemo(() => {
    return contactos.filter((c) => {
      const q = searchTerm.toLowerCase();
      const matchesSearch =
        (c.nombre_completo && c.nombre_completo.toLowerCase().includes(q)) ||
        (c.telefono_wa && c.telefono_wa.includes(q)) ||
        (c.unidad_funcional && c.unidad_funcional.toLowerCase().includes(q)) ||
        (c.consorcio_nombre && c.consorcio_nombre.toLowerCase().includes(q));

      const matchesConsorcio =
        filterConsorcio === 'all'
          ? true
          : filterConsorcio === 'sin_consorcio'
          ? !c.consorcio_id
          : c.consorcio_id === filterConsorcio;

      const matchesRol = filterRol === 'all' ? true : c.rol === filterRol;

      return matchesSearch && matchesConsorcio && matchesRol;
    });
  }, [contactos, searchTerm, filterConsorcio, filterRol]);

  const handleOpenCreateModal = () => {
    setEditingContacto(null);
    setFormData({
      nombre_completo: '',
      telefono_wa: '',
      consorcio_id: '',
      unidad_funcional: '',
      rol: 'PROPIETARIO',
      notas: '',
    });
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (c) => {
    setEditingContacto(c);
    setFormData({
      nombre_completo: c.nombre_completo || '',
      telefono_wa: c.telefono_wa || '',
      consorcio_id: c.consorcio_id || '',
      unidad_funcional: c.unidad_funcional || '',
      rol: c.rol || 'PROPIETARIO',
      notas: c.notas || '',
    });
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingContacto(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.nombre_completo.trim() || !formData.telefono_wa.trim()) {
      alert('Nombre y teléfono son obligatorios.');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        nombre_completo: formData.nombre_completo.trim(),
        telefono_wa: formData.telefono_wa.trim(),
        consorcio_id: formData.consorcio_id || null,
        unidad_funcional: formData.unidad_funcional.trim() || null,
        rol: formData.rol,
        notas: formData.notas.trim() || null,
      };

      if (editingContacto) {
        const updated = await ApiService.updateContacto(editingContacto.id, payload);
        setContactos((prev) => prev.map((c) => (c.id === editingContacto.id ? updated : c)));
        toast.success('Contacto actualizado correctamente');
      } else {
        const created = await ApiService.createContacto(payload);
        setContactos((prev) => [created, ...prev]);
        toast.success('Contacto registrado exitosamente');
      }
      handleCloseModal();
    } catch (err) {
      console.error('[CONTACTOS] Error guardando contacto:', err);
      toast.error('Error al guardar el contacto.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await ApiService.deleteContacto(id);
      setContactos((prev) => prev.filter((c) => c.id !== id));
      setDeleteConfirmId(null);
      toast.success('Contacto eliminado');
    } catch (err) {
      console.error('[CONTACTOS] Error al eliminar:', err);
      toast.error('No se pudo eliminar el contacto.');
    }
  };

  const getRolBadge = (rol) => {
    switch (rol) {
      case 'PROPIETARIO':
        return <Badge variant="neutral" className="text-[10px]">Propietario</Badge>;
      case 'INQUILINO':
        return <Badge variant="info" className="text-[10px]">Inquilino</Badge>;
      case 'ENCARGADO':
        return <Badge variant="warning" className="text-[10px]">Encargado</Badge>;
      case 'PROVEEDOR':
        return <Badge variant="success" className="text-[10px]">Proveedor</Badge>;
      default:
        return <Badge variant="neutral" className="text-[10px]">{rol || 'General'}</Badge>;
    }
  };

  return (
    <div className="w-full h-full flex flex-col min-h-0">
      <Card className="h-full flex flex-col min-h-0 bg-white border border-border shadow-subtle overflow-hidden">
        {/* Cabecera Principal - Fija en la parte superior */}
        <CardHeader className="border-b border-border bg-white px-4 py-3 sm:px-6 sm:py-4 shrink-0 z-10">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-2">
              <h2 className="text-lg sm:text-xl font-bold tracking-tight text-brand-ink">
                Directorio de Vecinos &amp; Contactos
              </h2>
              <Badge variant="neutral" className="text-[10px]">
                {contactos.length} contactos
              </Badge>
            </div>

            <div className="flex items-center gap-2 self-start sm:self-auto">
              <Button
                variant="secondary"
                size="icon-sm"
                onClick={handleRefresh}
                loading={loading}
                confirmed={refreshConfirmed}
                title="Actualizar directorio"
                aria-label="Actualizar directorio"
              >
                <RotateCw size={18} strokeWidth={2} />
              </Button>

              <Button
                variant="primary"
                size="icon-sm"
                onClick={handleOpenCreateModal}
                className="bg-brand-ink text-white"
                title="Nuevo Contacto"
                aria-label="Nuevo Contacto"
              >
                <Plus size={18} strokeWidth={2} />
              </Button>
            </div>
          </div>

          {/* Filtros */}
          <div className="mt-3.5 pt-3 border-t border-border/70 flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3">
            <div className="relative flex-1">
              <Search size={18} strokeWidth={1.8} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none" />
              <input
                type="text"
                placeholder="Buscar por nombre, teléfono o unidad funcional…"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full h-10 sm:h-11 bg-surface-soft border border-border/80 text-brand-ink text-sm rounded-xl pl-10 pr-4 outline-none transition-all duration-500 focus:border-brand-ink focus:bg-white shadow-2xs"
              />
            </div>

            <select
              value={filterConsorcio}
              onChange={(e) => setFilterConsorcio(e.target.value)}
              className="h-10 sm:h-11 bg-surface-soft border border-border/80 text-brand-ink text-xs sm:text-sm font-medium rounded-xl px-3 outline-none transition-all duration-500 focus:border-brand-ink shadow-2xs"
            >
              <option value="all">Todos los consorcios</option>
              <option value="sin_consorcio">Sin consorcio asignado</option>
              {consorcios.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nombre}
                </option>
              ))}
            </select>

            <select
              value={filterRol}
              onChange={(e) => setFilterRol(e.target.value)}
              className="h-10 sm:h-11 bg-surface-soft border border-border/80 text-brand-ink text-xs sm:text-sm font-medium rounded-xl px-3 outline-none transition-all duration-500 focus:border-brand-ink shadow-2xs"
            >
              <option value="all">Todos los roles</option>
              {ROLES.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>
        </CardHeader>

        {/* Tabla de Contactos - Área scrollable única */}
        <CardContent className="p-0 flex-1 min-h-0 overflow-hidden relative flex flex-col">
          {errorMsg && (
            <div className="p-3 bg-danger-soft text-danger text-xs flex items-center gap-2 border-b border-border shrink-0">
              <AlertCircle size={14} strokeWidth={2} />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Vista Móvil / Tablet Estrecha: Tarjetas Compactas */}
          <div className="md:hidden flex-1 min-h-0 overflow-y-auto p-2.5 space-y-2.5">
            {filteredContactos.length === 0 ? (
              <div className="py-12 text-center text-text-muted text-xs">
                {loading
                  ? 'Cargando directorio de contactos...'
                  : 'No se encontraron contactos con los criterios seleccionados.'}
              </div>
            ) : (
              filteredContactos.map((c) => (
                <div
                  key={c.id}
                  className="p-3.5 bg-white border border-border/80 rounded-xl space-y-2.5 shadow-2xs hover:border-brand-ink/40 transition-all duration-500 ease-out hover:shadow-subtle group"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="size-9 rounded-full bg-surface-muted text-brand-ink font-bold text-xs flex items-center justify-center shrink-0 border border-border shadow-2xs transition-transform duration-500 group-hover:scale-108">
                        {c.nombre_completo ? c.nombre_completo.charAt(0).toUpperCase() : 'V'}
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-bold text-brand-ink truncate">{c.nombre_completo}</p>
                        <div className="flex items-center gap-1.5 text-text-secondary mt-0.5">
                          <Phone size={13} strokeWidth={1.8} className="text-text-muted shrink-0" />
                          <span className="text-xs">{c.telefono_wa}</span>
                        </div>
                      </div>
                    </div>
                    <div className="shrink-0">{getRolBadge(c.rol)}</div>
                  </div>

                  <div className="flex items-center justify-between text-xs text-text-secondary pt-2 border-t border-border/60">
                    <div className="min-w-0 flex items-center gap-1.5 text-text-secondary truncate">
                      <Building2 size={13} strokeWidth={1.8} className="text-text-muted shrink-0" />
                      <span className="truncate font-medium">{c.consorcio_nombre || 'Sin consorcio'}</span>
                      {c.unidad_funcional && (
                        <>
                          <span>•</span>
                          <span className="font-semibold text-brand-ink shrink-0">U.F. {c.unidad_funcional}</span>
                        </>
                      )}
                    </div>

                    <div className="flex items-center gap-1.5 shrink-0 ml-2">
                      {onOpenChat && (
                        <button
                          type="button"
                          onClick={() => onOpenChat(c)}
                          title="Abrir conversación WhatsApp"
                          aria-label="Abrir conversación WhatsApp"
                          className="size-9 rounded-xl border border-border/80 bg-white flex items-center justify-center text-text-secondary hover:text-brand-ink hover:bg-surface-muted transition-all duration-500 ease-out hover:scale-110 active:scale-90 [&>svg]:transition-transform [&>svg]:duration-500 hover:[&>svg]:scale-115 cursor-pointer shadow-2xs"
                        >
                          <MessageSquare size={17} strokeWidth={1.8} />
                        </button>
                      )}

                      <button
                        type="button"
                        onClick={() => handleOpenEditModal(c)}
                        title="Editar contacto"
                        aria-label="Editar contacto"
                        className="size-9 rounded-xl border border-border/80 bg-white flex items-center justify-center text-text-secondary hover:text-brand-ink hover:bg-surface-muted transition-all duration-500 ease-out hover:scale-110 active:scale-90 [&>svg]:transition-transform [&>svg]:duration-500 hover:[&>svg]:scale-115 cursor-pointer shadow-2xs"
                      >
                        <Pencil size={17} strokeWidth={1.8} />
                      </button>

                      {deleteConfirmId === c.id ? (
                        <div className="flex items-center gap-1">
                          <button
                            type="button"
                            onClick={() => handleDelete(c.id)}
                            title="Confirmar eliminación"
                            aria-label="Confirmar eliminación"
                            className="size-9 rounded-xl flex items-center justify-center bg-danger text-white hover:bg-rose-700 transition-all duration-500 ease-out hover:scale-110 active:scale-90 [&>svg]:transition-transform [&>svg]:duration-500 hover:[&>svg]:scale-115 cursor-pointer shadow-2xs"
                          >
                            <Check size={17} strokeWidth={2.2} />
                          </button>
                          <button
                            type="button"
                            onClick={() => setDeleteConfirmId(null)}
                            title="Cancelar"
                            aria-label="Cancelar"
                            className="size-9 rounded-xl flex items-center justify-center border border-border/80 bg-white text-text-secondary hover:text-brand-ink transition-all duration-500 ease-out hover:scale-110 active:scale-90 [&>svg]:transition-transform [&>svg]:duration-500 hover:[&>svg]:scale-115 cursor-pointer shadow-2xs"
                          >
                            <X size={17} strokeWidth={2} />
                          </button>
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={() => setDeleteConfirmId(c.id)}
                          title="Eliminar contacto"
                          aria-label="Eliminar contacto"
                          className="size-9 rounded-xl border border-border/80 bg-white flex items-center justify-center text-text-muted hover:text-danger hover:border-danger/30 hover:bg-danger-soft transition-all duration-500 ease-out hover:scale-110 active:scale-90 [&>svg]:transition-transform [&>svg]:duration-500 hover:[&>svg]:scale-115 cursor-pointer shadow-2xs"
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
          <div className="hidden md:flex flex-col flex-1 min-h-0 overflow-hidden">
            <ScrollableTableContainer>
              <table className="w-full text-left border-collapse">
                <thead className="sticky top-0 z-10 bg-surface-soft border-b border-border text-[11px] font-bold uppercase tracking-wider text-text-muted shadow-2xs">
                  <tr>
                    <th className="py-2.5 px-4 min-w-[200px]">Vecino / Contacto</th>
                    <th className="py-2.5 px-4 w-40">Teléfono WA</th>
                    <th className="py-2.5 px-4 min-w-[180px]">Consorcio</th>
                    <th className="py-2.5 px-4 w-32">Unidad</th>
                    <th className="py-2.5 px-4 w-28">Rol</th>
                    <th className="py-2.5 px-4 w-32 text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border text-xs">
                  {filteredContactos.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-12 text-center text-text-muted text-xs">
                        {loading
                          ? 'Cargando directorio de contactos...'
                          : 'No se encontraron contactos con los criterios seleccionados.'}
                      </td>
                    </tr>
                  ) : (
                    filteredContactos.map((c) => (
                      <tr key={c.id} className="hover:bg-surface-soft/60 transition-colors duration-500 group">
                        {/* Nombre */}
                        <td className="py-3 px-4 font-bold text-brand-ink">
                          <div className="flex items-center gap-2">
                            <div className="size-7 rounded-full bg-surface-muted text-brand-ink font-bold text-[11px] flex items-center justify-center shrink-0 border border-border transition-transform duration-500 group-hover:scale-110">
                              {c.nombre_completo ? c.nombre_completo.charAt(0).toUpperCase() : 'V'}
                            </div>
                            <span className="truncate">{c.nombre_completo}</span>
                          </div>
                        </td>

                        {/* Teléfono sin font-mono */}
                        <td className="py-3 px-4 text-brand-ink font-normal">
                          <div className="flex items-center gap-1.5 text-text-secondary">
                            <Phone size={13} strokeWidth={1.8} className="text-text-muted shrink-0" />
                            <span className="text-xs">{c.telefono_wa}</span>
                          </div>
                        </td>

                        {/* Consorcio */}
                        <td className="py-3 px-4 text-text-secondary">
                          {c.consorcio_nombre ? (
                            <div className="flex items-center gap-1.5 text-brand-ink">
                              <Building2 size={14} strokeWidth={1.8} className="text-text-muted shrink-0" />
                              <span className="truncate">{c.consorcio_nombre}</span>
                            </div>
                          ) : (
                            <span className="text-text-muted text-[11px] italic">Sin consorcio</span>
                          )}
                        </td>

                        {/* Unidad */}
                        <td className="py-3 px-4 font-semibold text-brand-ink">
                          {c.unidad_funcional || '—'}
                        </td>

                        {/* Rol */}
                        <td className="py-3 px-4">{getRolBadge(c.rol)}</td>

                        {/* Acciones */}
                        <td className="py-3 px-4 text-right">
                          <div className="flex items-center justify-end gap-1">
                            {/* Botón Abrir Chat */}
                            {onOpenChat && (
                              <button
                                type="button"
                                onClick={() => onOpenChat(c)}
                                title="Abrir conversación WhatsApp"
                                aria-label="Abrir conversación WhatsApp"
                                className="size-9 rounded-xl border border-border/80 bg-white flex items-center justify-center text-text-secondary hover:text-brand-ink hover:bg-surface-muted transition-all duration-500 ease-out hover:scale-110 active:scale-90 [&>svg]:transition-transform [&>svg]:duration-500 hover:[&>svg]:scale-115 cursor-pointer shadow-2xs"
                              >
                                <MessageSquare size={18} strokeWidth={1.8} />
                              </button>
                            )}

                            {/* Botón Editar */}
                            <button
                              type="button"
                              onClick={() => handleOpenEditModal(c)}
                              title="Editar contacto"
                              aria-label="Editar contacto"
                              className="size-9 rounded-xl border border-border/80 bg-white flex items-center justify-center text-text-secondary hover:text-brand-ink hover:bg-surface-muted transition-all duration-500 ease-out hover:scale-110 active:scale-90 [&>svg]:transition-transform [&>svg]:duration-500 hover:[&>svg]:scale-115 cursor-pointer shadow-2xs"
                            >
                              <Pencil size={18} strokeWidth={1.8} />
                            </button>

                            {/* Botón Eliminar */}
                            {deleteConfirmId === c.id ? (
                              <div className="flex items-center gap-1">
                                <button
                                  type="button"
                                  onClick={() => handleDelete(c.id)}
                                  title="Confirmar eliminación"
                                  aria-label="Confirmar eliminación"
                                  className="size-9 rounded-xl flex items-center justify-center bg-danger text-white hover:bg-rose-700 transition-all duration-500 ease-out hover:scale-110 active:scale-90 [&>svg]:transition-transform [&>svg]:duration-500 hover:[&>svg]:scale-115 cursor-pointer shadow-2xs"
                                >
                                  <Check size={18} strokeWidth={2.2} />
                                </button>
                                <button
                                  type="button"
                                  onClick={() => setDeleteConfirmId(null)}
                                  title="Cancelar"
                                  aria-label="Cancelar"
                                  className="size-9 rounded-xl flex items-center justify-center border border-border/80 bg-white text-text-secondary hover:text-brand-ink transition-all duration-500 ease-out hover:scale-110 active:scale-90 [&>svg]:transition-transform [&>svg]:duration-500 hover:[&>svg]:scale-115 cursor-pointer shadow-2xs"
                                >
                                  <X size={18} strokeWidth={2} />
                                </button>
                              </div>
                            ) : (
                              <button
                                type="button"
                                onClick={() => setDeleteConfirmId(c.id)}
                                title="Eliminar contacto"
                                aria-label="Eliminar contacto"
                                className="size-9 rounded-xl border border-border/80 bg-white flex items-center justify-center text-text-muted hover:text-danger hover:border-danger/30 hover:bg-danger-soft transition-all duration-500 ease-out hover:scale-110 active:scale-90 [&>svg]:transition-transform [&>svg]:duration-500 hover:[&>svg]:scale-115 cursor-pointer shadow-2xs"
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

      {/* Modal Crear / Editar Contacto */}
      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        className="bg-white rounded-xl border border-border shadow-2xl w-full max-w-md overflow-hidden flex flex-col max-h-[90dvh]"
      >
        <div className="flex items-center justify-between border-b border-border px-5 py-3.5 bg-surface-soft">
          <div className="flex items-center gap-2">
            <Users size={18} strokeWidth={1.8} className="text-brand-ink" />
            <h3 className="text-sm font-bold text-brand-ink">
              {editingContacto ? 'Editar Contacto' : 'Nuevo Contacto'}
            </h3>
          </div>
          <button
            type="button"
            onClick={handleCloseModal}
            title="Cerrar modal"
            aria-label="Cerrar modal"
            className="size-9 sm:size-10 rounded-xl border border-border/80 bg-white flex items-center justify-center text-text-muted hover:text-brand-ink hover:bg-surface-muted transition-all duration-500 ease-out hover:scale-105 active:scale-90 [&>svg]:transition-transform [&>svg]:duration-500 hover:[&>svg]:scale-115 cursor-pointer shadow-2xs"
          >
            <X size={18} strokeWidth={2} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-3.5 overflow-y-auto">
          <div>
            <label className="block text-xs font-bold text-brand-ink mb-1">Nombre Completo *</label>
            <input
              type="text"
              required
              placeholder="Ej: Marcelo Benítez"
              value={formData.nombre_completo}
              onChange={(e) => setFormData({ ...formData, nombre_completo: e.target.value })}
              className="w-full h-10 sm:h-11 bg-white border border-border text-brand-ink text-sm sm:text-xs rounded-xl px-3 outline-none transition-all duration-500 focus:border-brand-ink shadow-2xs"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-brand-ink mb-1">
              Teléfono WhatsApp * (con código de país)
            </label>
            <input
              type="text"
              required
              placeholder="+5491166778899"
              value={formData.telefono_wa}
              onChange={(e) => setFormData({ ...formData, telefono_wa: e.target.value })}
              className="w-full h-10 sm:h-11 bg-white border border-border text-brand-ink text-sm sm:text-xs rounded-xl px-3 outline-none transition-all duration-500 focus:border-brand-ink font-normal shadow-2xs"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-brand-ink mb-1">Consorcio Asignado</label>
            <select
              value={formData.consorcio_id}
              onChange={(e) => setFormData({ ...formData, consorcio_id: e.target.value })}
              className="w-full h-10 sm:h-11 bg-white border border-border text-brand-ink text-sm sm:text-xs rounded-xl px-3 outline-none transition-all duration-500 focus:border-brand-ink shadow-2xs"
            >
              <option value="">Sin consorcio asignado</option>
              {consorcios.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nombre}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-brand-ink mb-1">Unidad Funcional</label>
              <input
                type="text"
                placeholder="Ej: 4° B"
                value={formData.unidad_funcional}
                onChange={(e) => setFormData({ ...formData, unidad_funcional: e.target.value })}
                className="w-full h-10 sm:h-11 bg-white border border-border text-brand-ink text-sm sm:text-xs rounded-xl px-3 outline-none transition-all duration-500 focus:border-brand-ink shadow-2xs"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-brand-ink mb-1">Rol / Vínculo</label>
              <select
                value={formData.rol}
                onChange={(e) => setFormData({ ...formData, rol: e.target.value })}
                className="w-full h-10 sm:h-11 bg-white border border-border text-brand-ink text-sm sm:text-xs rounded-xl px-3 outline-none transition-all duration-500 focus:border-brand-ink shadow-2xs"
              >
                {ROLES.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-brand-ink mb-1">Notas Administrativas</label>
            <textarea
              rows={3}
              placeholder="Observaciones de cobranza, horarios de contacto o detalles de la unidad..."
              value={formData.notas}
              onChange={(e) => setFormData({ ...formData, notas: e.target.value })}
              className="w-full bg-white border border-border text-brand-ink text-sm sm:text-xs rounded-xl p-3 outline-none transition-all duration-500 focus:border-brand-ink leading-relaxed shadow-2xs"
            />
          </div>

          <div className="pt-3 border-t border-border flex items-center justify-end gap-2">
            <Button
              variant="ghost"
              size="md"
              type="button"
              onClick={handleCloseModal}
              disabled={submitting}
            >
              Cancelar
            </Button>
            <Button
              variant="primary"
              size="md"
              type="submit"
              loading={submitting}
              className="bg-brand-ink text-white font-semibold"
            >
              <span>{editingContacto ? 'Guardar Cambios' : 'Registrar'}</span>
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
