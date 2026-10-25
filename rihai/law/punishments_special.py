"""Maximum punishments under the special and local Acts that account for a large share of undertrials.

Keyed as "<ACT>/<section>". Same field conventions as punishments_bns.py. Coverage is deliberately narrow: the
sections that recur in prison rosters. Everything else is UNKNOWN_SECTION until a reviewer adds it.

NDPS quantity thresholds matter: the same section carries 1 year for a small quantity and 20 years for a
commercial quantity. Charge-sheets usually record the quantity class; where they do not, the engine returns
NEEDS_REVIEW rather than guess.
"""

P = {}

def _(key, max_years=None, *, min_years=0, life=False, death=False, life_if=None, fine_only=False, umbrella=False,
      variants=None, notes=""):
    P[key] = dict(max_years=max_years, min_years=min_years, life=life, death=death, life_if=life_if, fine_only=fine_only,
                  umbrella=umbrella, variants=variants or [], notes=notes)

# ---- Narcotic Drugs and Psychotropic Substances Act, 1985
for sec, what in [("20", "cannabis"), ("21", "manufactured drugs and preparations"), ("22", "psychotropic substances"),
                  ("23", "import into, export from or transhipment through India"),
                  ("8/20", "cannabis (charged as s.8 r/w s.20)"), ("8/21", "manufactured drugs (s.8 r/w s.21)"), ("8/22", "psychotropic substances (s.8 r/w s.22)"),
                  ("8/23", "import or export (s.8 r/w s.23)")]:
    base = sec.replace("8/", "")
    _(f"NDPS/{sec}(small)", 1, notes=f"NDPS s.{base}, {what}, small quantity: RI up to 1 year, or fine up to 10,000, or both.")
    _(f"NDPS/{sec}(intermediate)", 10, notes=f"NDPS s.{base}, {what}, quantity between small and commercial: RI up to 10 years and fine up to 1 lakh.")
    _(f"NDPS/{sec}(commercial)", 20, min_years=10, notes=f"NDPS s.{base}, {what}, commercial quantity: RI 10 to 20 years and fine 1 to 2 lakh.")
    _(f"NDPS/{sec}", umbrella=True, variants=[f"NDPS/{sec}(small)", f"NDPS/{sec}(intermediate)", f"NDPS/{sec}(commercial)"],
      notes="Quantity class decides the maximum: small 1 yr, intermediate 10 yrs, commercial 20 yrs. Specify it.")
_("NDPS/15(small)", 1, notes="NDPS s.15, poppy straw, small quantity: RI up to 1 year, or fine up to 10,000, or both.")
_("NDPS/15(intermediate)", 10, notes="NDPS s.15, poppy straw, intermediate quantity: RI up to 10 years and fine up to 1 lakh.")
_("NDPS/15(commercial)", 20, min_years=10, notes="NDPS s.15, poppy straw, commercial quantity: RI 10 to 20 years and fine 1 to 2 lakh.")
_("NDPS/15", umbrella=True, variants=["NDPS/15(small)", "NDPS/15(intermediate)", "NDPS/15(commercial)"], notes="Specify quantity class.")
_("NDPS/18(small)", 1, notes="NDPS s.18, opium poppy and opium, small quantity: RI up to 1 year, or fine, or both.")
_("NDPS/18(intermediate)", 10, notes="NDPS s.18, intermediate quantity: RI up to 10 years and fine up to 1 lakh.")
_("NDPS/18(commercial)", 20, min_years=10, notes="NDPS s.18, commercial quantity: RI 10 to 20 years and fine 1 to 2 lakh.")
_("NDPS/18", umbrella=True, variants=["NDPS/18(small)", "NDPS/18(intermediate)", "NDPS/18(commercial)"], notes="Specify quantity class.")
_("NDPS/27", 1, notes="NDPS s.27, consumption: RI up to 1 year (cocaine, morphine, heroin etc.) or up to 6 months (other), or fine, or both. Max 1.")
_("NDPS/27A", 20, min_years=10, notes="NDPS s.27A, financing illicit traffic and harbouring offenders: RI 10 to 20 years and fine 1 to 2 lakh.")
_("NDPS/28", None, notes="NDPS s.28, attempt: punished as for the offence attempted - resolve against the principal section and quantity.")
_("NDPS/29", None, notes="NDPS s.29, abetment and criminal conspiracy: punished as for the offence - resolve against the principal section and quantity.")
_("NDPS/31A", 0, death=True, notes="NDPS s.31A, repeat offender, certain quantities: death (discretionary after 2014 amendment) - excluded.")

