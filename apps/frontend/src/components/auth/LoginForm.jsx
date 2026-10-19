import React, { useState, useRef, useEffect } from 'react';
import { AlertCircle, ArrowRight, ArrowLeft, ShieldCheck, Lock } from 'lucide-react';
import { ApiService } from '../../lib/api-client.js';

export function LoginForm({ onLoginSuccess }) {
  const [step, setStep] = useState('credentials'); // 'credentials' | 'pin'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [tempToken, setTempToken] = useState(null);
  const [userNombre, setUserNombre] = useState('');

  // Estados para el PIN de 6 dígitos
  const [pinDigits, setPinDigits] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const pinInputsRef = useRef([]);

  useEffect(() => {
    if (step === 'pin' && pinInputsRef.current[0]) {
      pinInputsRef.current[0].focus();
    }
  }, [step]);

  const handleCredentialsSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Por favor completá todos los campos.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await ApiService.login(email.trim(), password);

      if (res.requires_pin) {
        setTempToken(res.temp_token);
        setUserNombre(res.user_nombre || email.trim());
        setStep('pin');
        setPinDigits(['', '', '', '', '', '']);
      } else if (res.user && onLoginSuccess) {
        onLoginSuccess(res.user);
      }
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        'No se pudo iniciar sesión. Verificá tus credenciales o el estado del servidor.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handlePinChange = (index, value) => {
    // Aceptar solo números
    const cleanValue = value.replace(/\D/g, '');

    // Soporte para pegar código completo de 6 dígitos
    if (cleanValue.length > 1) {
      const pasted = cleanValue.slice(0, 6).split('');
      const updated = [...pinDigits];
      pasted.forEach((char, i) => {
        if (i < 6) updated[i] = char;
      });
      setPinDigits(updated);
      const nextIdx = Math.min(pasted.length, 5);
      pinInputsRef.current[nextIdx]?.focus();
      return;
    }

    const updated = [...pinDigits];
    updated[index] = cleanValue;
    setPinDigits(updated);

    if (cleanValue && index < 5) {
      pinInputsRef.current[index + 1]?.focus();
    }
  };

  const handlePinKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !pinDigits[index] && index > 0) {
      pinInputsRef.current[index - 1]?.focus();
    }
  };

  const handlePinSubmit = async (e) => {
    e.preventDefault();
    const fullPin = pinDigits.join('');
    if (fullPin.length < 6) {
      setError('Por favor ingresá los 6 dígitos completos del PIN de seguridad.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const { user } = await ApiService.verifyPin(tempToken, fullPin);
      if (onLoginSuccess) {
        onLoginSuccess(user);
      }
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        'PIN de seguridad incorrecto. Verificá los dígitos e intentá nuevamente.';
      setError(msg);
      setPinDigits(['', '', '', '', '', '']);
      pinInputsRef.current[0]?.focus();
    } finally {
      setLoading(false);
    }
  };

  const handleBackToCredentials = () => {
    setStep('credentials');
    setTempToken(null);
    setError(null);
    setPinDigits(['', '', '', '', '', '']);
  };

  return (
    <div className="min-h-[100dvh] bg-surface-soft flex flex-col justify-center items-center px-4 py-8 sm:px-6">
      <div className="w-full max-w-sm space-y-7">
        {/* Título Principal Limpio */}
        <div className="text-center">
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-brand-ink">
            Dra. Ivana Seliz
          </h1>
          <p className="mt-1 text-xs text-text-muted uppercase tracking-wider font-medium">
            Administración de Consorcios
          </p>
        </div>

        {/* Tarjeta de Formulario con Segundo Factor */}
        <div className="bg-white rounded-2xl border border-border/80 shadow-card p-6 sm:p-8 space-y-6">
          {error && (
            <div className="flex items-start gap-2.5 p-3.5 rounded-lg bg-danger-soft border border-danger/30 text-danger text-xs sm:text-sm leading-relaxed animate-in fade-in duration-200">
              <AlertCircle className="size-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {step === 'credentials' ? (
            <form onSubmit={handleCredentialsSubmit} className="space-y-5">
              <div className="space-y-2">
                <label className="block text-sm font-semibold text-brand-ink">
                  Correo electrónico
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="nombre@ejemplo.com"
                  required
                  autoFocus
                  className="w-full h-12 px-4 text-sm sm:text-base rounded-lg border border-border bg-white text-brand-ink placeholder:text-text-muted focus:outline-none focus:border-brand-ink focus:ring-2 focus:ring-brand-ink/10 transition-all"
                />
              </div>

              <div className="space-y-2">
                <label className="block text-sm font-semibold text-brand-ink">
                  Contraseña
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  required
                  className="w-full h-12 px-4 text-sm sm:text-base rounded-lg border border-border bg-white text-brand-ink placeholder:text-text-muted focus:outline-none focus:border-brand-ink focus:ring-2 focus:ring-brand-ink/10 transition-all"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full h-12 mt-2 flex items-center justify-center gap-2 rounded-lg bg-brand-ink hover:bg-black text-white text-sm sm:text-base font-semibold transition-all disabled:opacity-50 cursor-pointer shadow-subtle"
              >
                {loading ? (
                  <>
                    <div className="size-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Verificando credenciales...</span>
                  </>
                ) : (
                  <>
                    <span>Continuar</span>
                    <ArrowRight className="size-4" />
                  </>
                )}
              </button>
            </form>
          ) : (
            <form onSubmit={handlePinSubmit} className="space-y-5">
              <div className="text-center space-y-1.5 pb-1">
                <div className="inline-flex items-center justify-center size-10 rounded-full bg-brand-ink/5 border border-brand-ink/10 text-brand-ink mb-1">
                  <ShieldCheck className="size-5" />
                </div>
                <h2 className="text-base font-bold text-brand-ink">
                  Verificación de Seguridad
                </h2>
                <p className="text-xs text-text-muted leading-relaxed">
                  Ingresá el PIN de seguridad de 6 dígitos asignado para confirmar el acceso a la cuenta de {userNombre}.
                </p>
              </div>

              {/* Cajas de dígitos del PIN */}
              <div className="flex justify-between gap-1.5 sm:gap-2">
                {pinDigits.map((digit, idx) => (
                  <input
                    key={idx}
                    ref={(el) => (pinInputsRef.current[idx] = el)}
                    type="password"
                    inputMode="numeric"
                    maxLength={6}
                    value={digit}
                    onChange={(e) => handlePinChange(idx, e.target.value)}
                    onKeyDown={(e) => handlePinKeyDown(idx, e)}
                    className="w-11 h-13 sm:w-12 sm:h-14 text-center text-lg sm:text-xl font-bold rounded-lg border border-border bg-white text-brand-ink focus:outline-none focus:border-brand-ink focus:ring-2 focus:ring-brand-ink/15 transition-all"
                  />
                ))}
              </div>

              <button
                type="submit"
                disabled={loading || pinDigits.join('').length < 6}
                className="w-full h-12 mt-2 flex items-center justify-center gap-2 rounded-lg bg-brand-ink hover:bg-black text-white text-sm sm:text-base font-semibold transition-all disabled:opacity-50 cursor-pointer shadow-subtle"
              >
                {loading ? (
                  <>
                    <div className="size-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Validando PIN...</span>
                  </>
                ) : (
                  <>
                    <span>Ingresar al Sistema</span>
                    <ArrowRight className="size-4" />
                  </>
                )}
              </button>

              <div className="pt-1 text-center">
                <button
                  type="button"
                  onClick={handleBackToCredentials}
                  className="inline-flex items-center gap-1.5 text-xs text-text-muted hover:text-brand-ink transition-colors cursor-pointer"
                >
                  <ArrowLeft className="size-3.5" />
                  <span>Volver a ingresar credenciales</span>
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
