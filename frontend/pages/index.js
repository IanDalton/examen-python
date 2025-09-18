'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

const EXPLANATIONS = {
  'tests/test_bookbyte_catalogo.py::test_agregar_y_buscar':
    'Asegurate de que Catalogo.buscar devuelva el mismo objeto que se agregó y None cuando el código no existe.',
  'tests/test_bookbyte_catalogo.py::test_agregar_duplicado_imprime_mensaje':
    'Cuando se agrega dos veces el mismo código, el método debe detectar el duplicado y mostrar el mensaje indicado.',
  'tests/test_bookbyte_catalogo.py::test_eliminar_y_mensajes':
    'El método eliminar debe informar si el código no existe y realmente quitar el producto cuando sí estaba.',
  'tests/test_bookbyte_catalogo.py::test_listar_por_precio_vacio':
    'Si el catálogo está vacío, listar_por_precio debe imprimir el mensaje especial y no fallar.',
  'tests/test_bookbyte_catalogo.py::test_listar_por_precio_orden':
    'Revisa que la lista se ordene por precio ascendente y que el formato de cada línea coincida con el esperado.',
  'tests/test_bookbyte_catalogo.py::test_filtrar_baratos_header_y_total':
    'La salida debe incluir el encabezado, solo los productos baratos y el total correcto al final.',
  'tests/test_bookbyte_catalogo.py::test_exportar_csv_crea_archivo_con_campos':
    'El CSV debe crearse con encabezados exactos y cada fila debe respetar el formato solicitado para eBooks y libros físicos.',
  'tests/test_bookbyte_catalogo.py::test_exportar_csv_cat_vacio_no_crea_archivo':
    'No deberías generar archivos cuando el catálogo no tiene productos.',
  'tests/test_bookbyte_catalogo.py::test_exportar_csv_error_escribe_mensaje':
    'Ante un error de escritura, captura la excepción y mostrá el mensaje de error correcto.',
  'tests/test_bookbyte_products.py::test_ean13_validator_exists':
    'Implementá validar_ean13 en Producto y devolvé True solo cuando el código cumpla el chequeo EAN-13.',
  'tests/test_bookbyte_products.py::test_librofisico_multiple_inheritance':
    'LibroFisico debe heredar de Producto, ImponibleIVA y Puntuable para compartir los métodos requeridos.',
  'tests/test_bookbyte_products.py::test_ebook_inherits_puntuable':
    'EBook hereda de Producto y Puntuable, pero no de ImponibleIVA; revisá la jerarquía de clases.',
  'tests/test_bookbyte_products.py::test_validaciones_basicas_producto':
    'Las validaciones deben lanzar excepciones cuando faltan datos obligatorios o el precio no es positivo.',
  'tests/test_bookbyte_products.py::test_validaciones_especificas':
    'Chequeá los campos particulares: formato permitido, tamaño positivo y validación del ISBN y peso.',
  'tests/test_bookbyte_products.py::test_repr_formato':
    'El texto de mostrar/str debe incluir tipo, título, autor, código, precio y datos específicos de cada producto.',
  'tests/test_bookbyte_products.py::test_puntuable_ratings':
    'Guardá las calificaciones numéricas y devolvé el promedio correcto cuando haya ratings.',
  'tests/test_bookbyte_products.py::test_imponible_iva':
    'Implementá precio_con_iva multiplicando por 1.21 para los productos imponibles.',
};

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
            {(() => {
              const feedback = entry.last_feedback || EXPLANATIONS[entry.nodeid];
              if (!feedback) return null;
              return (
                <p className="explanation">
                  <strong>Última pista:</strong> {feedback}
                </p>
              );
            })()}
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
  const numericScore = typeof score === 'number' ? score : Number(score);
  const displayScore = Number.isFinite(numericScore) ? numericScore.toFixed(2) : score;
  return (
    <div className="panel">
      <h2>Resultado del examen</h2>
      <div className="score-card">
        <div>
          <span className="score">{displayScore}</span>
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
          {results.map((test, index) => {
            const nodeid = test.nodeid || `desconocido-${index}`;
            const phase = test.phase && test.phase !== 'call' ? ` (${test.phase})` : '';
            const key = `${nodeid}-${test.phase || 'call'}-${index}`;
            const explanation = test.feedback || EXPLANATIONS[nodeid];
            return (
              <li key={key} className={test.outcome === 'passed' ? 'ok' : 'fail'}>
                <div className="test-header">
                  <span>{test.outcome === 'passed' ? '✅' : '❌'}</span>
                  <code>{`${nodeid}${phase}`}</code>
                </div>
                {test.outcome !== 'passed' && explanation ? (
                  <p className="explanation">
                    <strong>Posible causa:</strong> {explanation}
                  </p>
                ) : null}
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

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const stored = window.localStorage.getItem('exam-result');
    if (!stored) return;
    try {
      const parsed = JSON.parse(stored);
      setResult(parsed);
    } catch (err) {
      console.warn('No se pudo leer el resultado guardado', err);
    }
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined' || !result) return;
    window.localStorage.setItem('exam-result', JSON.stringify(result));
  }, [result]);

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
