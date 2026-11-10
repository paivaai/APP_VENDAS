'use client';

import { useParams, useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function TenantDetail() {
  const params = useParams();
  const router = useRouter();

  useEffect(() => {
    const auth = localStorage.getItem('adminAuth');
    if (!auth) router.push('/');
  }, [router]);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-4xl font-bold">Detalhe do Cliente {params.id}</h1>
        <a href="/tenants" className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700">Voltar</a>
      </div>
      <div className="grid grid-cols-2 gap-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-2xl font-bold mb-4">Canais Conectados</h2>
          <ul className="space-y-2">
            <li className="flex items-center gap-2"><span className="text-green-600">✓</span>Mercado Livre</li>
            <li className="flex items-center gap-2"><span className="text-red-600">✗</span>Shopee</li>
            <li className="flex items-center gap-2"><span className="text-red-600">✗</span>Shein</li>
          </ul>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-2xl font-bold mb-4">Uso de Tokens</h2>
          <p className="text-3xl font-bold text-blue-600">1,234 / 5,000</p>
          <div className="mt-4 bg-gray-200 rounded-full h-2"><div className="bg-blue-600 h-2 rounded-full" style={{width: '24.68%'}}></div></div>
        </div>
      </div>
    </div>
  );
}
