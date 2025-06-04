'use client'
import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'

const BOARD_MODEL_OPTIONS = [
  'gpt-4o',
  'o4-mini:high',
  'claude-3-7-sonnet-20250219',
  'gemini-2.0-flash'
]

const CEO_MODEL_OPTIONS = [
  'gemini-1.5-pro',
  'claude-3-5-sonnet-20240620'
]

export default function Home() {
  const [purpose, setPurpose] = useState('')
  const [factors, setFactors] = useState<string[]>([''])
  const [boardModels, setBoardModels] = useState<string[]>([BOARD_MODEL_OPTIONS[0]])
  const [ceoModel, setCeoModel] = useState(CEO_MODEL_OPTIONS[0])
  const [decisionResources, setDecisionResources] = useState('')
  const [response, setResponse] = useState<any | null>(null)
  const [loading, setLoading] = useState(false)

  const addFactor = () => setFactors([...factors, ''])
  const updateFactor = (index: number, value: string) => {
    setFactors(factors.map((f, i) => (i === index ? value : f)))
  }

  const addBoardModel = () => setBoardModels([...boardModels, BOARD_MODEL_OPTIONS[0]])
  const updateBoardModel = (index: number, value: string) => {
    setBoardModels(boardModels.map((m, i) => (i === index ? value : m)))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const boardXML = boardModels
      .map((m) => `<model name="${m}" />`)
      .join('')
    const factorsText = factors.filter(Boolean).join('\n')
    const xml = `<root><purpose>${purpose}</purpose><factors>${factorsText}</factors><board-models>${boardXML}</board-models><ceo-model name="${ceoModel}" /><decision-resources>${decisionResources}</decision-resources></root>`
    setLoading(true)
    try {
      const res = await fetch('http://localhost:8000/decide', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: xml })
      })
      const data = await res.json()
      setResponse(data)
    } catch (err) {
      setResponse({ error: 'Failed to submit request' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-xl space-y-6">
        <h1 className="text-2xl font-bold text-center">Rely AI Report Generator</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="purpose">Purpose</Label>
            <Textarea
              id="purpose"
              value={purpose}
              onChange={(e) => setPurpose(e.target.value)}
              placeholder="Describe the decision you need help with"
            />
          </div>
          <div className="space-y-2">
            <Label>Factors</Label>
            {factors.map((factor, i) => (
              <Input
                key={i}
                value={factor}
                onChange={(e) => updateFactor(i, e.target.value)}
                placeholder={`Factor ${i + 1}`}
                className="mb-2"
              />
            ))}
            <Button type="button" onClick={addFactor}>Add Factor</Button>
          </div>
          <div className="space-y-2">
            <Label>Board Models</Label>
            {boardModels.map((model, i) => (
              <Select
                key={i}
                value={model}
                onChange={(e) => updateBoardModel(i, e.target.value)}
                className="mb-2"
              >
                {BOARD_MODEL_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </Select>
            ))}
            <Button type="button" onClick={addBoardModel}>Add Model</Button>
          </div>
          <div className="space-y-2">
            <Label>CEO Model</Label>
            <Select value={ceoModel} onChange={(e) => setCeoModel(e.target.value)}>
              {CEO_MODEL_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="resources">Decision Resources</Label>
            <Textarea
              id="resources"
              value={decisionResources}
              onChange={(e) => setDecisionResources(e.target.value)}
              placeholder="Links or notes the models should consider"
            />
          </div>
          <Button type="submit" disabled={loading} className="w-full">
            {loading ? 'Generating...' : 'Generate'}
          </Button>
        </form>
        {response && (
          <pre className="whitespace-pre-wrap text-sm bg-gray-100 p-4 rounded">
            {JSON.stringify(response, null, 2)}
          </pre>
        )}
      </div>
    </div>
  )
}
