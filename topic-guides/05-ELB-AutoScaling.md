# Section 5: Elastic Load Balancing & Auto Scaling

## The idea

Imagine a popular restaurant with one front door and a host standing at it. Guests don't wander in and pick their own tables — they walk up to the host, and the host seats them at whichever table is free. If a table breaks (wobbly leg, spilled soup everywhere), the host simply stops seating people there until it's fixed. Guests never know or care which table they got; they just know the restaurant's one address.

That host is a **load balancer**. Your servers (EC2 instances) are the tables. The load balancer gives clients **one single DNS name** (one front door), **spreads incoming traffic** across many servers, and constantly runs **health checks** — little "are you okay?" pings — so it stops sending traffic to any server that's sick. When the server recovers, traffic flows to it again.

Auto Scaling is the restaurant manager who watches how busy it is and **adds or removes tables** to match demand. Put them together and you get the classic AWS architecture: an Elastic Load Balancer (ELB) out front, an Auto Scaling Group (ASG) behind it, growing and shrinking with load, healing itself when instances die.

## OSI layers in 60 seconds (you need this to pick the right LB)

Networking is described in "layers" — the OSI model — and the exam expects you to know layers 3, 4, and 7. Think of it as **mail**:

- **Layer 3 (Network)** = the **address on the envelope**. Just an IP address — which building does this go to?
- **Layer 4 (Transport)** = the envelope address **plus the apartment number** — the **port** (like TCP port 443 or UDP port 3000). Which building, AND which door inside it?
- **Layer 7 (Application)** = the mail carrier **opens the envelope and reads the letter**. Now you can see HTTP details: the URL path (`/api/orders`), headers, cookies, hostnames.

**The layer a load balancer works at = how deep it looks into traffic = what decisions it CAN make.** An L4 balancer never opens the envelope, so it can't route based on URL paths — it's blind to them. But not opening envelopes makes it *fast*. That trade-off is the whole ALB-vs-NLB story.

## The four load balancers

| | Layer | Protocols | Superpower | Exam smell |
|---|---|---|---|---|
| **ALB** (Application) | 7 | HTTP, HTTPS, gRPC | Smart routing by path/host/header | "route /api to...", microservices, WAF |
| **NLB** (Network) | 4 | TCP, UDP, TLS | Speed + **static IP** | "millions of requests", UDP, "whitelist IPs" |
| **GLB** (Gateway) | 3 | IP packets (GENEVE) | Sends traffic *through* appliance fleets | "third-party firewall/IDS/IPS" |
| **CLB** (Classic) | 4/7 | Old | None — **legacy** | If CLB is an answer option, it's wrong |

### ALB — the smart host (Layer 7)

The ALB opens every envelope. Because it reads HTTP, it can make **content-based routing** decisions:

- **Path routing**: `/api/*` → the API target group, `/images/*` → the image servers
- **Host routing**: `app.example.com` → one group, `admin.example.com` → another
- **Header / query-string routing**: route by a custom header or `?version=beta`
- **HTTP-method routing**: `GET` vs `POST`/`PUT` to different groups
- **Source-IP routing**: route by the client's **source IP CIDR** (e.g., office range → internal group)

How the routing is wired: a **listener** only checks **protocol + port** (e.g., HTTPS:443). Behind it sit **listener rules** evaluated in **priority order** (lowest number first), with a **default rule** as the catch-all. Each rule's action forwards to a **target group**.

- **Weighted target groups**: one rule can forward to **several target groups with weights** (e.g., 90/10) — the ALB-native answer for **blue/green and canary** releases.
- **Slow start mode**: a newly registered target gets a **gradually increasing share** of requests over a ramp-up period instead of a full blast — for apps that need to warm caches/JIT first.
- The ALB runs **its own health checks** against each target group (HTTP path + expected code) — separate from EC2 status checks.

Key facts to lock in:

