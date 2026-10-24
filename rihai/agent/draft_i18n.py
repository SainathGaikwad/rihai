"""Hindi and Marathi templates for the Section 479 application.

Same structure as the English template in draft.py. Statutory references stay in English ("Section 479(1) of the
Bharatiya Nagarik Suraksha Sanhita, 2023"), which is how mixed-script applications are filed in Maharashtra's
courts and which keeps the citation gate working on every language. Numbers are Arabic numerals. Legal terms follow
district-court usage (Hindi: मुचलका for bond, जमानत for bail, अभिरक्षा for custody; Marathi: जातमुचलका, जामीन, कोठडी).

Every sentence that carries a figure takes it from the Assessment. A law-clinic reviewer checks the legal terms
before the first real filing; until then each draft carries the review line at the top.
"""
from __future__ import annotations

from datetime import date

from ..eligibility import Assessment, Status
from .draft import Particulars, SC_CASE, _charges_sentence, _d, _months_words, _years_words

REVIEW_LINE_HI = "[समीक्षा हेतु प्रारूप: किसी विधिक सहायता अधिवक्ता द्वारा जाँच के बाद ही दाखिल करें।]"
REVIEW_LINE_MR = "[पुनरावलोकनासाठी मसुदा: विधी सेवा वकिलांनी तपासल्यानंतरच दाखल करावा.]"

_ACT_HI = {"BNS": "भारतीय न्याय संहिता, 2023", "IPC": "भारतीय दंड संहिता, 1860"}
_ACT_MR = {"BNS": "भारतीय न्याय संहिता, 2023", "IPC": "भारतीय दंड संहिता, 1860"}


def _years_hi(y: float) -> str:
    if y is None:
        return "____"
    if y >= 1 and float(y).is_integer():
        n = int(y)
        return {1: "एक वर्ष", 2: "दो वर्ष", 3: "तीन वर्ष", 5: "पाँच वर्ष", 7: "सात वर्ष", 10: "दस वर्ष", 14: "चौदह वर्ष", 20: "बीस वर्ष"}.get(n, f"{n} वर्ष")
    m = round(y * 12)
    return f"{m} माह"


def _years_mr(y: float) -> str:
    if y is None:
        return "____"
    if y >= 1 and float(y).is_integer():
        n = int(y)
        return {1: "एक वर्ष", 2: "दोन वर्षे", 3: "तीन वर्षे", 5: "पाच वर्षे", 7: "सात वर्षे", 10: "दहा वर्षे", 14: "चौदा वर्षे", 20: "वीस वर्षे"}.get(n, f"{n} वर्षे")
    m = round(y * 12)
    return f"{m} महिने"


def _months(y: float, frac: float) -> int:
    return round(y * 12 * frac)


def _guard(a: Assessment):
    if a.status not in (Status.ELIGIBLE, Status.MUST_RELEASE_MAX_TERM):
        raise ValueError(f"no application is drafted for status {a.status.value}; reasons: {a.reasons}")


