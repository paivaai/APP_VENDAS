'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Dashboard() {
  const [stats, setStats] = useState({ tenants: 0, usage: 0, revenue: 0 });
  const router = useRouter();

  useEffect(() => {
    const auth = localStorage.getItem('adminAuth');
    if (!auth) router.push('/');
  }, [router]);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <h1 className="text-4xl font-bold mb-8">Dashboard Admin</h1>
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-600">Total de Clientes</h3>
          <p className="text-3xl font-bold text-blue-600">{stats.tenants}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-600">Uso de Tokens (Mês)</h3>
          <p className="text-3xl font-bold text-green-600">{stats.usage}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-600">Receita Total</h3>
          <p className="text-3xl font-bold text-purple-600">R$ {stats.revenue}</p>
        </div>
      </div>
      <div className="mt-8 flex gap-4">
        <a href="/tenants" className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700">Ver Clientes</a>
        <button onClick={() => { localStorage.removeItem('adminAuth'); router.push('/'); }} className="bg-red-600 text-white px-6 py-2 rounded hover:bg-red-700">Sair</button>
      </div>
    </div>
  );
}
