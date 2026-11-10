'use client'
import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
const DashboardPage = () => {
  const [activeTab, setActiveTab] = useState('total')
  const [suggestions, setSuggestions] = useState([
    { id: 1, agent: 'PreSaleAgent', type: 'pre', icon: '🏷️', title: 'Estoque baixo detectado', description: 'Produto "Camiseta Básica P" com 3 unidades restantes no TikTok Shop. Sugestão: repor 50 unidades.', priority: 'high', action: 'Aprovar Reposição', channel: 'TikTok Shop' },
    { id: 2, agent: 'SaleAgent', type: 'sale', icon: '💰', title: 'Aplicar desconto de 15%', description: 'Queda de 8% nas vendas nos últimos 3 dias. Aplicar cupom PROMO15 para reativar demanda.', priority: 'medium', action: 'Aplicar Cupom', channel: 'Mercado Livre' },
    { id: 3, agent: 'PostSaleAgent', type: 'post', icon: '↩️', title: 'Devolução pendente #12343', description: 'Cliente Pedro Oliveira solicitou devolução. Produto com defeito. Sugestão: reembolso imediato.', priority: 'critical', action: 'Aprovar Devolução', channel: 'TikTok Shop' },
    { id: 4, agent: 'PreSaleAgent', type: 'pre', icon: '📦', title: 'Cadastrar 12 novos produtos', description: 'Planilha enviada pelo cliente contém 12 produtos prontos para cadastro no Shopee.', priority: 'low', action: 'Iniciar Cadastro', channel: 'Shopee' },
    { id: 5, agent: 'SaleAgent', type: 'sale', icon: '🤖', title: 'Responder 4 clientes no WhatsApp', description: '4 clientes aguardando resposta há mais de 30 minutos. IA pode responder automaticamente.', priority: 'high', action: 'Responder com IA', channel: 'TikTok Shop' },
  ])
  const [activeAgent, setActiveAgent] = useState('all')
  const [dismissed, setDismissed] = useState([])
  const [approved, setApproved] = useState([])
  const roiEstimated = approved.length * 847.50
  const router = useRouter()
  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) router.push('/login')
  }, [])
  const handleLogout = () => {
    localStorage.removeItem('token')
    router.push('/login')
  }
  const channels = [
    { id: 'total', name: 'Total', connected: true, cards: [{ title: 'Produtos', value: '1.541', trend: '+15%' },{ title: 'Vendas', value: '3.840', trend: '+22%' },{ title: 'Avaliação', value: '4.8★', trend: 'Estável' },{ title: 'Receita', value: 'R$ 285K', trend: '+32%' }], orders: [{ id: '#12345', client: 'João Silva', status: 'Entregue', date: '23/06/2026', value: 'R$ 299,90', statusColor: 'bg-green-500' },{ id: '#12344', client: 'Maria Santos', status: 'Processando', date: '22/06/2026', value: 'R$ 549,99', statusColor: 'bg-blue-500' },{ id: '#12343', client: 'Pedro Oliveira', status: 'Preparando', date: '21/06/2026', value: 'R$ 189,50', statusColor: 'bg-orange-500' },]},
    { id: 'tiktok', name: 'TikTok Shop', connected: true, cards: [{ title: 'Produtos', value: '542', trend: '+8%' },{ title: 'Vendas', value: '1.2K', trend: '+18%' },{ title: 'Avaliação', value: '4.9★', trend: 'Estável' },{ title: 'Receita', value: 'R$ 98K', trend: '+12%' }], connectUrl: '/api/integrations/tiktok/connect', orders: [{ id: '#12345', client: 'João Silva', status: 'Entregue', date: '23/06/2026', value: 'R$ 299,90', statusColor: 'bg-green-500' },{ id: '#12343', client: 'Pedro Oliveira', status: 'Preparando', date: '21/06/2026', value: 'R$ 189,50', statusColor: 'bg-orange-500' },]},
    { id: 'mercadolivre', name: 'Mercado Livre', connected: false, cards: [{ title: 'Produtos', value: '342', trend: '+5%' },{ title: 'Vendas', value: '1.8K', trend: '+18%' },{ title: 'Avaliação', value: '4.8★', trend: 'Estável' },{ title: 'Receita', value: 'R$ 125K', trend: '+32%' }], connectUrl: 'https://api.pdp.paivaai.com.br/integrations/mercadolivre/auth/connect?tenant_id=1', orders: [] },
    { id: 'shopee', name: 'Shopee', connected: false, cards: [{ title: 'Produtos', value: '287', trend: '+3%' },{ title: 'Vendas', value: '924', trend: '+12%' },{ title: 'Avaliação', value: '4.7★', trend: 'Estável' },{ title: 'Receita', value: 'R$ 87K', trend: '+24%' }], connectUrl: 'https://api.pdp.paivaai.com.br/integrations/shopee/connect?tenant_id=1', orders: [] },
    { id: 'shein', name: 'Shein', connected: false, cards: [{ title: 'Produtos', value: '512', trend: '+8%' },{ title: 'Vendas', value: '2.1K', trend: '+26%' },{ title: 'Avaliação', value: '4.6★', trend: '+0.1' },{ title: 'Receita', value: 'R$ 156K', trend: '+41%' }], connectUrl: 'https://api.pdp.paivaai.com.br/integrations/shein/connect?tenant_id=1', orders: [] },
  ]
  const currentChannel = channels.find(c => c.id === activeTab)
  const handleConnect = (url) => { window.location.href = url }
  const handleBlingConnect = () => {
    const token = localStorage.getItem('token')
    window.location.href = `https://api.pdp.paivaai.com.br/integrations/bling/connect?token=${token}`
  }
  const handleApprove = (id) => {
    const s = suggestions.find(x => x.id === id)
    if (s) setApproved(a => [...a, s])
    setSuggestions(s => s.filter(x => x.id !== id))
  }
  const handleDismiss = (id) => { setDismissed(d => [...d, id]); setSuggestions(s => s.filter(x => x.id !== id)) }
  const agentFilters = [{ id: 'all', label: '✦ Todas', color: 'purple' },{ id: 'pre', label: '🏷️ Pré-venda', color: 'blue' },{ id: 'sale', label: '💰 Venda', color: 'green' },{ id: 'post', label: '↩️ Pós-venda', color: 'orange' },]
  const priorityConfig = { critical: { label: 'Crítico', color: 'bg-red-500/20 text-red-400 border border-red-500/30' }, high: { label: 'Alta', color: 'bg-orange-500/20 text-orange-400 border border-orange-500/30' }, medium: { label: 'Média', color: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' }, low: { label: 'Baixa', color: 'bg-slate-500/20 text-slate-400 border border-slate-500/30' }, }
  const filteredSuggestions = activeAgent === 'all' ? suggestions : suggestions.filter(s => s.type === activeAgent)
  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <header className="bg-slate-900 border-b border-slate-800 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-purple-600 flex items-center justify-center">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          </div>
          <span className="font-bold text-white tracking-wide">PAIVA AI</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-6">
            <div className="text-right">
              <p className="text-xs text-slate-500">Gerado pelos Agentes IA</p>
              <p className="text-lg font-bold text-green-400">R$ {roiEstimated.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</p>
            </div>
            <div className="w-px h-8 bg-slate-700"></div>
            <div className="flex items-center gap-6">
            <div className="text-right">
              <p className="text-xs text-slate-500">Gerado pelos Agentes IA</p>
            </div>
            <div className="w-px h-8 bg-slate-700"></div>
            <span className="text-slate-400 text-sm">{suggestions.length > 0 && <span className="bg-purple-600 text-white text-xs px-2 py-0.5 rounded-full mr-2">{suggestions.length}</span>}Sugestões pendentes</span>
          </div>
          </div>
          <button className="bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors">✦ Recomendações</button>
          <button onClick={handleLogout} className="text-slate-400 hover:text-white text-sm transition-colors">Sair</button>
        </div>
      </header>
      <div className="max-w-7xl mx-auto px-6 py-6 flex gap-6">
        <div className="flex-1 min-w-0">
          {/* Bling Banner */}
          <div className="bg-slate-900 border border-green-800 rounded-lg px-5 py-3 mb-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-green-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">B</div>
              <div>
                <p className="text-sm font-medium">Conectar Bling ERP</p>
                <p className="text-xs text-slate-400">Sincronize ML, Shopee e TikTok automaticamente</p>
              </div>
            </div>
            <button onClick={handleBlingConnect} className="bg-green-600 hover:bg-green-700 text-white text-xs font-medium px-4 py-2 rounded-lg transition-colors">Conectar Bling</button>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg mb-6">
            <div className="flex gap-0 overflow-x-auto">
              {channels.map((channel) => (
                <button key={channel.id} onClick={() => setActiveTab(channel.id)} className={`py-3 px-5 font-medium transition-colors relative whitespace-nowrap text-sm ${ activeTab === channel.id ? 'text-purple-400' : 'text-slate-400 hover:text-slate-300' }`}>
                  {channel.name}
                  {activeTab === channel.id && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-500"></div>}
                </button>
              ))}
            </div>
          </div>
          {!currentChannel.connected ? (
            <div className="bg-slate-900 border border-dashed border-slate-700 rounded-lg p-12 text-center">
              <div className="text-4xl mb-4">🔗</div>
              <h3 className="text-lg font-semibold mb-2">Conecte sua conta {currentChannel.name}</h3>
              <p className="text-slate-400 text-sm mb-6">Autorize o acesso para importar pedidos, estoque e receber recomendações de IA</p>
              <button onClick={() => handleConnect(currentChannel.connectUrl)} className="bg-purple-600 hover:bg-purple-700 text-white font-medium px-6 py-2.5 rounded-lg transition-colors">Conectar {currentChannel.name}</button>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                {currentChannel.cards.map((card, idx) => (
                  <div key={idx} className="bg-slate-900 border border-slate-800 rounded-lg p-5 hover:border-slate-700 transition-colors">
                    <p className="text-slate-400 text-xs mb-2">{card.title}</p>
                    <p className="text-2xl font-bold mb-1">{card.value}</p>
                    <p className="text-green-400 text-xs">{card.trend}</p>
                  </div>
                ))}
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-800"><h3 className="font-semibold text-sm">Pedidos Recentes</h3></div>
                <table className="w-full"><thead><tr className="border-b border-slate-800"><th className="text-left px-6 py-3 text-xs text-slate-400 font-medium">ID</th><th className="text-left px-6 py-3 text-xs text-slate-400 font-medium">Cliente</th><th className="text-left px-6 py-3 text-xs text-slate-400 font-medium">Status</th><th className="text-left px-6 py-3 text-xs text-slate-400 font-medium">Data</th><th className="text-right px-6 py-3 text-xs text-slate-400 font-medium">Valor</th></tr></thead><tbody>{(currentChannel.orders || []).map((order, idx) => (<tr key={idx} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors"><td className="px-6 py-4 text-sm text-slate-300">{order.id}</td><td className="px-6 py-4 text-sm">{order.client}</td><td className="px-6 py-4"><span className={`${order.statusColor} text-white text-xs px-2.5 py-1 rounded-full`}>{order.status}</span></td><td className="px-6 py-4 text-sm text-slate-400">{order.date}</td><td className="px-6 py-4 text-sm text-right font-medium">{order.value}</td></tr>))}</tbody></table>
              </div>
            </>
          )}
        </div>
        <div className="w-80 flex-shrink-0">
          <div className="bg-slate-900 border border-slate-800 rounded-lg sticky top-6">
            <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2"><span className="text-sm font-semibold">Agentes IA</span>{suggestions.length > 0 && <span className="bg-purple-600 text-white text-xs px-1.5 py-0.5 rounded-full">{suggestions.length}</span>}</div>
              <span className="text-xs text-slate-500">ao vivo</span>
            </div>
            <div className="px-4 py-2 border-b border-slate-800 flex gap-1 flex-wrap">
              {agentFilters.map(f => (
                <button key={f.id} onClick={() => setActiveAgent(f.id)} className={`text-xs px-2 py-1 rounded-md transition-colors ${activeAgent === f.id ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-slate-300 hover:bg-slate-800'}`}>{f.label}</button>
              ))}
            </div>
            <div className="divide-y divide-slate-800 max-h-[600px] overflow-y-auto">
              {filteredSuggestions.length === 0 ? (
                <div className="px-4 py-8 text-center text-slate-500 text-sm"><div className="text-2xl mb-2">✓</div>Nenhuma sugestão pendente</div>
              ) : (
                filteredSuggestions.map(s => (
                  <div key={s.id} className={`p-4 ${s.priority === 'critical' ? 'bg-red-500/5' : ''}`}>
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2"><span className="text-base">{s.icon}</span><span className={`text-xs px-1.5 py-0.5 rounded-md ${priorityConfig[s.priority].color}`}>{priorityConfig[s.priority].label}</span></div>
                      <span className="text-xs text-slate-500">{s.channel}</span>
                    </div>
                    <p className="text-sm font-medium mb-1">{s.title}</p>
                    <p className="text-xs text-slate-400 mb-3 leading-relaxed">{s.description}</p>
                    <div className="flex gap-2">
                      <button onClick={() => handleApprove(s.id)} className="flex-1 bg-purple-600 hover:bg-purple-700 text-white text-xs font-medium py-1.5 rounded-md transition-colors">{s.action}</button>
                      <button onClick={() => handleDismiss(s.id)} className="px-3 text-slate-400 hover:text-white text-xs py-1.5 rounded-md hover:bg-slate-800 transition-colors">✕</button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
export default DashboardPage
