import React, { useEffect, useState } from 'react';
import { storesAPI, tenantsAPI } from '../api';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Building2, Plus, Pencil, Trash2, MapPin } from 'lucide-react';
import { toast } from 'sonner';
import { getUser, canManageStores, isMaster } from '../auth';

export const StoresPage = () => {
  const me = getUser() || {};
  const [stores, setStores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ name: '', code: '', address: '' });
  const [tenants, setTenants] = useState([]);
  const [selectedTenant, setSelectedTenant] = useState('');

  const canManage = canManageStores(me);
  const isMasterUser = isMaster(me);
  // Master seleciona o estabelecimento (tenant) ao criar a loja
  const needsTenantPick = isMasterUser;

  const load = async () => {
    try {
      const r = await storesAPI.getAll();
      setStores(r.data);
    } catch { toast.error('Erro ao carregar lojas'); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  // Carrega TODOS os tenants para o Master (necessario para o dropdown e para criar lojas de qualquer estabelecimento)
  useEffect(() => {
    if (isMasterUser) {
      tenantsAPI.getAll()
        .then(r => setTenants(r.data))
        .catch(() => toast.error('Erro ao carregar estabelecimentos'));
    }
  }, [canManage, isMasterUser]);

  const openNew = () => { setEditing(null); setForm({ name: '', code: '', address: '' }); setSelectedTenant(''); setOpen(true); };
  const openEdit = (s) => { setEditing(s); setForm({ name: s.name, code: s.code || '', address: s.address || '' }); setOpen(true); };

  const save = async () => {
    if (!form.name || form.name.trim().length < 2) { toast.error('Informe o nome da loja'); return; }
    try {
      if (editing) {
        await storesAPI.update(editing.id, form);
        toast.success('Loja atualizada');
      } else if (needsTenantPick) {
        if (!selectedTenant) { toast.error('Selecione o estabelecimento'); return; }
        await tenantsAPI.createStore(selectedTenant, form);
        toast.success('Loja criada');
      } else {
        await storesAPI.create(form);
        toast.success('Loja criada');
      }
      setOpen(false);
      load();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erro ao salvar');
    }
  };

  const remove = async (s) => {
    if (!window.confirm(`Excluir loja "${s.name}"?`)) return;
    try { await storesAPI.delete(s.id); toast.success('Loja excluida'); load(); }
    catch (e) { toast.error(e.response?.data?.detail || 'Nao foi possivel excluir'); }
  };

  if (loading) return <div className="p-6 text-zinc-500">Carregando...</div>;

  return (
    <div className="p-6 space-y-4" data-testid="stores-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-zinc-900 flex items-center gap-2"><Building2 className="h-6 w-6 text-blue-600" />Lojas / Unidades</h1>
          <p className="text-sm text-zinc-500">Cada loja agrupa depositos PAI/FILHO. Util para grupos com varias unidades fisicas.</p>
        </div>
        {canManage && (
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button onClick={openNew} className="bg-blue-600 hover:bg-blue-700 text-white" data-testid="new-store-btn"><Plus className="h-4 w-4 mr-1" />Nova loja</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>{editing ? 'Editar loja' : 'Nova loja'}</DialogTitle></DialogHeader>
              <div className="space-y-3">
                {!editing && needsTenantPick && (
                  <div>
                    <label className="block text-sm font-medium text-zinc-700 mb-1">Estabelecimento</label>
                    <Select value={selectedTenant} onValueChange={setSelectedTenant}>
                      <SelectTrigger data-testid="store-tenant-select"><SelectValue placeholder="Selecione o estabelecimento" /></SelectTrigger>
                      <SelectContent>{tenants.map(t => <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                )}
                <Input placeholder="Nome (ex: Restaurante A)" value={form.name} onChange={e => setForm({...form, name: e.target.value})} data-testid="store-name" />
                <Input placeholder="Codigo (ex: REST-A)" value={form.code} onChange={e => setForm({...form, code: e.target.value})} data-testid="store-code" />
                <Input placeholder="Endereco" value={form.address} onChange={e => setForm({...form, address: e.target.value})} data-testid="store-address" />
                <Button onClick={save} className="w-full bg-blue-600 hover:bg-blue-700 text-white" data-testid="save-store-btn">{editing ? 'Salvar' : 'Criar'}</Button>
              </div>
            </DialogContent>
          </Dialog>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {stores.length === 0 && <div className="col-span-full p-8 text-center text-zinc-500 border border-dashed border-zinc-300 rounded-lg">Nenhuma loja cadastrada</div>}
        {stores.map(s => (
          <div key={s.id} className="bg-white rounded-lg border border-zinc-200 p-4 hover:shadow-sm transition" data-testid={`store-card-${s.id}`}>
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-zinc-900 truncate">{s.name}</h3>
                {s.code && <p className="text-xs text-zinc-500">{s.code}</p>}
                {s.address && <p className="text-sm text-zinc-600 mt-1 flex items-start gap-1"><MapPin className="h-3.5 w-3.5 mt-0.5 flex-shrink-0" />{s.address}</p>}
              </div>
              {canManage && (
                <div className="flex gap-1">
                  <button onClick={() => openEdit(s)} className="p-1.5 text-zinc-500 hover:text-blue-600 hover:bg-blue-50 rounded" data-testid={`edit-store-${s.id}`}><Pencil className="h-4 w-4" /></button>
                  <button onClick={() => remove(s)} className="p-1.5 text-zinc-500 hover:text-red-600 hover:bg-red-50 rounded" data-testid={`delete-store-${s.id}`}><Trash2 className="h-4 w-4" /></button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
