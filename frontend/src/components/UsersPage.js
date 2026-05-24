import React, { useState, useEffect } from 'react';
import { usersAPI, authAPI, tenantsAPI, warehousesAPI } from '../api';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Switch } from './ui/switch';
import { Plus, Pencil, Trash2, UserCircle } from 'lucide-react';
import { toast } from 'sonner';

const ROLE_LABEL = { master: 'Master Global', admin: 'Administrador', gerente_geral: 'Gerente Geral', gerente_logistica: 'Gerente Logistica', gerente_operacional: 'Gerente Operacional', logistica: 'Logistica (PAI)', operacional: 'Operacional (FILHO)' };
const ROLE_COLOR = { master: 'bg-indigo-100 text-indigo-700', admin: 'bg-blue-100 text-blue-700', gerente_geral: 'bg-amber-100 text-amber-800', gerente_logistica: 'bg-emerald-100 text-emerald-700', gerente_operacional: 'bg-sky-100 text-sky-700', logistica: 'bg-purple-100 text-purple-700', operacional: 'bg-zinc-100 text-zinc-700' };

const getCurrentUser = () => { try { return JSON.parse(localStorage.getItem('user') || '{}'); } catch { return {}; } };
const initial = { email: '', name: '', password: '', role: 'operacional', tenant_id: '', warehouse_id: '' };

