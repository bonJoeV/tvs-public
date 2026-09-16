# The Vital Stretch, Momence Nurture Build Reference

Everything needed to build, extend, or rebuild the Twin Cities lead-nurture
system. Written to be self-contained: no console required.

---

## 1. The offer this is all built around

- **$29 intro = two 45-minute sessions.**
- The lead books **session 1** themselves.
- Staff books **session 2** at the end of session 1, at the desk.
- After session 2, the client either converts to a membership or does not.
- **Any booking after session 2 is the conversion signal.** Nobody books a
  third session and then declines to pay, so a post-intro booking = converted.

Every trigger and counter-condition below follows from those five facts.

---

## 2. Architecture: stages carry the flow

Momence has an **Update lead stage** action. Sequences chain by lead stage,
not by tags. A stage is visible on the Leads list; a tag is not, so front desk
can see where every lead sits without opening anything.

**The lead source is the router.** Each lead source (Apple Maps, Google, Meta,
Microsoft) has a **Default lead stage** set to that studio's Intro Nurture stage.
The stage lands at lead creation, before any sequence runs. So there is **no
router sequence**, the entry sequence just triggers on the Intro Nurture stage.

Stages per studio:
- **{STUDIO CODE} - Intro Nurture**, entry, set by the lead source (e.g. MTKA - Intro Nurture)
- **{STUDIO CODE} - Long Term**, the slow drip; every dead end drains here
- **{STUDIO CODE} - Not Interested**, where a "not now" reply lands
- **{STUDIO CODE} - No Show**, set by front desk on a missed first visit; triggers 40

Shared across Twin Cities:
- **TC - Unassigned**, entry for generic and manually created leads that have
  not selected a studio. It triggers the shared location-choice flow.

---

## 3. The twelve per-studio sequences

Naming: `{Code}-NN Descriptive name`. Code is the capitalized studio slug
(Mtka, Slp, Ep, Sav). Two-digit numbers give sort order; 00s = routing, 10s =
lead, 20s = long-term, 30s = pre-visit, 40s = no-show, 50s/60s = intro visits
and conversion, 70s/80s = member. Gaps are intentional so new sequences slot in
without renumbering.

Nine are the spine (10, 20, 30, 40, 50, 60, 65, 70, 80). Three supporting
sequences sit outside it: the intro booking email (31) and two retention saves
(82, 84). The shared unassigned-lead and abandoned-cart flows are market-wide,
not duplicated per studio.

| # | Name | Trigger | Enroll once | Counter conditions |
|---|------|---------|-------------|--------------------|
| 10 | New lead: book the $29 intro | Lead assigned new stage = {STUDIO CODE} - Intro Nurture | Yes | Appointment purchase, Appointment booking, Membership purchase (**all-time**) |
| 20 | Long-term: stay in touch until ready | Lead assigned new stage = {STUDIO CODE} - Long Term | Yes | same three, **after enrollment** |
| 30 | Before every visit: remind | Appointment visit, every visit, **On booking** | **No** | Appointment cancellation |
| 31 | Intro booking: prepare for visit 1 | Appointment visit, visit 1, **On booking** | Yes | none |
| 40 | No-show: one warm rescue | Lead assigned new stage = {STUDIO CODE} - No Show | Yes | Appointment booking, Appointment purchase, Membership purchase, **after enrollment** |
| 50 | After visit 1: recap and book visit 2 | Appointment visit, visit 1, **On check-in** | Yes | none on sequence; internal gate handles the nudge |
| 60 | After visit 2: make the offer | Appointment visit, visit 2, **On check-in** | Yes | Membership purchase, Appointment booking, **after enrollment** |
| 65 | New member: welcome, then review ask | Membership purchase | Yes | none available |
| 70 | Gone quiet: win the member back | Win-back trigger, active-membership gates at 14 + 28 days | Yes | Appointment booking, Membership purchase, **after enrollment** |
| 80 | Cancelled: one honest save attempt | Subscription cancellation | Yes | Membership purchase, **after enrollment** |
| 82 | Frozen: keep the pause from becoming an exit | Membership freeze | Yes | Membership purchase, Appointment booking, **after enrollment** |
| 84 | Lapsed: win back an expired membership | Membership expiration | Yes | Membership purchase, Appointment booking, **after enrollment** |

