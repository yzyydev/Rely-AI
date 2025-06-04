'use client';
import { useState } from 'react';

export default function Home() {
  const [purpose, setPurpose] = useState('');
  const [factors, setFactors] = useState('');
  const [boardModels, setBoardModels] = useState('');
  const [ceoModel, setCeoModel] = useState('');
  const [decisionResources, setDecisionResources] = useState('');
  const [response, setResponse] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const boardXML = boardModels
      .split(',')
      .map((m) => m.trim())
      .filter(Boolean)
      .map((m) => `<model name="${m}" />`)
      .join('');
    const xml = `<root><purpose>${purpose}</purpose><factors>${factors}</factors><board-models>${boardXML}</board-models><ceo-model name="${ceoModel}" /><decision-resources>${decisionResources}</decision-resources></root>`;
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/decide', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: xml }),
      });
      const data = await res.json();
      setResponse(data);
    } catch (err) {
      setResponse({ error: 'Failed to submit request' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Rely AI Report Generator</h1>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <textarea
          value={purpose}
          onChange={(e) => setPurpose(e.target.value)}
          placeholder="Purpose"
          className="border p-2 rounded"
        />
        <textarea
          value={factors}
          onChange={(e) => setFactors(e.target.value)}
          placeholder="Factors"
          className="border p-2 rounded"
        />
        <input
          value={boardModels}
          onChange={(e) => setBoardModels(e.target.value)}
          placeholder="Board Models (comma separated)"
          className="border p-2 rounded"
        />
        <input
          value={ceoModel}
          onChange={(e) => setCeoModel(e.target.value)}
          placeholder="CEO Model"
          className="border p-2 rounded"
        />
        <textarea
          value={decisionResources}
          onChange={(e) => setDecisionResources(e.target.value)}
          placeholder="Decision Resources"
          className="border p-2 rounded"
        />
        <button
          type="submit"
          className="bg-black text-white px-4 py-2 rounded disabled:opacity-50"
          disabled={loading}
        >
          {loading ? 'Generating...' : 'Generate'}
        </button>
      </form>
      {response && (
        <pre className="mt-4 whitespace-pre-wrap text-sm bg-gray-100 p-4 rounded">
          {JSON.stringify(response, null, 2)}
        </pre>
      )}
    </div>
  );
}
