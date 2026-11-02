# Section 7: Route 53

## The idea

You type `www.example.com` into your browser. Your computer has no idea what that means — the internet runs on IP addresses, not names. So the first thing that happens, before a single byte of your website loads, is a lookup: *"what IP address is example.com?"*

**DNS (Domain Name System) is the internet's phonebook.** You give it a name, it gives you back a number, and then it's done. Route 53 is AWS's DNS service — and the single most important thing to understand about it is this:

**Route 53 answers the question, then EXITS. It never carries your traffic.**

Compare that to a load balancer, which is a **doorman standing in the path of every request** — every packet flows through it, forever. Route 53 is more like the receptionist in the lobby who points you to the right building and never sees you again.

That difference sets the two services at **different zoom levels**:

```
        "Which SITE/REGION?"           "Which INSTANCE?"
              Route 53          →      Load Balancer (ELB)
           (phonebook —                  (doorman —
         out of the path)             in the path always)
```

- **Route 53 picks between REGIONS or sites** (us-east-1 vs eu-west-1, primary vs DR).
- **ELB picks between instances** inside a region.

And because clients **cache** DNS answers (controlled by **TTL — Time To Live**, the "how long may you remember this answer" setting), Route 53 failover is **slow** — clients keep using the old cached IP until TTL expires. ELB failover is **instant** because the doorman is in the path and just stops sending to the dead instance. This one fact decides several exam questions.

The standard architecture sandwich you'll see over and over:

```
User → Route 53 → picks a REGION → ALB in that region → picks an INSTANCE
        (DNS)                        (load balancer)
```

## Record types

| Record | Maps | Notes |
|---|---|---|
| **A** | name → IPv4 address | The bread and butter |
| **AAAA** | name → IPv6 address | "Quad-A" = IPv6 |
| **CNAME** | name → **another name** | **CANNOT exist at the root/apex** (`example.com` itself) — only on subdomains like `www.example.com` |
| **Alias** | name → **AWS resource** | AWS extension. **WORKS at the apex**, queries are **free**, and it **auto-tracks the resource's changing IPs** |

Alias records point at ALBs, CloudFront distributions, S3 static websites, API Gateway, and more. AWS resources like ALBs have IPs that change constantly, so you can never hardcode an A record to one.

- An Alias comes in an **A flavor (IPv4)** and an **AAAA flavor (IPv6)**; a *non-alias* A record is for when you genuinely have a raw, fixed IP (e.g., an Elastic IP). An "alias CNAME at the apex" is still wrong — the apex rule bans CNAMEs, period.
- **MX** = mail exchange record (a priority + a mail server name) — the answer when the scenario is about *email* delivery for the domain.
- **DNSSEC is not a record type** — it's a set of protocols that cryptographically sign DNS answers. If an option lists "DNSSEC" as a record to create, it's a decoy. (Route 53 *does* support DNSSEC **signing** for public hosted zones as a feature.)
- **TTL** is set per record: the number of **seconds recursive resolvers may cache** the answer. Low TTL = faster failover/changes but more queries (cost); high TTL = cheaper, slower to change.

