import React, { useState, useEffect } from 'react';
import { tenantsAPI, usersAPI, productsAPI, warehousesAPI, dashboardAPI } from '../api';
import { Building2, Users, Package, Warehouse, TrendingUp, Activity, Store, BarChart3 } from 'lucide-react';
import { toast } from 'sonner';

export const MasterDashboardPage = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalTenants: 0,
    totalUsers: 0,
    totalProducts: 0,
    totalWarehouses: 0,
    activeUsers: 0,
    inactiveUsers: 0,
  });
  const [tenants, setTenants] = useState([]);
  const [recentUsers, setRecentUsers] = useState([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [tenantsRes, usersRes, productsRes, warehousesRes] = await Promise.all([
        tenantsAPI.getAll(),
        usersAPI.getAll(),
        productsAPI.getAll(),
        warehousesAPI.getAll(),
      ]);

      const tenantsData = tenantsRes.data;
      const usersData = usersRes.data;
      const productsData = productsRes.data;
      const warehousesData = warehousesRes.data;

      setTenants(tenantsData);
      setRecentUsers(usersData.slice(0, 10));

      setStats({
        totalTenants: tenantsData.length,
        totalUsers: usersData.length,
        totalProducts: productsData.length,
        totalWarehouses: warehousesData.length,
        activeUsers: usersData.filter(u => u.active).length,
        inactiveUsers: usersData.filter(u => !u.active).length,
      });
    } catch (error) {
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-8 w-8 border-4 border-indigo-600 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  const StatCard = ({ icon: Icon, title, value, subtitle, color = "blue", trend }) => (
    <div className="bg-white rounded-xl border border-zinc-200 p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-zinc-600 mb-1">{title}</p>
          <p className="text-3xl font-bold text-zinc-900">{value}</p>
          {subtitle && <p className="text-xs text-zinc-500 mt-1">{subtitle}</p>}
          {trend && (
            <div className="flex items-center gap-1 mt-2">
              <TrendingUp className="h-3 w-3 text-green-600" />
              <span className="text-xs text-green-600 font-medium">{trend}</span>
            </div>
          )}
        </div>
        <div className={`h-12 w-12 rounded-xl bg-${color}-100 flex items-center justify-center`}>
          <Icon className={`h-6 w-6 text-${color}-600`} />
        </div>
      </div>
    </div>
  );

  return (
    <div className="p-4 md:p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center text-white">
            <Activity className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-zinc-900">Dashboard Master</h1>
            <p className="text-sm text-zinc-600">Visão global de todos os estabelecimentos e usuários</p>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          icon={Building2}
          title="Estabelecimentos"
          value={stats.totalTenants}
          subtitle="Total de tenants cadastrados"
          color="indigo"
        />
        <StatCard
          icon={Users}
          title="Usuários"
          value={stats.totalUsers}
          subtitle={`${stats.activeUsers} ativos, ${stats.inactiveUsers} inativos`}
          color="blue"
        />
        <StatCard
          icon={Package}
          title="Produtos"
          value={stats.totalProducts}
          subtitle="Produtos cadastrados no sistema"
          color="emerald"
        />
        <StatCard
          icon={Warehouse}
          title="Depósitos"
          value={stats.totalWarehouses}
          subtitle="Depósitos em todos os estabelecimentos"
          color="amber"
        />
      </div>

      {/* Establishments Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-xl border border-zinc-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-zinc-900">Estabelecimentos</h2>
            <Building2 className="h-5 w-5 text-zinc-400" />
          </div>
          <div className="space-y-3">
            {tenants.length === 0 ? (
              <p className="text-sm text-zinc-500 text-center py-8">Nenhum estabelecimento cadastrado</p>
            ) : (
              tenants.map(tenant => (
                <div key={tenant.id} className="flex items-center justify-between p-3 bg-zinc-50 rounded-lg hover:bg-zinc-100 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white font-bold text-sm">
                      {tenant.name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-zinc-900">{tenant.name}</p>
                      <p className="text-xs text-zinc-500">{tenant.slug}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {tenant.active ? (
                      <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded">Ativo</span>
                    ) : (
                      <span className="px-2 py-1 bg-zinc-100 text-zinc-700 text-xs font-medium rounded">Inativo</span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recent Users */}
        <div className="bg-white rounded-xl border border-zinc-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-zinc-900">Usuários Recentes</h2>
            <Users className="h-5 w-5 text-zinc-400" />
          </div>
          <div className="space-y-3">
            {recentUsers.length === 0 ? (
              <p className="text-sm text-zinc-500 text-center py-8">Nenhum usuário cadastrado</p>
            ) : (
              recentUsers.map(user => (
                <div key={user.id} className="flex items-center justify-between p-3 bg-zinc-50 rounded-lg hover:bg-zinc-100 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white font-semibold text-sm">
                      {user.name?.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-zinc-900">{user.name}</p>
                      <p className="text-xs text-zinc-500">{user.email}</p>
                    </div>
                  </div>
                  <div>
                    {user.active ? (
                      <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                    ) : (
                      <div className="h-2 w-2 bg-zinc-300 rounded-full"></div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl border border-indigo-200 p-6">
        <h2 className="text-lg font-semibold text-zinc-900 mb-4">Ações Rápidas</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <a
            href="/dashboard/tenants"
            className="flex items-center gap-3 p-4 bg-white rounded-lg hover:shadow-md transition-shadow border border-zinc-200"
          >
            <div className="h-10 w-10 rounded-lg bg-indigo-100 flex items-center justify-center">
              <Building2 className="h-5 w-5 text-indigo-600" />
            </div>
            <div>
              <p className="font-medium text-zinc-900">Gerenciar Estabelecimentos</p>
              <p className="text-xs text-zinc-500">Criar, editar e visualizar tenants</p>
            </div>
          </a>

          <a
            href="/dashboard/users"
            className="flex items-center gap-3 p-4 bg-white rounded-lg hover:shadow-md transition-shadow border border-zinc-200"
          >
            <div className="h-10 w-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <Users className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="font-medium text-zinc-900">Gerenciar Usuários</p>
              <p className="text-xs text-zinc-500">Criar e gerenciar usuários do sistema</p>
            </div>
          </a>

          <a
            href="/dashboard/audit"
            className="flex items-center gap-3 p-4 bg-white rounded-lg hover:shadow-md transition-shadow border border-zinc-200"
          >
            <div className="h-10 w-10 rounded-lg bg-emerald-100 flex items-center justify-center">
              <Activity className="h-5 w-5 text-emerald-600" />
            </div>
            <div>
              <p className="font-medium text-zinc-900">Logs de Auditoria</p>
              <p className="text-xs text-zinc-500">Visualizar ações do sistema</p>
            </div>
          </a>
        </div>
      </div>

      {/* System Info */}
      <div className="mt-6 p-4 bg-zinc-50 rounded-lg border border-zinc-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
            <p className="text-sm text-zinc-600">Sistema operando normalmente</p>
          </div>
          <p className="text-xs text-zinc-500">
            Última atualização: {new Date().toLocaleString('pt-BR')}
          </p>
        </div>
      </div>
    </div>
  );
};
