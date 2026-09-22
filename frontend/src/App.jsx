import React, { useState } from 'react'
import AuthScreen from './components/AuthScreen'
import Dashboard from './components/Dashboard'
import { isSignedIn } from './lib/api'

export default function App() {
  const [signedIn, setSignedIn] = useState(isSignedIn())
  return signedIn ? <Dashboard onLogout={()=>setSignedIn(false)} /> : <AuthScreen onDone={()=>setSignedIn(true)} />
}
