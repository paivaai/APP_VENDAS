'use client'
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

const typeConfig = {
  low_stock: { label:'Estoque baixo', color:'#f87171', bg:'rgba(127,29,29,0.3)', border:'#7f1d1d', icon:'⚠️' },
  discount:  { label:'Desconto sugerido', color:'#a78bfa', bg:'rgba(109,40,217,0.2)', border:'#5b21b6', icon:'🏷️' },
  coupon:    { label:'Cupom sugerido', color:'#fbbf24', bg:'rgba(120,53,15,0.3)', border:'#92400e', icon:'🎟️' },
}

export default function Recommendations() {
  const [recs, setRecs] = useState([])
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const router = useRouter()
  const API = 'https://api.pdp.paivaai.com.br'

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) { router.push('/login'); return }
    loadRecs(token)
  }, [])

  async function loadRecs(token) {
    try {
      const res = await fetch(`${API}/decisions/`, { headers:{ Authorization:`Bearer ${token}` } })
      if (!res.ok) { router.push('/login'); return }
      setRecs(await res.json())
    } catch(e) { console.error(e) }
    finally { setLoading(false) }
  }

  async function analyze() {
    const token = localStorage.getItem('token')
    setAnalyzing(true)
    try {
      const res = await fetch(`${API}/decisions/analyze`, {
        method:'POST', headers:{ Authorization:`Bearer ${token}` }
      })
      const data = await res.json()
      await loadRecs(token)
      alert(`✅ ${data.generated} recomendações geradas!`)
    } catch(e) {
      alert('Erro ao analisar.')
    } finally { setAnalyzing(false) }
  }

  const s = {
    page: {minHeight:'100vh',background:'#030712',color:'white'},
    header: {borderBottom:'1px solid #1f2937',padding:'1rem 1.5rem',display:'flex',alignItems:'center',justifyContent:'space-between'},
    logoWrap: {display:'flex',alignItems:'center',gap:'0.75rem'},
    backBtn: {background:'none',border:'none',color:'#9ca3af',cursor:'pointer',fontSize:'1.25rem',padding:'0 0.25rem'},
    logoIcon: {width:'32px',height:'32px',background:'#7c3aed',borderRadius:'8px',display:'flex',alignItems:'center',justifyContent:'center'},
    logoText: {fontSize:'1.1rem',fontWeight:'700'},
    analyzeBtn: {background:'#7c3aed',border:'none',borderRadius:'8px',padding:'0.5rem 1.25rem',color:'white',fontSize:'0.875rem',fontWeight:'600',cursor:'pointer'},
    main: {maxWidth:'800px',margin:'0 auto',padding:'2rem 1.5rem'},
    empty: {textAlign:'center',padding:'5rem 0'},
    emptyIcon: {fontSize:'4rem',marginBottom:'1rem'},
    emptyTitle: {fontSize:'1.25rem',fontWeight:'600',marginBottom:'0.5rem'},
    emptySub: {color:'#9ca3af',fontSize:'0.875rem',marginBottom:'1.5rem'},
    bigBtn: {background:'#7c3aed',border:'none',borderRadius:'12px',padding:'0.875rem 2rem',color:'white',fontWeight:'600',cursor:'pointer',fontSize:'1rem'},
    count: {color:'#9ca3af',fontSize:'0.875rem',marginBottom:'1.5rem'},
    card: (cfg) => ({background:cfg.bg,border:`1px solid ${cfg.border}`,borderRadius:'16px',padding:'1.5rem',marginBottom:'1rem'}),
    cardHeader: {display:'flex',alignItems:'center',gap:'0.5rem',marginBottom:'0.5rem'},
    cardLabel: (cfg) => ({fontSize:'0.875rem',fontWeight:'600',color:cfg.color}),
    pill: (cfg) => ({fontSize:'0.75rem',padding:'0.15rem 0.5rem',borderRadius:'999px',background:'#1f2937',color:cfg.color}),
    rule: {color:'#d1d5db',fontSize:'0.875rem',marginBottom:'0.75rem'},
    aiBox: {background:'rgba(0,0,0,0.3)',borderRadius:'8px',padding:'1rem',border:'1px solid #374151'},
    aiLabel: {fontSize:'0.75rem',color:'#9ca3af',fontWeight:'500',marginBottom:'0.375rem'},
    aiText: {fontSize:'0.875rem',color:'#e5e7eb',lineHeight:'1.6'},
    date: {fontSize:'0.75rem',color:'#6b7280'},
  }

  if (loading) return (
    <div style={{minHeight:'100vh',background:'#030712',display:'flex',alignItems:'center',justifyContent:'center'}}>
      <div style={{color:'#a78bfa'}}>Carregando...</div>
    </div>
  )

  return (
    <div style={s.page}>
      <header style={s.header}>
        <div style={s.logoWrap}>
          <button style={s.backBtn} onClick={() => router.push('/dashboard')}>←</button>
          <div style={s.logoIcon}>
            <svg width="16" height="16" fill="none" stroke="white" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
          </div>
          <span style={s.logoText}>Recomendações IA</span>
        </div>
        <button style={s.analyzeBtn} onClick={analyze} disabled={analyzing}>
          {analyzing ? '⟳ Analisando...' : '✨ Analisar agora'}
        </button>
      </header>

      <main style={s.main}>
        {recs.length === 0 ? (
          <div style={s.empty}>
            <div style={s.emptyIcon}>🤖</div>
            <div style={s.emptyTitle}>Nenhuma recomendação ainda</div>
            <div style={s.emptySub}>Clique em "Analisar agora" para gerar recomendações com IA</div>
            <button style={s.bigBtn} onClick={analyze} disabled={analyzing}>
              {analyzing ? 'Analisando...' : '✨ Gerar recomendações'}
            </button>
          </div>
        ) : (
          <>
            <div style={s.count}>{recs.length} recomendações encontradas</div>
            {recs.map(rec => {
              const cfg = typeConfig[rec.type] || typeConfig.discount
              return (
                <div key={rec.id} style={s.card(cfg)}>
                  <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start'}}>
                    <div style={{flex:1}}>
                      <div style={s.cardHeader}>
                        <span>{cfg.icon}</span>
                        <span style={s.cardLabel(cfg)}>{cfg.label}</span>
                        {rec.suggested_value != null && (
                          <span style={s.pill(cfg)}>
                            {rec.type === 'low_stock' ? `${rec.suggested_value} unid.` : `${rec.suggested_value}%`}
                          </span>
                        )}
                      </div>
                      <div style={s.rule}>{rec.rule}</div>
                      {rec.justification && (
                        <div style={s.aiBox}>
                          <div style={s.aiLabel}>Análise IA</div>
                          <div style={s.aiText}>{rec.justification}</div>
                        </div>
                      )}
                    </div>
                    <div style={{...s.date,marginLeft:'1rem'}}>
                      {new Date(rec.created_at).toLocaleDateString('pt-BR')}
                    </div>
                  </div>
                </div>
              )
            })}
          </>
        )}
      </main>
    </div>
  )
}
