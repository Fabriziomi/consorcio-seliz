import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Users,
  Search,
  Plus,
  Trash2,
  Edit3,
  MessageSquare,
  Building2,
  RotateCcw,
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
import { ScrollableTableContainer } from '../ui/ScrollableTableContainer.jsx';
import { ApiService } from '../../lib/api-client.js';

const ROLES = [
  { id: 'PROPIETARIO', label: 'Propietario' },
  { id: 'INQUILINO', label: 'Inquilino' },
  { id: 'ENCARGADO', label: 'Portería / Encargado' },
  { id: 'PROVEEDOR', label: 'Proveedor' },
  { id: 'OTRO', label: 'Otro' },
];

export function ContactosManager({ consorcios = [], onOpenChat }) {
  const [contactos, setContactos] = useState([]);
  const [loading, setLoading] = useState(false);
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
  });
  const [submitting, setSubmitting] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);

  const loadContactos = useCallback(async () => {
    setLoading(true);
    try {
      const data = await ApiService.getContactos();
      if (Array.isArray(data)) {
        setContactos(data);
      }
    } catch (err) {
      console.error('[CONTACTOS] Error cargando directorio:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadContactos();
  }, [loadContactos]);

  // Filtrado
  const filtered = useMemo(() => {
    return contactos.filter((c) => {
      const q = searchTerm.toLowerCase();
      const matchesSearch =
        c.nombre_completo.toLowerCase().includes(q) ||
        c.telefono_wa.includes(q) ||
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
      telefono_wa: '+549',
      consorcio_id: '',
      unidad_funcional: '',
      rol: 'PROPIETARIO',
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
    });
    setIsModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.nombre_completo.trim() || !formData.telefono_wa.trim()) {
      alert('Nombre completo y teléfono WhatsApp son obligatorios.');
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
      };

      if (editingContacto) {
        const updated = await ApiService.updateContacto(editingContacto.id, payload);
        setContactos((prev) => prev.map((c) => (c.id === editingContacto.id ? updated : c)));
      } else {
        const created = await ApiService.createContacto(payload);
        setContactos((prev) => [created, ...prev]);
      }
      setIsModalOpen(false);
    } catch (err) {
      console.error('[CONTACTOS] Error al guardar contacto:', err);
      alert('Error al guardar contacto en el servidor.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await ApiService.deleteContacto(id);
      setContactos((prev) => prev.filter((c) => c.id !== id));
      setDeleteConfirmId(null);
    } catch (err) {
      console.error('[CONTACTOS] Error al eliminar contacto:', err);
      alert('No se pudo eliminar el contacto.');
    }
  };

  const getRolBadgeVariant = (rol) => {
    switch (rol) {
      case 'PROPIETARIO':
        return 'brand';
      case 'INQUILINO':
        return 'info';
      case 'ENCARGADO':
        return 'warning';
      case 'PROVEEDOR':
        return 'success';
      default:
        return 'neutral';
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
                <Users size={18} className="text-brand-ink" />
                <h2 className="text-sm sm:text-base font-bold tracking-tight text-brand-ink">
                  Directorio de Vecinos & Contactos
                </h2>
                <Badge variant="neutral" className="text-[10px]">
                  {contactos.length} contactos
                </Badge>
              </div>
              <p className="text-xs text-text-secondary mt-0.5">
                Padrón oficial de propietarios, inquilinos y personal de consorcios con acceso directo al historial de chat.
              </p>
            </div>

            <div className="flex items-center gap-2 self-start sm:self-auto">
              <Button
                variant="secondary"
                size="sm"
                onClick={loadContactos}
                disabled={loading}
                className="h-8 px-2.5 text-xs text-text-secondary hover:text-brand-ink"
                title="Recargar directorio"
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
                <span>Nuevo Contacto</span>
              </Button>
            </div>
          </div>

          {/* Filtros */}
          <div className="mt-3.5 pt-3 border-t border-border/70 flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none" />
              <input
                type="text"
                placeholder="Buscar por nombre, teléfono o unidad funcional…"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full h-8 sm:h-9 bg-surface-soft border border-border text-brand-ink text-xs rounded-base pl-9 pr-3 outline-none transition-colors focus:border-brand-ink focus:bg-white"
              />
            </div>

            <select
              value={filterConsorcio}
              onChange={(e) => setFilterConsorcio(e.target.value)}
              className="h-8 sm:h-9 bg-surface-soft border border-border text-brand-ink text-xs rounded-base px-2.5 outline-none focus:border-brand-ink"
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
              className="h-8 sm:h-9 bg-surface-soft border border-border text-brand-ink text-xs rounded-base px-2.5 outline-none focus:border-brand-ink"
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

        {/* Tabla de Contactos */}
        <CardContent className="flex-1 p-0 overflow-hidden relative">
          <ScrollableTableContainer className="h-full">
            <table className="w-full text-left border-collapse">
              <thead className="sticky top-0 z-10 bg-surface-soft border-b border-border text-[11px] font-bold uppercase tracking-wider text-text-muted">
                <tr>
                  <th className="py-2.5 px-4 min-w-[200px]">Nombre Completo</th>
                  <th className="py-2.5 px-4 min-w-[140px]">Teléfono WhatsApp</th>
                  <th className="py-2.5 px-4 min-w-[180px]">Consorcio</th>
                  <th className="py-2.5 px-4 w-32">Unidad</th>
                  <th className="py-2.5 px-4 w-32 text-center">Rol</th>
                  <th className="py-2.5 px-4 w-28 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-xs">
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-text-muted text-xs">
                      {loading
                        ? 'Cargando directorio de contactos...'
                        : 'No se encontraron contactos con los filtros seleccionados.'}
                    </td>
                  </tr>
                ) : (
                  filtered.map((c) => (
                    <tr key={c.id} className="hover:bg-surface-soft/60 transition-colors">
                      {/* Nombre */}
                      <td className="py-3 px-4 font-bold text-brand-ink">
                        <div className="flex items-center gap-2">
                          <div className="size-7 rounded-full bg-surface-muted text-brand-ink font-bold text-[11px] flex items-center justify-center shrink-0 border border-border">
                            {c.nombre_completo ? c.nombre_completo.charAt(0).toUpperCase() : 'V'}
                          </div>
                          <span className="truncate">{c.nombre_completo}</span>
                        </div>
                      </td>

                      {/* Teléfono */}
                      <td className="py-3 px-4 font-mono text-brand-ink">
                        <div className="flex items-center gap-1.5 text-text-secondary">
                          <Phone size={12} className="text-text-muted shrink-0" />
                          <span className="text-xs">{c.telefono_wa}</span>
                        </div>
                      </td>

                      {/* Consorcio */}
                      <td className="py-3 px-4 text-text-secondary">
                        {c.consorcio_nombre ? (
                          <div className="flex items-center gap-1.5 text-brand-ink">
                            <Building2 size={13} className="text-text-muted shrink-0" />
                            <span className="truncate">{c.consorcio_nombre}</span>
                          </div>
                        ) : (
                          <span className="text-text-muted text-[11px] italic">Sin consorcio</span>
                        )}
                      </td>

                      {/* Unidad */}
                      <td className="py-3 px-4 text-brand-ink font-medium">
                        {c.unidad_funcional || <span className="text-text-muted text-[11px]">S/E</span>}
                      </td>

                      {/* Rol */}
                      <td className="py-3 px-4 text-center">
                        <Badge variant={getRolBadgeVariant(c.rol)} className="text-[10px]">
                          {c.rol}
                        </Badge>
                      </td>

                      {/* Acciones */}
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1">
                          {/* Abrir Chat */}
                          {onOpenChat && (
                            <button
                              type="button"
                              onClick={() => onOpenChat(c)}
                              title="Abrir conversación en Inbox"
                              className="size-7 rounded-base flex items-center justify-center text-text-secondary hover:text-brand-ink hover:bg-surface-muted transition-colors cursor-pointer"
                            >
                              <MessageSquare size={13} />
                            </button>
                          )}

                          {/* Editar */}
                          <button
                            type="button"
                            onClick={() => handleOpenEditModal(c)}
                            title="Editar contacto"
                            className="size-7 rounded-base flex items-center justify-center text-text-secondary hover:text-brand-ink hover:bg-surface-muted transition-colors cursor-pointer"
                          >
                            <Edit3 size={13} />
                          </button>

                          {/* Eliminar con confirmación */}
                          {deleteConfirmId === c.id ? (
                            <div className="flex items-center gap-1">
                              <button
                                type="button"
                                onClick={() => handleDelete(c.id)}
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
                              onClick={() => setDeleteConfirmId(c.id)}
                              title="Eliminar contacto"
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

      {/* Modal Crear / Editar Contacto */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-brand-ink/40 backdrop-blur-xs animate-in fade-in duration-150">
          <div className="bg-white rounded-base border border-border shadow-2xl w-full max-w-md overflow-hidden flex flex-col max-h-[90dvh]">
            <div className="flex items-center justify-between border-b border-border px-5 py-3.5 bg-surface-soft">
              <div className="flex items-center gap-2">
                <Users size={16} className="text-brand-ink" />
                <h3 className="text-sm font-bold text-brand-ink">
                  {editingContacto ? 'Editar Contacto' : 'Registrar Nuevo Contacto'}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="size-7 rounded-base flex items-center justify-center text-text-muted hover:text-brand-ink hover:bg-surface-muted transition-colors cursor-pointer"
              >
                <X size={15} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-5 space-y-4 overflow-y-auto">
              <div>
                <label className="block text-xs font-bold text-brand-ink mb-1">Nombre Completo *</label>
                <input
                  type="text"
                  required
                  placeholder="Ej: Lucía Rossi"
                  value={formData.nombre_completo}
                  onChange={(e) => setFormData({ ...formData, nombre_completo: e.target.value })}
                  className="w-full h-9 bg-white border border-border text-brand-ink text-xs rounded-base px-3 outline-none focus:border-brand-ink"
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
                  className="w-full h-9 bg-white border border-border text-brand-ink text-xs rounded-base px-3 outline-none focus:border-brand-ink font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-brand-ink mb-1">Consorcio Asignado</label>
                <select
                  value={formData.consorcio_id}
                  onChange={(e) => setFormData({ ...formData, consorcio_id: e.target.value })}
                  className="w-full h-9 bg-white border border-border text-brand-ink text-xs rounded-base px-2.5 outline-none focus:border-brand-ink"
                >
                  <option value="">Sin consorcio asignado</option>
                  {consorcios.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nombre}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-brand-ink mb-1">Unidad Funcional</label>
                  <input
                    type="text"
                    placeholder="Ej: 7° A, Cochera 12"
                    value={formData.unidad_funcional}
                    onChange={(e) => setFormData({ ...formData, unidad_funcional: e.target.value })}
                    className="w-full h-9 bg-white border border-border text-brand-ink text-xs rounded-base px-3 outline-none focus:border-brand-ink"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-brand-ink mb-1">Rol</label>
                  <select
                    value={formData.rol}
                    onChange={(e) => setFormData({ ...formData, rol: e.target.value })}
                    className="w-full h-9 bg-white border border-border text-brand-ink text-xs rounded-base px-2.5 outline-none focus:border-brand-ink"
                  >
                    {ROLES.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="pt-3 border-t border-border flex items-center justify-end gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  type="button"
                  onClick={() => setIsModalOpen(false)}
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
                  className="h-9 px-4 text-xs bg-brand-ink text-white font-semibold"
                >
                  {submitting ? 'Guardando...' : editingContacto ? 'Guardar Cambios' : 'Registrar Contacto'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
