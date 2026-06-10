import Navbar from '@/components/Navbar';

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-[var(--bg)] text-[var(--fg)]">
      <Navbar />
      <section className="py-24 px-6 text-center">
        <h1 className="text-6xl font-extrabold mb-6 tracking-tight">Build Faster with AgentForge</h1>
        <p className="text-xl text-slate-600 mb-12 max-w-2xl mx-auto">The premium SaaS starter kit for modern developers. Scale your ideas with integrated Stripe payments and secure authentication.</p>
        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          <div className="p-8 rounded-2xl border border-slate-200 bg-white shadow-sm">
            <h3 className="text-2xl font-bold mb-4">Starter</h3>
            <p className="text-4xl font-bold mb-6">$0<span className="text-lg text-slate-500">/mo</span></p>
            <a href="/dashboard" className="block w-full py-3 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-all">Get Started</a>
          </div>
          <div className="p-8 rounded-2xl border-2 border-[var(--accent)] bg-blue-50 shadow-lg">
            <h3 className="text-2xl font-bold mb-4">Pro</h3>
            <p className="text-4xl font-bold mb-6">$29<span className="text-lg text-slate-500">/mo</span></p>
            <a href="/dashboard" className="block w-full py-3 bg-[var(--accent)] text-white rounded-lg hover:bg-blue-700 transition-all">Upgrade Now</a>
          </div>
        </div>
      </section>
    </main>
  );
}