'use client'

import React from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'

export default function ClientDashboardPage() {
  const params = useParams()
  const clientId = params.clientId as string

  const tools = [
    {
      name: 'Cash Flow Forecast',
      description: 'Spreadsheet-style 12-week cash flow forecast with actual vs forecast',
      href: `/dashboard/${clientId}/forecast`,
      icon: '📊',
      color: 'bg-blue-500 hover:bg-blue-600',
      featured: true
    },
    {
      name: 'Vendor Mapping',
      description: 'Map vendor names to forecast groups for automated categorization',
      href: `/dashboard/${clientId}/vendor-mapping`,
      icon: '🔗',
      color: 'bg-green-500 hover:bg-green-600'
    },
    {
      name: 'Pattern Review',
      description: 'Review detected patterns and forecast rules for each vendor group',
      href: `/dashboard/${clientId}/pattern-review-v2`,
      icon: '🔍',
      color: 'bg-purple-500 hover:bg-purple-600'
    }
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-4">
              <Link 
                href="/dashboard"
                className="text-blue-600 hover:text-blue-800"
              >
                ← All Clients
              </Link>
              <h1 className="text-3xl font-bold text-gray-900">
                {clientId} Dashboard
              </h1>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Featured Tool */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Featured</h2>
          <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl shadow-lg overflow-hidden">
            <div className="px-8 py-6 text-white">
              <div className="flex items-center space-x-4">
                <div className="text-4xl">📊</div>
                <div className="flex-1">
                  <h3 className="text-2xl font-bold mb-2">Cash Flow Forecast</h3>
                  <p className="text-blue-100 mb-4">
                    Your complete 12-week rolling cash flow forecast - looks and works like Google Sheets
                  </p>
                  <div className="flex space-x-4 text-sm">
                    <span className="bg-blue-400 bg-opacity-50 px-3 py-1 rounded-full">✓ Auto-reconciliation</span>
                    <span className="bg-blue-400 bg-opacity-50 px-3 py-1 rounded-full">✓ Edit-in-place</span>
                    <span className="bg-blue-400 bg-opacity-50 px-3 py-1 rounded-full">✓ Pattern detection</span>
                  </div>
                </div>
                <div>
                  <Link
                    href={`/dashboard/${clientId}/forecast`}
                    className="bg-white text-blue-600 font-semibold px-6 py-3 rounded-lg hover:bg-blue-50 transition-colors inline-flex items-center"
                  >
                    Open Forecast →
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Tools Grid */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Tools</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {tools.filter(tool => !tool.featured).map((tool) => (
              <Link
                key={tool.name}
                href={tool.href}
                className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-6 border border-gray-200"
              >
                <div className="flex items-start space-x-4">
                  <div className="text-3xl">{tool.icon}</div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {tool.name}
                    </h3>
                    <p className="text-gray-600 text-sm">
                      {tool.description}
                    </p>
                  </div>
                  <div className="text-gray-400">
                    →
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Quick Start Guide */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">🚀 Quick Start</h2>
          <div className="space-y-4">
            <div className="flex items-start space-x-3">
              <div className="bg-blue-100 text-blue-600 rounded-full w-8 h-8 flex items-center justify-center text-sm font-semibold">1</div>
              <div>
                <h3 className="font-medium text-gray-900">Set up vendor mapping</h3>
                <p className="text-gray-600 text-sm">Map your vendor names to forecast categories (revenue, expenses, etc.)</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="bg-blue-100 text-blue-600 rounded-full w-8 h-8 flex items-center justify-center text-sm font-semibold">2</div>
              <div>
                <h3 className="font-medium text-gray-900">Review patterns</h3>
                <p className="text-gray-600 text-sm">Check detected patterns and adjust forecast rules as needed</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="bg-blue-100 text-blue-600 rounded-full w-8 h-8 flex items-center justify-center text-sm font-semibold">3</div>
              <div>
                <h3 className="font-medium text-gray-900">Use the forecast</h3>
                <p className="text-gray-600 text-sm">View your 12-week forecast and import Mercury CSV files for reconciliation</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}