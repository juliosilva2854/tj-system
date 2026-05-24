import React, { useState, useEffect, useCallback } from 'react';
import { Outlet, useNavigate, useLocation, Link } from 'react-router-dom';
import { authAPI, notificationsAPI } from '../api';
import { Home, Package, Warehouse, Users, FileText, TrendingUp, LogOut, ClipboardList, UserCircle, BarChart3, Bell, Menu, X, HelpCircle, Building2, ArrowLeftRight, ShieldCheck, Store, Settings, Boxes } from 'lucide-react';

const ROLE_LABEL = {
  master: 'Master Global',
  admin: 'Administrador',
  gerente_geral: 'Gerente Geral',
  gerente_logistica: 'Gerente Logistica',
  gerente_operacional: 'Gerente Operacional',
  logistica: 'Logistica (PAI)',
  operacional: 'Operacional (FILHO)',
};

// Grupos de role para uso nos menus
const ALL_NON_MASTER = ['admin', 'gerente_geral', 'gerente_logistica', 'gerente_operacional', 'logistica', 'operacional'];
const ADMIN_LIKE = ['master', 'admin', 'gerente_geral'];
const ADMIN_LOG_LIKE = ['master', 'admin', 'gerente_geral', 'gerente_logistica', 'logistica'];
const OPS_LIKE = ['master', 'admin', 'gerente_geral', 'gerente_logistica', 'gerente_operacional', 'logistica', 'operacional'];
const APPROVERS = ['master', 'admin', 'gerente_geral', 'gerente_logistica', 'logistica'];

