'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Shield, AlertTriangle, TrendingUp, Users, Building2, FileText, Activity, ChevronRight, ArrowUpRight } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || '/api').replace(/\/$/, '')

// ── Types ──────────────────────────────────────────────────────────────────────

interface OverviewStats {
  total_awards: number
  total_value: number
  total_suppliers: number
  total_authorities: number
  avg_bids_per_award: number
  low_competition_rate: number
}

interface ProcedureType {
  type: string
  count: number
  total_value: number
  risk_level: 'high' | 'medium' | 'low'
}

interface CompetitionBucket {
  bids: number
  count: number
  total_value: number
  risk_level: 'high' | 'medium' | 'low'
}

interface TopAuthority {
  id: number
  name: string
  city: string
  contract_count: number
  total_value: number
}

// ── Helpers ────────────────────────────────────────────────────────────────────

function fmt(n: number | null | undefined): string {
  if (n == null || isNaN(n)) return '—'
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)}B`
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return n.toLocaleString()
}

function fmtBAM(n: number | null | undefined): string {
  if (n == null || isNaN(n)) return '—'
  return `BAM ${fmt(n)}`
}

const RISK_COLORS: Record<string, string> = {
  high: '#ef4444',
  medium: '#f59e0b',
  low: '#22c55e',
}

const CHART_COLORS = ['#6468f0', '#818cf8', '#a5b4fc', '#c7d2fe', '#e0e7ff']

// ── Sub-components ─────────────────────────────────────────────────────────────

function StatCard({
                    icon: Icon,
                    label,
                    value,
                    sub,
                    accent,
                  }: {
  icon: React.ElementType
  label: string
  value: string
  sub?: string
  accent?: string
}) {
  return (
      <div className="bg-white border border-slate-200 rounded-2xl p-6 flex flex-col gap-3 hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-widest text-slate-400">{label}</span>
          <div className="w-8 h-8 rounded-xl bg-indigo-50 flex items-center justify-center">
            <Icon className="w-4 h-4 text-indigo-500" />
          </div>
        </div>
        <div className="text-3xl font-bold text-slate-900 tracking-tight">{value}</div>
        {sub && (
            <div className={`text-xs font-medium ${accent ?? 'text-slate-400'}`}>{sub}</div>
        )}
      </div>
  )
}

function RiskBadge({ level }: { level: string }) {
  const map: Record<string, string> = {
    high: 'bg-red-50 text-red-600 border border-red-200',
    medium: 'bg-amber-50 text-amber-600 border border-amber-200',
    low: 'bg-emerald-50 text-emerald-600 border border-emerald-200',
  }
  return (
      <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${map[level] ?? map.medium}`}>
      {level}
    </span>
  )
}

