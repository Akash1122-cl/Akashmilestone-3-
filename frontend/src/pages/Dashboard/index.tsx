import React from 'react'
import { MetricCard } from '@/components/ui/MetricCard'
import { RecentReviews } from '@/components/dashboard/RecentReviews'
import { SentimentChart } from '@/components/charts/SentimentChart'
import { ThemeDistribution } from '@/components/charts/ThemeDistribution'
import { SystemHealth } from '@/components/dashboard/SystemHealth'

export const Dashboard: React.FC = () => {
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
            Dashboard
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Overview of your review analytics and system status
          </p>
        </div>
        <div className="flex space-x-3">
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            Generate Report
          </button>
          <button className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-800 transition-colors">
            Export Data
          </button>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Reviews"
          value="12,543"
          change="+12%"
          changeType="positive"
          icon="📊"
        />
        <MetricCard
          title="Active Products"
          value="8"
          change="+2"
          changeType="positive"
          icon="📱"
        />
        <MetricCard
          title="Avg. Sentiment"
          value="4.2"
          change="+0.3"
          changeType="positive"
          icon="😊"
        />
        <MetricCard
          title="Reports Generated"
          value="47"
          change="+8"
          changeType="positive"
          icon="📄"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SentimentChart />
        <ThemeDistribution />
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <RecentReviews />
        </div>
        <div>
          <SystemHealth />
        </div>
      </div>
    </div>
  )
}
