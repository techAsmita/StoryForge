import { Route, Routes } from 'react-router-dom'
import Sidebar, { Logo, ModeCard } from './components/Sidebar'
import CreatePage from './pages/CreatePage'
import LibraryPage from './pages/LibraryPage'
import StoryPage from './pages/StoryPage'
import ExplorePage from './pages/ExplorePage'
import SettingsPage from './pages/SettingsPage'

export default function App() {
  return (
    <div className="min-h-screen">
      <Sidebar />
      <div className="lg:pl-56">
        {/* Compact header on phones and tablets (the sidebar is hidden there) */}
        <div className="lg:hidden flex items-center justify-between px-4 pt-4 [&_img]:size-8 [&_span]:text-lg">
          <div className="[&>div]:flex-row [&>div]:gap-2"><Logo /></div>
        </div>
        <main className="mx-auto max-w-[1500px] px-3 sm:px-6 lg:px-8 py-4 sm:py-6 pb-28 lg:pb-8">
          <Routes>
            <Route path="/" element={<CreatePage />} />
            <Route path="/library" element={<LibraryPage />} />
            <Route path="/library/:id" element={<StoryPage />} />
            <Route path="/explore" element={<ExplorePage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
          <div className="lg:hidden mt-6"><ModeCard /></div>
        </main>
      </div>
    </div>
  )
}
