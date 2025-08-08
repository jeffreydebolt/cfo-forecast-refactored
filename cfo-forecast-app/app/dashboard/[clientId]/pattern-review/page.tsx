'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { getSupabaseClient } from '@/lib/supabase'

type Transaction = {
  transaction_date: string
  amount: number
}

type VendorPattern = {
  vendor_name: string
  display_name: string
  transactions: Transaction[]
  detected_pattern: string
  detected_interval: number
  detected_amount: number
  confidence: number
  next_date?: string
  override_pattern?: string
  override_amount?: number
  override_next_date?: string
}

const PATTERN_OPTIONS = [
  { value: 'daily', label: 'Daily', days: 1 },
  { value: 'weekly', label: 'Weekly', days: 7 },
  { value: 'bi-weekly', label: 'Bi-weekly (14 days)', days: 14 },
  { value: 'monthly', label: 'Monthly', days: 30 },
  { value: 'quarterly', label: 'Quarterly', days: 90 },
  { value: 'irregular', label: 'Irregular', days: 0 }
]

export default function PatternReviewPage() {
  const router = useRouter()
  const params = useParams()
  const clientId = params.clientId as string
  
  const [patterns, setPatterns] = useState<VendorPattern[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showAllTransactions, setShowAllTransactions] = useState<{[key: string]: boolean}>({})
  
  const supabase = getSupabaseClient()

  useEffect(() => {
    loadPatterns()
  }, [clientId])

  const loadPatterns = async () => {
    try {
      // Get vendor mappings
      const { data: vendors, error: vendorError } = await supabase
        .from('vendors')
        .select('vendor_name, display_name')
        .eq('client_id', clientId)

      if (vendorError) throw vendorError

      // Get all transactions
      const { data: transactions, error: txError } = await supabase
        .from('transactions')
        .select('vendor_name, transaction_date, amount')
        .eq('client_id', clientId)
        .order('transaction_date', { ascending: false })

      if (txError) throw txError

      // Create vendor lookup map
      const vendorMap = new Map(vendors?.map(v => [v.vendor_name, v.display_name]))

      // Group transactions by display name
      const groupedByDisplay = new Map<string, Transaction[]>()
      
      transactions?.forEach(tx => {
        const displayName = vendorMap.get(tx.vendor_name) || tx.vendor_name
        if (!groupedByDisplay.has(displayName)) {
          groupedByDisplay.set(displayName, [])
        }
        groupedByDisplay.get(displayName)!.push({
          transaction_date: tx.transaction_date,
          amount: tx.amount
        })
      })

      // Analyze patterns for each vendor group
      const patternAnalysis: VendorPattern[] = []
      
      groupedByDisplay.forEach((txs, displayName) => {
        const analysis = analyzePattern(txs)
        patternAnalysis.push({
          vendor_name: displayName,
          display_name: displayName,
          transactions: txs,
          ...analysis
        })
      })

      // Sort by total transaction value
      patternAnalysis.sort((a, b) => {
        const totalA = a.transactions.reduce((sum, tx) => sum + Math.abs(tx.amount), 0)
        const totalB = b.transactions.reduce((sum, tx) => sum + Math.abs(tx.amount), 0)
        return totalB - totalA
      })

      setPatterns(patternAnalysis)
    } catch (error) {
      console.error('Error loading patterns:', error)
    } finally {
      setLoading(false)
    }
  }

  const analyzePattern = (transactions: Transaction[]) => {
    if (transactions.length < 2) {
      return {
        detected_pattern: 'irregular',
        detected_interval: 0,
        detected_amount: transactions[0]?.amount || 0,
        confidence: 0
      }
    }

    // Get recent transactions (last 90 days)
    const today = new Date()
    const ninetyDaysAgo = new Date(today.getTime() - 90 * 24 * 60 * 60 * 1000)
    const recentTxs = transactions.filter(tx => 
      new Date(tx.transaction_date) >= ninetyDaysAgo
    )

    if (recentTxs.length < 2) {
      return {
        detected_pattern: 'irregular',
        detected_interval: 0,
        detected_amount: transactions[0]?.amount || 0,
        confidence: 0
      }
    }

    // Calculate intervals between transactions
    const intervals: number[] = []
    for (let i = 0; i < recentTxs.length - 1; i++) {
      const date1 = new Date(recentTxs[i].transaction_date)
      const date2 = new Date(recentTxs[i + 1].transaction_date)
      const daysDiff = Math.abs(date1.getTime() - date2.getTime()) / (1000 * 60 * 60 * 24)
      intervals.push(daysDiff)
    }

    // Calculate average interval
    const avgInterval = intervals.reduce((a, b) => a + b, 0) / intervals.length

    // Determine pattern based on average interval
    let pattern = 'irregular'
    let interval = 0
    
    if (avgInterval <= 1.5) {
      pattern = 'daily'
      interval = 1
    } else if (avgInterval <= 8) {
      pattern = 'weekly'
      interval = 7
    } else if (avgInterval <= 17) {
      pattern = 'bi-weekly'
      interval = 14
    } else if (avgInterval <= 35) {
      pattern = 'monthly'
      interval = 30
    } else if (avgInterval <= 100) {
      pattern = 'quarterly'
      interval = 90
    }

    // Calculate confidence (0-100)
    const variance = intervals.map(i => Math.abs(i - avgInterval))
    const avgVariance = variance.reduce((a, b) => a + b, 0) / variance.length
    const confidence = Math.max(0, Math.min(100, 100 - (avgVariance / avgInterval * 100)))

    // Calculate average amount
    const amounts = recentTxs.map(tx => Math.abs(tx.amount))
    const avgAmount = amounts.reduce((a, b) => a + b, 0) / amounts.length

    // Calculate next date
    const lastDate = new Date(recentTxs[0].transaction_date)
    const nextDate = new Date(lastDate.getTime() + interval * 24 * 60 * 60 * 1000)

    return {
      detected_pattern: pattern,
      detected_interval: interval,
      detected_amount: avgAmount,
      confidence: Math.round(confidence),
      next_date: nextDate.toISOString().split('T')[0]
    }
  }

  const handlePatternChange = (vendorName: string, field: string, value: any) => {
    setPatterns(prev => prev.map(p => 
      p.vendor_name === vendorName 
        ? { ...p, [`override_${field}`]: value }
        : p
    ))
  }

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    })
  }

  const savePatterns = async () => {
    setSaving(true)
    try {
      // Prepare pattern records
      const patternRecords = patterns.map(p => ({
        client_id: clientId,
        vendor_group: p.display_name,
        pattern_type: p.override_pattern || p.detected_pattern,
        interval_days: p.override_pattern 
          ? PATTERN_OPTIONS.find(opt => opt.value === p.override_pattern)?.days || p.detected_interval
          : p.detected_interval,
        average_amount: p.override_amount || p.detected_amount,
        next_date: p.override_next_date || p.next_date,
        confidence: p.confidence,
        created_at: new Date().toISOString()
      }))

      // Save to a patterns table (you'll need to create this)
      alert('Pattern data ready to save. Next step: Generate forecast!')
      
      // For now, just log the data
      console.log('Pattern records:', patternRecords)
      
      // Navigate to forecast page (to be built)
      router.push(`/dashboard/${clientId}/forecast`)
      
    } catch (error) {
      console.error('Error saving patterns:', error)
      alert('Failed to save patterns. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg">Analyzing payment patterns...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={() => router.back()}
                className="text-gray-500 hover:text-gray-700 mr-4"
              >
                ← Back
              </button>
              <h1 className="text-xl font-semibold">Pattern Review - {clientId}</h1>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white shadow rounded-lg p-6 mb-6">
            <h2 className="text-lg font-medium text-gray-900 mb-2">Review Payment Patterns</h2>
            <p className="text-sm text-gray-600">
              AI has detected payment patterns based on recent transactions. Review and adjust as needed.
            </p>
          </div>

          <div className="space-y-6">
            {patterns.map((pattern) => (
              <div key={pattern.vendor_name} className="bg-white shadow rounded-lg overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200">
                  <div className="flex justify-between items-center">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">{pattern.display_name}</h3>
                      <p className="text-sm text-gray-500">
                        {pattern.transactions.length} transactions | 
                        ${Math.abs(pattern.transactions.reduce((sum, tx) => sum + tx.amount, 0)).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} total
                      </p>
                    </div>
                    <div className={`text-sm px-3 py-1 rounded-full ${
                      pattern.confidence >= 80 ? 'bg-green-100 text-green-800' :
                      pattern.confidence >= 60 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {pattern.confidence}% confidence
                    </div>
                  </div>
                </div>

                <div className="px-6 py-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Pattern
                      </label>
                      <select
                        className="w-full border border-gray-300 rounded-md px-3 py-2"
                        value={pattern.override_pattern || pattern.detected_pattern}
                        onChange={(e) => handlePatternChange(pattern.vendor_name, 'pattern', e.target.value)}
                      >
                        {PATTERN_OPTIONS.map(opt => (
                          <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Average Amount
                      </label>
                      <input
                        type="number"
                        className="w-full border border-gray-300 rounded-md px-3 py-2"
                        value={pattern.override_amount || pattern.detected_amount.toFixed(2)}
                        onChange={(e) => handlePatternChange(pattern.vendor_name, 'amount', parseFloat(e.target.value))}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Next Payment Date
                      </label>
                      <input
                        type="date"
                        className="w-full border border-gray-300 rounded-md px-3 py-2"
                        value={pattern.override_next_date || pattern.next_date}
                        onChange={(e) => handlePatternChange(pattern.vendor_name, 'next_date', e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="border-t pt-4">
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="text-sm font-medium text-gray-700">Recent Transactions</h4>
                      <button
                        onClick={() => setShowAllTransactions(prev => ({ ...prev, [pattern.vendor_name]: !prev[pattern.vendor_name] }))}
                        className="text-sm text-indigo-600 hover:text-indigo-500"
                      >
                        {showAllTransactions[pattern.vendor_name] ? 'Show less' : 'Show all'}
                      </button>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-sm">
                      {pattern.transactions
                        .slice(0, showAllTransactions[pattern.vendor_name] ? undefined : 10)
                        .map((tx, idx) => (
                          <div key={idx} className="flex justify-between py-1 px-2 bg-gray-50 rounded">
                            <span className="text-gray-600">{formatDate(tx.transaction_date)}</span>
                            <span className="font-medium">${Math.abs(tx.amount).toLocaleString()}</span>
                          </div>
                        ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 flex justify-between">
            <button
              onClick={() => router.back()}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Back
            </button>
            <button
              onClick={savePatterns}
              disabled={saving}
              className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Patterns & Generate Forecast'}
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}