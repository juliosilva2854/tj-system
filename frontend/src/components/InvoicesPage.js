import React, { useState, useEffect } from 'react';
import { invoicesAPI } from '../api';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Plus, FileText, Image as ImageIcon, FileUp, Eye, Package } from 'lucide-react';
import { toast } from 'sonner';

export const InvoicesPage = () => {
  const [invoices, setInvoices] = useState([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [viewOpen, setViewOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('file');
  const [processing, setProcessing] = useState(false);
  const [formData, setFormData] = useState({ invoice_number: '', supplier_name: '', issue_date: '', total_value: 0, tax_value: 0, items: [] });

  useEffect(() => { loadData(); }, []);
  const loadData = async () => {
    try { const r = await invoicesAPI.getAll(); setInvoices(r.data); }
    catch (err) { toast.error('Erro ao carregar notas'); } finally { setLoading(false); }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]; if (!file) return;
    setProcessing(true);
    try {
      const res = await invoicesAPI.uploadFile(file);
      const d = res.data.data;
      setFormData({
        invoice_number: d.invoice_number || '', supplier_name: d.supplier_name || '', issue_date: d.issue_date || '',
        total_value: d.total_value || 0, tax_value: d.tax_value || 0,
        items: (d.items || []).map(it => ({ product_name: it.product_name || '', product_sku: it.product_sku || '', quantity: it.quantity || 0, unit_price: it.unit_price || 0, total: it.total || 0, tax: it.tax || 0 })),
      });
      toast.success('Arquivo processado!'); setActiveTab('review');
    } catch (err) { toast.error(err.response?.data?.detail || 'Erro ao processar'); }
    setProcessing(false); e.target.value = '';
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files[0]; if (!file) return;
    setProcessing(true);
    const reader = new FileReader();
    reader.onloadend = async () => {
      try {
        const res = await invoicesAPI.processOCR(reader.result.split(',')[1]);
        setFormData({
          invoice_number: res.data.invoice_number || '', supplier_name: res.data.supplier_name || '',
          issue_date: res.data.issue_date || '', total_value: res.data.total_value || 0, tax_value: res.data.tax_value || 0,
          items: (res.data.items || []).map(it => ({ product_name: it.product_name || '', product_sku: '', quantity: it.quantity || 0, unit_price: it.unit_price || 0, total: it.total || 0, tax: 0 })),
        });
        toast.success('Imagem processada!'); setActiveTab('review');
      } catch (err) { toast.error('Erro ao processar imagem'); }
      setProcessing(false);
    };
    reader.readAsDataURL(file); e.target.value = '';
  };

  const handleSave = async () => {
    try {
      await invoicesAPI.create({ ...formData, status: 'pending', type: 'entrada' });
      toast.success('Nota fiscal salva!'); setDialogOpen(false);
      setFormData({ invoice_number: '', supplier_name: '', issue_date: '', total_value: 0, tax_value: 0, items: [] }); setActiveTab('file');
      loadData();
    } catch (err) { toast.error('Erro ao salvar'); }
  };

  const handleProcessItems = async (invoiceId) => {
    try {
      const res = await invoicesAPI.processItems(invoiceId);
      toast.success(res.data.message); loadData();
    } catch (err) { toast.error(err.response?.data?.detail || 'Erro ao processar'); }
  };

  if (loading) return <div className="p-4 md:p-8"><div className="animate-pulse"><div className="h-8 bg-zinc-200 rounded w-64 mb-4" /><div className="h-64 bg-zinc-200 rounded" /></div></div>;

  return (
    <div className="p-4 md:p-8" data-testid="invoices-page">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl md:text-4xl font-semibold font-primary text-zinc-900 tracking-tight">Notas Fiscais</h1>
          <p className="mt-1 text-sm text-zinc-600">Upload PDF/XML ou escaneie com IA. Processe para enviar para aba Produtos.</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(o) => { setDialogOpen(o); if (!o) { setActiveTab('file'); setFormData({ invoice_number: '', supplier_name: '', issue_date: '', total_value: 0, tax_value: 0, items: [] }); } }}>
          <DialogTrigger asChild><Button data-testid="add-invoice-button" className="bg-blue-600 hover:bg-blue-700 text-white"><Plus className="h-4 w-4 mr-2" />Nova Nota Fiscal</Button></DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader><DialogTitle>Nova Nota Fiscal</DialogTitle></DialogHeader>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="file"><FileUp className="h-4 w-4 mr-1" />PDF/XML</TabsTrigger>
                <TabsTrigger value="ocr"><ImageIcon className="h-4 w-4 mr-1" />OCR</TabsTrigger>
                <TabsTrigger value="review"><FileText className="h-4 w-4 mr-1" />Revisar</TabsTrigger>
              </TabsList>
              <TabsContent value="file" className="space-y-4">
                <div className="border-2 border-dashed border-zinc-300 rounded-lg p-8 text-center">
                  <FileUp className="h-12 w-12 mx-auto text-zinc-400 mb-4" />
                  <p className="text-sm text-zinc-600 mb-4">Upload de PDF ou XML (NFe)</p>
                  <input type="file" accept=".pdf,.xml" onChange={handleFileUpload} className="hidden" id="file-upload" disabled={processing} />
                  <Button type="button" disabled={processing} onClick={() => document.getElementById('file-upload').click()} className="bg-blue-600 hover:bg-blue-700 text-white">{processing ? 'Processando...' : 'Selecionar Arquivo'}</Button>
                </div>
              </TabsContent>
              <TabsContent value="ocr" className="space-y-4">
                <div className="border-2 border-dashed border-zinc-300 rounded-lg p-8 text-center">
                  <ImageIcon className="h-12 w-12 mx-auto text-zinc-400 mb-4" />
                  <p className="text-sm text-zinc-600 mb-4">Upload de imagem para extracao com IA</p>
                  <input type="file" accept="image/*" onChange={handleImageUpload} className="hidden" id="image-upload" disabled={processing} />
                  <Button type="button" disabled={processing} onClick={() => document.getElementById('image-upload').click()} className="bg-blue-600 hover:bg-blue-700 text-white">{processing ? 'Processando...' : 'Selecionar Imagem'}</Button>
                </div>
              </TabsContent>
              <TabsContent value="review" className="space-y-4">
                {formData.invoice_number ? (
                  <>
                    <div className="grid grid-cols-2 gap-4 p-4 bg-zinc-50 rounded-lg">
                      <div><p className="text-xs text-zinc-500">Numero</p><p className="text-sm font-medium">{formData.invoice_number}</p></div>
                      <div><p className="text-xs text-zinc-500">Fornecedor</p><p className="text-sm font-medium">{formData.supplier_name}</p></div>
                      <div><p className="text-xs text-zinc-500">Data</p><p className="text-sm font-medium">{formData.issue_date}</p></div>
                      <div><p className="text-xs text-zinc-500">Valor Total</p><p className="text-sm font-medium font-mono">R$ {formData.total_value.toFixed(2)}</p></div>
                    </div>
                    {formData.items.length > 0 && (
                      <div className="max-h-[45vh] overflow-y-auto overflow-x-auto border border-zinc-200 rounded-md">
                        <table className="w-full text-sm">
                          <thead className="bg-zinc-50 sticky top-0 z-10 shadow-sm"><tr><th className="px-3 py-2 text-left text-xs font-semibold text-zinc-500">Produto</th><th className="px-3 py-2 text-right text-xs font-semibold text-zinc-500">Qtd</th><th className="px-3 py-2 text-right text-xs font-semibold text-zinc-500">Valor Unit.</th><th className="px-3 py-2 text-right text-xs font-semibold text-zinc-500">Total</th></tr></thead>
                          <tbody className="divide-y divide-zinc-100">
                            {formData.items.map((it, i) => <tr key={i}><td className="px-3 py-2">{it.product_name}</td><td className="px-3 py-2 text-right font-mono">{it.quantity}</td><td className="px-3 py-2 text-right font-mono">R$ {it.unit_price.toFixed(2)}</td><td className="px-3 py-2 text-right font-mono">R$ {it.total.toFixed(2)}</td></tr>)}
                          </tbody>
                        </table>
                      </div>
                    )}
                    <Button onClick={handleSave} className="w-full bg-blue-600 hover:bg-blue-700 text-white">Salvar Nota Fiscal</Button>
                  </>
                ) : <div className="p-8 text-center text-zinc-500">Faca upload de um arquivo ou imagem primeiro</div>}
              </TabsContent>
            </Tabs>
          </DialogContent>
        </Dialog>
      </div>

      <Dialog open={viewOpen} onOpenChange={setViewOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle>Nota Fiscal - {selectedInvoice?.invoice_number}</DialogTitle></DialogHeader>
          {selectedInvoice && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 p-4 bg-zinc-50 rounded-lg">
                <div><p className="text-xs text-zinc-500">Fornecedor</p><p className="text-sm font-medium">{selectedInvoice.supplier_name}</p></div>
                <div><p className="text-xs text-zinc-500">Data</p><p className="text-sm font-medium">{selectedInvoice.issue_date}</p></div>
                <div><p className="text-xs text-zinc-500">Valor</p><p className="text-sm font-mono">R$ {selectedInvoice.total_value.toFixed(2)}</p></div>
                <div><p className="text-xs text-zinc-500">Impostos</p><p className="text-sm font-mono">R$ {(selectedInvoice.tax_value || 0).toFixed(2)}</p></div>
              </div>
              {(selectedInvoice.items || []).length > 0 && (
                <div className="max-h-[50vh] overflow-y-auto overflow-x-auto border border-zinc-200 rounded-md">
                  <table className="w-full text-sm">
                    <thead className="bg-zinc-50 sticky top-0 z-10 shadow-sm"><tr><th className="px-3 py-2 text-left text-xs text-zinc-500">Produto</th><th className="px-3 py-2 text-right text-xs text-zinc-500">Qtd</th><th className="px-3 py-2 text-right text-xs text-zinc-500">Unit.</th><th className="px-3 py-2 text-right text-xs text-zinc-500">Total</th></tr></thead>
                    <tbody className="divide-y divide-zinc-100">{selectedInvoice.items.map((it, i) => <tr key={i}><td className="px-3 py-2">{it.product_name}</td><td className="px-3 py-2 text-right font-mono">{it.quantity}</td><td className="px-3 py-2 text-right font-mono">R$ {it.unit_price.toFixed(2)}</td><td className="px-3 py-2 text-right font-mono">R$ {it.total.toFixed(2)}</td></tr>)}</tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      <div className="bg-white rounded-xl border border-zinc-200 shadow-sm overflow-x-auto">
        <table className="w-full min-w-[600px]" data-testid="invoices-table">
          <thead className="bg-zinc-50 border-b border-zinc-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">Numero</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">Fornecedor</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">Data</th>
              <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-zinc-500">Valor</th>
              <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-zinc-500">Status</th>
              <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-zinc-500">Acoes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100">
            {invoices.map(inv => (
              <tr key={inv.id} className="hover:bg-zinc-50 transition-colors">
                <td className="px-4 py-3 text-sm font-mono text-zinc-800">{inv.invoice_number}</td>
                <td className="px-4 py-3 text-sm text-zinc-900">{inv.supplier_name}</td>
                <td className="px-4 py-3 text-sm text-zinc-600">{inv.issue_date}</td>
                <td className="px-4 py-3 text-sm font-mono text-zinc-800 text-right">R$ {inv.total_value.toFixed(2)}</td>
                <td className="px-4 py-3 text-center">
                  <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${inv.status === 'processed' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                    {inv.status === 'processed' ? 'Processada' : 'Pendente'}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-1">
                    <button onClick={() => { setSelectedInvoice(inv); setViewOpen(true); }} title="Visualizar" className="p-1.5 text-zinc-600 hover:bg-zinc-100 rounded-lg"><Eye className="h-4 w-4" /></button>
                    {inv.status === 'pending' && (
                      <button onClick={() => handleProcessItems(inv.id)} title="Enviar para Produtos" className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg"><Package className="h-4 w-4" /></button>
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