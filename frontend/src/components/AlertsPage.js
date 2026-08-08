import React, { useState, useEffect } from 'react';
import { notificationsAPI, productsAPI, inventoryAPI } from '../api';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Bell, CheckCheck, Package, SlidersHorizontal, Mail, Monitor } from 'lucide-react';
import { toast } from 'sonner';

export const AlertsPage = () => {
  const [notifications, setNotifications] = useState([]);
  const [products, setProducts] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stockDialogOpen, setStockDialogOpen] = useState(false);
  const [stockForm, setStockForm] = useState({ productId: '', minStock: 0, productName: '' });
  const [prefEvents, setPrefEvents] = useState([]);
  const [prefs, setPrefs] = useState({});
  const [savingPrefs, setSavingPrefs] = useState(false);
  const notifColors = { info: 'bg-blue-100 text-blue-700', warning: 'bg-yellow-100 text-yellow-700', error: 'bg-red-100 text-red-700', success: 'bg-green-100 text-green-700' };

  useEffect(() => { loadData(); loadPrefs(); }, []);

  const loadData = async () => {
    try {
      const [n, i] = await Promise.all([notificationsAPI.getAll(), inventoryAPI.getAll()]);
      setNotifications(n.data); setInventory(i.data);
      const productMap = {};
      i.data.forEach(item => {
        if (!productMap[item.product_id]) productMap[item.product_id] = { id: item.product_id, name: item.product_name, min_stock: item.min_stock || 0, warehouses: [] };
        productMap[item.product_id].warehouses.push({ warehouse: item.warehouse_name, qty: item.quantity });
      });
      setProducts(Object.values(productMap));
    } catch (err) {
      console.error('Erro ao carregar alertas:', err);
    } finally { setLoading(false); }
  };

  const loadPrefs = async () => {
    try {
      const r = await notificationsAPI.getPreferences();
      setPrefEvents(r.data.events || []);
      setPrefs(r.data.preferences || {});
    } catch (err) {
      console.error('Erro ao carregar preferencias:', err);
    }
  };

  const handleMarkRead = async (id) => { await notificationsAPI.markRead(id); loadData(); };
  const handleMarkAllRead = async () => { await notificationsAPI.markAllRead(); toast.success('Todas marcadas como lidas'); loadData(); };

  const togglePref = (eventKey, channel) => {
    setPrefs(prev => ({
      ...prev,
      [eventKey]: { ...prev[eventKey], [channel]: !prev[eventKey]?.[channel] },
    }));
  };

  const savePrefs = async () => {
    setSavingPrefs(true);
    try {
      await notificationsAPI.updatePreferences(prefs);
      toast.success('Preferencias de notificacao salvas');
    } catch (err) {
      toast.error('Erro ao salvar preferencias');
    } finally { setSavingPrefs(false); }
  };

  const handleSetMinStock = async (e) => {
    e.preventDefault();
    try {
      await productsAPI.update(stockForm.productId, { min_stock: stockForm.minStock });
      toast.success(`Estoque minimo de "${stockForm.productName}" configurado para ${stockForm.minStock}`);
      setStockDialogOpen(false);
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao configurar estoque minimo');
    }
  };

  if (loading) return <div className="p-4 md:p-8">Carregando...</div>;
  return (
    <div className="p-4 md:p-8" data-testid="alerts-page">
      <div className="mb-6">
        <h1 className="text-2xl md:text-4xl font-semibold font-primary text-zinc-900 tracking-tight">Alertas e Notificacoes</h1>
        <p className="mt-1 text-sm text-zinc-600">Caixa de entrada, estoque minimo e suas preferencias de notificacao</p>
      </div>
      <Tabs defaultValue="notifications" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="notifications" data-testid="tab-notifications"><Bell className="h-4 w-4 mr-1" />Caixa ({notifications.filter(n => !n.read).length})</TabsTrigger>
          <TabsTrigger value="stock" data-testid="tab-stock"><Package className="h-4 w-4 mr-1" />Estoque Minimo</TabsTrigger>
          <TabsTrigger value="preferences" data-testid="tab-preferences"><SlidersHorizontal className="h-4 w-4 mr-1" />Preferencias</TabsTrigger>
        </TabsList>

        <TabsContent value="notifications">
          <div className="bg-white rounded-xl border border-zinc-200 shadow-sm">
            <div className="flex items-center justify-between p-4 border-b border-zinc-200">
              <h2 className="text-lg font-semibold text-zinc-900">Caixa de Entrada</h2>
              <Button variant="outline" size="sm" onClick={handleMarkAllRead} data-testid="mark-all-read-btn"><CheckCheck className="h-4 w-4 mr-1" />Marcar todas lidas</Button>
            </div>
            <div className="divide-y divide-zinc-100">
              {notifications.length === 0 ? <div className="p-8 text-center text-zinc-500" data-testid="empty-notifications">Nenhuma notificacao</div> :
                notifications.map(n => (
                  <div key={n.id} className={`p-4 flex items-start gap-3 ${!n.read ? 'bg-blue-50/50' : ''} hover:bg-zinc-50`} data-testid="notification-item">
                    <div className={`h-8 w-8 rounded-full flex items-center justify-center flex-shrink-0 ${notifColors[n.type] || notifColors.info}`}><Bell className="h-4 w-4" /></div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-zinc-900">{n.title}</p>
                      <p className="text-sm text-zinc-600 mt-0.5">{n.message}</p>
                      <p className="text-xs text-zinc-400 mt-1">{new Date(n.created_at).toLocaleString('pt-BR')}</p>
                    </div>
                    {!n.read && <button onClick={() => handleMarkRead(n.id)} className="text-xs text-blue-600 hover:underline">Lida</button>}
                  </div>
                ))}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="stock">
          <div className="bg-white rounded-xl border border-zinc-200 shadow-sm p-5 mb-4">
            <h2 className="text-lg font-semibold text-zinc-900 mb-2">Configurar Estoque Minimo</h2>
            <p className="text-sm text-zinc-600">Selecione um produto do estoque e defina a quantidade minima. Quando atingir esse valor, uma notificacao automatica sera gerada.</p>
          </div>
          <div className="bg-white rounded-xl border border-zinc-200 shadow-sm overflow-x-auto">
            <table className="w-full min-w-[500px]">
              <thead className="bg-zinc-50 border-b border-zinc-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-zinc-500">Produto</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-zinc-500">Depositos</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-zinc-500">Estoque Min.</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-zinc-500">Acao</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {products.length === 0 ? <tr><td colSpan={4} className="px-4 py-8 text-center text-zinc-500">Nenhum produto no estoque. Transfira produtos da aba Produtos primeiro.</td></tr> :
                  products.map(p => (
                    <tr key={p.id} className="hover:bg-zinc-50">
                      <td className="px-4 py-3 text-sm font-medium text-zinc-900">{p.name}</td>
                      <td className="px-4 py-3 text-sm text-zinc-600">{p.warehouses.map(w => `${w.warehouse} (${w.qty})`).join(', ')}</td>
                      <td className="px-4 py-3 text-sm font-mono text-right">{p.min_stock || 0}</td>
                      <td className="px-4 py-3 text-right">
                        <button onClick={() => { setStockForm({ productId: p.id, minStock: p.min_stock || 0, productName: p.name }); setStockDialogOpen(true); }} className="text-xs text-blue-600 hover:underline font-medium">Configurar</button>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
          <Dialog open={stockDialogOpen} onOpenChange={setStockDialogOpen}>
            <DialogContent>
              <DialogHeader><DialogTitle>Configurar Estoque Minimo</DialogTitle></DialogHeader>
              <p className="text-sm text-zinc-600 mb-2">Produto: <strong>{stockForm.productName}</strong></p>
              <form onSubmit={handleSetMinStock} className="space-y-4">
                <div><label className="block text-sm font-medium text-zinc-700 mb-1">Quantidade minima para alerta</label>
                  <Input type="number" min="0" value={stockForm.minStock} onChange={e => setStockForm({...stockForm, minStock: parseFloat(e.target.value) || 0})} required />
                </div>
                <p className="text-xs text-zinc-500">Quando o estoque ficar igual ou abaixo deste valor, uma notificacao sera gerada.</p>
                <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white" data-testid="save-min-stock-btn">Salvar</Button>
              </form>
            </DialogContent>
          </Dialog>
        </TabsContent>

        <TabsContent value="preferences">
          <div className="bg-white rounded-xl border border-zinc-200 shadow-sm p-5 mb-4">
            <h2 className="text-lg font-semibold text-zinc-900 mb-2">Minhas Preferencias de Notificacao</h2>
            <p className="text-sm text-zinc-600">Escolha para cada tipo de evento se quer receber notificacao no sistema (sino) e/ou por email. Estas configuracoes sao individuais, apenas suas.</p>
          </div>
          <div className="bg-white rounded-xl border border-zinc-200 shadow-sm divide-y divide-zinc-100" data-testid="preferences-list">
            {prefEvents.length === 0 ? <div className="p-8 text-center text-zinc-500">Nenhum evento configuravel.</div> :
              prefEvents.map(ev => {
                const p = prefs[ev.key] || { in_app: true, email: false };
                return (
                  <div key={ev.key} className="p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3" data-testid={`pref-${ev.key}`}>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-zinc-900">{ev.label}</p>
                      <p className="text-xs text-zinc-500 mt-0.5">{ev.description}</p>
                    </div>
                    <div className="flex items-center gap-4">
                      <label className="flex items-center gap-2 cursor-pointer text-sm text-zinc-700" data-testid={`pref-${ev.key}-in_app`}>
                        <Monitor className="h-4 w-4 text-zinc-400" />
                        <span className="hidden sm:inline">Sistema</span>
                        <input type="checkbox" checked={!!p.in_app} onChange={() => togglePref(ev.key, 'in_app')} className="h-4 w-4 accent-blue-600" />
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer text-sm text-zinc-700" data-testid={`pref-${ev.key}-email`}>
                        <Mail className="h-4 w-4 text-zinc-400" />
                        <span className="hidden sm:inline">Email</span>
                        <input type="checkbox" checked={!!p.email} onChange={() => togglePref(ev.key, 'email')} className="h-4 w-4 accent-blue-600" />
                      </label>
                    </div>
                  </div>
                );
              })}
          </div>
          <div className="mt-4 flex justify-end">
            <Button onClick={savePrefs} disabled={savingPrefs} className="bg-blue-600 hover:bg-blue-700 text-white" data-testid="save-preferences-btn">
              {savingPrefs ? 'Salvando...' : 'Salvar Preferencias'}
            </Button>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};
