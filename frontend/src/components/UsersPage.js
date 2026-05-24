import React, { useState, useEffect } from 'react';
import { usersAPI, authAPI, tenantsAPI, warehousesAPI } from '../api';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Switch } from './ui/switch';
import { Plus, Pencil, Trash2, UserCircle, Phone, CreditCard, AtSign } from 'lucide-react';
import { toast } from 'sonner';

const ROLE_LABEL = { 
  master: 'Master Global', 
  admin: 'Administrador', 
  gerente_geral: 'Gerente Geral', 
  gerente_logistica: 'Gerente Logística', 
  gerente_operacional: 'Gerente Operacional', 
  logistica: 'Logística (PAI)', 
  operacional: 'Operacional (FILHO)' 
};

const ROLE_COLOR = { 
  master: 'bg-indigo-100 text-indigo-700 border-indigo-200', 
  admin: 'bg-blue-100 text-blue-700 border-blue-200', 
  gerente_geral: 'bg-amber-100 text-amber-800 border-amber-200', 
  gerente_logistica: 'bg-emerald-100 text-emerald-700 border-emerald-200', 
  gerente_operacional: 'bg-sky-100 text-sky-700 border-sky-200', 
  logistica: 'bg-purple-100 text-purple-700 border-purple-200', 
  operacional: 'bg-zinc-100 text-zinc-700 border-zinc-200' 
};

const getCurrentUser = () => { try { return JSON.parse(localStorage.getItem('user') || '{}'); } catch { return {}; } };

const formatCPF = (value) => {
  const numbers = value.replace(/\D/g, '');
  if (numbers.length <= 11) {
    return numbers.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
  }
  return value;
};

const formatPhone = (value) => {
  const numbers = value.replace(/\D/g, '');
  if (numbers.length <= 11) {
    return numbers.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
  }
  return value;
};

