import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { ChatPage } from './pages/ChatPage'
import { HomePage } from './pages/HomePage'
import { PipelinePage } from './pages/PipelinePage'
import { ProjectsPage } from './pages/ProjectsPage'
import { UploadPage } from './pages/UploadPage'

/** Under nginx gateway the app is served at /gw/agent/*; keep local root otherwise. */
function gatewayBasename(): string {
  if (typeof window === 'undefined') return '/'
  const m = window.location.pathname.match(/^(.*?\/gw\/agent)(?=\/|$)/)
  return m?.[1] || '/'
}

export default function App() {
  return (
    <BrowserRouter basename={gatewayBasename()}>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/pipeline" element={<PipelinePage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
