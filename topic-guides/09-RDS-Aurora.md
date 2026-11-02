# Section 9: RDS & Aurora

## The idea

Running your own database server means patching the OS, applying engine updates, taking backups at 2 a.m., and rebuilding everything when the hardware dies. **RDS (Relational Database Service) = AWS runs the database for you.** You pick an engine — **MySQL, PostgreSQL, MariaDB, Oracle, or SQL Server** — and AWS handles the machinery underneath.

The price of that convenience: **you get NO OS access**. You can't SSH in, can't install custom extensions at the OS level, can't tweak the engine binaries. If a question demands **custom engine configuration or OS-level access**, RDS is out — the answer is **database on EC2** (full control, all the toil) or **RDS Custom** (a halfway house for Oracle/SQL Server).

Now for **THE core distinction — the most-tested database fact on the entire exam.** RDS has two features that both involve "extra copies of your database," and they exist for completely different reasons. Think of your car:

- **Multi-AZ is the spare tire.** It exists for the day something goes wrong. You never drive on it during normal life.
- **Read Replicas are extra checkout lanes at the supermarket.** They exist to serve more customers at once, every ordinary day.

| | **Multi-AZ** (availability) | **Read Replicas** (performance) |
|---|---|---|
| Replication | **Synchronous** (standby is always exactly current) | **Asynchronous** (slight lag) |
| Where | Standby in **another AZ** | **Same AZ, cross-AZ, or cross-REGION** |
| How many | 1 standby | **Up to 15** |
| Can you read from it? | **NO — ZERO reads from the standby** | **Yes — that's the whole point** (read-only endpoints) |
| Failover | **Automatic, 60–120 seconds**, via **DNS flip** (same endpoint, new machine behind it) | **None automatic — manual promotion only** |
| Solves | AZ failure, hardware death | Read-heavy workloads, reporting |

**THE trap:** *"use the Multi-AZ standby to serve read traffic"* → **impossible**. The standby is invisible until failover — the spare tire stays in the trunk.

**THE trap (mirror image):** *"read replica provides automatic failover"* → **no**. Promotion is a **manual** decision — which also makes a cross-region replica a decent **budget DR** plan, just not an automatic one.

And note: **production uses BOTH** — Multi-AZ for surviving failures, replicas for scaling reads. They're not competitors.

### The full three-way: Multi-AZ vs Multi-Region vs Read Replicas

| | **Multi-AZ** | **Multi-Region** (e.g. Aurora Global DB) | **Read Replicas** |
|---|---|---|---|
| Main purpose | **High availability** | **Disaster recovery + local read performance** | **Scalability** (reads) |
| Replication | **Sync** (non-Aurora); **async** (Aurora) | **Async** | **Async** |
| Active instances | **Primary only** (non-Aurora); **all active** (Aurora) | **All regions readable** | **All replicas readable** |
| Backups | Taken **from the standby** (non-Aurora); from **shared storage** (Aurora) | Per region | **None by default** |
| Span | ≥2 AZs in **one region** | Each region can itself be Multi-AZ | Within an AZ, cross-AZ, or cross-Region |
| Engine upgrades | On the **primary** (non-Aurora); **all instances together** (Aurora) | Independent per region (Aurora: together) | **Independent of the source** (Aurora: together) |
| Failover | **Automatic** to standby (non-Aurora) / to a replica (Aurora) | Aurora can **promote a secondary region** to master | **Manual promotion** to a standalone DB (non-Aurora) / to primary (Aurora) |

- **How Multi-AZ failover actually works:** RDS **flips the endpoint's CNAME** to the standby — the app keeps the same hostname. Automatic triggers: **loss of the primary AZ, loss of network, compute failure, storage failure**.
- **Read replicas** exist for **MySQL, MariaDB, PostgreSQL, Oracle, SQL Server — and Aurora**. Cross-region replication runs over an **encrypted, public-key channel**. Lag: **seconds on RDS**, **milliseconds (<1s) on Aurora**.
- **"Managed", not "fully managed" / not serverless:** RDS still makes **you** pick instance size, **backup window**, and **maintenance (patch) window**. *"No servers to manage at all"* points to DynamoDB / Aurora Serverless, not RDS.

## Backups & encryption

- **Automated backups** → enable **PITR (Point-In-Time Recovery)**, retention **maximum 35 days**. Deleted when the instance is deleted.
- **Manual snapshots** → kept **forever**, until you delete them. **"Retain backups for 5 years / 7 years / compliance" → manual snapshot**, always — 35 days is the wall automated backups can't cross. The managed alternative for >35 days: an **AWS Backup plan** (e.g. daily backups, retained 90 days / 7 years) does the scheduling and expiry for you.
- **Snapshots can be copied cross-region** (cheap DR). Exporting snapshot data **to S3 is a manual "export" action** — automated snapshots don't land in S3 by themselves.
- **MySQL: use InnoDB, not MyISAM.** PITR and snapshot restore depend on crash-recoverable storage; **MyISAM has no reliable crash recovery**, so restores can be inconsistent. MyISAM only makes sense for heavy full-text search.

