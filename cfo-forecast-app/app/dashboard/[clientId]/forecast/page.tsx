'use client'

import React, { useState } from 'react'
import { useParams } from 'next/navigation'
import ForecastSpreadsheet from '../../../../components/ForecastSpreadsheet'
import ReconciliationPanel from '../../../../components/ReconciliationPanel'
import Link from 'next/link'

export default function ForecastPage() {
  const params = useParams()
  const clientId = params.clientId as string
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-4">
              <Link 
                href={`/dashboard/${clientId}`}
                className="text-blue-600 hover:text-blue-800"
              >
                ← Back to Dashboard
              </Link>
              <h1 className="text-3xl font-bold text-gray-900">
                Cash Flow Forecast - {clientId}
              </h1>
            </div>
            
            <div className="flex space-x-3">
              <Link
                href={`/dashboard/${clientId}/vendor-mapping`}
                className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-md text-sm font-medium"
              >
                Vendor Mapping
              </Link>
              <Link
                href={`/dashboard/${clientId}/pattern-review`}
                className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-md text-sm font-medium"
              >
                Pattern Review
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <ReconciliationPanel 
          clientId={clientId} 
          onReconciliationComplete={() => setRefreshTrigger(prev => prev + 1)}
        />
        <ForecastSpreadsheet 
          clientId={clientId} 
          key={refreshTrigger} 
        />
      </div>
    </div>
  )
}