# Section 36: Classic Traps & Must-Know Combos

## The idea

The SAA-C03 isn't trying to see if you've *heard* of services — it's checking whether you know where the **tripwires** are. Think of this section as the **map of the minefield**: every trap below is a wrong answer that *sounds* right and appears on the exam over and over, paired with the truth that defuses it. Walk this list twice before exam day and you'll feel the wires before you step on them.

## The greatest-hits trap list

| THE trap | The truth |
|---|---|
| "Read from the RDS Multi-AZ standby to offload queries" | **NO** — the standby is invisible; use **read replicas** for reads |
| "CNAME record at the zone apex (example.com)" | CNAMEs can't sit at the apex — use an **Alias record** |
| "Add a deny rule to the security group" | Security groups have **no deny rules** (allow-only, stateful) — deny lives in **NACLs** |
| "Private subnet reaches S3 via NAT Gateway" | Works but costs money — **Gateway VPC Endpoint** is free and private |
| "Run the 20-minute job in Lambda" | Lambda caps at **15 minutes** — use Fargate/Batch/Step Functions |
| "Mount EFS on Windows instances" | EFS is Linux-only — Windows shared storage = **FSx for Windows File Server** |
| "Snowball imports directly into Glacier" | No — Snowball lands in **S3**, then a **lifecycle policy** moves it to Glacier |
| "A↔B and B↔C peering lets A reach C" | Peering is **non-transitive** — need **Transit Gateway** (or direct A↔C peering) |
| "Encrypt the existing unencrypted RDS/EBS in place" | Impossible in place — **snapshot → copy snapshot with encryption → restore** |
| "KMS for FIPS 140-2 Level 3 / single-tenant keys" | That's **CloudHSM** (KMS is Level 2*, multi-tenant) |
| "Shield Standard stops layer-7 application attacks" | Standard is L3/L4 only — L7 protection = **WAF / Shield Advanced** |
| "Apply an SCP to restrict the management account" | SCPs **never affect the management account** |
| "Replay DynamoDB Streams data from last month" | Streams keep **24 hours** — longer retention → **Kinesis Data Streams** |
| "Give the ALB a static IP" | ALBs have no static IPs — **NLB** has static/Elastic IPs (or NLB in front of ALB) |
| "Add an LSI to the existing DynamoDB table" | **LSIs only at table creation** — after creation, add a **GSI** |
| "Accelerate UDP traffic with CloudFront" | CloudFront is HTTP(S) only — UDP/TCP acceleration = **Global Accelerator** |
| "Parameter Store rotates the DB password automatically" | No native rotation — automatic rotation = **Secrets Manager** |
| "One NAT Gateway serves all AZs, highly available" | AZ failure kills it — deploy **one NAT Gateway per AZ** |
| "SNS alone guarantees consumers never miss messages" | SNS doesn't persist for offline consumers — durable fan-out = **SNS → SQS** |
| "Direct Connect is encrypted because it's private" | **Not encrypted** — run a **VPN over DX** for encryption |
| "Auto Scaling absorbs a spike that lasts a few seconds" | New instances take **minutes** to boot, so ASG is **NOT suitable** for second-level bursts. Buffer the spike with **SQS**, or use Lambda. |
| "Stretch one ASG/ELB across two Regions to cut latency" | ELB and ASG are **single-Region**. Use **Route 53** latency routing or **Global Accelerator** for multi-Region. |
| "Multi-AZ will scale our reads" | Multi-AZ is for **HA/failover only**. Read scaling needs **Read Replicas** or Aurora Replicas. |
| "Throttle clients at the load balancer" | ELB cannot throttle. **API Gateway** (usage plans/throttling) or **WAF rate-based rules** can. |
| "CloudWatch alarm emails ops via SES" | Alarms notify through **SNS**. SES is for application, bulk or marketing email. |
| "Order Direct Connect for a one-time bulk transfer next week" | DX takes **weeks to months** to set up. One-time bulk transfer → **Snowball** or **DataSync** over the internet/VPN. |
| "Firewall Manager / Security Hub / Trusted Advisor will block the attack" | These only **manage, aggregate or advise**. Blocking is done by **WAF, Shield, NACL or Network Firewall**. |
| "Attach a security group to the S3 bucket" | S3 has no security groups. Control access with **bucket policies**, **VPC endpoint policies** or Block Public Access. |
| "Run session state or OLTP on Redshift" | Redshift is an **OLAP** warehouse. Use **DynamoDB or ElastiCache** for sessions and **RDS/Aurora** for OLTP. |

## Must-know combos (the exam's favorite Lego sets)

| Need | The combo |
|---|---|
| Serverless web app | **CloudFront + S3 (static) + API Gateway + Lambda + DynamoDB** |
| Reliable fan-out | **SNS → multiple SQS queues** (durable, each consumer own queue) |
| Global highly available DB | **Aurora Global Database** (SQL) / **DynamoDB Global Tables** (NoSQL) |
| Protect a web app | **CloudFront + WAF + Shield + ALB** |
| Real-time streaming pipeline | **Kinesis Data Streams → Lambda → DynamoDB/S3** |
| Analytics on data lake | **S3 + Glue (catalog/ETL) + Athena (query) + QuickSight (dashboards)** |
| Migration toolkit | **DataSync (files) + DMS (databases) + DX/Snow family (transport)** |
| DR stack | **Route 53 failover + Aurora Global + S3 CRR** |
| App authentication | **Cognito User Pools (login) + Identity Pools (AWS credentials)** |
| Classic 3-tier web app | **Web tier**: ALB in **public** subnets with an ASG behind it. **App tier**: EC2/containers in **private** subnets. **DB tier**: RDS Multi-AZ in **private** subnets. Only the load balancer faces the internet. |

### Design keyword → architectural goal

