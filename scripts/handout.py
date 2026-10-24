"""One-page handout for clinic and DLSA visits: English on page 1, Marathi on page 2, QR code to the live app.

    python scripts/handout.py --out Rihai_handout.pdf [--phone 98xxxxxxxx] [--url https://rihai-pune.streamlit.app]

Needs: pip install qrcode playwright  (and a Devanagari font on the machine, e.g. Noto Sans Devanagari or Mangal).
The phone number is never stored in the repository; pass it on the command line when you print.
"""
from __future__ import annotations

import argparse
import base64
import io
import tempfile
from pathlib import Path

CSS = """
@page { size: A4; margin: 16mm 16mm 14mm 16mm; }
* { box-sizing: border-box; }
body { font-family: "Noto Sans Devanagari", "Mangal", "Nirmala UI", "Public Sans", Arial, sans-serif; color: #1a1a1a; margin: 0; }
.page { page-break-after: always; font-size: 10.6pt; line-height: 1.42; }
.page:last-child { page-break-after: auto; }
h1 { font-size: 26pt; margin: 0 0 2mm 0; letter-spacing: 0.2px; }
h1 small { font-size: 12pt; font-weight: normal; color: #444; margin-left: 6px; }
.tag { color: #1f4e79; font-weight: bold; font-size: 12.5pt; margin: 0 0 1.5mm 0; }
.sub { color: #444; margin: 0 0 5mm 0; }
h2 { font-size: 12pt; color: #1f4e79; margin: 4.5mm 0 1.2mm 0; border-bottom: 1px solid #c9d6e2; padding-bottom: 0.8mm; }
p { margin: 0 0 2mm 0; }
ul { margin: 0 0 1.5mm 0; padding-left: 5mm; }
li { margin: 0 0 1mm 0; }
.grid { display: grid; grid-template-columns: 1fr 52mm; gap: 6mm; align-items: start; }
.qr { text-align: center; border: 1px solid #c9d6e2; border-radius: 3mm; padding: 3mm 2mm; }
.qr img { width: 40mm; height: 40mm; }
.qr .u { font-weight: bold; font-size: 9.4pt; white-space: nowrap; }
.qr .c { color: #444; font-size: 8.6pt; word-break: break-all; }
.box { background: #f3f6f9; border-radius: 3mm; padding: 3mm 4mm; margin-top: 2mm; }
.foot { margin-top: 5mm; border-top: 1px solid #c9d6e2; padding-top: 2mm; font-size: 9.6pt; color: #333; }
.num { font-weight: bold; }
"""

