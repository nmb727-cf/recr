import { createRoot } from 'react-dom/client'
import './index.css'
import './i18n'  // must be imported before App so translations are ready on first render
import App from './App.tsx'

// Note: StrictMode intentionally omitted — react-beautiful-dnd is incompatible
// with React 18 StrictMode's double-invocation behaviour.
createRoot(document.getElementById('root')!).render(<App />)