### Why each is separate or merged
- **10 absorbs the old Hot/Warm split.** One drip, one stage.
- **31 keeps first-visit preparation out of 30.** Sequence 30 repeats on every
  appointment, while the screening, intake form and intro image belong only to
  visit 1. Sequence 31 sends that email once, immediately after visit 1 is
  booked.
- **40 exists because 10 cannot absorb the no-show.** The tempting shortcut is
  to reset a missed lead to the Intro Nurture stage so 10 re-fires with a rescue
  text on top. It cannot work: 10 is enrolled-once, so a lead who already ran
  through is never enrolled again and the rescue silently never sends. A
  separate stage and sequence is the only version that fires. (If the native
  no-show trigger turns out to fire on appointment services, swap it in for the
  stage trigger.)
- **50 absorbs the old visit-2 nudge.** Recap email goes to everyone; a
  true/false gate on "Appointment booking since enrollment" decides whether the
  nudge text and task follow. Desk-bookers pass the gate and skip the nudge.
- **65 exists because 60 cannot hold the welcome.** A counter condition is an
  exit, not a step-level gate: the Membership purchase counter on 60 removes a
  convert from the sequence, so a welcome placed after it could never fire. 65
  has its own trigger, which also turns "when they book a third" and "two weeks
  after converting" into ordinary offsets of 1 and 14 days.
- **60 is now only the ask.** Two emails, a call task, and a drop to Long Term.
- **20 stays separate.** Different cadence, clean exit from the active drip. It
  is also the one sequence built as a **ladder**: Momence has no recurring
  scheduler, so "two emails a month" is not a thing you can build. 20 is 16
  fixed offsets across a year (day 7 through day 370), 12 emails and 4 texts,
  dense through the first quarter and thinning after. Only four pieces of copy
  exist, a value email, a proof email, an evergreen offer email and a check-in
  text; each is duplicated into its remaining slots with the body swapped.
- **Nothing in a sequence can be seasonal.** Steps fire on offsets from the
  moment a person enrolled, and people enroll continuously, so any given step
  lands in a different month for every lead. Sequence copy must be true in any
  month. **Seasonal pushes are broadcasts**, sent to a filtered list on the real
  date: late-December restart, March golf prep, June summer ramp, September back
  to routine, November gift cards. Five one-off sends a year, written the week
  they go out. Segmented list > Contact customers, filtered to the Long Term
  stage.
- **10 is deliberately kept short.** 7 emails and 4 texts over 22 days. Nine
  emails to a lead who never booked is a deliverability liability, and the two
  that were cut said nothing the rest did not: the old day 21 repeated day 6,
  and the old day 13 and day 15 were two proof sends 48 hours apart (now one
  merged email at day 13). The old day 18 text asked the identical question to
  day 3, so the late text slot is now the day 9 message moved to day 17.
- **80, 82 and 84 are the same shape** (one email, one call, drop to Long Term)
  on three different triggers, because Momence takes one trigger per sequence.
  Maintain them as one template with a changed opening line.

### Shared Twin Cities unassigned-lead flow

This replaces the unsafe per-studio catch-all. A lead with no stated location
cannot receive a studio stage without inventing intent, and four per-studio
catch-alls could race to assign four conflicting stages.

- **Trigger:** Lead assigned new stage = TC - Unassigned.
- **Association:** generic Twin Cities and manual lead sources only.
- **Enroll once:** Yes.
- **Counters:** Appointment booking, Appointment purchase and Membership
  purchase, all-time.
