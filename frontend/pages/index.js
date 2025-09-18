'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

function FailureLog({ log }) {
  const entries = useMemo(() => {
    if (!log || !log.failures) return [];
    return Object.entries(log.failures)
      .map(([nodeid, info]) => ({ nodeid, ...info }))
      .sort((a, b) => b.count - a.count);
  }, [log]);

  if (!entries.length) {
    return (
      <div className="panel">
        <h2>Historial de fallos</h2>
        <p>Aún no hay envíos registrados.</p>
      </div>
    );
  }

  return (
    <div className="panel">
      <h2>Historial de fallos</h2>
      <ul className="log-list">
        {entries.map((entry) => (
          <li key={entry.nodeid}>
            <div className="log-header">
              <span className="badge">{entry.count}</span>
              <code>{entry.nodeid}</code>
            </div>
            {entry.last_message ? (
              <details>
                <summary>Último error</summary>
                <pre>{entry.last_message}</pre>
              </details>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}

function ResultsPanel({ result }) {
  if (!result) {
    return (
      <div className="panel">
        <h2>Resultado del examen</h2>
        <p>Envía tu solución para ver la calificación.</p>
      </div>
    );
  }

  const { student, score, passed, failed, total_tests, results } = result;
  return (
    <div className="panel">
      <h2>Resultado del examen</h2>
      <div className="score-card">
        <div>
          <span className="score">{score}</span>
          <span className="over">/100</span>
        </div>
        <div className="meta">
          <p><strong>Estudiante:</strong> {student}</p>
          <p>
            <strong>Tests:</strong> {passed} aprobados · {failed} fallidos · {total_tests} en total
          </p>
        </div>
      </div>
      <div className="tests">
        <h3>Detalle de tests</h3>
        <ul>
          {results.map((test) => {
            const phase = test.phase && test.phase !== 'call' ? ` (${test.phase})` : '';
            const key = `${test.nodeid}${phase}`;
            return (
              <li key={key} className={test.outcome === 'passed' ? 'ok' : 'fail'}>
                <div className="test-header">
                  <span>{test.outcome === 'passed' ? '✅' : '❌'}</span>
                  <code>{`${test.nodeid}${phase}`}</code>
                </div>
                {test.message ? <pre>{test.message}</pre> : null}
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

export default function Home() {
  const [studentName, setStudentName] = useState('');
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [log, setLog] = useState({ failures: {} });

  const fetchLog = useCallback(async () => {
    try {
      const resp = await fetch(`${BACKEND_URL}/api/logs`);
      if (!resp.ok) throw new Error('No se pudo obtener el historial');
      const data = await resp.json();
      setLog(data);
    } catch (err) {
      console.error(err);
    }
  }, []);

  useEffect(() => {
    fetchLog();
  }, [fetchLog]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setResult(null);

    if (!studentName.trim()) {
      setError('Debes ingresar tu nombre completo.');
      return;
    }
    if (!file) {
      setError('Debes adjuntar tu archivo de examen (.py).');
      return;
    }

    const formData = new FormData();
    formData.append('student_name', studentName.trim());
    formData.append('file', file);

    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/submit`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const message = await response.json().catch(() => ({}));
        throw new Error(message.detail || 'Error al procesar el examen');
      }

      const data = await response.json();
      setResult(data);
      setLog(data.failure_log || { failures: {} });
    } catch (err) {
      setError(err.message || 'Error inesperado');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="layout">
      <header>
        <h1>Portal de Exámenes Book&Byte</h1>
        <p>Carga tu solución, ejecutamos las pruebas automáticamente y recibe tu puntaje al instante.</p>
      </header>

      <section className="panel">
        <h2>Subir examen</h2>
        <form onSubmit={handleSubmit} className="form">
          <label>
            Nombre del estudiante
            <input
              type="text"
              value={studentName}
              onChange={(event) => setStudentName(event.target.value)}
              placeholder="Ej: Ada Lovelace"
            />
          </label>
          <label className="file">
            Archivo del examen (.py)
            <input type="file" accept=".py" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
          </label>
          {error ? <p className="error">{error}</p> : null}
          <button type="submit" disabled={loading}>
            {loading ? 'Evaluando…' : 'Enviar y evaluar'}
          </button>
        </form>
      </section>

      <div className="grid">
        <ResultsPanel result={result} />
        <FailureLog log={log} />
      </div>

      <footer>
        <small>
          Backend: <code>{BACKEND_URL}</code>
        </small>
      </footer>
    </main>
  );
}
