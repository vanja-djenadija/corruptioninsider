import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { ArrowRight, Shield, Database, BarChart3, Github, ExternalLink, AlertTriangle } from 'lucide-react'
import Image from 'next/image'

export default function Home() {
  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="border-b border-blue-200 bg-gradient-to-r from-white to-blue-500 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="w-6 h-6 text-primary" />
              <span className="font-bold text-xl">Balkan Corruption Insider</span>
            </div>
            <div className="flex items-center gap-4">
              <Link href="/about" className="text-sm font-medium hover:text-primary transition-colors">
                About
              </Link>
              <Link href="/dashboard">
                <Button variant="outline" size="sm">Dashboard</Button>
              </Link>
              <Link href="https://github.com/yourusername/HackCorruption" target="_blank">
                <Button variant="ghost" size="sm" className="gap-2">
                  <Github className="w-4 h-4" />
                  GitHub
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-accent/30 via-background to-background py-20 md:py-32">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            <div className="flex flex-wrap items-center justify-center gap-3 mb-8">
              <Badge variant="secondary" className="gap-1.5 py-1.5 px-3">
                <Shield className="w-3.5 h-3.5" />
                #HackCorruption Winner
              </Badge>
              <Badge variant="outline" className="py-1.5 px-3">
                Open Source
              </Badge>
            </div>

            <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-foreground mb-6">
              Exposing Corruption Through
              <span className="text-primary"> Data Analysis</span>
            </h1>

            <p className="text-xl text-muted-foreground mb-8 leading-relaxed max-w-3xl mx-auto">
              An open-source platform that analyzes public procurement data across Bosnia and Herzegovina,
              Albania, and North Macedonia to detect corruption patterns and enhance transparency.
            </p>

            <div className="flex flex-wrap gap-4 justify-center">
              <Link href="/dashboard">
                <Button size="lg" className="gap-2">
                  Explore Data
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>

              <Link href="https://github.com/yourusername/HackCorruption" target="_blank">
                <Button size="lg" variant="outline" className="gap-2">
                  <Github className="w-4 h-4" />
                  View on GitHub
                </Button>
              </Link>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-8 mt-16 max-w-2xl mx-auto">
              <div>
                <div className="text-3xl font-bold text-primary">287K+</div>
                <div className="text-sm text-muted-foreground mt-1">Awards Analyzed</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-primary">5</div>
                <div className="text-sm text-muted-foreground mt-1">Risk Indicators</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-primary">3</div>
                <div className="text-sm text-muted-foreground mt-1">Countries</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Partners Section */}
      <section className="py-20 bg-gradient-to-b from-white via-indigo-50/30 to-white">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 bg-indigo-100 text-indigo-700 px-4 py-2 rounded-full text-sm font-semibold mb-4">
              <Shield className="w-4 h-4" />
              Partnership Network
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-3">Supported By</h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Collaborating with leading organizations committed to transparency and accountability
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {/* HackCorruption */}
            <Link
              href="https://hackcorruption.org/"
              target="_blank"
              className="group relative bg-white rounded-2xl border border-slate-200 p-8 hover:border-indigo-300 hover:shadow-xl transition-all duration-300"
            >
              <div className="absolute -top-3 -right-3 bg-indigo-600 text-white text-xs font-bold px-3 py-1 rounded-full shadow-lg">
                Winner
              </div>

              <div className="flex flex-col items-center text-center space-y-4">
                {/* Logo */}
                <div className="w-full h-24 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl flex items-center justify-center group-hover:scale-105 transition-transform overflow-hidden p-4">
                  <Image
                    src="/images/partners/hc.png"
                    alt="HackCorruption"
                    width={180}
                    height={80}
                    className="object-contain w-full h-full"
                  />
                </div>

                <div>
                  <h3 className="text-lg font-bold text-gray-900 group-hover:text-indigo-600 transition-colors mb-1">
                    HackCorruption
                  </h3>
                  <p className="text-sm text-gray-500">Global Anti-Corruption Hackathon</p>
                </div>

                <div className="flex items-center gap-2 text-sm text-indigo-600 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                  Visit Website
                  <ArrowRight className="w-4 h-4" />
                </div>
              </div>
            </Link>

            {/* AccountabilityLab */}
            <Link
              href="https://accountabilitylab.org/"
              target="_blank"
              className="group relative bg-white rounded-2xl border border-slate-200 p-8 hover:border-indigo-300 hover:shadow-xl transition-all duration-300"
            >
              <div className="flex flex-col items-center text-center space-y-4">
                {/* Logo */}
                <div className="w-full h-24 bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl flex items-center justify-center group-hover:scale-105 transition-transform overflow-hidden p-4">
                  <Image
                    src="/images/partners/accountability-lab.png"
                    alt="AccountabilityLab"
                    width={180}
                    height={80}
                    className="object-contain w-full h-full"
                  />
                </div>

                <div>
                  <h3 className="text-lg font-bold text-gray-900 group-hover:text-indigo-600 transition-colors mb-1">
                    AccountabilityLab
                  </h3>
                  <p className="text-sm text-gray-500">Empowering Citizen Engagement</p>
                </div>

                <div className="flex items-center gap-2 text-sm text-indigo-600 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                  Visit Website
                  <ArrowRight className="w-4 h-4" />
                </div>
              </div>
            </Link>

            {/* Development Gateway */}
            <Link
              href="https://www.developmentgateway.org/"
              target="_blank"
              className="group relative bg-white rounded-2xl border border-slate-200 p-8 hover:border-indigo-300 hover:shadow-xl transition-all duration-300"
            >
              <div className="flex flex-col items-center text-center space-y-4">
                {/* Logo */}
                <div className="w-full h-24 bg-gradient-to-br from-emerald-50 to-teal-50 rounded-xl flex items-center justify-center group-hover:scale-105 transition-transform overflow-hidden p-4">
                  <Image
                    src="/images/partners/dg.png"
                    alt="Development Gateway"
                    width={180}
                    height={80}
                    className="object-contain w-full h-full"
                  />
                </div>

                <div>
                  <h3 className="text-lg font-bold text-gray-900 group-hover:text-indigo-600 transition-colors mb-1">
                    Development Gateway
                  </h3>
                  <p className="text-sm text-gray-500">Data-Driven Development</p>
                </div>

                <div className="flex items-center gap-2 text-sm text-indigo-600 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                  Visit Website
                  <ArrowRight className="w-4 h-4" />
                </div>
              </div>
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-background">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <Badge className="mb-4">How It Works</Badge>
            <h2 className="text-4xl font-bold mb-4">
              Data-Driven Corruption Detection
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto text-lg">
              We integrate multiple data sources and apply sophisticated algorithms
              to identify corruption risk indicators in public procurement
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            <Card className="border-2 hover:border-primary/50 transition-colors">
              <CardHeader>
                <Database className="w-12 h-12 text-primary mb-4" />
                <CardTitle className="text-xl">Data Integration</CardTitle>
                <CardDescription className="text-base">
                  Consolidating public procurement records, company registries,
                  and sanctions lists from official sources across the region
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-2 hover:border-primary/50 transition-colors">
              <CardHeader>
                <BarChart3 className="w-12 h-12 text-primary mb-4" />
                <CardTitle className="text-xl">Risk Analysis</CardTitle>
                <CardDescription className="text-base">
                  Automated detection of 5 key corruption risk indicators including
                  procedural transparency, competition levels, and timing anomalies
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-2 hover:border-primary/50 transition-colors">
              <CardHeader>
                <Shield className="w-12 h-12 text-primary mb-4" />
                <CardTitle className="text-xl">Open Methodology</CardTitle>
                <CardDescription className="text-base">
                  Transparent, open-source approach with comprehensive documentation
                  available for researchers and journalists
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* Risk Indicators Section */}
      <section className="py-20 bg-muted">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-12">
              <Badge className="mb-4" variant="secondary">
                <AlertTriangle className="w-3 h-3 mr-1" />
                Risk Indicators
              </Badge>
              <h2 className="text-3xl font-bold mb-4">
                5 Key Corruption Risk Indicators
              </h2>
            </div>

            <div className="space-y-4">
              {[
                {
                  num: 1,
                  title: "Procedural Transparency (RI-PROC-01)",
                  desc: "Identifies use of less transparent procurement procedures like direct negotiations"
                },
                {
                  num: 2,
                  title: "Competition Analysis (RI-COMP-01)",
                  desc: "Detects low number of bids indicating potential favoritism or rigged tenders"
                },
                {
                  num: 3,
                  title: "Sanctioned Suppliers (RI-SANC-01)",
                  desc: "Cross-references procurement winners with international sanctions lists"
                },
                {
                  num: 4,
                  title: "Shared Ownership (RI-OWN-01)",
                  desc: "Reveals hidden ownership structures and connections between competing bidders"
                },
                {
                  num: 5,
                  title: "Election Timing (RI-TIME-01)",
                  desc: "Flags contracts signed close to election periods, indicating potential misuse of public funds"
                }
              ].map((indicator) => (
                <Card key={indicator.num}>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <span className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary text-sm font-bold">
                        {indicator.num}
                      </span>
                      {indicator.title}
                    </CardTitle>
                    <CardDescription>{indicator.desc}</CardDescription>
                  </CardHeader>
                </Card>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Twitter Section */}
      <section className="py-20 bg-background">
        <div className="container mx-auto px-4">
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-12">
              <Badge className="mb-4">Recognition</Badge>
              <h2 className="text-3xl font-bold mb-4">
                #HackCorruption Winner
              </h2>
            </div>

            {/* Twitter Embed */}
            <div className="flex justify-center">
              <blockquote className="twitter-tweet">
                <p lang="en" dir="ltr">
                  How do you expose{' '}
                  <a href="https://twitter.com/hashtag/transnational?src=hash&amp;ref_src=twsrc%5Etfw">
                    #transnational
                  </a>{' '}
                  corruption networks? In many regions, tons of data is already available, primed for analysis &amp; aggregation.
                  One of our winning{' '}
                  <a href="https://twitter.com/hashtag/HackCorruption?src=hash&amp;ref_src=twsrc%5Etfw">
                    #HackCorruption
                  </a>{' '}
                  Balkans teams, Balkan Corruption Insider, is doing just that...
                  <a href="https://twitter.com/DGateway?ref_src=twsrc%5Etfw">@dgateway</a>{' '}
                  <a href="https://twitter.com/CIPEglobal?ref_src=twsrc%5Etfw">@CIPEglobal</a>{' '}
                  <a href="https://twitter.com/MSIWorldwide?ref_src=twsrc%5Etfw">@MSIWorldwide</a>{' '}
                  <a href="https://t.co/lGlGwuYq2O">pic.twitter.com/lGlGwuYq2O</a>
                </p>
                &mdash; #HackCorruption (@hackcorruption){' '}
                <a href="https://twitter.com/hackcorruption/status/1853717410420810133?ref_src=twsrc%5Etfw">
                  November 5, 2024
                </a>
              </blockquote>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-primary text-primary-foreground">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-4xl font-bold mb-4">
            Ready to Explore the Data?
          </h2>
          <p className="opacity-90 mb-8 max-w-2xl mx-auto text-lg">
            Access our interactive dashboard to analyze corruption risk patterns
            in real-time across the Balkans region
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/dashboard">
              <Button size="lg" variant="secondary" className="gap-2">
                Open Dashboard
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
            <Link href="https://github.com/yourusername/HackCorruption" target="_blank">
              <Button size="lg" variant="outline" className="gap-2 bg-transparent text-primary-foreground border-primary-foreground hover:bg-primary-foreground/10">
                <Github className="w-4 h-4" />
                Contribute
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-card border-t py-12">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Shield className="w-5 h-5 text-primary" />
                <span className="font-bold">Balkan Corruption Insider</span>
              </div>
              <p className="text-sm text-muted-foreground">
                Open-source platform for corruption detection through data analysis
              </p>
            </div>

            <div>
              <h4 className="font-semibold mb-3">Project</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link href="/about" className="hover:text-foreground transition-colors">About</Link></li>
                <li><Link href="/dashboard" className="hover:text-foreground transition-colors">Dashboard</Link></li>
                <li><Link href="https://github.com/yourusername/HackCorruption" className="hover:text-foreground transition-colors">Documentation</Link></li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold mb-3">Partners</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>
                  <a href="https://hackcorruption.org/" target="_blank" className="hover:text-foreground transition-colors">
                    #HackCorruption
                  </a>
                </li>
                <li>
                  <a href="https://accountabilitylab.org/" target="_blank" className="hover:text-foreground transition-colors">
                    AccountabilityLab
                  </a>
                </li>
                <li>
                  <a href="https://developmentgateway.org/" target="_blank" className="hover:text-foreground transition-colors">
                    Development Gateway
                  </a>
                </li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold mb-3">Connect</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>
                  <a href="https://github.com/yourusername/HackCorruption" target="_blank" className="hover:text-foreground transition-colors flex items-center gap-2">
                    <Github className="w-4 h-4" />
                    GitHub
                  </a>
                </li>
              </ul>
            </div>
          </div>

          <Separator className="my-8" />

          <div className="text-center text-sm text-muted-foreground">
            <p>© 2024 Balkan Corruption Insider. Open-source project licensed under MIT.</p>
            <p className="mt-2">Built with ❤️ at #HackCorruption Balkans 2024</p>
          </div>
        </div>
      </footer>
    </div>
  )
}