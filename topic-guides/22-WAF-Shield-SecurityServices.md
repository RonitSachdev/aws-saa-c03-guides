# Section 22: WAF, Shield & the Security Service Zoo

## The idea

Picture your application as a nightclub. Traffic pours in from the internet — most of it friendly, some of it trying to sneak SQL injection through the front door, some of it a mob of 10 million bots trying to trample the entrance. AWS gives you a **layered security crew**: a smart bouncer at the door who reads every ID (WAF), riot police who handle mobs (Shield), a head of security who makes sure *every* club in your chain follows the same door policy (Firewall Manager), and a whole back office of detectives watching camera feeds for suspicious behavior (GuardDuty, Macie, Inspector, and friends).

The exam loves this section because it's mostly a **matching game**: read the scenario, name the right crew member. Let's meet them.

### WAF — the Layer 7 bouncer

**AWS WAF** (Web Application Firewall) works at **Layer 7** — the application layer — meaning it actually *reads HTTP requests*: URLs, headers, query strings, body content. Jargon check: "Layer 7" is the top of the OSI networking model, where HTTP lives; Layers 3/4 are raw IP packets and TCP connections.

Because WAF reads HTTP, it can catch things a packet firewall never could:

| Rule type | What it catches |
|---|---|
| **SQL injection rules** | `' OR 1=1 --` hiding in a form field |
| **XSS rules** | Cross-Site Scripting — malicious `<script>` tags in input |
| **Rate-based rules** | Too many requests **per IP** in 5 minutes → block that IP |
| **Geo-match** | Block or allow by country |
| **IP sets** | Explicit allow/deny lists of IP addresses |
| **Managed rule groups** | Pre-built rule packs from AWS/vendors (e.g., **OWASP Top 10** core rule set) |

**Exam gold:** *"rate limit requests per IP"* → **WAF rate-based rule**. Every time.

And a lovely testing feature: **Count mode** — the rule *counts* matches instead of blocking, so you can test rules against production traffic without breaking real users. "Evaluate a new rule without impacting users" → Count mode.

**Where can WAF attach?** Only to **Layer 7 fronts**:

```
        WAF can attach to:                WAF CANNOT attach to:
  ┌──────────────────────────┐         ┌─────────────────────┐
  │  CloudFront              │         │  NLB  (Layer 4!)     │
  │  ALB                     │         │  EC2 directly        │
  │  API Gateway             │         │  Route 53            │
  │  AppSync                 │         └─────────────────────┘
  │  Cognito User Pools      │
  └──────────────────────────┘
```

Also: **NACLs and Security Groups can't block SQLi/XSS** — they only see IPs/ports. HTTP-content attacks → **WAF**.

THE trap: *"attach WAF to a Network Load Balancer"* → **impossible**. NLB is Layer 4 (TCP) — it never parses HTTP, so a Layer 7 firewall has nothing to read. WAF needs an L7 front: **CloudFront, ALB, API Gateway, AppSync, or Cognito**.

### Shield — the riot police (DDoS)

**DDoS** = Distributed Denial of Service — thousands of machines flooding you with traffic to knock you offline.

- **Shield Standard**: **free, automatic, for everyone**. Protects against common **Layer 3/4** attacks (SYN floods, UDP reflection). You already have it — nothing to enable.
- **Shield Advanced**: **~$3,000/month** (1-year commitment). Adds **Layer 7 DDoS protection**, a **24/7 DDoS Response Team (DRT)** of human experts you can call mid-attack, and **cost protection** — AWS refunds the scaling charges the attack caused.

