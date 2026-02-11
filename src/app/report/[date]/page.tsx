'use client'

import { useParams } from 'next/navigation'
import Link from 'next/link'
import { useState, useEffect } from 'react'

export default function ReportPage() {
  const params = useParams()
  const date = params.date || new Date().toISOString().split('T')[0]
  const [reportData, setReportData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`/data/reports/${date}.json`)
      .then(res => res.json())
      .then(data => {
        setReportData(data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [date])

  if (loading) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-400">加载中...</p>
      </div>
    )
  }

  if (!reportData) {
    return (
      <div className="text-center py-12 bg-white rounded-lg shadow">
        <h1 className="text-2xl font-bold mb-4">{date}</h1>
        <p className="text-gray-400 mb-4">暂无报告</p>
        <Link href="/" className="text-blue-500 hover:underline">
          返回首页
        </Link>
      </div>
    )
  }

  return (
    <div>
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-800">📰 {date} 时事报告</h1>
        <Link href="/" className="text-blue-500 hover:underline mt-2 inline-block">
          ← 返回日历
        </Link>
      </div>

      {reportData.news?.map((item, index) => (
        <div key={index} className="news-card">
          <h2>{index + 1}. {item.title}</h2>
          <div className="text-sm text-gray-400 mb-2">
            {item.source} · {item.time}
          </div>
          <p className="text-gray-700">{item.summary}</p>
          
          {item.matchedChapters?.length > 0 && (
            <div className="chapter-ref">
              <h3 className="font-bold text-green-700 mb-2">📚 课本关联</h3>
              {item.matchedChapters.map((ch, i) => (
                <div key={i} className="mb-2">
                  <div className="flex items-center gap-2">
                    <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-sm">
                      {ch.title} (页码 {ch.page_range})
                    </span>
                    <a
                      href={`/pdf/道法课本.pdf#page=${ch.page_start}`}
                      target="_blank"
                      className="text-blue-500 hover:underline text-sm"
                    >
                      📖 查看课本 →
                    </a>
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

      {/* 课本索引 */}
      <div className="mt-12">
        <h3 className="text-lg font-semibold mb-4">📖 课本索引</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {reportData.chapters?.map((ch, i) => (
            <a
              key={i}
              href={`/pdf/道法课本.pdf#page=${ch.page_start}`}
              target="_blank"
              className="block p-4 bg-white border rounded hover:shadow"
            >
              <div className="font-medium">{ch.title}</div>
              <div className="text-sm text-gray-500">页码 {ch.page_range}</div>
            </a>
          ))}
        </div>
      </div>
    </div>
  )
}