**Encryption is a birth decision.** You can only encrypt an RDS database **at creation**. To encrypt an existing unencrypted database, do the snapshot dance (this question is essentially guaranteed):

```
unencrypted DB → snapshot → COPY the snapshot (enable encryption) → restore from encrypted copy → repoint the app
```

You cannot flip encryption on in place, and you cannot encrypt the original snapshot directly — you encrypt the **copy**.

## RDS Proxy

Databases hate being swarmed. Every connection costs memory, and **Lambda** — which can scale to thousands of concurrent executions in seconds — will happily open thousands of connections and knock your database over. **RDS Proxy = a connection pool** that sits in front of RDS, letting thousands of clients share a small, warm set of database connections.

- **Lambda + RDS = RDS Proxy. Always.** If those two appear in the same sentence with "too many connections" or "connection errors," you're done reading.
- Bonus: the proxy also **shrinks failover time** (it holds client connections and re-routes them, instead of everyone re-resolving DNS).
- Keyword generalization: **"database connection exhaustion"** from *any* fleet (Lambda, containers, autoscaled EC2) → **RDS Proxy**. It **preserves application connections during failover** and routes them to the new primary.

Also worth one neuron: **storage autoscaling** — RDS can grow its storage automatically when it runs low ("database keeps running out of disk with unpredictable growth" → enable storage autoscaling).

## Security & monitoring

- **Network lockdown:** put the DB in a **private subnet** (app behind ALB + Auto Scaling), and make the **DB security group's inbound rule reference the app/EC2 security group** as its source — never IP ranges (SG referencing, Section 6).
- **IAM database authentication** (MySQL & PostgreSQL): token instead of password, over SSL, managed centrally in IAM — full detail in Section 1. (Raw STS tokens on their own are **not** the RDS answer.)
- **RDS events** (via SNS/EventBridge) cover **operational** events only — instance, parameter group, security group, snapshot changes. Reacting to **row-level INSERT/UPDATE/DELETE** needs engine-native features (triggers / stored procedures calling Lambda), not RDS event subscriptions.

**Enhanced Monitoring vs CloudWatch metrics:**

| | **CloudWatch (standard)** | **Enhanced Monitoring** |
|---|---|---|
| Source | The **hypervisor** | An **agent on the instance** |
| Sees | CPUUtilization, DB connections, FreeableMemory, Read/Write IOPS | **OS-level** metrics: **per-process CPU% and memory%**, RDS processes, RDS child processes, OS processes |

**THE trap:** *"see how much CPU/memory each process or thread uses"* → **Enhanced Monitoring**. Keywords **"OS", "process", "thread", "child process"** = Enhanced Monitoring; plain CloudWatch can't see inside the instance.

## Aurora

Aurora is AWS's own cloud-native engine, **compatible with MySQL and PostgreSQL** (your app connects the same way). The architectural trick: Aurora **separates compute from storage**.

```
   [Writer node]  [Reader]  [Reader] ...   ← compute: disposable, pluggable
        │            │         │
   ═════╧════════════╧═════════╧═════════
     Shared storage: 6 copies across 3 AZs, self-healing,
     auto-grows to 128 TB
```

Because every node plugs into the **same shared storage**, a failed writer is replaced by simply promoting a reader that already sees all the data:

- **Failover in under 30 seconds** (vs 60–120s for RDS Multi-AZ)
- **Up to 15 replicas with ~millisecond lag** (vs async seconds on RDS)
- **Storage auto-grows to 128 TB** — no provisioning
- **Two endpoints**: the **writer endpoint** (points at the current writer, survives failover) and the **reader endpoint** (load-balances across all replicas). Apps send writes to one and reads to the other — never hardcode instance addresses.
- Also: **continuous backup to S3 with PITR**, storage across **3 AZs**. Aurora is **not** an in-memory DB, and it handles **OLTP (ACID transactions) plus complex queries**. Aurora is **"provisioned"** (fixed instance sizes, predictable load) unless you choose Serverless (infrequent / intermittent / sporadic load).

**Aurora endpoints cheat sheet:**

| Endpoint | Use it for |
|---|---|
| **Cluster (writer)** | All **writes** + DDL (and reads) — always points at the current primary |
| **Reader** | **Load-balanced read-only** traffic across replicas |
| **Custom** | Route a workload to a **specific subset** of replicas (e.g. bigger instances for analytics) |
| **Instance** | Connect to **one exact DB instance** — troubleshooting / fine-grained tuning |

- **Aurora failover** = the cluster endpoint's **CNAME is flipped** to a promoted replica (not an A-record change). **No replica?** Aurora tries to create a new primary in the **same AZ first**, then another AZ (slower).
- **Parallel Query** pushes processing down to the storage layer to speed up **one big analytical query** — it does **NOT** load-balance traffic.
- **Babelfish for Aurora PostgreSQL** understands **T-SQL / SQL Server wire protocol** → move a **SQL Server app** to Aurora PostgreSQL with **minimal code changes**.

