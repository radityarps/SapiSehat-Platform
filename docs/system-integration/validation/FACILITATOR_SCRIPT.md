# Facilitator Script — Limited Field Validation

Use this script to run a consistent session with each participant. Text in
"quotes" can be read aloud. Adapt to Indonesian as needed (key phrases provided).

---

## 0. Before the participant arrives

- [ ] Validation build installed and opened to the splash/home screen.
- [ ] Smoke test passed (`apps/mobile/SMOKE_TEST_CHECKLIST.md`).
- [ ] Sample cattle images ready (healthy / FMD / LSD).
- [ ] If testing region visuals, prepare validation-only mockup labelled
      "model attention area" / "area to review". Do not call it lesion
      detection.
- [ ] Printed consent form, task checklist, metrics sheet, pen.
- [ ] Timer ready. Note-taking device ready.
- [ ] Decide online vs offline mode for the session and note it.

---

## 1. Welcome & consent (5 min)

> "Thank you for helping us. Today we are testing an app called SapiSehat that
> gives an **early indication** of cattle disease from a photo. We are testing
> the **app**, not you — there are no wrong answers. If something is confusing,
> that is useful information for us."

(ID) "Kami menguji aplikasinya, bukan Anda. Tidak ada jawaban yang salah."

- [ ] Walk through `CONSENT_FORM.md`. Answer questions.
- [ ] Obtain signature / verbal recorded consent.
- [ ] Remind: "You can stop at any time."

---

## 2. Background (3 min)

Record on `METRICS_SHEET.md`:
- Role (farmer / animal health officer / other)
- Years working with cattle
- Smartphone familiarity (low / medium / high)

---

## 3. Tasks (20–30 min) — think-aloud

> "Please tell me what you are thinking as you go. I will mostly stay quiet and
> watch. I will only step in if you are completely stuck."

For each task in `TASK_CHECKLIST.md`:
- [ ] Read the task prompt.
- [ ] Start the timer.
- [ ] Observe silently. Do NOT coach. Note hesitation/confusion.
- [ ] Stop the timer when the task is done or the participant gives up.
- [ ] If you must assist, mark "assistance required" and note what you said.

### Task prompts (read one at a time)

1. **Scan**: "Take a photo of this cow (or pick one from the gallery) and get a
   result."
2. **Interpret result**: "Looking at this screen, what does the app think, and
   how sure is it? What would you do next?"
3. **Disclaimer comprehension** (do not hint): "In your own words, what is this
   result telling you? Is it a final diagnosis?"
4. **Guide**: "Find information in the app about this disease (or about taking a
   good photo)."
5. **History**: "Find your previous scan. Add a short note to it. Then delete it."
6. **Settings/privacy**: "Find where you control whether your photo is uploaded
   to the server. Turn it off."
7. **PDF**: "Create a report you could share with a vet, and show me how you'd
   share it."

### Optional region visual probe (validation-only)

Only run this if the study plan includes issue #32. Show the participant a
mockup or disabled prototype state. Say:

> "This visual would mark a model attention area / area to review. It does not
> confirm a lesion and is not a veterinary diagnosis."

Ask:

1. "What do you think this marked area means?"
2. "Would this help you decide what to do next, or could it be misleading?"
3. "Does this make the result feel like a diagnosis? Why?"
4. "Which wording is clearest: model attention area, area to review, or another
   phrase?"

Record exact wording. Do not approve farmer-facing region UI unless participants
consistently understand it as review guidance, not confirmed disease evidence.

---

## 4. Comprehension check (5 min)

Ask the structured questions from `METRICS_SHEET.md` §Disclaimer Comprehension.
Record correct / partial / incorrect. Do not correct the participant until after
scoring; then you may clarify for their benefit.

---

## 5. Debrief (5 min)

Open questions (capture quotes):
- "What did you like most?"
- "What was confusing or frustrating?"
- "Would you trust this as a first check before calling a vet? Why / why not?"
- "Anything you expected the app to do that it didn't?"
- If region mockup was shown: "Should this kind of area marker be shown to
  farmers, kept only for developers/health officers, or not shown? Why?"

(Optional) Administer the 10-item SUS questionnaire.

---

## 6. Close

> "Thank you. To be clear, this app gives an early indication only — for any
> real concern, please consult a veterinarian."

- [ ] Collect materials. Confirm no PII left on device.
- [ ] Note any crash/error observed during the session on `METRICS_SHEET.md`.

---

## Facilitator rules

- Stay neutral. Don't lead ("Don't you think this button is nice?").
- Silence is fine. Let the participant struggle briefly before helping.
- Record exactly what happened, including your own interventions.
- If a crash occurs, note the screen, the action, and whether it recovered.
