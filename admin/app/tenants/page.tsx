'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Tenants() {
  const [tenants, setTenants] = useState([]);
  const router = useRouter();

  useEffect(() => {
    const auth = localStorage.getItem('adminAuth');
    if (!auth) router.push('/');
  }, [router]);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-4xl font-bold">Clientes</h1>
        <a href="/dashboard" className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700">Voltar</a>
      </div>
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-100 border-b">
            <tr>
              <th className="px-6 py-3 text-left">ID</th>
              <th className="px-6 py-3 text-left">Nome</th>
              <th className="px-6 py-3 text-left">Email</th>
              <th className="px-6 py-3 text-left">Status</th>
              <th className="px-6 py-3 text-left">Ações</th>
            </tr>
          </thead>
          <tbody>
            {tenants.length === 0 ? (
              <tr><td colSpan={5} className="px-6 py-4 text-center text-gray-500">Nenhum cliente encontrado</td></tr>
            ) : (
              tenants.map((tenant: any) => (
                <tr key={tenant.id} className="border-b hover:bg-gray-50">
                  <td className="px-6 py-4">{tenant.id}</td>
                  <td className="px-6 py-4">{tenant.name}</td>
                  <td className="px-6 py-4">{tenant.email}</td>
                  <td className="px-6 py-4"><span className="bg-green-100 text-green-800 px-3 py-1 rounded">Ativo</span></td>
                  <td className="px-6 py-4"><a href={`/tenants/${tenant.id}`} className="text-blue-600 hover:underline">Detalhe</a></td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