export const UsersPage = () => {
  const [users, setUsers] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState(initial);
  const me = getCurrentUser();
  const isMaster = me.role === 'master';

  useEffect(() => { load(); }, []);

  const load = async () => {
    try {
      const u = await usersAPI.getAll();
      setUsers(u.data);
      if (isMaster) {
        const t = await tenantsAPI.getAll();
        setTenants(t.data);
      } else {
        const w = await warehousesAPI.getAll();
        setWarehouses(w.data);
      }
    } catch { toast.error('Erro ao carregar dados'); }
    finally { setLoading(false); }
  };

  // For master: when tenant selected, load warehouses of that tenant lazily
  const [tenantWarehouses, setTenantWarehouses] = useState([]);
  useEffect(() => {
    if (!isMaster) return;
    if (!formData.tenant_id) { setTenantWarehouses([]); return; }
    // Use a dedicated call. Since list_warehouses already filters by current user tenant,
    // master gets all - we filter client-side
    warehousesAPI.getAll().then(r => {
      setTenantWarehouses(r.data.filter(w => w.tenant_id === formData.tenant_id));
    }).catch(() => setTenantWarehouses([]));
  }, [formData.tenant_id, isMaster]);

  const warehouseOptions = isMaster ? tenantWarehouses : warehouses;
  const availableRoles = isMaster
    ? ['admin', 'gerente_geral', 'gerente_logistica', 'gerente_operacional', 'logistica', 'operacional', 'master']
    : ['admin', 'gerente_geral', 'gerente_logistica', 'gerente_operacional', 'logistica', 'operacional'];

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingId) {
        const updateData = { name: formData.name, role: formData.role };
        if (formData.password) updateData.password = formData.password;
        if (formData.warehouse_id !== undefined) updateData.warehouse_id = formData.warehouse_id;
        await usersAPI.update(editingId, updateData);
        toast.success('Usuario atualizado!');
      } else {
        const payload = { ...formData };
        if (payload.role === 'master') { delete payload.tenant_id; delete payload.warehouse_id; }
        await authAPI.register(payload);
        toast.success('Usuario criado!');
      }
      setDialogOpen(false); resetForm(); load();
    } catch (err) { toast.error(err.response?.data?.detail || 'Erro ao salvar'); }
  };

  const handleEdit = (u) => {
    setFormData({ email: u.email, name: u.name, password: '', role: u.role, tenant_id: u.tenant_id || '', warehouse_id: u.warehouse_id || '' });
    setEditingId(u.id);
    setDialogOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Excluir este usuario?')) return;
    try { await usersAPI.delete(id); toast.success('Excluido!'); load(); }
    catch (err) { toast.error(err.response?.data?.detail || 'Erro'); }
  };

  const handleToggleActive = async (id, active) => {
    try { await usersAPI.update(id, { active: !active }); toast.success('Status atualizado'); load(); }
    catch { toast.error('Erro'); }
  };

  const resetForm = () => { setFormData(initial); setEditingId(null); };

  if (loading) return <div className="p-4 md:p-8" data-testid="users-loading">Carregando...</div>;

  const tenantName = (id) => tenants.find(t => t.id === id)?.name || (id ? '—' : 'Global');
  const warehouseName = (id) => warehouseOptions.find(w => w.id === id)?.name || (id ? '—' : '');

  return (
    <div className="p-4 md:p-8" data-testid="users-page">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl md:text-4xl font-semibold font-primary text-zinc-900 tracking-tight">Usuarios</h1>
          <p className="mt-1 text-sm text-zinc-600">Defina papel (RBAC) e vinculacao a estabelecimento e deposito.</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(o) => { setDialogOpen(o); if (!o) resetForm(); }}>
          <DialogTrigger asChild>
            <Button data-testid="add-user-button" className="bg-blue-600 hover:bg-blue-700 text-white"><Plus className="h-4 w-4 mr-2" />Novo Usuario</Button>
          </DialogTrigger>
          <DialogContent className="max-h-[90vh] overflow-y-auto">
            <DialogHeader><DialogTitle>{editingId ? 'Editar Usuario' : 'Novo Usuario'}</DialogTitle></DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">Nome</label>
                <Input data-testid="user-name-input" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} required />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">Email</label>
                <Input data-testid="user-email-input" type="email" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} required disabled={!!editingId} />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">Senha {editingId ? '(vazio = nao alterar)' : ''}</label>
                <Input data-testid="user-password-input" type="password" value={formData.password} onChange={e => setFormData({...formData, password: e.target.value})} required={!editingId} minLength={editingId ? 0 : 6} />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">Papel (RBAC)</label>
                <Select value={formData.role} onValueChange={v => setFormData({...formData, role: v})}>
                  <SelectTrigger data-testid="user-role-select"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {availableRoles.map(r => <SelectItem key={r} value={r}>{ROLE_LABEL[r]}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              {isMaster && formData.role !== 'master' && (
                <div>
                  <label className="block text-sm font-medium text-zinc-700 mb-1.5">Estabelecimento</label>
                  <Select value={formData.tenant_id} onValueChange={v => setFormData({...formData, tenant_id: v, warehouse_id: ''})}>
                    <SelectTrigger data-testid="user-tenant-select"><SelectValue placeholder="Selecione" /></SelectTrigger>
                    <SelectContent>{tenants.map(t => <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>)}</SelectContent>
                  </Select>
                </div>
              )}
              {formData.role !== 'master' && formData.role !== 'admin' && (
                <div>
                  <label className="block text-sm font-medium text-zinc-700 mb-1.5">Deposito vinculado {formData.role === 'operacional' ? '(obrigatorio)' : '(opcional)'}</label>
                  <Select value={formData.warehouse_id} onValueChange={v => setFormData({...formData, warehouse_id: v})}>
                    <SelectTrigger data-testid="user-warehouse-select"><SelectValue placeholder="Selecione" /></SelectTrigger>
                    <SelectContent>
                      {warehouseOptions.length === 0 && <div className="px-3 py-2 text-xs text-zinc-500">Nenhum deposito disponivel</div>}
                      {warehouseOptions.map(w => <SelectItem key={w.id} value={w.id}>{w.name} ({w.type.toUpperCase()})</SelectItem>)}
                    </SelectContent>
                  </Select>
                  <p className="text-[11px] text-zinc-500 mt-1">{formData.role === 'operacional' ? 'Vincule ao deposito FILHO. Esse usuario cria requisicoes ao PAI.' : 'Logistica do PAI: vincule ao deposito PAI que ele opera.'}</p>
                </div>
              )}
              <Button data-testid="user-submit-button" type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white">{editingId ? 'Atualizar' : 'Criar'} Usuario</Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="bg-white rounded-xl border border-zinc-200 shadow-sm overflow-x-auto">
        <table className="w-full min-w-[750px]" data-testid="users-table">
          <thead className="bg-zinc-50 border-b border-zinc-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">Usuario</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">Email</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">Papel</th>
              {isMaster && <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">Estabelecimento</th>}
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">Deposito</th>
              <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-zinc-500">Ativo</th>
              <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-zinc-500">Acoes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100">
            {users.map(u => (
              <tr key={u.id} className="hover:bg-zinc-50 transition-colors" data-testid={`user-row-${u.id}`}>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0"><UserCircle className="h-4 w-4 text-blue-600" /></div>
                    <span className="text-sm font-medium text-zinc-900">{u.name}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-sm text-zinc-600">{u.email}</td>
                <td className="px-4 py-3"><span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${ROLE_COLOR[u.role]}`}>{ROLE_LABEL[u.role]}</span></td>
                {isMaster && <td className="px-4 py-3 text-xs text-zinc-600">{tenantName(u.tenant_id)}</td>}
                <td className="px-4 py-3 text-xs text-zinc-600">{warehouseName(u.warehouse_id)}</td>
                <td className="px-4 py-3 text-center">
                  <Switch checked={u.active} onCheckedChange={() => handleToggleActive(u.id, u.active)} disabled={u.id === me.id} />
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-1">
                    <button onClick={() => handleEdit(u)} data-testid={`edit-user-${u.id}`} className="p-1.5 text-zinc-600 hover:bg-zinc-100 rounded-lg"><Pencil className="h-4 w-4" /></button>
                    {u.id !== me.id && isMaster && (
                      <button onClick={() => handleDelete(u.id)} data-testid={`delete-user-${u.id}`} className="p-1.5 text-red-600 hover:bg-red-50 rounded-lg"><Trash2 className="h-4 w-4" /></button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