# ---- Arms Act, 1959
_("ARMS/25(1)", 7, min_years=3, notes="Arms Act s.25(1): manufacture, sale etc. of arms or ammunition without licence: 3 to 7 years and fine.")
_("ARMS/25(1A)", 14, min_years=7, notes="Arms Act s.25(1A): acquisition or possession of prohibited arms or ammunition: 7 to 14 years and fine.")
_("ARMS/25(1AA)", None, min_years=7, life=True, notes="Arms Act s.25(1AA): manufacture etc. of prohibited arms: not less than 7 years, may extend to life.")
_("ARMS/25(1B)", 3, min_years=1, notes="Arms Act s.25(1B): acquisition or possession of firearm without licence etc.: 1 to 3 years and fine.")
_("ARMS/25(8)", 10, notes="Arms Act s.25(8): use of firearm in celebratory gunfire endangering life: up to 2 years, or fine up to 1 lakh, or both. Reviewer to confirm.")
_("ARMS/25(9)", 10, min_years=10, life=True, notes="Arms Act s.25(9): organised crime syndicate involvement: not less than 10 years, may extend to life.")
_("ARMS/25", umbrella=True, variants=["ARMS/25(1)", "ARMS/25(1A)", "ARMS/25(1AA)", "ARMS/25(1B)"], notes="Specify sub-section.")
_("ARMS/26(1)", 7, min_years=0.5, notes="Arms Act s.26(1): secret contravention of ss.3, 4, 10 or 12: 6 months to 7 years and fine.")
_("ARMS/26(2)", 10, min_years=5, notes="Arms Act s.26(2): secret contravention of ss.5, 6, 7 or 11: 5 to 10 years and fine.")
_("ARMS/26(3)", 10, notes="Arms Act s.26(3): concealing arms or ammunition during a search under s.22: up to 10 years and fine.")
_("ARMS/26", umbrella=True, variants=["ARMS/26(1)", "ARMS/26(2)", "ARMS/26(3)"], notes="Specify sub-section: (1) up to 7 years, (2) up to 10, (3) up to 10.")
_("ARMS/27(1)", 7, min_years=3, notes="Arms Act s.27(1): using arms in contravention of s.5: 3 to 7 years and fine.")
_("ARMS/27(2)", 10, min_years=7, notes="Arms Act s.27(2): using prohibited arms in contravention of s.7: 7 to 10 years and fine.")
_("ARMS/27(3)", 0, death=True, life=True, notes="Arms Act s.27(3): use of prohibited arms resulting in death: death or life (death mandatory portion struck down in State of Punjab v Dalbir Singh, 2012).")
_("ARMS/27", umbrella=True, variants=["ARMS/27(1)", "ARMS/27(2)", "ARMS/27(3)"], notes="Specify sub-section.")
_("ARMS/30", 1, notes="Arms Act s.30: contravention of licence or rule: up to 1 year, or fine up to 2,000, or both. Reviewer to confirm.")

# ---- Protection of Children from Sexual Offences Act, 2012
_("POCSO/4", None, min_years=10, life=True, notes="POCSO s.4: penetrative sexual assault: not less than 10 years, may extend to life (20 years min if child under 16).")
_("POCSO/6", None, min_years=20, life=True, death=True, notes="POCSO s.6: aggravated penetrative sexual assault: RI not less than 20 years, may extend to life (natural life), or death.")
_("POCSO/3", None, min_years=10, life=True, notes="POCSO s.3 defines penetrative sexual assault; charge-sheets cite 3/4. Punishment is s.4: not less than 10 years, may extend to life.")
_("POCSO/5", None, min_years=20, life=True, death=True, notes="POCSO s.5 defines aggravated penetrative sexual assault; punishment is s.6: 20 years to life, or death.")
_("POCSO/7", 5, min_years=3, notes="POCSO s.7 defines sexual assault; charge-sheets cite 7/8. Punishment is s.8: 3 to 5 years and fine.")
_("POCSO/8", 5, min_years=3, notes="POCSO s.8: sexual assault: 3 to 5 years and fine.")
_("POCSO/9", 7, min_years=5, notes="POCSO s.9 defines aggravated sexual assault (clauses (a) to (v)); charge-sheets cite 9/10. Punishment is s.10: 5 to 7 years and fine.")
_("POCSO/9(m)", 7, min_years=5, notes="POCSO s.9(m): sexual assault on a child below twelve; punishment is s.10: 5 to 7 years and fine.")
_("POCSO/11", 3, notes="POCSO s.11 defines sexual harassment of a child; charge-sheets cite 11/12. Punishment is s.12: up to 3 years and fine.")
_("POCSO/10", 7, min_years=5, notes="POCSO s.10: aggravated sexual assault: 5 to 7 years and fine.")
_("POCSO/12", 3, notes="POCSO s.12: sexual harassment of a child: up to 3 years and fine.")
_("POCSO/14", 7, min_years=5, notes="POCSO s.14: using child for pornographic purposes: not less than 5 years (first conviction) / 7 (subsequent) and fine. Reviewer to confirm limb.")
_("POCSO/15", 5, notes="POCSO s.15: storage of pornographic material involving child: up to 3 / 5 years depending on sub-section. Max 5.")
_("POCSO/17", None, notes="POCSO s.17: abetment: punished as for the offence - resolve against the principal section.")
_("POCSO/18", None, notes="POCSO s.18: attempt: up to one-half of the longest term - resolve against the principal section.")