**Memory hook:** any question mentioning **L7 DDoS, expert help, or refunds for attack-driven scaling** → **Shield Advanced**. A plain "protect against common DDoS at no cost" → **Shield Standard** (it's already on). Shield Advanced also gives **near-real-time visibility into attacks** and integrates with WAF.

**THE trap:** **WAF alone is not a DDoS answer** — rate-based rules help with L7 floods, but large-scale DDoS resilience = **Shield + WAF** together.

**DDoS-resilient architecture (the exam's reference answer):**

- **CloudFront** (and Route 53) at the edge to absorb traffic
- **ALB + Auto Scaling group** to scale out under load
- Databases (e.g., **RDS**) in **private subnets**
- **CloudWatch alarms** on unusual **NetworkIn / CPU** spikes
- **Shield (Advanced for L7/DRT) + WAF** on CloudFront/ALB

### Firewall Manager — the head of security for the whole chain

You have 50 AWS accounts in an **AWS Organization**. You want every ALB in every account — including accounts created *next month* — to automatically get your WAF rules. Manually? Nightmare. **AWS Firewall Manager** is the **central policy manager**: define security policies once (WAF rules, Shield Advanced, Security Group rules, Network Firewall rules) and it **auto-applies them across the organization**, including to **new accounts and new resources as they appear**.

**Prerequisites (exam-tested):** requires **AWS Organizations** + **AWS Config** enabled.

THE trap: *"every new account automatically gets the security policies"* → that word **automatically across accounts** means **Firewall Manager**, not WAF alone. WAF is the rule; Firewall Manager is the rollout machine.

THE trap: **Firewall Manager and Security Hub don't stop attacks themselves.** Firewall Manager only *administers* WAF/Shield Advanced/SG/Network Firewall policies across accounts; Security Hub only *reports* alerts and posture. The thing that actually blocks is **WAF** (L7) / **Shield** (DDoS) / **Network Firewall** (VPC).

### Network Firewall — the VPC-wide inspector

**AWS Network Firewall** is a **managed firewall for your whole VPC**, inspecting traffic at **Layers 3 through 7** — think intrusion prevention, domain filtering, stateful rules for *all* traffic entering/leaving the VPC, not just HTTP to one ALB. Scenario says *"inspect all traffic in the VPC"* or *"filter outbound traffic to specific domains for the entire VPC"* → **Network Firewall**.

- **Stateful IDS/IPS** built on open-source **Suricata** rules; filters traffic via **IGW, NAT gateway, VPN, or Direct Connect**.
- Can do **deep packet inspection**, allow only known AWS service domains/IPs, block lists of bad **domains (FQDN)**, and detect protocols like HTTPS **regardless of port** (a NAT Gateway can't filter domains).
- Deployed at the **VPC level** (firewall endpoints in dedicated subnets), not per subnet; it **can't attach to an ALB** and can't by itself restrict S3 bucket access to one VPC (use bucket policy + VPC endpoint).

**Lookalikes, not firewalls:** **Network Access Analyzer** (VPC feature) *reports* unintended network access paths against your requirements — **no deep packet inspection**. **Traffic Mirroring** *copies* ENI traffic to an appliance/NLB/GWLB for out-of-band analysis. **Detective** can't create a firewall either.

### The detection zoo — one-liners you must know cold

These are pure matching questions. Burn in the one-liners:

| Service | One-liner |
|---|---|
| **GuardDuty** | **ML threat detection** on **CloudTrail, VPC Flow Logs, DNS logs** — no agents. Finds **cryptomining, unusual API calls, compromised credentials** |
| **Macie** | **PII / sensitive data discovery in S3** (ML finds credit cards, SSNs) — data classification, shows where sensitive data lives and how it's accessed |
| **Inspector** | **Vulnerability scanner** — **CVEs** on **EC2 (via SSM agent), ECR container images, Lambda**; automated security/compliance assessment of apps (agent collects package & config info) |
| **Security Hub** | **Aggregation dashboard** — collects findings from all the above + runs compliance standards (CIS, PCI) |
| **Detective** | **Investigate AFTER a finding** — builds a graph of relationships to find **root cause** |
| **Artifact** | **Download AWS compliance reports** (SOC, PCI, ISO) to hand to auditors |

Mental model of the flow:

```
GuardDuty/Macie/Inspector ──findings──▶ Security Hub (one dashboard)
                                              │
                              "wait, WHY did this happen?"
                                              ▼
                                          Detective (root cause)
```

THE trap: *"GuardDuty vs Inspector"* — GuardDuty watches **behavior in logs** (threats happening now); Inspector scans **software for vulnerabilities** (holes that *could* be exploited). Threat = GuardDuty; CVE = Inspector.

THE trap: *"Macie for EC2 or RDS"* → no. **Macie is S3-only.**

## Question patterns

> *"Block SQL injection attacks against an application behind an ALB"* → **WAF on the ALB** (L7 rules read HTTP).

> *"Limit each client IP to 2,000 requests per 5 minutes"* → **WAF rate-based rule** ("per IP rate limit" is WAF's signature move).

> *"Protection against common DDoS attacks at no additional cost"* → **Shield Standard** (free, automatic, L3/L4).

> *"Company suffered a large DDoS, wants expert support during attacks and refunds for attack-related scaling costs"* → **Shield Advanced** (DRT + cost protection = the $3k tier).

> *"Ensure WAF rules are applied to all ALBs across 50 accounts, including future accounts"* → **Firewall Manager** (org-wide auto-apply; needs Organizations + Config).

> *"Identify S3 buckets containing personally identifiable information"* → **Macie** (PII in S3, full stop).

> *"Alert when EC2 instances are used for cryptocurrency mining or credentials are compromised"* → **GuardDuty** (ML on CloudTrail/Flow/DNS logs, agentless).

> *"Continuously scan EC2 instances and container images for software vulnerabilities (CVEs)"* → **Inspector** (SSM agent on EC2, ECR, Lambda).

> *"Single pane of glass for security findings across all accounts and services"* → **Security Hub** (the aggregation dashboard).

> *"After a GuardDuty finding, analyze and identify the root cause of the incident"* → **Detective** (post-finding investigation graph).

> *"Auditor requests AWS's SOC 2 / PCI compliance reports"* → **Artifact** (self-service report downloads).

> *"Block SQL injection — options include NACL rules"* → **WAF** (NACLs/SGs only see IPs and ports).

> *"Design a web app resilient to DDoS"* → **CloudFront + Shield/WAF in front of ALB + ASG, DB in private subnets, CloudWatch alarms on NetworkIn/CPU** (WAF alone isn't enough).

> *"Which service prevents attacks: WAF, Security Hub, or Firewall Manager?"* → **WAF** (Security Hub reports; Firewall Manager administers).

> *"Deep packet inspection and domain-based filtering for all traffic leaving the VPC"* → **Network Firewall** (Suricata IPS; not Network Access Analyzer, not NAT Gateway).

> *"Identify unintended network access paths to resources against compliance requirements"* → **Network Access Analyzer** (reports only, no packet inspection).

## Pocket card

| Keyword | Answer |
|---|---|
| SQLi / XSS / HTTP filtering | WAF |
| Rate limit per IP | WAF rate-based rule |
| Test rule without blocking | WAF Count mode |
| WAF attach points | CloudFront, ALB, API GW, AppSync, Cognito (never NLB/EC2) |
| Free automatic DDoS (L3/L4) | Shield Standard |
| L7 DDoS / DRT / cost protection | Shield Advanced ($3k/mo) |
| Security policies across org, auto for new accounts | Firewall Manager (needs Organizations + Config) |
| Inspect ALL VPC traffic L3–L7 | Network Firewall |
| Cryptomining / odd API calls / no agents | GuardDuty |
| PII in S3 | Macie |
| CVEs on EC2/ECR/Lambda | Inspector |
| One findings dashboard + compliance checks | Security Hub |
| Root cause after a finding | Detective |
| SOC/PCI/ISO reports for auditors | Artifact |
| SQLi via NACL/SG? | No — WAF |
| Large-scale DDoS resilience | Shield + WAF + CloudFront + ASG (not WAF alone) |
| Manages but doesn't block | Firewall Manager / Security Hub |
| Suricata IPS, deep packet inspection, FQDN filtering | Network Firewall |
| Report unintended network access, no DPI | Network Access Analyzer |
| Copy ENI traffic for analysis | Traffic Mirroring |

You've now got the security crew sorted — next up, the service that decides who your app's *users* even are: Cognito.
