import type { RichAnalysis } from '../types'
import { TrendingUp } from 'lucide-react'

type Props = {
  data: RichAnalysis
}

export function RevenueChart({
  points,
}: {
  points: { label: string; value: number }[]
}) {
  const w = 800
  const h = 200
  const padY = 20
  const padBottom = 40
  const max = Math.max(...points.map((p) => p.value), 1)
  const min = 0
  const plotH = h - padY - padBottom

  const coords = points.map((p, i) => {
    const x = points.length === 1 ? w / 2 : (i / (points.length - 1)) * w
    const y = padY + plotH - ((p.value - min) / (max - min)) * plotH
    return { x, y, ...p }
  })

  const line = coords.map((c, i) => `${i === 0 ? 'M' : 'L'} ${c.x} ${c.y}`).join(' ')
  const area = `${line} L ${w} ${h} L 0 ${h} Z`

  return (
    <svg className="h-48 w-full" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id="chartGradient" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="#4aff94" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#4aff94" stopOpacity="0" />
        </linearGradient>
      </defs>
      {[40, 80, 120, 160].map((y) => (
        <line
          key={y}
          x1="0"
          x2={w}
          y1={y}
          y2={y}
          stroke="#e2dfe1"
          strokeDasharray="4"
          strokeWidth="1"
        />
      ))}
      <path d={area} fill="url(#chartGradient)" />
      <path d={line} fill="none" stroke="#4aff94" strokeLinecap="round" strokeWidth="3" />
      {coords.map((c, i) => (
        <circle
          key={c.label}
          cx={c.x}
          cy={c.y}
          r={i === coords.length - 1 ? 6 : 4}
          fill="#4aff94"
          stroke="#ffffff"
          strokeWidth="2"
        />
      ))}
      {coords.map((c) => (
        <text
          key={`t-${c.label}`}
          x={Math.min(c.x, w - 20)}
          y={190}
          textAnchor="middle"
          className="fill-outline text-data-tabular"
          style={{ fontSize: 14, fontWeight: 500 }}
        >
          {c.label}
        </text>
      ))}
    </svg>
  )
}

export function RichAnalysisBlock({ data }: Props) {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-4">
        <h2 className="text-headline-lg font-semibold text-on-surface">{data.title}</h2>
        <p className="max-w-[65ch] text-body-md text-on-surface-variant">{data.summary}</p>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        {data.metrics.map((m) => (
          <div
            key={m.label}
            className="flex flex-col gap-2 rounded-2xl border border-outline-variant/30 bg-surface-container-lowest p-6 shadow-sm"
          >
            <span className="text-label-sm font-semibold uppercase tracking-wider text-outline">
              {m.label}
            </span>
            <div className="flex flex-wrap items-baseline gap-2">
              <span className="text-display-lg font-bold tracking-tight text-on-surface max-md:text-[36px]">
                {m.value}
              </span>
              {m.trend && (
                <span className="inline-flex items-center gap-0.5 rounded-full bg-primary-container px-2 py-1 text-label-sm font-semibold text-[#006d38]">
                  <TrendingUp size={14} />
                  {m.trend}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="flex flex-col gap-6 rounded-3xl border border-outline-variant/30 bg-surface-container-lowest p-8 shadow-sm">
        <div className="flex items-center justify-between gap-4">
          <h3 className="text-headline-md font-semibold text-on-surface">{data.chart.title}</h3>
          <span className="text-label-sm font-semibold text-outline">{data.chart.unit}</span>
        </div>
        <RevenueChart points={data.chart.points} />
      </div>

      <div className="flex flex-col gap-4">
        <h3 className="text-headline-md font-semibold text-on-surface">Analysis</h3>
        <p className="max-w-[65ch] text-body-md text-on-surface-variant">{data.analysis}</p>
      </div>
    </div>
  )
}
