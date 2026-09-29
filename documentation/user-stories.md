# ShopFloor Copilot — MVP User Stories

These two stories cover the MVP core described in the
[architecture plan](architecture-plan.md): **RAG over plant documents** and
**plain-language questions over live MES data**.

---

## US-01 — Troubleshoot an alarm from plant documents

**As a** machine operator on the shop floor,
**I want to** ask the copilot what an alarm means and how to clear it, in plain language,
**so that** I can fix common stoppages myself without searching through PDF manuals or waiting for
maintenance.

### Example

> **Operator:** "Alarm E-217 on Filler 2. What do I check first?"
>
> **Copilot:** "E-217 is *low bottle infeed pressure*. Check in this order:
> 1. Air supply valve V-12 is open (pressure ≥ 6 bar) [1]
> 2. Infeed star wheel is not jammed [1]
> 3. If it still faults, lock out the machine and call maintenance — do not bypass sensor PS-4 [2]
>
> [1] Filler 2 Operating Manual, §7.3, p. 84 · [2] SOP-SAF-011 Lockout/Tagout, rev C"

### Acceptance criteria

1. **Given** SOPs, manuals and alarm guides have been ingested (PDF, DOCX),
   **when** the operator asks a question, **then** the answer is returned in under 5 seconds (p95).
2. Every factual statement in the answer has a **citation**: document title, revision, and
   section or page. Clicking a citation opens the source at that page.
3. **Given** no relevant document is found (retrieval score below the threshold),
   **then** the copilot says *"I couldn't find this in the plant documents"* and does **not** guess.
4. Safety-critical content (lockout/tagout, PPE, bypass warnings) from the source is always included
   in the answer, never left out by summarization.
5. Only the **current** revision of a document is used. Superseded revisions are excluded from
   retrieval.
6. The operator can mark an answer 👍 / 👎. The feedback, question, retrieved chunks and answer are
   logged to Langfuse for evaluation.
7. Users only see documents for the sites and lines their role allows (Keycloak roles).

### Out of scope (MVP)

- Voice input, multilingual answers, images and diagrams inside answers.
- Writing anything back to the MES or creating maintenance tickets.

---

## US-02 — Ask why a line underperformed, using live MES data

**As a** production supervisor,
**I want to** ask the copilot questions about OEE, downtime and scrap for my lines in plain language,
**so that** I can find the main causes of lost production in seconds instead of building reports
by hand at the start of every shift.

### Example

> **Supervisor:** "Why was Line 3 OEE low on yesterday's night shift?"
>
> **Copilot:** "Line 3 night shift (22:00–06:00, 26 Oct) OEE was **61%** vs a 7-day average of 78%.
> - **Availability 72%**: 95 min unplanned downtime. 70 min came from *Labeler jam* (4 stops)
> - **Performance 91%**, **Quality 93%**: scrap 412 units, mostly *label misalignment*
>
> The labeler jams and the misalignment scrap probably share a cause. The Labeler manual suggests
> checking web tension and the label sensor calibration [1].
>
> Data: MES downtime and production records, Line 3, 26 Oct 22:00–06:00 · [1] Labeler LX-500
> Manual, §5.2"

### Acceptance criteria

1. The copilot answers using **tool calls** (`get_oee`, `get_downtime`, `get_scrap`,
   `get_work_order`) that run safe, parameterized, **read-only** SQL against the MES data.
   The LLM never writes raw SQL.
2. Numbers in the answer exactly match the tool results. Each answer shows the **data source and
   time range** it used, and the user can expand the raw tool output.
3. Relative times ("yesterday's night shift", "last week") resolve using the plant's **shift
   calendar and time zone**, and the resolved range is stated in the answer.
4. **Given** a line, shift or time range that has no data, **then** the copilot says so instead of
   inventing figures.
5. When documents are relevant to the cause (e.g. a manual section for the top downtime reason),
   the answer can combine data and document citations, as in US-01.
6. The supervisor only sees data for the sites and lines their role allows.
7. Response time under 8 seconds (p95) for questions that need up to 3 tool calls.

### Out of scope (MVP)

- Charts inside the chat (dashboards cover this separately).
- Predictive answers ("will Line 3 miss its target today?").
- Changing schedules, orders or any other write action.
