'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { getSupabaseClient } from '@/lib/supabase'

type VendorMapping = {
  vendor_name: string
  display_name: string
  transaction_count: number
  total_amount: number
}

export default function VendorMappingPage() {
  const router = useRouter()
  const params = useParams()
  const clientId = params.clientId as string
  
  const [vendors, setVendors] = useState<VendorMapping[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [mappingChanges, setMappingChanges] = useState<{[key: string]: string}>({})

  // Initialize Supabase client
  const supabase = getSupabaseClient()

  useEffect(() => {
    loadVendors()
  }, [clientId])

  const loadVendors = async () => {
    try {
      // Get unique vendors from transactions
      const { data: transactions, error } = await supabase
        .from('transactions')
        .select('vendor_name, amount')
        .eq('client_id', clientId)

      if (error) throw error

      // Group by vendor name
      const vendorMap = new Map<string, { count: number, total: number }>()
      
      transactions?.forEach(t => {
        const current = vendorMap.get(t.vendor_name) || { count: 0, total: 0 }
        vendorMap.set(t.vendor_name, {
          count: current.count + 1,
          total: current.total + Math.abs(t.amount)
        })
      })

      // Check existing mappings
      const { data: existingMappings } = await supabase
        .from('vendors')
        .select('vendor_name, display_name')
        .eq('client_id', clientId)

      const mappingLookup = new Map(
        existingMappings?.map(m => [m.vendor_name, m.display_name]) || []
      )

      // Apply auto-mapping rules
      const autoMapRules = [
        { pattern: /^AMAZON/i, display: 'Amazon Revenue' },
        { pattern: /^AMZN/i, display: 'Amazon Revenue' },
        { pattern: /^SHOPIFY/i, display: 'Shopify Revenue' },
        { pattern: /^SQ \*/i, display: 'Square Revenue' },
        { pattern: /^STRIPE/i, display: 'Stripe Revenue' },
        { pattern: /^PAYPAL/i, display: 'PayPal Revenue' },
        { pattern: /GOOGLE.*ADS/i, display: 'Google Ads' },
        { pattern: /META.*FACEBOOK/i, display: 'Meta Ads' },
        { pattern: /^WISE/i, display: 'Wise Transfers' }
      ]

      // Convert to array and apply mappings
      const vendorList: VendorMapping[] = Array.from(vendorMap.entries()).map(([vendor_name, stats]) => {
        // Check if already mapped
        let display_name = mappingLookup.get(vendor_name) || vendor_name
        
        // If not already mapped differently, try auto-mapping
        if (display_name === vendor_name) {
          const rule = autoMapRules.find(r => r.pattern.test(vendor_name))
          if (rule) {
            display_name = rule.display
          }
        }

        return {
          vendor_name,
          display_name,
          transaction_count: stats.count,
          total_amount: stats.total
        }
      })

      // Sort by total amount descending
      vendorList.sort((a, b) => b.total_amount - a.total_amount)
      
      setVendors(vendorList)
    } catch (error) {
      console.error('Error loading vendors:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleMappingChange = (vendor_name: string, new_display_name: string) => {
    setMappingChanges(prev => ({
      ...prev,
      [vendor_name]: new_display_name
    }))
  }

  const getCurrentDisplayName = (vendor: VendorMapping) => {
    return mappingChanges[vendor.vendor_name] !== undefined 
      ? mappingChanges[vendor.vendor_name] 
      : vendor.display_name
  }

  const saveMappings = async () => {
    setSaving(true)
    try {
      // Prepare vendor records
      const vendorRecords = vendors.map(v => ({
        client_id: clientId,
        vendor_name: v.vendor_name,
        display_name: getCurrentDisplayName(v),
        created_at: new Date().toISOString()
      }))

      // Delete existing mappings for this client
      await supabase
        .from('vendors')
        .delete()
        .eq('client_id', clientId)

      // Insert new mappings
      const { error } = await supabase
        .from('vendors')
        .insert(vendorRecords)

      if (error) throw error

      alert('Vendor mappings saved successfully!')
      
      // Navigate to pattern review
      router.push(`/dashboard/${clientId}/pattern-review`)
      
    } catch (error) {
      console.error('Error saving mappings:', error)
      alert('Failed to save mappings. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg">Loading vendors...</div>
      </div>
    )
  }

  // Group vendors by their current display name
  const groupedVendors = vendors.reduce((acc, vendor) => {
    const displayName = getCurrentDisplayName(vendor)
    if (!acc[displayName]) {
      acc[displayName] = []
    }
    acc[displayName].push(vendor)
    return acc
  }, {} as { [key: string]: VendorMapping[] })

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
              <h1 className="text-xl font-semibold">Vendor Mapping - {clientId}</h1>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white shadow rounded-lg p-6 mb-6">
            <h2 className="text-lg font-medium text-gray-900 mb-2">Review and Group Vendors</h2>
            <p className="text-sm text-gray-600 mb-4">
              Auto-mapping has been applied where possible. You can manually group vendors by giving them the same display name.
            </p>
            <div className="text-sm text-gray-500">
              Found {vendors.length} unique vendors | {Object.keys(groupedVendors).length} groups after mapping
            </div>
          </div>

          <div className="bg-white shadow rounded-lg overflow-hidden">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Original Vendor Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Display Name / Group
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Transactions
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Amount
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {vendors.map((vendor) => (
                  <tr key={vendor.vendor_name}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {vendor.vendor_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="text"
                        className="text-sm border-gray-300 rounded-md w-full"
                        value={getCurrentDisplayName(vendor)}
                        onChange={(e) => handleMappingChange(vendor.vendor_name, e.target.value)}
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                      {vendor.transaction_count}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                      ${vendor.total_amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-6 flex justify-between">
            <button
              onClick={() => router.back()}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Back
            </button>
            <button
              onClick={saveMappings}
              disabled={saving}
              className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Mappings & Continue'}
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}