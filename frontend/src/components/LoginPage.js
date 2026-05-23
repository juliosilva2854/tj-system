import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI, isMasterSubdomain } from '../api';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { toast } from 'sonner';
import { ShieldCheck, Building2 } from 'lucide-react';

export const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const masterMode = isMasterSubdomain();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await authAPI.login({ email, password });
      const user = response.data.user;
      if (masterMode && user.role !== 'master') {
        toast.error('Este subdominio aceita apenas o usuario Master');
        setLoading(false);
        return;
      }
      if (!masterMode && user.role === 'master') {
        toast.error('Master deve acessar pelo subdominio master.*');
        setLoading(false);
        return;
      }
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);
      localStorage.setItem('user', JSON.stringify(user));
      toast.success('Login realizado com sucesso!');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao fazer login');
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-50 px-4" data-testid="login-page">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className={`h-16 w-16 rounded-2xl ${masterMode ? 'bg-indigo-600' : 'bg-blue-600'} flex items-center justify-center text-white font-bold text-2xl mx-auto mb-4`}>TJ</div>
          <h1 className="text-3xl font-semibold font-primary text-zinc-900 tracking-tight">Gestao TJ</h1>
          <p className="mt-2 text-sm text-zinc-600">Sistema SaaS de Controle de Estoque</p>
          <div className="mt-3 inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-zinc-100 text-zinc-700" data-testid="login-subdomain-badge">
            {masterMode ? <ShieldCheck className="h-3.5 w-3.5 text-indigo-600" /> : <Building2 className="h-3.5 w-3.5 text-blue-600" />}
            {masterMode ? 'Painel Master Global' : 'Painel do Estabelecimento'}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-zinc-200 shadow-sm p-8">
          <h2 className="text-xl font-semibold text-zinc-900 mb-6">Entrar no sistema</h2>
          <form onSubmit={handleLogin} className="space-y-4" data-testid="login-form">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-zinc-700 mb-1.5">Email</label>
              <Input id="email" data-testid="login-email-input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="seu@email.com" />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-zinc-700 mb-1.5">Senha</label>
              <Input id="password" data-testid="login-password-input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required placeholder="********" />
            </div>
            <Button type="submit" data-testid="login-submit-button" disabled={loading} className={`w-full text-white ${masterMode ? 'bg-indigo-600 hover:bg-indigo-700' : 'bg-blue-600 hover:bg-blue-700'}`}>
              {loading ? 'Entrando...' : 'Entrar'}
            </Button>
          </form>
        </div>

        <div className="mt-4 p-4 bg-zinc-100 rounded-lg border border-zinc-200" data-testid="login-credentials-help">
          <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-2">Credenciais de teste</p>
          <div className="space-y-1 text-xs text-zinc-600">
            {masterMode ? (
              <p><strong>Master:</strong> master@sconnecta.com.br / Master@2026</p>
            ) : (
              <>
                <p><strong>Admin:</strong> admin@tj.sconnecta.com.br / Admin@2026</p>
                <p><strong>Logistica (PAI):</strong> logistica@tj.sconnecta.com.br / Logistica@2026</p>
                <p><strong>Operacional (FILHO):</strong> operacional@tj.sconnecta.com.br / Operacional@2026</p>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
