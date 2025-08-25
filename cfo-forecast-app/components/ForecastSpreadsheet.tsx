'use client'

import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { ColDef, GridReadyEvent, CellValueChangedEvent } from 'ag-grid-community'
import axios from 'axios'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'

// Types
interface ForecastData {
  [date: string]: {
    [category: string]: {
      [subcategory: string]: {
        forecasted: number
        actual: number
        variance: number
        is_actual: boolean
      }
    }
  }
}

interface CashBalance {
  balance_date: string
  beginning_balance: number
  ending_balance?: number
}

interface DashboardData {
  forecast_data: ForecastData
  cash_balances: { [date: string]: CashBalance }
  start_date: string
  end_date: string
}

interface Period {
  week_number: number
  start_date: string
  end_date: string
  display_text: string
}

interface VendorGroup {
  id: number
  group_name: string
  display_name: string
  category: string
  subcategory: string
  is_inflow: boolean
}

// Custom cell renderer for currency values
const CurrencyCellRenderer = ({ value, data }: any) => {
  const isNegative = value < 0
  const absValue = Math.abs(value)
  const formatted = new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(absValue)
  
  // Style based on actual vs forecast
  const isActual = data?.is_actual
  const className = isActual ? 'bg-green-50' : 'bg-white'
  
  return (
    <div className={`${className} h-full w-full flex items-center px-2`}>
      <span className={isNegative ? 'text-red-600' : ''}>
        {isNegative ? `(${formatted})` : formatted}
      </span>
    </div>
  )
}

// Editable currency cell renderer
const EditableCurrencyCellRenderer = ({ value, setValue, data }: any) => {
  const [editing, setEditing] = useState(false)
  const [editValue, setEditValue] = useState(value?.toString() || '0')
  
  const handleDoubleClick = () => {
    setEditing(true)
    setEditValue(Math.abs(value)?.toString() || '0')
  }
  
  const handleSubmit = () => {
    const newValue = parseFloat(editValue) || 0
    const finalValue = data?.is_inflow === false ? -Math.abs(newValue) : Math.abs(newValue)
    setValue(finalValue)
    setEditing(false)
  }
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmit()
    } else if (e.key === 'Escape') {
      setEditing(false)
      setEditValue(Math.abs(value)?.toString() || '0')
    }
  }
  
  if (editing) {
    return (
      <input
        type="number"
        value={editValue}
        onChange={(e) => setEditValue(e.target.value)}
        onBlur={handleSubmit}
        onKeyDown={handleKeyDown}
        className="w-full h-full px-2 border-2 border-blue-500 outline-none"
        autoFocus
      />
    )
  }
  
  const isNegative = value < 0
  const absValue = Math.abs(value || 0)
  const formatted = new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(absValue)
  
  const isActual = data?.is_actual
  const className = isActual ? 'bg-green-50' : 'bg-white hover:bg-blue-50 cursor-pointer'
  
  return (
    <div 
      className={`${className} h-full w-full flex items-center px-2`}
      onDoubleClick={handleDoubleClick}
      title="Double-click to edit"
    >
      <span className={isNegative ? 'text-red-600' : ''}>
        {isNegative ? `(${formatted})` : formatted}
      </span>
    </div>
  )
}

interface ForecastSpreadsheetProps {
  clientId: string
}

