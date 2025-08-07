export type Transaction = {
  transaction_id: string
  client_id: string
  transaction_date: string
  vendor_name: string
  amount: number
  created_at: string
}

export async function parseCSV(file: File, clientName: string): Promise<{
  transactions: Transaction[]
  skipped: number
}> {
  const text = await file.text()
  const lines = text.split('\n')
  
  if (lines.length < 2) {
    throw new Error('CSV file appears to be empty')
  }
  
  const transactions: Transaction[] = []
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
      // Parse values
      const date = values[0]?.replace(/"/g, '')
      const description = values[1]?.replace(/"/g, '')
      const amount = parseFloat(values[2]?.replace(/[",]/g, '') || '0')
      
      if (!date || !description || isNaN(amount)) {
        skipped++
        continue
      }
      
      // Format date
      let transactionDate: string
      const dateParts = date.split(/[-\/]/)
      
      if (dateParts.length === 3) {
        const [month, day, year] = dateParts
        const dateObj = new Date(parseInt(year), parseInt(month) - 1, parseInt(day))
        transactionDate = dateObj.toISOString().split('T')[0]
      } else {
        skipped++
        continue
      }
      
      transactions.push({
        transaction_id: `${clientName}_${transactionDate}_${i}`,
        client_id: clientName,
        transaction_date: transactionDate,
        vendor_name: description.trim(),
        amount: amount,
        created_at: new Date().toISOString()
      })
      
    } catch (error) {
      skipped++
      continue
    }
  }
  
  return { transactions, skipped }
}