import React, { useState, useEffect } from 'react';
import { tenantsAPI } from '../api';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Plus, Building2 } from 'lucide-react';
import { toast } from 'sonner';

export const TenantsPage = () => {
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({ name: '', slug: '' });

  useEffect(() => { load(); }, []);
  const load = async () => {
    try { const r = await tenantsAPI.getAll(); setTenants(r.data); }
    catch { toast.error('Erro ao carregar estabelecimentos'); }
    finally { setLoading(false); }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await tenantsAPI.create(formData);
      toast.success('Estabelecimento criado!');
      setDialogOpen(false);
      setFormData({ name: '', slug: '' });
      load();
    } catch (err) { toast.error(err.response?.data?.detail || 'Erro ao criar'); }
  };

  if (loading) return <div className="p-4 md:p-8" data-testid="tenants-loading">Carregando...</div>;

  return (
    <div className="p-4 md:p-8" data-testid="tenants-page">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl md:text-4xl font-semibold font-primary text-zinc-900 tracking-tight">Estabelecimentos</h1>
          <p className="mt-1 text-sm text-zinc-600">Gerencie unidades (tenants) da plataforma SaaS</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button data-testid="add-tenant-button" className="bg-indigo-600 hover:bg-indigo-700 text-white"><Plus className="h-4 w-4 mr-2" />Novo Estabelecimento</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Novo Estabelecimento</DialogTitle></DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">Nome</label>
                <Input data-testid="tenant-name-input" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} required />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">Slug (subdominio)</label>
                <Input data-testid="tenant-slug-input" value={formData.slug} onChange={e => setFormData({...formData, slug: e.target.value.toLowerCase()})} required placeholder="ex: tj, unidade2" />
                <p className="text-[11px] text-zinc-500 mt-1">Apenas letras minusculas, numeros e hifen. Sera usado em subdominios.</p>
              </div>
              <Button data-testid="tenant-submit-button" type="submit" className="w-full bg-indigo-600 hover:bg-indigo-700 text-white">Criar</Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {tenants.length === 0 && (
          <div className="col-span-full bg-white rounded-xl border border-zinc-200 shadow-sm p-8 text-center text-zinc-500" data-testid="tenants-empty">
            Nenhum estabelecimento. Crie o primeiro para comecar.
          </div>
        )}
        {tenants.map(t => (
          <div key={t.id} className="bg-white rounded-xl border border-zinc-200 shadow-sm p-5" data-testid={`tenant-card-${t.id}`}>
            <div className="flex items-start justify-between mb-3">
              <div className="h-9 w-9 rounded-lg bg-indigo-50 flex items-center justify-center"><Building2 className="h-5 w-5 text-indigo-600" /></div>
              <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${t.active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>{t.active ? 'Ativo' : 'Inativo'}</span>
            </div>
            <h3 className="text-base font-semibold text-zinc-900">{t.name}</h3>
            <p className="text-xs text-zinc-500 mt-0.5">slug: <span className="font-mono">{t.slug}</span></p>
            <p className="text-[11px] text-zinc-400 mt-1 break-all">{t.slug}.sconnecta.com.br</p>
            <p className="text-[11px] text-zinc-400 mt-2">ID: <span className="font-mono">{t.id}</span></p>
          </div>
        ))}
      </div>
    </div>
  );
};
