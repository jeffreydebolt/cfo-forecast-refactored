'use client'

import React from 'react'

export default function TestPage() {
  return (
    <div className="min-h-screen bg-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          🎉 System Test - Configuration Working!
        </h1>
        
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-8">
          <h2 className="text-lg font-semibold text-green-800 mb-4">✅ Environment Variables Status</h2>
          <div className="space-y-2 text-sm">
            <p><strong>Supabase URL:</strong> {process.env.NEXT_PUBLIC_SUPABASE_URL ? '✅ Set' : '❌ Missing'}</p>
            <p><strong>Supabase Key:</strong> {process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ? '✅ Set' : '❌ Missing'}</p>
            <p><strong>API URL:</strong> {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="font-semibold text-blue-800 mb-2">📊 Frontend Status</h3>
            <p className="text-blue-700">React/Next.js app is running properly</p>
            <p className="text-sm text-blue-600 mt-2">This page loads without database access</p>
          </div>
          
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h3 className="font-semibold text-yellow-800 mb-2">🔗 Navigation Test</h3>
            <div className="space-y-2">
              <a 
                href="/dashboard" 
                className="block text-blue-600 hover:text-blue-800 underline"
              >
                → Dashboard
              </a>
              <a 
                href="/dashboard/BestSelf" 
                className="block text-blue-600 hover:text-blue-800 underline"
              >
                → BestSelf Client
              </a>
              <a 
                href="/dashboard/BestSelf/forecast" 
                className="block text-blue-600 hover:text-blue-800 underline"
              >
                → Cash Flow Forecast
              </a>
            </div>
          </div>
        </div>

        <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
          <h3 className="font-semibold text-gray-800 mb-4">🔧 System Information</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p><strong>Build Time:</strong> {new Date().toISOString()}</p>
              <p><strong>Node Env:</strong> {process.env.NODE_ENV || 'development'}</p>
            </div>
            <div>
              <p><strong>Vercel:</strong> {process.env.VERCEL ? 'Yes' : 'Local'}</p>
              <p><strong>Region:</strong> {process.env.VERCEL_REGION || 'N/A'}</p>
            </div>
          </div>
        </div>

        <div className="mt-8 p-4 bg-blue-600 text-white rounded-lg">
          <p className="text-center">
            If you can see this page, the Next.js app is working! 
            The 401 error must be from database/API calls.
          </p>
        </div>
      </div>
    </div>
  )
}