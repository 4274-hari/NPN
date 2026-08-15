import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

function App() {
  return <main className="page"><p className="eyebrow">NPN</p><h1>Social Copilot</h1><p className="description">Your React workspace is ready. Connect your social platforms, models, RAG pipeline, and LLM services from here.</p><section className="status-card"><span className="status-dot" /><div><strong>Frontend is running</strong><p>FastAPI will be available at <code>http://localhost:8000</code>.</p></div></section></main>;
}
createRoot(document.getElementById('root')).render(<StrictMode><App /></StrictMode>);
