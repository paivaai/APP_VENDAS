'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function Home() {
  const router = useRouter()
  useEffect(() => {
    const token = localStorage.getItem('token')
    router.push(token ? '/dashboard' : '/login')
  }, [])
  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="text-violet-400 animate-pulse">Redirecionando...</div>
    </div>
  )
}
