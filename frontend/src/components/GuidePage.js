import React from 'react';
import { Home, Package, Warehouse, ClipboardList, UserCircle, FileText, BarChart3, Bell, TrendingUp, Users, ArrowLeftRight, Building2, ShieldCheck } from 'lucide-react';

const sections = [
  {
    icon: ShieldCheck, title: 'Arquitetura SaaS Multi-Tenant',
    items: [
      'O sistema isola dados por "estabelecimento" (tenant). Cada usuario so ve dados do seu proprio estabelecimento.',
      'Master Global (subdominio master.*): cria estabelecimentos e gerencia usuarios em toda a plataforma.',
      'Administrador, Logistica e Operacional (subdominio do seu tenant): operam o estoque do estabelecimento.',
      'Cada estabelecimento tem um Almoxarifado Central (PAI) e um ou mais Setores Operacionais (FILHO).',
    ]
  },
  {
    icon: Building2, title: 'Estabelecimentos (Master)',
    items: [
      'Apenas Master pode criar estabelecimentos.',
      'Cada estabelecimento tem um Slug unico (ex: tj) que vira subdominio (tj.sconnecta.com.br).',
      'Apos criar, o Master cria um usuario Administrador para o estabelecimento.',
    ]
  },
  {
    icon: Home, title: 'Dashboard',
    items: [
      'Cards com os indicadores principais do estabelecimento.',
      'Produtos, Fornecedores, Depositos, NFs Pendentes, Requisicoes Pendentes e Alertas de Estoque Baixo.',
      'Usuarios Operacionais veem apenas dados do seu deposito FILHO.',
    ]
  },
  {
    icon: Warehouse, title: 'Depositos (PAI / FILHO)',
    items: [
      'PAI (Almoxarifado Central): recebe as Notas Fiscais e aprova requisicoes.',
      'FILHO (Setor Operacional): consome estoque criando Requisicoes para o PAI.',
      'Ao criar um FILHO, voce escolhe o PAI ao qual ele esta vinculado.',
      'Setores ajudam a organizar internamente cada deposito (ex: Prateleira A, Geladeira).',
    ]
  },
  {
    icon: ArrowLeftRight, title: 'Requisicoes (FILHO -> PAI)',
    items: [
      'Operacional (do FILHO) cria uma requisicao selecionando produtos disponiveis no PAI.',
      'Logistica/Admin (do PAI) revisa e Aprova ou Rejeita.',
      'Ao Aprovar: o sistema debita do estoque do PAI e credita no estoque do FILHO automaticamente.',
      'Se rejeitada, o estoque nao se move.',
    ]
  },
  {
    icon: Package, title: 'Produtos',
    items: [
      'Lista produtos importados das notas fiscais ainda nao alocados a um deposito.',
      'Clique em "Transferir" para envia-los ao PAI (almoxarifado central).',
    ]
  },
  {
    icon: ClipboardList, title: 'Estoque',
    items: [
      'Mostra produtos em cada deposito com a quantidade atual e status (OK / Baixo).',
      'Operacional ve apenas o estoque do seu deposito FILHO.',
      'Faca baixa do estoque escolhendo o setor de destino.',
    ]
  },
  {
    icon: UserCircle, title: 'Fornecedores',
    items: [
      'Cadastre fornecedores com CNPJ, contato, email e telefone.',
      'Cada estabelecimento ve apenas seus proprios fornecedores.',
    ]
  },
  {
    icon: FileText, title: 'Notas Fiscais',
    items: [
      'Upload PDF/XML/imagem. XML e lido nativamente; PDF e imagem usam Gemini AI para extracao.',
      'Revise os dados extraidos e salve a nota.',
      'Apos salvar, clique no icone Caixa para enviar os itens para a aba "Produtos".',
    ]
  },
  {
    icon: BarChart3, title: 'Relatorios',
    items: [
      'DRE, Curva ABC e Giro de Estoque.',
      'Exporte em PDF ou Excel.',
      'Disponivel para Admin do estabelecimento.',
    ]
  },
  {
    icon: Bell, title: 'Alertas e Notificacoes',
    items: [
      'Caixa de entrada com notificacoes do sistema.',
      'Configure o estoque minimo por produto - alertas serao gerados quando atingir o limite.',
    ]
  },
  {
    icon: TrendingUp, title: 'Auditoria',
    items: [
      'Historico completo de acoes no sistema com filtros e exportacao em Excel.',
      'Cada acao registra usuario, entidade, ID e timestamp.',
    ]
  },
  {
    icon: Users, title: 'Usuarios e Papeis (RBAC)',
    items: [
      'Master Global: gerencia estabelecimentos e usuarios em toda a plataforma.',
      'Administrador: gerencia todos os recursos do seu estabelecimento.',
      'Logistica (PAI): opera o almoxarifado central, aprova requisicoes.',
      'Operacional (FILHO): opera um setor operacional, cria requisicoes ao PAI.',
    ]
  },
];

export const GuidePage = () => {
  return (
    <div className="p-4 md:p-8" data-testid="guide-page">
      <div className="mb-8">
        <h1 className="text-2xl md:text-4xl font-semibold font-primary text-zinc-900 tracking-tight">Guia do Sistema</h1>
        <p className="mt-1 text-sm text-zinc-600">Tudo sobre o Gestao TJ (SaaS multi-tenant com hierarquia PAI/FILHO)</p>
      </div>
      <div className="space-y-6">
        {sections.map((section, idx) => {
          const Icon = section.icon;
          return (
            <div key={idx} className="bg-white rounded-xl border border-zinc-200 shadow-sm overflow-hidden">
              <div className="flex items-center gap-3 p-5 bg-zinc-50 border-b border-zinc-200">
                <div className="h-10 w-10 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
                  <Icon className="h-5 w-5 text-blue-600" />
                </div>
                <h2 className="text-lg font-semibold text-zinc-900">{section.title}</h2>
              </div>
              <div className="p-5">
                <ul className="space-y-2">
                  {section.items.map((item, i) => <li key={i} className="text-sm text-zinc-700 leading-relaxed">{item}</li>)}
                </ul>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
