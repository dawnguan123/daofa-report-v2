import '@/styles/globals.css'
import Link from 'next/link'

export const metadata = {
  title: '道法时事报告',
  description: '每日道法课程时事报告',
}

export default function RootLayout({ children }) {
  return (
    <html lang="zh-CN">
      <body className="bg-gray-50 min-h-screen">
        <header className="bg-white shadow-sm sticky top-0 z-10">
          <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
            <Link href="/" className="text-xl font-bold text-gray-800">
              📰 道法时事报告
            </Link>
            <Link href="/report" className="text-blue-500 hover:underline">
              查看最新 →
            </Link>
          </div>
        </header>
        <main className="max-w-6xl mx-auto px-4 py-8">
          {children}
        </main>
        <footer className="text-center text-gray-400 py-8">
          <p>© 2026 道法时事报告</p>
        </footer>
      </body>
    </html>
  )
}
