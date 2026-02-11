import { NextResponse } from 'next/server'

export async function GET(request) {
  const { searchParams } = new URL(request.url)
  const date = searchParams.get('date')
  
  if (!date) {
    return NextResponse.json({ error: '缺少日期参数' }, { status: 400 })
  }
  
  try {
    // 从文件读取报告数据
    const fs = require('fs')
    const path = require('path')
    
    const reportsDir = path.join(process.cwd(), 'public', 'data', 'reports')
    const reportPath = path.join(reportsDir, `${date}.json`)
    
    if (!fs.existsSync(reportPath)) {
      return NextResponse.json({ error: '报告不存在' }, { status: 404 })
    }
    
    const data = JSON.parse(fs.readFileSync(reportPath, 'utf-8'))
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}