EN = """
<div class="page">
<h1>Rihai <small>रिहाई</small></h1>
<p class="tag">Who in the jail is already entitled to release under Section 479 BNSS?</p>
<p class="sub">A free, open-source tool for prison legal-aid clinics, DLSA secretaries and jail superintendents. Pune pilot, 2026.</p>

<div class="grid">
<div>
<h2>The problem</h2>
<p>India's prisons hold <span class="num">5.3 lakh</span> people; <span class="num">three in four</span> are undertrials (NCRB, Prison Statistics India 2023).
Section 479 of the Bharatiya Nagarik Suraksha Sanhita, 2023 says an undertrial <b>must</b> be released on bail after serving one-half of the
maximum sentence for the offence charged, a first-time offender on bond after one-third, and nobody may be held beyond the maximum term.
The Supreme Court has ordered every state to apply it proactively (<i>In Re: Inhuman Conditions in 1382 Prisons</i>, 2024).</p>
<p>Yet between July 2024 and April 2025 only <span class="num">334</span> undertrials were released under it in the whole country (Rajya Sabha, 3 April 2025).
Eligibility is checked by hand, jail by jail, once a quarter. The arithmetic is simple; nobody runs it continuously.</p>

<h2>What Rihai does</h2>
<ul>
<li>Takes a roster (charge sections, custody date, prior conviction yes/no) and computes who is eligible today, who becomes eligible on which date, and whose case needs a lawyer's look. Unknown sections are refused; nothing is guessed.</li>
<li>Drafts the Section 479 application and the DLSA/UTRC note in English, Hindi or Marathi, for counsel to review.</li>
<li>Checks every section cited in a draft against a law table of 757 entries (BNS, IPC, 17 special Acts).</li>
</ul>
</div>
<div class="qr">
<img src="data:image/png;base64,{QR}" alt="QR code">
<div class="u">{URL_SHORT}</div>
<div>Try it on any phone or laptop. A sample roster is built in.</div>
<div class="c">Code: github.com/SainathGaikwad/rihai</div>
</div>
</div>

<h2>What it does not do</h2>
<p>It files nothing, sends nothing and decides nothing. Legal-aid counsel reviews every draft; the court decides. No name leaves the clinic: the roster uses identifiers only, and real rosters never go on the internet.</p>

<div class="box">
<b>What we ask:</b> 30 minutes, and a list of cases with the names removed (charge sections, custody date, first-time or not).<br>
<b>What you get:</b> the eligibility list and the draft applications the same day, and the tool itself, free, for good (MIT licence). Your corrections go into the next version.
</div>

<div class="foot">
<b>Sainath Gaikwad</b>, Pune &nbsp;·&nbsp; gaikwadsainath738@gmail.com &nbsp;·&nbsp; Phone: {PHONE}<br>
Field visits: Pushkar (Indira College, Pune). Website: {URL} &nbsp;·&nbsp; Nothing in this leaflet is legal advice.
</div>
</div>
"""