const initial = { 
  email: '', 
  name: '', 
  username: '',
  cpf: '',
  phone: '',
  password: '', 
  role: 'operacional', 
  tenant_id: '', 
  warehouse_id: '' 
};

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

  const [tenantWarehouses, setTenantWarehouses] = useState([]);
  useEffect(() => {
    if (!isMaster) return;
    if (!formData.tenant_id) { setTenantWarehouses([]); return; }
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
      const payload = {
        ...formData,
        cpf: formData.cpf.replace(/\D/g, ''), // Remove formatação
        phone: formData.phone.replace(/\D/g, ''),
      };

      if (editingId) {
        const updateData = { 
          name: payload.name, 
          role: payload.role,
          phone: payload.phone,
        };
        if (payload.password) updateData.password = payload.password;
        if (payload.warehouse_id !== undefined) updateData.warehouse_id = payload.warehouse_id;
        await usersAPI.update(editingId, updateData);
        toast.success('Usuário atualizado!');
      } else {
        if (payload.role === 'master') { 
          delete payload.tenant_id; 
          delete payload.warehouse_id;
          payload.is_master_access = true;
        }
        await authAPI.register(payload);
        toast.success('Usuário criado!');
      }
      setDialogOpen(false); resetForm(); load();
    } catch (err) { 
      toast.error(err.response?.data?.detail || 'Erro ao salvar'); 
    }
  };

  const handleEdit = (u) => {
    setFormData({ 
      email: u.email, 
      name: u.name, 
      username: u.username || '',
      cpf: u.cpf ? formatCPF(u.cpf) : '',
      phone: u.phone ? formatPhone(u.phone) : '',
      password: '', 
      role: u.role, 
      tenant_id: u.tenant_id || '', 
      warehouse_id: u.warehouse_id || '' 
    });
    setEditingId(u.id);
    setDialogOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Excluir este usuário?')) return;
    try { await usersAPI.delete(id); toast.success('Excluído!'); load(); }
    catch (err) { toast.error(err.response?.data?.detail || 'Erro'); }
  };

  const handleToggleActive = async (id, active) => {
    try { await usersAPI.update(id, { active: !active }); toast.success('Status atualizado'); load(); }
    catch { toast.error('Erro'); }
  };

  const resetForm = () => { setFormData(initial); setEditingId(null); };

  if (loading) return (
    <div className="p-4 md:p-8 flex items-center justify-center h-64" data-testid="users-loading">
      <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
    </div>
  );

  const tenantName = (id) => tenants.find(t => t.id === id)?.name || (id ? '—' : 'Global');
  const warehouseName = (id) => warehouseOptions.find(w => w.id === id)?.name || (id ? '—' : '');

  return (
    <div className="p-4 md:p-8" data-testid="users-page">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl md:text-4xl font-semibold font-primary text-zinc-900 tracking-tight">Usuários</h1>
          <p className="mt-1 text-sm text-zinc-600">Gerencie usuários, permissões e acessos ao sistema.</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(o) => { setDialogOpen(o); if (!o) resetForm(); }}>
          <DialogTrigger asChild>
            <Button data-testid="add-user-button" className="bg-blue-600 hover:bg-blue-700 text-white">
              <Plus className="h-4 w-4 mr-2" />Novo Usuário
            </Button>
          </DialogTrigger>
          <DialogContent className="max-h-[90vh] overflow-y-auto max-w-2xl">
            <DialogHeader>
              <DialogTitle>{editingId ? 'Editar Usuário' : 'Novo Usuário'}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Informações Pessoais */}
              <div className="bg-zinc-50 p-4 rounded-lg border border-zinc-200">
                <h3 className="text-sm font-semibold text-zinc-900 mb-3">Informações Pessoais</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-zinc-700 mb-1.5">Nome Completo</label>
                    <Input 
                      data-testid="user-name-input" 
                      value={formData.name} 
                      onChange={e => setFormData({...formData, name: e.target.value})} 
                      required 
                      placeholder="João da Silva"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-zinc-700 mb-1.5">CPF</label>
                    <Input 
                      data-testid="user-cpf-input"
                      value={formData.cpf} 
                      onChange={e => setFormData({...formData, cpf: formatCPF(e.target.value)})} 
                      placeholder="000.000.000-00"
                      maxLength={14}
                      disabled={!!editingId}
                    />
                    {!editingId && <p className="text-xs text-zinc-500 mt-1">Apenas números, será formatado automaticamente</p>}
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-zinc-700 mb-1.5">
                      <Phone className="h-3 w-3 inline mr-1" />
                      Telefone
                    </label>
                    <Input 
                      data-testid="user-phone-input"
                      value={formData.phone} 
                      onChange={e => setFormData({...formData, phone: formatPhone(e.target.value)})} 
                      placeholder="(11) 99999-9999"
                      maxLength={15}
                    />
                  </div>
                </div>
              </div>

              {/* Credenciais de Acesso */}
              <div className="bg-zinc-50 p-4 rounded-lg border border-zinc-200">
                <h3 className="text-sm font-semibold text-zinc-900 mb-3">Credenciais de Acesso</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-zinc-700 mb-1.5">Email</label>
                    <Input 
                      data-testid="user-email-input" 
                      type="email" 
                      value={formData.email} 
                      onChange={e => setFormData({...formData, email: e.target.value})} 
                      required 
                      disabled={!!editingId}
                      placeholder="usuario@exemplo.com"
                    />
                    {editingId && <p className="text-xs text-zinc-500 mt-1">Email não pode ser alterado</p>}
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-zinc-700 mb-1.5">
                      <AtSign className="h-3 w-3 inline mr-1" />
                      Usuário (Username)
                    </label>
                    <Input 
                      data-testid="user-username-input"
                      value={formData.username} 
                      onChange={e => setFormData({...formData, username: e.target.value.toLowerCase().replace(/[^a-z0-9._-]/g, '')})} 
                      placeholder="usuario.sistema"
                      disabled={!!editingId}
                      required={formData.role !== 'master'}
                    />
                    {!editingId && <p className="text-xs text-zinc-500 mt-1">Apenas letras, números, ponto, hífen e underscore</p>}
                    {editingId && <p className="text-xs text-zinc-500 mt-1">Username não pode ser alterado</p>}
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-zinc-700 mb-1.5">
                      Senha {editingId ? '(deixe vazio para não alterar)' : ''}
                    </label>
                    <Input 
                      data-testid="user-password-input" 
                      type="password" 
                      value={formData.password} 
                      onChange={e => setFormData({...formData, password: e.target.value})} 
                      required={!editingId} 
                      minLength={editingId ? 0 : 6}
                      placeholder={editingId ? "••••••••" : "Mínimo 6 caracteres"}
                    />
                  </div>
                </div>
              </div>

              {/* Permissões e Vínculos */}
              <div className="bg-zinc-50 p-4 rounded-lg border border-zinc-200">
                <h3 className="text-sm font-semibold text-zinc-900 mb-3">Permissões e Vínculos</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-zinc-700 mb-1.5">Papel (Role)</label>
                    <Select value={formData.role} onValueChange={v => setFormData({...formData, role: v})}>
                      <SelectTrigger data-testid="user-role-select"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {availableRoles.map(r => (
                          <SelectItem key={r} value={r}>{ROLE_LABEL[r]}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-zinc-500 mt-1">Define o nível de acesso e permissões do usuário</p>
                  </div>

                  {isMaster && formData.role !== 'master' && (
                    <div>
                      <label className="block text-sm font-medium text-zinc-700 mb-1.5">Estabelecimento</label>
                      <Select value={formData.tenant_id} onValueChange={v => setFormData({...formData, tenant_id: v, warehouse_id: ''})}>
                        <SelectTrigger data-testid="user-tenant-select"><SelectValue placeholder="Selecione" /></SelectTrigger>
                        <SelectContent>
                          {tenants.map(t => <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>)}
                        </SelectContent>
                      </Select>
                    </div>
                  )}

                  {formData.role !== 'master' && formData.role !== 'admin' && (
                    <div>
                      <label className="block text-sm font-medium text-zinc-700 mb-1.5">
                        Depósito Vinculado {formData.role === 'operacional' ? '(obrigatório)' : '(opcional)'}
                      </label>
                      <Select value={formData.warehouse_id} onValueChange={v => setFormData({...formData, warehouse_id: v})}>
                        <SelectTrigger data-testid="user-warehouse-select"><SelectValue placeholder="Selecione" /></SelectTrigger>
                        <SelectContent>
                          {warehouseOptions.length === 0 && (
                            <div className="px-3 py-2 text-xs text-zinc-500">Nenhum depósito disponível</div>
                          )}
                          {warehouseOptions.map(w => (
                            <SelectItem key={w.id} value={w.id}>
                              {w.name} ({w.type.toUpperCase()})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <p className="text-xs text-zinc-500 mt-1">
                        {formData.role === 'operacional' 
                          ? 'Vincule ao depósito FILHO. Esse usuário cria requisições ao PAI.' 
                          : 'Logística do PAI: vincule ao depósito PAI que ele opera.'}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex gap-2">
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => setDialogOpen(false)}
                  className="flex-1"
                >
                  Cancelar
                </Button>
                <Button 
                  data-testid="user-submit-button" 
                  type="submit" 
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
                >
                  {editingId ? 'Atualizar' : 'Criar'} Usuário
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Tabela de Usuários */}
      <div className="bg-white rounded-xl border border-zinc-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[900px]" data-testid="users-table">
            <thead className="bg-zinc-50 border-b border-zinc-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">Usuário</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">Contato</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">Papel</th>
                {isMaster && <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">Estabelecimento</th>}
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">Depósito</th>
                <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-zinc-500">Status</th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-zinc-500">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {users.map(u => (
                <tr key={u.id} className="hover:bg-zinc-50 transition-colors" data-testid={`user-row-${u.id}`}>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center flex-shrink-0 text-white font-semibold">
                        {u.name?.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <div className="text-sm font-medium text-zinc-900">{u.name}</div>
                        {u.username && (
                          <div className="text-xs text-zinc-500 font-mono">@{u.username}</div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm text-zinc-600">{u.email}</div>
                    {u.phone && (
                      <div className="text-xs text-zinc-500 flex items-center gap-1 mt-0.5">
                        <Phone className="h-3 w-3" />
                        {formatPhone(u.phone)}
                      </div>
                    )}
                    {u.cpf && (
                      <div className="text-xs text-zinc-500 flex items-center gap-1 mt-0.5">
                        <CreditCard className="h-3 w-3" />
                        {formatCPF(u.cpf)}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium border ${ROLE_COLOR[u.role]}`}>
                      {ROLE_LABEL[u.role]}
                    </span>
                  </td>
                  {isMaster && <td className="px-4 py-3 text-sm text-zinc-600">{tenantName(u.tenant_id)}</td>}
                  <td className="px-4 py-3 text-sm text-zinc-600">{warehouseName(u.warehouse_id)}</td>
                  <td className="px-4 py-3 text-center">
                    <Switch 
                      checked={u.active} 
                      onCheckedChange={() => handleToggleActive(u.id, u.active)} 
                      disabled={u.id === me.id}
                    />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button 
                        onClick={() => handleEdit(u)} 
                        data-testid={`edit-user-${u.id}`} 
                        className="p-2 text-zinc-600 hover:bg-zinc-100 rounded-lg transition-colors"
                        title="Editar usuário"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      {u.id !== me.id && isMaster && (
                        <button 
                          onClick={() => handleDelete(u.id)} 
                          data-testid={`delete-user-${u.id}`} 
                          className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          title="Excluir usuário"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={isMaster ? 7 : 6} className="px-4 py-8 text-center text-zinc-500">
                    Nenhum usuário encontrado
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
