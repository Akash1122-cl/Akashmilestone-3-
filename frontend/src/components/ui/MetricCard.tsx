import React from 'react'

interface MetricCardProps {
  title: string
  value: string
  change: string
  changeType: 'positive' | 'negative' | 'neutral'
  icon: string
  description?: string
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  change,
  changeType,
  icon,
  description
}) => {
  const changeColors = {
    positive: { color: '#166534', backgroundColor: '#dcfce7' },
    negative: { color: '#991b1b', backgroundColor: '#fee2e2' },
    neutral: { color: '#475569', backgroundColor: '#e2e8f0' }
  }

  return (
    <div
      style={{
        background: 'linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)',
        border: '1px solid #e2e8f0',
        borderRadius: 16,
        boxShadow: '0 12px 30px rgba(15, 23, 42, 0.08)',
        padding: 20
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16 }}>
        <div>
          <p style={{ fontSize: 14, fontWeight: 600, color: '#475569', margin: 0 }}>{title}</p>
          <p style={{ fontSize: 30, fontWeight: 700, color: '#0f172a', margin: '8px 0 0 0' }}>{value}</p>
          {description && <p style={{ fontSize: 13, color: '#64748b', margin: '8px 0 0 0' }}>{description}</p>}
        </div>
        <div style={{ fontSize: 26, lineHeight: 1 }}>
          <span role="img" aria-label={title}>
            {icon}
          </span>
        </div>
      </div>

      <div style={{ marginTop: 14 }}>
        <span
          style={{
            ...changeColors[changeType],
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            fontSize: 12,
            fontWeight: 700,
            borderRadius: 9999,
            padding: '4px 10px'
          }}
        >
          <span>{changeType === 'positive' ? '↑' : changeType === 'negative' ? '↓' : '→'}</span>
          {change}
        </span>
      </div>
    </div>
  )
}
