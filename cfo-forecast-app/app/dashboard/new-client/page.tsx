'use client'

import { useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useDropzone } from 'react-dropzone'
import { parseCSV } from '@/utils/csv-parser'

export default function NewClientPage() {
  const [clientName, setClientName] = useState('')
  const [startingBalance, setStartingBalance] = useState('')
  const [csvFile, setCsvFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const router = useRouter()

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setCsvFile(acceptedFiles[0])
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.csv']
    },
    maxFiles: 1
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!clientName || !csvFile || !startingBalance) return

    setUploading(true)

    try {
      // Parse CSV client-side
      const { transactions, skipped } = await parseCSV(csvFile, clientName)
      
      if (transactions.length === 0) {
        throw new Error('No valid transactions found in CSV')
      }
      
      // Send parsed transactions to API
      const response = await fetch('/api/save-transactions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transactions,
          clientName
        }),
      })

      const result = await response.json()

      if (response.ok) {
        alert(`Client "${clientName}" created successfully!\\n\\nImported: ${transactions.length} transactions\\nSkipped: ${skipped} transactions\\n\\nNext: Review vendor mappings.`)
        router.push(`/dashboard/${clientName}/vendor-mapping`)
      } else {
        const errorMsg = result.details ? `${result.error}: ${result.details}` : result.error || 'Upload failed'
        throw new Error(errorMsg)
      }

    } catch (error: any) {
      setUploading(false)
      const errorMessage = error?.details || (error instanceof Error ? error.message : 'Error uploading file. Please try again.')
      console.error('Upload error:', error)
      alert(errorMessage)
    }
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
              <h1 className="text-xl font-semibold">Add New Client</h1>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-3xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Client Info */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Client Information</h2>
              
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label htmlFor="clientName" className="block text-sm font-medium text-gray-700">
                    Client Name
                  </label>
                  <input
                    type="text"
                    id="clientName"
                    required
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                    placeholder="e.g. BestSelf Co"
                    value={clientName}
                    onChange={(e) => setClientName(e.target.value)}
                  />
                </div>
                
                <div>
                  <label htmlFor="startingBalance" className="block text-sm font-medium text-gray-700">
                    Starting Cash Balance
                  </label>
                  <input
                    type="number"
                    id="startingBalance"
                    required
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                    placeholder="100000"
                    value={startingBalance}
                    onChange={(e) => setStartingBalance(e.target.value)}
                  />
                </div>
              </div>
            </div>

            {/* CSV Upload */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Bank Transaction CSV</h2>
              <p className="text-sm text-gray-600 mb-4">
                Upload a CSV file with your bank transactions. Supported formats: Mercury, Chase, Wells Fargo.
              </p>
              
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${"${"}
                  isDragActive 
                    ? 'border-indigo-400 bg-indigo-50' 
                    : csvFile 
                    ? 'border-green-400 bg-green-50' 
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <input {...getInputProps()} />
                {csvFile ? (
                  <div className="text-green-600">
                    <svg className="mx-auto h-12 w-12 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="font-medium">{csvFile.name}</p>
                    <p className="text-sm text-gray-500">{(csvFile.size / 1024).toFixed(1)} KB</p>
                  </div>
                ) : (
                  <div className="text-gray-400">
                    <svg className="mx-auto h-12 w-12 mb-4" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                      <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    <p className="mb-2">
                      {isDragActive ? 'Drop your CSV file here' : 'Drag and drop your CSV file here'}
                    </p>
                    <p className="text-sm text-gray-500">or click to browse</p>
                  </div>
                )}
              </div>
              
              {csvFile && (
                <div className="mt-4 text-sm text-gray-600">
                  <p><strong>Next steps after upload:</strong></p>
                  <ol className="list-decimal list-inside mt-2 space-y-1">
                    <li>Review and group vendor names</li>
                    <li>Adjust payment patterns and frequencies</li>
                    <li>Generate 13-week cash flow forecast</li>
                  </ol>
                </div>
              )}
            </div>

            {/* Submit */}
            <div className="flex justify-end space-x-4">
              <button
                type="button"
                onClick={() => router.back()}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!clientName || !csvFile || !startingBalance || uploading}
                className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploading ? 'Creating Client...' : 'Create Client & Import Data'}
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  )
}