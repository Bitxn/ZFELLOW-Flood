"""
Google Form auto-filler: one file, standard library only.
Edit the CONFIG section, then press Run in VS Code.
"""

import os
import json
import time
import re
import sys
import difflib
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

# ============================ CONFIG ============================
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeKZ2LFKJFxACeeBN9WXA-lAaT6BelMCSjzD4lb5waJqNadyA/viewform"

# Same order and same length. Question text doesn't have to match exactly
# (case, spacing and a trailing "*" are ignored, and close matches are accepted).
QUESTIONS = [
    # ---------- Page 1 ----------
    "Email",                                                                            # 1
    "First Name",                                                                       # 2
    "Last Name",                                                                        # 3
    "Company or project name",                                                          # 4
    "Birthday",                                                                         # 5
    "Phone Number",                                                                     # 6
    "Are you technical?",                                                               # 7
    "Have you previously applied to Z Fellows?",                                        # 8
    "Where are you based?",                                                             # 9
    "Are you in school or working? Or both? Where at?",                                 # 10
    "What is the project that you are currently working on or would like to pursue? Why? (Max: 500 characters - about 100 words)",  # 11
    "What problem are you solving? (Max: 500 characters - about 100 words)",            # 12
    "What expertise do you have to execute on the work that you want to do? (Max: 500 characters - about 100 words)",               # 13
    "Who are your competitors and what do you understand about your idea that they don't? (Max: 500 characters - about 100 words)",  # 14
    "What have you worked on in the past? (Max: 500 characters - about 100 words)",     # 15
    "What's the nerdiest thing about you? (Max: 250 characters - about 50 words)",      # 16
    "What drives you? (Max: 250 characters - about 50 words)",                          # 17
    "What non-traditional things were you doing growing up?",                           # 18
    "Tell us about a risk youʼve taken or a challenge you've faced. Tell us whether you failed or succeeded, how you behaved, and how you think this reflects your character. (Max: 500 characters - about 100 words)",  # 19
    "Personal and/or Project Website and/or Links about you",                           # 20
    "Please list or describe any achievements and prizes.",                             # 21
    "Please include a 1 minute video of yourself with a short introduction on your background, something impressive about yourself (i.e. brag :)), and what project you're working on today. (Optional)",  # 22
    "Who would you co-found a company with if you could pick anyone in your network? In other words, who is someone un-recruitable you would want to hire regardless?",  # 23
    "How did you hear about Z Fellows?",                                                # 24
    "Optional: What's 1 thing you need help with? (Max: 500 characters - about 100 words)",  # 25

    # ---------- Page 2 (referrals) ----------
    "How this works: We'll email the person you refer to let them know you referred them and CC you on the email. Please refer smart friends, not cofounders or team members. We only need 1 application per team.",  # 26
    "Optional: Name of friend 1",                                                       # 27
    "Optional: Email of friend 1",                                                      # 28
    "Optional: Name of friend 2",                                                       # 29
    "Optional: Email of friend 2",                                                      # 30
    "Optional: Name of friend 3",                                                       # 31
    "Optional: Email of friend 3",                                                      # 32
]