- **Actions:** location-choice SMS immediately, all-studio email after 5
  minutes, location-choice SMS day 2, and final all-studio email day 5.
- **Identity:** The Vital Stretch Twin Cities Team.

Both emails show booking links for Minnetonka, St Louis Park, Eden Prairie and
Savage. If the lead replies with a location, front desk sets that studio's Intro
Nurture stage. Studio-specific sources continue to enter their studio stage
directly.

### Shared Twin Cities abandoned-cart flow

This is one generic sequence for the whole market, not one sequence per studio.
The abandoned checkout does not establish a preferred studio, so its emails
show booking links for Minnetonka, St Louis Park, Eden Prairie and Savage.

- **Trigger:** New lead record created.
- **Association:** abandoned-checkout lead source only.
- **Enroll once:** Yes.
- **Counters:** Appointment booking, Appointment purchase and Membership
  purchase, all-time.
- **Actions:** SMS at 15 minutes, email day 1, SMS day 2, email day 3, SMS day
  4, email day 7, and the existing day-7 SMS left disabled.
- **Identity:** The Vital Stretch Twin Cities Team. No studio sender, address or
  phone is used because no location has been selected.

Do not associate the abandoned-checkout source with a studio router or studio
nurture sequence. That would enroll the same lead in overlapping flows before
they have chosen a location.

---

## 4. Critical Momence settings (learned the hard way)

- **On booking vs On check-in:** this is an enrollment option of the
  **Appointment visit** trigger, not a separate trigger. Sequence 30 uses
  Appointment visit enrolled **On booking**, the only setting that unlocks
  actions scheduled *before* the visit, which is what makes pre-visit reminders
  possible. Sequence 31 also uses **On booking**, limited to visit 1, for the
  intro booking email. Sequences 50 and 60 use Appointment visit enrolled **On
  check-in**, each set to a specific visit number (1 and 2).
- **Counter-condition timeframe is the single most dangerous setting in the
  build.** Every counter has an **All-time** vs **After customer is enrolled**
  toggle. **Sequence 10 and the two shared new-lead flows use all-time**, because
  these leads have no history, so any purchase or booking means they converted.
  Every other sequence targets somebody who already has a booking, purchase or
  membership behind them: a long-term lead who did both intro visits, a lapsing
  member, or a person who just cancelled the membership you are countering on.
  Set those to all-time and Momence enrolls them and ejects them in the
  same instant, sends nothing, and reports nothing. It is indistinguishable
  from a sequence nobody qualified for. Scope 20, 40, 60, 70, 80, 82 and 84
  **after enrollment**.
- **A counter condition is an exit, not a step-level gate.** It removes the
  person from the sequence; it does not skip one step and resume. Nothing that
  should happen *after* a conversion can live in a sequence that counters on
  conversion. Use a true/false condition when you want a fork; use a counter
  when you want someone gone.
- **"Optional: associate with specific"** on a counter condition: leave
  **blank**. Empty = any appointment/any membership counts, which is what you
  want. Filling it scopes to one service and silently misses conversions.
- **Enrollment once = Yes everywhere except 30.** Pre-visit fires on every
  appointment; everything else, a lead whose stage moves twice would get the
  whole drip twice.
- **Counter-condition types available:** Class purchase, Membership purchase,
  Appointment purchase, Appointment booking, Customer has tag. We never use
  Class purchase (we sell appointments, not classes).
- **True/false conditions available:** choices include Lead is already a
  customer, Customer has active membership, Lead has a stage assigned, Email
  opened, Email sent, and Link in email clicked. **Confirmed in the builder: a
  condition forks the flow into a True branch and a False branch**, not a
  single-step gate. A branch with no step ends there. Sequence 50 uses a
  terminal booking gate. Sequence 70 checks active membership at day 14,
  merges the two message branches, and checks current status again at day 28.
  AND/OR stacking is available.
