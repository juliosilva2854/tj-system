import React, { useState, useEffect } from 'react';
import { productsAPI, warehousesAPI } from '../api';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Search, ArrowRightLeft, Plus, Pencil } from 'lucide-react';
import { toast } from 'sonner';
import { canManageProducts } from '../auth';

const EMPTY_PRODUCT = { name: '', sku: '', description: '', category: '', unit: 'UN', cost_price: 0, min_stock: 0 };

export const ProductsPage = () => {
  const [products, setProducts] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [search, setSearch] = useState('');
  const [transferOpen, setTransferOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [transferData, setTransferData] = useState({ productId: '', productName: '', warehouseId: '', quantity: 1, sector: '', maxQty: 0 });
  // Criacao / Edicao de produtos
  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState(null); // null = criar; id = editar
  const [form, setForm] = useState({ ...EMPTY_PRODUCT });
  const [saving, setSaving] = useState(false);

  const canManage = canManageProducts();

  useEffect(() => { loadData(); }, []);
  useEffect(() => {
    const term = search.toLowerCase();
    setFiltered(products.filter(p => (p.name || '').toLowerCase().includes(term) || (p.sku || '').toLowerCase().includes(term)));
  }, [search, products]);

  const loadData = async () => {
    try {
      const [pR, wR] = await Promise.all([productsAPI.getAll(), warehousesAPI.getAll()]);
      setProducts(pR.data); setWarehouses(wR.data);
    } catch (err) { toast.error('Erro ao carregar'); } finally { setLoading(false); }
  };

  // ===== Transferencia para deposito =====
  const handleTransfer = async (e) => {
    e.preventDefault();
    if (!transferData.warehouseId) { toast.error('Selecione o deposito'); return; }
    if (transferData.quantity <= 0 || transferData.quantity > transferData.maxQty) { toast.error(`Quantidade deve ser entre 1 e ${transferData.maxQty}`); return; }
    try {
      const res = await productsAPI.transfer(transferData.productId, transferData.warehouseId, transferData.quantity, transferData.sector);
      toast.success(res.data.message);
      setTransferOpen(false);
      loadData();
    } catch (err) { toast.error(err.response?.data?.detail || 'Erro na transferencia'); }
  };

  const openTransfer = (p) => {
    setTransferData({ productId: p.id, productName: p.name, warehouseId: '', quantity: p.available_qty || 0, sector: '', maxQty: p.available_qty || 0 });
    setTransferOpen(true);
  };

  const getSectors = (wid) => {
    const w = warehouses.find(x => x.id === wid);
    return w?.sectors || [];
  };

  // ===== Criar / Editar produto =====
  const openCreate = () => { setEditingId(null); setForm({ ...EMPTY_PRODUCT }); setFormOpen(true); };
  const openEdit = (p) => {
    setEditingId(p.id);
    setForm({
      name: p.name || '', sku: p.sku || '', description: p.description || '',
      category: p.category || '', unit: p.unit || 'UN',
      cost_price: p.cost_price || 0, min_stock: p.min_stock || 0,
    });
    setFormOpen(true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) { toast.error('Informe o nome do produto'); return; }
    if (!form.sku.trim()) { toast.error('Informe o SKU do produto'); return; }
    const payload = {
      name: form.name.trim(), sku: form.sku.trim(),
      description: form.description?.trim() || '', category: form.category?.trim() || '',
      unit: form.unit?.trim() || 'UN',
      cost_price: parseFloat(form.cost_price) || 0, min_stock: parseFloat(form.min_stock) || 0,
    };
    setSaving(true);
    try {
      if (editingId) {
        await productsAPI.update(editingId, payload);
        toast.success('Produto atualizado!');
      } else {
        await productsAPI.create(payload);
        toast.success('Produto criado!');
      }
      setFormOpen(false);
      loadData();
    } catch (err) { toast.error(err.response?.data?.detail || 'Erro ao salvar produto'); }
    finally { setSaving(false); }
  };

  if (loading) return <div className="p-4 md:p-8"><div className="animate-pulse"><div className="h-8 bg-zinc-200 rounded w-64 mb-4" /><div className="h-64 bg-zinc-200 rounded" /></div></div>;

  return (
    <div className="p-4 md:p-8" data-testid="products-page">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl md:text-4xl font-semibold font-primary text-zinc-900 tracking-tight">Produtos</h1>
          <p className="mt-1 text-sm text-zinc-600">Cadastro de produtos. Crie manualmente ou importe via nota fiscal e transfira para o deposito.</p>
        </div>
        {canManage && (
          <Button onClick={openCreate} data-testid="new-product-button" className="bg-blue-600 hover:bg-blue-700 text-white">
            <Plus className="h-4 w-4 mr-2" />Novo Produto
          </Button>
        )}
      </div>

      {/* Modal Transferir */}
      <Dialog open={transferOpen} onOpenChange={setTransferOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Transferir para Deposito</DialogTitle></DialogHeader>
          <p className="text-sm text-zinc-600 mb-2">Produto: <strong>{transferData.productName}</strong></p>
          <p className="text-sm text-zinc-500 mb-4">Disponivel: {transferData.maxQty} unidades</p>
          <form onSubmit={handleTransfer} className="space-y-4">
            <div><label className="block text-sm font-medium text-zinc-700 mb-1">Deposito</label>
              <Select value={transferData.warehouseId} onValueChange={v => setTransferData({...transferData, warehouseId: v, sector: ''})}>
                <SelectTrigger><SelectValue placeholder="Selecione o deposito" /></SelectTrigger>
                <SelectContent>{warehouses.map(w => <SelectItem key={w.id} value={w.id}>{w.name}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            {transferData.warehouseId && getSectors(transferData.warehouseId).length > 0 && (
              <div><label className="block text-sm font-medium text-zinc-700 mb-1">Setor</label>
                <Select value={transferData.sector} onValueChange={v => setTransferData({...transferData, sector: v})}>
                  <SelectTrigger><SelectValue placeholder="Selecione o setor" /></SelectTrigger>
                  <SelectContent>{getSectors(transferData.warehouseId).map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
                </Select>
              </div>
            )}
            <div><label className="block text-sm font-medium text-zinc-700 mb-1">Quantidade</label>
              <Input type="number" min="1" max={transferData.maxQty} value={transferData.quantity} onChange={e => setTransferData({...transferData, quantity: parseFloat(e.target.value) || 0})} required />
            </div>
            <p className="text-xs text-zinc-500">Ao transferir toda a quantidade, o produto vai para o estoque do deposito.</p>
            <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white">Transferir para Deposito</Button>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal Criar / Editar produto */}
      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>{editingId ? 'Editar Produto' : 'Novo Produto'}</DialogTitle></DialogHeader>
          <form onSubmit={handleSave} className="space-y-4" data-testid="product-form">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-zinc-700 mb-1">Nome *</label>
                <Input data-testid="product-name-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Nome do produto" required />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1">SKU *</label>
                <Input data-testid="product-sku-input" value={form.sku} onChange={e => setForm({ ...form, sku: e.target.value })} placeholder="Codigo/SKU" className="font-mono" required />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1">Unidade</label>
                <Input data-testid="product-unit-input" value={form.unit} onChange={e => setForm({ ...form, unit: e.target.value })} placeholder="UN, KG, CX..." />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1">Categoria</label>
                <Input data-testid="product-category-input" value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} placeholder="Categoria" />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1">Custo Unit. (R$)</label>
                <Input type="number" min="0" step="0.01" data-testid="product-cost-input" value={form.cost_price} onChange={e => setForm({ ...form, cost_price: e.target.value })} />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1">Estoque Minimo</label>
                <Input type="number" min="0" step="0.01" data-testid="product-minstock-input" value={form.min_stock} onChange={e => setForm({ ...form, min_stock: e.target.value })} />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-zinc-700 mb-1">Descricao</label>
                <Input data-testid="product-description-input" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} placeholder="Descricao (opcional)" />
              </div>
            </div>
            <Button type="submit" disabled={saving} data-testid="product-save-button" className="w-full bg-blue-600 hover:bg-blue-700 text-white">
              {saving ? 'Salvando...' : (editingId ? 'Salvar Alteracoes' : 'Criar Produto')}
            </Button>
          </form>
        </DialogContent>
      </Dialog>

      <div className="mb-4 relative"><Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" /><Input placeholder="Buscar por nome ou SKU..." value={search} onChange={e => setSearch(e.target.value)} className="pl-10" /></div>

      {filtered.length === 0 ? (
        <div className="bg-white rounded-xl border border-zinc-200 shadow-sm p-8 text-center text-zinc-500">
          Nenhum produto cadastrado. Clique em "Novo Produto" ou importe uma nota fiscal.
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-zinc-200 shadow-sm overflow-x-auto">
          <table className="w-full min-w-[600px]" data-testid="products-table">
            <thead className="bg-zinc-50 border-b border-zinc-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">SKU</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">Nome</th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-zinc-500">Custo Unit.</th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-zinc-500">Qtd Disponivel</th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-zinc-500">Acoes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {filtered.map(p => (
                <tr key={p.id} className="hover:bg-zinc-50 transition-colors" data-testid={`product-row-${p.id}`}>
                  <td className="px-4 py-3 text-sm font-mono text-zinc-800">{p.sku}</td>
                  <td className="px-4 py-3 text-sm font-medium text-zinc-900">{p.name}</td>
                  <td className="px-4 py-3 text-sm font-mono text-zinc-800 text-right">R$ {(p.cost_price || 0).toFixed(2)}</td>
                  <td className="px-4 py-3 text-sm font-mono text-zinc-800 text-right font-semibold">{p.available_qty || 0}</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {canManage && (
                        <Button onClick={() => openEdit(p)} size="sm" variant="outline" data-testid={`edit-product-${p.id}`} className="text-zinc-700 border-zinc-200 hover:bg-zinc-50">
                          <Pencil className="h-4 w-4 mr-1" />Editar
                        </Button>
                      )}
                      {(p.available_qty || 0) > 0 && (
                        <Button onClick={() => openTransfer(p)} size="sm" variant="outline" data-testid={`transfer-product-${p.id}`} className="text-blue-600 border-blue-200 hover:bg-blue-50">
                          <ArrowRightLeft className="h-4 w-4 mr-1" />Transferir
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
