# Submission draft: Bharat Agentic-AI Hackathon 2026 (Code for India)

Deadline 15 November 2026. Submission is a GitHub issue on `karlmehta/code-for-a-billion`. Fill the `[...]` fields
on the day; everything else is current. Judging is 25% each on size of problem, severity, quality of solution and
**proven impact** ("actual deployment data, not intentions"), so the pilot numbers section is the one that wins or
loses and must contain only what actually happened.

---

**Title:** Rihai: Section 479 BNSS release eligibility for undertrial prisoners, with a citation-gated drafter

**Team:** Sainath Gaikwad (build, Pune) with Pushkar [surname] (field pilot, Pune). Solo developer.

**Impact area / track:** Timely Justice / Legal Backlog

**Repo:** https://github.com/SainathGaikwad/rihai (MIT)

**Live demo:** [https://rihai.streamlit.app]

**Demo video:** [link, under 3 minutes]

**Built in AgentFoundry:** yes. Project `rihai`, Claude Agent SDK scaffold. The six tools in `rihai/agent/tools.py`
are the agent's whole tool surface; `rihai/agent/run.py` is the harness with the PreToolUse and Stop guardrails.
[screenshot of the AgentFoundry project attached]

## The problem

India's prisons held 5,34,993 people in September 2025 (NALSA UTRC report, Q3 2025); roughly three in four are
undertrials, people not convicted of anything. Section 479 of the Bharatiya Nagarik Suraksha Sanhita, 2023, in
force since 1 July 2024, entitles an undertrial to release on bail after serving half the maximum sentence for the
offence charged, a first-time offender to release on bond after one-third, and nobody may be held beyond the
maximum term. The Supreme Court directed every state to apply it proactively (*In Re: Inhuman Conditions in 1382
Prisons*, W.P.(C) 406/2013, orders of 23 August and 22 October 2024).

Between July 2024 and April 2025, 951 undertrials were identified under the section and 334 released nationally
(Rajya Sabha, 3 April 2025). In Q3 2025, 591 identified and 393 released (NALSA). Against a population in the
lakhs, that is the gap. The bottleneck is identification: the jail compiles a list by hand, the District Legal
Services Authority checks it by hand, the Undertrial Review Committee meets once a quarter. The arithmetic is a
date, a fraction and a maximum sentence, and nobody runs it continuously.

## What Rihai does

1. **Eligibility as code.** A prison roster (charge sections, custody start, prior convictions, pending cases) goes
   through `rihai/eligibility/s479.py`, which encodes each line of Section 479 against a law table of maximum
   sentences (755 rows: BNS, IPC, 17 special Acts). Unknown sections are refused. Ambiguous ones (a bare section
   with sub-sections of different maxima; attempt to murder where life depends on hurt caused) come back as
   `NEEDS_REVIEW` with the reason. Life or death offences are excluded as the section requires. Calendar arithmetic
   is done the way courts count sentences.
2. **Drafts from the assessment only.** For every eligible prisoner Rihai writes the Section 479 application and
   the DLSA/UTRC memo in English, Hindi or Marathi. In template mode no model is involved, so no figure in the
   draft can differ from what the engine computed.
3. **A citation gate.** Every statutory reference in any draft, template or model-written, English or Devanagari,
   must resolve to the law table or the short list of procedural provisions a s.479 application may cite. A bare
   "Section 999" with no Act, or "Section 999 of the Sanhita", blocks the draft.
4. **A model that narrates and cannot decide.** The agent (Claude Agent SDK; any OpenAI-compatible model for the
   prose layer) has six tools and no others. It cannot compute a date or a maximum term; it can only call the
   engine and rewrite prose, and its rewrite is used only if the gate passes and every date, day count and
   section survives unchanged. If a model is down, Rihai still works.

Rihai files nothing and decides nothing. Legal-aid counsel reviews; the court decides.

## Quality of solution

- 53 automated tests on the rule, the gate, the drafter in three languages, the model-acceptance contract, the
  agent guardrails and the front end.
- Every law-table row carries a `verified` flag and the India Code handle; `scripts/verify.py` records each row a
  reviewer checks. The engine reports which unverified rows an assessment relied on.
- The sample roster of 25 synthetic cases exercises every status: 10 eligible, 1 held beyond the maximum term,
  8 not yet, 2 excluded (life), 1 excluded (other case pending), 2 needing review, 1 unknown section.
- No prisoner names anywhere in the code or data; real rosters never enter the repository.

## Proven impact (the pilot)

Pune. Yerawada Central Prison (about 7,000 inmates), the prison legal-aid clinics of ILS Law College, Symbiosis
Law School and DES Law College, the Pune DLSA, and Prayas (TISS), which has worked in Yerawada for decades.

Fill with real numbers only; leave a line out rather than estimate it.

- Organisations met: [names, dates]
- Case files run through Rihai (anonymised, identifiers only): [n]
- Of those, found eligible by Rihai: [n]; confirmed by the clinic's lawyer: [n]; Rihai wrong: [n, with reason]
- Applications drafted: [n]; filed through LADC: [n]; orders received: [n]
- Time per case before (clinic's own estimate) and with Rihai: [minutes]
- Law-table rows verified against India Code by law students: [n] of 755
- Letters of intent / MoU: [who]

## Why it will keep working after the hackathon

The code is MIT, has no paid dependency, runs on a laptop without internet, and the rule it encodes is a statute
that changes rarely. The legal clinics already have the students and the access; what they lacked was the
arithmetic at scale. The next steps are OCR of scanned jail registers, splitting IPC 392 into its two limbs, and
verifying the remaining law-table rows.

---

*Draft prepared 24 October 2026. Rewrite the pilot section from the outreach log before posting.*
