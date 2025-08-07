import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const { transactions, clientName } = await request.json()
    
    if (!transactions || !Array.isArray(transactions) || !clientName) {
      return NextResponse.json({ error: 'Invalid data' }, { status: 400 })
    }

    // Import Supabase only when needed
    const { createClient } = await import('@supabase/supabase-js')
    
    const url = process.env.NEXT_PUBLIC_SUPABASE_URL
    const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
    
    if (!url || !key) {
      return NextResponse.json({ error: 'Server configuration error' }, { status: 500 })
    }
    
    const supabase = createClient(url, key)
    
    // Insert transactions in batches
    const batchSize = 100
    let totalInserted = 0
    
    for (let i = 0; i < transactions.length; i += batchSize) {
      const batch = transactions.slice(i, i + batchSize)
      const { error } = await supabase.from('transactions').insert(batch)
      
      if (error) {
        console.error('Database error:', error)
        return NextResponse.json({ 
          error: 'Failed to save transactions',
          details: error.message,
          inserted: totalInserted 
        }, { status: 500 })
      }
      
      totalInserted += batch.length
    }
    
    return NextResponse.json({
      success: true,
      inserted: totalInserted
    })
    
  } catch (error) {
    console.error('Server error:', error)
    return NextResponse.json({ 
      error: 'Server error',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}