- Targets can be **EC2 instances, private IPs, Lambda functions, or containers (ECS)** — grouped into **target groups**.
- The ALB terminates the client connection and opens a new one to the target, so the target sees the ALB's IP. The real client IP is passed in the **X-Forwarded-For** header. *"App needs the client's IP behind an ALB"* → read X-Forwarded-For.
- **AWS WAF attaches to ALB** (a web application firewall inspects HTTP — it needs Layer 7, so it can't attach to an NLB).
- **Sticky sessions**: a cookie pins a user to the same target — for legacy apps that store session state locally. (Better design: externalize session to ElastiCache/DynamoDB, but "sticky sessions" is the quick fix answer.) If session state is **already shared** across instances, sticky sessions add nothing but uneven load — don't use them.
- **Dynamic port mapping** with ECS: multiple containers of the same app on one instance, each on a random port — the ALB tracks and routes to them. This is how you pack containers densely.
- ALB gives you a **DNS name, not a static IP**. THE trap: *"customers must whitelist a fixed IP"* → ALB **cannot** do this → put an **NLB** in front, or use **Global Accelerator**. (You **cannot attach an Elastic IP to an ALB** — the pattern is an **NLB with EIPs → ALB as its target**.)

### NLB — the fast, no-questions host (Layer 4)

The NLB never opens envelopes. It sees IP + port and forwards, blazingly fast:

- Handles **millions of requests per second** with **ultra-low latency** — the "extreme performance" keyword answer.
- Speaks **any TCP or UDP** — gaming servers, IoT, MQTT, custom binary protocols. ALB can't do UDP; NLB can.
- **One static IP per AZ**, and you can assign your own **Elastic IPs**. This is THE whitelisting answer. With **BYOIP (Bring Your Own IP)** you can even use your **own already-trusted public IP range** as the NLB's Elastic IPs — partners don't have to update their allow-lists.
- **IP-address targets** can be **any private IP from an ENI** — including targets in a **peered VPC, even cross-Region**, or on-premises over Direct Connect/VPN.
- **No content-based routing** — the NLB (like the CLB) can't read paths, hosts, or headers.
- **Preserves the client source IP** by default — targets see the real client, no header tricks needed.
- **Required as the front of a PrivateLink endpoint service** — when you expose your app privately to other VPCs, an NLB (or ALB behind an NLB) sits in front. (More in Section 6.)

### GLB — the security-appliance plumber (Layer 3)

The Gateway Load Balancer has exactly **one job**: transparently push all traffic **through a fleet of third-party security appliances** — intrusion detection/prevention systems (IDS/IPS), next-gen firewalls, deep packet inspectors — before it reaches your app. It's a "bump in the wire": traffic goes in one side, through the appliances, out the other, and nobody has to change IP addresses.

- Uses the **GENEVE protocol on port 6081** (a recognizable exam factoid).
- Keyword mapping is mechanical: *"inspect traffic with third-party / partner security appliances"* → **GLB**. Every time.

### CLB — the retired host

Classic Load Balancer is the legacy generation (built for the long-retired **EC2-Classic** network). It has no modern superpower — no content routing and **no SNI** (one certificate per CLB, so many domains would need a multi-name **SAN** certificate). **On the exam, CLB is always the wrong answer.** Done.

## Shared ELB features worth points

- **Cross-zone load balancing**: without it, each LB node only sends traffic to targets in *its own* AZ — if AZ-a has 2 instances and AZ-b has 8, the AZ-a pair gets hammered. Cross-zone spreads evenly across ALL targets in ALL AZs. **ALB: on by default, free. NLB: off by default, inter-AZ data charges apply when enabled.**
- **Connection draining / deregistration delay**: when a target is removed (or ASG scales in), the LB stops NEW requests but lets in-flight requests **finish gracefully** (default 300s). *"Users get errors during scale-in"* → tune deregistration delay.
- **SNI (Server Name Indication)**: lets one load balancer host **multiple TLS certificates** — the client says which hostname it wants during the TLS handshake, and the LB serves the matching cert. *"Host many HTTPS domains on one ALB"* → SNI. ALB and NLB support it; CLB doesn't.
  - **SAN vs SNI**: **SAN (Subject Alternative Name)** = *many domain names inside ONE certificate* — adding a domain means **reissuing** the cert. **SNI** = *many separate certificates behind ONE listener* — add a domain by just adding its cert. *"Add domains without reissuing certificates"* → **SNI**.
- **TLS termination**: the LB decrypts HTTPS itself (certificate lives on the LB, usually from ACM) and can talk plain HTTP to targets — offloading crypto work from your instances. (TLS = Transport Layer Security, the encryption behind the "s" in https.)
- **Access logs**: per-request detail (time, client IP, latencies, request path, response code) — **disabled by default**; when enabled, the LB writes **compressed log files to an S3 bucket you choose**. *"Analyze traffic patterns / troubleshoot requests to the LB"* → enable **ELB access logs**.
- **What an ELB can't do** (popular wrong answers):
  - **Span Regions** — every load balancer lives in **one Region**; multi-Region distribution is **Route 53** or **Global Accelerator**.
  - **Throttle / rate-limit requests** — that's **API Gateway** (or WAF rate-based rules).
  - **Reduce latency from distant clients** — it balances, it doesn't move you closer; that's **CloudFront / Global Accelerator**.

## Auto Scaling Groups

An ASG is a rule that says: "keep a fleet of instances alive, sized between these bounds, built from this recipe."

```
   Launch Template  ──►  ┌──────────── ASG ────────────┐
   (AMI, type, SG,       │  min: 2   desired: 4  max: 10│
    user data, key)      │  [EC2] [EC2] [EC2] [EC2]     │
                         │   AZ-a   AZ-a   AZ-b   AZ-b  │
                         └──────────────┬───────────────┘
                                        ▲
                             ELB spreads traffic, health-checks
```

- **Launch template** = the recipe (AMI, instance type, security group, user data). Launch *configurations* are the legacy version — prefer templates:

  | | Launch Template | Launch Configuration (legacy) |
  |---|---|---|
  | Editable? | **Versioned** — create new versions, pick default/latest | **Immutable** — must create a new one and swap it onto the ASG |
  | Mixed instance types + **On-Demand AND Spot** in one ASG | ✅ yes | ❌ no |
  | Per ASG | one template (any version) | only **one** at a time |
  | Status | current, recommended | legacy — no new instance types/features |

  *"One ASG provisioning across multiple instance types with both On-Demand and Spot"* → **launch template** (mixed instances policy).
- **min / desired / max**: the ASG always steers actual count toward **desired**, clamped between min and max. Scaling policies work by changing desired.
- If an instance dies, the ASG **replaces it automatically** — self-healing for free.
- **What an ASG is NOT**: it **can't span Regions** (it spans AZs within one Region), it **doesn't distribute traffic** (that's the ELB), it **doesn't cut latency** by itself, and it's **too slow for bursts lasting seconds** — new instances take minutes to boot. Second-level spikes → **pre-provision**, buffer with **SQS**, or use **Lambda**.
- **Attaching an existing instance** to an ASG requires that the instance is **running**, its **AMI still exists**, it's **not in another ASG**, it's in **one of the ASG's AZs**, and (if the ASG has a load balancer) it's in the **same VPC** as the LB/target group.

### Scaling policies — match the keyword

| Policy | What it does | Exam keyword |
|---|---|---|
| **Target Tracking** | "Keep this metric at this value" (e.g., CPU at 40%) — AWS does the math | **Simplest**, "maintain X%" |
| **Step Scaling** | Add/remove N instances at metric thresholds you define | Fine-grained thresholds, **multiple adjustments** by alarm severity, sudden spikes |
| **Simple Scaling** | One CloudWatch alarm → **one fixed adjustment** (e.g., CPU > 70% → +1), then **waits out the cooldown** | Basic, single adjustment (older; Step/Target preferred) |
| **Scheduled** | Scale at known times | "**every Monday 9am**", "month-end batch", predictable |
| **Predictive** | Machine learning forecasts load and scales **ahead** of it | Recurring patterns, "proactively" |

- **Scheduled actions** set new min/desired/max at a time — e.g., traffic climbs **Wednesday**, stays high **Thursday**, drops **Friday** → one action to scale out before Wednesday, one to scale in Friday. **Predictive scaling assumes a homogeneous ASG** (all instances of equal capacity).
- **Target tracking** is also the fix for an ASG that's **over-provisioned** — it scales in as well as out to hold the target.
- **Suspend / Resume processes**: temporarily pause ASG processes (`Launch`, `Terminate`, `HealthCheck`, `ReplaceUnhealthy`, `AZRebalance`, …) — e.g., to troubleshoot an instance without the ASG replacing it — then resume. (Or move the instance to **Standby**.)
- **Custom metrics**: **memory isn't a default EC2 metric** — to scale on memory, install the **CloudWatch agent** to publish it, then scale on that custom metric. For time-sensitive queue work, CPU is the wrong signal; scale on a queue metric like **`ApproximateAgeOfOldestMessage`** or backlog per instance.

- **Warm-up / cooldown** (default **300 seconds**, configurable): after a scaling action, the ASG waits before launching or terminating more — so it doesn't count a booting instance as "still overloaded" and over-scale. *"ASG launches too many instances in bursts"* or *"scales out and in several times within an hour"* → tune the **cooldown/warm-up**.

### Lifecycle hooks: pause a launch or a termination

A **lifecycle hook** holds an instance in a **wait state** (default 1 hour, extendable) so you can run custom actions, then you **complete the lifecycle action** (or the timeout does) and it proceeds:

| Transition | States |
|---|---|
| Scale-out (launch hook `EC2_INSTANCE_LAUNCHING`) | `Pending` → **`Pending:Wait`** → `Pending:Proceed` → `InService` |
| Scale-in / health-check failure (terminate hook `EC2_INSTANCE_TERMINATING`) | `Terminating` → **`Terminating:Wait`** → `Terminating:Proceed` → `Terminated` |
| Standby | `InService` → `EnteringStandby` → `Standby` → back via `Pending` |
| Detach | `InService` → `Detaching` → `Detached` |

- **Launch hook** → install software, pull config, register with an external system **before** traffic arrives.
- **Terminate hook** → **download logs, take a final backup, drain work** before the instance is gone.

**THE trap:** *"Download log files from instances before they're terminated during scale-in"* → **lifecycle hook (terminating)**, NOT a scheduled action — scheduled actions only change capacity, they can't run anything on the instance.

### THE health-check trap (this WILL be on your exam)

By default, an ASG uses **EC2 status checks only** — is the VM itself running? But an instance can be perfectly *running* while the app on it is crashed, hung, or returning 500s. The ASG shrugs: "VM's alive, looks fine to me."

THE trap: *"the load balancer marks instances unhealthy but the ASG never replaces them"* → **enable ELB health checks on the ASG**. Then the ASG trusts the LB's application-level verdict and terminates + replaces app-dead instances. Recommended setup when an ALB fronts the ASG: use the **ALB health check for both** routing and replacement.

### The ASG + SQS pattern

Classic decoupling architecture: workers in an ASG consume jobs from an SQS queue. Scale on the queue metric — ideally a **custom metric of backlog per instance** (`ApproximateNumberOfMessagesVisible` ÷ instance count) with target tracking. *"Scale workers based on pending jobs"* → **SQS queue depth drives the ASG**, not CPU.

### Termination policy (scale-in: who dies first?)

The default termination policy, step by step:

1. Pick the **AZ with the most instances** (to **keep AZs balanced**). If there's a tie, pick an AZ at random among them.
2. Within it, terminate the instance with the **oldest launch template/configuration**.
3. Still tied → the instance **closest to the next billing hour** (a **legacy** rule from hourly billing; with per-second billing it rarely matters).
4. Still tied → **random**.

You mostly just need to know: *default scale-in keeps AZs balanced and retires the oldest config first.* Instances in **Standby** or with **scale-in protection** are skipped.

## The layered HA picture

Two different tools survive two different disasters:

```
Route 53 (DNS)  ──►  survives a REGION dying   (DNS failover — minutes, TTL-bound)
     │
     ▼
   ELB          ──►  survives an INSTANCE dying (in-path, near-instant rerouting)
     │
     ▼
   ASG          ──►  REPLACES the dead instance (self-healing capacity)
```

**ELB is fast, in-path, within a region. Route 53 failover is DNS-based, slower, across regions.** Serious architectures use both — that's the layered high-availability answer the exam loves.

## Question patterns

> *"Route `/api/*` to one set of servers and `/images/*` to another"* → **ALB path-based routing** (only L7 sees URLs)

> *"UDP-based multiplayer game needs low latency and a static IP"* → **NLB** (ALB can't do UDP or static IPs)

> *"Inspect all traffic with a third-party firewall/IDS appliance fleet"* → **Gateway Load Balancer** (GENEVE 6081, bump-in-the-wire)

> *"LB marks instances unhealthy, but ASG doesn't replace them"* → **enable ELB health checks on the ASG** (default is EC2 status checks only)

> *"Payroll traffic spikes every month-end at a known time"* → **Scheduled scaling** (predictable = scheduled)

> *"Keep average CPU at 40% with minimal configuration"* → **Target Tracking** ("keep metric at value" + "simplest")

> *"Serve many HTTPS domains with different certificates on one ALB"* → **SNI** (multiple TLS certs, one listener)

> *"Corporate clients must whitelist fixed IP addresses for your load balancer"* → **NLB with Elastic IPs** (or Global Accelerator in front of an ALB)

> *"App behind ALB needs the original client IP"* → **X-Forwarded-For header** (NLB would preserve it natively)

> *"Scale workers based on the number of unprocessed jobs"* → **ASG scaling on SQS queue depth** (backlog per instance)

> *"Millions of TCP requests per second, extreme performance"* → **NLB** ("millions" + "ultra-low latency" = L4)

> *"Send 10% of traffic to the new version behind the same ALB"* → **Weighted target groups** on a listener rule

> *"Partners allow-list our existing public IP range; front the app with it"* → **NLB with BYOIP Elastic IPs** (ALB can't take an EIP — put the ALB behind the NLB)

> *"Add new HTTPS domains without reissuing the certificate"* → **SNI** with separate certs (SAN = one cert, reissue per domain; CLB has no SNI)

> *"Capture client IPs, latencies, and paths for every request to the LB"* → **Enable ELB access logs → S3** (off by default)

> *"Collect logs from instances before scale-in terminates them"* → **Lifecycle hook on termination** (`Terminating:Wait`), not a scheduled action

> *"One ASG mixing several instance types with On-Demand and Spot"* → **Launch template** (launch configurations can't)

> *"ASG scales out and in repeatedly within the hour"* → **Increase the cooldown** (default 300s)

> *"Scale on memory utilization"* → **CloudWatch agent custom metric** + scaling policy (memory isn't a default metric)

> *"Distribute traffic across two Regions with one load balancer / one ASG"* → **Not possible** — ELB and ASG are single-Region; use **Route 53** or **Global Accelerator**

> *"Traffic spikes last only a few seconds"* → **ASG is too slow** — pre-provision, buffer with SQS, or go serverless

## Pocket card

| Keyword | Answer |
|---|---|
| Path / host / header routing | ALB |
| HTTP, microservices, containers, Lambda target | ALB |
| WAF on a load balancer | ALB (L7 only) |
| UDP, extreme performance, millions req/s | NLB |
| Static IP / Elastic IP / whitelisting | NLB (or Global Accelerator) |
| PrivateLink endpoint service front | NLB |
| Third-party security appliances, GENEVE 6081 | GLB |
| Classic Load Balancer | Wrong answer |
| Multiple TLS certs, one LB | SNI |
| Errors during scale-in | Deregistration delay (draining) |
| Uneven traffic across AZs | Cross-zone LB (ALB free/on, NLB paid/off) |
| Client IP behind ALB | X-Forwarded-For |
| "Keep CPU at X%" simply | Target Tracking |
| Known time spikes | Scheduled scaling |
| ML-forecasted scaling | Predictive scaling |
| ASG ignores app-level failures | Enable ELB health checks on ASG |
| Scale on job backlog | SQS queue depth metric |
| Instance-level failover | ELB (in-path, instant) |
| Region-level failover | Route 53 (DNS, slower) |
| Route by HTTP method / source IP CIDR | ALB listener rules |
| Rules evaluated how? | Priority order; listener = protocol + port only |
| Canary / blue-green on one ALB | Weighted target groups |
| New target needs gradual ramp-up | Slow start mode |
| Request-level logs | ELB access logs → S3 (off by default) |
| EIP on an ALB | Not possible → NLB (EIP) in front |
| Use own trusted IP range on LB | NLB + BYOIP |
| NLB IP targets | any private IP; peered VPC (even cross-Region) |
| Many domains, ONE certificate | SAN |
| Many certificates, ONE listener | SNI (not on CLB) |
| LB across Regions | Not possible (single-Region) |
| Throttle / rate-limit requests | API Gateway, not ELB |
| Multiple types + On-Demand + Spot in ASG | Launch template |
| Launch configuration | Legacy, immutable |
| Single fixed adjustment, waits for cooldown | Simple scaling |
| Pause ASG replacing instances | Suspend processes / Standby |
| Run actions before launch completes / before terminate | Lifecycle hooks (`Pending:Wait` / `Terminating:Wait`) |
| Scale in/out several times per hour | Cooldown (300s default) |
| Scale on memory | CloudWatch agent custom metric |
| Time-sensitive queue scaling | `ApproximateAgeOfOldestMessage` / backlog per instance |
| Scale-in victim | AZ with most → oldest template/config → (legacy) billing hour → random |
| Attach existing instance | running, AMI exists, not in another ASG, same AZs/VPC |
| ASG across Regions / sub-second bursts | No |

One layer down from the load balancer sits the network it all lives in — subnets, gateways, and firewalls — which is exactly where Section 6 (VPC) picks up.
