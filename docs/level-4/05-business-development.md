# Business Development

!!! info "Reference"
    Core business development concepts — positioning, proposals, and client retention — are covered in the [Leadership & Team Management](04-leadership.md) module. This file covers the financial and commercial aspects of running a security practice.

---

## Pricing Security Services

### Day Rate vs Fixed Price

**Day rate (time and materials):** Client pays per day of effort. Good for engagements with undefined scope or significant unknowns. Risk shifts to client if the engagement takes longer than expected.

**Fixed price:** Agreed price for a defined deliverable. Good for well-scoped assessments with repeatable methodology. Risk shifts to vendor if scope creep occurs.

**Hybrid:** Fixed price for defined scope, day rate for anything outside. Most common in practice.

### Rate Benchmarks (India market, approximate)

| Experience | Day Rate Range |
|------------|---------------|
| Junior (0-2 years) | ₹8,000–15,000/day |
| Mid-level (2-5 years) | ₹15,000–30,000/day |
| Senior (5+ years) | ₹30,000–60,000/day |
| Principal/Partner | ₹60,000–1,50,000/day |

Boutique firms typically bill at 2-3x the cost of the consultant (covering overhead, margin, non-billable time, sales cost). These are rough benchmarks — MNC consulting firms charge significantly more; smaller boutiques may charge less.

---

## Managing Client Relationships

### The Trusted Advisor Position

The goal of every client relationship is to move from "vendor" to "trusted advisor" — the person the CISO calls when they have a problem, not just when they need to buy something.

How to build it:
- Share relevant threat intelligence proactively (not just when billing)
- Be honest about what you don't know and refer appropriately
- Call out problems with their approach even if it loses you the sale
- Follow up on recommendations from previous reports — do they need help prioritizing?

### Handling Scope Disagreements

Clients sometimes push back on scope after signing the SOW — adding requirements without adjusting timeline or budget.

**Approach:** Acknowledge the request professionally, clarify it's outside the agreed scope, and offer a formal scope change amendment with adjusted timeline and cost. Never agree verbally to expanded scope and absorb the cost — it sets a precedent and erodes margins.

---

## Building a VAPT Practice (Startup Context)

For a firm like Vexonis, building credibility early:

**Certifications as credibility signals:** CEH, OSCP, CRTE, CISAs — each certification the team holds reduces the barrier to enterprise clients who need to justify their vendor selection.

**Case studies:** Anonymized case studies ("We helped a mid-size e-commerce firm discover and remediate a critical authentication bypass that could have exposed 2 lakh customer accounts") are more powerful than generic capability descriptions.

**Compliance-driven entry:** PCI-DSS ASV scans and ISO 27001 gap assessments are easier to sell than red team assessments to clients without mature security programs. These clients then trust you for more complex work.

**Niche expertise:** Being known as the best in a specific domain (healthcare security, fintech, SCADA/OT) is more valuable than being generically good at everything. It drives inbound referrals.

**Partnerships:** Partnering with law firms (pre-breach assessments as legal privilege), insurance brokers (cyber insurance requirements), and IT MSPs (security as an add-on service) creates referral channels.

---

## Managing the Sales Pipeline

### Lead Generation for a Security Firm

Cold outreach in security is less effective than warm introductions and inbound marketing. Channels that actually work:

**Speaking and content:** Conference talks, webinars, blog posts, and LinkedIn articles position you as an expert. A single well-written post about a novel finding or methodology tip can generate months of inbound leads. This is why the Vexonis blog matters — it's a credibility signal that prospects find when researching vendors.

**Referrals:** The highest-quality leads. Happy clients refer to their networks. Legal firms, accounting firms, and MSSPs that don't offer security testing are natural referral partners — they regularly encounter clients who need VAPT and can refer without competing.

**LinkedIn outreach:** Target CISOs, IT managers, and compliance officers at organizations in your industry vertical. Message with genuine insight ("I noticed your public certificate transparency shows some subdomains that might be worth reviewing") — not generic pitches. Engagement rate is low but conversion when it happens is high.

**Bug bounty and CVE publication:** Publicly credited findings build reputation. Even one CVE or a blog post documenting a novel technique in a common product gets your name in front of the right people.

