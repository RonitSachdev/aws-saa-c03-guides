# Section 31: Cost Management Tools

## The idea

AWS billing tools all sound alike, so think of your AWS bill as a household budget. One tool is the **bank app** where you browse where the money went (Cost Explorer). One is the **spending alarm** on your phone (Budgets). One is the **shoebox of every raw receipt** (Cost & Usage Report). One is your **suspicious spouse** noticing you spent triple the usual on takeout (Anomaly Detection). One is the **personal trainer** telling you your gym membership is too big for your usage (Compute Optimizer). The exam never asks you to master any of them — it asks you to **pick the right one from a verb**.

## The tool zoo

| Tool | One-liner | Signal words |
|---|---|---|
| **Cost Explorer** | Visualize and filter **historical** spend, **forecast ~12 months** ahead, get **RI/Savings Plan purchase recommendations** | "analyze," "visualize," "which service drives the bill" |
| **AWS Budgets** | Set thresholds on cost or usage; **alert** (or trigger actions) when actual/forecast crosses them | "notify," "alert at 80%," "exceeds" |
| **Cost & Usage Report (CUR)** | The **most detailed** line-item billing data, delivered **to S3**, queried with **Athena** (or QuickSight) | "granular," "most detailed," "line items," "SQL" |
| **Cost Anomaly Detection** | **Machine learning** watches spend and alerts on **unusual spikes** — no thresholds needed | "unexpected," "unusual," "anomaly" |
| **Compute Optimizer** | ML **rightsizing recommendations** for EC2, EBS volumes, Lambda, ASGs | "overprovisioned," "rightsize," "recommend instance size" |
| **Cost Allocation Tags** | Tag resources (team/project), then slice costs by tag — must be **activated in the Billing console** | "cost per team/department/project," "chargeback" |

Two footnotes:
- **Savings Plans / Reserved Instances** are the *commitment discounts* themselves (covered with EC2 pricing) — Cost Explorer is where AWS **recommends** buying them based on your history.
- **Billing Conductor** — niche one-liner: build *customized* (pro forma) billing views/rates for showing costs to internal groups or customers.

THE trap: **Budgets alerts, Explorer analyzes.** If the scenario wants a *notification when spending hits X%*, Cost Explorer is the decoy — it has forecasts but doesn't page you. And in the other direction, Budgets won't give you pretty historical breakdowns.

Second nuance worth a mark: tags don't help billing **retroactively or automatically** — a cost allocation tag only starts appearing in billing data **after you activate it**, and only for usage from then on.

Third lookalike: **Compute Optimizer vs Well-Architected Tool.** Compute Optimizer asks *"are my **resources** the right **size**?"* (EC2/EBS/Lambda/ASG metrics → rightsizing). The WA Tool asks *"is my **architecture** designed correctly across all six pillars?"* (a questionnaire → improvement plan). Resource sizing ≠ design review.

Reserved Instance billing quirks:
- When an RI **expires**, the instance keeps running and is billed at the **On-Demand** rate.
- **Terminating** the instance does **not** stop RI charges. You pay for the full term.
- A Reserved Instance is a billing commitment, not a specific machine.

**The decision line:** **SEE** spend → Cost Explorer. **ALERT** on spend → Budgets. **RAW detail** → CUR + Athena. **UNUSUAL** spend → Anomaly Detection. **RIGHTSIZE** → Compute Optimizer. **Per-team chargeback** → Cost Allocation Tags.

## Question patterns

> *"Receive a notification when forecasted spend reaches 80% of the monthly budget"* → **AWS Budgets** (threshold + notify = Budgets, every time)

> *"Finance needs to attribute AWS costs to individual teams and projects"* → **Cost Allocation Tags** (tag, activate in billing, slice the bill)

> *"Analysts need the most granular billing data, queryable with standard SQL"* → **CUR + Athena** (detailed line items land in S3; Athena is the SQL)

> *"Identify EC2 instances that are overprovisioned and get sizing recommendations"* → **Compute Optimizer** (ML rightsizing)

> *"Get alerted about unexpected spending spikes without setting thresholds"* → **Cost Anomaly Detection** (ML learns 'normal', flags weird)

> *"Understand which service caused last month's bill increase and forecast next quarter"* → **Cost Explorer** (visualize history + 12-month forecast)

> *"Decide how much Savings Plan commitment to purchase"* → **Cost Explorer recommendations** (based on your historical usage)

> *"Check whether the workload's overall design follows AWS best practices (not just instance sizes)"* → **Well-Architected Tool** (Compute Optimizer only rightsizes resources)

> *"A 1-year RI ended last week; what happens to the running instance's bill?"* → **It keeps running at On-Demand rates** (nothing stops, the discount just disappears)

## Pocket card

| Keyword | Answer |
|---|---|
| Visualize / analyze spend, forecast | Cost Explorer |
| Alert at % of budget | AWS Budgets |
| Most detailed / line items / SQL | CUR + Athena |
| Unusual spike, ML detection | Cost Anomaly Detection |
| Rightsize EC2/EBS/Lambda | Compute Optimizer |
| Cost per team / chargeback | Cost Allocation Tags (activate first) |
| RI / Savings Plan buy advice | Cost Explorer |
| Custom internal billing views | Billing Conductor |
| Review design against pillars | Well-Architected Tool (not Compute Optimizer) |
| RI expired | Falls back to On-Demand price |
| One bill across accounts | Organizations consolidated billing |

That closes out the governance-and-cost corner of the exam — from here, every scenario about "who pays, who sees, who's warned" should feel like matching verbs to vending machines.
