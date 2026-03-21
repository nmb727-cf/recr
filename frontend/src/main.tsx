import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// Note: StrictMode intentionally omitted — react-beautiful-dnd is incompatible
// with React 18 StrictMode's double-invocation behaviour.
createRoot(document.getElementById('root')!).render(<App />)
