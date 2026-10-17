import React, { useState, useRef, useEffect } from 'react';
import {
  SendHorizontal,
  Paperclip,
  ChevronLeft,
  Lock,
  Globe,
  Bot,
  UserCheck,
  CheckCircle2,
  Clock,
  Sparkles,
  Loader2,
  ChevronDown,
  User,
  X,
  FileText,
} from 'lucide-react';
import { WhatsAppDoodleBackground } from './WhatsAppDoodleBackground.jsx';

export function MessageThread({
  conversationId,
  senderName,
  phone,
  consorcio,
  unidad,
  avatarUrl,
  status = 'open',
  botActive = true,
  messages = [],
  onSendMessage,
  onUpdateStatus,
  onGenerateAiDraft,
  generatingDraft = false,
  onBack,
  onClose,
}) {
  const [inputText, setInputText] = useState('');
  const [isPrivateNote, setIsPrivateNote] = useState(false);
  const [statusDropdownOpen, setStatusDropdownOpen] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [aiNotice, setAiNotice] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const fileInputRef = useRef(null);
  const statusDropdownRef = useRef(null);

  // Auto-scroll al final con cada mensaje nuevo
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, selectedFile]);

  // Cerrar el menú desplegable al hacer clic fuera o presionar Escape
  useEffect(() => {
    if (!statusDropdownOpen) return;

    const handleClickOutside = (event) => {
      if (statusDropdownRef.current && !statusDropdownRef.current.contains(event.target)) {
        setStatusDropdownOpen(false);
      }
    };

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        setStatusDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [statusDropdownOpen]);

  // Manejo de selección de archivo nativo
  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Límite de 15MB
    if (file.size > 15 * 1024 * 1024) {
      alert('El archivo supera el límite de 15MB.');
      e.target.value = '';
      return;
    }

    const isImage = file.type.startsWith('image/');
    const previewUrl = URL.createObjectURL(file);

    setSelectedFile({
      file,
      name: file.name,
      size: (file.size / 1024).toFixed(1) + ' KB',
      type: file.type,
      isImage,
      previewUrl,
    });

    e.target.value = '';
  };

  const handleRemoveFile = () => {
    if (selectedFile?.previewUrl) {
      URL.revokeObjectURL(selectedFile.previewUrl);
    }
    setSelectedFile(null);
  };

  const handleAiSuggestion = async () => {
    if (!onGenerateAiDraft || generatingDraft) return;
    const suggestionText = await onGenerateAiDraft();
    if (suggestionText) {
      setInputText(suggestionText);
      setAiNotice(true);
      setTimeout(() => {
        inputRef.current?.focus();
      }, 50);
    }
  };

  const handleSend = (e) => {
    e.preventDefault();
    if (!inputText.trim() && !selectedFile) return;
    onSendMessage(inputText.trim(), isPrivateNote, selectedFile);
    setInputText('');
    handleRemoveFile();
    setAiNotice(false);
  };

  const handleStatusSelect = (newStatus) => {
    if (onUpdateStatus) {
      onUpdateStatus(newStatus);
    }
    setStatusDropdownOpen(false);
  };

  const handleCloseConversation = () => {
    if (onClose) {
      onClose();
    } else if (onBack) {
      onBack();
    }
  };

  const statusLabels = {
    open: 'Abierto',
    pending: 'Pendiente',
    resolved: 'Resuelto',
    emergency: 'Emergencia',
  };

  return (
    <div className="h-full flex flex-col bg-surface-soft min-w-0 relative">
      {/* Cabecera del Hilo Monocromática y Limpia */}
      <div className="h-14 sm:h-15 px-3 sm:px-4 border-b border-border/80 flex items-center justify-between bg-white shrink-0 min-w-0 relative z-20 shadow-xs">
        <div className="flex items-center gap-2 sm:gap-2.5 min-w-0">
          {/* Botón Volver en Móvil */}
          <button
            type="button"
            onClick={handleCloseConversation}
            aria-label="Volver a la bandeja"
            title="Volver a la bandeja"
            className="md:hidden grid size-10 place-items-center rounded-xl border border-border/80 bg-white text-brand-ink hover:bg-surface-muted transition-colors shrink-0 cursor-pointer shadow-2xs"
          >
            <ChevronLeft size={20} strokeWidth={2} />
          </button>

          {/* Botón Cerrar Conversación en Desktop */}
          <button
            type="button"
            onClick={handleCloseConversation}
            aria-label="Cerrar conversación activa"
            title="Cerrar conversación activa"
            className="hidden md:grid size-10 sm:size-11 place-items-center rounded-xl border border-border/80 bg-white text-text-secondary hover:text-brand-ink hover:bg-surface-muted transition-colors shrink-0 cursor-pointer shadow-2xs"
          >
            <X size={18} strokeWidth={2} />
          </button>

          {/* Avatar con prioridad a la imagen original de Evolution API */}
          <div className="size-10 sm:size-11 rounded-full bg-brand-ink text-white flex items-center justify-center text-xs sm:text-sm font-bold shadow-2xs shrink-0 relative overflow-hidden border border-border/60">
            {avatarUrl && !imageError ? (
              <img
                src={avatarUrl}
                alt={senderName || 'Contacto'}
                onError={() => setImageError(true)}
                className="size-full object-cover rounded-full"
                loading="lazy"
              />
            ) : senderName ? (
              <span>{senderName.charAt(0).toUpperCase()}</span>
            ) : (
              <User size={20} strokeWidth={1.8} />
            )}
          </div>

          <div className="min-w-0">
            <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
              <span className="text-xs sm:text-sm font-bold text-brand-ink truncate">
                {senderName || 'Vecino'}
              </span>
              {phone && (
                <span className="text-[11px] sm:text-xs text-text-muted truncate font-normal">
                  {phone}
                </span>
              )}
            </div>
            <div className="flex items-center gap-1.5 text-[11px] sm:text-xs text-text-secondary mt-0.5 truncate">
              <span className="truncate">{consorcio || 'Consorcio General'}</span>
              <span>•</span>
              <span className="font-medium text-brand-ink shrink-0">
                {unidad || 'Unidad S/E'}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
          {/* Indicador de Atención Personalizada (Humano) */}
          {!botActive && (
            <div
              title="El bot automático está pausado. Atención humana personalizada activa."
              className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-surface-muted border border-border/80 text-brand-ink text-xs font-semibold shadow-2xs"
            >
              <UserCheck size={16} strokeWidth={1.8} />
              <span>Humano</span>
            </div>
          )}

          {/* Selector de Estado Monocromático */}
          <div ref={statusDropdownRef} className="relative">
            <button
              type="button"
              onClick={() => setStatusDropdownOpen((prev) => !prev)}
              aria-expanded={statusDropdownOpen}
              aria-haspopup="menu"
              aria-label={`Estado actual: ${statusLabels[status] || status}. Cambiar estado`}
              title={`Estado: ${statusLabels[status] || status}`}
              className="h-10 sm:h-11 px-3.5 sm:px-4 rounded-xl border border-border/80 bg-white text-brand-ink text-xs sm:text-sm font-semibold flex items-center gap-2 hover:bg-surface-muted cursor-pointer transition-colors shadow-2xs"
            >
              <span className="capitalize">{statusLabels[status] || status}</span>
              <ChevronDown size={14} strokeWidth={2} className={`text-text-muted transition-transform duration-150 ${statusDropdownOpen ? 'rotate-180' : ''}`} />
            </button>

            {statusDropdownOpen && (
              <div className="absolute right-0 mt-1.5 w-36 bg-white border border-border rounded-xl shadow-lg z-50 py-1 text-xs divide-y divide-border/60 overflow-hidden animate-in fade-in zoom-in-95 duration-100">
                <button
                  type="button"
                  onClick={() => handleStatusSelect('open')}
                  className="w-full text-left px-3 py-2 hover:bg-surface-soft flex items-center justify-between text-brand-ink font-medium cursor-pointer transition-colors"
                >
                  <span>Abierto</span>
                  {status === 'open' && <CheckCircle2 size={16} strokeWidth={2} className="text-brand-ink" />}
                </button>
                <button
                  type="button"
                  onClick={() => handleStatusSelect('pending')}
                  className="w-full text-left px-3 py-2 hover:bg-surface-soft flex items-center justify-between text-brand-ink font-medium cursor-pointer transition-colors"
                >
                  <span>Pendiente</span>
                  {status === 'pending' && <CheckCircle2 size={16} strokeWidth={2} className="text-brand-ink" />}
                </button>
                <button
                  type="button"
                  onClick={() => handleStatusSelect('resolved')}
                  className="w-full text-left px-3 py-2 hover:bg-surface-soft flex items-center justify-between text-brand-ink font-medium cursor-pointer transition-colors"
                >
                  <span>Resuelto</span>
                  {status === 'resolved' && <CheckCircle2 size={16} strokeWidth={2} className="text-brand-ink" />}
                </button>
              </div>
            )}
          </div>

          {/* Botón Sugerencia con IA: Icono concéntrico Phosphor que gira sobre su propio centro */}
          {onGenerateAiDraft && (
            <button
              type="button"
              onClick={handleAiSuggestion}
              disabled={generatingDraft}
              aria-label={generatingDraft ? 'Generando propuesta con IA...' : 'Sugerencia con IA'}
              title="Sugerencia con IA (Insertar respuesta sugerida)"
              className="size-10 sm:size-11 rounded-xl border border-border/80 bg-white text-brand-ink hover:border-brand-ink hover:bg-surface-muted transition-all flex items-center justify-center cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed shadow-2xs group relative"
            >
              {generatingDraft ? (
                <Loader2 size={20} strokeWidth={2} className="animate-spin text-brand-ink shrink-0" />
              ) : (
                <Sparkles size={20} strokeWidth={1.8} className="text-brand-ink group-hover:scale-110 transition-transform shrink-0" />
              )}
            </button>
          )}
        </div>
      </div>

      {/* Contenedor de Mensajes con Wallpaper WhatsApp Fijo y Continuo */}
      <div className="flex-1 relative isolate overflow-hidden bg-[#efeae2] min-h-0 z-0">
        <WhatsAppDoodleBackground />

        <div className="absolute inset-0 overflow-y-auto p-3 sm:p-4 space-y-2">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-xs text-text-muted relative z-10">
              <p className="bg-white/95 px-3 py-1.5 rounded-full border border-border/80 shadow-2xs">
                No hay mensajes registrados en este hilo de conversación.
              </p>
            </div>
          ) : (
            messages.map((m) => {
              // 1. Nota interna (Privada para administración)
              if (m.privado || m.isPrivateNote) {
                return (
                  <div key={m.id} className="flex justify-center my-2 relative z-10">
                    <div className="w-fit max-w-[90%] sm:max-w-[560px] bg-amber-50/95 border border-amber-200/90 rounded-xl px-3.5 py-2.5 text-amber-950 shadow-xs">
                      <div className="flex items-center justify-between gap-3 text-[10px] sm:text-[11px] font-bold text-amber-900 mb-1">
                        <div className="flex items-center gap-1.5">
                          <Lock size={13} strokeWidth={2} className="shrink-0" />
                          <span>Nota Interna (Confidencial)</span>
                        </div>
                        <span className="text-amber-800/80 font-normal shrink-0">{m.timestamp || m.creado_el}</span>
                      </div>
                      {m.attachment && (
                        <div className="mb-2">
                          {m.attachment.isImage && m.attachment.previewUrl ? (
                            <img
                              src={m.attachment.previewUrl}
                              alt={m.attachment.name || 'Adjunto'}
                              className="max-w-full rounded-lg object-cover max-h-60 border border-amber-300"
                            />
                          ) : (
                            <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-amber-100/60 border border-amber-300/80 text-xs">
                              <FileText size={18} strokeWidth={1.8} className="shrink-0 text-amber-900" />
                              <span className="truncate font-semibold">{m.attachment.name}</span>
                              {m.attachment.size && (
                                <span className="text-[10px] text-amber-800/70 shrink-0">{m.attachment.size}</span>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                      <p className="text-xs sm:text-[13px] whitespace-pre-line leading-relaxed text-amber-950 font-medium break-words">
                        {m.text || m.contenido}
                      </p>
                    </div>
                  </div>
                );
              }

              // 2. Mensaje de actividad / sistema
              if (m.tipo === 'activity' || m.isStatusNote) {
                return (
                  <div key={m.id} className="flex justify-center my-2 relative z-10">
                    <span className="bg-white/95 text-text-secondary text-[10px] sm:text-[11px] font-medium px-3 py-1 rounded-full border border-border/80 shadow-2xs">
                      {m.text || m.contenido}
                    </span>
                  </div>
                );
              }

              // 3. Mensaje saliente (Administración / Seliz Bot)
              const isOutgoing =
                m.sender === 'ivana' ||
                m.sender === 'bot' ||
                m.sender === 'admin' ||
                m.remitente === 'BOT' ||
                m.remitente === 'HUMANO';

              if (isOutgoing) {
                return (
                  <div key={m.id} className="flex justify-end my-1 relative z-10">
                    <div className="w-fit max-w-[85%] sm:max-w-[520px] bg-brand-ink text-white rounded-2xl rounded-tr-xs px-3.5 py-2.5 shadow-xs border border-brand-ink break-words">
                      <div className="flex items-center justify-between gap-3 text-[10px] sm:text-[11px] font-medium text-zinc-300 mb-0.5">
                        <div className="flex items-center gap-1.5">
                          {m.sender === 'bot' || m.remitente === 'BOT' ? (
                            <>
                              <Bot size={14} strokeWidth={2} className="shrink-0 text-zinc-300" />
                              <span>Seliz Bot</span>
                            </>
                          ) : (
                            <span>Dra. Ivana Seliz</span>
                          )}
                        </div>
                        <span className="text-zinc-400 font-normal shrink-0">{m.timestamp || m.creado_el}</span>
                      </div>

                      {/* Renderizado de Archivo Adjunto */}
                      {m.attachment && (
                        <div className="mb-2 mt-1">
                          {m.attachment.isImage && m.attachment.previewUrl ? (
                            <img
                              src={m.attachment.previewUrl}
                              alt={m.attachment.name || 'Adjunto'}
                              className="max-w-full rounded-lg object-cover max-h-60 border border-zinc-700"
                            />
                          ) : (
                            <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-zinc-800/80 border border-zinc-700 text-xs">
                              <FileText size={18} strokeWidth={1.8} className="shrink-0 text-zinc-200" />
                              <span className="truncate font-medium">{m.attachment.name}</span>
                              {m.attachment.size && (
                                <span className="text-[10px] text-zinc-400 shrink-0">{m.attachment.size}</span>
                              )}
                            </div>
                          )}
                        </div>
                      )}

                      <p className="text-xs sm:text-[13px] whitespace-pre-line leading-relaxed text-zinc-100 break-words font-normal">
                        {m.text || m.contenido}
                      </p>
                    </div>
                  </div>
                );
              }

              // 4. Mensaje entrante (Vecino / Propietario / Inquilino)
              return (
                <div key={m.id} className="flex items-start gap-2 my-1 relative z-10 w-fit max-w-[85%] sm:max-w-[520px]">
                  <div className="size-6 sm:size-7 rounded-full bg-brand-ink text-white font-bold flex items-center justify-center text-[10px] sm:text-xs shrink-0 mt-0.5 shadow-2xs">
                    {senderName ? senderName.charAt(0).toUpperCase() : 'V'}
                  </div>
                  <div className="bg-white border border-border/80 rounded-2xl rounded-tl-xs px-3.5 py-2.5 text-brand-ink shadow-xs break-words w-full">
                    <div className="flex items-center justify-between gap-3 text-[10px] sm:text-[11px] font-bold text-brand-ink mb-0.5">
                      <span className="truncate">{senderName || 'Vecino'}</span>
                      <span className="text-text-muted font-normal text-[10px] shrink-0">{m.timestamp || m.creado_el}</span>
                    </div>

                    {/* Renderizado de Archivo Adjunto */}
                    {m.attachment && (
                      <div className="mb-2 mt-1">
                        {m.attachment.isImage && m.attachment.previewUrl ? (
                          <img
                            src={m.attachment.previewUrl}
                            alt={m.attachment.name || 'Adjunto'}
                            className="max-w-full rounded-lg object-cover max-h-60 border border-border"
                          />
                        ) : (
                          <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-surface-soft border border-border/80 text-xs text-brand-ink">
                            <FileText size={18} strokeWidth={1.8} className="shrink-0 text-brand-ink" />
                            <span className="truncate font-semibold">{m.attachment.name}</span>
                            {m.attachment.size && (
                              <span className="text-[10px] text-text-muted shrink-0">{m.attachment.size}</span>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    <p className="text-xs sm:text-[13px] whitespace-pre-line leading-relaxed text-brand-ink break-words font-normal">
                      {m.text || m.contenido}
                    </p>
                  </div>
                </div>
              );
            })
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Barra de Entrada Monocromática e Íconos Sin Texto Innecesario */}
      <div className="p-2.5 sm:p-3 bg-white border-t border-border/80 shrink-0 z-10 shadow-xs">
        {/* Selector de Modo: Iconos Monocromáticos con tooltips claros */}
        <div className="inline-flex p-0.5 rounded-lg bg-surface-muted border border-border/60 mb-2 gap-0.5">
          <button
            type="button"
            onClick={() => setIsPrivateNote(false)}
            title="Respuesta oficial por WhatsApp al vecino"
            aria-label="Respuesta WhatsApp"
            className={`p-1.5 sm:px-2 rounded-md transition-all flex items-center justify-center cursor-pointer shadow-2xs ${
              !isPrivateNote
                ? 'bg-white text-brand-ink shadow-2xs font-bold'
                : 'text-text-secondary hover:text-brand-ink'
            }`}
          >
            <Globe size={15} />
          </button>

          <button
            type="button"
            onClick={() => setIsPrivateNote(true)}
            title="Nota interna confidencial (solo visible para administración)"
            aria-label="Nota Interna Privada"
            className={`p-1.5 sm:px-2 rounded-md transition-all flex items-center justify-center cursor-pointer shadow-2xs ${
              isPrivateNote
                ? 'bg-white text-brand-ink shadow-2xs font-bold'
                : 'text-text-secondary hover:text-brand-ink'
            }`}
          >
            <Lock size={18} strokeWidth={isPrivateNote ? 2 : 1.75} />
          </button>
        </div>

        {/* Aclaración sutil de Sugerencia con IA insertada */}
        {aiNotice && (
          <div className="flex items-center justify-between gap-2 px-2.5 py-1.5 mb-2 rounded-lg bg-surface-muted border border-border/80 text-[11px] text-text-secondary animate-in fade-in duration-150">
            <div className="flex items-center gap-1.5 truncate">
              <Sparkles size={14} strokeWidth={2} className="text-brand-ink shrink-0" />
              <span className="truncate">Sugerencia con IA insertada. Puedes editarla antes de enviar.</span>
            </div>
            <button
              type="button"
              onClick={() => {
                setInputText('');
                setAiNotice(false);
              }}
              title="Limpiar sugerencia"
              aria-label="Limpiar sugerencia"
              className="p-1 rounded text-text-muted hover:text-brand-ink hover:bg-surface-soft transition-colors cursor-pointer shrink-0"
            >
              <X size={14} strokeWidth={2} />
            </button>
          </div>
        )}

        {/* Archivo adjunto seleccionado para despachar */}
        {selectedFile && (
          <div className="flex items-center justify-between gap-2 px-3 py-1.5 mb-2 rounded-lg bg-surface-soft border border-border text-xs text-brand-ink animate-in fade-in duration-150">
            <div className="flex items-center gap-2 truncate">
              {selectedFile.isImage ? (
                <img
                  src={selectedFile.previewUrl}
                  alt={selectedFile.name}
                  className="size-8 rounded object-cover border border-border/80 shrink-0"
                />
              ) : (
                <FileText size={18} strokeWidth={1.8} className="text-brand-ink shrink-0" />
              )}
              <div className="truncate">
                <span className="font-semibold truncate block max-w-[200px] sm:max-w-[340px]">
                  {selectedFile.name}
                </span>
                <span className="text-[10px] text-text-muted">{selectedFile.size}</span>
              </div>
            </div>
            <button
              type="button"
              onClick={handleRemoveFile}
              aria-label="Quitar archivo adjunto"
              title="Quitar archivo adjunto"
              className="p-1 text-text-muted hover:text-brand-ink rounded cursor-pointer transition-colors"
            >
              <X size={14} strokeWidth={2} />
            </button>
          </div>
        )}

        {/* Formulario de Entrada con Botones de Iconos Puros */}
        <form onSubmit={handleSend} className="flex items-center gap-2 min-w-0">
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileSelect}
            className="hidden"
            accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.txt"
          />

          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            aria-label="Adjuntar archivo o comprobante"
            title="Adjuntar archivo o comprobante"
            className="grid size-10 sm:size-11 place-items-center rounded-xl border border-border/80 text-text-secondary hover:bg-surface-muted hover:text-brand-ink transition-colors cursor-pointer shrink-0 shadow-2xs"
          >
            <Paperclip size={20} strokeWidth={1.8} />
          </button>

          <input
            ref={inputRef}
            type="text"
            placeholder={
              isPrivateNote
                ? 'Escribir nota interna privada...'
                : 'Escribir mensaje oficial para despachar por WhatsApp...'
            }
            value={inputText}
            onChange={(e) => {
              setInputText(e.target.value);
              if (aiNotice) setAiNotice(false);
            }}
            className={`flex-1 min-w-0 h-10 sm:h-11 border text-brand-ink text-xs sm:text-sm rounded-xl px-3.5 sm:px-4 outline-none transition-all shadow-2xs ${
              isPrivateNote
                ? 'bg-amber-50/50 border-amber-300 focus:border-amber-500 focus:ring-1 focus:ring-amber-500/30'
                : 'bg-surface-soft border-border/80 focus:bg-white focus:border-brand-ink focus:ring-1 focus:ring-brand-ink/20'
            }`}
          />

          {/* Botón Enviar: Icono monocromático puro */}
          <button
            type="submit"
            disabled={!inputText.trim() && !selectedFile}
            aria-label={isPrivateNote ? 'Guardar nota interna' : 'Enviar mensaje por WhatsApp'}
            title={isPrivateNote ? 'Guardar nota interna (Enter)' : 'Enviar mensaje (Enter)'}
            className="grid size-10 sm:size-11 place-items-center rounded-xl bg-brand-ink text-white hover:bg-black disabled:opacity-40 disabled:cursor-not-allowed shadow-2xs transition-colors shrink-0 cursor-pointer"
          >
            <SendHorizontal size={20} strokeWidth={2} />
          </button>
        </form>
      </div>
    </div>
  );
}
