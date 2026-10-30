# Five skills, one barber, several questionable ideas

[English](DIALOGUE.md) · [Русский](DIALOGUE.ru.md) · [简体中文](DIALOGUE.zh-CN.md)

**Educational fiction applies to every scene below.** These standalone sketches show working methods, not recorded runs, measured results, endorsements or guarantees. Any scans, observations and tests inside the story are fictional.

**Contents:** [CEO](#ceo) | [Writer](#writer) | [Security](#security) | [Debugger](#debugger) | [User Review](#user-review)

## CEO

### “Make it sparkle. We'll add the customers later.”

**Educational fiction:** a working style, not a real case, measured result, or guarantee of CEO AI's behavior.

**Customer:** I have a billion-dollar idea: a booking app, social network, marketplace, and AI. Everything should sparkle.

**CEO:** Ambitious. Before choosing the glitter: whose problem are we solving, and what would success look like?

**Customer:** My barber loses bookings in messages. But I'm thinking globally.

**CEO:** Let's learn where appointments get lost. First hypothesis: one barber, available slots, booking, confirmation. Global glitter can wait outside.

**Customer:** Fine. Put the API key in the website so setup is easier. No login either. Friction kills conversion.

**CEO:** A public secret becomes someone else's spending money. Keep keys server-side in a secret manager, grant minimal permissions, and revoke or rotate exposed keys. We can simplify the booking flow without exposing secrets or customer records.

**Customer:** Customers could edit bookings by changing the number in the URL. Very intuitive!

**CEO:** Also intuitive for editing someone else's haircut. The server must check access to each booking; guessing an ID must not grant access. We'll test those checks, including attempts to open another customer's booking. The exact access method depends on the data and workflow.

**Customer:** Let's skip interviews. I am a user, and I already agree with myself.

**CEO:** Useful input, incomplete sample. Let's observe real booking attempts and test a prototype. If people get stuck, changing a sketch costs less than rebuilding an app.

**Customer:** The landing page should say “The world's safest booking system. Guaranteed double revenue.”

**CEO:** We have evidence for neither claim. Let's describe what it actually does: helps customers choose a slot and receive confirmation. Then run a small campaign with a capped budget and measure completed bookings and abandoned attempts.

**Customer:** So where is my disruptive innovation?

**CEO:** Perhaps customers booking successfully. Let's establish the baseline before declaring a disruption.

**Customer:** One barber, a prototype, access checks, private keys, and a small marketing test. Can the confirmation button sparkle?

**CEO:** If it stays readable and usable. I have also occasionally mistaken an animation for a strategy.

**Later, in this fictional story, after prototyping and testing:**

**Customer:** Booking works! Tests reject access to someone else's booking, keys stay private, and the marketing finally explains the product.

**CEO:** A useful first version. Keep testing assumptions as it grows.

**Fictional outcome:** A working, focused booking product—not a real benchmark or security guarantee.

### Practices behind the advice

- [OWASP: Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [OWASP: Authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [GOV.UK: Start by learning user needs](https://www.gov.uk/service-manual/user-research/start-by-learning-user-needs)
- [GOV.UK: Prototyping](https://prototype-kit.service.gov.uk/prototyping/)

## Writer

### "Make it sound human. But keep the synergy."

**Customer:** Our barber needs a booking announcement. Make it sound like me, but impressive. Keep "synergy". I paid for that word in a webinar.

**Writer:** Who will read it? What works? Your notes supply the facts. The webinar can supply the receipt.

**Customer:** Existing customers. One barber, available times, booking confirmation. Payment is at the shop. My draft: "Our solution enables seamless synergy between clients and available appointment slots, with confirmation and in-shop settlement."

**Writer:** After: "You can now book your haircut online. Choose an available time and get your booking confirmation. Pay at the shop."

**Customer:** That's clear. But could we say customers already love it?

**Writer:** Only with evidence. The notes contain no feedback. The rewrite keeps the steps and payment detail without adding a testimonial.

**Customer:** Fine. Keep "haircut". I never say "grooming experience" unless the mirror is charging me by the syllable.

**Writer:** Kept. I checked that "confirmation" didn't become "instant confirmation". That would promise speed the notes don't establish.

**Customer:** Remember that preference forever. Actually, no, just this draft. Can synergy go somewhere?

**Writer:** Memory stays off. I'll use the correction in this chat. Put "synergy" in the barber's crossword. The announcement is ready for your review, and has not been published.

## Security

### "Audit the booking app. Can you try the live site?"

*Fictional walkthrough; no system was accessed and no test was performed.*

**Customer:** Audit our booking app. Can you try the live site? I would prefer to find the holes before our customers do.

**Security:** Which target do you own or have permission to test, and what is in scope? I can begin with approved code and configuration. Active tests need a concrete plan and your informed consent; the host's permissions and policy still apply.

**Customer:** We own https://booking-staging.example.invalid. Only /api/bookings/synthetic-17 is in scope. Review its booking handler and access-control configuration. We have two synthetic test accounts and fake bookings. Production, payments and third-party systems are outside scope. No active requests yet.

**Security:** In this fictional code review, the handler appears to check login without checking who owns the booking. One account might read another account's booking. Code review supports that hypothesis; it does not prove the deployed API behaves that way.

**Customer:** How would you verify it without turning a booking into an incident?

**Security:** Proposed test: two read-only GET requests to the approved staging booking endpoint, first as the owner of a synthetic booking, then as the other test account for that same booking. Purpose: check the ownership boundary. Limit: two requests, one at a time, within 60 seconds, a 5-second timeout per request, redirects disabled; no retries or intended booking-data writes. Even reads can create logs and expose data. A safer option is to keep the finding as an unverified code-review hypothesis. Stop on real data, instability, an unexpected redirect or any scope change. Record only status and the synthetic booking marker, keep credentials out of the report, then discard the local test clients without extra requests. Reads can still affect logs or session metadata; if a prearranged cleanup cannot be completed, I will stop and report it. Do you approve this plan?

**Customer:** Within this fictional story, I approve exactly that staging test, with those two synthetic accounts, the two-request/60-second limit and stop/local-client-cleanup rules. No production access.

**Security:** Fictional outcome: the second account receives the synthetic booking marker too. Stop at that minimal proof. The report would identify the endpoint, conditions, observed response and impact, without saving tokens or unrelated data. Add server-side ownership enforcement, then verify that the owner succeeds and the other account is denied under an approved retest plan.

**Customer:** So we can stamp the entire app secure after the fix?

**Security:** No. This example covers one access-control path. Mobile clients, infrastructure, AI integrations and other endpoints were not tested. Any checks that could not run remain unverified. The report separates verified evidence from hypotheses. A new target or risk needs new consent; approval can be reused only while scope and risk stay unchanged.

## Debugger

### "The button is broken. Let's rewrite the company."

**Customer:** Our barber's booking button does nothing. New framework, new database, perhaps a new barber?

**Debugger:** First reproduce: choose a time, press "Book", expect confirmation. In this fictional test environment, it fails. Let's trace the click before replacing the scissors.

**Customer:** It's probably the server. Servers have that look.

**Debugger:** If a request arrives, inspect the response. If none leaves, inspect the client. In the story's trace, none leaves. The click handler runs, then exits because it reads `selectedSlot`; the picker writes `slotId`.

**Customer:** Two names for one appointment. Very premium. Fix that, within the agreed scope.

**Debugger:** The focused test first fails after selecting a slot. I make the handler read `slotId`. In this fictional check, the reproduction and test pass. Without a slot, it still asks the customer to choose one.

**A separate act: refactoring.**

**Customer:** Now merge the two confirmation builders. Keep the output. Can we add a loyalty scheme inside the helper?

**Debugger:** Separate request. For this refactor, I record both builders' outputs, error text and send counts. Then extract the shared formatting, preserving those contracts after each step.

**Customer:** And the result?

**Debugger:** In the story's comparison, confirmation text, errors and one-send behavior match the baseline. The duplicate formatting is gone. Those checks cover these paths, not every possible input. The barber keeps the scissors and the framework.

## User Review

### "The button is obvious. I invented it."

**Customer:** Review this barber booking screen. The button says "Activate your transformation". Obviously, you click it to book.

**User Review:** Goal: book a Tuesday evening haircut. I'll inspect the supplied screenshot as a tired first-time customer and an experienced salon receptionist, also tired and new to this app. This is a synthetic review.

**Customer:** Customers should study our terminology. There's a glossary in the footer.

**User Review:** Novice lens: visible slots invite progress, but the button doesn't name the action. "Transformation" might mean a product offer. Possible hesitation is a hypothesis from the wording, not an observed exit.

**Customer:** The receptionist handles appointments all day. They'll understand.

**User Review:** Professional lens: times help, but there's no service duration. They might hesitate, unable to judge whether it fits. Experience doesn't reveal hidden fields.

**Customer:** So, bigger button? It already takes up most of Tuesday.

**User Review:** Label it "Book Tuesday at 18:00". Add service, duration and price: more text, but useful for deciding. Provide confirmation and a way to change the booking. A screenshot can't verify interactions.

**Customer:** What if they book and leave immediately? Our engagement will look terrible.

**User Review:** That could be success: both need a confirmed appointment, then a free exit. Validate these proposals through real booking attempts in an approved test setting. We have no measured user results.
