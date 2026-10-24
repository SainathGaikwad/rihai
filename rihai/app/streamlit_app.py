"""Rihai - Streamlit front end.  streamlit run rihai/app/streamlit_app.py

Three tabs: one prisoner, a roster CSV, the law table. No names are stored; the roster identifier is whatever the
jail or clinic uses. Everything shown is computed by rihai.eligibility; the application text is the template drafter
with the citation gate run on it.
"""
from __future__ import annotations

import io
import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rihai.agent import llm  # noqa: E402
from rihai.agent.draft import Particulars, draft  # noqa: E402
from rihai.eligibility import Charge, Prisoner, Status, assess, assess_roster  # noqa: E402
from rihai.eligibility.s479 import _split_charge  # noqa: E402
from rihai.law import all_rows, stats  # noqa: E402

st.set_page_config(page_title="Rihai - Section 479 BNSS", page_icon="⚖️", layout="wide")

st.title("Rihai")
st.caption("Release eligibility of undertrial prisoners under Section 479 of the Bharatiya Nagarik Suraksha Sanhita, 2023. "
           "The code decides; the model narrates. Drafts are for review by legal-aid counsel before filing.")

with st.sidebar:
    st.markdown("**How it works**")
    st.markdown("1. The rule in s.479 runs as code over the roster: charges, custody date, prior convictions.\n"
                "2. Eligible cases get a template application and a DLSA memo in English, Hindi or Marathi.\n"
                "3. A citation gate checks every section in every draft against the law table.\n"
                "4. A model may rewrite the prose; its version is used only if the gate passes and every date, "
                "day count and section is unchanged.")
    st.markdown(f"Model for prose: **{'configured (' + str(llm.config()['model']) + ')' if llm.available() else 'none; template mode'}**")
    st.caption("Keys live in Streamlit secrets or environment variables, never in the repository.")
    st.markdown("[Source and law table on GitHub](https://github.com/SainathGaikwad/rihai)")

STATUS_HELP = {
    "ELIGIBLE": "Threshold under s.479(1) met: release on bond (first-time) or bail.",
    "MUST_RELEASE_MAX_TERM": "Detained for the full maximum term: third proviso to s.479(1), release is mandatory.",
    "NOT_YET": "Threshold not yet reached; the date it will be is shown.",
    "EXCLUDED_LIFE_OR_DEATH": "An offence charged carries death or life imprisonment; s.479 does not apply.",
    "EXCLUDED_MULTIPLE_CASES": "s.479(2): other cases pending. Verify; the maximum-term cap still applies.",
    "NEEDS_REVIEW": "The law table cannot settle it without a human (sub-section, conditional life, no stated ceiling).",
    "UNKNOWN_SECTION": "A charge is not in the law table. Nothing is guessed.",
}

tab1, tab2, tab3 = st.tabs(["One prisoner", "Roster (CSV)", "Law table"])

with tab1:
    c1, c2 = st.columns([1, 1])
    with c1:
        charges_txt = st.text_input("Charges (comma-separated)", "BNS 303(2)", help="e.g. BNS 303(2), IPC/379, NDPS/20(small)")
        custody = st.date_input("In custody since", date(2025, 1, 10), min_value=date(2000, 1, 1), max_value=date.today())
        first = st.checkbox("First-time offender (never convicted of any offence)", True)
        multi = st.checkbox("Another case / investigation pending (s.479(2))", False)
        delay = st.number_input("Days of delay attributable to the accused (Explanation)", 0, 5000, 0)
        ident = st.text_input("Roster identifier (no names)", "UTP-0417")
        as_of = st.date_input("Assess as on", date.today())
    with c2:
        st.markdown("**Particulars for the draft** (optional; stay out of logs)")
        name = st.text_input("Applicant name", "")
        age = st.text_input("Age", "")
        parent = st.text_input("Father's / mother's name", "")
        ps = st.text_input("Police station", "")
        fir = st.text_input("C.R. / FIR No.", "")
        case = st.text_input("Case No.", "")
        jail = st.text_input("Jail", "Yerawada Central Prison, Pune")
        court = st.text_input("Court", "the Court of the Judicial Magistrate First Class, Pune")
        lang = st.radio("Application language", ["en", "hi", "mr"], horizontal=True,
                        format_func=lambda k: {"en": "English", "hi": "हिंदी", "mr": "मराठी"}[k],
                        help="Statutory references stay in English in every language; the citation gate runs on all three.")
        use_model = st.checkbox("Let the model rewrite the prose (gated)", value=False, disabled=not llm.available(),
                                help="Only offered when a model is configured. Its text replaces the template only if the "
                                     "citation gate passes and every date, day count and section survives unchanged.")

    if st.button("Assess", type="primary"):
        charges = [Charge(*_split_charge(c)) for c in charges_txt.split(",") if c.strip()]
        p = Prisoner(charges=charges, custody_start=custody, first_time_offender=first, multiple_cases_pending=multi,
                     delay_attributable_days=int(delay), identifier=ident)
        a = assess(p, as_of=as_of)
        colour = {"ELIGIBLE": "green", "MUST_RELEASE_MAX_TERM": "green", "NOT_YET": "orange"}.get(a.status.value, "red")
        st.markdown(f"### :{colour}[{a.status.value}]")
        st.caption(STATUS_HELP[a.status.value])
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Controlling section", a.controlling.key if a.controlling else "-")
        m2.metric("Maximum term", f"{a.max_term_years:g} y" if a.max_term_years is not None else "-")
        m3.metric("Days served", a.days_served if a.days_served is not None else "-")
        m4.metric("Eligible from", a.eligible_on.strftime("%d %b %Y") if a.eligible_on else "-")
        for r in a.reasons:
            st.write("• " + r)
        if a.unverified:
            st.warning("Law-table rows used that are not yet verified against India Code: " + ", ".join(a.unverified))
        if a.eligible:
            part = Particulars(applicant_name=name or "________", applicant_age=age or "__", parent_name=parent or "________",
                               police_station=ps or "________", fir_no=fir or "____ of 20__", case_no=case or "____ of 20__",
                               jail=jail, court=court)
            d = draft(a, part, lang=lang)
            application = d["application"]
            g = d["gate"]
            if use_model:
                with st.spinner("Model rewriting the prose; gate checking it"):
                    pol = llm.polish(application, a, lang=lang)
                application = pol.text
                (st.info if pol.polished else st.warning)(pol.reason + (f" (missing: {', '.join(pol.missing_anchors)})" if pol.missing_anchors else ""))
                from rihai.gate import check as _gate_check
                g = _gate_check(application)
            st.markdown("#### Citation gate")
            (st.success if not g.blocked else st.error)(g.summary())
            with st.expander("Citations read"):
                st.table([{"act": c.act, "section": c.section, "as written": c.text, "ok": c.ok, "note": c.reason} for c in g.citations])
            st.markdown("#### DLSA / UTRC memo")
            st.code(d["memo"], language=None)
            st.markdown("#### Application (review before filing)")
            st.text_area("application", application, height=600, label_visibility="collapsed")
            st.download_button("Download application (.txt)", application, file_name=f"s479_application_{ident}_{lang}.txt")
        else:
            part = Particulars(jail=jail, court=court)
            st.markdown("#### DLSA / UTRC memo")
            st.code(draft(a, part)["memo"], language=None)