ANSWERS = [
    # ---------- Page 1 ----------
    "bitandutta6345@gmail.com",                       # 1  Email
    "Bitan",                                          # 2  First Name
    "Dutta",                                          # 3  Last Name
    "OnePort",                                        # 4  Company or project name
    "2005-01-04",                                     # 5  Birthday (YYYY-MM-DD)
    "+919136072896",                                  # 6  Phone Number
    "Yes",                                            # 7  Are you technical?
    "Yes",                                            # 8  Previously applied?
    "Bangalore, India",                               # 9  Where are you based?

    # 10 School or working?
    "Both. I'm doing my undergrad at B.M.S. College of Engineering, Bengaluru, while building OnePort full-time, and the startup gets basically all my hours. I turned down a campus placement and a Product Engineer offer from a Bangalore AI startup to go all in on this.",

    # 11 Project + why (493 chars)
    "I'm building OnePort, a pre-ship safety gate for AI-written code. AI writes most startup code, but it leaks API keys, pulls in vulnerable packages and breaks things nobody reviewed. One command scans your changes and returns READY, INCONCLUSIVE or BLOCKED before anything ships. I started it after my own AI-written code broke in prod, then talked to 400+ devs with the same pain. As AI writes more of the world's code, someone will own the layer that decides what ships. I want that to be me.",

    # 12 Problem (unchanged, 492 chars)
    "AI writes most startup code now — fast, but unsafe. It leaks secrets, imports dependencies with known CVEs, and breaks things no human reviewed. Devs shipping the most AI code are the ones least able to catch what it gets wrong, and a single leaked key or shipped vulnerability can mean a breach or a dead product. There's no single gate that says \"safe to ship\" for AI-written code — so people eyeball it and pray, stitch together 5 noisy tools, or find out in production when it's too late.",

    # 13 Expertise (432 chars)
    "I built OnePort solo, end to end: CLI, Windows desktop app, 18 analysis tools, backend. In ~2 months: 227 users across 7 startups, ~150 weekly actives and ₹37,908 revenue in July, zero marketing. At NVIDIA (picked from 2,500+) I pre-trained a 1B-parameter LLM across 100+ GPUs with NeMo and Slurm. I was CTO of Numble.ai and have shipped software since I was 14. I build hard infra AND walk into startup offices to sell it myself.",

    # 14 Competitors (unchanged, 491 chars)
    "Snyk, Semgrep, Socket, GitGuardian — each solves one slice (SCA, SAST, secrets); GitHub's scanners flag but don't gate; AI review bots check style, not security. What they miss: they were built for code humans wrote and reviewed. AI code fails differently and at 10x the volume, and devs don't want 200 findings from 5 tools — they want ONE verdict: ship or don't. So I gate every commit locally, before a secret leaves the repo. Built for AI-native devs, not retrofitted enterprise tooling.",

    # 15 Past work (449 chars)
    "A) OnePort: pre-ship security for AI code. 227 users, 7 startups, ₹37,908 revenue in July 2026, solo and self-funded.\n"
    "B) NVIDIA intern: pre-trained a 1B-param LLM across 100+ GPUs.\n"
    "C) CTO, Numble.ai: astronomy AI on a fine-tuned 2B CodeLlama.\n"
    "D) TYP: fintech app that recovers failed UPI payments.\n"
    "E) YC S26 partner interview, a16z speedrun interview round, EF F26 Selection Hackathon (top 70 of 6,000).\n"
    "F) Smart India Hackathon national finalist.",

    # 16 Nerdiest thing (190 chars)
    "My hostel friends and I wired college microprocessors into a tiny homemade parallel compute unit, then trained a 211,406-parameter language model on it from scratch, just to see if we could.",

    # 17 What drives you (210 chars)
    "I missed IIT by a few thousand ranks and decided to build my own door instead. I'd rather fail at something huge than succeed at something small. Watching a stranger use what I built is the best feeling I know.",

    # 18 Non-traditional things growing up
    "I started coding at 9 on my dad's office laptop, which he could only bring home on Fridays, reading the source code in Inspect Element. By 10 I was building games and chat systems, by 12 I was winning local hackathons for my school, and from 14 to 16 I was freelancing, building websites and apps for startups and getting paid for it. While classmates chased marks, I chased shipping.",

    # 19 Risk / challenge (490 chars)
    "I had a guaranteed campus placement, the safe path every Indian engineering student is told to want, plus a Product Engineer offer from an AI startup. I turned both down to build OnePort full-time: self-funded, no co-founder, no safety net, funded by money I saved from my lunches. Family thought I was insane. I haven't won yet, I'm mid-fight, but I already won the hard part: I chose the risk over the comfortable path, and I'd do it again. That's the one thing you can't teach a founder.",

    # 20 Website / links
    "Personal site + proof: https://bitannet.netlify.app\n"
    "Evidence: https://bitannet.netlify.app/#evidence\n"
    "Product: https://oneport.co.in\n"
    "GitHub: https://github.com/Bitxn\n"
    "X: https://x.com/Oneport_\n"
    "LinkedIn: https://www.linkedin.com/in/bitan-dutta-4aa1bb2b2/",

    # 21 Achievements and prizes
    "• Y Combinator S26: partner interview for OnePort\n"
    "• a16z speedrun Alpha: advanced to interview round\n"
    "• Entrepreneur First F26: Selection Hackathon, top 70 of 6,000 applicants\n"
    "• South Park Commons: finalist\n"
    "• Smart India Hackathon: national finalist\n"
    "• NVIDIA internship: selected from 2,500+ applicants\n"
    "• 2x college hackathon winner\n"
    "• National Science Olympiad: Gold Medal\n"
    "• JEE Advanced AIR 19,447 · COMEDK AIR 2,008\n"
    "• OnePort: ₹37,908 revenue in July 2026, solo and self-funded",

    # 22 Video
    "https://youtu.be/bBZvbdsuxLo",

    # 23 Who would you co-found with
    "Paras, my Smart India Hackathon team lead. We've built under real deadline pressure together, he's sharp and dependable, and he's the person I'd most want beside me. He's committed to a job right now to pay student loans, which is exactly what makes him un-recruitable for the moment.",

    # 24 How did you hear about Z Fellows
    "Founder Twitter/X — I've followed Z Fellows and its alumni for a while, and kept seeing it recommended as the best fast-moving program for young technical founders.",

    # 25 What you need help with (315 chars)
    "Warm introductions to pre-seed investors and angels who back dev tools and security. As a solo founder in India with a small network, my hardest problem isn't building, it's getting into the room. I'd also love intros to engineering leaders at AI-native startups who feel this pain and could become design partners.",

    # ---------- Page 2 (referrals) ----------
    "I want to get in either Hook or by crook",        # 26 Acknowledgement  <-- CHECK THIS, see note below
    "",              # 27 Friend 1 name (optional)
    "",              # 28 Friend 1 email (optional)
    "",              # 29 Friend 2 name (optional)
    "",              # 30 Friend 2 email (optional)
    "",              # 31 Friend 3 name (optional)
    "",              # 32 Friend 3 email (optional)
]

