# FastAPI Backend – **Experimental Parallel‑LLM MVP (Stateless)**

**Version:** 0.3  **Date:** 2025‑05‑13

---

## 1 · Goal

Prove that we can **fan‑out** multiple LLM calls in parallel (Board Phase) and immediately **fan‑in** a second LLM call (CEO Phase) that decides between the board responses, all within a single FastAPI process—with **no database or external persistence layer** except simple markdown files written to `/backend/output`. The Backend should be implemented in /backend folder.

---

## 2 · Key Requirements

| ID      | Requirement                                                                                                                                             |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **R‑1** | Accept an HTTP request containing a xml file with purpose, factors, decision resources and models.                                            |
| **R‑2** | For each model, call the corresponding provider **concurrently** and capture its response (Board Phase).                                                |
| **R‑3** | After all board responses resolve, call a *CEO* model with the structured prompt template (see §5) and receive the final decision markdown (CEO Phase). |
| **R‑4** | Write all board responses and the CEO markdown to `/output/<uuid>/…` files.                                                                             |
| **R‑5** | Return a JSON payload indicating the filesystem path of the CEO markdown once the entire flow finishes.                                                 |
---

## 3 · Minimal Tech Stack

| Concern           | Choice                  | Rationale                            |
| ----------------- | ----------------------- | ------------------------------------ |
| API Server        | **FastAPI**             | Async‑friendly, quick Swagger.       |
| HTTP Client       | **httpx (async)**       | Native `asyncio` watches.            |
| LLM Provider      | `openai`                | Can route to multiple models.        |
| Concurrency       | `asyncio.gather`        | Single event loop, no Celery needed. |
| State at run‑time | Python `dict` in memory | Thread status tracking.              |
| Persistence       | *Filesystem only*       | All artefacts under `/output`.       |

---

## 4 · Runtime Flow

```
Client  ── POST /decide ─▶  FastAPI Route
                              │ (validate)
                              ▼
                   async process_decision()            
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼  (fan‑out)
     call_model(model‑1) … call_model(model‑N)    ≤— asyncio.gather
              │                               │
              └───────────────┬───────────────┘
                              ▼  (fan‑in)
                    call_ceo_model(board_responses)
                              │
                              ▼
                write /output/<id>/*.md files
                              │
                              ▼
            JSON response { id, ceo_path }
```

**Blocking behaviour**: the HTTP connection stays open until the CEO markdown is ready. This keeps the MVP stateless.

---

## 5 · Prompt Templates

### 5.1 Board Phase

<purpose> I want to rigorously evaluate whether purchasing a Ferrari F80 under current liquidity constraints, using a bank loan at a 3% yield, is a sound financial decision, considering the potential to resell the vehicle at a 20% premium. Here are the top 3 factors I'm considering: 
</purpose>
<factors>
    1. Net Return on Investment (Comparison between the loan interest cost and the expected resale profit) 
    2. Liquidity Management (Ability to cover short-term obligations while capital is tied up in the asset) 
    3. Market Risk (Certainty and timing of achieving the projected 20% selling price premium) 
    4. Transaction & Holding Costs (Fees, taxes, insurance, and potential depreciation during holding period) 
    5. Opportunity Cost (Potential returns from alternative investments or use of capital) 
    6. Bank Loan Terms & Repayment Flexibility (Early repayment penalties, collateral requirements, default risk) 
</factors>
<models>
    <model name="gpt-4o" />
    <model name="claude-3-sonnet" />
</models>
<decision-resources>
...
</decision-resources>

### 5.2 CEO Phase

