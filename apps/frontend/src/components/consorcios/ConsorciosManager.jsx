import React, { useState, useEffect, useCallback } from 'react';
import {
  Building2,
  Plus,
  Trash2,
  Pencil,
  Save,
  RotateCw,
  Check,
  X,
  Phone,
  CreditCard,
  Mail,
  Truck,
  Eye,
  EyeOff,
  Layers,
  ChevronRight,
  ChevronLeft,
  AlertCircle,
} from 'lucide-react';
import { useToast } from '../ui/ToastNotification.jsx';
import { Card, CardHeader, CardContent } from '../ui/Card.jsx';
import { Badge } from '../ui/Badge.jsx';
import { Button } from '../ui/Button.jsx';
import { Modal } from '../ui/Modal.jsx';
import { ApiService } from '../../lib/api-client.js';

export function ConsorciosManager({ consorcios: initialConsorcios = [], onRefreshParent }) {
  const toast = useToast();
  const [consorcios, setConsorcios] = useState(initialConsorcios);
  const [selectedId, setSelectedId] = useState(() => initialConsorcios[0]?.id || null);
  const [activeSubTab, setActiveSubTab] = useState('datos'); // 'datos' | 'atributos'
  const [mobileView, setMobileView] = useState('list'); // 'list' | 'detail' en vista movil
  const [loading, setLoading] = useState(false);
  const [savingConsorcio, setSavingConsorcio] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState('');

  // Atributos dinámicos del consorcio seleccionado
  const [atributos, setAtributos] = useState([]);
  const [loadingAtributos, setLoadingAtributos] = useState(false);
  const [editingAttrId, setEditingAttrId] = useState(null);
  const [editAttrForm, setEditAttrForm] = useState({ clave: '', etiqueta: '', valor: '', es_publico: false });
  const [newAttrForm, setNewAttrForm] = useState({ clave: '', etiqueta: '', valor: '', es_publico: false });
  const [showNewAttrRow, setShowNewAttrRow] = useState(false);

  // Modal para Crear Consorcio
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createForm, setCreateForm] = useState({
    nombre: '',
    direccion: '',
    cuit: '',
    cbu_bancario: '',
    alias_bancario: '',
    email_cobranzas: '',
    telefono_porteria: '',
    emergencia_ascensores: '',
    emergencia_plomeria: '',
    pautas_mudanza: '',
  });
  const [creating, setCreating] = useState(false);

  // Formulario de edición del consorcio seleccionado
  const [currentForm, setCurrentForm] = useState({});

  const loadConsorcios = useCallback(async () => {
    setLoading(true);
    try {
      const data = await ApiService.getConsorcios();
      if (Array.isArray(data) && data.length > 0) {
        setConsorcios(data);
        if (!selectedId || !data.some((c) => c.id === selectedId)) {
          setSelectedId(data[0].id);
        }
      }
      if (onRefreshParent) onRefreshParent();
    } catch (err) {
      console.error('[CONSORCIOS] Error al recargar consorcios:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedId, onRefreshParent]);

  // Sincronizar selección actual con el formulario
  useEffect(() => {
    if (selectedId) {
      const current = consorcios.find((c) => c.id === selectedId);
      if (current) {
        setCurrentForm({
          nombre: current.nombre || '',
          direccion: current.direccion || '',
          cuit: current.cuit || '',
          cbu_bancario: current.cbu_bancario || '',
          alias_bancario: current.alias_bancario || '',
          email_cobranzas: current.email_cobranzas || '',
          telefono_porteria: current.telefono_porteria || '',
          emergencia_ascensores: current.emergencia_ascensores || '',
          emergencia_plomeria: current.emergencia_plomeria || '',
          pautas_mudanza: current.pautas_mudanza || '',
        });
      }
    }
  }, [selectedId, consorcios]);

  // Cargar atributos dinámicos cuando cambia el consorcio
  const loadAtributos = useCallback(async (consorcioId) => {
    if (!consorcioId) return;
    setLoadingAtributos(true);
    try {
      const data = await ApiService.getAtributos(consorcioId);
      setAtributos(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('[CONSORCIOS] Error al cargar atributos dinámicos:', err);
      setAtributos([]);
    } finally {
      setLoadingAtributos(false);
    }
  }, []);

  useEffect(() => {
    if (selectedId && activeSubTab === 'atributos') {
      loadAtributos(selectedId);
    }
  }, [selectedId, activeSubTab, loadAtributos]);

  const selectedConsorcio = consorcios.find((c) => c.id === selectedId);

  // Guardar datos del consorcio
  const handleSaveConsorcio = async (e) => {
    e.preventDefault();
    if (!selectedId) return;

    setSavingConsorcio(true);
    setSaveSuccessMsg('');
    try {
      const updated = await ApiService.updateConsorcio(selectedId, currentForm);
      setConsorcios((prev) => prev.map((c) => (c.id === selectedId ? updated : c)));
      setSaveSuccessMsg('Datos actualizados correctamente.');
      setTimeout(() => setSaveSuccessMsg(''), 4000);
      if (onRefreshParent) onRefreshParent();
    } catch (err) {
      console.error('[CONSORCIOS] Error al actualizar consorcio:', err);
      alert('Error al guardar los cambios del consorcio.');
    } finally {
      setSavingConsorcio(false);
    }
  };

  // Crear nuevo consorcio
  const handleCreateConsorcio = async (e) => {
    e.preventDefault();
    if (!createForm.nombre.trim() || !createForm.direccion.trim()) {
      alert('Nombre y dirección son obligatorios.');
      return;
    }

    setCreating(true);
    try {
      const created = await ApiService.createConsorcio(createForm);
      setConsorcios((prev) => [...prev, created]);
      setSelectedId(created.id);
      setIsCreateModalOpen(false);
      setCreateForm({
        nombre: '',
        direccion: '',
        cuit: '',
        cbu_bancario: '',
        alias_bancario: '',
        email_cobranzas: '',
        telefono_porteria: '',
        emergencia_ascensores: '',
        emergencia_plomeria: '',
        pautas_mudanza: '',
      });
      if (onRefreshParent) onRefreshParent();
    } catch (err) {
      console.error('[CONSORCIOS] Error al crear consorcio:', err);
      alert('No se pudo crear el consorcio.');
    } finally {
      setCreating(false);
    }
  };

  // Atributos dinámicos: Crear nuevo
  const handleCreateAtributo = async (e) => {
    e.preventDefault();
    if (!newAttrForm.clave.trim() || !newAttrForm.valor.trim()) {
      alert('Clave y valor son obligatorios.');
      return;
    }

    try {
      const created = await ApiService.createAtributo(selectedId, {
        clave: newAttrForm.clave.trim().toLowerCase(),
        etiqueta: newAttrForm.etiqueta.trim() || newAttrForm.clave.trim(),
        valor: newAttrForm.valor.trim(),
        es_publico: newAttrForm.es_publico,
      });
      setAtributos((prev) => [...prev, created]);
      setNewAttrForm({ clave: '', etiqueta: '', valor: '', es_publico: false });
      setShowNewAttrRow(false);
    } catch (err) {
      console.error('[CONSORCIOS] Error al crear atributo dinámico:', err);
      alert('Error al crear atributo dinámico.');
    }
  };

  // Atributos dinámicos: Iniciar edición
  const handleStartEditAttr = (attr) => {
    setEditingAttrId(attr.id);
    setEditAttrForm({
      clave: attr.clave,
      etiqueta: attr.etiqueta || '',
      valor: attr.valor,
      es_publico: !!attr.es_publico,
    });
  };

  // Atributos dinámicos: Guardar edición
  const handleSaveEditAttr = async (attrId) => {
    try {
      const updated = await ApiService.updateAtributo(selectedId, attrId, editAttrForm);
      setAtributos((prev) => prev.map((a) => (a.id === attrId ? updated : a)));
      setEditingAttrId(null);
    } catch (err) {
      console.error('[CONSORCIOS] Error al editar atributo:', err);
      alert('Error al actualizar atributo.');
    }
  };

  // Atributos dinámicos: Eliminar
  const handleDeleteAttr = async (attrId) => {
    if (!confirm('¿Estás seguro de eliminar este atributo dinámico?')) return;
    try {
      await ApiService.deleteAtributo(selectedId, attrId);
      setAtributos((prev) => prev.filter((a) => a.id !== attrId));
    } catch (err) {
      console.error('[CONSORCIOS] Error al eliminar atributo:', err);
      alert('No se pudo eliminar el atributo.');
    }
  };

  return (
    <div className="w-full space-y-3.5 sm:space-y-4">
      {/* Contenedor Master/Detail */}
      <div className="flex flex-col md:flex-row gap-3.5 md:items-start">
        {/* Columna Izquierda: Lista de Consorcios */}
        <Card className={`w-full md:w-72 lg:w-80 flex flex-col bg-white border border-border shadow-subtle shrink-0 overflow-hidden md:sticky md:top-0 max-h-[calc(100dvh-6.5rem)] ${mobileView === 'detail' ? 'hidden md:flex' : 'flex'}`}>
          <CardHeader className="p-3.5 sm:p-4 border-b border-border bg-white flex items-center justify-between shrink-0">
            <div>
              <h2 className="text-lg sm:text-xl font-bold tracking-tight text-brand-ink">
                Consorcios
              </h2>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                size="icon-sm"
                onClick={loadConsorcios}
                disabled={loading}
                title="Recargar consorcios"
              >
                <RotateCw size={18} strokeWidth={2} className={loading ? 'animate-spin' : ''} />
              </Button>
              <Button
                variant="primary"
                size="icon-sm"
                onClick={() => setIsCreateModalOpen(true)}
                className="bg-brand-ink text-white"
                title="Nuevo Consorcio"
              >
                <Plus size={18} strokeWidth={2} />
              </Button>
            </div>
          </CardHeader>

          <CardContent className="p-0 overflow-y-auto divide-y divide-border max-h-[calc(100dvh-12rem)]">
            {consorcios.map((c) => {
              const isSelected = c.id === selectedId;
              return (
                <div
                  key={c.id}
                  onClick={() => {
                    setSelectedId(c.id);
                    setMobileView('detail');
                  }}
                  className={`p-3.5 cursor-pointer group transition-all duration-500 ease-out flex items-center justify-between gap-2 border-l-4 hover:translate-x-0.5 ${
                    isSelected
                      ? 'bg-surface-soft border-brand-ink'
                      : 'border-transparent hover:bg-surface-soft/80'
                  }`}
                >
                  <div className="min-w-0">
                    <p className="text-xs sm:text-sm font-bold text-brand-ink truncate">
                      {c.nombre}
                    </p>
                    <p className="text-[11px] text-text-muted truncate mt-0.5">
                      {c.direccion}
                    </p>
                    {c.cuit && (
                      <span className="inline-block mt-1 text-[10px] font-semibold text-text-secondary bg-surface-muted px-1.5 py-0.2 rounded border border-border/60">
                        CUIT {c.cuit}
                      </span>
                    )}
                  </div>
                  <ChevronRight size={14} strokeWidth={2} className={`transition-all duration-500 ease-out group-hover:translate-x-1 group-hover:scale-120 ${isSelected ? 'text-brand-ink' : 'text-text-muted'}`} />
                </div>
              );
            })}
          </CardContent>
        </Card>

        {/* Columna Derecha: Ficha de Edición y Atributos Dinámicos */}
        <Card className={`flex-1 flex flex-col bg-white border border-border shadow-subtle overflow-hidden max-h-[calc(100dvh-6.5rem)] ${mobileView === 'list' ? 'hidden md:flex' : 'flex'}`}>
          {selectedConsorcio ? (
            <>
              {/* Header de la Ficha con Botón Volver en Móvil */}
              <div className="px-4 sm:px-5 py-3 sm:py-4 border-b border-border bg-white flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0">
                <div className="flex items-center gap-2.5 min-w-0">
                  <button
                    type="button"
                    onClick={() => setMobileView('list')}
                    aria-label="Volver al listado de consorcios"
                    title="Volver al listado de consorcios"
                    className="md:hidden size-9 rounded-xl border border-border/80 flex items-center justify-center text-brand-ink hover:bg-surface-muted transition-all duration-500 ease-out hover:scale-105 active:scale-90 [&>svg]:transition-transform [&>svg]:duration-500 hover:[&>svg]:scale-115 shrink-0 shadow-2xs cursor-pointer"
                  >
                    <ChevronLeft size={20} strokeWidth={2} />
                  </button>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <Building2 size={18} strokeWidth={1.8} className="text-brand-ink shrink-0" />
                      <h2 className="text-sm sm:text-base font-bold text-brand-ink truncate">
                        {selectedConsorcio.nombre}
                      </h2>
                    </div>
                    <p className="text-xs text-text-secondary mt-0.5 truncate">
                      {selectedConsorcio.direccion}
                    </p>
                  </div>
                </div>

                {/* Sub-Tabs: Datos Administrativos vs Atributos Dinámicos */}
                <div className="flex items-center gap-1.5 bg-surface-muted p-1 rounded-xl border border-border/80 shrink-0 self-start sm:self-auto">
                  <button
                    type="button"
                    onClick={() => setActiveSubTab('datos')}
                    className={`text-xs sm:text-sm font-semibold px-3.5 py-1.5 rounded-lg transition-all duration-500 ease-out cursor-pointer hover:scale-[1.02] active:scale-95 ${
                      activeSubTab === 'datos'
                        ? 'bg-brand-ink text-white shadow-xs'
                        : 'text-text-secondary hover:text-brand-ink'
                    }`}
                  >
                    Datos Oficiales
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveSubTab('atributos')}
                    className={`text-xs sm:text-sm font-semibold px-3.5 py-1.5 rounded-lg transition-all duration-500 ease-out cursor-pointer flex items-center gap-2 hover:scale-[1.02] active:scale-95 [&>svg]:transition-transform [&>svg]:duration-500 hover:[&>svg]:scale-115 ${
                      activeSubTab === 'atributos'
                        ? 'bg-brand-ink text-white shadow-xs'
                        : 'text-text-secondary hover:text-brand-ink'
                    }`}
                  >
                    <Layers size={16} strokeWidth={2} />
                    <span>Atributos Dinámicos</span>
                  </button>
                </div>
              </div>

              {/* Mensaje de Éxito al Guardar */}
              {saveSuccessMsg && (
                <div className="px-5 py-2.5 bg-emerald-50 border-b border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center gap-2">
                  <Check size={14} strokeWidth={2.2} />
                  <span>{saveSuccessMsg}</span>
                </div>
              )}

              {/* Contenido según SubTab */}
              <div className="flex-1 overflow-y-auto p-4 sm:p-6 min-h-0">
                {activeSubTab === 'datos' ? (
                  /* Formulario de Edición de Consorcio */
                  <form onSubmit={handleSaveConsorcio} className="space-y-4 w-full">
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-xs font-bold text-brand-ink mb-1">
                          Nombre del Consorcio *
                        </label>
                        <input
                          type="text"
                          required
                          value={currentForm.nombre || ''}
                          onChange={(e) => setCurrentForm({ ...currentForm, nombre: e.target.value })}
                          className="w-full h-10 sm:h-11 bg-white border border-border text-brand-ink text-sm sm:text-xs rounded-xl px-3 sm:px-3.5 outline-none transition-all duration-500 focus:border-brand-ink shadow-2xs"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-brand-ink mb-1">
                          Dirección Completa *
                        </label>
                        <input
                          type="text"
                          required
                          value={currentForm.direccion || ''}
                          onChange={(e) => setCurrentForm({ ...currentForm, direccion: e.target.value })}
                          className="w-full h-10 sm:h-11 bg-white border border-border text-brand-ink text-sm sm:text-xs rounded-xl px-3 sm:px-3.5 outline-none transition-all duration-500 focus:border-brand-ink shadow-2xs"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-brand-ink mb-1">
                          CUIT Tributario
                        </label>
                        <input
                          type="text"
                          placeholder="30-71122334-5"
                          value={currentForm.cuit || ''}
                          onChange={(e) => setCurrentForm({ ...currentForm, cuit: e.target.value })}
                          className="w-full h-10 sm:h-11 bg-white border border-border text-brand-ink text-sm sm:text-xs rounded-xl px-3 sm:px-3.5 outline-none transition-all duration-500 focus:border-brand-ink shadow-2xs"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-brand-ink mb-1">
                          Email de Cobranzas / Liquidación
                        </label>
                        <input
                          type="email"
                          placeholder="cobranzas@selizadministraciones.com.ar"
                          value={currentForm.email_cobranzas || ''}
                          onChange={(e) => setCurrentForm({ ...currentForm, email_cobranzas: e.target.value })}
                          className="w-full h-10 sm:h-11 bg-white border border-border text-brand-ink text-sm sm:text-xs rounded-xl px-3 sm:px-3.5 outline-none transition-all duration-500 focus:border-brand-ink shadow-2xs"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-brand-ink mb-1">
                          CBU Bancario Oficial (22 dígitos)
                        </label>
                        <input
                          type="text"
                          placeholder="0140000000000000000001"
                          value={currentForm.cbu_bancario || ''}
                          onChange={(e) => setCurrentForm({ ...currentForm, cbu_bancario: e.target.value })}
                          className="w-full h-10 sm:h-11 bg-white border border-border text-brand-ink text-sm sm:text-xs rounded-xl px-3 sm:px-3.5 outline-none transition-all duration-500 focus:border-brand-ink shadow-2xs"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-brand-ink mb-1">
                          Alias Bancario
                        </label>
                        <input
                          type="text"
                          placeholder="CONSORCIO.LAVALLE.OFICIAL"
                          value={currentForm.alias_bancario || ''}
                          onChange={(e) => setCurrentForm({ ...currentForm, alias_bancario: e.target.value })}
                          className="w-full h-10 sm:h-11 bg-white border border-border text-brand-ink text-sm sm:text-xs rounded-xl px-3 sm:px-3.5 outline-none transition-all duration-500 focus:border-brand-ink font-semibold shadow-2xs"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-brand-ink mb-1">
                          Teléfono Portería / Encargado
                        </label>
                        <input
                          type="text"
                          placeholder="+54 9 11 4371-0001"
                          value={currentForm.telefono_porteria || ''}
                          onChange={(e) => setCurrentForm({ ...currentForm, telefono_porteria: e.target.value })}
                          className="w-full h-10 sm:h-11 bg-white border border-border text-brand-ink text-sm sm:text-xs rounded-xl px-3 sm:px-3.5 outline-none transition-all duration-500 focus:border-brand-ink shadow-2xs"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-brand-ink mb-1">
                          Guardia Ascensores 24hs
                        </label>
                        <input
                          type="text"
                          placeholder="+54 9 11 4444-1111"
                          value={currentForm.emergencia_ascensores || ''}
                          onChange={(e) => setCurrentForm({ ...currentForm, emergencia_ascensores: e.target.value })}
                          className="w-full h-10 sm:h-11 bg-white border border-border text-brand-ink text-sm sm:text-xs rounded-xl px-3 sm:px-3.5 outline-none transition-all duration-500 focus:border-brand-ink shadow-2xs"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-brand-ink mb-1">
                          Guardia Plomería / Destapes 24hs
                        </label>
                        <input
                          type="text"
                          placeholder="+54 9 11 4444-2222"
                          value={currentForm.emergencia_plomeria || ''}
                          onChange={(e) => setCurrentForm({ ...currentForm, emergencia_plomeria: e.target.value })}
                          className="w-full h-10 sm:h-11 bg-white border border-border text-brand-ink text-sm sm:text-xs rounded-xl px-3 sm:px-3.5 outline-none transition-all duration-500 focus:border-brand-ink shadow-2xs"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-brand-ink mb-1">
                        Pautas Oficiales de Mudanza
                      </label>
                      <textarea
                        rows={3}
                        placeholder="Días y horarios permitidos, seguro de flete y requisitos..."
                        value={currentForm.pautas_mudanza || ''}
                        onChange={(e) => setCurrentForm({ ...currentForm, pautas_mudanza: e.target.value })}
                        className="w-full bg-white border border-border text-brand-ink text-sm sm:text-xs rounded-xl p-3 outline-none transition-all duration-500 focus:border-brand-ink leading-relaxed shadow-2xs"
                      />
                    </div>

                    <div className="pt-3 border-t border-border flex justify-end">
                      <Button
                        type="submit"
                        variant="primary"
                        size="md"
                        disabled={savingConsorcio}
                        className="bg-brand-ink text-white font-semibold flex items-center gap-2"
                      >
                        <Save size={18} strokeWidth={2} />
                        <span>{savingConsorcio ? 'Guardando...' : 'Guardar Cambios Oficiales'}</span>
                      </Button>
                    </div>
                  </form>
                ) : (
                  /* SubTab: Atributos Dinámicos */
                  <div className="space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <h3 className="text-sm sm:text-base font-bold text-brand-ink">
                          Atributos Personalizados del Consorcio
                        </h3>
                        <p className="text-xs text-text-secondary mt-0.5">
                          Variables y valores específicos consultables por el bot o el CRM (claves de alarma, códigos de portón, teléfonos extra).
                        </p>
                      </div>

                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => setShowNewAttrRow(true)}
                        className="bg-brand-ink text-white font-semibold flex items-center gap-2 self-start sm:self-auto"
                      >
                        <Plus size={18} strokeWidth={2} />
                        <span>Agregar Atributo</span>
                      </Button>
                    </div>

                    {/* Fila para agregar nuevo atributo inline */}
                    {showNewAttrRow && (
                      <form onSubmit={handleCreateAtributo} className="p-3 bg-surface-soft border border-brand-ink/40 rounded-base space-y-3">
                        <p className="text-xs font-bold text-brand-ink">Nuevo Atributo Dinámico</p>
                        <div className="grid grid-cols-1 sm:grid-cols-4 gap-2.5">
                          <input
                            type="text"
                            required
                            placeholder="Identificador (ej: codigo_alarma)"
                            value={newAttrForm.clave}
                            onChange={(e) => setNewAttrForm({ ...newAttrForm, clave: e.target.value })}
                            className="h-8 bg-white border border-border text-brand-ink text-xs rounded px-2.5 outline-none"
                          />
                          <input
                            type="text"
                            placeholder="Nombre visible (ej: Código Alarma)"
                            value={newAttrForm.etiqueta}
                            onChange={(e) => setNewAttrForm({ ...newAttrForm, etiqueta: e.target.value })}
                            className="h-8 bg-white border border-border text-brand-ink text-xs rounded px-2.5 outline-none"
                          />
                          <input
                            type="text"
                            required
                            placeholder="Valor asignado"
                            value={newAttrForm.valor}
                            onChange={(e) => setNewAttrForm({ ...newAttrForm, valor: e.target.value })}
                            className="h-8 bg-white border border-border text-brand-ink text-xs rounded px-2.5 outline-none"
                          />
                          <label className="flex items-center gap-2 cursor-pointer select-none text-xs text-brand-ink font-medium">
                            <input
                              type="checkbox"
                              checked={newAttrForm.es_publico}
                              onChange={(e) => setNewAttrForm({ ...newAttrForm, es_publico: e.target.checked })}
                              className="size-4 rounded border-border text-brand-ink"
                            />
                            <span>Visible para vecinos</span>
                          </label>
                        </div>
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="secondary"
                            size="sm"
                            type="button"
                            onClick={() => setShowNewAttrRow(false)}
                            className="h-7 px-2.5 text-xs"
                          >
                            Cancelar
                          </Button>
                          <Button
                            variant="primary"
                            size="sm"
                            type="submit"
                            className="h-7 px-3 text-xs bg-brand-ink text-white"
                          >
                            Guardar Atributo
                          </Button>
                        </div>
                      </form>
                    )}

                    {/* Tabla de Atributos */}
                    <div className="border border-border rounded-base overflow-hidden">
                      <table className="w-full text-left border-collapse">
                        <thead className="bg-surface-soft border-b border-border text-[11px] font-bold uppercase tracking-wider text-text-muted">
                          <tr>
                            <th className="py-2.5 px-3">Identificador</th>
                            <th className="py-2.5 px-3">Nombre del Dato</th>
                            <th className="py-2.5 px-3">Valor</th>
                            <th className="py-2.5 px-3 text-center">Visibilidad</th>
                            <th className="py-2.5 px-3 text-right">Acciones</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border text-xs">
                          {atributos.length === 0 ? (
                            <tr>
                              <td colSpan={5} className="py-8 text-center text-text-muted text-xs">
                                {loadingAtributos ? 'Cargando atributos...' : 'Este consorcio no tiene atributos dinámicos configurados.'}
                              </td>
                            </tr>
                          ) : (
                            atributos.map((attr) => (
                              <tr key={attr.id} className="hover:bg-surface-soft/60 transition-colors duration-500">
                                {editingAttrId === attr.id ? (
                                  <>
                                    <td className="py-2 px-3">
                                      <input
                                        type="text"
                                        value={editAttrForm.clave}
                                        onChange={(e) => setEditAttrForm({ ...editAttrForm, clave: e.target.value })}
                                        className="h-7 w-full bg-white border border-border text-xs rounded px-2 transition-all duration-500 outline-none focus:border-brand-ink"
                                      />
                                    </td>
                                    <td className="py-2 px-3">
                                      <input
                                        type="text"
                                        value={editAttrForm.etiqueta}
                                        onChange={(e) => setEditAttrForm({ ...editAttrForm, etiqueta: e.target.value })}
                                        className="h-7 w-full bg-white border border-border text-xs rounded px-2 transition-all duration-500 outline-none focus:border-brand-ink"
                                      />
                                    </td>
                                    <td className="py-2 px-3">
                                      <input
                                        type="text"
                                        value={editAttrForm.valor}
                                        onChange={(e) => setEditAttrForm({ ...editAttrForm, valor: e.target.value })}
                                        className="h-7 w-full bg-white border border-border text-xs rounded px-2 transition-all duration-500 outline-none focus:border-brand-ink"
                                      />
                                    </td>
                                    <td className="py-2 px-3 text-center">
                                      <input
                                        type="checkbox"
                                        checked={editAttrForm.es_publico}
                                        onChange={(e) => setEditAttrForm({ ...editAttrForm, es_publico: e.target.checked })}
                                        className="size-4"
                                      />
                                    </td>
                                    <td className="py-2.5 px-3 text-right">
                                      <div className="flex items-center justify-end gap-1.5">
                                        <button
                                          type="button"
                                          onClick={() => handleSaveEditAttr(attr.id)}
                                          title="Guardar atributo"
                                          className="size-8 sm:size-9 rounded-xl bg-brand-ink text-white flex items-center justify-center cursor-pointer shadow-2xs hover:bg-black transition-all duration-500 ease-out hover:scale-110 active:scale-90 [&>svg]:transition-transform [&>svg]:duration-500 hover:[&>svg]:scale-115"
                                        >
                                          <Check size={16} strokeWidth={2.2} />
                                        </button>
                                        <button
                                          type="button"
                                          onClick={() => setEditingAttrId(null)}
                                          title="Cancelar edición"
                                          className="size-8 sm:size-9 rounded-xl border border-border/80 bg-white text-text-secondary hover:text-brand-ink hover:bg-surface-muted flex items-center justify-center cursor-pointer shadow-2xs transition-all duration-500 ease-out hover:scale-110 active:scale-90 [&>svg]:transition-transform [&>svg]:duration-500 hover:[&>svg]:scale-115"
                                        >
                                          <X size={16} strokeWidth={2.2} />
                                        </button>
                                      </div>
                                    </td>
                                  </>
                                ) : (
                                  <>
                                    <td className="py-2.5 px-3 font-semibold text-brand-ink">
                                      {attr.clave}
                                    </td>
                                    <td className="py-2.5 px-3 text-text-secondary">
                                      {attr.etiqueta || attr.clave}
                                    </td>
                                    <td className="py-2.5 px-3 font-medium text-brand-ink">
                                      {attr.valor}
                                    </td>
                                    <td className="py-2.5 px-3 text-center">
                                      {attr.es_publico ? (
                                        <Badge variant="success" className="text-[10px]">
                                          Público
                                        </Badge>
                                      ) : (
                                        <Badge variant="neutral" className="text-[10px]">
                                          Restringido
                                        </Badge>
                                      )}
                                    </td>
                                    <td className="py-2.5 px-3 text-right">
                                      <div className="flex items-center justify-end gap-1.5">
                                        <button
                                          type="button"
                                          onClick={() => handleStartEditAttr(attr)}
                                          title="Editar atributo"
                                          className="size-8 sm:size-9 rounded-xl border border-border/80 bg-white text-text-secondary hover:text-brand-ink hover:bg-surface-muted flex items-center justify-center cursor-pointer shadow-2xs transition-all duration-500 ease-out hover:scale-110 active:scale-90 [&>svg]:transition-transform [&>svg]:duration-500 hover:[&>svg]:scale-115"
                                        >
                                          <Pencil size={16} strokeWidth={1.8} />
                                        </button>
                                        <button
                                          type="button"
                                          onClick={() => handleDeleteAttr(attr.id)}
                                          title="Eliminar atributo"
                                          className="size-8 sm:size-9 rounded-xl border border-border/80 bg-white text-text-muted hover:text-danger hover:border-danger/30 hover:bg-danger-soft flex items-center justify-center cursor-pointer shadow-2xs transition-all duration-500 ease-out hover:scale-110 active:scale-90 [&>svg]:transition-transform [&>svg]:duration-500 hover:[&>svg]:scale-115"
                                        >
                                          <Trash2 size={16} strokeWidth={1.8} />
                                        </button>
                                      </div>
                                    </td>
                                  </>
                                )}
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-text-muted">
              Seleccione un consorcio para ver y editar sus datos oficiales y atributos.
            </div>
          )}
        </Card>
      </div>

      {/* Modal Crear Nuevo Consorcio */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        className="bg-white rounded-base border border-border shadow-2xl w-full max-w-lg overflow-hidden flex flex-col max-h-[90dvh]"
      >
        <div className="flex items-center justify-between border-b border-border px-5 py-3.5 bg-surface-soft">
          <div className="flex items-center gap-2">
            <Building2 size={18} strokeWidth={1.8} className="text-brand-ink" />
            <h3 className="text-sm font-bold text-brand-ink">Registrar Nuevo Consorcio</h3>
          </div>
          <button
            type="button"
            onClick={() => setIsCreateModalOpen(false)}
            className="size-9 sm:size-10 rounded-xl flex items-center justify-center text-text-muted hover:text-brand-ink hover:bg-surface-muted transition-all duration-500 ease-out hover:scale-105 active:scale-90 [&>svg]:transition-transform [&>svg]:duration-500 hover:[&>svg]:scale-115 cursor-pointer border border-border/80 shadow-2xs"
            aria-label="Cerrar modal"
          >
            <X size={18} strokeWidth={2} />
          </button>
        </div>

        <form onSubmit={handleCreateConsorcio} className="p-5 space-y-4 overflow-y-auto">
          <div>
            <label className="block text-xs font-bold text-brand-ink mb-1">Nombre Oficial del Consorcio *</label>
            <input
              type="text"
              required
              placeholder="Ej: Consorcio Corrientes 1240"
              value={createForm.nombre}
              onChange={(e) => setCreateForm({ ...createForm, nombre: e.target.value })}
              className="w-full h-9 bg-white border border-border text-brand-ink text-xs rounded-base px-3 outline-none focus:border-brand-ink"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-brand-ink mb-1">Dirección Completa *</label>
            <input
              type="text"
              required
              placeholder="Ej: Av. Corrientes 1240, CABA"
              value={createForm.direccion}
              onChange={(e) => setCreateForm({ ...createForm, direccion: e.target.value })}
              className="w-full h-9 bg-white border border-border text-brand-ink text-xs rounded-base px-3 outline-none focus:border-brand-ink"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-brand-ink mb-1">CUIT</label>
              <input
                type="text"
                placeholder="30-71122334-5"
                value={createForm.cuit}
                onChange={(e) => setCreateForm({ ...createForm, cuit: e.target.value })}
                className="w-full h-9 bg-white border border-border text-brand-ink text-xs rounded-base px-3 outline-none focus:border-brand-ink"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-brand-ink mb-1">Email Cobranzas</label>
              <input
                type="email"
                placeholder="cobranzas@seliz.com.ar"
                value={createForm.email_cobranzas}
                onChange={(e) => setCreateForm({ ...createForm, email_cobranzas: e.target.value })}
                className="w-full h-9 bg-white border border-border text-brand-ink text-xs rounded-base px-3 outline-none focus:border-brand-ink"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-brand-ink mb-1">CBU Oficial</label>
              <input
                type="text"
                placeholder="0140000000000000000001"
                value={createForm.cbu_bancario}
                onChange={(e) => setCreateForm({ ...createForm, cbu_bancario: e.target.value })}
                className="w-full h-9 bg-white border border-border text-brand-ink text-xs rounded-base px-3 outline-none focus:border-brand-ink"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-brand-ink mb-1">Alias Bancario</label>
              <input
                type="text"
                placeholder="CONSORCIO.EXPENSAS"
                value={createForm.alias_bancario}
                onChange={(e) => setCreateForm({ ...createForm, alias_bancario: e.target.value })}
                className="w-full h-9 bg-white border border-border text-brand-ink text-xs rounded-base px-3 outline-none focus:border-brand-ink"
              />
            </div>
          </div>

          <div className="pt-3 border-t border-border flex items-center justify-end gap-2">
            <Button
              variant="secondary"
              size="md"
              type="button"
              onClick={() => setIsCreateModalOpen(false)}
              disabled={creating}
            >
              Cancelar
            </Button>
            <Button
              variant="primary"
              size="md"
              type="submit"
              disabled={creating}
              className="bg-brand-ink text-white font-semibold"
            >
              {creating ? 'Guardando...' : 'Crear Consorcio'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