def application_hi(a: Assessment, p: Particulars) -> str:
    _guard(a)
    c = a.controlling
    first = a.prisoner.first_time_offender
    sec_c = c.section.split("/")[-1]
    act_en = {"BNS": "the Bharatiya Nyaya Sanhita, 2023", "IPC": "the Indian Penal Code, 1860"}.get(c.act, c.act)
    act_hi = _ACT_HI.get(c.act, c.act)

    if a.status == Status.MUST_RELEASE_MAX_TERM:
        heading = ("भारतीय नागरिक सुरक्षा संहिता, 2023 की धारा 479(1) के तृतीय परंतुक के अंतर्गत अधिकतम अवधि से अधिक निरुद्ध "
                   "विचाराधीन बंदी की रिहाई हेतु आवेदन")
        ground = (f"आवेदक दिनांक {_d(a.prisoner.custody_start)} से अभिरक्षा में है, अर्थात दिनांक {_d(a.as_of)} तक {a.days_served} दिन, "
                  f"जो Section {sec_c} of {act_en} ({act_hi}) के अपराध हेतु निर्धारित कारावास की अधिकतम अवधि {_years_hi(c.max_years)} के बराबर या उससे अधिक है। "
                  f"Section 479(1) of the Bharatiya Nagarik Suraksha Sanhita, 2023 के तृतीय परंतुक के अनुसार किसी भी विचाराधीन बंदी को अन्वेषण, "
                  f"जाँच या विचारण के दौरान उक्त अपराध हेतु उपबंधित कारावास की अधिकतम अवधि से अधिक समय तक निरुद्ध नहीं रखा जा सकता। "
                  f"अतः आवेदक का निरंतर निरोध विधि के प्राधिकार के बिना है।")
        prayer = "आवेदक को अभिरक्षा से तत्काल मुक्त करने का आदेश दें"
    elif first:
        heading = ("भारतीय नागरिक सुरक्षा संहिता, 2023 की धारा 479(1) के अंतर्गत प्रथम बार के अपराधी विचाराधीन बंदी को "
                   "मुचलके पर रिहा करने हेतु आवेदन")
        ground = (f"आवेदक प्रथम बार का अपराधी है जिसे पूर्व में किसी भी अपराध के लिए कभी दोषसिद्ध नहीं किया गया है। "
                  f"Section 479(1) of the Bharatiya Nagarik Suraksha Sanhita, 2023 के प्रथम परंतुक के अनुसार ऐसे व्यक्ति ने यदि उक्त अपराध हेतु "
                  f"निर्धारित कारावास की अधिकतम अवधि के एक-तिहाई तक निरोध भोग लिया है तो न्यायालय द्वारा उसे मुचलके पर रिहा किया जाएगा। "
                  f"{_years_hi(c.max_years)} का एक-तिहाई {_months(c.max_years, 1/3)} माह है, जो अवधि दिनांक {_d(a.eligible_on)} को पूर्ण हो चुकी है।")
        prayer = "आवेदक को Section 479(1) of the Bharatiya Nagarik Suraksha Sanhita, 2023 के प्रथम परंतुक के अंतर्गत मुचलके पर रिहा करें"
    else:
        heading = "भारतीय नागरिक सुरक्षा संहिता, 2023 की धारा 479(1) के अंतर्गत विचाराधीन बंदी को जमानत पर रिहा करने हेतु आवेदन"
        ground = (f"Section 479(1) of the Bharatiya Nagarik Suraksha Sanhita, 2023 के अनुसार जिस व्यक्ति ने उक्त अपराध हेतु निर्धारित कारावास की "
                  f"अधिकतम अवधि के आधे तक निरोध भोग लिया है उसे न्यायालय द्वारा जमानत पर रिहा किया जाएगा। "
                  f"{_years_hi(c.max_years)} का आधा {_months(c.max_years, 1/2)} माह है, जो अवधि दिनांक {_d(a.eligible_on)} को पूर्ण हो चुकी है।")
        prayer = "आवेदक को Section 479(1) of the Bharatiya Nagarik Suraksha Sanhita, 2023 के अंतर्गत जमानत पर रिहा करें"

    delay = (f", जिसमें Section 479(1) के स्पष्टीकरण के अनुसार आवेदक के कारण हुए विलंब के {a.prisoner.delay_attributable_days} दिन सम्मिलित नहीं हैं।"
             if a.prisoner.delay_attributable_days else "।")
    multi = ("आवेदक के विरुद्ध किसी अन्य अपराध या प्रकरण में कोई अन्वेषण, जाँच या विचारण लंबित नहीं है, अतः संहिता की Section 479(2) लागू नहीं होती।"
             if not a.prisoner.multiple_cases_pending else
             "[समीक्षा: अभिलेख में एक अन्य लंबित प्रकरण दर्ज है। Section 479(2) एक से अधिक प्रकरण लंबित होने पर उपधारा (1) के अंतर्गत रिहाई को वर्जित करती है; "
             "पुष्टि करें कि वह प्रकरण जीवित है। तृतीय परंतुक फिर भी लागू होता है।]")

    paras = [
        f"आवेदक {p.jail} में निरुद्ध विचाराधीन बंदी है, जो {p.police_station} थाने में पंजीकृत अपराध क्रमांक {p.fir_no} से उद्भूत "
        f"{p.case_type} क्रमांक {p.case_no} में {_charges_sentence(a)} के अंतर्गत दंडनीय अपराधों के लिए अभियुक्त है।",
        f"आवेदक को गिरफ्तार किया गया और वह दिनांक {_d(a.prisoner.custody_start)} से निरंतर अभिरक्षा में है। दिनांक {_d(a.as_of)} तक आवेदक "
        f"{a.days_served} दिन का निरोध भोग चुका है{delay}",
        f"Section {sec_c} of {act_en} ({act_hi}) का अपराध, जो आरोपित अपराधों में सबसे लंबी अधिकतम सजा वाला अपराध है, ऐसे कारावास से दंडनीय है "
        f"जिसकी अवधि {_years_hi(c.max_years)} तक हो सकती है। यह ऐसा अपराध नहीं है जिसके लिए मृत्युदंड या आजीवन कारावास को दंडों में से एक के रूप में "
        f"विनिर्दिष्ट किया गया हो।",
        ground,
        multi,
        f"माननीय सर्वोच्च न्यायालय ने {SC_CASE} में दिनांक 23.08.2024 एवं 22.10.2024 के आदेशों द्वारा सभी राज्यों एवं संघ राज्य क्षेत्रों को "
        f"निर्देश दिया है कि Section 479 सभी विचाराधीन बंदियों पर लागू की जाए तथा पात्र बंदियों की पहचान एवं रिहाई हेतु सक्रिय कदम उठाए जाएँ।",
        f"संहिता की Section 479(3) के अनुसार कारागार अधीक्षक का यह कर्तव्य है कि संबंधित अवधि पूर्ण होने पर वह आवेदक की रिहाई हेतु इस माननीय "
        f"न्यायालय में तत्काल लिखित आवेदन करे। यह आवेदन {p.filed_through} के माध्यम से प्रस्तुत किया जा रहा है ताकि आवेदक का वैधानिक अधिकार बिना "
        f"और विलंब के इस माननीय न्यायालय के समक्ष रखा जा सके।",
    ] + p.extra_facts
    body = "\n\n".join(f"{i}. {t}" for i, t in enumerate(paras, 1))

    return f"""{REVIEW_LINE_HI}

न्यायालय: {p.court}
{p.district}

आपराधिक विविध आवेदन क्रमांक ______ / {a.as_of.year}
में
{p.case_type} क्रमांक {p.case_no}
(अपराध क्रमांक {p.fir_no}, थाना {p.police_station})

{p.applicant_name}, आयु {p.applicant_age} वर्ष,
पिता/माता {p.parent_name},
वर्तमान में {p.jail} में निरुद्ध                                   ... आवेदक / अभियुक्त

बनाम

{p.state} राज्य
(थाना {p.police_station} द्वारा)                                   ... प्रत्यर्थी

{heading}

सविनय निवेदन है कि:

{body}

प्रार्थना

अतः इस माननीय न्यायालय से प्रार्थना है कि कृपया:

(क) {p.case_type} क्रमांक {p.case_no} में {prayer};

(ख) अधीक्षक, {p.jail} को निर्देश दें कि अनुपालन पर आवेदक को तत्काल रिहा किया जाए; तथा

(ग) न्यायहित में अन्य ऐसे आदेश पारित करें जो यह माननीय न्यायालय उचित समझे।

स्थान: {p.place}
दिनांक: {_d(a.as_of)}
                                                                  आवेदक
                                                                  द्वारा {p.filed_through}

सत्यापन

मैं, उपरोक्त आवेदक, सत्यनिष्ठा से कथन करता/करती हूँ कि उपरोक्त पैरा 1 से {len(paras)} की विषयवस्तु मेरी जानकारी एवं विश्वास के अनुसार सत्य है
तथा कोई भी तात्विक तथ्य छिपाया नहीं गया है।

स्थान: {p.place}
दिनांक: {_d(a.as_of)}                                               आवेदक
"""


