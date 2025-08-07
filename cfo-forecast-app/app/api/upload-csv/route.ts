import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export async function POST(request: NextRequest) {
  try {
    // Check environment variables
    if (!process.env.NEXT_PUBLIC_SUPABASE_URL || !process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) {
      return NextResponse.json({ 
        error: 'Server configuration error. Please contact support.' 
      }, { status: 500 })
    }

    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
    )
    const formData = await request.formData()
    const clientName = formData.get('clientName') as string
    const startingBalance = formData.get('startingBalance') as string
    const csvFile = formData.get('csvFile') as File

    if (!clientName || !startingBalance || !csvFile) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 })
    }

    // Read CSV file
    const csvText = await csvFile.text()
    const lines = csvText.split('\\n')
    const headers = lines[0].split(',')
    
    // Basic CSV validation
    if (lines.length < 2) {
      return NextResponse.json({ error: 'CSV file appears to be empty' }, { status: 400 })
    }

    // Parse transactions
    const transactions = []
    let imported = 0
    let skipped = 0

    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim()
      if (!line) continue

      const values = line.split(',')
      if (values.length < 3) {
        skipped++
        continue
      }

      try {
        // Basic parsing - adjust based on your CSV format
        const date = values[0]?.replace(/"/g, '')
        const description = values[1]?.replace(/"/g, '')
        const amount = parseFloat(values[2]?.replace(/[",]/g, '') || '0')

        if (!date || !description || isNaN(amount)) {
          skipped++
          continue
        }

        // Format date
        let transactionDate
        try {
          const dateParts = date.split(/[-\/]/)
          if (dateParts.length === 3) {
            // Assume MM-DD-YYYY or MM/DD/YYYY
            const [month, day, year] = dateParts
            transactionDate = new Date(parseInt(year), parseInt(month) - 1, parseInt(day))
              .toISOString().split('T')[0]
          } else {
            throw new Error('Invalid date format')
          }
        } catch {
          skipped++
          continue
        }

        const transaction = {
          transaction_id: `${clientName}_${transactionDate}_${i}`,
          client_id: clientName,
          transaction_date: transactionDate,
          vendor_name: description.trim(),
          amount: amount,
          created_at: new Date().toISOString()
        }

        transactions.push(transaction)
        imported++

      } catch (error) {
        skipped++
        continue
      }
    }

    // Insert transactions into database
    if (transactions.length > 0) {
      const batchSize = 100
      for (let i = 0; i < transactions.length; i += batchSize) {
        const batch = transactions.slice(i, i + batchSize)
        const { error } = await supabase.from('transactions').insert(batch)
        if (error) {
          console.error('Database insert error:', error)
          return NextResponse.json({ 
            error: 'Failed to save transactions to database' 
          }, { status: 500 })
        }
      }
    }

    return NextResponse.json({
      success: true,
      clientName,
      imported,
      skipped,
      message: `Successfully imported ${imported} transactions for ${clientName}`
    })

  } catch (error) {
    console.error('Upload error:', error)
    return NextResponse.json({ 
      error: 'Failed to process CSV file' 
    }, { status: 500 })
  }
}