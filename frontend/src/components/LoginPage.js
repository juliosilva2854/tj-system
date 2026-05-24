import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI, isMasterSubdomain } from '../api';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { toast } from 'sonner';
import { ShieldCheck, Building2, Eye, EyeOff, Lock } from 'lucide-react';

export const LoginPage = () => {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const isMaster = isMasterSubdomain();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await authAPI.login({
        identifier: identifier.toLowerCase().trim(),
        password,
        is_master: isMaster
      });
      const user = response.data.user;
      
      // Validações de subdomínio
      if (isMaster && !user.is_master_access) {
        toast.error('Este domínio é exclusivo para acesso Master');
        setLoading(false);
        return;
      }
      if (!isMaster && user.is_master_access) {
        toast.error('Master deve acessar pelo domínio administrator.*');
        setLoading(false);
        return;
      }
      
      // Security: Apenas dados não-sensíveis em sessionStorage
      // Tokens vêm automaticamente em httpOnly cookies (protegido contra XSS)
      sessionStorage.setItem('user', JSON.stringify(user));
      
      toast.success(`Bem-vindo, ${user.name}!`);
      navigate('/dashboard');
    } catch (error) {
      console.error('Login failed:', error);
      toast.error(error.response?.data?.detail || 'Credenciais incorretas');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex" data-testid="login-page">
      {/* Left Side - Login Form */}
      <div className="flex-1 flex items-center justify-center px-4 sm:px-6 lg:px-8 bg-white">
        <div className="w-full max-w-md space-y-8">
          {/* Logo & Title */}
          <div>
            <div className="flex justify-center">
              <div className={`h-16 w-16 rounded-2xl ${isMaster ? 'bg-gradient-to-br from-indigo-600 to-purple-600' : 'bg-gradient-to-br from-blue-600 to-cyan-600'} flex items-center justify-center text-white font-bold text-2xl shadow-lg`}>
                TJ
              </div>
            </div>
            <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-gray-900">
              Gestão TJ
            </h2>
            <p className="mt-2 text-center text-sm text-gray-600">
              Sistema de Gestão Empresarial
            </p>
            
            {/* Subdomain Badge */}
            <div className="mt-4 flex justify-center">
              <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium ${isMaster ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' : 'bg-blue-50 text-blue-700 border border-blue-200'}`}>
                {isMaster ? (
                  <>
                    <ShieldCheck className="h-4 w-4" />
                    <span>Acesso Master Global</span>
                  </>
                ) : (
                  <>
                    <Building2 className="h-4 w-4" />
                    <span>Painel do Estabelecimento</span>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Login Form */}
          <form className="mt-8 space-y-6" onSubmit={handleLogin} data-testid="login-form">
            <div className="space-y-4">
              <div>
                <label htmlFor="identifier" className="block text-sm font-medium text-gray-700 mb-1.5">
                  {isMaster ? 'Email' : 'Usuário'}
                </label>
                <Input
                  id="identifier"
                  data-testid="login-identifier-input"
                  type="text"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  required
                  placeholder={isMaster ? 'master@sconnecta.com.br' : 'seu.usuario'}
                  className="h-11"
                  autoComplete="username"
                />
                {!isMaster && (
                  <p className="mt-1.5 text-xs text-gray-500">
                    Use seu nome de usuário para acessar
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1.5">
                  Senha
                </label>
                <div className="relative">
                  <Input
                    id="password"
                    data-testid="login-password-input"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    placeholder="••••••••"
                    className="h-11 pr-10"
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="text-sm">
                <Link
                  to="/forgot-password"
                  className="font-medium text-blue-600 hover:text-blue-500"
                >
                  Esqueceu sua senha?
                </Link>
              </div>
            </div>

            <Button
              type="submit"
              data-testid="login-submit-button"
              disabled={loading}
              className={`w-full h-11 text-white font-medium ${isMaster ? 'bg-indigo-600 hover:bg-indigo-700' : 'bg-blue-600 hover:bg-blue-700'}`}
            >
              {loading ? (
                <div className="flex items-center gap-2">
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                  <span>Entrando...</span>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Lock className="h-4 w-4" />
                  <span>Entrar no Sistema</span>
                </div>
              )}
            </Button>
          </form>

          {/* Test Credentials */}
          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200"></div>
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-white px-2 text-gray-500">Credenciais de Teste</span>
              </div>
            </div>
            
            <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200" data-testid="login-credentials-help">
              <div className="space-y-2 text-xs text-gray-600">
                {isMaster ? (
                  <div className="flex justify-between">
                    <span className="font-medium">Master:</span>
                    <span className="font-mono">master@sconnecta.com.br / Master@2026</span>
                  </div>
                ) : (
                  <>
                    <div className="flex justify-between">
                      <span className="font-medium">Admin TJ:</span>
                      <span className="font-mono">admin.tj / Admin@2026</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium">Admin Arcos:</span>
                      <span className="font-mono">admin.arcos / Admin@2026</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium">Gerente Geral:</span>
                      <span className="font-mono">geral.arcos / GerenteGeral@2026</span>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right Side - Hero Image */}
      <div className="hidden lg:flex lg:flex-1 relative bg-gradient-to-br from-blue-600 to-cyan-500 overflow-hidden">
        {/* Overlay Pattern */}
        <div className="absolute inset-0 bg-grid-white/10"></div>
        
        {/* Content */}
        <div className="relative z-10 flex flex-col justify-center px-12 text-white">
          <div className="space-y-6">
            <h1 className="text-5xl font-bold leading-tight">
              Gestão Inteligente<br />
              <span className="text-blue-200">para seu Negócio</span>
            </h1>
            <p className="text-xl text-blue-50 max-w-md">
              Controle completo de estoque, transferências entre lojas, relatórios em tempo real e muito mais.
            </p>
            <div className="space-y-4 pt-4">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 h-6 w-6 rounded-full bg-white/20 flex items-center justify-center">
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold">Multi-tenant SaaS</h3>
                  <p className="text-sm text-blue-100">Gerencie múltiplos estabelecimentos</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 h-6 w-6 rounded-full bg-white/20 flex items-center justify-center">
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold">Controle Hierárquico</h3>
                  <p className="text-sm text-blue-100">Permissões customizáveis por usuário</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 h-6 w-6 rounded-full bg-white/20 flex items-center justify-center">
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold">Relatórios Avançados</h3>
                  <p className="text-sm text-blue-100">DRE, Curva ABC, Giro de Estoque</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Decorative Image */}
        <div className="absolute inset-0 opacity-10">
          <img
            src="https://images.unsplash.com/photo-1600132806370-bf17e65e942f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA2MTJ8MHwxfHNlYXJjaHwxfHxidXNpbmVzcyUyMHRlY2hub2xvZ3klMjBkYXNoYm9hcmR8ZW58MHx8fGJsdWV8MTc3OTY0MDA4M3ww&ixlib=rb-4.1.0&q=85"
            alt="Dashboard"
            className="object-cover w-full h-full"
          />
        </div>
      </div>
    </div>
  );
};
