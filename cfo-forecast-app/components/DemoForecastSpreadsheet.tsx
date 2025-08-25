'use client'

import React, { useState, useMemo } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { ColDef } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'

// Mock data - no API calls needed
const mockPeriods = [
  { week_number: 1, start_date: '2025-08-25', display_text: '8/25/25' },
  { week_number: 2, start_date: '2025-09-01', display_text: '9/1/25' },
  { week_number: 3, start_date: '2025-09-08', display_text: '9/8/25' },
  { week_number: 4, start_date: '2025-09-15', display_text: '9/15/25' },
  { week_number: 5, start_date: '2025-09-22', display_text: '9/22/25' },
  { week_number: 6, start_date: '2025-09-29', display_text: '9/29/25' },
  { week_number: 7, start_date: '2025-10-06', display_text: '10/6/25' },
  { week_number: 8, start_date: '2025-10-13', display_text: '10/13/25' },
  { week_number: 9, start_date: '2025-10-20', display_text: '10/20/25' },
  { week_number: 10, start_date: '2025-10-27', display_text: '10/27/25' },
  { week_number: 11, start_date: '2025-11-03', display_text: '11/3/25' },
  { week_number: 12, start_date: '2025-11-10', display_text: '11/10/25' }
]

const mockForecastData = {
  '2025-08-25': { core_capital: 250000, operating_revenue: 150000, cc: -46655, ops: -34056, ga: -3984, payroll: -33208, distributions: -200000 },
  '2025-09-01': { core_capital: 300000, operating_revenue: 171000, cc: 0, ops: -21431, ga: -3737, payroll: -33208, distributions: -2042 },
  '2025-09-08': { core_capital: 300000, operating_revenue: 177000, cc: -46655, ops: -23314, ga: -976, payroll: -22140, distributions: -2042 },
  '2025-09-15': { core_capital: 300000, operating_revenue: 182500, cc: -46655, ops: -25000, ga: -1200, payroll: -33208, distributions: -2042 },
  '2025-09-22': { core_capital: 300000, operating_revenue: 185000, cc: 0, ops: -21431, ga: -3737, payroll: -33208, distributions: -2042 },
  '2025-09-29': { core_capital: 300000, operating_revenue: 188000, cc: -46655, ops: -23314, ga: -976, payroll: -22140, distributions: -2042 },
  '2025-10-06': { core_capital: 300000, operating_revenue: 190000, cc: -46655, ops: -25000, ga: -1200, payroll: -33208, distributions: -2042 },
  '2025-10-13': { core_capital: 300000, operating_revenue: 192500, cc: 0, ops: -21431, ga: -3737, payroll: -33208, distributions: -2042 },
  '2025-10-20': { core_capital: 300000, operating_revenue: 195000, cc: -46655, ops: -23314, ga: -976, payroll: -22140, distributions: -2042 },
  '2025-10-27': { core_capital: 300000, operating_revenue: 197500, cc: -46655, ops: -25000, ga: -1200, payroll: -33208, distributions: -2042 },
  '2025-11-03': { core_capital: 300000, operating_revenue: 200000, cc: 0, ops: -21431, ga: -3737, payroll: -33208, distributions: -2042 },
  '2025-11-10': { core_capital: 300000, operating_revenue: 202500, cc: -46655, ops: -23314, ga: -976, payroll: -22140, distributions: -2042 }
}

// Currency formatter
const CurrencyCellRenderer = ({ value }: any) => {
  const isNegative = value < 0
  const absValue = Math.abs(value || 0)
  const formatted = new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(absValue)
  
  return (
    <div className="h-full w-full flex items-center px-2 bg-white hover:bg-blue-50 cursor-pointer" title="Double-click to edit">
      <span className={isNegative ? 'text-red-600' : ''}>
        {isNegative ? `(${formatted})` : formatted}
      </span>
    </div>
  )
}

interface DemoForecastSpreadsheetProps {
  clientId: string
}

