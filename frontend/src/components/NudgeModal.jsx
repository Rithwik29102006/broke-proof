import React, { useState } from 'react'
import { api } from '../lib/api'

export default function NudgeModal({ nudge, onDone }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  if (!nudge) return null
  async function respond(accepted, action) {
    setLoading(true); setError('')
    try { await api(`/controller/nudges/${nudge.id}/respond`, { method:'POST', body: JSON.stringify({ accepted, action }) }); onDone() }
    catch(e){ setError(e.message) } finally { setLoading(false) }
  }
  return <div className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/50 p-5 backdrop-blur-sm">
    <div className="card w-full max-w-md p-7"><div className="text-4xl">⚡</div><h2 className="mt-4 text-2xl font-black">Overspend detected</h2><p className="mt-3 leading-7 text-slate-600">{nudge.message}</p><div className="mt-6 space-y-3"><button className="btn-primary w-full" onClick={()=>respond(true,'auto_trim')} disabled={loading}>Auto-trim tomorrow by ₹{Number(nudge.overage).toFixed(0)}</button><button className="btn-secondary w-full" onClick={()=>respond(false,'log_anyway')} disabled={loading}>Log anyway</button></div>{error&&<p className="mt-3 text-sm text-rose-600">{error}</p>}<p className="mt-4 text-xs text-slate-400">Your response is added to the visible Learn stat so the controller can adapt its future suggestions.</p></div>
  </div>
}
