'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { getSupabaseClient } from '@/lib/supabase'

type Client = {
  id: string
  name: string
  lastUpdated: string
  balance: number
  transactionCount?: number
}

export default function DashboardPage() {
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadClients()
  }, [])

  const loadClients = async () => {
    try {
      const supabase = getSupabaseClient()
      
      // Get unique client_ids from transactions table
      const { data: transactionData, error: transactionError } = await supabase
        .from('transactions')
        .select('client_id, transaction_date, amount')
        .order('transaction_date', { ascending: false })

      if (transactionError) {
        throw transactionError
      }

      // Process clients from transaction data
      const clientsMap = new Map<string, Client>()
      
      transactionData?.forEach(transaction => {
        const clientId = transaction.client_id
        if (!clientsMap.has(clientId)) {
          clientsMap.set(clientId, {
            id: clientId,
            name: clientId,
            lastUpdated: transaction.transaction_date,
            balance: 0,
            transactionCount: 0
          })
        }
        
        const client = clientsMap.get(clientId)!
        client.transactionCount = (client.transactionCount || 0) + 1
        
        // Update last updated date if this transaction is more recent
        if (transaction.transaction_date > client.lastUpdated) {
          client.lastUpdated = transaction.transaction_date
        }
        
        // Simple balance calculation (sum of all amounts)
        client.balance += transaction.amount || 0
      })

      const clientsList = Array.from(clientsMap.values())
      setClients(clientsList)
      
    } catch (err) {
      console.error('Error loading clients:', err)
      setError('Failed to load clients')
      
      // Fallback to hardcoded clients if database fails
      setClients([
        { id: 'BestSelf', name: 'BestSelf', lastUpdated: '2025-08-01', balance: 429428 },
        { id: 'ClientB', name: 'Client B', lastUpdated: '2025-07-21', balance: 45801 },
        { id: 'c', name: 'Client C', lastUpdated: '2025-08-25', balance: 0, transactionCount: 3210 }
      ])
    } finally {
      setLoading(false)
    }
  }

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
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Your Clients</h2>
            {loading && (
              <div className="text-sm text-gray-500">Loading clients...</div>
            )}
          </div>
          
          {error && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-6">
              <p className="text-yellow-800">{error} - Showing fallback data</p>
            </div>
          )}
          
          {clients.length === 0 && !loading ? (
            <div className="text-center py-12">
              <p className="text-gray-500">No clients found. Import some transaction data to get started.</p>
            </div>
          ) : (
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
                    {client.transactionCount && (
                      <div className="mt-1 text-sm text-gray-500">
                        {client.transactionCount.toLocaleString()} transactions
                      </div>
                    )}
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
          )}
        </div>
      </main>
    </div>
  )
}