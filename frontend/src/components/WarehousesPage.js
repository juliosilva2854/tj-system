import React, { useState, useEffect } from 'react';
import { warehousesAPI } from '../api';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Plus, Pencil, Trash2, Warehouse, X, Crown, GitBranch } from 'lucide-react';
import { toast } from 'sonner';

const initialForm = { name: '', location: '', description: '', sectors: [], type: 'pai', parent_id: '' };

export const WarehousesPage = () => {
  const [warehouses, setWarehouses] = useState([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState(initialForm);
  const [newSector, setNewSector] = useState('');

  useEffect(() => { loadData(); }, []);
  const loadData = async () => {
    try { const r = await warehousesAPI.getAll(); setWarehouses(r.data); }
    catch { toast.error('Erro ao carregar'); }
    finally { setLoading(false); }
  };

  const paiList = warehouses.filter(w => w.type === 'pai');
  const paiById = (id) => warehouses.find(w => w.id === id);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (formData.type === 'filho' && !formData.parent_id) { toast.error('Selecione o deposito PAI vinculado'); return; }
    try {
      if (editingId) { await warehousesAPI.update(editingId, formData); toast.success('Deposito atualizado!'); }
      else { await warehousesAPI.create(formData); toast.success('Deposito criado!'); }
      setDialogOpen(false); resetForm(); loadData();
    } catch (err) { toast.error(err.response?.data?.detail || 'Erro'); }
  };

  const handleEdit = (w) => {
    setFormData({
      name: w.name, location: w.location, description: w.description || '',
      sectors: w.sectors || [], type: w.type || 'pai', parent_id: w.parent_id || ''
    });
    setEditingId(w.id);
    setDialogOpen(true);
  };
  const handleDelete = async (id) => {
    if (!window.confirm('Excluir?')) return;
    try { await warehousesAPI.delete(id); toast.success('Excluido!'); loadData(); }
    catch (err) { toast.error(err.response?.data?.detail || 'Erro'); }
  };
  const handleToggleActive = async (id, active) => {
    try { await warehousesAPI.update(id, { active: !active }); toast.success('Status atualizado!'); loadData(); }
    catch { toast.error('Erro'); }
  };
  const addSector = () => {
    if (newSector.trim() && !formData.sectors.includes(newSector.trim())) {
      setFormData({...formData, sectors: [...formData.sectors, newSector.trim()]});
      setNewSector('');
    }
  };
  const removeSector = (s) => setFormData({...formData, sectors: formData.sectors.filter(x => x !== s)});
  const resetForm = () => { setFormData(initialForm); setEditingId(null); setNewSector(''); };

  if (loading) return <div className="p-4 md:p-8" data-testid="warehouses-loading"><div className="animate-pulse"><div className="h-8 bg-zinc-200 rounded w-64 mb-4" /><div className="h-64 bg-zinc-200 rounded" /></div></div>;

  return (
    <div className="p-4 md:p-8" data-testid="warehouses-page">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl md:text-4xl font-semibold font-primary text-zinc-900 tracking-tight">Depositos</h1>
          <p className="mt-1 text-sm text-zinc-600">PAI (almoxarifado central) recebe notas. FILHO consome via requisicoes.</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(o) => { setDialogOpen(o); if (!o) resetForm(); }}>
          <DialogTrigger asChild>
            <Button data-testid="add-warehouse-button" className="bg-blue-600 hover:bg-blue-700 text-white"><Plus className="h-4 w-4 mr-2" />Novo Deposito</Button>
          </DialogTrigger>
          <DialogContent className="max-h-[90vh] overflow-y-auto">
            <DialogHeader><DialogTitle>{editingId ? 'Editar Deposito' : 'Novo Deposito'}</DialogTitle></DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">Tipo</label>
                <Select value={formData.type} onValueChange={v => setFormData({...formData, type: v, parent_id: v === 'pai' ? '' : formData.parent_id})}>
                  <SelectTrigger data-testid="warehouse-type-select"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pai">PAI - Almoxarifado Central</SelectItem>
                    <SelectItem value="filho">FILHO - Setor Operacional</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-[11px] text-zinc-500 mt-1">{formData.type === 'pai' ? 'Recebe notas fiscais e aprova requisicoes' : 'Cria requisicoes ao deposito PAI'}</p>
              </div>
              {formData.type === 'filho' && (
                <div>
                  <label className="block text-sm font-medium text-zinc-700 mb-1.5">Deposito PAI vinculado</label>
                  <Select value={formData.parent_id} onValueChange={v => setFormData({...formData, parent_id: v})}>
                    <SelectTrigger data-testid="warehouse-parent-select"><SelectValue placeholder="Selecione o PAI" /></SelectTrigger>
                    <SelectContent>
                      {paiList.length === 0 && <div className="px-3 py-2 text-xs text-zinc-500">Crie um PAI primeiro</div>}
                      {paiList.map(p => <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">Nome</label>
                <Input data-testid="warehouse-name-input" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} required />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">Localidade</label>
                <Input data-testid="warehouse-location-input" value={formData.location} onChange={e => setFormData({...formData, location: e.target.value})} required />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">Descricao</label>
                <Input value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">Setores</label>
                <div className="flex gap-2 mb-2">
                  <Input data-testid="warehouse-sector-input" placeholder="Nome do setor" value={newSector} onChange={e => setNewSector(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addSector(); } }} />
                  <Button type="button" onClick={addSector} variant="outline" size="sm" data-testid="warehouse-add-sector-button">Adicionar</Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {formData.sectors.map(s => (
                    <span key={s} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                      {s}<button type="button" onClick={() => removeSector(s)} className="hover:text-red-600"><X className="h-3 w-3" /></button>
                    </span>
                  ))}
                </div>
              </div>
              <Button data-testid="warehouse-submit-button" type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white">{editingId ? 'Atualizar' : 'Criar'} Deposito</Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {warehouses.length === 0 && <div className="col-span-full bg-white rounded-xl border border-zinc-200 shadow-sm p-8 text-center text-zinc-500" data-testid="warehouses-empty">Nenhum deposito ainda. Crie um PAI para comecar.</div>}
        {warehouses.map(w => {
          const isPai = w.type === 'pai';
          const parent = w.parent_id ? paiById(w.parent_id) : null;
          return (
            <div key={w.id} data-testid={`warehouse-card-${w.id}`} className="bg-white rounded-xl border border-zinc-200 shadow-sm p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div className={`h-9 w-9 rounded-lg ${isPai ? 'bg-purple-50' : 'bg-blue-50'} flex items-center justify-center`}>
                  {isPai ? <Crown className="h-5 w-5 text-purple-600" /> : <GitBranch className="h-5 w-5 text-blue-600" />}
                </div>
                <div className="flex gap-1">
                  <button onClick={() => handleEdit(w)} data-testid={`edit-warehouse-${w.id}`} className="p-1.5 text-zinc-600 hover:bg-zinc-100 rounded-lg"><Pencil className="h-4 w-4" /></button>
                  <button onClick={() => handleDelete(w.id)} data-testid={`delete-warehouse-${w.id}`} className="p-1.5 text-red-600 hover:bg-red-50 rounded-lg"><Trash2 className="h-4 w-4" /></button>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-semibold text-zinc-900">{w.name}</h3>
                <span className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${isPai ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'}`}>{w.type}</span>
              </div>
              <p className="text-sm text-zinc-600 mt-0.5">{w.location}</p>
              {parent && <p className="text-xs text-zinc-500 mt-1">Vinculado ao PAI: <strong>{parent.name}</strong></p>}
              {w.description && <p className="text-xs text-zinc-500 mt-1">{w.description}</p>}
              {(w.sectors || []).length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1">
                  {w.sectors.map(s => <span key={s} className="px-2 py-0.5 rounded-full text-xs bg-zinc-100 text-zinc-700">{s}</span>)}
                </div>
              )}
              <div className="mt-3 pt-2 border-t border-zinc-100 flex items-center justify-between">
                <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${w.active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>{w.active ? 'Ativo' : 'Inativo'}</span>
                <button onClick={() => handleToggleActive(w.id, w.active)} data-testid={`toggle-warehouse-${w.id}`} className="text-xs text-blue-600 hover:underline">{w.active ? 'Desativar' : 'Ativar'}</button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