export const DashboardLayout = () => {
  const [user, setUser] = useState(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const fetchUnread = useCallback(async () => {
    try { const r = await notificationsAPI.getUnreadCount(); setUnreadCount(r.data.count); } catch {}
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) { navigate('/login'); return; }
    authAPI.me().then(r => {
      setUser(r.data);
      localStorage.setItem('user', JSON.stringify(r.data));
    }).catch(() => {
      const ud = localStorage.getItem('user');
      if (ud) setUser(JSON.parse(ud));
      else navigate('/login');
    });
    fetchUnread();
    const iv = setInterval(fetchUnread, 30000);
    return () => clearInterval(iv);
  }, [navigate, fetchUnread]);

  useEffect(() => { setSidebarOpen(false); }, [location.pathname]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  // Cada item tem (1) roles permitidos e (2) module key (opcional) — se houver, item so aparece se modulo estiver habilitado
  const menuItems = [
    { icon: Home, label: 'Dashboard', path: '/dashboard', roles: ['master', ...ALL_NON_MASTER], module: 'dashboard' },
    { icon: Building2, label: 'Estabelecimentos', path: '/dashboard/tenants', roles: ['master'] },
    { icon: Settings, label: 'Modulos', path: '/dashboard/modules', roles: ['master', 'admin'], module: 'modules' },
    { icon: Store, label: 'Lojas', path: '/dashboard/stores', roles: ['master', 'admin', 'gerente_geral', 'gerente_logistica', 'gerente_operacional'], module: 'stores' },
    { icon: Warehouse, label: 'Depositos', path: '/dashboard/warehouses', roles: ADMIN_LOG_LIKE, module: 'warehouses' },
    { icon: Package, label: 'Produtos', path: '/dashboard/products', roles: ADMIN_LOG_LIKE, module: 'products' },
    { icon: ClipboardList, label: 'Estoque', path: '/dashboard/inventory', roles: OPS_LIKE, module: 'inventory' },
    { icon: ArrowLeftRight, label: 'Requisicoes', path: '/dashboard/requisitions', roles: OPS_LIKE, module: 'requisitions' },
    { icon: Boxes, label: 'Transferencias', path: '/dashboard/transfers', roles: ADMIN_LIKE, module: 'transfers' },
    { icon: UserCircle, label: 'Fornecedores', path: '/dashboard/suppliers', roles: ADMIN_LOG_LIKE, module: 'suppliers' },
    { icon: FileText, label: 'Notas Fiscais', path: '/dashboard/invoices', roles: ADMIN_LOG_LIKE, module: 'invoices' },
    { icon: BarChart3, label: 'Relatorios', path: '/dashboard/reports', roles: ADMIN_LIKE, module: 'reports' },
    { icon: Bell, label: 'Alertas', path: '/dashboard/alerts', roles: OPS_LIKE, module: 'alerts' },
    { icon: TrendingUp, label: 'Auditoria', path: '/dashboard/audit', roles: ['master', 'admin', 'gerente_geral', 'gerente_logistica', 'gerente_operacional', 'logistica', 'operacional'], module: 'audit' },
    { icon: Users, label: 'Usuarios', path: '/dashboard/users', roles: ['master', 'admin'], module: 'users' },
    { icon: HelpCircle, label: 'Guia', path: '/dashboard/guide', roles: ['master', ...ALL_NON_MASTER], module: 'guide' },
  ];

  if (!user) return null;
  const enabled = user.enabled_modules || [];
  const isMasterOrAdmin = ['master', 'admin'].includes(user.role);
  const filteredMenu = menuItems.filter(i =>
    i.roles.includes(user.role) &&
    (isMasterOrAdmin || !i.module || enabled.includes(i.module))
  );
  const isActive = (p) => location.pathname === p || (p !== '/dashboard' && location.pathname.startsWith(p));
  const accentBg = user.role === 'master' ? 'bg-indigo-600' : 'bg-blue-600';
  const accentText = user.role === 'master' ? 'text-indigo-600' : 'text-blue-600';
  const accentBgSoft = user.role === 'master' ? 'bg-indigo-50' : 'bg-blue-50';

  const scopeLabel = () => {
    if (user.role === 'master') return null;
    if (user.warehouse_name) return user.warehouse_name;
    const stores = user.store_names || [];
    if (stores.length > 0) return stores.join(' + ');
    return null;
  };
  const scope = scopeLabel();

  return (
    <div className="flex h-screen bg-zinc-50" data-testid="dashboard-layout">
      {sidebarOpen && <div className="fixed inset-0 bg-black/40 z-40 lg:hidden" onClick={() => setSidebarOpen(false)} />}
      <div className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-white border-r border-zinc-200 flex flex-col transform transition-transform duration-200 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
        <div className="h-14 flex items-center justify-between px-4 border-b border-zinc-200">
          <div className="flex items-center gap-2">
            <div className={`h-7 w-7 rounded ${accentBg} flex items-center justify-center text-white font-bold text-sm`}>TJ</div>
            <span className="text-lg font-semibold font-primary text-zinc-900">Gestao TJ</span>
          </div>
          <button onClick={() => setSidebarOpen(false)} className="lg:hidden p-1 text-zinc-600 hover:bg-zinc-100 rounded" data-testid="close-sidebar-button"><X className="h-5 w-5" /></button>
        </div>

        <div className="px-3 py-2 border-b border-zinc-100">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">Estabelecimento</p>
          <p className="text-sm font-medium text-zinc-900 truncate flex items-center gap-1.5" data-testid="dashboard-tenant-name">
            {user.role === 'master' ? <><ShieldCheck className="h-3.5 w-3.5 text-indigo-600" />Global (Master)</> : <><Building2 className="h-3.5 w-3.5 text-blue-600" />{user.tenant_name || '—'}</>}
          </p>
          {scope && (
            <p className="text-[11px] text-zinc-500 mt-0.5 truncate flex items-center gap-1" data-testid="dashboard-warehouse-name">
              <Warehouse className="h-3 w-3" />{scope}
            </p>
          )}
        </div>

        <nav className="flex-1 overflow-y-auto py-2 scrollbar-hide" data-testid="sidebar-nav">
          {filteredMenu.map((item) => { const Icon = item.icon; const active = isActive(item.path); return (
            <Link key={item.path} to={item.path} data-testid={`nav-${item.label.toLowerCase().replace(/\s+/g,'-')}`}
              className={`flex items-center gap-3 mx-2 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${active ? `${accentBgSoft} ${accentText}` : 'text-zinc-700 hover:bg-zinc-100'}`}>
              <Icon className="h-4 w-4 flex-shrink-0" /><span className="flex-1">{item.label}</span>
              {item.label === 'Alertas' && unreadCount > 0 && <span className="bg-red-500 text-white text-xs font-medium px-1.5 py-0.5 rounded-full min-w-[18px] text-center leading-none">{unreadCount}</span>}
            </Link>); })}
        </nav>

        <div className="border-t border-zinc-200 p-3">
          <Link to="/dashboard/profile" className="flex items-center gap-2 mb-2 hover:bg-zinc-50 rounded-lg p-2 -m-2 transition-colors">
            <div className={`h-8 w-8 rounded-full ${accentBgSoft} flex items-center justify-center flex-shrink-0`}><UserCircle className={`h-4 w-4 ${accentText}`} /></div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-zinc-900 truncate" data-testid="user-name">{user.name}</p>
              <p className="text-[10px] text-zinc-500 truncate" data-testid="user-role">{ROLE_LABEL[user.role] || user.role}</p>
            </div>
          </Link>
          <button onClick={handleLogout} data-testid="logout-button" className="flex items-center gap-2 w-full px-3 py-1.5 text-sm text-zinc-700 hover:bg-zinc-100 rounded-lg transition-colors"><LogOut className="h-4 w-4" /><span>Sair</span></button>
        </div>
      </div>

      <div className="flex-1 flex flex-col min-w-0">
        <div className="lg:hidden h-14 flex items-center justify-between px-4 bg-white border-b border-zinc-200">
          <button onClick={() => setSidebarOpen(true)} data-testid="open-sidebar-button" className="p-2 text-zinc-700 hover:bg-zinc-100 rounded-lg"><Menu className="h-5 w-5" /></button>
          <span className="text-base font-semibold font-primary text-zinc-900">Gestao TJ</span>
          <Link to="/dashboard/alerts" className="p-2 relative"><Bell className="h-5 w-5 text-zinc-700" />{unreadCount > 0 && <span className="absolute top-1 right-1 bg-red-500 text-white text-xs rounded-full h-4 w-4 flex items-center justify-center">{unreadCount}</span>}</Link>
        </div>
        <div className="flex-1 overflow-y-auto"><Outlet /></div>
      </div>
    </div>
  );
};
