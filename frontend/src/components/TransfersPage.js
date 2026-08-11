import React, { useEffect, useState, useMemo } from 'react';
import { transfersAPI, warehousesAPI, storesAPI, inventoryAPI } from '../api';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { ArrowLeftRight, Plus, ArrowRight, CheckCircle2, X } from 'lucide-react';
import { toast } from 'sonner';
import { getUser, canManageTransfers } from '../auth';

export const TransfersPage = () => {
  const me = getUser() || {};
  const [transfers, setTransfers] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [stores, setStores] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [items, setItems] = useState([{ product_id: '', product_name: '', quantity: 1 }]);
  const [notes, setNotes] = useState('');

  const canCreate = canManageTransfers();

  const load = async () => {
    try {
      const [t, w, s, i] = await Promise.all([
        transfersAPI.getAll(), warehousesAPI.getAll(), storesAPI.getAll(), inventoryAPI.getAll()
      ]);
      setTransfers(t.data); setWarehouses(w.data); setStores(s.data); setInventory(i.data);
    } catch { toast.error('Erro ao carregar transferencias'); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const pais = warehouses.filter(w => w.type === 'pai');
  const fromInventory = useMemo(() => inventory.filter(i => i.warehouse_id === from), [inventory, from]);
  const wName = (id) => warehouses.find(w => w.id === id)?.name || '—';
  const sName = (id) => stores.find(s => s.id === id)?.name || '—';

  const reset = () => { setFrom(''); setTo(''); setItems([{ product_id: '', product_name: '', quantity: 1 }]); setNotes(''); };

  const addItem = () => setItems([...items, { product_id: '', product_name: '', quantity: 1 }]);
  const removeItem = (idx) => setItems(items.filter((_, i) => i !== idx));
  const updateItem = (idx, k, v) => {
    const next = [...items];
    next[idx][k] = v;
    if (k === 'product_id') {
      const p = fromInventory.find(i => i.product_id === v);
      next[idx].product_name = p?.product_name || '';
    }
    setItems(next);
  };

  const submit = async () => {
    if (!from || !to) return toast.error('Selecione origem e destino');
    if (from === to) return toast.error('Origem e destino devem ser diferentes');
    const valid = items.filter(i => i.product_id && i.quantity > 0);
    if (valid.length === 0) return toast.error('Adicione ao menos 1 item');
    try {
      await transfersAPI.create({ from_warehouse_id: from, to_warehouse_id: to, items: valid, notes });
      toast.success('Transferencia realizada');
      setOpen(false); reset(); load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Erro ao transferir'); }
  };

  if (loading) return <div className="p-6 text-zinc-500">Carregando...</div>;

  return (
    <div className="p-6 space-y-4" data-testid="transfers-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-zinc-900 flex items-center gap-2"><ArrowLeftRight className="h-6 w-6 text-blue-600" />Transferencias entre Lojas</h1>
          <p className="text-sm text-zinc-500">Mover estoque de um Almoxarifado (PAI) para outro dentro do mesmo estabelecimento.</p>
        </div>
        {canCreate && (
          <Dialog open={open} onOpenChange={(v) => { setOpen(v); if (!v) reset(); }}>
            <DialogTrigger asChild>
              <Button className="bg-blue-600 hover:bg-blue-700 text-white" data-testid="new-transfer-btn"><Plus className="h-4 w-4 mr-1" />Nova transferencia</Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader><DialogTitle>Nova transferencia entre lojas</DialogTitle></DialogHeader>
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-medium text-zinc-600 mb-1 block">De (loja origem)</label>
                    <Select value={from} onValueChange={setFrom}>
                      <SelectTrigger data-testid="transfer-from"><SelectValue placeholder="Almoxarifado origem" /></SelectTrigger>
                      <SelectContent>{pais.map(w => <SelectItem key={w.id} value={w.id}>{w.name} ({sName(w.store_id)})</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-zinc-600 mb-1 block">Para (loja destino)</label>
                    <Select value={to} onValueChange={setTo}>
                      <SelectTrigger data-testid="transfer-to"><SelectValue placeholder="Almoxarifado destino" /></SelectTrigger>
                      <SelectContent>{pais.filter(w => w.id !== from).map(w => <SelectItem key={w.id} value={w.id}>{w.name} ({sName(w.store_id)})</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <label className="text-xs font-medium text-zinc-600 mb-1 block">Itens</label>
                  {items.map((it, idx) => (
                    <div key={idx} className="flex gap-2 items-end mb-2">
                      <div className="flex-1">
                        <Select value={it.product_id} onValueChange={(v) => updateItem(idx, 'product_id', v)} disabled={!from}>
                          <SelectTrigger data-testid={`transfer-item-${idx}`}><SelectValue placeholder={from ? 'Produto na origem' : 'Selecione origem primeiro'} /></SelectTrigger>
                          <SelectContent>
                            {fromInventory.map(i => <SelectItem key={i.product_id} value={i.product_id}>{i.product_name} (disp: {i.quantity})</SelectItem>)}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="w-24">
                        <Input type="number" min="0.01" step="0.01" value={it.quantity} onChange={e => updateItem(idx, 'quantity', parseFloat(e.target.value) || 0)} />
                      </div>
                      {items.length > 1 && <button onClick={() => removeItem(idx)} className="p-2 text-red-500 hover:bg-red-50 rounded"><X className="h-4 w-4" /></button>}
                    </div>
                  ))}
                  <button type="button" onClick={addItem} className="text-sm text-blue-600 hover:underline">+ Adicionar item</button>
                </div>

                <Input placeholder="Observacoes (opcional)" value={notes} onChange={e => setNotes(e.target.value)} />
                <Button onClick={submit} className="w-full bg-blue-600 hover:bg-blue-700 text-white" data-testid="submit-transfer-btn">Executar transferencia</Button>
              </div>
            </DialogContent>
          </Dialog>
        )}
      </div>

      <div className="bg-white rounded-lg border border-zinc-200 overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-zinc-50 text-zinc-600 text-xs uppercase">
            <tr>
              <th className="px-4 py-2 text-left">Data</th>
              <th className="px-4 py-2 text-left">Origem</th>
              <th className="px-4 py-2"></th>
              <th className="px-4 py-2 text-left">Destino</th>
              <th className="px-4 py-2 text-left">Itens</th>
              <th className="px-4 py-2 text-left">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100">
            {transfers.length === 0 && <tr><td colSpan="6" className="px-4 py-6 text-center text-zinc-500">Nenhuma transferencia ainda</td></tr>}
            {transfers.map(t => (
              <tr key={t.id} data-testid={`transfer-row-${t.id}`}>
                <td className="px-4 py-2 text-zinc-600">{new Date(t.created_at).toLocaleString('pt-BR')}</td>
                <td className="px-4 py-2">
                  <div className="font-medium text-zinc-900">{wName(t.from_warehouse_id)}</div>
                  <div className="text-xs text-zinc-500">{sName(t.from_store_id)}</div>
                </td>
                <td className="px-4 py-2"><ArrowRight className="h-4 w-4 text-zinc-400" /></td>
                <td className="px-4 py-2">
                  <div className="font-medium text-zinc-900">{wName(t.to_warehouse_id)}</div>
                  <div className="text-xs text-zinc-500">{sName(t.to_store_id)}</div>
                </td>
                <td className="px-4 py-2 text-zinc-700">{t.items.length} item(ns)</td>
                <td className="px-4 py-2">
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-700">
                    <CheckCircle2 className="h-3 w-3" />Concluida
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
