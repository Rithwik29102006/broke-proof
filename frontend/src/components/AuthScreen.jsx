import React, { useMemo, useState } from 'react'
import { api, saveTokens } from '../lib/api'

function iso(date) { return date.toISOString().slice(0, 10) }

export default function AuthScreen({ onDone }) {
  const [mode, setMode] = useState('register')
  const today = useMemo(() => new Date(), [])
  const end = useMemo(() => { const d = new Date(); d.setDate(d.getDate() + 30); return d }, [])
  const [form, setForm] = useState({
    name: '', email: '', password: '', starting_balance: '10000',
    cycle_start: iso(today), cycle_end: iso(end),
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const change = (e) => setForm(v => ({ ...v, [e.target.name]: e.target.value }))

  async function submit(e) {
    e.preventDefault(); setError(''); setLoading(true)
    try {
      const payload = mode === 'login'
        ? { email: form.email, password: form.password }
        : { ...form, starting_balance: Number(form.starting_balance) }
      const tokens = await api(`/auth/${mode}`, { method: 'POST', body: JSON.stringify(payload) })
      saveTokens(tokens); onDone()
    } catch (err) { setError(err.message) } finally { setLoading(false) }
  }

  return <div className="min-h-screen px-5 py-10 lg:grid lg:grid-cols-2 lg:items-center lg:gap-16 lg:px-20">
    <section className="mx-auto max-w-xl lg:mx-0">
      <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-lime-200 bg-lime-50 px-3 py-1 text-sm font-semibold text-lime-800">● AI Spending Controller</div>
      <h1 className="text-5xl font-black tracking-tight text-slate-950 sm:text-6xl">Know your <span className="text-lime-600">Broke Date</span> before it happens.</h1>
      <p className="mt-6 text-lg leading-8 text-slate-600">Broke-Proof predicts when your money runs out, recalculates a safe daily limit, saves spare change into a protected jar, and nudges you before an overspend hurts the rest of your month.</p>
      <div className="mt-8 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
        {['Broke Date','Safe/day','Round-up Jar','No bank link'].map(x => <div key={x} className="rounded-2xl border border-slate-200 bg-white p-4 font-semibold shadow-sm">{x}</div>)}
      </div>
    </section>

    <section className="card mx-auto mt-10 w-full max-w-lg p-6 sm:p-8 lg:mt-0">
      <div className="mb-7 flex rounded-2xl bg-slate-100 p-1">
        {['register','login'].map(x => <button key={x} onClick={() => setMode(x)} className={`flex-1 rounded-xl px-3 py-2 text-sm font-bold capitalize ${mode===x ? 'bg-white shadow-sm':'text-slate-500'}`}>{x}</button>)}
      </div>
      <form onSubmit={submit} className="space-y-4">
        {mode === 'register' && <div><label className="label">Your name</label><input className="input" name="name" value={form.name} onChange={change} placeholder="Aarav" required /></div>}
        <div><label className="label">Email</label><input className="input" type="email" name="email" value={form.email} onChange={change} placeholder="you@college.edu" required /></div>
        <div><label className="label">Password</label><input className="input" type="password" name="password" value={form.password} onChange={change} minLength={8} required /></div>
        {mode === 'register' && <>
          <div><label className="label">Money available this cycle (₹)</label><input className="input" type="number" min="1" step="0.01" name="starting_balance" value={form.starting_balance} onChange={change} required /></div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Cycle starts</label><input className="input" type="date" name="cycle_start" value={form.cycle_start} onChange={change} required /></div>
            <div><label className="label">Next income / cycle ends</label><input className="input" type="date" name="cycle_end" value={form.cycle_end} onChange={change} required /></div>
          </div>
        </>}
        {error && <div className="rounded-2xl bg-rose-50 p-3 text-sm font-medium text-rose-700">{error}</div>}
        <button className="btn-primary w-full" disabled={loading}>{loading ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create my controller'}</button>
      </form>
      <p className="mt-5 text-center text-xs leading-5 text-slate-500">No bank linking required. Add spending manually, paste payment SMS, or upload a payment screenshot.</p>
    </section>
  </div>
}
