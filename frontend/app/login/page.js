'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isRegister, setIsRegister] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const API = 'https://api.pdp.paivaai.com.br'

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      let res
      if (isRegister) {
        res = await fetch(`${API}/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        })
      } else {
        const form = new URLSearchParams()
        form.append('username', email)
        form.append('password', password)
        res = await fetch(`${API}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: form
        })
      }
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Erro ao autenticar')
      localStorage.setItem('token', data.access_token)
      router.push('/dashboard')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const s = {
    page: { minHeight:'100vh', display:'flex', alignItems:'center', justifyContent:'center', background:'#030712', padding:'1rem' },
    card: { width:'100%', maxWidth:'420px' },
    logo: { textAlign:'center', marginBottom:'2rem' },
    logoIcon: { width:'64px', height:'64px', background:'#7c3aed', borderRadius:'16px', display:'flex', alignItems:'center', justifyContent:'center', margin:'0 auto 1rem' },
    title: { fontSize:'1.5rem', fontWeight:'700', color:'white', marginBottom:'0.25rem' },
    sub: { color:'#9ca3af', fontSize:'0.875rem' },
    box: { background:'#111827', border:'1px solid #1f2937', borderRadius:'16px', padding:'2rem' },
    h2: { fontSize:'1.25rem', fontWeight:'600', color:'white', marginBottom:'1.5rem' },
    err: { background:'rgba(127,29,29,0.4)', border:'1px solid #991b1b', color:'#fca5a5', borderRadius:'8px', padding:'0.75rem', marginBottom:'1rem', fontSize:'0.875rem' },
    label: { display:'block', fontSize:'0.875rem', color:'#9ca3af', marginBottom:'0.375rem' },
    input: { width:'100%', background:'#1f2937', border:'1px solid #374151', borderRadius:'8px', padding:'0.75rem 1rem', color:'white', fontSize:'1rem', outline:'none', marginBottom:'1rem' },
    btn: { width:'100%', background:'#7c3aed', border:'none', borderRadius:'8px', padding:'0.875rem', color:'white', fontSize:'1rem', fontWeight:'600', cursor:'pointer', marginTop:'0.5rem' },
    toggle: { textAlign:'center', marginTop:'1.5rem', fontSize:'0.875rem', color:'#6b7280' },
    link: { color:'#a78bfa', background:'none', border:'none', cursor:'pointer', fontSize:'0.875rem' }
  }

  return (
    <div style={s.page}>
      <div style={s.card}>
        <div style={s.logo}>
          <div style={s.logoIcon}>
            <svg width="28" height="28" fill="none" stroke="white" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div style={s.title}>Paiva AI</div>
          <div style={s.sub}>Decision Platform</div>
        </div>
        <div style={s.box}>
          <h2 style={s.h2}>{isRegister ? 'Criar conta' : 'Entrar na plataforma'}</h2>
          {error && <div style={s.err}>{error}</div>}
          <form onSubmit={handleSubmit}>
            <label style={s.label}>Email</label>
            <input style={s.input} type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="seu@email.com" required />
            <label style={s.label}>Senha</label>
            <input style={s.input} type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="••••••••" required />
            <button style={s.btn} type="submit" disabled={loading}>
              {loading ? 'Aguarde...' : isRegister ? 'Criar conta' : 'Entrar'}
            </button>
          </form>
          <div style={s.toggle}>
            {isRegister ? 'Já tem conta? ' : 'Ainda não tem conta? '}
            <button style={s.link} onClick={()=>{setIsRegister(!isRegister);setError('')}}>
              {isRegister ? 'Entrar' : 'Criar agora'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