- **Staff tasks** assign to the **Front Desk role**, never a named person, so
  they survive turnover. The assignment control is **Staff assignment mode**
  with four options (Select specific staff, By staff role, By staff location,
  Staff based on customer home location); use **By staff role**, then set
  **Staff role** to **Front desk**.
- **"Send new task and reminder emails" defaults to noise.** On means one email
  the instant the task is assigned *plus a second 24 hours later if nobody has
  marked it complete*, sent to everyone holding the assigned role. Ten task
  steps across four studios, two emails each, times headcount, is where a
  20-a-day inbox comes from. Leave it **off** everywhere except the day 0
  **NEW LEAD - call now** task, which is the only one measured in minutes. The
  lead's own day 0 SMS fires regardless, so an unseen task is not a silent lead.
- **Timing is two buttons, Immediately and Offset**, not a number that can be
  zero. A day 0 step uses **Immediately**. Everything else is Offset plus a
  number and a unit, and On booking additionally allows *before* the trigger.
- **"Trigger action even if lead is enrolled after the action"** is a checkbox
  under Timing. It makes an already-overdue step fire immediately rather than
  be skipped. **It can only matter in sequence 30**, the only sequence with
  steps scheduled *before* the trigger; everywhere else a step is an offset
  forward from enrollment, so its due moment is never in the past and the box
  is a no-op. Inside 30 it is per-step, not blanket:
  - **2-hour SMS: ticked.** A booking made inside two hours gets it at once and
    the wording still holds, since it says "later today" and names no clock time.
  - **24-hour email: unticked.** Its subject and first line both say *tomorrow*,
    so firing it at a same-day booker states the wrong day, which is worse than
    silence. Those people still get the Momence booking confirmation and the
    2-hour text. To change this, remove both uses of "tomorrow", then tick it.
- **Action type is a row of six buttons:** E-mail, SMS, Staff task, Add tags,
  Remove tags, Update lead stage. This build uses four and never tags.
- **Every action needs an Action name.** Each action (and each condition) has an
  internal **Action name** field plus an **Action enabled** toggle (leave on).
  The name never reaches the customer; keep it short and unique within the
  sequence, numbered in build order, e.g. `1. SMS - Day 0, immediately` or
  `Condition - Visit 2 booking gate`. The console's Copy tab generates one per
  step.
- **Uptime window:** 8 AM to 8 PM, one account setting. Anything triggered
  outside reschedules into the next window instead of texting at 2 AM.
