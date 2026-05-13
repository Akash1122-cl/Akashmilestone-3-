import React from 'react'
import { MetricCard } from '@/components/ui/MetricCard'
import { toast } from 'react-hot-toast'

export const Dashboard: React.FC = () => {
  const quickInsights = [
    'Negative mentions around battery performance dropped by 18% this month after the latest patch release.',
    'Customers are asking for better onboarding tips; tutorial-focused content has a strong opportunity score.',
    'Most 5-star reviews mention speed and reliability, making those ideal hero benefits for marketing copy.'
  ]

  const topThemes = [
    { name: 'Performance', score: '91/100', sentiment: 'Very Positive' },
    { name: 'Battery Life', score: '82/100', sentiment: 'Improving' },
    { name: 'User Interface', score: '88/100', sentiment: 'Positive' },
    { name: 'Customer Support', score: '76/100', sentiment: 'Mixed' }
  ]

  const handleGenerateReport = () => {
    toast.success('Initiating Weekly Report Generation via MCP...', {
      icon: '🔄',
    });
  };

  const handleExportInsights = () => {
    toast.success('Insights exported successfully.', {
      icon: '📥',
    });
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        background:
          'radial-gradient(circle at 10% 20%, rgba(59,130,246,0.12), transparent 40%), radial-gradient(circle at 90% 0%, rgba(139,92,246,0.16), transparent 35%), #f8fafc',
        padding: '24px 28px 40px',
        color: '#0f172a',
        fontFamily: 'Inter, Segoe UI, Arial, sans-serif'
      }}
    >
      <div
        style={{
          background: 'linear-gradient(135deg, #1d4ed8 0%, #7c3aed 100%)',
          borderRadius: 22,
          padding: '30px 28px',
          color: 'white',
          boxShadow: '0 22px 40px rgba(37, 99, 235, 0.25)',
          marginBottom: 24
        }}
      >
        <p style={{ margin: 0, opacity: 0.85, fontWeight: 700, letterSpacing: 0.5 }}>REVIEW PULSE INTELLIGENCE</p>
        <h1 style={{ margin: '8px 0 10px 0', fontSize: 34, lineHeight: 1.2 }}>
          Turn customer feedback into product growth decisions
        </h1>
        <p style={{ margin: 0, maxWidth: 760, opacity: 0.92, lineHeight: 1.55 }}>
          Track customer sentiment, identify feature opportunities, and prioritize roadmap improvements with one live
          analytics workspace. Teams use this dashboard to understand what customers love, where friction is
          increasing, and how fast improvements are being adopted.
        </p>
        <div style={{ marginTop: 18, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <button
            onClick={handleGenerateReport}
            style={{
              border: 'none',
              borderRadius: 10,
              padding: '10px 16px',
              background: 'white',
              color: '#1e3a8a',
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            Generate Weekly Report
          </button>
          <button
            onClick={handleExportInsights}
            style={{
              border: '1px solid rgba(255,255,255,0.6)',
              borderRadius: 10,
              padding: '10px 16px',
              background: 'transparent',
              color: 'white',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Export Insights
          </button>
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: 16,
          marginBottom: 24
        }}
      >
        <MetricCard
          title="Total Reviews"
          value="12,543"
          change="+12%"
          changeType="positive"
          icon="📊"
          description="Across all tracked channels in the last 30 days"
        />
        <MetricCard
          title="Active Products"
          value="8"
          change="+2"
          changeType="positive"
          icon="📱"
          description="Products currently receiving sufficient review volume"
        />
        <MetricCard
          title="Average Sentiment"
          value="4.2 / 5"
          change="+0.3"
          changeType="positive"
          icon="😊"
          description="Weighted score derived from review polarity and confidence"
        />
        <MetricCard
          title="Reports Generated"
          value="47"
          change="+8"
          changeType="positive"
          icon="📄"
          description="Automated and manually created reports this quarter"
        />
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 16,
          marginBottom: 16
        }}
      >
        <div
          style={{
            background: '#ffffff',
            borderRadius: 16,
            border: '1px solid #e2e8f0',
            padding: 22,
            boxShadow: '0 8px 20px rgba(15, 23, 42, 0.06)'
          }}
        >
          <h2 style={{ margin: 0, fontSize: 20 }}>Executive Snapshot</h2>
          <p style={{ margin: '10px 0 16px 0', color: '#475569', lineHeight: 1.5 }}>
            Customer satisfaction is trending upward for the second consecutive sprint. Performance-focused updates
            are having measurable impact, while support-related friction still needs targeted action.
          </p>
          <ul style={{ margin: 0, paddingLeft: 20, color: '#1e293b', lineHeight: 1.7 }}>
            {quickInsights.map((insight) => (
              <li key={insight}>{insight}</li>
            ))}
          </ul>
        </div>
        <div
          style={{
            background: '#0f172a',
            color: '#e2e8f0',
            borderRadius: 16,
            padding: 22,
            boxShadow: '0 8px 20px rgba(2, 6, 23, 0.32)'
          }}
        >
          <h3 style={{ margin: 0 }}>Next Milestone</h3>
          <p style={{ margin: '10px 0 14px', opacity: 0.9, lineHeight: 1.5 }}>
            Launch proactive issue detection with alerting when negative sentiment spikes above baseline.
          </p>
          <p style={{ margin: 0, fontSize: 13, opacity: 0.8 }}>Target Date: May 15, 2026</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16 }}>
        <div
          style={{
            background: '#ffffff',
            borderRadius: 16,
            border: '1px solid #e2e8f0',
            padding: 22
          }}
        >
          <h3 style={{ margin: 0, fontSize: 18 }}>Top Discussion Themes</h3>
          <p style={{ margin: '8px 0 16px', fontSize: 14, color: '#64748b' }}>
            Prioritized by review frequency, trend acceleration, and business impact.
          </p>
          <div style={{ display: 'grid', gap: 10 }}>
            {topThemes.map((theme) => (
              <div
                key={theme.name}
                style={{
                  border: '1px solid #e2e8f0',
                  borderRadius: 12,
                  padding: '10px 12px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div>
                  <p style={{ margin: 0, fontWeight: 700 }}>{theme.name}</p>
                  <p style={{ margin: '4px 0 0', fontSize: 12, color: '#64748b' }}>{theme.sentiment}</p>
                </div>
                <span style={{ fontWeight: 700, color: '#2563eb' }}>{theme.score}</span>
              </div>
            ))}
          </div>
        </div>

        <div
          style={{
            background: '#ffffff',
            borderRadius: 16,
            border: '1px solid #e2e8f0',
            padding: 22
          }}
        >
          <h3 style={{ margin: 0, fontSize: 18 }}>Recent Customer Signals</h3>
          <p style={{ margin: '8px 0 16px', fontSize: 14, color: '#64748b' }}>
            Latest insights pulled from app store, support tickets, and social channels.
          </p>
          <div style={{ display: 'grid', gap: 10 }}>
            <div style={{ borderLeft: '4px solid #22c55e', background: '#f8fafc', borderRadius: 8, padding: '10px 12px' }}>
              "App feels much faster after the update. Great progress on loading times."
            </div>
            <div style={{ borderLeft: '4px solid #f59e0b', background: '#f8fafc', borderRadius: 8, padding: '10px 12px' }}>
              "Dark mode settings reset after restart. Please fix this in the next release."
            </div>
            <div style={{ borderLeft: '4px solid #3b82f6', background: '#f8fafc', borderRadius: 8, padding: '10px 12px' }}>
              "Onboarding is good, but a short interactive tutorial would make setup easier."
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
