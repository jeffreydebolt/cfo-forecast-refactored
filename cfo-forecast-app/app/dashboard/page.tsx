'use client'

import { useState } from 'react'
import Link from 'next/link'

type Client = {
  id: string
  name: string
  lastUpdated: string
  balance: number
}

export default function DashboardPage() {
  const [clients] = useState<Client[]>([
    { id: 'BestSelf', name: 'BestSelf', lastUpdated: '2025-08-01', balance: 429428 },
    { id: 'ClientB', name: 'Client B', lastUpdated: '2025-07-21', balance: 45801 },
  ])

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold">CFO Forecast</h1>
            </div>
            <div className="flex items-center">
              <Link
                href="/dashboard/new-client"
                className="ml-3 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
              >
                + Add Client
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Your Clients</h2>
          
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {clients.map((client) => (
              <Link
                key={client.id}
                href={`/dashboard/${client.id}`}
                className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow"
              >
                <div className="px-4 py-5 sm:p-6">
                  <h3 className="text-lg font-medium text-gray-900">{client.name}</h3>
                  <div className="mt-2 text-sm text-gray-500">
                    Last updated: {client.lastUpdated}
                  </div>
                  <div className="mt-3 text-2xl font-semibold text-gray-900">
                    ${client.balance.toLocaleString()}
                  </div>
                  <div className="mt-4 text-sm text-indigo-600 hover:text-indigo-500">
                    View forecast →
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </main>
    </div>
  )
}