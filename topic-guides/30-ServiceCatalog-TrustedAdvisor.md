# Section 30: Service Catalog & Trusted Advisor

## The idea

Two small services, one shared theme: keeping humans out of trouble.

**AWS Service Catalog** is a **vending machine of pre-approved infrastructure**. The cloud team stocks the machine; everyone else just presses a button and gets a compliant, working stack — no keys to the kitchen required. Concretely: administrators define **products** (which are really **CloudFormation templates**) and group them into **portfolios**, then grant end users access to launch them. The magic trick: users can launch these stacks **without holding broad IAM permissions themselves** — Service Catalog launches on their behalf using its own constrained role. So a data scientist can spin up "the approved EMR cluster" without ever having permission to create EMR clusters directly.

Signal phrase: "allow teams to deploy **only approved, standardized, compliant configurations** via self-service" → **Service Catalog**.

**Trusted Advisor** is your **automated AWS consultant** — a robot auditor that continuously scans your account and nags you about the exact things a human consultant would bill you for.

## Trusted Advisor's five pillars

| Pillar | Example checks |
|---|---|
| **Cost Optimization** | Idle EC2 instances, unattached Elastic IPs, underused RDS |
| **Performance** | Overutilized instances, high-latency configs |
| **Security** | Security groups open to 0.0.0.0/0, **MFA missing on root**, public S3 buckets |
| **Fault Tolerance** | Missing Multi-AZ, snapshots not taken, single-AZ exposure |
| **Service Limits** | You're approaching a **service quota** (e.g., near your VPC or EC2 limit) |

THE trap (tested nuance): **the free tier of Trusted Advisor gives only a handful of core checks** (basic security + service limits). To unlock the **full set of checks — including all Cost Optimization checks — you need a Business or Enterprise support plan.** If a question asks "why can't the team see the cost optimization checks?", the answer is their support plan, not a permissions problem.

Also worth one neuron each:
- Trusted Advisor **recommends**; it doesn't fix. Pair it with EventBridge/CloudWatch for alerting on check status changes.
- Trusted Advisor **can't define custom rules** — need your own compliance rule (e.g., "IAM password policy must require X" via the managed rule **`iam-password-policy`**)? → **AWS Config**.
- The **Service Limits** check flags a quota once usage passes **80%**; Performance/Fault Tolerance checks also surface **over-utilized resources**.
- Distinguish from neighbors: **Config** = "is this resource *compliant with my rules*?"; **Inspector** = software vulnerabilities on workloads; **Trusted Advisor** = broad best-practice checks across the five pillars, including cost and limits.

**The governance look-alikes (the exam lines them up as options):**

| Service | Primary purpose |
|---|---|
| **CloudTrail** | "**Who did what?**" — API auditing |
| **AWS Config** | "**What changed, and is it compliant?**" — config tracking + custom rules |
| **Trusted Advisor** | Best-practice **recommendations** (cost, security, limits...) |
| **IAM credential report** | Status of IAM users' **credentials** |
| **Control Tower** | **Landing zone** for a governed multi-account setup |
| **Service Catalog** | Catalog of **approved products/templates** |
| **Security Hub** | Aggregated **security findings** dashboard (doesn't prevent attacks) |
| **RAM** | **Share resources** across accounts |
| **Systems Manager OpsCenter** | Central place for **operational issues** (OpsItems) |
| **Well-Architected Tool** | Reviews whether a **workload's architecture** follows best practices |
| **Personal Health Dashboard** | AWS events affecting **your** resources (vs Service Health Dashboard = public, all customers) |

## Question patterns

> *"Non-technical teams must deploy infrastructure, but only pre-approved configurations, without granting them broad IAM permissions"* → **Service Catalog** (vending machine: products in portfolios, launch-on-behalf)

> *"Identify idle instances and unattached Elastic IPs to reduce the bill"* → **Trusted Advisor** (Cost Optimization pillar)

> *"Team can only see a few Trusted Advisor checks — why?"* → **Support plan** (full checks need Business/Enterprise)

> *"Get warned before hitting an AWS service quota"* → **Trusted Advisor Service Limits check** (limits = its own pillar)

> *"Flag security groups allowing unrestricted access and missing root MFA"* → **Trusted Advisor** (Security pillar)

> *"Central IT curates standard CloudFormation-based products for business units"* → **Service Catalog portfolios** (products live in portfolios, shared to users/accounts)

> *"Continuously check that the IAM password policy meets company rules"* → **AWS Config rule** (`iam-password-policy`) — Trusted Advisor can't define custom rules

> *"Is AWS EC2 having an outage affecting MY instances?"* → **AWS Health / Personal Health Dashboard** (Service Health Dashboard shows only public, general events)

## Pocket card

| Keyword | Answer |
|---|---|
| Self-service approved stacks, minimal IAM | Service Catalog |
| Product / portfolio | Service Catalog terms (CFN template / group of products) |
| Idle / unused / unattached resources | Trusted Advisor (Cost) |
| Approaching quota warning | Trusted Advisor (Service Limits) |
| Open SGs, root MFA check | Trusted Advisor (Security) |
| Full checks locked | Business/Enterprise support plan |
| Five pillars | Cost, Performance, Security, Fault Tolerance, Service Limits |
| Custom compliance rule (e.g., password policy) | AWS Config, not Trusted Advisor |
| Service Limits alert threshold | 80% of quota |
| Who did it? / What changed? / Recommendations? | CloudTrail / Config / Trusted Advisor |
| Events affecting my resources | Personal Health Dashboard |

Trusted Advisor tells you the bill *could* be smaller — the cost management tool zoo in the next section is how you actually see, alert on, and shrink it.