def application_mr(a: Assessment, p: Particulars) -> str:
    _guard(a)
    c = a.controlling
    first = a.prisoner.first_time_offender
    sec_c = c.section.split("/")[-1]
    act_en = {"BNS": "the Bharatiya Nyaya Sanhita, 2023", "IPC": "the Indian Penal Code, 1860"}.get(c.act, c.act)
    act_mr = _ACT_MR.get(c.act, c.act)

    if a.status == Status.MUST_RELEASE_MAX_TERM:
        heading = ("भारतीय नागरिक सुरक्षा संहिता, 2023 च्या कलम 479(1) च्या तिसऱ्या परंतुकाखाली कमाल मुदतीपेक्षा अधिक काळ स्थानबद्ध "
                   "न्यायाधीन कैद्याच्या सुटकेसाठी अर्ज")
        ground = (f"अर्जदार दिनांक {_d(a.prisoner.custody_start)} पासून कोठडीत आहे, म्हणजे दिनांक {_d(a.as_of)} पर्यंत {a.days_served} दिवस, "
                  f"जे Section {sec_c} of {act_en} ({act_mr}) खालील गुन्ह्यासाठी विहित कारावासाच्या कमाल मुदतीइतके किंवा त्याहून अधिक आहे "
                  f"(कमाल मुदत {_years_mr(c.max_years)}). Section 479(1) of the Bharatiya Nagarik Suraksha Sanhita, 2023 च्या तिसऱ्या परंतुकानुसार "
                  f"कोणत्याही न्यायाधीन कैद्यास तपास, चौकशी किंवा खटल्याच्या कालावधीत सदर गुन्ह्यासाठी विहित कारावासाच्या कमाल मुदतीपेक्षा अधिक काळ "
                  f"स्थानबद्ध ठेवता येत नाही. त्यामुळे अर्जदाराची पुढील स्थानबद्धता कायद्याच्या अधिकाराशिवाय आहे.")
        prayer = "अर्जदारास कोठडीतून तात्काळ मुक्त करण्याचा आदेश द्यावा"
    elif first:
        heading = ("भारतीय नागरिक सुरक्षा संहिता, 2023 च्या कलम 479(1) खाली प्रथमच गुन्हा केलेल्या न्यायाधीन कैद्यास "
                   "जातमुचलक्यावर सोडण्यासाठी अर्ज")
        ground = (f"अर्जदार प्रथमच गुन्हा केलेला आरोपी असून त्यास यापूर्वी कोणत्याही गुन्ह्यात कधीही दोषी ठरविण्यात आलेले नाही. "
                  f"Section 479(1) of the Bharatiya Nagarik Suraksha Sanhita, 2023 च्या पहिल्या परंतुकानुसार अशा व्यक्तीने सदर गुन्ह्यासाठी विहित "
                  f"कारावासाच्या कमाल मुदतीच्या एक तृतीयांश इतका काळ स्थानबद्धता भोगली असल्यास न्यायालयाने त्यास जातमुचलक्यावर सोडावे. "
                  f"{_years_mr(c.max_years)} चा एक तृतीयांश म्हणजे {_months(c.max_years, 1/3)} महिने, ही मुदत दिनांक {_d(a.eligible_on)} रोजी पूर्ण झाली आहे.")
        prayer = "अर्जदारास Section 479(1) of the Bharatiya Nagarik Suraksha Sanhita, 2023 च्या पहिल्या परंतुकाखाली जातमुचलक्यावर सोडावे"
    else:
        heading = "भारतीय नागरिक सुरक्षा संहिता, 2023 च्या कलम 479(1) खाली न्यायाधीन कैद्यास जामिनावर सोडण्यासाठी अर्ज"
        ground = (f"Section 479(1) of the Bharatiya Nagarik Suraksha Sanhita, 2023 नुसार ज्या व्यक्तीने सदर गुन्ह्यासाठी विहित कारावासाच्या कमाल "
                  f"मुदतीच्या निम्मा काळ स्थानबद्धता भोगली आहे तिला न्यायालयाने जामिनावर सोडावे. {_years_mr(c.max_years)} चा निम्मा काळ म्हणजे "
                  f"{_months(c.max_years, 1/2)} महिने, ही मुदत दिनांक {_d(a.eligible_on)} रोजी पूर्ण झाली आहे.")
        prayer = "अर्जदारास Section 479(1) of the Bharatiya Nagarik Suraksha Sanhita, 2023 खाली जामिनावर सोडावे"

    delay = (f", ज्यात Section 479(1) च्या स्पष्टीकरणानुसार अर्जदारामुळे झालेल्या विलंबाचे {a.prisoner.delay_attributable_days} दिवस वगळले आहेत."
             if a.prisoner.delay_attributable_days else ".")
    multi = ("अर्जदाराविरुद्ध अन्य कोणत्याही गुन्ह्यात किंवा प्रकरणात तपास, चौकशी किंवा खटला प्रलंबित नाही, त्यामुळे संहितेचे Section 479(2) लागू होत नाही."
             if not a.prisoner.multiple_cases_pending else
             "[पुनरावलोकन: नोंदीत आणखी एक प्रलंबित प्रकरण दिसते. Section 479(2) एकाहून अधिक प्रकरणे प्रलंबित असल्यास उपकलम (1) खालील सुटकेस प्रतिबंध करते; "
             "ते प्रकरण चालू आहे का याची खात्री करावी. तिसरे परंतुक तरीही लागू होते.]")

    paras = [
        f"अर्जदार हा {p.jail} येथे स्थानबद्ध न्यायाधीन कैदी असून {p.police_station} पोलीस ठाण्यात नोंदलेल्या गु.र.नं. {p.fir_no} मधून उद्भवलेल्या "
        f"{p.case_type} क्र. {p.case_no} मध्ये {_charges_sentence(a)} खाली दंडनीय गुन्ह्यांसाठी आरोपी आहे.",
        f"अर्जदारास अटक झाली असून तो दिनांक {_d(a.prisoner.custody_start)} पासून सलग कोठडीत आहे. दिनांक {_d(a.as_of)} पर्यंत अर्जदाराने "
        f"{a.days_served} दिवसांची स्थानबद्धता भोगली आहे{delay}",
        f"Section {sec_c} of {act_en} ({act_mr}) खालील गुन्हा, जो आरोपित गुन्ह्यांपैकी सर्वाधिक कमाल शिक्षेचा गुन्हा आहे, तो "
        f"{_years_mr(c.max_years)} पर्यंत वाढविता येणाऱ्या कारावासाने दंडनीय आहे. हा असा गुन्हा नाही ज्यासाठी मृत्युदंड किंवा जन्मठेप ही शिक्षांपैकी "
        f"एक म्हणून विहित केलेली आहे.",
        ground,
        multi,
        f"मा. सर्वोच्च न्यायालयाने {SC_CASE} या प्रकरणात दिनांक 23.08.2024 व 22.10.2024 च्या आदेशांद्वारे सर्व राज्ये व केंद्रशासित प्रदेशांना "
        f"Section 479 सर्व न्यायाधीन कैद्यांना लागू करण्याचे व पात्र कैद्यांची ओळख व सुटका यासाठी सक्रिय पावले उचलण्याचे निर्देश दिले आहेत.",
        f"संहितेच्या Section 479(3) नुसार संबंधित मुदत पूर्ण झाल्यावर कारागृह अधीक्षकाने अर्जदाराच्या सुटकेसाठी या मा. न्यायालयाकडे तात्काळ लेखी "
        f"अर्ज करणे बंधनकारक आहे. अर्जदाराचा वैधानिक हक्क विनाविलंब या मा. न्यायालयासमोर ठेवता यावा म्हणून हा अर्ज {p.filed_through} यांच्यामार्फत "
        f"दाखल केला जात आहे.",
    ] + p.extra_facts
    body = "\n\n".join(f"{i}. {t}" for i, t in enumerate(paras, 1))

    return f"""{REVIEW_LINE_MR}

न्यायालय: {p.court}
{p.district}

फौजदारी किरकोळ अर्ज क्र. ______ / {a.as_of.year}
मध्ये
{p.case_type} क्र. {p.case_no}
(गु.र.नं. {p.fir_no}, {p.police_station} पोलीस ठाणे)

{p.applicant_name}, वय {p.applicant_age} वर्षे,
वडील/आई {p.parent_name},
सध्या {p.jail} येथे स्थानबद्ध                                   ... अर्जदार / आरोपी

विरुद्ध

{p.state} शासन
({p.police_station} पोलीस ठाण्यामार्फत)                           ... सामनेवाला

{heading}

सविनय निवेदन की:

{body}

विनंती

म्हणून या मा. न्यायालयास विनंती आहे की कृपया:

(अ) {p.case_type} क्र. {p.case_no} मध्ये {prayer};

(ब) अधीक्षक, {p.jail} यांना अनुपालनानंतर अर्जदारास तात्काळ मुक्त करण्याचे निर्देश द्यावेत; आणि

(क) न्यायाच्या हितासाठी या मा. न्यायालयास योग्य वाटतील असे अन्य आदेश द्यावेत.

ठिकाण: {p.place}
दिनांक: {_d(a.as_of)}
                                                                  अर्जदार
                                                                  तर्फे {p.filed_through}

पडताळणी

मी, वरील अर्जदार, प्रामाणिकपणे नमूद करतो/करते की वरील परिच्छेद 1 ते {len(paras)} मधील मजकूर माझ्या माहिती व समजुतीप्रमाणे खरा आहे
आणि कोणतीही महत्त्वाची बाब लपविलेली नाही.

ठिकाण: {p.place}
दिनांक: {_d(a.as_of)}                                               अर्जदार
"""