# Google's built-in "Collect email addresses" box at the top of the form.
EMAIL = "bitandutta634@gmail.com"

PAGE_HISTORY = None         # only needed for branching forms, e.g. "0,2,3"

DRY_RUN = False             # True = show what would be sent, without submitting
ASK_BEFORE_SUBMIT = False   # True = asks y/n in the terminal before sending
# ================================================================

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"}

TYPE_NAMES = {0: "short answer", 1: "paragraph", 2: "multiple choice", 3: "dropdown",
              4: "checkboxes", 5: "linear scale", 7: "grid", 9: "date", 10: "time"}

SUCCESS_MARKERS = ("Thanks for applying", "Your response has been recorded",
                   "freebirdFormviewerViewResponseConfirmationMessage")


def norm(text):
    text = (text or "").lower().replace("*", " ")
    return re.sub(r"\s+", " ", text).strip()


def http(url, data=None):
    body = urllib.parse.urlencode(data, doseq=True).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=UA)
    if body:
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, resp.read().decode("utf-8", errors="replace"), resp.geturl()


def load_form(url):
    url = url.split("?")[0].split("#")[0].rstrip("/")
    url = re.sub(r"/(edit|viewform|formResponse)$", "", url)
    if "forms.gle" not in url:
        url += "/viewform"

    _, html, final_url = http(url)          # follows redirects (short links, /d/ -> /d/e/)
    final_url = re.sub(r"/viewform.*$", "/viewform", final_url.split("?")[0])

    m = re.search(r"FB_PUBLIC_LOAD_DATA_\s*=\s*(.*?);\s*</script>", html, re.S)
    if not m:
        if "accounts.google.com" in final_url:
            sys.exit("This form requires Google sign-in, so it can't be submitted from a script.")
        sys.exit("Couldn't read the form. Check that FORM_URL is the public 'viewform' link.")
    data = json.loads(m.group(1))

    fbzx = re.search(r'name="fbzx" value="([^"]+)"', html)
    items = data[1][1] or []

    questions, pages = [], 0
    for item in items:
        if not item:
            continue
        qtype = item[3]
        if qtype == 8:                      # page break / new section
            pages += 1
            continue
        if len(item) < 5 or not item[4]:    # titles, images, videos: nothing to answer
            continue
        questions.append({
            "title": item[1] or "",
            "type": qtype,
            "fields": item[4],              # grids have one field per row
        })

    return {
        "submit_url": final_url.replace("/viewform", "/formResponse"),
        "questions": questions,
        "pages": pages,
        "fbzx": fbzx.group(1) if fbzx else None,
        "title": (data[1][8] if len(data[1]) > 8 else "") or "",
    }


def match_question(qtext, form_questions):
    target = norm(qtext)
    by_norm = {norm(q["title"]): q for q in form_questions}
    if target in by_norm:
        return by_norm[target]
    close = difflib.get_close_matches(target, by_norm.keys(), n=1, cutoff=0.75)
    return by_norm[close[0]] if close else None


def add_answer(payload, q, answer):
    qtype, fields = q["type"], q["fields"]
    entry = f"entry.{fields[0][0]}"

    if qtype == 9:      # date: "YYYY-MM-DD"
        y, mo, d = str(answer).split("-")
        payload[f"{entry}_year"], payload[f"{entry}_month"], payload[f"{entry}_day"] = y, mo, d
    elif qtype == 10:   # time: "HH:MM"
        h, mi = str(answer).split(":")
        payload[f"{entry}_hour"], payload[f"{entry}_minute"] = h, mi
    elif qtype == 7:    # grid: answer is a list, one value per row
        rows = answer if isinstance(answer, list) else [answer]
        for field, val in zip(fields, rows):
            payload[f"entry.{field[0]}"] = val
    elif isinstance(answer, list):   # checkboxes
        payload[entry] = [str(a) for a in answer]
    else:
        payload[entry] = str(answer)

    # Warn when a choice answer isn't one of the form's options
    options = [o[0] for o in (fields[0][1] or []) if o and o[0]] if len(fields[0]) > 1 else []
    if options and qtype in (2, 3, 4) and answer not in ("", []):
        given = answer if isinstance(answer, list) else [answer]
        bad = [a for a in given if str(a) not in options]
        if bad:
            print(f"   ⚠️  {bad} is not an option. Valid options: {options}")