| Keyword in the stem | What AWS wants to see |
|---|---|
| **Highly available** | Multi-AZ, redundancy, automatic failover (ASG across AZs, RDS Multi-AZ, one NAT GW per AZ) |
| **Fault tolerant / survive a Region failure** | Multi-Region (Route 53 failover, Aurora Global, DynamoDB Global Tables, S3 CRR) |
| **Decouple** | A queue or topic between components (**SQS**, SNS, EventBridge), so producers and consumers fail and scale independently |
| **Real-time / streaming** | **Kinesis** (or MSK if "Kafka") |
| **Shared file storage** | **EFS** (Linux) / **FSx** (Windows, Lustre) |
| **Low-cost archive** | **S3 Glacier** tiers (Deep Archive for rarely accessed data) |
| **Serverless** | Lambda, Fargate, DynamoDB, API Gateway, S3, Aurora Serverless |
| **Read-heavy / read scalability** | **Read Replicas**, Aurora Replicas, ElastiCache, DAX, CloudFront |
| **Secure / encrypt / least privilege** | IAM roles, KMS, WAF, private subnets plus VPC endpoints |
| **Cost-efficient / MOST cost-effective** | The cheapest option that **still meets every requirement** (Spot, S3 lifecycle, serverless, Savings Plans) |
| **LEAST operational overhead** | The most managed or serverless option (Glue over EMR for ETL, Fargate over EC2) |
| **NOT suitable / which will NOT work** | The question is inverted. Find the option that **breaks** a requirement (wrong Region scope, time limit, protocol). |

### Scenario → service quick-match

| Scenario | Service |
|---|---|
| DB connection exhaustion from many Lambdas | **RDS Proxy** |
| Sudden traffic spikes overwhelm the backend | **SQS** buffer |
| One event → many consumers | **SNS** fan-out (→ SQS for durability) |
| Multi-step workflow with retries and branching | **Step Functions** |
| Multi-Region traffic routing with static IPs | **Global Accelerator** |
| Private access to AWS services from a VPC | **VPC Endpoint** (Gateway for S3/DynamoDB, Interface for the rest) |
| On-prem file server extended to AWS | **Storage Gateway** (File Gateway) |
| Read-heavy relational DB | **Read Replica** |
| Cross-Region relational DR | **Aurora Global Database** |
| Metrics + alarm + notify ops | **CloudWatch + SNS** |
| Application/bulk/transactional email | **SES** |
| Automated, cross-account long-term backup retention | **AWS Backup** |
| ETL with least operational overhead | **Glue** |

## Exam technique (the meta-game)

- **Read the last sentence first** — that's where the actual question and qualifier live; the story above it is scenery.
- **Eliminate two** — almost every question has two obviously wrong answers. Kill them, then compare the survivors.
- **The qualifier decides** between two working answers: **cost** → cheapest that still works; **least operational overhead** → most managed/serverless; **highly available** → Multi-AZ; **survive region failure** → multi-region.
- **~2 minutes per question** (130 min, 65 questions). Stuck at 90 seconds? **Flag it and move on** — later questions often jog your memory.
- **Answer everything.** No penalty for wrong answers; a guess beats a blank.

## Question patterns

> *"Route example.com (apex) to an ALB"* → **Alias record** (CNAME illegal at apex)

> *"Block a specific malicious IP address"* → **NACL deny rule** (security groups can't deny)

> *"Private subnet needs S3 access at no cost"* → **Gateway VPC Endpoint** (NAT Gateway is the paid decoy)

> *"Encrypt an existing unencrypted RDS instance"* → **Snapshot → encrypted copy → restore** ("enable encryption" checkbox doesn't exist)

> *"Fan out orders to inventory, billing, shipping — none may be lost"* → **SNS topic → three SQS queues** (durability per consumer)

> *"Static IPs required by the firewall team for the load balancer"* → **Network Load Balancer** (ALB has none)

> *"Improve performance AND static IPs for global TCP/UDP app"* → **Global Accelerator** (CloudFront can't do UDP)

> *"Rotate database credentials automatically every 30 days"* → **Secrets Manager** (Parameter Store is the decoy)

> *"Traffic surges for 5–10 seconds and requests are dropped; Auto Scaling is already configured"* → **Put SQS in front to buffer** (ASG reacts in minutes, too slow for second-level bursts)

> *"Which architecture is NOT suitable…"* → **find the option that violates a hard limit** (e.g., ELB across Regions, Lambda over 15 min, CNAME at the apex)

> *"Decouple the order service from the slow invoicing service"* → **SQS queue between them** ("decouple" is almost always SQS/SNS)

## Pocket card

| Keyword | Answer |
|---|---|
| Apex domain | Alias record |
| Deny traffic | NACL (never SG) |
| Free S3 access from VPC | Gateway Endpoint |
| >15 minutes | Not Lambda (Fargate/Batch) |
| Windows file share | FSx for Windows |
| Transitive routing | Transit Gateway |
| Encrypt existing volume/DB | Snapshot dance |
| FIPS Level 3 | CloudHSM |
| Static IP load balancer | NLB |
| UDP acceleration | Global Accelerator |
| Auto-rotation | Secrets Manager |
| HA NAT | One per AZ |
| Durable fan-out | SNS → SQS |
| Encrypted DX | VPN over DX |
| Seconds-long spike | SQS buffer (not ASG) |
| Multi-Region load balancing | Route 53 / Global Accelerator (ELB is single-Region) |
| Throttling | API Gateway / WAF rate-based rule |
| Decouple | SQS / SNS |
| Highly available | Multi-AZ |
| 3-tier | ALB public, app + DB private |

Traps mapped, combos memorized — one last sweep remains: the small-but-tested gap-fill services that each show up for one or two easy points.