**THE trap:** *"point the root domain `example.com` at an ALB"* → **Alias record, never CNAME** (CNAME is illegal at the apex) **and never a plain A record** (the ALB's IPs change). Root domain + AWS resource = **Alias**. Every time.

## Hosted zones

A **hosted zone** is a container for all the DNS records of one domain.

- **Public hosted zone** — answers queries from the whole internet.
- **Private hosted zone** — answers queries **only from inside VPCs you attach it to**. This is how you get internal DNS names like `db.internal.company.com` that resolve only within your network. Exam signal: *"DNS names resolvable only within the VPC"* → private hosted zone.

**S3 static website on your own domain via Route 53** needs three things: a **registered domain**, **Route 53 as its DNS service** (public hosted zone), and an **S3 bucket named exactly like the domain/subdomain** (`www.example.com` bucket for `www.example.com`), pointed at with an Alias record.

## Routing policies

This is the heart of the Route 53 exam material. Learn the **signal phrases**:

| Policy | What it does | Exam signal phrase |
|---|---|---|
| **Simple** | One record, one answer, no health checks | The default; rarely the answer |
| **Weighted** | Split traffic by percentage you assign | *"A/B test"*, *"send 10% to the new version"* — **canary** |
| **Latency** | Answers with whichever region is **fastest for that user** | *"best performance for global users"*, *"lowest latency"* |
| **Failover** | Primary + secondary; flips when **health check** fails | *"active-passive"*, *"disaster recovery site"* |
| **Geolocation** | Routes by **where the user IS** — a hard rule | *"EU users must be served from EU"* (compliance), language-specific sites. **Needs a Default record** for unmatched locations |
| **Geoproximity** | Draws a map boundary between **YOUR resources**, adjustable with a **BIAS** dial | *"gradually shift/increase the traffic share to a region"*, the literal word **"bias"** |
| **Multi-Value** | Returns **up to 8 healthy** answers at once | *"simple load balancing via DNS"* — a poor man's load balancer |

**Latency vs Geolocation** — the classic confusion pair:
- **Latency** = a **performance** decision. "What's FASTEST for this user?" (A user in London might get served from us-east-1 if that's genuinely faster right now.)
- **Geolocation** = a **legal/content RULE**. "Users in Germany get the German site, period." Location is the rule, not the speed.

Ask yourself: does the scenario care about *speed* or about *where the user physically is*? Speed → Latency. Rule → Geolocation. Corollary: latency routing **does not guarantee** that users in the same country always land in the same region — network conditions change the answer.

**Geoproximity's name tag:** if the question says **"bias"** or talks about **expanding one region's share of traffic** by turning a dial, that's Geoproximity. Geolocation has no dial; Geoproximity is all dial. Example: servers in London and Frankfurt — a user in France lands on London by plain proximity; give Frankfurt a **positive bias** and its boundary grows, pulling more mainland-Europe users there (configured through **Traffic Flow**). Negative bias shrinks a region.

**Route 53 only answers questions** — it has no compute (it can't "run a Lambda" to decide) and it can't block **SQL injection/XSS** (that's WAF).

### Active-active vs active-passive failover

| | **Active-active** | **Active-passive** |
|---|---|---|
| Who serves | **All** resources, all the time — no primary, no secondary | **Primary** serves everything; secondary waits |
| How | Any policy *other than* Failover (e.g., **Weighted**, Latency, Multi-Value) with health checks — all records with the same name/type/policy are returned unless unhealthy | **Failover** policy — only healthy primaries are returned; secondaries only when **all** primaries are unhealthy |
| Signal | *"use all resources", "both regions serve traffic"* | *"standby / backup site waits for failure"* |

**THE trap:** you can't build active-active out of a Failover policy's one-primary-one-secondary pair — the moment you see "primary/secondary", it's active-passive.

## Health checks

Route 53 health checks are performed by a fleet of **global checkers** scattered around the internet. That creates one famous limitation:

**Global checkers live on the public internet — they CANNOT see private endpoints** (instances in private subnets, private IPs). The fix: create a **CloudWatch alarm** that monitors the private resource, then create a Route 53 health check **based on that alarm**.

**THE trap:** *"health check a private endpoint"* → global checkers can't reach it → **CloudWatch alarm-based health check**.

You can also build **calculated health checks** — combine up to 256 child checks with AND/OR/NOT logic into one parent check ("healthy only if at least 3 of 5 children are healthy").

## Failover: who handles what

| Failure level | Who fixes it | Speed |
|---|---|---|
| Instance dies in a region | **ELB** stops routing to it | Instant (in-path) |
| Whole region/site dies | **Route 53** failover policy | Slow-ish (DNS TTL caching) |

One neat corollary: if your DR design is **a single instance per region**, there's nothing for an ELB to balance — Route 53 Failover pointing at the instances directly is enough, and you can **skip the ELB entirely** (saves money; the exam likes this).

## Question patterns

> *"Point the apex/root domain example.com at an Application Load Balancer"* → **Alias record** (CNAME is forbidden at the apex; Alias is the AWS answer, free and auto-tracking).

> *"Active-passive setup: send traffic to the standby region only when the primary fails"* → **Failover routing policy + health check** ("active-passive" is the giveaway).

> *"Test a new app version by sending 10% of users to it"* → **Weighted routing** (canary = percentages = weights).

> *"Users in Germany must see the German-language site"* → **Geolocation** (user's location is a RULE, not a performance choice — and don't forget the Default record).

> *"Serve global users with the best possible performance"* → **Latency routing** ("fastest" = latency).

> *"Gradually increase the share of traffic going to the new region"* → **Geoproximity with bias** ("shift traffic share" / "bias" is Geoproximity's name tag).

> *"Health-check an endpoint that has a private IP inside a VPC"* → **CloudWatch alarm-based health check** (global checkers can't see inside your VPC).

> *"Return several healthy IPs and let clients pick, without a load balancer"* → **Multi-Value answer routing** (up to 8 healthy records).

> *"Both regions should serve traffic all the time, removing any that become unhealthy"* → **Active-active** (Weighted/Latency + health checks — not the Failover policy)

> *"Host a static website from S3 at www.example.com"* → **bucket named `www.example.com`** + Route 53 hosted zone + **Alias** record

> *"Which DNS record should be created for DNSSEC?"* → **none — DNSSEC isn't a record type** (it's a signing protocol)

> *"Multi-region app needs near-INSTANT failover; DNS caching delays are unacceptable"* → **Global Accelerator instead of Route 53** (anything in the request path beats a phonebook when clients cache old answers).

## Pocket card

| Keyword in question | Answer |
|---|---|
| Root/apex domain → ALB/CloudFront/S3 | **Alias record** |
| name → name, NOT at apex | CNAME |
| "A/B test", "10% canary" | **Weighted** |
| "best performance", "lowest latency" | **Latency** |
| "active-passive", "DR site" | **Failover** + health check |
| "users in country X get X content", compliance | **Geolocation** (+ Default record) |
| "bias", "shift traffic share between regions" | **Geoproximity** |
| up to 8 healthy answers, DNS-level LB | **Multi-Value** |
| DNS only inside a VPC | **Private hosted zone** |
| health check a private endpoint | **CloudWatch alarm-based check** |
| combine many health checks | Calculated health check |
| instant multi-region failover, no DNS lag | **Global Accelerator** |
| All resources serve, no primary/secondary | **Active-active** (Weighted/Latency + health checks) |
| Email for the domain | MX record |
| S3 website on own domain | Bucket name = domain + Alias |
| Shift Geoproximity boundary | Bias (via Traffic Flow) |

Route 53 hands out addresses and steps aside — but when the exam demands *instant* global failover with fixed IPs, you need something that stays in the path, which is exactly where Section 8's Global Accelerator picks up.
