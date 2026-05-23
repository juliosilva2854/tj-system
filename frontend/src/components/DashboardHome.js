import React, { useState, useEffect } from 'react';
import { dashboardAPI } from '../api';
import { Package, Users, Warehouse, FileText, AlertTriangle, ArrowLeftRight } from 'lucide-react';
import { toast } from 'sonner';

const getCurrentUser = () => { try { return JSON.parse(localStorage.getItem('user') || '{}'); } catch { return {}; } };

export const DashboardHome = () => {
  const [stats, setStats] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const me = getCurrentUser();

  useEffect(() => { loadData(); }, []);
  const loadData = async () => {
    try {
      const [s, a] = await Promise.all([dashboardAPI.getStats(), dashboardAPI.getAlerts()]);
      setStats(s.data); setAlerts(a.data);
    } catch { toast.error('Erro ao carregar dashboard'); }
    finally { setLoading(false); }
  };

  if (loading) return <div className="p-4 md:p-8" data-testid="dashboard-loading"><div className="animate-pulse space-y-4"><div className="h-24 bg-zinc-200 rounded-xl" /><div className="h-24 bg-zinc-200 rounded-xl" /></div></div>;

  const cards = [
    { label: 'Produtos', value: stats?.total_products || 0, icon: Package, color: 'bg-blue-50 text-blue-600' },
    { label: 'Fornecedores', value: stats?.total_suppliers || 0, icon: Users, color: 'bg-green-50 text-green-600' },
    { label: 'Depositos', value: stats?.total_warehouses || 0, icon: Warehouse, color: 'bg-purple-50 text-purple-600' },
    { label: 'NFs Pendentes', value: stats?.pending_invoices || 0, icon: FileText, color: 'bg-yellow-50 text-yellow-600' },
    { label: 'Requisicoes Pendentes', value: stats?.pending_requisitions || 0, icon: ArrowLeftRight, color: 'bg-cyan-50 text-cyan-600' },
    { label: 'Alertas Estoque', value: stats?.low_stock_alerts || 0, icon: AlertTriangle, color: 'bg-red-50 text-red-600' },
  ];

  return (
    <div className="p-4 md:p-8" data-testid="dashboard-home">
      <div className="mb-6">
        <h1 className="text-2xl md:text-4xl font-semibold font-primary text-zinc-900 tracking-tight">Dashboard</h1>
        <p className="mt-1 text-sm text-zinc-600">
          {me.role === 'master' ? 'Visao global da plataforma (todos os estabelecimentos)' : me.role === 'operacional' ? 'Visao do deposito FILHO vinculado a voce' : 'Visao operacional do estabelecimento'}
        </p>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-6">
        {cards.map(c => { const Icon = c.icon; return (
          <div key={c.label} data-testid={`stats-card-${c.label.toLowerCase().replace(/\s+/g, '-')}`} className="bg-white rounded-xl border border-zinc-200 shadow-sm p-4 md:p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">{c.label}</p>
              <div className={`h-8 w-8 md:h-10 md:w-10 rounded-lg ${c.color} flex items-center justify-center`}><Icon className="h-4 w-4 md:h-5 md:w-5" /></div>
            </div>
            <p className="text-2xl md:text-3xl font-semibold font-mono text-zinc-900">{c.value}</p>
          </div>
        ); })}
      </div>
      {alerts.length > 0 && (
        <div className="bg-white rounded-xl border border-zinc-200 shadow-sm p-4 md:p-6" data-testid="low-stock-section">
          <div className="flex items-center gap-2 mb-4"><AlertTriangle className="h-5 w-5 text-red-600" /><h2 className="text-lg font-semibold text-zinc-900">Alertas de Estoque Baixo</h2></div>
          <div className="space-y-2">
            {alerts.map((a, i) => (
              <div key={i} className="flex flex-col sm:flex-row sm:items-center justify-between p-3 bg-red-50 border border-red-200 rounded-lg gap-2">
                <div><p className="font-medium text-zinc-900">{a.product_name}</p><p className="text-sm text-zinc-600">{a.warehouse_name}</p></div>
                <p className="text-base font-mono font-semibold text-red-600">{a.current_quantity} / {a.min_stock}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