# ---- Maharashtra Prohibition Act, 1949 (Bombay Prohibition Act) - common in Pune / Yerawada rosters
_("MPA/65", 5, notes="Maharashtra Prohibition Act s.65: manufacture, sale, transport etc. of liquor: up to 5 years and fine (s.65(e) possession/transport). Reviewer to confirm clause.")
_("MPA/66", 3, notes="Maharashtra Prohibition Act s.66(1)(b): consumption of liquor without permit: up to 6 months and fine (first). Reviewer to confirm.")
_("MPA/83", 1, notes="Maharashtra Prohibition Act s.83: tampering etc. Reviewer to confirm.")

# ---- Maharashtra Control of Organised Crime Act, 1999
_("MCOCA/3(1)", 0, life=True, death=True, notes="MCOCA s.3(1)(i): organised crime resulting in death: death or life. Excluded.")
_("MCOCA/3(1)(ii)", None, min_years=5, life=True, notes="MCOCA s.3(1)(ii): organised crime, other cases: not less than 5 years, may extend to life. Excluded.")
_("MCOCA/3(2)", None, min_years=5, life=True, notes="MCOCA s.3(2): conspiracy / abetment / facilitation: not less than 5 years, may extend to life. Excluded.")
_("MCOCA/3(4)", None, min_years=5, life=True, notes="MCOCA s.3(4): member of organised crime syndicate: not less than 5 years, may extend to life. Excluded.")
_("MCOCA/3", umbrella=True, variants=["MCOCA/3(1)", "MCOCA/3(1)(ii)", "MCOCA/3(2)", "MCOCA/3(4)"], notes="All limbs carry life: excluded from s.479.")

# ---- Unlawful Activities (Prevention) Act, 1967 (most limbs excluded)
_("UAPA/13", 7, notes="UAPA s.13: unlawful activities: up to 7 years and fine.")
_("UAPA/16", 0, life=True, death=True, notes="UAPA s.16: terrorist act: death or life (if death results); else not less than 5 years, may extend to life. Excluded.")
_("UAPA/17", None, min_years=5, life=True, notes="UAPA s.17: raising funds for terrorist act: not less than 5 years, may extend to life. Excluded.")
_("UAPA/18", None, min_years=5, life=True, notes="UAPA s.18: conspiracy etc.: not less than 5 years, may extend to life. Excluded.")
_("UAPA/20", 0, life=True, notes="UAPA s.20: membership of terrorist gang or organisation: life and fine. Excluded.")
_("UAPA/38", 10, notes="UAPA s.38: membership of a terrorist organisation: up to 10 years, or fine, or both.")
_("UAPA/39", 10, notes="UAPA s.39: support to a terrorist organisation: up to 10 years, or fine, or both.")

# ---- Prevention of Money-Laundering Act, 2002
_("PMLA/3", 7, min_years=3, notes="PMLA s.3 defines money-laundering; complaints cite 3/4. Punishment is s.4: RI 3 to 7 years and fine (up to 10 where proceeds relate to NDPS offences).")
_("PMLA/4", 7, min_years=3, notes="PMLA s.4: money-laundering: RI 3 to 7 years and fine (up to 10 where proceeds relate to NDPS offences).")

