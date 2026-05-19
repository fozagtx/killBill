# Demo Video Script — 3 minutes

Track: **Fintech** · Targets: Best Demo ($200), Best Startup Idea (PearVC interview)

> Hook the judge in the first 10 seconds, prove the agent does real work in the middle, and land the headline number at the end.

---

## 0:00–0:20 — Hook (talking head, no screen yet)

> "The average American spends $273 a month on subscriptions — and forgets about 40% of them. Banks won't tell you which ones to kill. So I built an agent that will. It reads your bank statement, decides what's overpriced, and drafts the cancellation emails for you."

(Cut to title card: **Subscription Killer · built on Jac**)

---

## 0:20–0:50 — Upload and kick off the agent

(Screen recording)

1. Show `samples/statement_001.csv` open briefly — "12 months, 331 transactions, all fictional."
2. Open the web UI at `http://127.0.0.1:5173`.
3. Drag the CSV onto the drop zone.
4. The progress bar starts. The agent-log on screen shows lines like:
   > `> uploaded statement_001.csv (332 lines)`
   > `> planning audit...`
   > `> agent analyzing: Netflix ($22.99/mo)`
   > `> agent analyzing: Hulu ($17.99/mo)`

(Voiceover while it runs)
> "Behind the scenes, a Jac walker hands each detected charge to a byLLM agent that decides *itself* which tools to call — merchant enricher, value judge, alternative finder, email drafter. No hardcoded pipeline."

---

## 0:50–2:00 — The agent's reasoning (the meat)

Once the report appears, scroll through it:

1. **CANCEL: Planet Fitness — $24.99/mo**
   > "Charged for 8 months — and look, the reason is specific: 'no adjacent fitness-related spend.' The agent looked at the *rest* of the statement to decide that."

2. **CANCEL: Audible — $14.95/mo**
   > "Same deal. Twelve months of Audible, zero Amazon book purchases. Cancel."

3. **DOWNGRADE: Hulu — $17.99/mo**
   > "Note the reason — 'You already pay for Netflix Premium.' That's the agent reading the entire subscription portfolio, not just one charge in isolation."

4. **DOWNGRADE: Adobe Creative Cloud — $54.99 → Canva Pro $12.99**
   > "It found the cheaper alternative."

5. Click the "show drafted cancellation email →" disclosure on Planet Fitness.
   > "And the email is already written. Subject, body, where to send it. Copy, paste, done."

---

## 2:00–2:40 — The headline reveal

Scroll back up to the hero:

> "Bottom line: this person could save **\$XX a month, \$XXX a year**. (Big number animates up on screen.) That's a vacation — and they didn't have to do anything except drop a CSV."

(Optional: hover the verdict badges — show that the agent decided 5 CANCEL, 3 DOWNGRADE, 5 KEEP.)

---

## 2:40–3:00 — What's next / close

> "Built on Jac and byLLM in 16 hours for JacHacks Spring. Next steps: Plaid integration so users don't upload CSVs, and a one-click 'cancel for me' that actually sends the email through a service like DoNotPay's API. The agent is the differentiator — it doesn't just find subscriptions, it tells you *why* each one is wasteful, with reasoning that references the rest of your spending."

(End card: GitHub link + "Subscription Killer · Jac + byLLM")

---

## Filming checklist

- [ ] Record at 1080p, 30fps, screen-record the browser at native resolution.
- [ ] Two terminals visible (briefly) — one running `jac serve audit.jac`, one running `python3 -m http.server 5173`.
- [ ] Use **Featherless.AI** with `Qwen2.5-14B-Instruct` (default) for the recording — fast enough (~5s/tool-call) and unlocks the **Best Use of Featherless.AI** sponsor prize. Mention "powered by Featherless.AI" once on camera. If the 14B model mislabels Planet Fitness (occasional), bump to 72B via `export SUBKILLER_MODEL=openai/Qwen/Qwen2.5-72B-Instruct` and rely on the UI's cached JSON fallback.
- [ ] Pre-script the headline number — know exactly what total your sample produces so you can reference it confidently on the voiceover.
- [ ] Talk over the wait — never let the video go silent while the agent thinks.

## Closer-look shots (B-roll)

- Show `audit.jac` line 129 (`def analyze_one_subscription ... by llm(tools=[...])`) with a brief highlight — "this one call is the agent."
- Show the persisted `__jac_gen__` graph if you've run it twice — "subscriptions persist across runs via Jac's root graph."