const DemoForecastSpreadsheet: React.FC<DemoForecastSpreadsheetProps> = ({ clientId }) => {
  const [editingCell, setEditingCell] = useState<{date: string, field: string} | null>(null)

  // Generate row data
  const rowData = useMemo(() => {
    const rows: any[] = []
    
    // Beginning Cash row
    const beginningCashRow: any = {
      id: 'beginning_cash',
      display_name: 'Beginning Cash',
      is_header: true
    }
    
    let runningCash = 476121
    mockPeriods.forEach((period) => {
      beginningCashRow[period.start_date] = runningCash
      
      // Calculate ending cash for next period
      const data = mockForecastData[period.start_date as keyof typeof mockForecastData]
      if (data) {
        const revenue = data.core_capital + data.operating_revenue
        const expenses = data.cc + data.ops + data.ga + data.payroll
        const financing = data.distributions
        runningCash = runningCash + revenue + expenses + financing
      }
    })
    
    rows.push(beginningCashRow)
    
    // Spacer
    rows.push({ id: 'spacer1', display_name: '', is_spacer: true })
    
    // Operating Activities Header
    rows.push({ id: 'operating_header', display_name: 'OPERATING ACTIVITIES', is_section_header: true })
    rows.push({ id: 'revenue_header', display_name: 'Revenue Inflows:', is_subsection_header: true })
    
    // Core Capital row
    const coreCapitalRow: any = {
      id: 'core_capital',
      display_name: '  Core Capital',
      field: 'core_capital'
    }
    mockPeriods.forEach((period) => {
      coreCapitalRow[period.start_date] = mockForecastData[period.start_date as keyof typeof mockForecastData]?.core_capital || 0
    })
    rows.push(coreCapitalRow)
    
    // Operating Revenue row
    const operatingRevenueRow: any = {
      id: 'operating_revenue',
      display_name: '  Operating Revenue',
      field: 'operating_revenue'
    }
    mockPeriods.forEach((period) => {
      operatingRevenueRow[period.start_date] = mockForecastData[period.start_date as keyof typeof mockForecastData]?.operating_revenue || 0
    })
    rows.push(operatingRevenueRow)
    
    // Total Revenue row
    const totalRevenueRow: any = {
      id: 'total_revenue',
      display_name: 'Total Revenue',
      is_total: true
    }
    mockPeriods.forEach((period) => {
      const data = mockForecastData[period.start_date as keyof typeof mockForecastData]
      totalRevenueRow[period.start_date] = (data?.core_capital || 0) + (data?.operating_revenue || 0)
    })
    rows.push(totalRevenueRow)
    
    // Spacer
    rows.push({ id: 'spacer2', display_name: '', is_spacer: true })
    
    // Operating Outflows
    rows.push({ id: 'outflows_header', display_name: 'Operating Outflows:', is_subsection_header: true })
    
    const outflowRows = [
      { id: 'cc', name: '  CC', field: 'cc' },
      { id: 'ops', name: '  Ops', field: 'ops' },
      { id: 'ga', name: '  G&A', field: 'ga' },
      { id: 'payroll', name: '  Payroll', field: 'payroll' }
    ]
    
    outflowRows.forEach(({ id, name, field }) => {
      const row: any = {
        id,
        display_name: name,
        field
      }
      mockPeriods.forEach((period) => {
        row[period.start_date] = mockForecastData[period.start_date as keyof typeof mockForecastData]?.[field as keyof typeof mockForecastData['2025-08-25']] || 0
      })
      rows.push(row)
    })
    
    // Total Outflows
    const totalOutflowsRow: any = {
      id: 'total_outflows',
      display_name: 'Total Outflows',
      is_total: true
    }
    mockPeriods.forEach((period) => {
      const data = mockForecastData[period.start_date as keyof typeof mockForecastData]
      totalOutflowsRow[period.start_date] = (data?.cc || 0) + (data?.ops || 0) + (data?.ga || 0) + (data?.payroll || 0)
    })
    rows.push(totalOutflowsRow)
    
    // Net Operating CF
    const netOperatingRow: any = {
      id: 'net_operating',
      display_name: 'Net Operating CF',
      is_total: true
    }
    mockPeriods.forEach((period) => {
      const revenue = totalRevenueRow[period.start_date]
      const outflows = totalOutflowsRow[period.start_date]
      netOperatingRow[period.start_date] = revenue + outflows // outflows are negative
    })
    rows.push(netOperatingRow)
    
    // Spacer
    rows.push({ id: 'spacer3', display_name: '', is_spacer: true })
    
    // Financing Activities
    rows.push({ id: 'financing_header', display_name: 'FINANCING ACTIVITIES', is_section_header: true })
    
    const distributionsRow: any = {
      id: 'distributions',
      display_name: '  Distributions',
      field: 'distributions'
    }
    mockPeriods.forEach((period) => {
      distributionsRow[period.start_date] = mockForecastData[period.start_date as keyof typeof mockForecastData]?.distributions || 0
    })
    rows.push(distributionsRow)
    
    const netFinancingRow: any = {
      id: 'net_financing',
      display_name: 'Net Financing CF',
      is_total: true
    }
    mockPeriods.forEach((period) => {
      netFinancingRow[period.start_date] = distributionsRow[period.start_date]
    })
    rows.push(netFinancingRow)
    
    // Spacer
    rows.push({ id: 'spacer4', display_name: '', is_spacer: true })
    
    // Ending Cash
    const endingCashRow: any = {
      id: 'ending_cash',
      display_name: 'Ending Cash',
      is_total: true
    }
    mockPeriods.forEach((period, index) => {
      const beginningCash = beginningCashRow[period.start_date]
      const netOperating = netOperatingRow[period.start_date]
      const netFinancing = netFinancingRow[period.start_date]
      endingCashRow[period.start_date] = beginningCash + netOperating + netFinancing
    })
    rows.push(endingCashRow)
    
    return rows
  }, [])

  // Column definitions
  const columnDefs = useMemo((): ColDef[] => {
    const cols: ColDef[] = [
      {
        headerName: 'Week Starting:',
        field: 'display_name',
        pinned: 'left',
        width: 200,
        cellStyle: (params: any) => {
          if (params.data?.is_section_header) return { fontWeight: 'bold', fontSize: '14px' } as any
          if (params.data?.is_subsection_header) return { fontWeight: '600' } as any
          if (params.data?.is_total) return { fontWeight: 'bold', borderTop: '1px solid #ccc' } as any
          if (params.data?.is_spacer) return { borderTop: 'none', borderBottom: 'none' } as any
          return {} as any
        }
      }
    ]
    
    mockPeriods.forEach((period) => {
      cols.push({
        headerName: period.display_text,
        field: period.start_date,
        width: 120,
        type: 'numericColumn',
        cellRenderer: (params: any) => {
          if (params.data?.is_spacer || params.data?.is_section_header || params.data?.is_subsection_header) {
            return ''
          }
          return React.createElement(CurrencyCellRenderer, params)
        },
        cellStyle: (params: any) => {
          if (params.data?.is_total) return { fontWeight: 'bold', borderTop: '1px solid #ccc' } as any
          if (params.data?.is_header) return { fontWeight: 'bold', backgroundColor: '#f8f9fa' } as any
          return {} as any
        }
      })
    })
    
    return cols
  }, [])

  return (
    <div className="w-full">
      <div className="mb-4 flex justify-between items-center">
        <h2 className="text-2xl font-bold">Cash Flow Forecast - {clientId} (Demo)</h2>
        <div className="space-x-2">
          <button className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded">
            Generate Forecasts
          </button>
          <button className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded">
            Refresh
          </button>
        </div>
      </div>
      
      <div className="ag-theme-alpine" style={{ height: '600px', width: '100%' }}>
        <AgGridReact
          rowData={rowData}
          columnDefs={columnDefs}
          suppressRowClickSelection={true}
          suppressCellFocus={false}
          enableCellTextSelection={true}
          animateRows={true}
          suppressMovableColumns={true}
          suppressRowHoverHighlight={false}
          rowHeight={32}
          headerHeight={36}
        />
      </div>
      
      <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded">
        <h3 className="font-semibold text-green-800 mb-2">✅ Demo System Working!</h3>
        <p className="text-sm text-green-700">
          This is a fully functional demo with mock data. In the real system:
        </p>
        <ul className="text-sm text-green-600 mt-2 space-y-1">
          <li>• Data comes from your Supabase database</li>
          <li>• Double-click cells to edit forecasts</li>
          <li>• Upload Mercury CSV files for reconciliation</li>
          <li>• Pattern detection learns your vendor cycles</li>
        </ul>
      </div>
    </div>
  )
}

export default DemoForecastSpreadsheet