# ---- Information Technology Act, 2000
_("IT/66", 3, notes="IT Act s.66: computer related offences: up to 3 years, or fine up to 5 lakh, or both.")
_("IT/66C", 3, notes="IT Act s.66C: identity theft: up to 3 years and fine up to 1 lakh.")
_("IT/66D", 3, notes="IT Act s.66D: cheating by personation using computer resource: up to 3 years and fine up to 1 lakh.")
_("IT/66E", 3, notes="IT Act s.66E: violation of privacy: up to 3 years, or fine up to 2 lakh, or both.")
_("IT/67", 5, notes="IT Act s.67: publishing obscene material in electronic form: first conviction up to 3 years and fine up to 5 lakh; subsequent up to 5 years. Max 5.")
_("IT/67A", 7, notes="IT Act s.67A: sexually explicit material: first conviction up to 5 years; subsequent up to 7. Max 7.")
_("IT/67B", 7, notes="IT Act s.67B: child sexual abuse material: first conviction up to 5 years; subsequent up to 7. Max 7.")

# ---- Scheduled Castes and Scheduled Tribes (Prevention of Atrocities) Act, 1989
_("SCST/3(1)", 5, min_years=0.5, notes="SC/ST Act s.3(1): atrocities listed in cl. (a)-(zc): 6 months to 5 years and fine.")
_("SCST/3(1)(r)", 5, min_years=0.5, notes="SC/ST Act s.3(1)(r): 6 months to 5 years and fine.")
_("SCST/3(1)(s)", 5, min_years=0.5, notes="SC/ST Act s.3(1)(s): 6 months to 5 years and fine.")
_("SCST/3(1)(u)", 5, min_years=0.5, notes="SC/ST Act s.3(1)(u): 6 months to 5 years and fine.")
_("SCST/3(1)(w)", 5, min_years=0.5, notes="SC/ST Act s.3(1)(w): 6 months to 5 years and fine.")
_("SCST/3(1)(w)(i)", 5, min_years=0.5, notes="SC/ST Act s.3(1)(w)(i): 6 months to 5 years and fine.")
_("SCST/3(1)(w)(ii)", 5, min_years=0.5, notes="SC/ST Act s.3(1)(w)(ii): 6 months to 5 years and fine.")
_("SCST/3(1)(za)", 5, min_years=0.5, notes="SC/ST Act s.3(1)(za): 6 months to 5 years and fine.")
_("SCST/3(1)(zc)", 5, min_years=0.5, notes="SC/ST Act s.3(1)(zc): 6 months to 5 years and fine.")
_("SCST/3(2)(v)", 0, life=True, notes="SC/ST Act s.3(2)(v): offence under IPC punishable with 10+ years committed against SC/ST member: life and fine. Excluded.")
_("SCST/3(2)(va)", None, notes="SC/ST Act s.3(2)(va): offences in the Schedule: punished as under IPC/BNS for that offence - resolve against the principal section.")
_("SCST/3", umbrella=True, variants=["SCST/3(1)", "SCST/3(2)(v)", "SCST/3(2)(va)"], notes="Specify clause.")

# ---- Dowry Prohibition Act, 1961
_("DPA/3", None, min_years=5, notes="Dowry Prohibition Act s.3: giving or taking dowry: not less than 5 years and fine not less than 15,000 - no ceiling stated. NEEDS_REVIEW.")
_("DPA/4", 2, min_years=0.5, notes="Dowry Prohibition Act s.4: demanding dowry: 6 months to 2 years and fine up to 10,000.")

# ---- Immoral Traffic (Prevention) Act, 1956
_("ITPA/3", 3, min_years=1, notes="ITPA s.3: keeping a brothel: first conviction RI 1 to 3 years and fine; subsequent 2 to 5. Reviewer to confirm limb.")
_("ITPA/4", 2, notes="ITPA s.4: living on the earnings of prostitution: up to 2 years, or fine up to 1,000, or both (7 to 10 if child/minor).")
_("ITPA/5", 7, min_years=3, notes="ITPA s.5: procuring, inducing or taking person for prostitution: RI 3 to 7 years and fine (7 to 14 if child; 7 to life if against will). Reviewer to confirm limb.")
_("ITPA/7", 0.25, notes="ITPA s.7: prostitution in or near public places: up to 3 months (up to 7 years... if child). Reviewer to confirm.")
_("ITPA/8", 0.5, notes="ITPA s.8: seducing or soliciting for prostitution: up to 6 months (first) / 1 year. Max 1.")

