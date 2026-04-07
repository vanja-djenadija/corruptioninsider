import Link from 'next/link'
import { Shield, Github, ExternalLink, Database, BarChart3, FileSearch } from 'lucide-react'

export default function AboutPage() {
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
                        <Link href="/dashboard" className="hover:text-slate-700 px-3 py-1.5 rounded-lg hover:bg-slate-50 transition-colors">Dashboard</Link>
                        <span className="px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-600 font-semibold">About</span>
                    </div>
                </div>
            </nav>

            <div className="container mx-auto px-6 py-16 max-w-4xl">

                <div className="mb-12">
                    <h1 className="text-4xl font-bold text-slate-900 tracking-tight mb-4">About the Project</h1>
                    <p className="text-lg text-slate-500 leading-relaxed">
                        Balkan Corruption Insider is an open-source platform that won the{' '}
                        <a href="https://hackcorruption.org/" target="_blank" className="text-indigo-600 hover:underline">
                            #HackCorruption Balkans 2024
                        </a>{' '}
                        hackathon, supported by AccountabilityLab and Development Gateway. It analyzes public
                        procurement data across Bosnia and Herzegovina, Albania, and North Macedonia to detect
                        corruption patterns and enhance transparency.
                    </p>
                </div>

                {/* Data Sources */}
                <section className="mb-12">
                    <h2 className="text-2xl font-bold text-slate-900 mb-6">Data Sources</h2>
                    <div className="grid md:grid-cols-3 gap-4">
                        {[
                            {
                                country: 'Bosnia and Herzegovina',
                                sources: [
                                    { label: 'Public Procurement Portal', url: 'https://open.ejn.gov.ba/docs/index.html' },
                                    { label: 'FIA Company Registry', url: 'https://fia.ba/bs/profil-pravnih-lica@' },
                                    { label: 'Republika Srpska Registry', url: 'http://bizreg.esrpska.com' },
                                ],
                            },
                            {
                                country: 'Albania',
                                sources: [
                                    { label: 'Open Procurement Albania', url: 'https://openprocurement.al/en' },
                                    { label: 'QKB Company Registry', url: 'https://qkb.gov.al/' },
                                ],
                            },
                            {
                                country: 'North Macedonia',
                                sources: [
                                    { label: 'e-Nabavki Portal', url: 'https://e-nabavki.gov.mk' },
                                    { label: 'CRM Company Registry', url: 'https://crm.com.mk/' },
                                ],
                            },
                        ].map((item) => (
                            <div key={item.country} className="bg-white border border-slate-200 rounded-2xl p-6">
                                <h3 className="font-bold text-slate-800 mb-3">{item.country}</h3>
                                <ul className="space-y-2">
                                    {item.sources.map((s) => (
                                        <li key={s.url}>
                                            <a
                                                href={s.url}
                                                target="_blank"
                                                className="text-sm text-indigo-600 hover:underline flex items-center gap-1"
                                            >
                                                <ExternalLink className="w-3 h-3 flex-shrink-0" />
                                                {s.label}
                                            </a>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        ))}
                    </div>
                    <div className="mt-4 bg-white border border-slate-200 rounded-2xl p-6">
                        <h3 className="font-bold text-slate-800 mb-2">Sanctions Data</h3>
                        <a href="https://www.opensanctions.org/" target="_blank" className="text-sm text-indigo-600 hover:underline flex items-center gap-1">
                            <ExternalLink className="w-3 h-3" />
                            OpenSanctions — consolidated international sanctions lists
                        </a>
                    </div>
                </section>

                {/* Methodology */}
                <section className="mb-12">
                    <h2 className="text-2xl font-bold text-slate-900 mb-6">Risk Indicator Methodology</h2>
                    <div className="space-y-4">
                        {[
                            {
                                code: 'RI-PROC-01',
                                title: 'Procedural Transparency',
                                icon: FileSearch,
                                detail: 'Flags procurement procedures with lower transparency requirements — direct agreements and negotiated procedures. These procedure types bypass competitive bidding and are statistically associated with higher corruption risk.',
                            },
                            {
                                code: 'RI-COMP-01',
                                title: 'Competition Analysis',
                                icon: BarChart3,
                                detail: 'Identifies awards where only one or zero bids were received. Low competition may indicate pre-arranged contracts, restrictive technical specifications designed to favour a specific supplier, or market manipulation.',
                            },
                            {
                                code: 'RI-SANC-01',
                                title: 'Sanctioned Suppliers',
                                icon: Shield,
                                detail: 'Cross-references all awarded suppliers against the OpenSanctions database. Any match between a procurement winner and a sanctioned individual or entity is flagged as a high-priority risk alert.',
                            },
                            {
                                code: 'RI-OWN-01',
                                title: 'Shared Ownership',
                                icon: Database,
                                detail: 'Uses company registry data to identify cases where competing bidders in the same procedure share common owners or founders — a strong indicator of bid rigging or collusion.',
                            },
                            {
                                code: 'RI-TIME-01',
                                title: 'Election Timing',
                                icon: BarChart3,
                                detail: 'Flags contracts signed within 90 days before a national or local election. Procurement activity tends to spike before elections as a mechanism for distributing political patronage using public funds.',
                            },
                        ].map((ind) => (
                            <div key={ind.code} className="bg-white border border-slate-200 rounded-2xl p-6">
                                <div className="flex items-start gap-4">
                                    <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center flex-shrink-0 mt-0.5">
                                        <ind.icon className="w-5 h-5 text-indigo-500" />
                                    </div>
                                    <div>
                                        <div className="flex items-center gap-3 mb-1">
                                            <span className="font-bold text-slate-900">{ind.title}</span>
                                            <span className="text-[10px] font-mono font-bold text-slate-400 bg-slate-100 px-2 py-0.5 rounded">{ind.code}</span>
                                        </div>
                                        <p className="text-sm text-slate-500 leading-relaxed">{ind.detail}</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Open Source */}
                <section>
                    <div className="bg-indigo-50 border border-indigo-100 rounded-2xl p-8 text-center">
                        <h2 className="text-2xl font-bold text-slate-900 mb-3">Open Source</h2>
                        <p className="text-slate-500 mb-6 max-w-lg mx-auto">
                            This project is fully open-source. The methodology, data pipelines, and codebase are
                            available for review, contribution, and reuse by researchers, journalists, and civil society.
                        </p>
                        <a
                            href="https://github.com/yourusername/HackCorruption"
                            target="_blank"
                            className="inline-flex items-center gap-2 bg-slate-900 text-white px-6 py-3 rounded-xl font-semibold text-sm hover:bg-slate-700 transition-colors"
                        >
                            <Github className="w-4 h-4" />
                            View on GitHub
                        </a>
                    </div>
                </section>

            </div>
        </div>
    )
}