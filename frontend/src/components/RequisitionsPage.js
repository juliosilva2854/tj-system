import React, { useState, useEffect } from 'react';
import { requisitionsAPI, inventoryAPI, warehousesAPI } from '../api';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { ArrowLeftRight, Plus, Check, X, Clock, CheckCircle2, XCircle } from 'lucide-react';
import { toast } from 'sonner';

const STATUS_LABEL = { pending: 'Pendente', approved: 'Aprovada', rejected: 'Rejeitada' };
const STATUS_COLOR = { pending: 'bg-yellow-100 text-yellow-700', approved: 'bg-green-100 text-green-700', rejected: 'bg-red-100 text-red-700' };
const STATUS_ICON = { pending: Clock, approved: CheckCircle2, rejected: XCircle };

const getCurrentUser = () => { try { return JSON.parse(localStorage.getItem('user') || '{}'); } catch { return {}; } };

export const RequisitionsPage = () => {
  const [reqs, setReqs] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [items, setItems] = useState([{ product_id: '', product_name: '', quantity: 1 }]);
  const [notes, setNotes] = useState('');
  const me = getCurrentUser();
  const canCreate = ['operacional', 'admin'].includes(me.role);
  const canApprove = ['master', 'admin', 'logistica'].includes(me.role);

  useEffect(() => { load(); }, []);

  const load = async () => {
    try {
      const [r, w, i] = await Promise.all([
        requisitionsAPI.getAll(),
        warehousesAPI.getAll(),
        inventoryAPI.getAll(),
      ]);
      setReqs(r.data); setWarehouses(w.data); setInventory(i.data);
    } catch { toast.error('Erro ao carregar requisicoes'); }
    finally { setLoading(false); }
  };

  // For operacional - find their PAI inventory candidates via parent warehouse
  const myWh = warehouses.find(w => w.id === me.warehouse_id);
  const parentWhId = myWh?.parent_id || '';
  const paiInventory = inventory.filter(it => it.warehouse_id === parentWhId);
  // Distinct products in PAI
  const productOptions = paiInventory.map(it => ({ id: it.product_id, name: it.product_name, sku: it.product_sku, available: it.quantity }));

  const wName = (id) => warehouses.find(w => w.id === id)?.name || '—';

  const addItem = () => setItems([...items, { product_id: '', product_name: '', quantity: 1 }]);
  const updateItem = (idx, key, val) => {
    const next = [...items];
    next[idx][key] = val;
    if (key === 'product_id') {
      const p = productOptions.find(o => o.id === val);
      next[idx].product_name = p ? p.name : '';
    }
    setItems(next);
  };
  const removeItem = (idx) => setItems(items.filter((_, i) => i !== idx));

  const handleCreate = async (e) => {
    e.preventDefault();
    const validItems = items.filter(i => i.product_id && i.quantity > 0);
    if (!validItems.length) { toast.error('Adicione pelo menos um item'); return; }
    try {
      await requisitionsAPI.create({ items: validItems, notes });
      toast.success('Requisicao criada!');
      setDialogOpen(false);
      setItems([{ product_id: '', product_name: '', quantity: 1 }]);
      setNotes('');
      load();
    } catch (err) { toast.error(err.response?.data?.detail || 'Erro ao criar'); }
  };

  const handleApprove = async (id) => {
    if (!window.confirm('Aprovar esta requisicao? O estoque sera transferido do PAI para o FILHO.')) return;
    try { await requisitionsAPI.approve(id); toast.success('Requisicao aprovada e estoque transferido!'); load(); }
    catch (err) { toast.error(err.response?.data?.detail || 'Erro ao aprovar'); }
  };

  const handleReject = async (id) => {
    if (!window.confirm('Rejeitar esta requisicao?')) return;
    try { await requisitionsAPI.reject(id); toast.success('Requisicao rejeitada'); load(); }
    catch (err) { toast.error(err.response?.data?.detail || 'Erro ao rejeitar'); }
  };

  if (loading) return <div className="p-4 md:p-8" data-testid="requisitions-loading">Carregando...</div>;

  // operacional can only create if they're attached to a FILHO warehouse
  const operacionalEligible = me.role !== 'operacional' || (myWh && myWh.type === 'filho' && parentWhId);

  return (
    <div className="p-4 md:p-8" data-testid="requisitions-page">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl md:text-4xl font-semibold font-primary text-zinc-900 tracking-tight">Requisicoes de Insumos</h1>
          <p className="mt-1 text-sm text-zinc-600">FILHO solicita ao PAI. Logistica aprova e o estoque e transferido.</p>
        </div>
        {canCreate && (
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button data-testid="add-requisition-button" disabled={!operacionalEligible && me.role === 'operacional'} className="bg-blue-600 hover:bg-blue-700 text-white"><Plus className="h-4 w-4 mr-2" />Nova Requisicao</Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader><DialogTitle>Nova Requisicao</DialogTitle></DialogHeader>
              {!operacionalEligible && me.role === 'operacional' ? (
                <p className="text-sm text-red-600 p-3 bg-red-50 rounded">Voce precisa estar vinculado a um deposito FILHO com PAI definido.</p>
              ) : (
                <form onSubmit={handleCreate} className="space-y-4">
                  <div className="text-xs text-zinc-600 bg-zinc-50 p-3 rounded">
                    De: <strong>{wName(me.warehouse_id)}</strong> &rarr; Para: <strong>{wName(parentWhId) || '(PAI)'}</strong>
                  </div>
                  <div className="space-y-3">
                    {items.map((it, idx) => (
                      <div key={idx} className="flex gap-2 items-end" data-testid={`req-item-row-${idx}`}>
                        <div className="flex-1">
                          <label className="block text-xs font-medium text-zinc-700 mb-1">Produto (disponivel no PAI)</label>
                          <Select value={it.product_id} onValueChange={v => updateItem(idx, 'product_id', v)}>
                            <SelectTrigger data-testid={`req-product-select-${idx}`}><SelectValue placeholder="Selecione" /></SelectTrigger>
                            <SelectContent>
                              {productOptions.length === 0 && <div className="px-3 py-2 text-xs text-zinc-500">Nenhum produto no PAI</div>}
                              {productOptions.map(p => <SelectItem key={p.id} value={p.id}>{p.name} ({p.sku}) - {p.available} disp.</SelectItem>)}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="w-24">
                          <label className="block text-xs font-medium text-zinc-700 mb-1">Qtd</label>
                          <Input data-testid={`req-quantity-input-${idx}`} type="number" min="1" value={it.quantity} onChange={e => updateItem(idx, 'quantity', parseFloat(e.target.value) || 0)} />
                        </div>
                        {items.length > 1 && (
                          <button type="button" onClick={() => removeItem(idx)} className="p-2 text-red-600 hover:bg-red-50 rounded" data-testid={`req-remove-item-${idx}`}><X className="h-4 w-4" /></button>
                        )}
                      </div>
                    ))}
                  </div>
                  <Button type="button" variant="outline" onClick={addItem} data-testid="req-add-item-button" className="w-full">+ Adicionar item</Button>
                  <div>
                    <label className="block text-sm font-medium text-zinc-700 mb-1.5">Observacoes (opcional)</label>
                    <Input data-testid="req-notes-input" value={notes} onChange={e => setNotes(e.target.value)} placeholder="ex: urgente" />
                  </div>
                  <Button data-testid="req-submit-button" type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white">Enviar Requisicao</Button>
                </form>
              )}
            </DialogContent>
          </Dialog>
        )}
      </div>

      <div className="bg-white rounded-xl border border-zinc-200 shadow-sm overflow-x-auto">
        <table className="w-full min-w-[800px]" data-testid="requisitions-table">
          <thead className="bg-zinc-50 border-b border-zinc-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">Data</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">De (FILHO)</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">Para (PAI)</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">Itens</th>
              <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-zinc-500">Status</th>
              <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-zinc-500">Acoes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100">
            {reqs.length === 0 && <tr><td colSpan={6} className="px-4 py-8 text-center text-zinc-500" data-testid="requisitions-empty">Nenhuma requisicao registrada</td></tr>}
            {reqs.map(r => { const Icon = STATUS_ICON[r.status]; return (
              <tr key={r.id} className="hover:bg-zinc-50 transition-colors" data-testid={`requisition-row-${r.id}`}>
                <td className="px-4 py-3 text-sm text-zinc-600 whitespace-nowrap">{new Date(r.created_at).toLocaleString('pt-BR')}</td>
                <td className="px-4 py-3 text-sm text-zinc-900">{wName(r.from_warehouse_id)}</td>
                <td className="px-4 py-3 text-sm text-zinc-900">{wName(r.to_warehouse_id)}</td>
                <td className="px-4 py-3 text-xs text-zinc-700">
                  {r.items.map((i, k) => <div key={k}>{i.product_name} <span className="font-mono">×{i.quantity}</span></div>)}
                </td>
                <td className="px-4 py-3 text-center">
                  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLOR[r.status]}`}>
                    <Icon className="h-3 w-3" />{STATUS_LABEL[r.status]}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  {r.status === 'pending' && canApprove && (
                    <div className="flex items-center justify-end gap-1">
                      <button onClick={() => handleApprove(r.id)} data-testid={`approve-requisition-${r.id}`} title="Aprovar" className="p-1.5 text-green-600 hover:bg-green-50 rounded-lg"><Check className="h-4 w-4" /></button>
                      <button onClick={() => handleReject(r.id)} data-testid={`reject-requisition-${r.id}`} title="Rejeitar" className="p-1.5 text-red-600 hover:bg-red-50 rounded-lg"><X className="h-4 w-4" /></button>
                    </div>
                  )}
                </td>
              </tr>
            ); })}
          </tbody>
        </table>
      </div>
      <div className="mt-4 flex items-center gap-2 text-xs text-zinc-500">
        <ArrowLeftRight className="h-3.5 w-3.5" />
        Aprovacao transfere automaticamente o estoque do deposito PAI para o FILHO solicitante.
      </div>
    </div>
  );
};
