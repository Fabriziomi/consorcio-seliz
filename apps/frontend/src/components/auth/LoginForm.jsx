import React, { useState } from 'react';
import { AlertCircle, ArrowRight } from 'lucide-react';
import { ApiService } from '../../lib/api-client.js';

export function LoginForm({ onLoginSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Por favor completá todos los campos.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const { user } = await ApiService.login(email.trim(), password);
      if (onLoginSuccess) {
        onLoginSuccess(user);
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

  const handleFillDemo = () => {
    setEmail('admin@selizadministraciones.com.ar');
    setPassword('AdminSeliz2026!');
    setError(null);
  };

  return (
    <div className="min-h-[100dvh] bg-surface-soft flex flex-col justify-center items-center px-4 py-8 sm:px-6">
      <div className="w-full max-w-sm space-y-7">
        {/* Título Principal Limpio */}
        <div className="text-center">
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-brand-ink">
            Dra. Ivana Seliz
          </h1>
        </div>

        {/* Tarjeta de Formulario Minimalista */}
        <div className="bg-white rounded-2xl border border-border/80 shadow-card p-6 sm:p-8 space-y-6">
          {error && (
            <div className="flex items-start gap-2.5 p-3.5 rounded-lg bg-danger-soft border border-danger/30 text-danger text-xs sm:text-sm leading-relaxed animate-in fade-in duration-200">
              <AlertCircle className="size-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
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
                  <span>Verificando...</span>
                </>
              ) : (
                <>
                  <span>Ingresar</span>
                  <ArrowRight className="size-4" />
                </>
              )}
            </button>
          </form>

          {/* Atajo sutil */}
          <div className="pt-2 text-center">
            <button
              type="button"
              onClick={handleFillDemo}
              className="text-xs text-text-muted hover:text-brand-ink transition-colors cursor-pointer"
            >
              Completar credenciales de prueba
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
