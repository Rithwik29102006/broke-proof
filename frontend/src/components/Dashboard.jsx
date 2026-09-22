import React, { useEffect, useMemo, useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api, clearTokens } from '../lib/api'
import AddTransactionModal from './AddTransactionModal'
import NudgeModal from './NudgeModal'

const money = n => `₹${Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
const niceDate = v => v ? new Date(`${v}T00:00:00`).toLocaleDateString('en-IN', { day:'numeric', month:'short' }) : 'Beyond this cycle'

export default function Dashboard({ onLogout }) {
  const [data, setData] = useState(null)
  const [categories, setCategories] = useState([])
  const [addOpen, setAddOpen] = useState(false)
  const [nudge, setNudge] = useState(null)
  const [error, setError] = useState('')

  async function load() {
    try {
      const [d, c] = await Promise.all([api('/dashboard'), api('/categories')])
      setData(d); setCategories(c)
    } catch(e) { setError(e.message) }
  }
  useEffect(()=>{ load() }, [])

  async function toggleWeekend() {
    const enabled = !data.no_spend_weekend
    setData({...data, no_spend_weekend: enabled})
    try { await api('/controller/no-spend-weekend', {method:'POST', body:JSON.stringify({enabled})}); await load() }
    catch(e){ setError(e.message); await load() }
  }

  function saved(res) {
    setAddOpen(false); if (res.nudge) setNudge(res.nudge); load()
  }

  function logout(){ clearTokens(); onLogout() }

  if (!data) return <div className="grid min-h-screen place-items-center"><div className="text-center"><div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-slate-200 border-t-lime-500"/><p className="mt-4 text-sm text-slate-500">Starting your spending controller…</p>{error&&<p className="mt-2 text-rose-600">{error}</p>}</div></div>

  const riskDays = data.broke_date ? Math.ceil((new Date(data.broke_date)-new Date())/86400000) : null
  const progress = Math.max(0, Math.min(100, data.current_balance / data.cycle.starting_balance * 100))

  return <div className="min-h-screen">
    <header className="sticky top-0 z-30 border-b border-slate-200/70 bg-white/80 backdrop-blur-xl"><div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8"><div className="flex items-center gap-3"><div className="grid h-10 w-10 place-items-center rounded-2xl bg-slate-950 text-xl text-white">₹</div><div><div className="font-black tracking-tight">Broke-Proof</div><div className="text-xs text-slate-500">AI Spending Controller</div></div></div><div className="flex items-center gap-2"><button className="btn-primary hidden sm:block" onClick={()=>setAddOpen(true)}>+ Add spending</button><button className="rounded-xl px-3 py-2 text-sm font-semibold text-slate-500 hover:bg-slate-100" onClick={logout}>Log out</button></div></div></header>

    <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-sm font-semibold text-slate-500">Hi, {data.user.name} 👋</p><h1 className="mt-1 text-3xl font-black tracking-tight">Here’s how long your money lasts.</h1></div><button className="btn-primary sm:hidden" onClick={()=>setAddOpen(true)}>+ Add spending</button></div>

      {error && <div className="mb-5 rounded-2xl bg-rose-50 p-4 text-sm font-medium text-rose-700">{error}</div>}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metric title="Spendable balance" value={money(data.current_balance)} sub={`${progress.toFixed(0)}% of cycle money left`} accent="💳" />
        <Metric title="Safe to spend today" value={money(data.safe_to_spend_today)} sub={`${data.cycle.days_remaining} days until next cycle`} accent="🛡️" />
        <div className={`card p-5 ${data.status==='at_risk'?'ring-2 ring-rose-200':''}`}><div className="flex items-start justify-between"><div className="text-sm font-semibold text-slate-500">Broke Date</div><div className="text-2xl">⏳</div></div><div className={`mt-2 text-3xl font-black ${data.status==='at_risk'?'text-rose-600':'text-slate-950'}`}>{niceDate(data.broke_date)}</div><div className="mt-2 text-sm text-slate-500">{data.status==='at_risk' ? `${Math.max(0,riskDays)} days away · before cycle ends` : 'On track through your income cycle'}</div></div>
        <Metric title="Protected Jar" value={money(data.jar_balance)} sub="Round-ups excluded from spendable money" accent="🫙" />
      </section>

      <section className="mt-5 grid gap-5 lg:grid-cols-[1.6fr_.8fr]">
        <div className="card p-5 sm:p-6"><div className="flex items-center justify-between"><div><h2 className="text-lg font-black">Spend by category</h2><p className="text-sm text-slate-500">Discretionary rate: {money(data.discretionary_daily_rate)}/day</p></div><span className={`rounded-full px-3 py-1 text-xs font-extrabold ${data.status==='at_risk'?'bg-rose-100 text-rose-700':'bg-lime-100 text-lime-800'}`}>{data.status==='at_risk'?'AT RISK':'ON TRACK'}</span></div><div className="mt-6 h-64"><ResponsiveContainer width="100%" height="100%"><BarChart data={data.category_breakdown}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="category" tick={{fontSize:11}} axisLine={false}/><YAxis tick={{fontSize:11}} axisLine={false}/><Tooltip formatter={(v)=>money(v)}/><Bar dataKey="amount" fill="#84cc16" radius={[8,8,0,0]} /></BarChart></ResponsiveContainer></div></div>

        <div className="card overflow-hidden bg-slate-950 p-6 text-white"><div className="text-sm font-bold text-lime-300">AI CONTROLLER</div><h2 className="mt-2 text-2xl font-black">No-Spend Weekend</h2><p className="mt-2 text-sm leading-6 text-slate-300">When active, Fri–Sun uses a near-zero daily cap so your live safe-to-spend number protects the rest of the cycle.</p><button onClick={toggleWeekend} className={`mt-6 flex w-full items-center justify-between rounded-2xl p-4 font-bold ${data.no_spend_weekend?'bg-lime-400 text-slate-950':'bg-white/10 text-white'}`}><span>{data.no_spend_weekend?'Active':'Off'}</span><span className={`relative h-7 w-12 rounded-full ${data.no_spend_weekend?'bg-slate-950':'bg-white/20'}`}><span className={`absolute top-1 h-5 w-5 rounded-full bg-white transition ${data.no_spend_weekend?'left-6':'left-1'}`}/></span></button><div className="mt-6 border-t border-white/10 pt-5"><div className="flex justify-between text-sm"><span className="text-slate-400">Suggestion acceptance</span><b>{data.learn.acceptance_rate}%</b></div><div className="mt-3 flex justify-between text-sm"><span className="text-slate-400">Estimated days gained</span><b className="text-lime-300">+{data.learn.days_gained} days</b></div></div></div>
      </section>

      <section className="mt-5 grid gap-5 lg:grid-cols-2">
        <div className="card p-5 sm:p-6"><div className="mb-4 flex items-center justify-between"><div><h2 className="text-lg font-black">Recent transactions</h2><p className="text-sm text-slate-500">Every input source ends in the same spending engine.</p></div><button className="text-sm font-bold text-lime-700" onClick={()=>setAddOpen(true)}>Add +</button></div><div className="space-y-2">{data.recent_transactions.length ? data.recent_transactions.map(t => <div key={t.id} className="flex items-center gap-3 rounded-2xl p-3 hover:bg-slate-50"><div className="grid h-10 w-10 place-items-center rounded-xl bg-slate-100">{iconFor(t.category)}</div><div className="min-w-0 flex-1"><div className="truncate font-bold">{t.merchant}</div><div className="text-xs text-slate-500">{t.category} · {niceDate(t.date)} · {t.source}</div></div><div className="font-black">-{money(t.amount)}</div></div>) : <Empty text="No spending yet. Add your first transaction."/>}</div></div>

        <div className="card p-5 sm:p-6"><div className="mb-4"><h2 className="text-lg font-black">Detected subscriptions</h2><p className="text-sm text-slate-500">Recurring debits are separated from your discretionary burn rate.</p></div><div className="space-y-3">{data.subscriptions.length ? data.subscriptions.map(s => <div key={s.id} className="flex items-center justify-between rounded-2xl border border-slate-100 p-4"><div><div className="font-bold">{s.merchant}</div><div className="text-xs text-slate-500">Next: {niceDate(s.next_due_date)} · {s.confidence}% confidence</div></div><div className="text-right"><div className="font-black">{money(s.amount)}</div><div className="text-xs text-slate-400">every ~{s.cadence_days}d</div></div></div>) : <Empty text="Recurring payments will appear after repeated matching transactions."/>}</div></div>
      </section>

      <section className="mt-5 card p-5 sm:p-6"><div className="grid gap-5 md:grid-cols-3"><Mini title="Observe" text={`${data.recent_transactions.length} recent transactions are feeding your controller.`}/><Mini title="Predict" text={`At your current discretionary burn, Broke Date is ${niceDate(data.broke_date)}.`}/><Mini title="Learn" text={`${data.learn.accepted} of ${data.learn.responded} answered nudges accepted · +${data.learn.days_gained} days estimated gained.`}/></div></section>
    </main>

    <AddTransactionModal open={addOpen} onClose={()=>setAddOpen(false)} onSaved={saved} categories={categories}/>
    <NudgeModal nudge={nudge} onDone={()=>{setNudge(null);load()}}/>
  </div>
}

function Metric({title,value,sub,accent}) { return <div className="card p-5"><div className="flex items-start justify-between"><div className="text-sm font-semibold text-slate-500">{title}</div><div className="text-2xl">{accent}</div></div><div className="mt-2 text-3xl font-black">{value}</div><div className="mt-2 text-sm text-slate-500">{sub}</div></div> }
function Mini({title,text}) { return <div className="rounded-2xl bg-slate-50 p-4"><div className="text-xs font-extrabold uppercase tracking-widest text-lime-700">{title}</div><p className="mt-2 text-sm leading-6 text-slate-600">{text}</p></div> }
function Empty({text}) { return <div className="rounded-2xl bg-slate-50 p-6 text-center text-sm text-slate-500">{text}</div> }
function iconFor(c){ return ({Food:'🍜',Groceries:'🛒',Transport:'🚕',Shopping:'🛍️',Entertainment:'🎬',Subscription:'🔁',Rent:'🏠',Tuition:'🎓',Utilities:'💡'})[c] || '💸' }