**Aurora's special features — feature → scenario:**

| Feature | The scenario it answers |
|---|---|
| **Serverless v2** | **Spiky, unpredictable, or idle** workloads — dev/test databases used a few hours a day, capacity scales itself, pay for what you use |
| **Global Database** | **Cross-region DR with RPO ~1 second, RTO <1 minute**, plus local low-latency reads on other continents. (A plain cross-region read replica = slower replication, slower promotion — the budget distractor) |
| **Cloning** | **Copy-on-write instant copy** of a production database — a full-size staging/test copy in minutes without duplicating storage |
| **Backtrack** | **Rewind the database in place** (Aurora MySQL) — *"undo an accidental delete/bad migration FAST, without restoring from backup"*, no new instance, no restore wait |

RPO (Recovery Point Objective) = how much data you may lose; RTO (Recovery Time Objective) = how long until you're back. Aurora Global Database's "~1s / <1min" pair is a memorize-it number.

## Question patterns

> *"Database must survive an AZ failure with no manual intervention"* → **Multi-AZ** ("survive failure" + "automatic" = spare tire, 60–120s DNS flip).

> *"Reporting/analytics queries are slowing down the production database"* → **Read Replica** (offload reads to a checkout lane — but if the queries are the *same ones repeatedly*, **ElastiCache** wins; replica is for **diverse/complex** queries).

> *"Lambda functions are exhausting database connections"* → **RDS Proxy** (Lambda + RDS = Proxy, every time).

> *"Encrypt an existing unencrypted RDS database"* → **snapshot → copy with encryption → restore** (encryption is creation-time only; this is the snapshot dance).

> *"Global application needs cross-region DR with less than 1 minute recovery"* → **Aurora Global Database** (RPO ~1s, RTO <1min — nothing else touches it).

> *"Dev database sits idle nights and weekends; minimize cost"* → **Aurora Serverless v2** (spiky/idle/unpredictable = serverless).

> *"Need a full copy of the production database for testing, quickly and cheaply"* → **Aurora Cloning** (copy-on-write = instant, near-free until it diverges).

> *"Developer ran a bad DELETE; restore the database to 5 minutes ago as fast as possible"* → **Aurora Backtrack** (rewind in place — no restore, no new instance).

> *"Compliance requires database backups kept for 7 years"* → **Manual snapshots** (automated backups cap at 35 days).

> *"Application needs OS-level access / a custom database engine"* → **EC2** (or RDS Custom for Oracle/SQL Server) — plain RDS gives no OS access.

> *"Monitor CPU and memory used by each process/thread on the RDS instance"* → **Enhanced Monitoring** (agent on the instance; CloudWatch only sees hypervisor-level metrics).

> *"Run analytics on a subset of Aurora replicas without touching the rest"* → **Aurora custom endpoint**.

> *"Speed up a single complex analytical query on Aurora MySQL"* → **Parallel Query** (not a load balancer — the reader endpoint does that).

> *"Migrate a SQL Server application to Aurora with minimal code changes"* → **Babelfish for Aurora PostgreSQL** (speaks T-SQL).

> *"Keep application connections alive through a database failover"* → **RDS Proxy** (holds connections, routes to the new primary).

## Pocket card

| Keyword in question | Answer |
|---|---|
| survive AZ failure, auto-failover | **Multi-AZ** (sync, 60–120s, DNS flip) |
| standby serves reads | **TRAP — never** |
| scale reads, offload reporting | **Read Replica** (async, up to 15, manual promotion) |
| replica auto-failover | **TRAP — promotion is manual** |
| same queries over and over | ElastiCache (not a replica) |
| Lambda + RDS connections | **RDS Proxy** |
| backups > 35 days / "retain X years" | **Manual snapshot** |
| restore to any point in time (≤35 days) | Automated backups / PITR |
| encrypt existing DB | **Snapshot → copy-encrypted → restore** |
| OS access / custom engine | EC2 or RDS Custom |
| failover <30s, 15 low-lag replicas, 128TB autogrow | **Aurora** |
| spiky / idle / unpredictable load | **Aurora Serverless v2** |
| cross-region DR, RPO ~1s, RTO <1min | **Aurora Global Database** |
| instant prod copy for staging | **Aurora Cloning** |
| undo mistake fast, no restore | **Aurora Backtrack** |
| "OS", "process", "thread", "child process" metrics | **Enhanced Monitoring** |
| route to a subset of Aurora replicas | **Custom endpoint** (one exact node = instance endpoint) |
| one heavy analytic query faster | **Aurora Parallel Query** |
| SQL Server app → Aurora, minimal changes | **Babelfish** |
| MySQL engine for PITR/snapshots | **InnoDB** (not MyISAM) |
| backups >35 days, managed schedule | **AWS Backup plan** (or manual snapshots) |

You now know how to keep the database standing and fast — but when the exam's read traffic is the *same* hot data thousands of times per second, even fifteen replicas is the wrong answer, and that's where caching with ElastiCache takes over.
