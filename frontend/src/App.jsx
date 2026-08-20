import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const WELCOME_MESSAGE = {
  role: "assistant",
  content:
    "¡Hola! Soy CineMatch 🎬 Contame qué tenés ganas de ver (un género, un mood, una duración) y te tiro recomendaciones basadas en TMDb.",
};

function App() {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend(e) {
    e.preventDefault();
    const mensaje = input.trim();
    if (!mensaje || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: mensaje }]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_URL}/recomendar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mensaje }),
      });

      if (!res.ok) throw new Error(`El servidor respondió ${res.status}`);

      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.respuesta },
      ]);
    } catch (err) {
      setError(
        "No pude conectarme con CineMatch. Revisá que el backend esté corriendo."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="header">
        <span className="logo">🎬</span>
        <div>
          <h1>CineMatch</h1>
          <p>Tu asistente de recomendaciones de películas</p>
        </div>
      </header>

      <main className="chat">
        {messages.map((msg, i) => (
          <div key={i} className={`bubble-row ${msg.role}`}>
            <div className="bubble">{msg.content}</div>
          </div>
        ))}

        {loading && (
          <div className="bubble-row assistant">
            <div className="bubble typing">
              <span className="dot" />
              <span className="dot" />
              <span className="dot" />
            </div>
          </div>
        )}

        {error && <div className="error-banner">{error}</div>}

        <div ref={bottomRef} />
      </main>

      <form className="composer" onSubmit={handleSend}>
        <input
          type="text"
          placeholder="Ej: quiero una peli de terror para hoy..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Enviar
        </button>
      </form>
    </div>
  );
}

export default App;