const ForecastSpreadsheet: React.FC<ForecastSpreadsheetProps> = ({ clientId }) => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [periods, setPeriods] = useState<Period[]>([])
  const [vendorGroups, setVendorGroups] = useState<VendorGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  // Fetch data
  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      
      const [dashboardRes, periodsRes, vendorGroupsRes] = await Promise.all([
        axios.get(`${API_BASE}/api/forecast/dashboard/${clientId}?weeks=12`),
        axios.get(`${API_BASE}/api/forecast/periods/${clientId}?weeks=12`),
        axios.get(`${API_BASE}/api/forecast/vendor-groups/${clientId}`)
      ])
      
      setDashboardData(dashboardRes.data)
      setPeriods(periodsRes.data.periods)
      setVendorGroups(vendorGroupsRes.data.vendor_groups)
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data')
      console.error('Error fetching data:', err)
    } finally {
      setLoading(false)
    }
  }, [clientId, API_BASE])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  // Update cell value
  const updateCellValue = useCallback(async (
    date: string, 
    vendorGroupId: number, 
    newAmount: number
  ) => {
    try {
      await axios.post(`${API_BASE}/api/forecast/cell-update`, {
        client_id: clientId,
        forecast_date: date,
        vendor_group_id: vendorGroupId,
        new_amount: newAmount
      })
      
      // Refresh data
      fetchData()
    } catch (err) {
      console.error('Error updating cell:', err)
    }
  }, [clientId, API_BASE, fetchData])

  // Generate row data for AG Grid
  const rowData = useMemo(() => {
    if (!dashboardData || !vendorGroups.length || !periods.length) return []
    
    const rows: any[] = []
    
    // Cash balances row
    const cashBalanceRow = {
      id: 'beginning_cash',
      category: 'cash',
      subcategory: 'beginning_balance',
      display_name: 'Beginning Cash',
      is_inflow: true,
      is_header: true
    }
    
    periods.forEach((period) => {
      const balance = dashboardData.cash_balances[period.start_date]
      cashBalanceRow[period.start_date] = balance?.beginning_balance || 0
    })
    rows.push(cashBalanceRow)
    
    // Add empty row
    rows.push({
      id: 'spacer_1',
      display_name: '',
      is_spacer: true
    })
    
    // Revenue section header
    rows.push({
      id: 'revenue_header',
      display_name: 'OPERATING ACTIVITIES',
      is_section_header: true
    })
    
    rows.push({
      id: 'revenue_inflows_header',
      display_name: 'Revenue Inflows:',
      is_subsection_header: true
    })
    
    // Revenue rows
    const revenueGroups = vendorGroups.filter(vg => vg.category === 'revenue')
    revenueGroups.forEach(vg => {
      const row = {
        id: `vendor_group_${vg.id}`,
        vendor_group_id: vg.id,
        category: vg.category,
        subcategory: vg.subcategory,
        display_name: `  ${vg.display_name}`,
        is_inflow: vg.is_inflow
      }
      
      periods.forEach((period) => {
        const data = dashboardData.forecast_data[period.start_date]?.[vg.category]?.[vg.subcategory]
        row[period.start_date] = data?.is_actual ? data.actual : data?.forecasted || 0
        row[`${period.start_date}_is_actual`] = data?.is_actual || false
      })
      
      rows.push(row)
    })
    
    // Total Revenue row
    const totalRevenueRow = {
      id: 'total_revenue',
      display_name: 'Total Revenue',
      is_total: true,
      is_inflow: true
    }
    
    periods.forEach((period) => {
      let total = 0
      revenueGroups.forEach(vg => {
        const data = dashboardData.forecast_data[period.start_date]?.[vg.category]?.[vg.subcategory]
        total += data?.is_actual ? data.actual : data?.forecasted || 0
      })
      totalRevenueRow[period.start_date] = total
    })
    rows.push(totalRevenueRow)
    
    // Add empty row
    rows.push({
      id: 'spacer_2',
      display_name: '',
      is_spacer: true
    })
    
    // Operating Outflows
    rows.push({
      id: 'operating_outflows_header',
      display_name: 'Operating Outflows:',
      is_subsection_header: true
    })
    
    const operatingGroups = vendorGroups.filter(vg => vg.category === 'operating')
    operatingGroups.forEach(vg => {
      const row = {
        id: `vendor_group_${vg.id}`,
        vendor_group_id: vg.id,
        category: vg.category,
        subcategory: vg.subcategory,
        display_name: `  ${vg.display_name}`,
        is_inflow: vg.is_inflow
      }
      
      periods.forEach((period) => {
        const data = dashboardData.forecast_data[period.start_date]?.[vg.category]?.[vg.subcategory]
        row[period.start_date] = data?.is_actual ? data.actual : data?.forecasted || 0
        row[`${period.start_date}_is_actual`] = data?.is_actual || false
      })
      
      rows.push(row)
    })
    
    // Total Outflows row
    const totalOutflowsRow = {
      id: 'total_outflows',
      display_name: 'Total Outflows',
      is_total: true,
      is_inflow: false
    }
    
    periods.forEach((period) => {
      let total = 0
      operatingGroups.forEach(vg => {
        const data = dashboardData.forecast_data[period.start_date]?.[vg.category]?.[vg.subcategory]
        total += data?.is_actual ? data.actual : data?.forecasted || 0
      })
      totalOutflowsRow[period.start_date] = total
    })
    rows.push(totalOutflowsRow)
    
    // Net Operating CF
    const netOperatingRow = {
      id: 'net_operating_cf',
      display_name: 'Net Operating CF',
      is_total: true,
      is_inflow: true
    }
    
    periods.forEach((period) => {
      const revenue = totalRevenueRow[period.start_date] || 0
      const outflows = totalOutflowsRow[period.start_date] || 0
      netOperatingRow[period.start_date] = revenue + outflows // outflows are negative
    })
    rows.push(netOperatingRow)
    
    // Add empty row
    rows.push({
      id: 'spacer_3',
      display_name: '',
      is_spacer: true
    })
    
    // Financing Activities
    rows.push({
      id: 'financing_header',
      display_name: 'FINANCING ACTIVITIES',
      is_section_header: true
    })
    
    const financingGroups = vendorGroups.filter(vg => vg.category === 'financing')
    financingGroups.forEach(vg => {
      const row = {
        id: `vendor_group_${vg.id}`,
        vendor_group_id: vg.id,
        category: vg.category,
        subcategory: vg.subcategory,
        display_name: `  ${vg.display_name}`,
        is_inflow: vg.is_inflow
      }
      
      periods.forEach((period) => {
        const data = dashboardData.forecast_data[period.start_date]?.[vg.category]?.[vg.subcategory]
        row[period.start_date] = data?.is_actual ? data.actual : data?.forecasted || 0
        row[`${period.start_date}_is_actual`] = data?.is_actual || false
      })
      
      rows.push(row)
    })
    
    // Net Financing CF
    const netFinancingRow = {
      id: 'net_financing_cf',
      display_name: 'Net Financing CF',
      is_total: true
    }
    
    periods.forEach((period) => {
      let total = 0
      financingGroups.forEach(vg => {
        const data = dashboardData.forecast_data[period.start_date]?.[vg.category]?.[vg.subcategory]
        total += data?.is_actual ? data.actual : data?.forecasted || 0
      })
      netFinancingRow[period.start_date] = total
    })
    rows.push(netFinancingRow)
    
    // Add empty row
    rows.push({
      id: 'spacer_4',
      display_name: '',
      is_spacer: true
    })
    
    // Ending Cash
    const endingCashRow = {
      id: 'ending_cash',
      display_name: 'Ending Cash',
      is_total: true,
      is_inflow: true
    }
    
    periods.forEach((period, index) => {
      const beginningCash = index === 0 ? 
        cashBalanceRow[period.start_date] : 
        endingCashRow[periods[index - 1].start_date] || 0
      const netOperating = netOperatingRow[period.start_date] || 0
      const netFinancing = netFinancingRow[period.start_date] || 0
      
      endingCashRow[period.start_date] = beginningCash + netOperating + netFinancing
    })
    rows.push(endingCashRow)
    
    return rows
  }, [dashboardData, vendorGroups, periods])

  // Column definitions
  const columnDefs = useMemo((): ColDef[] => {
    const cols: ColDef[] = [
      {
        headerName: 'Week Starting:',
        field: 'display_name',
        pinned: 'left',
        width: 200,
        cellStyle: (params) => {
          if (params.data?.is_section_header) return { fontWeight: 'bold', fontSize: '14px' }
          if (params.data?.is_subsection_header) return { fontWeight: '600' }
          if (params.data?.is_total) return { fontWeight: 'bold', borderTop: '1px solid #ccc' }
          if (params.data?.is_spacer) return { borderTop: 'none', borderBottom: 'none' }
          return {}
        }
      }
    ]
    
    periods.forEach((period) => {
      cols.push({
        headerName: period.display_text,
        field: period.start_date,
        width: 120,
        type: 'numericColumn',
        cellRenderer: (params) => {
          if (params.data?.is_spacer || params.data?.is_section_header || params.data?.is_subsection_header) {
            return ''
          }
          
          if (params.data?.vendor_group_id) {
            // Editable forecast cells
            return React.createElement(EditableCurrencyCellRenderer, {
              ...params,
              setValue: (newValue: number) => {
                updateCellValue(period.start_date, params.data.vendor_group_id, newValue)
              }
            })
          }
          
          // Non-editable calculated cells
          return React.createElement(CurrencyCellRenderer, params)
        },
        cellStyle: (params) => {
          if (params.data?.is_total) return { fontWeight: 'bold', borderTop: '1px solid #ccc' }
          if (params.data?.is_header) return { fontWeight: 'bold', backgroundColor: '#f8f9fa' }
          return {}
        }
      })
    })
    
    return cols
  }, [periods, updateCellValue])

  const generateForecasts = async () => {
    try {
      setLoading(true)
      await axios.post(`${API_BASE}/api/forecast/generate/${clientId}?weeks=12`)
      await fetchData()
    } catch (err) {
      console.error('Error generating forecasts:', err)
      setError('Failed to generate forecasts')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <h3 className="text-red-800 font-medium">Error</h3>
        <p className="text-red-600 mt-1">{error}</p>
        <button 
          onClick={fetchData}
          className="mt-3 bg-red-100 hover:bg-red-200 text-red-800 px-4 py-2 rounded"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="w-full">
      <div className="mb-4 flex justify-between items-center">
        <h2 className="text-2xl font-bold">Cash Flow Forecast</h2>
        <div className="space-x-2">
          <button
            onClick={generateForecasts}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
          >
            Generate Forecasts
          </button>
          <button
            onClick={fetchData}
            className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded"
          >
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
      
      <div className="mt-4 text-sm text-gray-600">
        <p>• Light green cells show actual values (after reconciliation)</p>
        <p>• White cells show forecast values</p>
        <p>• Double-click any forecast cell to edit</p>
        <p>• Values in parentheses are negative (outflows)</p>
      </div>
    </div>
  )
}

export default ForecastSpreadsheet