function SectionHeader({ title, sub }: { title: string; sub?: string }) {
  return (
      <div className="mb-6">
        <h2 className="text-lg font-bold text-slate-900">{title}</h2>
        {sub && <p className="text-sm text-slate-400 mt-0.5">{sub}</p>}
      </div>
  )
}

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse bg-slate-100 rounded-xl ${className}`} />
}

// ── Main Dashboard ─────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const [overview, setOverview] = useState<OverviewStats | null>(null)
  const [procedures, setProcedures] = useState<ProcedureType[]>([])
  const [competition, setCompetition] = useState<CompetitionBucket[]>([])
  const [authorities, setAuthorities] = useState<TopAuthority[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const [ov, pr, co, au] = await Promise.all([
          fetch(`${API_BASE}/v1/dashboard/stats/overview`).then(r => r.json()),
          fetch(`${API_BASE}/v1/dashboard/stats/procedure-types`).then(r => r.json()),
          fetch(`${API_BASE}/v1/dashboard/stats/competition-analysis`).then(r => r.json()),
          fetch(`${API_BASE}/v1/dashboard/stats/top-authorities`).then(r => r.json()),
        ])
        setOverview(ov)
        setProcedures(pr)
        // Collapse competition buckets: group bids >= 10 together
        const bucketed: CompetitionBucket[] = []
        const overflow = { bids: 10, count: 0, total_value: 0, risk_level: 'low' as const }
        for (const b of co as CompetitionBucket[]) {
          if (b.bids >= 10) {
            overflow.count += b.count
            overflow.total_value += b.total_value
          } else {
            bucketed.push(b)
          }
        }
        if (overflow.count > 0) bucketed.push(overflow)
        setCompetition(bucketed)
        setAuthorities(au)
      } catch (e) {
        setError('Failed to load dashboard data. Make sure the API is reachable.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  // Prepare pie data for procedure types (top 5 + Other)
  const pieData = (() => {
    if (!procedures.length) return []
    const sorted = [...procedures].sort((a, b) => b.count - a.count)
    const top = sorted.slice(0, 5)
    const other = sorted.slice(5).reduce((acc, p) => acc + p.count, 0)
    const result = top.map(p => ({ name: p.type, value: p.count, risk_level: p.risk_level }))
    if (other > 0) result.push({ name: 'Other', value: other, risk_level: 'low' })
    return result
  })()

  // Competition chart — only show bids 1..10+
  const compChartData = competition.map(b => ({
    name: b.bids >= 10 ? '10+' : String(b.bids),
    count: b.count,
    risk: b.risk_level,
  }))

  return (
      <div className="min-h-screen bg-slate-50">
        {/* Nav */}
        <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
          <div className="container mx-auto px-6 py-4 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-indigo-500" />
              <span className="font-bold text-slate-900">Balkan Corruption Insider</span>
            </Link>
            <div className="flex items-center gap-1 text-sm text-slate-400">
              <Link href="/" className="hover:text-slate-700 px-3 py-1.5 rounded-lg hover:bg-slate-50 transition-colors">Home</Link>
              <span className="px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-600 font-semibold">Dashboard</span>
              <Link href="/about" className="hover:text-slate-700 px-3 py-1.5 rounded-lg hover:bg-slate-50 transition-colors">About</Link>
            </div>
          </div>
        </nav>

        <div className="container mx-auto px-6 py-10 max-w-7xl">

          {/* Header */}
          <div className="mb-10">
            <div className="flex items-center gap-2 text-xs font-semibold text-indigo-500 uppercase tracking-widest mb-3">
              <Activity className="w-3.5 h-3.5" />
              Live Data — Bosnia and Herzegovina
            </div>
            <h1 className="text-4xl font-bold text-slate-900 tracking-tight">Procurement Dashboard</h1>
            <p className="text-slate-400 mt-2 max-w-2xl">
              Real-time analysis of public procurement data to surface corruption risk patterns across contracting authorities, suppliers, and procedure types.
            </p>
          </div>

          {/* Error */}
          {error && (
              <div className="mb-8 flex items-center gap-3 bg-red-50 border border-red-200 text-red-700 px-5 py-4 rounded-2xl text-sm">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                {error}
              </div>
          )}

          {/* Overview Stats */}
          <section className="mb-10">
            {loading ? (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                  {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-36" />)}
                </div>
            ) : overview ? (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                  <StatCard icon={FileText} label="Total Awards" value={fmt(overview.total_awards)} />
                  <StatCard icon={TrendingUp} label="Total Value" value={fmtBAM(overview.total_value)} />
                  <StatCard icon={Users} label="Suppliers" value={fmt(overview.total_suppliers)} />
                  <StatCard icon={Building2} label="Authorities" value={fmt(overview.total_authorities)} />
                  <StatCard
                      icon={Activity}
                      label="Avg Bids"
                      value={overview.avg_bids_per_award.toFixed(1)}
                      sub="per award"
                  />
                  <StatCard
                      icon={AlertTriangle}
                      label="Low Competition"
                      value={`${overview.low_competition_rate.toFixed(1)}%`}
                      sub="≤1 bid received"
                      accent="text-red-500"
                  />
                </div>
            ) : null}
          </section>

          {/* Charts row */}
          <div className="grid lg:grid-cols-2 gap-6 mb-6">

            {/* Procedure Types Pie */}
            <div className="bg-white border border-slate-200 rounded-2xl p-6">
              <SectionHeader
                  title="Procedure Types"
                  sub="Distribution by procurement method — less transparent types carry higher risk"
              />
              {loading ? (
                  <Skeleton className="h-64" />
              ) : (
                  <>
                    <ResponsiveContainer width="100%" height={240}>
                      <PieChart>
                        <Pie
                            data={pieData}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={100}
                            paddingAngle={2}
                            dataKey="value"
                        >
                          {pieData.map((entry, i) => (
                              <Cell
                                  key={i}
                                  fill={RISK_COLORS[entry.risk_level] ?? CHART_COLORS[i % CHART_COLORS.length]}
                                  opacity={0.85}
                              />
                          ))}
                        </Pie>
                        <Tooltip
                            formatter={(value) => [Number(value).toLocaleString(), 'Awards']}
                            contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 12 }}
                        />
                        <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11 }} />
                      </PieChart>
                    </ResponsiveContainer>
                    {/* Risk breakdown table */}
                    <div className="mt-4 space-y-2">
                      {procedures.slice(0, 5).map((p, i) => (
                          <div key={i} className="flex items-center justify-between text-sm">
                            <div className="flex items-center gap-2 min-w-0">
                              <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: RISK_COLORS[p.risk_level] }} />
                              <span className="text-slate-600 truncate">{p.type}</span>
                            </div>
                            <div className="flex items-center gap-3 flex-shrink-0 ml-2">
                              <span className="text-slate-400 text-xs">{p.count.toLocaleString()}</span>
                              <RiskBadge level={p.risk_level} />
                            </div>
                          </div>
                      ))}
                    </div>
                  </>
              )}
            </div>

            {/* Competition Analysis Bar */}
            <div className="bg-white border border-slate-200 rounded-2xl p-6">
              <SectionHeader
                  title="Competition Analysis"
                  sub="Number of bids received per award — single-bid awards are a high-risk flag"
              />
              {loading ? (
                  <Skeleton className="h-64" />
              ) : (
                  <>
                    <ResponsiveContainer width="100%" height={240}>
                      <BarChart data={compChartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                        <XAxis
                            dataKey="name"
                            tick={{ fontSize: 11, fill: '#94a3b8' }}
                            axisLine={false}
                            tickLine={false}
                            label={{ value: 'Number of bids', position: 'insideBottom', offset: -2, fontSize: 10, fill: '#cbd5e1' }}
                        />
                        <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} tickFormatter={v => fmt(v)} />
                        <Tooltip
                            formatter={(v) => [Number(v).toLocaleString(), 'Awards']}
                            contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 12 }}
                        />
                        <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                          {compChartData.map((entry, i) => (
                              <Cell
                                  key={i}
                                  fill={entry.risk === 'high' ? '#ef4444' : entry.risk === 'medium' ? '#f59e0b' : '#6468f0'}
                                  opacity={0.85}
                              />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                    <div className="mt-4 flex items-center gap-4 text-xs text-slate-400">
                      <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-red-400 inline-block" />High risk (≤1 bid)</span>
                      <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-amber-400 inline-block" />Medium (2–3 bids)</span>
                      <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-indigo-400 inline-block" />Low (4+ bids)</span>
                    </div>
                  </>
              )}
            </div>
          </div>

          {/* Top Contracting Authorities */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 mb-6">
            <SectionHeader
                title="Top Contracting Authorities by Spending"
                sub="Entities with the highest total procurement value"
            />
            {loading ? (
                <div className="space-y-3">
                  {Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-12" />)}
                </div>
            ) : authorities.length === 0 ? (
                <p className="text-slate-400 text-sm">No data available.</p>
            ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                    <tr className="text-xs uppercase tracking-widest text-slate-400 border-b border-slate-100">
                      <th className="text-left py-3 pr-4 font-semibold">#</th>
                      <th className="text-left py-3 pr-4 font-semibold">Authority</th>
                      <th className="text-left py-3 pr-4 font-semibold">City</th>
                      <th className="text-right py-3 pr-4 font-semibold">Contracts</th>
                      <th className="text-right py-3 font-semibold">Total Value</th>
                    </tr>
                    </thead>
                    <tbody>
                    {authorities.map((a, i) => (
                        <tr key={a.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                          <td className="py-3 pr-4 text-slate-300 font-mono text-xs">{String(i + 1).padStart(2, '0')}</td>
                          <td className="py-3 pr-4 font-medium text-slate-800 max-w-xs">
                            <span className="block truncate">{a.name}</span>
                          </td>
                          <td className="py-3 pr-4 text-slate-400">{a.city || '—'}</td>
                          <td className="py-3 pr-4 text-right text-slate-600 tabular-nums">{a.contract_count.toLocaleString()}</td>
                          <td className="py-3 text-right font-semibold text-indigo-600 tabular-nums">{fmtBAM(a.total_value)}</td>
                        </tr>
                    ))}
                    </tbody>
                  </table>
                </div>
            )}
          </div>

          {/* Risk Indicators Summary */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6">
            <SectionHeader
                title="Risk Indicator Summary"
                sub="Overview of the 5 corruption risk indicators tracked by this platform"
            />
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[
                {
                  code: 'RI-PROC-01',
                  title: 'Procedural Transparency',
                  desc: 'Direct negotiations and restricted tenders signal elevated corruption risk.',
                  stat: procedures.filter(p => p.risk_level === 'high').reduce((a, b) => a + b.count, 0),
                  statLabel: 'high-risk procedure awards',
                  color: 'red',
                },
                {
                  code: 'RI-COMP-01',
                  title: 'Competition Analysis',
                  desc: 'Awards with one or zero bids indicate possible rigged or pre-arranged contracts.',
                  stat: overview?.low_competition_rate ?? null,
                  statLabel: '% of awards with ≤1 bid',
                  color: 'amber',
                  isPercent: true,
                },
                {
                  code: 'RI-SANC-01',
                  title: 'Sanctioned Suppliers',
                  desc: 'Cross-reference of procurement winners against international sanctions lists.',
                  stat: null,
                  statLabel: 'Requires sanctions data load',
                  color: 'red',
                },
                {
                  code: 'RI-OWN-01',
                  title: 'Shared Ownership',
                  desc: 'Competing bidders sharing owners indicates collusion or bid rigging.',
                  stat: null,
                  statLabel: 'Requires company registry load',
                  color: 'amber',
                },
                {
                  code: 'RI-TIME-01',
                  title: 'Election Timing',
                  desc: 'Contracts signed in the 90-day window before elections are flagged for review.',
                  stat: null,
                  statLabel: 'Requires election calendar data',
                  color: 'indigo',
                },
              ].map((ind) => {
                const colorMap: Record<string, string> = {
                  red: 'border-red-100 bg-red-50/30',
                  amber: 'border-amber-100 bg-amber-50/30',
                  indigo: 'border-indigo-100 bg-indigo-50/30',
                }
                const statColorMap: Record<string, string> = {
                  red: 'text-red-600',
                  amber: 'text-amber-600',
                  indigo: 'text-indigo-600',
                }
                return (
                    <div key={ind.code} className={`rounded-xl border p-5 ${colorMap[ind.color]}`}>
                      <div className="text-[10px] font-mono font-bold text-slate-400 mb-1">{ind.code}</div>
                      <div className="font-bold text-slate-800 mb-1">{ind.title}</div>
                      <p className="text-xs text-slate-500 mb-3 leading-relaxed">{ind.desc}</p>
                      {ind.stat !== null ? (
                          <div className={`text-xl font-bold tabular-nums ${statColorMap[ind.color]}`}>
                            {ind.isPercent ? `${(ind.stat as number).toFixed(1)}%` : fmt(ind.stat as number)}
                            <span className="text-xs font-normal text-slate-400 ml-1">{ind.statLabel}</span>
                          </div>
                      ) : (
                          <div className="text-xs text-slate-400 italic">{ind.statLabel}</div>
                      )}
                    </div>
                )
              })}
            </div>
          </div>

        </div>
      </div>
  )
}