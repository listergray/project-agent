import { useEffect } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { Shell } from './components/Shell'
import { ensureSettings } from './db'
import { ensureHome } from './lib/homeLayout'
import { ensureDefaultMaintains, syncMaintainTasks } from './lib/maintain'
import { syncMoneyMonthly } from './lib/moneyMonthly'
import {
  bootRemoteSync,
  pushLedgerToRemote,
  startRemotePushLoop,
} from './lib/remoteSync'
import { adoptRouteA } from './lib/route'
import { Assets } from './pages/Assets'
import { Body } from './pages/Body'
import { Cover } from './pages/Cover'
import { Goals } from './pages/Goals'
import { Home } from './pages/Home'
import { OpenPlanDesign } from './pages/OpenPlanDesign'
import { Nine } from './pages/Nine'
import { People } from './pages/People'
import { PersonDetail } from './pages/PersonDetail'
import { RoomDetail } from './pages/RoomDetail'
import { Settings } from './pages/Settings'
import { Today } from './pages/Today'
import { Todos } from './pages/Todos'

export default function App() {
  useEffect(() => {
    void (async () => {
      await ensureSettings()
      const sync = await bootRemoteSync()
      if (!sync.ok) console.warn('[sync]', sync.message)
      await ensureSettings()
      await ensureHome()
      await adoptRouteA()
      await ensureDefaultMaintains()
      await syncMaintainTasks()
      await syncMoneyMonthly()
      startRemotePushLoop()
      try {
        await pushLedgerToRemote(true)
      } catch (err) {
        console.warn('[sync] initial push', err)
      }
    })()
  }, [])

  return (
    <Routes>
      <Route path="/" element={<Cover />} />
      <Route path="home/design" element={<OpenPlanDesign />} />
      <Route element={<Shell />}>
        <Route path="assets" element={<Assets />} />
        <Route path="assets/:kind" element={<Assets />} />
        <Route path="today" element={<Today />} />
        <Route path="todos" element={<Todos />} />
        <Route path="goals" element={<Goals />} />
        <Route path="body" element={<Body />} />
        <Route path="people" element={<People />} />
        <Route path="people/:id" element={<PersonDetail />} />
        <Route path="nine" element={<Nine />} />
        <Route path="home" element={<Home />} />
        <Route path="home/room/:id" element={<RoomDetail />} />
        <Route path="settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
