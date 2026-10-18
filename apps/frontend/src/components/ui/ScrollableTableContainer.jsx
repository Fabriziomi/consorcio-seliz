import { useRef, useState, useCallback, useEffect } from 'react';

/**
 * ScrollableTableContainer
 *
 * Contenedor responsivo para tablas con:
 * 1. Scroll horizontal elástico con soporte de drag con el mouse (clic y arrastre).
 * 2. Indicador sutil de arrastre / scroll cuando la tabla tiene contenido oculto desbordado.
 * 3. Prevención de selección de texto y clicks accidentales al finalizar el arrastre.
 * 4. Soporte táctil nativo automático sin interferir con gestos de móviles y tablets.
 */
export function ScrollableTableContainer({
  children,
  className = '',
  containerClassName = '',
  hasOverflowHint = true,
  ...props
}) {
  const containerRef = useRef(null);
  const isDraggingRef = useRef(false);
  const startXRef = useRef(0);
  const scrollLeftRef = useRef(0);
  const movedDistanceRef = useRef(0);

  const [isGrabbing, setIsGrabbing] = useState(false);
  const [isCompressed, setIsCompressed] = useState(false);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  const checkScroll = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;
    const { scrollLeft, scrollWidth, clientWidth } = el;
    // La tabla está comprimida al interior únicamente cuando su ancho de contenido excede el ancho visible
    const compressed = scrollWidth > clientWidth + 1;
    setIsCompressed(compressed);

    // Las sombras indicadoras solo se aplican si la tabla está comprimida
    setCanScrollLeft(compressed && scrollLeft > 2);
    setCanScrollRight(compressed && scrollLeft + clientWidth < scrollWidth - 2);
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    checkScroll();

    let resizeObserver = null;
    if (typeof window !== 'undefined' && 'ResizeObserver' in window) {
      resizeObserver = new window.ResizeObserver(() => {
        checkScroll();
      });
      resizeObserver.observe(el);
      // Observar cambios de tamaño del contenido interno de la tabla
      if (el.firstElementChild) {
        resizeObserver.observe(el.firstElementChild);
      }
    }
    window.addEventListener('resize', checkScroll);

    return () => {
      if (resizeObserver) resizeObserver.disconnect();
      window.removeEventListener('resize', checkScroll);
    };
  }, [checkScroll]);

  const handleMouseDown = (e) => {
    // Si la tabla no está comprimida, no activar drag
    if (!isCompressed) return;

    // Si el clic fue en un botón, enlace, input o control interactivo, no activar drag
    if (
      e.target.closest('button') ||
      e.target.closest('a') ||
      e.target.closest('input') ||
      e.target.closest('select') ||
      e.target.closest('textarea') ||
      e.button !== 0 // Solo clic primario izquierdo
    ) {
      return;
    }

    const el = containerRef.current;
    if (!el) return;

    isDraggingRef.current = true;
    movedDistanceRef.current = 0;
    startXRef.current = e.pageX - el.offsetLeft;
    scrollLeftRef.current = el.scrollLeft;
    setIsGrabbing(true);
  };

  const handleMouseMove = (e) => {
    if (!isDraggingRef.current || !isCompressed) return;
    const el = containerRef.current;
    if (!el) return;

    e.preventDefault();
    const x = e.pageX - el.offsetLeft;
    const walk = (x - startXRef.current) * 1.5; // Factor de desplazamiento suave
    movedDistanceRef.current = Math.abs(x - startXRef.current);
    el.scrollLeft = scrollLeftRef.current - walk;
    checkScroll();
  };

  const handleMouseUpOrLeave = (e) => {
    if (!isDraggingRef.current) return;
    isDraggingRef.current = false;
    setIsGrabbing(false);

    // Si hubo arrastre significativo (>6px), prevenir click accidental
    if (movedDistanceRef.current > 6 && e.type === 'mouseup') {
      const captureClick = (clickEvent) => {
        clickEvent.stopPropagation();
        clickEvent.preventDefault();
        window.removeEventListener('click', captureClick, true);
      };
      window.addEventListener('click', captureClick, true);
    }
  };

  return (
    <div className={`relative group w-full max-w-full h-full flex flex-col min-h-0 overflow-hidden ${containerClassName}`}>
      {/* Sombra indicadora izquierda: únicamente visible si la tabla está comprimida y se desplazó */}
      {hasOverflowHint && canScrollLeft ? (
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-y-0 left-0 z-20 w-6 sm:w-8 bg-gradient-to-r from-black/10 via-black/5 to-transparent transition-opacity duration-200"
        />
      ) : null}

      {/* Sombra indicadora derecha: únicamente visible si la tabla está comprimida al interior y desborda */}
      {hasOverflowHint && canScrollRight ? (
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-y-0 right-0 z-20 w-6 sm:w-8 bg-gradient-to-l from-black/10 via-black/5 to-transparent transition-opacity duration-200"
        />
      ) : null}

      {/* Contenedor con scroll y drag */}
      <div
        ref={containerRef}
        onScroll={checkScroll}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUpOrLeave}
        onMouseLeave={handleMouseUpOrLeave}
        className={`overflow-auto flex-1 min-h-0 select-none sm:select-auto w-full max-w-full relative z-10 ${
          isGrabbing ? 'cursor-grabbing select-none' : isCompressed ? 'cursor-grab' : ''
        } ${className}`}
        style={{
          WebkitOverflowScrolling: 'touch',
          scrollbarWidth: 'thin',
          width: '100%',
          maxWidth: '100%',
        }}
        {...props}
      >
        {children}
      </div>
    </div>
  );
}
