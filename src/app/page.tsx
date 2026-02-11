'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { format, subDays, addDays } from 'date-fns'
import { zhCN } from 'date-fns/locale'

export default function Home() {
  const [currentDate, setCurrentDate] = useState(new Date())
  const [calendarDays, setCalendarDays] = useState([])
  const [selectedDate, setSelectedDate] = useState(null)
  const [reportData, setReportData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // 生成日历数据（近9天）
  useEffect(() => {
    const days = []
    const today = new Date()
    
    for (let i = 8; i >= 0; i--) {
      const date = subDays(today, i)
      const dateStr = format(date, 'yyyy-MM-dd')
      
      // 检查是否有报告
      const hasReport = dateStr <= '2026-02-11' // 根据实际生成的数据
      
      days.push({
        date: date,
        dateStr: dateStr,
        day: format(date, 'd'),
        hasReport: hasReport,
        isToday: dateStr === format(today, 'yyyy-MM-dd')
      })
    }
    setCalendarDays(days)
    setLoading(false)
  }, [])

  // 加载选中日期的报告
  useEffect(() => {
    if (!selectedDate) return
    
    setLoading(true)
    const dateStr = format(selectedDate, 'yyyy-MM-dd')
    
    // 尝试加载报告
    fetch(`/data/reports/${dateStr}.json`)
      .then(res => {
        if (!res.ok) throw new Error('报告不存在')
        return res.json()
      })
      .then(data => {
        setReportData(data)
        setError(null)
      })
      .catch(err => {
        setReportData(null)
        setError(err.message)
      })
      .finally(() => {
        setLoading(false)
      })
  }, [selectedDate])

  const goToDate = (date) => {
    setCurrentDate(date)
    setSelectedDate(date)
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <p className="text-gray-400 mt-2">加载中...</p>
      </div>
    )
  }

  return (
    <div>
      {/* 日历头部 */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-800">📅 选择日期</h1>
        <p className="text-gray-500 mt-2">近9天时事报告</p>
      </div>

      {/* 九宫格日历 */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        {calendarDays.map((day) => {
          const isSelected = selectedDate && format(day.date, 'yyyy-MM-dd') === format(selectedDate, 'yyyy-MM-dd')
          
          return (
            <div
              key={day.dateStr}
              onClick={() => setSelectedDate(day.date)}
              className={`
                aspect-square flex flex-col items-center justify-center rounded-lg cursor-pointer transition-all
                ${day.hasReport 
                  ? 'bg-blue-50 hover:bg-blue-100 border border-blue-200' 
                  : 'bg-gray-50 text-gray-400'
                }
                ${isSelected ? 'ring-2 ring-blue-500' : ''}
                ${day.isToday ? 'ring-2 ring-green-500' : ''}
              `}
            >
              <span className="text-2xl font-bold">{day.day}</span>
              <span className="text-xs mt-1">
                {format(day.date, 'MM月dd日', { locale: zhCN })}
              </span>
              {day.hasReport && (
                <span className="text-xs text-blue-500 mt-1">📰</span>
              )}
            </div>
          )
        })}
      </div>

      {/* 日期导航 */}
      <div className="flex justify-center gap-4 mb-8">
        <button
          onClick={() => {
            const newDate = subDays(currentDate, 9)
            setCurrentDate(newDate)
            setSelectedDate(newDate)
          }}
          className="px-4 py-2 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
        >
          ← 上一周
        </button>
        <button
          onClick={() => {
            setCurrentDate(new Date())
            setSelectedDate(new Date())
          }}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          回到今天
        </button>
        <button
          onClick={() => {
            const newDate = addDays(currentDate, 9)
            setCurrentDate(newDate)
            setSelectedDate(newDate)
          }}
          className="px-4 py-2 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
        >
          下一周 →
        </button>
      </div>

      {/* 报告内容 */}
      {selectedDate && (
        <div className="text-center mb-4">
          <h2 className="text-xl font-bold">
            {format(selectedDate, 'yyyy年MM月dd日')} 时事报告
          </h2>
        </div>
      )}

      {error && (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <p className="text-gray-400 mb-4">{error}</p>
          <Link href="/report" className="text-blue-500 hover:underline">
            查看最新报告 →
          </Link>
        </div>
      )}

      {!error && reportData && (
        <div>
          {reportData.news?.map((item, index) => (
            <div key={index} className="bg-white rounded-lg shadow p-6 mb-6">
              <h2 className="text-xl font-bold text-blue-600 mb-2">
                {index + 1}. {item.title}
              </h2>
              <div className="text-sm text-gray-400 mb-2">
                {item.source} · {item.time}
              </div>
              <p className="text-gray-700">{item.summary}</p>
              
              {item.matchedChapters?.length > 0 && (
                <div className="bg-green-50 border-l-4 border-green-500 p-4 mt-4">
                  <h3 className="font-bold text-green-700 mb-2">📚 课本关联</h3>
                  {item.matchedChapters.map((ch, i) => (
                    <div key={i} className="mb-2">
                      <div className="flex items-center gap-2">
                        <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-sm">
                          {ch.title} (页码 {ch.page_range})
                        </span>
                      </div>
                      <p className="text-gray-600 text-sm mt-1">
                        {ch.content_summary?.slice(0, 100)}...
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