with tab2:
    st.markdown("Upload a roster CSV with columns: `identifier, charges, custody_start, first_time_offender, multiple_cases_pending, delay_attributable_days`. "
                "`charges` is `;`-separated, e.g. `BNS 303(2);IPC/411`. Dates ISO. No names.")
    sample = ROOT / "data" / "samples" / "roster_sample.csv"
    if sample.exists():
        st.download_button("Download the sample roster", sample.read_bytes(), file_name="roster_sample.csv")
    up = st.file_uploader("Roster CSV", type=["csv"])
    as_of2 = st.date_input("Assess as on ", date.today(), key="asof2")
    if up is not None or st.button("Run on the sample roster"):
        df = pd.read_csv(up if up is not None else sample)
        rows = []
        for _, r in df.iterrows():
            rows.append({
                "identifier": str(r.get("identifier", "")),
                "charges": [c.strip() for c in str(r.get("charges", "")).split(";") if c.strip()],
                "custody_start": str(r.get("custody_start", "")),
                "first_time_offender": str(r.get("first_time_offender", "")).strip().lower() in ("1", "true", "yes", "y"),
                "multiple_cases_pending": str(r.get("multiple_cases_pending", "")).strip().lower() in ("1", "true", "yes", "y"),
                "delay_attributable_days": int(r.get("delay_attributable_days", 0) or 0),
            })
        out = assess_roster(rows, as_of=as_of2)
        res = pd.DataFrame([{
            "identifier": a.prisoner.identifier, "status": a.status.value,
            "controlling": a.controlling.key if a.controlling else "", "max_years": a.max_term_years,
            "first_time": a.prisoner.first_time_offender, "days_served": a.days_served,
            "eligible_on": a.eligible_on.isoformat() if a.eligible_on else "",
            "release_mode": a.release_mode or "", "reason": a.reasons[0] if a.reasons else "",
        } for a in out])
        counts = res["status"].value_counts().to_dict()
        st.markdown("**Summary:** " + " · ".join(f"{k} {v}" for k, v in counts.items()))
        st.dataframe(res, width='stretch', hide_index=True)
        st.download_button("Download results (.csv)", res.to_csv(index=False), file_name="rihai_results.csv")
        elig = [a for a in out if a.eligible]
        if elig:
            st.markdown(f"**{len(elig)} prisoner(s) eligible** - memos for the DLSA list:")
            st.code("\n\n".join(draft(a, Particulars())["memo"] for a in elig), language=None)

with tab3:
    s = stats()
    st.markdown(f"**{s['rows']} rows** · {s['verified']} verified against India Code · {s['excluded_life_or_death']} carry death/life · "
                f"{s['umbrella']} umbrella sections · {s['unbounded']} with no stated ceiling")
    st.caption("Section titles and the IPC/BNS mapping come from the GSMS-B concordance (CC-BY-4.0). Maximum terms are encoded "
               "from the statute text and flagged unverified until a reviewer checks them against the official text; the engine "
               "refuses unknown sections and marks unverified ones.")
    tdf = pd.DataFrame([r.to_dict() for r in all_rows().values()])
    q = st.text_input("Filter (act, section or title)", "")
    if q:
        m = tdf.apply(lambda row: q.lower() in f"{row['act']} {row['section']} {row['title']}".lower(), axis=1)
        tdf = tdf[m]
    st.dataframe(tdf[["act", "section", "title", "max_years", "min_years", "life", "death", "life_if", "umbrella", "verified", "notes"]],
                 width='stretch', hide_index=True, height=600)

