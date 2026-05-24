import React, { useEffect, useState } from 'react';
import { modulesAPI, warehousesAPI, storesAPI } from '../api';
import { Button } from './ui/button';
import { Toggle3D as Switch } from './ui/switch-shim';
import { Settings, Save, Warehouse, ShieldCheck } from 'lucide-react';
import { toast } from 'sonner';

const MODULE_LABELS = {
  dashboard: 'Dashboard', stores: 'Lojas', warehouses: 'Depositos',
  products: 'Produtos', inventory: 'Estoque', requisitions: 'Requisicoes',
  transfers: 'Transferencias', invoices: 'Notas Fiscais', suppliers: 'Fornecedores',
  sales: 'Vendas', reports: 'Relatorios', alerts: 'Alertas',
  audit: 'Auditoria', users: 'Usuarios', guide: 'Guia',
};

const getUser = () => { try { return JSON.parse(localStorage.getItem('user') || '{}'); } catch { return {}; } };

export const ModulesPage = () => {
  const me = getUser();
  const [allModules, setAllModules] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [stores, setStores] = useState([]);
  const [selected, setSelected] = useState('');
  const [enabled, setEnabled] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const canManage = ['master', 'admin'].includes(me.role);

  useEffect(() => {
    (async () => {
      try {
        const [m, w, s] = await Promise.all([modulesAPI.list(), warehousesAPI.getAll(), storesAPI.getAll()]);
        setAllModules(m.data.modules);
        const pais = w.data.filter(x => x.type === 'pai');
        setWarehouses(pais);
        setStores(s.data);
        if (pais.length > 0) {
          setSelected(pais[0].id);
          setEnabled(pais[0].enabled_modules || []);
        }
      } catch { toast.error('Erro ao carregar dados'); }
      finally { setLoading(false); }
    })();
  }, []);

  const onSelect = (wid) => {
    setSelected(wid);
    const w = warehouses.find(x => x.id === wid);
    setEnabled(w?.enabled_modules || []);
  };

  const toggle = (mod) => {
    setEnabled(prev => prev.includes(mod) ? prev.filter(m => m !== mod) : [...prev, mod]);
  };

  const save = async () => {
    setSaving(true);
    try {
      await modulesAPI.updateWarehouse(selected, enabled);
      toast.success('Modulos atualizados');
      // Atualiza state local
      setWarehouses(prev => prev.map(w => w.id === selected ? { ...w, enabled_modules: enabled } : w));
    } catch (e) { toast.error(e.response?.data?.detail || 'Erro ao salvar'); }
    finally { setSaving(false); }
  };

  const sName = (id) => stores.find(s => s.id === id)?.name || '—';

  if (loading) return <div className="p-6 text-zinc-500">Carregando...</div>;
  if (!canManage) return <div className="p-6 text-zinc-500">Sem permissao para acessar esta tela.</div>;
  if (warehouses.length === 0) return <div className="p-6 text-zinc-500">Nenhum deposito PAI cadastrado ainda.</div>;

  return (
    <div className="p-6 space-y-4" data-testid="modules-page">
      <div>
        <h1 className="text-2xl font-semibold text-zinc-900 flex items-center gap-2"><Settings className="h-6 w-6 text-indigo-600" />Configuracao de Modulos</h1>
        <p className="text-sm text-zinc-500">Habilite/desabilite menus por Deposito PAI. Cada FILHO herda do seu PAI.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-1 bg-white rounded-lg border border-zinc-200 p-3">
          <p className="text-xs font-semibold uppercase text-zinc-500 mb-2">Depositos PAI</p>
          <div className="space-y-1">
            {warehouses.map(w => (
              <button key={w.id} onClick={() => onSelect(w.id)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm flex items-center gap-2 ${selected === w.id ? 'bg-indigo-50 text-indigo-700 font-medium' : 'hover:bg-zinc-50'}`}
                data-testid={`pai-${w.id}`}>
                <Warehouse className="h-4 w-4 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="truncate">{w.name}</div>
                  <div className="text-[10px] text-zinc-500">{sName(w.store_id)}</div>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="lg:col-span-2 bg-white rounded-lg border border-zinc-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-xs font-semibold uppercase text-zinc-500">Modulos habilitados</p>
              <p className="text-sm font-medium text-zinc-900">{warehouses.find(w => w.id === selected)?.name}</p>
            </div>
            <Button onClick={save} disabled={saving} className="bg-indigo-600 hover:bg-indigo-700" data-testid="save-modules-btn">
              <Save className="h-4 w-4 mr-1" />{saving ? 'Salvando...' : 'Salvar'}
            </Button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {allModules.map(m => (
              <label key={m} className="flex items-center justify-between px-3 py-2 border border-zinc-200 rounded-lg cursor-pointer hover:bg-zinc-50" data-testid={`module-${m}`}>
                <div className="flex items-center gap-2">
                  <ShieldCheck className={`h-4 w-4 ${enabled.includes(m) ? 'text-indigo-600' : 'text-zinc-300'}`} />
                  <span className="text-sm text-zinc-700">{MODULE_LABELS[m] || m}</span>
                </div>
                <input type="checkbox" checked={enabled.includes(m)} onChange={() => toggle(m)} className="h-4 w-4 accent-indigo-600" />
              </label>
            ))}
          </div>
          <p className="text-xs text-zinc-500 mt-3">Lista vazia = todos os modulos habilitados (default).</p>
        </div>
      </div>
    </div>
  );
};
