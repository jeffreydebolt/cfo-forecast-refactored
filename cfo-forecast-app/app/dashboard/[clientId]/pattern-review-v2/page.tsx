'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { getSupabaseClient } from '@/lib/supabase'

type PatternReview = {
  id?: string
  vendor_group: string
  status: 'pending' | 'reviewed' | 'skipped'
  pattern_type: string
  interval_days: number
  average_amount: number
  next_date: string
  confidence: number
  total_transaction_value: number
  transaction_count: number
  reviewed_at?: string
  recent_transactions?: Array<{
    transaction_date: string
    amount: number
  }>
}

const PATTERN_OPTIONS = [
  { value: 'daily', label: 'Daily', days: 1 },
  { value: 'weekly', label: 'Weekly', days: 7 },
  { value: 'bi-weekly', label: 'Bi-weekly (14 days)', days: 14 },
  { value: 'monthly', label: 'Monthly', days: 30 },
  { value: 'quarterly', label: 'Quarterly', days: 90 },
  { value: 'irregular', label: 'Irregular', days: 0 }
]

export default function PatternReviewV2Page() {
  const router = useRouter()
  const params = useParams()
  const clientId = params.clientId as string
  
  const [patterns, setPatterns] = useState<PatternReview[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showAll, setShowAll] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const [editedPattern, setEditedPattern] = useState<Partial<PatternReview>>({})
  
  const supabase = getSupabaseClient()

  // Filter patterns based on $1k threshold
  const filteredPatterns = showAll 
    ? patterns 
    : patterns.filter(p => p.total_transaction_value >= 1000)

  const currentPattern = filteredPatterns[currentIndex]
  const totalPatterns = filteredPatterns.length
  const reviewedCount = filteredPatterns.filter(p => p.status === 'reviewed').length
  const progressPercent = totalPatterns > 0 ? (reviewedCount / totalPatterns) * 100 : 0

  useEffect(() => {
    loadPatterns()
  }, [clientId])

  const loadPatterns = async () => {
    try {
      // First check if we have existing pattern reviews
      const { data: existingReviews } = await supabase
        .from('pattern_reviews')
        .select('*')
        .eq('client_id', clientId)

      if (existingReviews && existingReviews.length > 0) {
        // Load from saved state
        const reviewMap = new Map(existingReviews.map(r => [r.vendor_group, r]))
        
        // Get recent transactions for current pattern
        if (existingReviews.length > 0) {
          await loadTransactionsForPattern(existingReviews[0].vendor_group)
        }
        
        setPatterns(existingReviews)
        
        // Find first pending item
        const firstPendingIndex = existingReviews.findIndex(p => p.status === 'pending')
        setCurrentIndex(firstPendingIndex >= 0 ? firstPendingIndex : 0)
      } else {
        // Fresh analysis needed
        await analyzeAndSavePatterns()
      }
    } catch (error) {
      console.error('Error loading patterns:', error)
    } finally {
      setLoading(false)
    }
  }

  const analyzeAndSavePatterns = async () => {
    // Get vendor mappings
    const { data: vendors } = await supabase
      .from('vendors')
      .select('vendor_name, display_name')
      .eq('client_id', clientId)

    // Get all transactions
    const { data: transactions } = await supabase
      .from('transactions')
      .select('vendor_name, transaction_date, amount')
      .eq('client_id', clientId)
      .order('transaction_date', { ascending: false })

    // Group and analyze (similar to original logic)
    const vendorMap = new Map(vendors?.map(v => [v.vendor_name, v.display_name]) || [])
    const groupedByDisplay = new Map<string, any[]>()
    
    transactions?.forEach(tx => {
      const displayName = vendorMap.get(tx.vendor_name) || tx.vendor_name
      if (!groupedByDisplay.has(displayName)) {
        groupedByDisplay.set(displayName, [])
      }
      groupedByDisplay.get(displayName)!.push(tx)
    })

    // Analyze each group
    const patternRecords: PatternReview[] = []
    
    groupedByDisplay.forEach((txs, displayName) => {
      const totalValue = txs.reduce((sum, tx) => sum + Math.abs(tx.amount), 0)
      const analysis = analyzePattern(txs)
      
      patternRecords.push({
        vendor_group: displayName,
        status: 'pending',
        pattern_type: analysis.pattern,
        interval_days: analysis.interval,
        average_amount: analysis.avgAmount,
        next_date: analysis.nextDate,
        confidence: analysis.confidence,
        total_transaction_value: totalValue,
        transaction_count: txs.length
      })
    })

    // Sort by total value descending
    patternRecords.sort((a, b) => b.total_transaction_value - a.total_transaction_value)

    // Save to database
    const { error } = await supabase
      .from('pattern_reviews')
      .insert(patternRecords.map(p => ({
        ...p,
        client_id: clientId
      })))

    if (!error) {
      setPatterns(patternRecords)
      if (patternRecords.length > 0) {
        await loadTransactionsForPattern(patternRecords[0].vendor_group)
      }
    }
  }

  const analyzePattern = (transactions: any[]) => {
    if (transactions.length < 2) {
      return {
        pattern: 'irregular',
        interval: 0,
        avgAmount: transactions[0]?.amount || 0,
        confidence: 0,
        nextDate: new Date().toISOString().split('T')[0]
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
        pattern: 'irregular',
        interval: 0,
        avgAmount: Math.abs(transactions[0]?.amount || 0),
        confidence: 0,
        nextDate: new Date().toISOString().split('T')[0]
      }
    }

    // Calculate intervals
    const intervals: number[] = []
    for (let i = 0; i < recentTxs.length - 1; i++) {
      const date1 = new Date(recentTxs[i].transaction_date)
      const date2 = new Date(recentTxs[i + 1].transaction_date)
      const daysDiff = Math.abs(date1.getTime() - date2.getTime()) / (1000 * 60 * 60 * 24)
      intervals.push(daysDiff)
    }

    const avgInterval = intervals.reduce((a, b) => a + b, 0) / intervals.length

    // Determine pattern
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

    // Calculate confidence
    const variance = intervals.map(i => Math.abs(i - avgInterval))
    const avgVariance = variance.reduce((a, b) => a + b, 0) / variance.length
    const confidence = Math.max(0, Math.min(100, 100 - (avgVariance / avgInterval * 100)))

    // Average amount
    const amounts = recentTxs.map(tx => Math.abs(tx.amount))
    const avgAmount = amounts.reduce((a, b) => a + b, 0) / amounts.length

    // Next date
    const lastDate = new Date(recentTxs[0].transaction_date)
    const nextDate = new Date(lastDate.getTime() + interval * 24 * 60 * 60 * 1000)

    return {
      pattern,
      interval,
      avgAmount,
      confidence: Math.round(confidence),
      nextDate: nextDate.toISOString().split('T')[0]
    }
  }

  const loadTransactionsForPattern = async (vendorGroup: string) => {
    // Get vendor names for this group
    const { data: vendors } = await supabase
      .from('vendors')
      .select('vendor_name')
      .eq('client_id', clientId)
      .eq('display_name', vendorGroup)

    const vendorNames = vendors?.map(v => v.vendor_name) || [vendorGroup]

    // Get recent transactions
    const { data: transactions } = await supabase
      .from('transactions')
      .select('transaction_date, amount')
      .eq('client_id', clientId)
      .in('vendor_name', vendorNames)
      .order('transaction_date', { ascending: false })
      .limit(10)

    setPatterns(prev => prev.map(p => 
      p.vendor_group === vendorGroup
        ? { ...p, recent_transactions: transactions || [] }
        : p
    ))
  }

  const handleAction = async (action: 'approve' | 'skip' | 'save-edit') => {
    if (!currentPattern) return
    
    setSaving(true)
    
    try {
      let updateData: Partial<PatternReview> = {}
      
      if (action === 'approve') {
        updateData = {
          status: 'reviewed',
          reviewed_at: new Date().toISOString()
        }
      } else if (action === 'skip') {
        updateData = {
          status: 'skipped'
        }
      } else if (action === 'save-edit') {
        updateData = {
          ...editedPattern,
          status: 'reviewed',
          reviewed_at: new Date().toISOString()
        }
      }

      // Update in database
      const { error } = await supabase
        .from('pattern_reviews')
        .update(updateData)
        .eq('client_id', clientId)
        .eq('vendor_group', currentPattern.vendor_group)

      if (!error) {
        // Update local state
        setPatterns(prev => prev.map(p => 
          p.vendor_group === currentPattern.vendor_group
            ? { ...p, ...updateData }
            : p
        ))

        // Move to next pattern
        if (action !== 'save-edit' || editMode) {
          setEditMode(false)
          setEditedPattern({})
          
          // Find next pending
          const nextPendingIndex = filteredPatterns.findIndex(
            (p, idx) => idx > currentIndex && p.status === 'pending'
          )
          
          if (nextPendingIndex >= 0) {
            setCurrentIndex(nextPendingIndex)
            await loadTransactionsForPattern(filteredPatterns[nextPendingIndex].vendor_group)
          } else if (currentIndex < totalPatterns - 1) {
            setCurrentIndex(currentIndex + 1)
            await loadTransactionsForPattern(filteredPatterns[currentIndex + 1].vendor_group)
          }
        }
      }
    } catch (error) {
      console.error('Error saving pattern:', error)
    } finally {
      setSaving(false)
    }
  }

  const startEdit = () => {
    setEditMode(true)
    setEditedPattern({
      pattern_type: currentPattern.pattern_type,
      average_amount: currentPattern.average_amount,
      next_date: currentPattern.next_date
    })
  }

  const finishAllAndGenerate = async () => {
    const allReviewed = filteredPatterns.every(p => p.status !== 'pending')
    
    if (!allReviewed) {
      const confirm = window.confirm(
        `You have ${filteredPatterns.filter(p => p.status === 'pending').length} patterns pending review. ` +
        'Generate forecast anyway?'
      )
      if (!confirm) return
    }

    router.push(`/dashboard/${clientId}/forecast`)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg">Loading patterns...</div>
      </div>
    )
  }

  if (totalPatterns === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-lg mb-4">No patterns to review.</p>
          <button
            onClick={() => router.back()}
            className="px-4 py-2 bg-gray-600 text-white rounded-md"
          >
            Go Back
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold">Pattern Review - {clientId}</h1>
            </div>
            <div className="flex items-center space-x-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={showAll}
                  onChange={(e) => {
                    setShowAll(e.target.checked)
                    setCurrentIndex(0)
                  }}
                  className="mr-2"
                />
                <span className="text-sm">Show all vendors</span>
              </label>
              <button
                onClick={finishAllAndGenerate}
                className="px-4 py-2 bg-green-600 text-white rounded-md text-sm"
              >
                Generate Forecast
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Progress Bar */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progress: {reviewedCount} of {totalPatterns} reviewed</span>
            <span>{Math.round(progressPercent)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-green-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <div className="mt-2 text-xs text-gray-500">
            {showAll ? 'Showing all vendors' : `Showing vendors with >$1k in transactions`}
          </div>
        </div>

        {/* Current Pattern */}
        {currentPattern && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-2xl font-bold">{currentPattern.vendor_group}</h2>
                  <div className="mt-2 flex items-center space-x-4 text-sm text-gray-600">
                    <span>{currentPattern.transaction_count} transactions</span>
                    <span>•</span>
                    <span>${currentPattern.total_transaction_value.toLocaleString()}</span>
                    <span>•</span>
                    <span className={`px-2 py-1 rounded ${
                      currentPattern.confidence >= 80 ? 'bg-green-100 text-green-800' :
                      currentPattern.confidence >= 60 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {currentPattern.confidence}% confidence
                    </span>
                  </div>
                </div>
                <div className="text-sm text-gray-500">
                  {currentIndex + 1} of {totalPatterns}
                </div>
              </div>
            </div>

            <div className="p-6">
              {/* Pattern Details */}
              <div className="grid grid-cols-3 gap-6 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Pattern
                  </label>
                  {editMode ? (
                    <select
                      className="w-full border rounded px-3 py-2"
                      value={editedPattern.pattern_type}
                      onChange={(e) => setEditedPattern({...editedPattern, pattern_type: e.target.value})}
                    >
                      {PATTERN_OPTIONS.map(opt => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  ) : (
                    <p className="text-lg font-semibold">
                      {PATTERN_OPTIONS.find(p => p.value === currentPattern.pattern_type)?.label}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Average Amount
                  </label>
                  {editMode ? (
                    <input
                      type="number"
                      className="w-full border rounded px-3 py-2"
                      value={editedPattern.average_amount}
                      onChange={(e) => setEditedPattern({...editedPattern, average_amount: parseFloat(e.target.value)})}
                    />
                  ) : (
                    <p className="text-lg font-semibold">
                      ${currentPattern.average_amount.toLocaleString()}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Next Date
                  </label>
                  {editMode ? (
                    <input
                      type="date"
                      className="w-full border rounded px-3 py-2"
                      value={editedPattern.next_date}
                      onChange={(e) => setEditedPattern({...editedPattern, next_date: e.target.value})}
                    />
                  ) : (
                    <p className="text-lg font-semibold">
                      {new Date(currentPattern.next_date).toLocaleDateString()}
                    </p>
                  )}
                </div>
              </div>

              {/* Recent Transactions */}
              {currentPattern.recent_transactions && (
                <div className="border-t pt-4">
                  <h3 className="text-sm font-medium text-gray-700 mb-3">Recent Transactions</h3>
                  <div className="grid grid-cols-2 gap-2">
                    {currentPattern.recent_transactions.map((tx, idx) => (
                      <div key={idx} className="flex justify-between text-sm py-1 px-3 bg-gray-50 rounded">
                        <span>{new Date(tx.transaction_date).toLocaleDateString()}</span>
                        <span className="font-medium">${Math.abs(tx.amount).toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="mt-6 flex justify-center space-x-4">
                {editMode ? (
                  <>
                    <button
                      onClick={() => handleAction('save-edit')}
                      disabled={saving}
                      className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                    >
                      Save Changes
                    </button>
                    <button
                      onClick={() => {
                        setEditMode(false)
                        setEditedPattern({})
                      }}
                      className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => handleAction('approve')}
                      disabled={saving}
                      className="px-8 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 text-lg"
                    >
                      Looks Good
                    </button>
                    <button
                      onClick={startEdit}
                      disabled={saving}
                      className="px-8 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 text-lg"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleAction('skip')}
                      disabled={saving}
                      className="px-8 py-3 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 text-lg"
                    >
                      Skip
                    </button>
                  </>
                )}
              </div>

              {/* Navigation */}
              {!editMode && (
                <div className="mt-4 flex justify-between">
                  <button
                    onClick={() => {
                      if (currentIndex > 0) {
                        setCurrentIndex(currentIndex - 1)
                        loadTransactionsForPattern(filteredPatterns[currentIndex - 1].vendor_group)
                      }
                    }}
                    disabled={currentIndex === 0}
                    className="text-sm text-gray-600 hover:text-gray-900 disabled:opacity-50"
                  >
                    ← Previous
                  </button>
                  <button
                    onClick={() => {
                      if (currentIndex < totalPatterns - 1) {
                        setCurrentIndex(currentIndex + 1)
                        loadTransactionsForPattern(filteredPatterns[currentIndex + 1].vendor_group)
                      }
                    }}
                    disabled={currentIndex === totalPatterns - 1}
                    className="text-sm text-gray-600 hover:text-gray-900 disabled:opacity-50"
                  >
                    Next →
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}