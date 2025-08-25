'use client'

import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'

interface ReconciliationPanelProps {
  clientId: string
  onReconciliationComplete?: () => void
}

const ReconciliationPanel: React.FC<ReconciliationPanelProps> = ({ 
  clientId, 
  onReconciliationComplete 
}) => {
  const [isUploading, setIsUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<string | null>(null)
  const [selectedWeek, setSelectedWeek] = useState<string>('')

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  // Get current Monday for default week selection
  const getCurrentMonday = () => {
    const today = new Date()
    const dayOfWeek = today.getDay()
    const diff = today.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1) // adjust when day is Sunday
    const monday = new Date(today.setDate(diff))
    return monday.toISOString().split('T')[0]
  }

  React.useEffect(() => {
    setSelectedWeek(getCurrentMonday())
  }, [])

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (!acceptedFiles.length || !selectedWeek) {
      setUploadStatus('Please select a file and week to reconcile')
      return
    }

    const file = acceptedFiles[0]
    
    // Validate file type
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setUploadStatus('Please upload a CSV file')
      return
    }

    setIsUploading(true)
    setUploadStatus('Processing Mercury CSV...')

    try {
      // Create FormData
      const formData = new FormData()
      formData.append('file', file)
      formData.append('client_id', clientId)
      formData.append('week_start_date', selectedWeek)

      // Upload and process
      const response = await axios.post(`${API_BASE}/api/forecast/reconcile`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      if (response.data.success) {
        setUploadStatus('✅ Reconciliation completed successfully!')
        if (onReconciliationComplete) {
          onReconciliationComplete()
        }
      } else {
        setUploadStatus('❌ Reconciliation failed: ' + response.data.message)
      }
    } catch (error: any) {
      console.error('Reconciliation error:', error)
      setUploadStatus('❌ Reconciliation failed: ' + (error.response?.data?.detail || error.message))
    } finally {
      setIsUploading(false)
    }
  }, [clientId, selectedWeek, API_BASE, onReconciliationComplete])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv']
    },
    multiple: false,
    disabled: isUploading
  })

  // Generate week options (current week and previous 4 weeks)
  const getWeekOptions = () => {
    const options = []
    const today = new Date()
    
    for (let i = 0; i < 5; i++) {
      const date = new Date(today)
      date.setDate(today.getDate() - (i * 7))
      
      const dayOfWeek = date.getDay()
      const diff = date.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1)
      const monday = new Date(date.setDate(diff))
      
      const dateStr = monday.toISOString().split('T')[0]
      const displayStr = monday.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        year: 'numeric'
      })
      
      options.push({
        value: dateStr,
        label: `Week of ${displayStr}`,
        isCurrent: i === 0
      })
    }
    
    return options
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Monday Reconciliation
        </h3>
        <div className="text-sm text-gray-500">
          Import Mercury CSV to update actuals
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Week Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Week to Reconcile
          </label>
          <select
            value={selectedWeek}
            onChange={(e) => setSelectedWeek(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isUploading}
          >
            {getWeekOptions().map((option) => (
              <option key={option.value} value={option.value}>
                {option.label} {option.isCurrent ? '(Current)' : ''}
              </option>
            ))}
          </select>
        </div>

        {/* File Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Mercury CSV File
          </label>
          <div
            {...getRootProps()}
            className={`
              border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors
              ${isDragActive 
                ? 'border-blue-400 bg-blue-50' 
                : 'border-gray-300 hover:border-gray-400'
              }
              ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
            `}
          >
            <input {...getInputProps()} />
            
            <div className="flex flex-col items-center">
              <svg
                className="w-8 h-8 text-gray-400 mb-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              
              {isUploading ? (
                <p className="text-sm text-gray-600">Processing...</p>
              ) : isDragActive ? (
                <p className="text-sm text-gray-600">Drop the CSV file here...</p>
              ) : (
                <>
                  <p className="text-sm text-gray-600">
                    Drag & drop Mercury CSV file here
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    or click to browse
                  </p>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Status Message */}
      {uploadStatus && (
        <div className={`mt-4 p-3 rounded-md ${
          uploadStatus.includes('✅') 
            ? 'bg-green-50 text-green-800 border border-green-200'
            : uploadStatus.includes('❌')
            ? 'bg-red-50 text-red-800 border border-red-200'
            : 'bg-blue-50 text-blue-800 border border-blue-200'
        }`}>
          <p className="text-sm">{uploadStatus}</p>
        </div>
      )}

      {/* Process Steps */}
      <div className="mt-6 bg-gray-50 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-2">Reconciliation Process:</h4>
        <ol className="text-sm text-gray-600 space-y-1">
          <li>1. Import Mercury CSV transactions for selected week</li>
          <li>2. Match transactions to vendor groups using existing mappings</li>
          <li>3. Update actual amounts in forecast records</li>
          <li>4. Calculate variances (Actual vs Forecast)</li>
          <li>5. Lock the reconciled week from further edits</li>
          <li>6. Update beginning cash for next week</li>
        </ol>
      </div>
    </div>
  )
}

export default ReconciliationPanel