# “Make it sparkle. We'll add the customers later.”

[English](DIALOGUE.md) · [Русский](DIALOGUE.ru.md) · [简体中文](DIALOGUE.zh-CN.md)

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

## Practices behind the advice

- [OWASP: Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [OWASP: Authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [GOV.UK: Start by learning user needs](https://www.gov.uk/service-manual/user-research/start-by-learning-user-needs)
- [GOV.UK: Prototyping](https://prototype-kit.service.gov.uk/prototyping/)