- **Not used:** missed-call triggers (calls don't run through Momence).

---

## 5. SMS cost engineering (Twilio)

Twilio bills **per segment**. One segment = **160 characters** if every
character is GSM-7. A single non-GSM character (curly quote, curly apostrophe,
em dash, ellipsis, emoji) re-encodes the whole message to UCS-2 and drops the
limit to **70 characters**, tripling the cost.

Rules enforced in every text:
- **Type in a plain-text editor.** Never Word or Google Docs, both auto-insert
  curly quotes.
- **No em dashes, ever.** Use a hyphen or restructure.
- Every message verified GSM-7 clean and **one segment at worst case**: longest
  studio name + either sender name + a 12-character first name.
- **"Reply STOP to opt out"** on first-touch and recurring messages.

The worst-case check that matters: the day-0 text with the longest studio name
lands near 155 chars. Any edit needs a re-count.

### STOP handling (three layers)
1. **Carrier/Twilio, automatic:** STOP, UNSUBSCRIBE, END, QUIT, STOPALL,
   REVOKE, OPTOUT, CANCEL. Not "OPT OUT" with a space. STOP is permanent
   (error 21610), re-opt-in needs START/UNSTOP, and it **also blocks
   appointment reminders**, which is why confirmations are email.
2. **Momence, manual:** stop the sequence (Sequences > select > Customers >
   three dots > Stop running), and set the Not Interested stage.
3. **Plain English, human:** "stop texting," "remove me" etc. arrive as normal
   inbound texts. A human must stop the sequences and set Not Interested. Don't
   reply asking them to text STOP.

**One Twilio number currently serves all four studios**, a STOP blocks the
person from every studio, silently. Per-studio numbers recommended.

---

## 6. Merge variables

Only these exist in Momence. Everything else is hard-typed per studio.

```
{{first_name}}  {{last_name}}  {{email}}
{{host_name}}  {{host_website}}  {{host_email}}  {{host_phone_number}}
```

---

## 7. Per-studio data

| | Minnetonka | St Louis Park | Eden Prairie | Savage |
|---|---|---|---|---|
| Code | Mtka | Slp | Ep | Sav |
| Sender | Karen | Karen | Lucie | Lucie |
| Address | 14200 Wayzata Blvd Suite C | 8314 Highway 7 | 7918 Mitchell Rd | 7737 Egan Dr |
| Phone | (952) 222-7563 | (952) 222-7822 | (952) 222-0789 | (952) 222-0793 |
| Booking slug | mtka | slp | ep | sav |
| Review slug | mtka-review | slp-review | ep-review | sav-review |
| boardId | 99073 | 99072 | 31146 | 35337 |
| venueId | 98916 | 98915 | 39159 | 42525 |
| Google place ID | ChIJu9YUbKVLs1IRUUzKcF35Yo0 | ChIJLcrLxNgh9ocRn7wGv1tAaq4 | ChIJI7Vp-fgZ9ocRmQ8CzbXobDs | ChIJQ5Mg8bA99ocR-jhFzWLoHvY |

Shared across all four: hostId **49534**, serviceId **220303**, staffId **-1**,
text-in number **(952) 800-3245**.

### URL patterns
```
Booking:  https://momence.com/The-Vital-Stretch-Twin-Cities/appointment-reservation/49534?boardId={board}&serviceId=220303&venueId={venue}&staffId=-1
Review:   https://search.google.com/local/writereview?placeid={place}
```
Short links redirect to those. **Use a 302 or 307, never a 301**, browsers
cache 301s forever, so you can't repoint a link already sitting in a text
thread. Hang UTMs on the destination, not the short link.

### Wayfinding landmarks (used in pre-visit copy)
| Studio | Short (in texts) | Long (in confirmation email) |
|---|---|---|
| Minnetonka | by Total Wine | in the center with Total Wine and Hobby Lobby, just northeast of where 494 meets 394 |
| St Louis Park | by Applebee's on Hwy 7 | at Knollwood Crossings on Highway 7 next to Applebee's, just east of 169 |
| Eden Prairie | next to Dojo Karate | on Mitchell Road just south of 5 and 212, right next to Dojo Karate |
| Savage | by Caribou at 13 & 42 | on the northeast corner of 13 and 42, next to Caribou Coffee over by the Target |

### Lead source IDs (Google / Microsoft / Meta)
- Minnetonka 188018 / 192509 / 172531
- St Louis Park 188017 / 192508 / 172530
- Eden Prairie 188015 / 192506 / 172528
- Savage 188016 / 192507 / 172529

---

## 8. Call window

**10 AM to 3 PM, Monday through Saturday.** This is the intersection of all four
studios' hours, so it's valid everywhere and never needs a per-studio edit. No
customer-facing message names a day or a clock time (the confirmation email
carries the exact appointment time), so nothing needs customizing per send.

---

## 9. Brand

- **Palette:** Deep Blue `#013160`, Light Blue `#71BED2`, Yellow `#FBB514`.
- **Type:** Yeseva One (headers), Futura Com Book (body). Both are licensed and
  absent from most email clients, build one branded Momence template with
  Georgia/Arial as the fallback stack. The brand lives in the words and color,
  not the typeface.
- **Method spine:** Strap In. / Let Loose. / Say Ahhh.
- **Four benefit pillars:** Everyday Ease, Graceful Aging, Peak Performance,
  Injury Recovery.
- **Terminology (overrides the stale brand guide):** VSP (Vital Stretch
  Practitioner), not CSP. PNF, not PNR. AIS = Active Isolated Stretching. Offer
  is 2×45min for $29 (the guide's $49/$29 is wrong).
- **Mandated email signature:** "When you're tight, nothing else goes right. We
  help you move freely so you can live fully."
- Legacy Connecticut assets and the old 20%-off card are out of scope.
- Testimonials Bob, Paul, Norma are from the corporate library, cleared for use
  until local ones exist.

---

## 10. Organization & rollout

- **One folder per studio** (Mtka, Slp, Ep, Sav) plus a **_Shared** folder
  (underscore sorts it to top). Not by sequence type, you build, pause, and
  duplicate a studio's whole flow as a unit.
- **Build order:** Minnetonka first (clean, no live sequences), then duplicate
  the folder three times and swap the per-studio content via find-and-replace.
- **Eden Prairie and Savage have live sequences already** (Savage "Local Drip,"
  EP legacy router). Before switching them: **pause** the old sequences
  (don't delete), let in-flight leads finish the old flow, and point only new
  leads at the new build. Two builds messaging the same lead is the failure
  mode to avoid.
- **Minnetonka opened Aug 3 2026 fully booked**, so launch copy says "we're now
  open" rather than naming a date. Launch block is Minnetonka-only, ~3 weeks,
  then revert to standard.

---

## 11. Open items to verify before trusting at scale

- **Test first, before building anything else: does "Lead assigned new stage"
  fire when the stage arrives from a lead-source default at creation**, or only
  when a human changes it afterwards? The entire main path assumes the former.
  If it is the latter, sequence 10 and TC - Unassigned need a different entry
  trigger. Do not create a per-studio catch-all.
- **Confirm the exact label of the membership-purchase trigger** used by 65. If
  the trigger list has no such trigger, have front desk set a
  `{STUDIO CODE} - Member` stage at the point of sale and trigger 65 on that stage;
  the rest of the sequence is unchanged.
- **Resolved: counter conditions are exits, not step-level gates.** This is why
  the welcome and review ask moved out of 60 into 65.
- **Resolved: true/false conditions fork into two paths.** The builder confirms
  a condition creates a True branch and a False branch, and a branch with no
  step ends there. Conditions go at the end of a sequence, never mid-drip.
- **Resolved: the appointment trigger is Appointment visit.** The account's
  trigger list shows Appointment booking, Appointment visit, Appointment visit
  using a membership, and Appointment visit using intro offers, and no
  standalone "Appointment check-in." The console and this file are correct.
- **Resolved: the Win-back trigger exists.** Searching the trigger box for
  "win" returns Win-back, based on the last class or appointment visit a
  customer made. Sequence 70 checks active membership at days 14 and 28. The
  active branch offers a complimentary 45-minute full-spectrum infrared sauna
  session for booking the next stretch; the inactive branch offers it for
  restarting a membership.
  Customers use code **SAUNAONUS** at checkout or give it to their practitioner
  to apply.
  Appointment booking and Membership purchase counters, both scoped after
  enrollment, remove customers once they come back. Sauna use is limited to
  adults 18+ after the required agreement and screening.
- Whether the native no-show trigger fires on appointment services or only
  classes. If it does, swap it into 40 in place of the No Show stage trigger.
- **Resolved: generic and manual leads use TC - Unassigned.** Abandoned checkout
  remains in its source-associated shared flow. Neither path receives a studio
  stage until the lead selects or books a location.
- **Resolved: sequence 20 is a finite offset ladder, not a rotation.** Momence
  cannot schedule recurring sends. 16 steps, day 7 to day 370, built from four
  templates duplicated into their slots.
- **Resolved: sequence 10 trimmed to 7 emails and 4 texts** with the duplicated
  asks and the doubled proof send removed.
- Birthday sequence is deferred: needs a customer custom field with "birthday"
  in the name before it can fire.
- Per-studio Twilio numbers to limit STOP blast radius.