```
<purpose>
    You are a CEO of a company. You are given a list of responses from your board of directors. Your job is to take in the original question prompt, and each of the board members' responses, and choose the best direction for your company.
</purpose>
<instructions>
    <instruction>Each board member has proposed an answer to the question posed in the prompt.</instruction>
    <instruction>Given the original question prompt, and each of the board members' responses, choose the best answer.</instruction>
    <instruction>Tally the votes of the board members, choose the best direction, and explain why you chose it.</instruction>
    <instruction>To preserve anonymity, we will use model names instead of real names of your board members. When responding, use the model names in your response.</instruction>
    <instruction>As a CEO, you breakdown the decision into several categories including: risk, reward, timeline, and resources. In addition to these guiding categories, you also consider the board members' expertise and experience. As a bleeding edge CEO, you also invent new dimensions of decision making to help you make the best decision for your company.</instruction>
    <instruction>Your final CEO response should be in markdown format with a comprehensive explanation of your decision. Start the top of the file with a title that says "CEO Decision", include a table of contents, briefly describe the question/problem at hand then dive into several sections. One of your first sections should be a quick summary of your decision, then breakdown each of the boards decisions into sections with your commentary on each. Where we lead into your decision with the categories of your decision making process, and then we lead into your final decision.</instruction>
</instructions>
<original-question>{original_prompt}</original-question>
<board-decisions>
    <board-response>
        <model-name>{name}</model-name>
        <response>{board_output}</response>
    </board-response>
    …
</board-decisions>
```

The backend interpolates **`{original_prompt}`** and loops over board responses to fill `<board-response>` elements.

---

## 6 · API Contract

### POST `/decide`

| Field    | Type      | Example                                          |
| -------- | --------- | ------------------------------------------------ |
| `prompt` | string    | "Should we enter the EV market?"                 |
| `models` | string\[] | `["gpt-4o", "gpt-3.5-turbo", "claude-3-sonnet"]` |

*Response (`200` OK, synchronous)*

```json
{
  "id": "0b68d7e8-…",
  "status": "completed",
  "board": [
    {"model": "gpt-4o", "path": "/output/…/board_gpt-4o.md"},
    {"model": "gpt-3.5-turbo", "path": "/output/…/board_gpt-3.5-turbo.md"}
  ],
  "ceo_decision_path": "/output/…/ceo_decision.md",
  "ceo_prompt": "/output/…/ceo_prompt.xml"
}
```

HTTP 400 on validation errors. No `GET` route is strictly required because call is blocking, but may be added later.

---

## 7 · File Layout under `/backend/output`

```
/backend/output/
 └─ <uuid>/
      ├─ board_<model‑name>.md     # N files, raw responses
      └─ ceo_decision.md          # final markdown
      └─ ceo_prompt.xml           # ceo decision prompt input from the CEO Phase
```

The UUID is generated per request. No other files are written.

---

## 8 · Key Implementation Points

1. **Global in‑memory registry**

   ```python
   DECISIONS: dict[str, DecisionStatus] = {}
   ```
2. **Parallel LLM calls**

   ```python
   board_results = await asyncio.gather(*[
       call_model(name, prompt) for name in models
   ])
   ```
3. **CEO call after gather**

---

## 9 · Environment Variables

| Var                 | Purpose                             | Default   |
| ------------------- | ----------------------------------- | --------- |
| `OPENAI_API_KEY`    | Used for any `gpt-*` model names    | —         |
| `ANTHROPIC_API_KEY` | For models starting with `claude-*` | —         |
| `OUTPUT_DIR`        | Parent folder for artefacts         | `/output` |

---

## 10 · Local Run & Demo

```bash
$ export OPENAI_API_KEY=sk‑...
$ uvicorn app.main:app --reload
# In another terminal:
$ curl -X POST http://localhost:8000/decide \
       -H 'Content-Type: application/json' \
       -d '{"prompt":"Should we enter the EV market?","models":["gpt-3.5-turbo","gpt-4o"]}'
```

Result JSON will list absolute paths. Open the generated markdown to verify structure.

---

## 11 · Testing

* **Unit**: prompt assembly, path creation.
* **Async Integration**: monkeypatch `openai.AsyncClient.chat.completions` to return canned text, ensure `asyncio.gather` runs.

---

**End of Document**