# ---- Essential Commodities Act, 1955
_("ECA/7", 7, min_years=3, notes="Essential Commodities Act s.7(1)(a)(ii): contravention of control order: 3 months to 7 years and fine. Max 7.")

# ---- Prevention of Corruption Act, 1988
_("PCA/7", 7, min_years=3, notes="PC Act s.7: public servant taking undue advantage: 3 to 7 years and fine.")
_("PCA/13", 10, min_years=4, notes="PC Act s.13: criminal misconduct by public servant: 4 to 10 years and fine.")
_("PCA/13(2)", 10, min_years=4, notes="PC Act s.13(2): punishment for criminal misconduct: 4 to 10 years and fine.")
_("PCA/13(1)(d)", 10, min_years=4, notes="PC Act s.13(1)(d) (pre-2018 text) defines criminal misconduct; charge-sheets cite 13(1)(d) r/w 13(2). Punishment is s.13(2): 4 to 10 years and fine.")

# ---- Motor Vehicles Act, 1988
_("MV/184", 1, notes="MV Act s.184: driving dangerously: first offence 6 months to 1 year, or fine, or both; subsequent up to 2 years. Max 1 (first).")
_("MV/185", 0.5, notes="MV Act s.185: driving by a drunken person: first offence up to 6 months, or fine up to 10,000, or both; subsequent up to 2 years.")
_("MV/187", 0.5, notes="MV Act s.187: offences relating to accident: first offence up to 6 months, or fine, or both.")

# ---- Electricity Act, 2003
_("ELEC/135", 3, notes="Electricity Act s.135: theft of electricity: up to 3 years, or fine, or both (first).")
_("ELEC/138", 3, notes="Electricity Act s.138: interference with meters: up to 3 years, or fine, or both.")

# ---- Wild Life (Protection) Act, 1972
_("WLPA/51", 7, min_years=3, notes="Wild Life (Protection) Act s.51: offences relating to Schedule I/II animals: 3 to 7 years and fine; other offences up to 3 years. Max 7.")

# ---- Explosive Substances Act, 1908
_("EXPL/3", 0, life=True, death=True, notes="Explosive Substances Act s.3: causing explosion likely to endanger life or property: death or life (if death results) / life or 10 years. Excluded.")
_("EXPL/4", 0, life=True, notes="Explosive Substances Act s.4: attempt to cause explosion / making or keeping explosive with intent: life or up to 10 years. Excluded.")
_("EXPL/5", 10, notes="Explosive Substances Act s.5: making or possessing explosives under suspicious circumstances: up to 10 years and fine.")

# ---- Public Gambling Act, 1867 / Maharashtra (Bombay) Prevention of Gambling Act, 1887
_("GAMB/3", 0.25, notes="Gambling Act s.3: keeping a common gaming house: up to 3 months, or fine, or both (state amendments vary - Maharashtra up to 2 years for repeat).")
_("GAMB/4", 1/12, notes="Gambling Act s.4: being found in a common gaming house: up to 1 month, or fine, or both.")
_("GAMB/12", 1/12, notes="Gambling Act s.12: gaming in public streets: up to 1 month, or fine up to 100, or both.")

# ---- Central Goods and Services Tax Act, 2017 (s.132 offences; arrests under s.69 fill economic-offence rosters)
_("CGST/132(1)(i)", 5, notes="CGST Act s.132(1)(i): tax evaded above Rs 5 crore: up to 5 years and fine.")
_("CGST/132(1)(ii)", 3, notes="CGST Act s.132(1)(ii): tax evaded Rs 2 to 5 crore: up to 3 years and fine.")
_("CGST/132(1)(iii)", 1, notes="CGST Act s.132(1)(iii): tax evaded Rs 1 to 2 crore: up to 1 year and fine.")
_("CGST/132(1)(iv)", 0.5, notes="CGST Act s.132(1)(iv): other offences in clauses (f), (g), (j): up to 6 months, or fine, or both.")
_("CGST/132", umbrella=True, variants=["CGST/132(1)(i)", "CGST/132(1)(ii)", "CGST/132(1)(iii)", "CGST/132(1)(iv)"], notes="Specify the clause: the ceiling depends on the amount of tax evaded.")