def main():
    if len(QUESTIONS) != len(ANSWERS):
        sys.exit(
            f"QUESTIONS has {len(QUESTIONS)} items and "
            f"ANSWERS has {len(ANSWERS)}. They must be the same length."
        )

    # Refuse to submit while any [placeholder] is left
    for i, a in enumerate(ANSWERS, 1):
        vals = a if isinstance(a, list) else [a]
        if any("[" in str(v) for v in vals):
            sys.exit(
                f"❌ Answer #{i} still has a [placeholder]. "
                "Fill it in before submitting."
            )

    attempt = 1

    try:
        while True:
            print("\n" + "=" * 60)
            print(f"🔄 Attempt #{attempt}")
            print("=" * 60)

            try:
                print("🔄 Loading form...")
                form = load_form(FORM_URL)

                print(
                    f"📝 {form['title'] or 'Untitled form'}: "
                    f"{len(form['questions'])} questions, "
                    f"{form['pages'] + 1} page(s)\n"
                )

                payload, used = {}, set()

                for qtext, ans in zip(QUESTIONS, ANSWERS):
                    q = match_question(qtext, form["questions"])

                    if not q:
                        print(f"❌ No match for: \"{qtext}\"")
                        continue

                    used.add(id(q))

                    print(
                        f"✅ \"{qtext[:70]}\" "
                        f"[{TYPE_NAMES.get(q['type'], q['type'])}] "
                        f"= {str(ans)[:60]}"
                    )

                    add_answer(payload, q, ans)

                unanswered = [
                    q["title"]
                    for q in form["questions"]
                    if id(q) not in used
                ]

                if unanswered:
                    print(
                        "\nℹ️ Form questions you didn't answer "
                        "(required ones may make submission fail):"
                    )
                    for title in unanswered:
                        print(f"   - {title}")

                if EMAIL:
                    payload["emailAddress"] = EMAIL

                payload["fvv"] = "1"
                payload["pageHistory"] = (
                    PAGE_HISTORY
                    or ",".join(str(i) for i in range(form["pages"] + 1))
                )

                if form["fbzx"]:
                    payload["fbzx"] = form["fbzx"]
                    payload["partialResponse"] = json.dumps(
                        [None, None, form["fbzx"]]
                    )

                if DRY_RUN:
                    print("\n🧪 DRY RUN. Payload:")
                    print(
                        json.dumps(
                            payload,
                            indent=2,
                            ensure_ascii=False
                        )
                    )
                    return

                if ASK_BEFORE_SUBMIT:
                    answer = input("\nSubmit now? (y/n): ").strip().lower()
                    if answer != "y":
                        print("Cancelled.")
                        return

                print("\n🚀 Submitting...")

                try:
                    status, html, _ = http(
                        form["submit_url"],
                        payload
                    )
                except urllib.error.HTTPError as e:
                    status = e.code
                    html = e.read().decode(
                        "utf-8",
                        errors="replace"
                    )

                out_file = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "form_response.html"
                )

                with open(
                    out_file,
                    "w",
                    encoding="utf-8"
                ) as f:
                    f.write(html)

                if any(
                    marker in html
                    for marker in SUCCESS_MARKERS
                ):
                    print(
                        "🎉 Submission succeeded. "
                        "No duplicate submission will be created."
                    )
                    

                print(
                    f"❌ Submission failed (HTTP {status})."
                )

                msgs = set(
                    re.findall(
                        r"(This is a required question|"
                        r"Over \d+ characters|"
                        r"Must be [^<\"]{1,80}|"
                        r"Please enter [^<\"]{1,80}|"
                        r"[^<>\\\"]{0,40}valid email[^<>\\\"]{0,40})",
                        html
                    )
                )

                for msg in msgs or ["(no specific error found)"]:
                    print("   -", msg)

                print(
                    f"Full reply saved to: {out_file}"
                )

                print(
                    "\n⏳ Retrying in 7 seconds..."
                )
                time.sleep(7)

                attempt += 1

            except Exception as e:
                print(
                    f"\n⚠️ Error during attempt #{attempt}: {e}"
                )
                print("⏳ Retrying in 7 seconds...")
                time.sleep(7)
                attempt += 1

    except KeyboardInterrupt:
        print(
            "\n\n🛑 Stopped by Ctrl+C."
        )
        print(
            f"Total attempts made: {attempt}"
        )


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()