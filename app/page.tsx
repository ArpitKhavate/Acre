import { AnimationProvider } from '@/components/animation-provider'
import { Navbar } from '@/components/navbar'
import { Hero } from '@/components/hero'
import { Trust } from '@/components/trust'
import { Problem } from '@/components/problem'
import { HowItWorks } from '@/components/how-it-works'
import { Hardware } from '@/components/hardware'
import { Dashboard } from '@/components/dashboard'
import { Platform } from '@/components/platform'
import { Metrics } from '@/components/metrics'
import { CTA } from '@/components/cta'
import { Footer } from '@/components/footer'

export default function Page() {
  return (
    <AnimationProvider>
      <Navbar />
      <main>
        <Hero />
        <Trust />
        <Problem />
        <HowItWorks />
        <Hardware />
        <Dashboard />
        <Platform />
        <Metrics />
        <CTA />
      </main>
      <Footer />
    </AnimationProvider>
  )
}
