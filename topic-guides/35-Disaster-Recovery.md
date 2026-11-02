# Section 35: Disaster Recovery

## The idea

Disaster recovery (DR) answers one question: *when a whole region catches fire, how fast are you back, and how much data did you lose?* Two numbers define everything:

- **RPO — Recovery Point Objective**: maximum acceptable **data loss**. How far back does the tape rewind? If you back up nightly, your RPO is up to 24 hours of lost work.
- **RTO — Recovery Time Objective**: maximum acceptable **downtime**. How long until you're serving customers again?

```
 last backup          DISASTER              back online
──────●───────────────────✖───────────────────────●──────▶ time
      ◀───── RPO ─────────▶◀───────── RTO ────────▶
       (data you lost)        (time you were down)
```

Think of DR strategies as **kinds of spare tires**. Backup & Restore is *no spare — call a tow truck*. Pilot Light is a *space-saver donut in the trunk*. Warm Standby is a *full spare, already inflated*. Active-Active is *a second identical car driving alongside you*. Better spares cost more to carry around; the exam always asks for the **cheapest one that meets the stated RPO/RTO** — the same eliminate-then-cheapest logic you used for S3 storage classes.

## The four strategies

| Strategy | RTO | RPO | Cost | What runs in the DR region |
|---|---|---|---|---|
| **Backup & Restore** | Hours | Hours | $ cheapest | Nothing — backups in S3, rebuild on disaster |
| **Pilot Light** | Tens of minutes | Minutes–seconds | $$ | Core only: **DB continuously replicated, servers off/minimal** |
| **Warm Standby** | Minutes | Seconds | $$$ | **Scaled-DOWN full copy always running** → scale UP on disaster |
| **Multi-Site Active-Active** | ~Zero | ~Zero | $$$$ | Full capacity in both regions, serving live traffic |

Signal phrases:

- "**Minimal DR footprint**, database continuously replicated, compute launched only on disaster" → **Pilot Light** (the pilot flame is lit; the furnace is off).
- "A smaller version of the full environment is **always running**" → **Warm Standby**.
- "**Zero downtime**, both regions active" → **Multi-Site Active-Active**.
- "Lowest cost, RTO of hours is fine" → **Backup & Restore**.

- Multi-Site is also called **"Hot Standby"** — both sites take a share of live traffic.
- Map to Route 53 (see Section 7): **active-active** (Weighted/Latency + health checks, every site serves, no primary/secondary) = Multi-Site; **active-passive** (Failover policy, primary serves, secondary waits) = Pilot Light / Warm Standby.

**THE trap: don't buy a better spare tire than the question asks for.** If RTO is "a few hours," Active-Active is wrong even though it's "better" — it fails the cost qualifier.

## The supporting cast

| Service | Role in DR |
|---|---|
| **Aurora Global Database** | Cross-region replication, **RPO ~1 second, RTO < 1 minute** |
| **DynamoDB Global Tables** | Multi-region, multi-active NoSQL — writes anywhere |
| **S3 Cross-Region Replication (CRR)** | Objects copied to a bucket in another region |
| **AWS Backup** | **Centralized, cross-service backup plans** (EBS, RDS, DynamoDB, EFS…) + **Vault Lock** for immutable backups |
| **Elastic Disaster Recovery (DRS)** | **Continuous block-level replication of servers** (on-prem or EC2) into AWS — cheap DR for lifted servers, RPO seconds / RTO minutes |
| **Route 53 failover routing** | Health check fails → DNS flips traffic to the DR region |
| **DMS** | Database Migration Service — also does ongoing replication between databases |
| **AMI copy** | AMIs are Region-bound — copy them to the DR region ahead of time (see Section 3) |
| **RDS / Redshift cross-region snapshot copy** | Ship DB snapshots to the DR region (Redshift: enable on the cluster with destination region + retention) — Backup & Restore tier |
| **ElastiCache Redis Global Datastore** | Cross-region cache replicas; promote a secondary in a regional outage |

**AWS Backup, a bit deeper:** one console for **backup policies**, **automated cross-region AND cross-account copies** (long-term retention in an isolated account), covering AWS services **plus on-prem VMware and Storage Gateway volumes**. Contrast with **Data Lifecycle Manager (DLM)** = EBS snapshots/AMIs only. (Notes sometimes say "AWS Backup only works on AWS resources" — outdated; hybrid VMware support exists.)

### Database migration with minimal downtime

| Requirement | Approach |
|---|---|
| Migrate with **minimal downtime** | **DMS** (source stays live, full load + CDC) |
| **Ongoing replication** between DBs | **DMS** |
| One-time copy, downtime acceptable | **Snapshot → restore** |
| Promote a read replica to standalone | Works, but **some downtime** at cut-over |
| Change engine / deployment type in place | **Usually not possible** → migrate instead |

- DMS does **homogeneous** (MySQL → MySQL) and **heterogeneous** (Oracle → Aurora) moves; for heterogeneous, **SCT** converts **schemas, stored procedures, foreign keys** first.
- DMS Basic Schema Copy vs SCT is covered in Section 37.

## How to answer any DR question

1. Find the stated **RPO/RTO numbers** (or words like "zero downtime").
2. **Eliminate** strategies that can't meet them.
3. Pick the **cheapest survivor**.

## Question patterns

> *"RTO of 10 minutes, RPO of seconds, keep costs reasonable"* → **Warm Standby** (Active-Active also works but costs more; Pilot Light is too slow)

> *"DR needed at the LOWEST cost; hours of downtime acceptable"* → **Backup & Restore** (cheapest strategy that meets a relaxed RTO)

> *"Application must survive a region failure with zero downtime and zero data loss"* → **Multi-Site Active-Active** (only ~zero RPO/RTO option)

> *"Database continuously replicated to DR region; EC2 launched only during a disaster"* → **Pilot Light** (core data live, compute off)

> *"Centrally manage and automate backups of EBS, RDS, and DynamoDB across the organization"* → **AWS Backup** (one service, backup plans + vault lock)

> *"Cost-effective DR for 200 on-premises servers into AWS"* → **Elastic Disaster Recovery (DRS)** (continuous block replication, pay tiny until failover)

> *"Global relational database with cross-region RPO of ~1 second"* → **Aurora Global Database** (RPO 1s, RTO under a minute)

> *"Automatically route users to the standby region when the primary fails"* → **Route 53 failover routing with health checks**

> *"Keep backups in a separate account for long-term retention, automatically"* → **AWS Backup cross-account copy** (centralized policies)

> *"Migrate a production database to AWS with minimal downtime"* → **DMS** (source stays operational; add SCT if the engine changes)

## Pocket card

| Keyword | Answer |
|---|---|
| Max data loss | RPO |
| Max downtime | RTO |
| Cheapest, RTO hours | Backup & Restore |
| DB replicated, servers off | Pilot Light |
| Scaled-down copy running | Warm Standby |
| Zero RPO/RTO, both live | Multi-Site Active-Active |
| RPO 1s / RTO <1 min relational | Aurora Global Database |
| Multi-region multi-active NoSQL | DynamoDB Global Tables |
| Centralized cross-service backups | AWS Backup (+ Vault Lock) |
| Replicate on-prem servers for DR | Elastic Disaster Recovery (DRS) |
| DNS failover to DR region | Route 53 failover routing |
| Backups in another account | AWS Backup cross-account copy |
| Migrate DB, minimal downtime | DMS (+ SCT if engine changes) |
| One-time DB copy, downtime OK | Snapshot → restore |

You now hold the full toolbox — time to sharpen it against the exam's favorite tricks: the classic traps and must-know combos.