MR = """
<div class="page">
<h1>रिहाई <small>Rihai</small></h1>
<p class="tag">कारागृहातील कोणते विचाराधीन कैदी (undertrial) कलम ४७९ BNSS नुसार आजच सुटकेस पात्र आहेत?</p>
<p class="sub">कारागृह विधी सहाय्य केंद्रे, जिल्हा विधी सेवा प्राधिकरण (DLSA) आणि कारागृह अधीक्षकांसाठी मोफत, मुक्त-स्रोत साधन. पुणे प्रायोगिक प्रकल्प, २०२६.</p>

<div class="grid">
<div>
<h2>समस्या</h2>
<p>भारतातील कारागृहांत <span class="num">५.३ लाख</span> लोक आहेत; त्यांपैकी <span class="num">चारपैकी तीन</span> विचाराधीन कैदी आहेत (NCRB, Prison Statistics India 2023).
भारतीय नागरिक सुरक्षा संहिता, २०२३ चे कलम ४७९ सांगते: आरोप असलेल्या गुन्ह्याच्या कमाल शिक्षेचा अर्धा काळ कोठडीत घालवल्यावर विचाराधीन कैद्याची जामिनावर सुटका झाली <b>पाहिजे</b>;
प्रथमच गुन्हा केलेल्याची एक-तृतीयांश काळानंतर जातमुचलक्यावर; आणि कोणालाही कमाल शिक्षेपेक्षा जास्त काळ कोठडीत ठेवता येत नाही.
सर्वोच्च न्यायालयाने प्रत्येक राज्याला हे कलम स्वतःहून लागू करण्याचे आदेश दिले आहेत (<i>In Re: Inhuman Conditions in 1382 Prisons</i>, २०२४).</p>
<p>तरीही जुलै २०२४ ते एप्रिल २०२५ या काळात देशभरात फक्त <span class="num">३३४</span> विचाराधीन कैद्यांची या कलमाखाली सुटका झाली (राज्यसभा, ३ एप्रिल २०२५).
पात्रता प्रत्येक कारागृहात हाताने, तिमाहीतून एकदा तपासली जाते. हिशेब सोपा आहे; तो सतत कोणीच करत नाही.</p>

<h2>रिहाई काय करते</h2>
<ul>
<li>कैद्यांची यादी (आरोपातील कलमे, कोठडीची तारीख, पूर्वी शिक्षा झाली आहे का) घेऊन आज कोण पात्र आहे, कोण कोणत्या तारखेला पात्र होईल आणि कोणाचे प्रकरण वकिलाने पाहावे हे ठरवते. अज्ञात कलम नाकारले जाते; काहीही अंदाजाने ठरवले जात नाही.</li>
<li>कलम ४७९ खालील अर्ज आणि DLSA/UTRC साठीची टिप्पणी मराठी, हिंदी किंवा इंग्रजीत तयार करते; वकिलांनी तपासण्यासाठी.</li>
<li>मसुद्यात आलेले प्रत्येक कलम कायद्याच्या तक्त्याशी (७५७ नोंदी: BNS, IPC, १७ विशेष कायदे) पडताळते.</li>
</ul>
</div>
<div class="qr">
<img src="data:image/png;base64,{QR}" alt="QR code">
<div class="u">{URL_SHORT}</div>
<div>कोणत्याही फोन किंवा लॅपटॉपवर वापरून पाहा. नमुना यादी आतच आहे.</div>
<div class="c">कोड: github.com/SainathGaikwad/rihai</div>
</div>
</div>

<h2>रिहाई काय करत नाही</h2>
<p>ती काहीही दाखल करत नाही, पाठवत नाही, ठरवत नाही. प्रत्येक मसुदा विधी सहाय्य वकील तपासतात; न्यायालय ठरवते. कोणाचेही नाव केंद्राबाहेर जात नाही: यादीत फक्त ओळख-क्रमांक असतात, आणि खऱ्या याद्या कधीही इंटरनेटवर जात नाहीत.</p>

<div class="box">
<b>आम्ही काय मागतो:</b> ३० मिनिटे, आणि नावे काढलेली प्रकरणांची यादी (आरोपातील कलमे, कोठडीची तारीख, प्रथमच गुन्हा आहे का).<br>
<b>तुम्हाला काय मिळते:</b> त्याच दिवशी पात्रतेची यादी आणि अर्जांचे मसुदे, आणि हे साधन कायमचे मोफत (MIT परवाना). तुमच्या दुरुस्त्या पुढील आवृत्तीत जातात.
</div>

<div class="foot">
<b>सैनाथ गायकवाड</b>, पुणे &nbsp;·&nbsp; gaikwadsainath738@gmail.com &nbsp;·&nbsp; फोन: {PHONE}<br>
भेटी: पुष्कर (इंदिरा कॉलेज, पुणे). संकेतस्थळ: {URL} &nbsp;·&nbsp; हे पत्रक कायदेशीर सल्ला नाही.
</div>
</div>
"""


def qr_png_b64(url: str) -> str:
    import qrcode  # type: ignore
    img = qrcode.make(url, box_size=8, border=1)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def build_html(url: str, phone: str) -> str:
    fill = {"{QR}": qr_png_b64(url), "{URL}": url, "{URL_SHORT}": url.replace("https://", ""), "{PHONE}": phone or "______________"}
    body = EN + MR
    for k, v in fill.items():
        body = body.replace(k, v)
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"


def to_pdf(html: str, out: Path) -> None:
    from playwright.sync_api import sync_playwright  # type: ignore
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "handout.html"
        src.write_text(html, encoding="utf-8")
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            pg.goto(src.as_uri())
            pg.wait_for_timeout(300)
            pg.pdf(path=str(out), format="A4", print_background=True, prefer_css_page_size=True)
            b.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="Rihai_handout.pdf")
    ap.add_argument("--url", default="https://rihai-pune.streamlit.app")
    ap.add_argument("--phone", default="", help="printed on the leaflet only; never stored in the repo")
    ap.add_argument("--html", action="store_true", help="also write the HTML next to the PDF")
    a = ap.parse_args()
    html = build_html(a.url, a.phone)
    out = Path(a.out)
    if a.html:
        out.with_suffix(".html").write_text(html, encoding="utf-8")
    to_pdf(html, out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
