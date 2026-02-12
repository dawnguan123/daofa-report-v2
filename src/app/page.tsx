'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { format } from 'date-fns'
import { zhCN } from 'date-fns/locale'

interface DateCard {
  publish_date: string
  count: number
  updated: string
}

interface NewsItem {
  id: number
  title: string
  url: string
  source: string
  publish_date: string
  category: string
  summary: string
  key_points: string[]
  ai_summary: string
  content_preview: string
}

export default function Home() {
  const [dates, setDates] = useState<DateCard[]>([])
  const [selectedDate, setSelectedDate] = useState<string>('')
  const [news, setNews] = useState<NewsItem[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingNews, setLoadingNews] = useState(false)

  // 加载日期列表
  useEffect(() => {
    fetch('/api/dates')
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setDates(data.dates)
          if (data.dates.length > 0) {
            setSelectedDate(data.dates[0].publish_date)
          }
        }
      })
      .finally(() => setLoading(false))
  }, [])

  // 加载选中日期的新闻
  useEffect(() => {
    if (!selectedDate) return
    
    setLoadingNews(true)
    fetch(`/api/news?date=${selectedDate}`)
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setNews(data.news)
        }
      })
      .finally(() => setLoadingNews(false))
  }, [selectedDate])

  const stats = {
    total: dates.reduce((acc, d) => acc + d.count, 0),
    days: dates.length
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
    <div className="max-w-4xl mx-auto">
      {/* 头部 */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-800">📰 道法时事报告</h1>
        <p className="text-gray-500 mt-2">自动采集 · 智能匹配 · 每日更新</p>
        <div className="flex justify-center gap-6 mt-4 text-sm text-gray-600">
          <span className="bg-blue-50 px-3 py-1 rounded-full">📚 {stats.days} 天数据</span>
          <span className="bg-green-50 px-3 py-1 rounded-full">📰 {stats.total} 篇新闻</span>
        </div>
      </div>

      {/* 九宫格日期选择 */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-gray-700 mb-4">📅 选择日期</h2>
        <div className="grid grid-cols-3 gap-4">
          {dates.map((dateInfo) => (
            <button
              key={dateInfo.publish_date}
              onClick={() => setSelectedDate(dateInfo.publish_date)}
              className={`
                aspect-square flex flex-col items-center justify-center rounded-xl transition-all
                ${selectedDate === dateInfo.publish_date 
                  ? 'bg-blue-500 text-white shadow-lg transform scale-105' 
                  : 'bg-white hover:bg-blue-50 border border-gray-200 shadow-sm'
                }
              `}
            >
              <span className="text-3xl font-bold">
                {parseInt(dateInfo.publish_date.split('-')[2])}
              </span>
              <span className="text-xs mt-1 opacity-80">
                {dateInfo.publish_date.split('-')[1]}月
              </span>
              <span className="text-xs mt-2 bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full">
                {dateInfo.count}篇
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* 日期导航 */}
      <div className="flex justify-center gap-4 mb-8">
        <button
          onClick={() => {
            const idx = dates.findIndex(d => d.publish_date === selectedDate)
            if (idx < dates.length - 1) {
              setSelectedDate(dates[idx + 1].publish_date)
            }
          }}
          disabled={dates.findIndex(d => d.publish_date === selectedDate) >= dates.length - 1}
          className="px-4 py-2 bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-50"
        >
          ← 上一周
        </button>
        <button
          onClick={() => dates.length > 0 && setSelectedDate(dates[0].publish_date)}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          回到最新
        </button>
        <button
          onClick={() => {
            const idx = dates.findIndex(d => d.publish_date === selectedDate)
            if (idx > 0) {
              setSelectedDate(dates[idx - 1].publish_date)
            }
          }}
          disabled={dates.findIndex(d => d.publish_date === selectedDate) <= 0}
          className="px-4 py-2 bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-50"
        >
          下一周 →
        </button>
      </div>

      {/* 新闻列表 */}
      {loadingNews ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <div>
          <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <span>📰 {selectedDate} 时事报告</span>
            <span className="text-sm font-normal text-gray-500">({news.length}条)</span>
          </h2>
          
          {news.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
              该日期暂无新闻
            </div>
          ) : (
            news.map((item, index) => (
              <NewsCard key={item.id} item={item} index={index + 1} />
            ))
          )}
        </div>
      )}
    </div>
  )
}

// 新闻卡片组件
function NewsCard({ item, index }: { item: NewsItem; index: number }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="bg-white rounded-lg shadow mb-6 overflow-hidden">
      {/* 标题区域 - 始终显示 */}
      <div 
        className="p-6 cursor-pointer hover:bg-gray-50"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start gap-4">
          <span className="flex-shrink-0 w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold text-sm">
            {index}
          </span>
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-800 leading-relaxed">{item.title}</h3>
            <div className="flex items-center gap-3 mt-3">
              <span className="text-sm text-gray-500">{item.source}</span>
              <span className="text-sm text-gray-400">·</span>
              <span className="text-sm text-gray-500">{item.publish_date}</span>
              <span className="text-sm bg-blue-50 text-blue-600 px-2 py-0.5 rounded">{item.category}</span>
            </div>
          </div>
          <span className={`text-gray-400 transform transition-transform ${expanded ? 'rotate-180' : ''}`}>
            ▼
          </span>
        </div>
      </div>

      {/* 展开内容 */}
      {expanded && (
        <div className="border-t border-gray-100 p-6 bg-gray-50">
          {/* 内容摘要 */}
          <div className="mb-4">
            <h4 className="font-semibold text-gray-700 mb-2 flex items-center gap-2">
              <span className="text-lg">📝</span> 内容摘要
            </h4>
            <p className="text-gray-600 leading-relaxed">{item.content_preview}</p>
          </div>

          {/* 关键要点 */}
          {item.key_points && item.key_points.length > 0 && (
            <div className="mb-4">
              <h4 className="font-semibold text-gray-700 mb-2 flex items-center gap-2">
                <span className="text-lg">📌</span> 关键要点
              </h4>
              <div className="flex flex-wrap gap-2">
                {item.key_points.map((point, i) => (
                  <span key={i} className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-sm">
                    {point}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* AI分析 */}
          {item.ai_summary && (
            <div className="mb-4">
              <h4 className="font-semibold text-gray-700 mb-2 flex items-center gap-2">
                <span className="text-lg">🤖</span> AI分析
              </h4>
              <div className="bg-white rounded-lg p-4 text-sm text-gray-600 leading-relaxed">
                {item.ai_summary.split('\n').map((line, i) => {
                  if (line.includes('【')) {
                    return <p key={i} className="font-bold text-blue-600 mt-3 mb-1">{line}</p>
                  }
                  return <p key={i} className="mb-1">{line}</p>
                })}
              </div>
            </div>
          )}

          {/* 原文链接 */}
          {item.url && (
            <a 
              href={item.url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-blue-500 hover:underline text-sm"
            >
              阅读原文 →
            </a>
          )}
        </div>
      )}
    </div>
  )
}
