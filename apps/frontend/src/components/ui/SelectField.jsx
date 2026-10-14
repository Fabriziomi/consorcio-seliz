import React, { Children, isValidElement, useEffect, useId, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { Check, ChevronDown, Loader2 } from 'lucide-react';
import { badgeVariants } from './Badge.jsx';

/**
 * Helper to extract options either from props.options or from <option> children.
 */
function parseOptions(optionsProp, children) {
  if (Array.isArray(optionsProp) && optionsProp.length > 0) {
    return optionsProp.map((opt) =>
      typeof opt === 'string'
        ? { value: opt, label: opt, disabled: false }
        : { value: String(opt.value ?? ''), label: opt.label ?? opt.value, disabled: Boolean(opt.disabled) }
    );
  }

  return Children.toArray(children)
    .filter((child) => isValidElement(child) && child.type === 'option')
    .map((child) => ({
      value: String(child.props.value ?? ''),
      label: child.props.children,
      disabled: Boolean(child.props.disabled),
    }));
}

const EDGE_OFFSET = 6;

function calculatePosition(triggerRect, dropdownRect, align, viewportWidth, viewportHeight) {
  let top = triggerRect.bottom + EDGE_OFFSET;
  let left = align === 'right' ? triggerRect.right - dropdownRect.width : triggerRect.left;

  if (left + dropdownRect.width > viewportWidth - EDGE_OFFSET) {
    left = Math.max(EDGE_OFFSET, viewportWidth - dropdownRect.width - EDGE_OFFSET);
  }
  if (left < EDGE_OFFSET) {
    left = EDGE_OFFSET;
  }

  const fitsBelow = top + dropdownRect.height <= viewportHeight - EDGE_OFFSET;
  if (!fitsBelow) {
    const above = triggerRect.top - dropdownRect.height - EDGE_OFFSET;
    if (above >= EDGE_OFFSET) {
      top = above;
    } else {
      top = Math.max(EDGE_OFFSET, Math.min(top, viewportHeight - dropdownRect.height - EDGE_OFFSET));
    }
  }

  return { top, left };
}

/**
 * Dot colors for badge dropdown options
 */
const dotColors = {
  success: 'bg-emerald-500',
  warning: 'bg-amber-500',
  danger: 'bg-rose-500',
  info: 'bg-slate-400',
  neutral: 'bg-zinc-400',
};

/**
 * SelectField / Dropdown
 * 
 * Componente modular de selección con menú flotante renderizado vía createPortal.
 * Soporta dos variantes principales:
 * - 'default': Botón/campo estándar de formulario
 * - 'badge': Chip interactivo con estilo de Badge que al hacer click abre el dropdown
 */
export function SelectField({
  className = '',
  containerClassName = '',
  popupClassName = '',
  placeholder = '',
  size = 'default', // 'xs' | 'sm' | 'default'
  align = 'left',   // 'left' | 'right'
  variant = 'default', // 'default' | 'badge'
  badgeVariant,
  badgeVariantMap,
  icon: Icon,
  loading = false,
  options: optionsProp,
  children,
  name,
  value,
  defaultValue = '',
  onChange,
  disabled = false,
  required,
  'aria-label': ariaLabel,
  ...props
}) {
  const options = parseOptions(optionsProp, children);
  const isControlled = value !== undefined;
  const [internalValue, setInternalValue] = useState(String(defaultValue));
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const [minWidth, setMinWidth] = useState(0);

  const containerRef = useRef(null);
  const triggerRef = useRef(null);
  const dropdownRef = useRef(null);
  const optionRefs = useRef([]);
  const listboxId = useId();

  const selectedValue = isControlled ? String(value ?? '') : internalValue;
  const selectedOption = options.find((o) => o.value === selectedValue) ?? options[0];
  const triggerLabel = !selectedValue && placeholder ? placeholder : selectedOption?.label;

  // Cerrar al clickear afuera
  useEffect(() => {
    if (!open) return;
    const handleOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        if (!triggerRef.current?.contains(event.target)) {
          setOpen(false);
        }
      }
    };
    document.addEventListener('pointerdown', handleOutside);
    return () => document.removeEventListener('pointerdown', handleOutside);
  }, [open]);

  // Posicionamiento dinámico respecto al viewport
  useLayoutEffect(() => {
    if (!open || !dropdownRef.current || !triggerRef.current) return;

    const updatePosition = () => {
      const triggerRect = triggerRef.current.getBoundingClientRect();
      const rect = dropdownRef.current.getBoundingClientRect();
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;
      const width = Math.min(
        Math.max(rect.width, triggerRect.width, 140),
        viewportWidth - 16
      );
      const effectiveRect = { width, height: rect.height };
      const pos = calculatePosition(triggerRect, effectiveRect, align, viewportWidth, viewportHeight);
      setPosition(pos);
      setMinWidth(width);
    };

    updatePosition();
    window.addEventListener('scroll', updatePosition, { capture: true, passive: true });
    window.addEventListener('resize', updatePosition);
    return () => {
      window.removeEventListener('scroll', updatePosition, { capture: true });
      window.removeEventListener('resize', updatePosition);
    };
  }, [open, align]);

  useEffect(() => {
    if (open && activeIndex >= 0) {
      optionRefs.current[activeIndex]?.focus();
    }
  }, [activeIndex, open]);

  const findEnabledIndex = (start, direction) => {
    if (!options.length) return -1;
    let index = start;
    for (let count = 0; count < options.length; count += 1) {
      index = (index + direction + options.length) % options.length;
      if (!options[index].disabled) return index;
    }
    return -1;
  };

  const openMenu = () => {
    if (disabled || loading) return;
    const selectedIndex = options.findIndex((o) => o.value === selectedValue && !o.disabled);
    setActiveIndex(selectedIndex >= 0 ? selectedIndex : findEnabledIndex(-1, 1));
    setOpen(true);
  };

  const selectOption = (option) => {
    if (option.disabled) return;
    if (!isControlled) setInternalValue(option.value);
    setOpen(false);
    triggerRef.current?.focus();
    onChange?.({
      target: { name, value: option.value },
      currentTarget: { name, value: option.value },
    });
  };

  const handleKeyDown = (event) => {
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      if (!open) {
        openMenu();
        return;
      }
      setActiveIndex(findEnabledIndex(activeIndex, event.key === 'ArrowDown' ? 1 : -1));
    }
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      if (!open) {
        openMenu();
      } else if (options[activeIndex]) {
        selectOption(options[activeIndex]);
      }
    }
    if (event.key === 'Escape' && open) {
      event.preventDefault();
      setOpen(false);
      triggerRef.current?.focus();
    }
  };

  const isBadge = variant === 'badge';
  const currentBadgeVariant = badgeVariant || (badgeVariantMap ? badgeVariantMap[selectedValue] : 'neutral');
  const badgeStyle = badgeVariants[currentBadgeVariant] ?? badgeVariants.neutral;

  const sizeStyles = {
    xs: isBadge
      ? 'min-h-7 h-7 text-xs px-3 py-0.5 rounded-full'
      : 'min-h-7 h-7 text-xs px-2.5 rounded-full',
    sm: 'min-h-8.5 h-8.5 text-xs px-2.5 rounded-base',
    default: 'min-h-11 w-full text-sm px-3 rounded-base',
  }[size] || 'min-h-11 w-full text-sm px-3 rounded-base';

  const defaultTheme = isBadge
    ? `${badgeStyle} font-medium tracking-tight cursor-pointer hover:opacity-85 active:opacity-75 focus-visible:ring-1 focus-visible:ring-brand-ink/40`
    : 'border border-border/80 bg-white text-brand-ink font-medium transition-[border-color,background-color,box-shadow] duration-150 hover:border-brand-ink/60 hover:bg-surface-soft focus-visible:ring-1 focus-visible:ring-brand-ink disabled:cursor-not-allowed disabled:bg-surface-muted disabled:text-text-muted shadow-subtle';

  const chevronSize = size === 'xs' ? 11 : size === 'sm' ? 13 : 15;

  const trigger = (
    <div ref={containerRef} className={`relative inline-block ${size === 'default' && !isBadge ? 'w-full' : ''} ${containerClassName}`}>
      <input type="hidden" name={name} value={selectedValue} disabled={disabled} aria-hidden="true" required={required} />
      <button
        ref={triggerRef}
        type="button"
        disabled={disabled || loading}
        className={`inline-flex items-center justify-between gap-1.5 text-left outline-none transition-all duration-150 ${sizeStyles} ${defaultTheme} ${className}`}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listboxId}
        aria-label={ariaLabel}
        onClick={(e) => {
          e.stopPropagation();
          open ? setOpen(false) : openMenu();
        }}
        onKeyDown={handleKeyDown}
        {...props}
      >
        <span className="inline-flex min-w-0 items-center gap-1.5 truncate">
          {Icon ? <Icon size={chevronSize} className="shrink-0 text-current opacity-70" aria-hidden="true" /> : null}
          <span className="truncate">
            {triggerLabel}
          </span>
        </span>
        <span className="shrink-0 opacity-60">
          {loading ? (
            <Loader2 size={chevronSize} className="animate-spin text-current" />
          ) : (
            <ChevronDown
              size={chevronSize}
              aria-hidden="true"
              className={`transition-transform duration-150 ${open ? 'rotate-180' : ''}`}
            />
          )}
        </span>
      </button>
    </div>
  );

  const dropdown = open && (
    <div
      ref={dropdownRef}
      id={listboxId}
      role="listbox"
      aria-label={ariaLabel ?? name}
      className={`fixed z-[9999] max-h-60 overflow-y-auto rounded-base border border-border/90 bg-white p-1 shadow-card ${popupClassName} min-w-[135px] max-w-[calc(100vw-16px)]`}
      style={{ top: position.top, left: position.left, minWidth: minWidth || undefined }}
      onKeyDown={handleKeyDown}
    >
      {options.map((option, index) => {
        const isSelected = option.value === selectedValue;
        const optBadgeVariant = badgeVariantMap ? badgeVariantMap[option.value] : null;
        const dotClass = optBadgeVariant ? dotColors[optBadgeVariant] : null;

        return (
          <button
            key={`${option.value}-${index}`}
            ref={(el) => {
              optionRefs.current[index] = el;
            }}
            type="button"
            role="option"
            aria-selected={isSelected}
            disabled={option.disabled}
            tabIndex={index === activeIndex ? 0 : -1}
            className={`flex w-full items-center justify-between gap-2 rounded-sm px-2.5 py-1.5 text-left text-xs transition-colors duration-150 disabled:cursor-not-allowed disabled:text-text-muted focus-visible:bg-surface-soft ${
              size === 'default' && !isBadge ? 'min-h-9 text-sm px-3' : 'min-h-7.5'
            } ${
              isSelected
                ? 'bg-surface-soft font-semibold text-brand-ink'
                : 'text-text-secondary hover:bg-surface-soft hover:text-brand-ink'
            }`}
            onClick={(e) => {
              e.stopPropagation();
              selectOption(option);
            }}
          >
            <span className="flex items-center gap-2 truncate">
              {dotClass && (
                <span className={`size-1.5 rounded-full shrink-0 ${dotClass}`} aria-hidden="true" />
              )}
              <span className="truncate">{option.label}</span>
            </span>
            {isSelected && <Check size={13} className="shrink-0 text-brand-ink" aria-hidden="true" />}
          </button>
        );
      })}
    </div>
  );

  return (
    <>
      {trigger}
      {dropdown && createPortal(dropdown, document.body)}
    </>
  );
}

// Export also as Dropdown for convenience
export const Dropdown = SelectField;
