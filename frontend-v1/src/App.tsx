/**
 * Root application shell.
 *
 * Routing, React Query provider, and Zustand store wiring are established in
 * AS-006. This placeholder intentionally renders only a bootstrap banner so the
 * Vite dev server, TypeScript, ESLint, and Tailwind pipeline can be verified
 * end-to-end.
 */
function App() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-100">
      <div className="text-center">
        <h1 className="text-3xl font-semibold tracking-tight">MarketSignal AI</h1>
        <p className="mt-2 text-sm text-slate-400">
          Hello Deric 
        </p>
      </div>
    </div>
  )
}

export default App
