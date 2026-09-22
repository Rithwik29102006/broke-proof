import React, { useRef, useState } from 'react'
import { api } from '../lib/api'

const tabs = ['Manual', 'SMS Paste', 'Screenshot']

export default function AddTransactionModal({ open, onClose, onSaved, categories = [] }) {
  const [tab, setTab] = useState('Manual')
  const [form, setForm] = useState({ amount: '', merchant: '', category: '', note: '' })
  const [sms, setSms] = useState('')
  const [previews, setPreviews] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const fileRef = useRef()
  if (!open) return null

  const resetParsed = () => { setPreviews([]); setError('') }

  async function saveManual(e) {
    e.preventDefault(); setError(''); setLoading(true)
    try {
      const payload = { ...form, amount: Number(form.amount), category: form.category || null }
      const res = await api('/transactions/manual', { method:'POST', body: JSON.stringify(payload) })
      setForm({ amount: '', merchant: '', category: '', note: '' })
      onSaved(res)
    } catch (e) { setError(e.message) } finally { setLoading(false) }
  }

  async function parseSms() {
    setError(''); setLoading(true)
    try { setPreviews(await api('/transactions/parse-sms', { method:'POST', body: JSON.stringify({ text: sms }) })) }
    catch(e) { setError(e.message) } finally { setLoading(false) }
  }

  async function parseScreenshot(file) {
    if (!file) return
    setError(''); setLoading(true)
    const fd = new FormData(); fd.append('file', file)
    try { setPreviews([await api('/transactions/parse-screenshot', { method:'POST', body: fd })]) }
    catch(e) { setError(e.message) } finally { setLoading(false) }
  }

  function updatePreview(index, patch) {
    setPreviews(prev => prev.map((p, i) => i === index ? { ...p, ...patch } : p))
  }

  async function confirmPreviews() {
    setError(''); setLoading(true)
    try {
      let firstNudge = null
      for (const preview of previews) {
        const res = await api('/transactions/confirm', { method:'POST', body: JSON.stringify(preview) })
        if (!firstNudge && res.nudge) firstNudge = res.nudge
      }
      setPreviews([]); setSms(''); onSaved({ nudge: firstNudge })
    } catch(e) { setError(e.message) } finally { setLoading(false) }
  }

  return <div className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/40 p-0 backdrop-blur-sm sm:items-center sm:p-5" onMouseDown={onClose}>
    <div className="max-h-[92vh] w-full max-w-xl overflow-y-auto rounded-t-3xl bg-white p-5 shadow-2xl sm:rounded-3xl sm:p-7" onMouseDown={e=>e.stopPropagation()}>
      <div className="mb-5 flex items-center justify-between"><div><h2 className="text-2xl font-black">Add spending</h2><p className="text-sm text-slate-500">One pipeline, three easy inputs.</p></div><button onClick={onClose} className="rounded-full bg-slate-100 px-3 py-2">✕</button></div>
      <div className="mb-5 flex gap-1 overflow-x-auto rounded-2xl bg-slate-100 p-1">{tabs.map(t => <button key={t} onClick={()=>{setTab(t);resetParsed()}} className={`min-w-max flex-1 rounded-xl px-3 py-2 text-sm font-bold ${tab===t?'bg-white shadow-sm':'text-slate-500'}`}>{t}</button>)}</div>

      {tab === 'Manual' && <form onSubmit={saveManual} className="space-y-4">
        <div><label className="label">Amount (₹)</label><input className="input" type="number" min="0.01" step="0.01" value={form.amount} onChange={e=>setForm({...form,amount:e.target.value})} required /></div>
        <div><label className="label">Merchant</label><input className="input" value={form.merchant} onChange={e=>setForm({...form,merchant:e.target.value})} placeholder="Swiggy" /></div>
        <div><label className="label">Category</label><select className="input" value={form.category} onChange={e=>setForm({...form,category:e.target.value})}><option value="">Auto-detect / remember merchant</option>{categories.map(c=><option key={c}>{c}</option>)}</select></div>
        <div><label className="label">Note (optional)</label><input className="input" value={form.note} onChange={e=>setForm({...form,note:e.target.value})} /></div>
        <button className="btn-primary w-full" disabled={loading}>Log transaction</button>
      </form>}

      {tab === 'SMS Paste' && previews.length === 0 && <div className="space-y-4"><textarea className="input min-h-40" value={sms} onChange={e=>setSms(e.target.value)} placeholder={'Paste a bank or UPI debit SMS here…\n\nBatch mode: separate multiple messages with a blank line.'}/><button className="btn-primary w-full" onClick={parseSms} disabled={loading || !sms.trim()}>{loading?'Parsing…':'Detect transaction'}</button></div>}

      {tab === 'Screenshot' && previews.length === 0 && <div className="rounded-3xl border-2 border-dashed border-slate-200 p-8 text-center"><div className="text-4xl">📸</div><h3 className="mt-3 font-black">Upload payment screenshot</h3><p className="mt-1 text-sm text-slate-500">Tesseract OCR reads the image, then the same transaction parser extracts the payment.</p><input ref={fileRef} className="hidden" type="file" accept="image/*" onChange={e=>parseScreenshot(e.target.files?.[0])}/><button className="btn-secondary mt-5" onClick={()=>fileRef.current?.click()} disabled={loading}>{loading?'Reading image…':'Choose image'}</button></div>}

      {previews.length > 0 && <div className="space-y-4">
        {previews.length > 1 && <div className="rounded-2xl bg-slate-100 p-3 text-sm font-semibold text-slate-700">Detected {previews.length} transactions. Review each one before saving.</div>}
        {previews.map((preview, index) => <div key={index} className="rounded-3xl border border-lime-200 bg-lime-50 p-5"><div className="mb-3 text-xs font-extrabold uppercase tracking-wider text-lime-700">Review {previews.length > 1 ? `${index+1} of ${previews.length}` : 'before saving'}</div><div className="grid grid-cols-2 gap-3 text-sm"><Editable label="Amount" value={preview.amount} onChange={v=>updatePreview(index,{amount:Number(v)})}/><Editable label="Merchant" value={preview.merchant} onChange={v=>updatePreview(index,{merchant:v})}/><div><div className="text-slate-500">Category</div><select className="mt-1 w-full rounded-xl border border-lime-200 bg-white p-2" value={preview.category} onChange={e=>updatePreview(index,{category:e.target.value})}>{categories.map(c=><option key={c}>{c}</option>)}</select></div><Editable label="Date" type="date" value={preview.txn_date} onChange={v=>updatePreview(index,{txn_date:v})}/></div><p className="mt-4 text-xs text-slate-500">Parser: {preview.parser} · confidence {Math.round((preview.confidence||0)*100)}%</p></div>)}
        <div className="flex gap-3"><button className="btn-secondary flex-1" onClick={resetParsed}>Edit input</button><button className="btn-primary flex-1" onClick={confirmPreviews} disabled={loading}>{loading?'Saving…':`Confirm & save${previews.length>1?` ${previews.length}`:''}`}</button></div>
      </div>}
      {error && <div className="mt-4 rounded-2xl bg-rose-50 p-3 text-sm font-medium text-rose-700">{error}</div>}
    </div>
  </div>
}

function Editable({ label, value, onChange, type='text' }) {
  return <div><div className="text-slate-500">{label}</div><input type={type} className="mt-1 w-full rounded-xl border border-lime-200 bg-white p-2 font-semibold" value={value ?? ''} onChange={e=>onChange(e.target.value)} /></div>
}