---

## Scope of Work Templates

Maintaining standard SOW templates for each service line reduces proposal time and ensures legal consistency.

**Template sections to standardize:**
```
1. Parties and authorization (boilerplate)
2. Engagement overview (customize per client)
3. Scope definition (carefully customize — this is the risk point)
4. Testing window (customize)
5. Deliverables and timeline (semi-standard)
6. Emergency contacts (always customize)
7. Data handling and confidentiality (boilerplate)
8. Limitation of liability (boilerplate with legal review)
9. Signatures
```

**Key scope language to get right:**
```
"In scope: The following IP ranges and domains, 
and any additional assets discovered during testing 
that are owned by [Client Name] and accessible from 
these entry points:
  - [IP ranges]
  - [Domains]

Out of scope: Third-party services, shared hosting 
environments, cloud provider infrastructure, and any 
system not explicitly listed above.

The following activities require separate written 
authorization and are not covered under this agreement:
  - Social engineering of employees
  - Physical security testing  
  - Denial-of-service testing
  - Testing outside defined windows"
```

---

## Financial Management for a Boutique VAPT Firm

### Revenue Metrics to Track

**Utilization rate:** What percentage of available billable hours are actually billed? Target: 65-75% for consultants (rest is business development, admin, training, non-billable work). Below 50% = revenue problem. Above 85% = burning out your team.

**Realization rate:** Of billed hours, what percentage are actually collected? Unpaid invoices are a cash flow killer. Net 30 payment terms and deposits (30-50% upfront) for new clients reduce this risk.

**Average engagement value:** Track the average revenue per engagement. If it's declining, you're being squeezed on price or taking smaller clients.

**Revenue per consultant:** Total revenue divided by number of billable consultants. Industry average for boutique security consulting: USD $150,000–400,000 per consultant per year, depending on market.

### Pricing Strategy

**Cost-plus pricing:** Calculate your cost (salary + overhead + margin) and price from there. Simple but doesn't capture value delivered or market rates.

**Market-rate pricing:** Research what comparable firms charge. Price at or slightly below initially to win clients, then increase rates as reputation builds.

**Value-based pricing:** Price based on what the engagement is worth to the client. A penetration test that protects ₹50 crore in cardholder data is worth more than the same test on a low-value system. Hard to execute without client trust and relationship.

**Packaging:** Fixed-price packages reduce sales friction. "Standard Web Application Assessment — ₹75,000 — 5-day engagement, one application, report + readout" is easier to sell than a custom quote every time.

---

## Client Onboarding and Delivery Excellence

### Pre-Engagement Checklist

```
□ SOW signed by appropriate authority
□ NDA signed
□ Emergency contact confirmed (24/7 phone number)
□ Technical contact confirmed
□ Scope confirmed in writing
□ Testing window confirmed
□ VPN or network access tested and working
□ Test accounts provided (if authenticated testing)
□ Payment terms confirmed (deposit received if new client)
□ Third-party authorization obtained if needed
```

### Delivery Timeline

```
Day 0:    Kick-off call — confirm scope, contacts, process
Days 1-N: Active testing (N depends on scope)
Day N:    Draft report shared internally for peer review
Day N+1:  Draft report delivered to client technical contact
Day N+3:  Client feedback period ends
Day N+5:  Final report delivered
Day N+7:  Readout call (optional — recommended for critical findings)
Day N+37: 30-day follow-up call (remediation progress check)
```

### Common Delivery Mistakes to Avoid

**Late reports:** A single late report damages the relationship more than any technical issue. If you're going to be late, communicate 48 hours in advance, not on the day.

**No executive summary:** Technical teams love technical detail. Executives stop reading after page 2. Without a strong executive summary, your findings don't reach the people who control the budget.

**Missing evidence:** "We found SQL injection" without a screenshot or HTTP request in the report is a professional failure. Every finding needs reproducible evidence.

**No remediation guidance:** Finding the vulnerability is half the job. Tell them specifically how to fix it — not just "use parameterized queries" but show the code change in their language and framework.

**Scope creep absorption:** If the client asks for more work mid-engagement, acknowledge it, scope it, quote it. Don't absorb it silently and then resent it.
