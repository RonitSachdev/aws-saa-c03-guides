# Section 10: DynamoDB

## The idea

Picture a coat-check counter at a giant stadium. You hand over your coat, you get ticket **#48291**. Later you hand back the ticket and — instantly — your coat appears. The coat-check clerk never *searches* the racks; the ticket number tells her exactly which hook to walk to. It doesn't matter if the stadium holds 500 people or 5 million: one ticket, one hook, one grab. **That's DynamoDB.**

DynamoDB is AWS's **serverless NoSQL database**. Spell that out:

- **Serverless** = you never see, patch, size, or connect to a server. No instance types, no connection pools, no maintenance windows. You just call an API.
- **NoSQL** = data lives as **items** (like rows) with flexible attributes (like columns, but each item can have different ones). No joins, no rigid schema.

Its superpower is the promise on the tin: **single-digit millisecond latency at ANY scale**. Ten requests per second or ten million — same speed. That's the coat-check trick: every lookup goes straight to a hook via a key, never a search.

### DynamoDB vs RDS — the first fork in every question

| Scenario says... | Pick |
|---|---|
| Joins, complex queries, existing SQL app, relational schema | **RDS / Aurora** |
| Massive scale, serverless, key-value lookups, millisecond latency, unpredictable growth | **DynamoDB** |

**THE trap:** *"migrate with no code changes from MySQL"* → that's **RDS/Aurora**, never DynamoDB. NoSQL means rewriting queries.

### Keys and hot partitions

Every table needs a **partition key** (the coat-check ticket — determines which physical partition stores the item), plus an optional **sort key** (orders items *within* a partition, so one customer can have many orders sorted by date).

DynamoDB spreads data across partitions by hashing the partition key. If everyone's key is `country = "USA"`, all traffic slams one partition — a **hot partition** — and you get throttled while the rest of the table sits idle.

**Rule: pick a high-cardinality partition key** (many distinct values: `user_id`, `order_id`), not a low-cardinality one (`status`, `country`, `date`).

```
Good key (user_id):            Bad key (country):
[P1][P2][P3][P4]               [P1][P2][P3][P4]
 ▲▲  ▲▲  ▲▲  ▲▲                ████  .   .   .
 even spread                    hot!  idle idle idle
```

### Capacity modes — same logic as EC2 pricing

- **Provisioned**: you declare read/write capacity up front. **Cheaper for steady, predictable traffic.** Add **auto scaling** to flex within bounds. (This is your Reserved-Instance instinct.)
- **On-Demand**: pay per request, no planning. **Pick for spiky, unpredictable, or brand-new workloads** — flash sales, new apps with unknown traffic. (This is On-Demand EC2 instinct.)

**THE trap:** *"app gets throttled during unpredictable traffic spikes"* → switch to **On-Demand mode**. Don't over-provision.

### RCU / WCU — the exam arithmetic

| Unit | Buys you |
|---|---|
| **1 RCU** | **1 strongly consistent** read/sec, item ≤ 4 KB — or **2 eventually consistent** reads/sec |
| **1 WCU** | **1 write**/sec, item ≤ **1 KB** |

Eventual consistency is half price because it may serve a copy that's a heartbeat stale. **"Must always read the latest write"** → request a **strongly consistent read** (default is eventual).

### Feature zoo → scenario matcher

| Feature | The one-liner |
|---|---|
| **DAX** (DynamoDB Accelerator) | In-memory cache in front of DynamoDB: **microsecond** reads, **API-compatible = ZERO code changes**, works **only** with DynamoDB. (Need caching for anything else, or need code-level flexibility → ElastiCache.) |
| **Global Tables** | **Multi-region ACTIVE-ACTIVE**: users read *and write* locally in every region, DynamoDB replicates. Requires **Streams enabled**. Contrast: **Aurora Global Database = one writer region** (active-passive writes). |
| **Streams** | A **change feed**: every insert/update/delete recorded for **24 hours**, typically triggering **Lambda**. Keyword: *"react to item changes."* |
| **TTL** (Time To Live) | Put an expiry timestamp attribute on items → DynamoDB **auto-deletes them for FREE** (no WCU). Deletion happens within ~**48 hours** of expiry, not the exact second. Classic: session data, temp tokens. |
| **GSI** (Global Secondary Index) | Query the table by a **different attribute** (e.g., by email when the key is user_id). Can be added **ANYTIME**, has its **own capacity**. |
| **LSI** (Local Secondary Index) | Alternate *sort* key, same partition key — but can be created **at table creation ONLY**. **THE trap:** if the table already exists, LSI is the wrong answer; pick **GSI**. |
| **Transactions** | **ACID** across multiple items/tables — all-or-nothing. Costs **2x** the capacity. Keyword: *"atomic"*, *"all succeed or none."* |
| **PITR** (Point-In-Time Recovery) | Continuous backup, restore to any second in the last **35 days**. |

### Two more exam staples

**The serverless poster-child stack** — memorize the chain:

```
User → CloudFront → API Gateway → Lambda → DynamoDB
        (CDN)       (front door)   (code)    (data)
```

Any question asking for a "fully serverless web/API architecture" is assembling this.

**400 KB item limit.** An item can't exceed 400 KB. Storing images/documents? **Put the object in S3, store the S3 pointer (key/URL) in DynamoDB.** This S3-plus-pointer pattern is a recurring correct answer.

## Question patterns

> *"Flash sale causes unpredictable spikes; table throttles"* → **On-Demand capacity mode** (pay-per-request absorbs spikes)

> *"Reduce read latency to microseconds without changing application code"* → **DAX** (API-compatible cache, DynamoDB-only)

> *"Global users need low-latency reads AND writes in every region"* → **Global Tables** (active-active; Aurora Global has only one writer)

> *"Run custom logic whenever items are added or modified"* → **DynamoDB Streams + Lambda** (24-hour change feed triggers functions)

> *"Automatically remove session records after 30 minutes, at no cost"* → **TTL** (free auto-delete, ~48h window)

> *"Table keyed on user_id, but app must also query by email"* → **GSI** (new query attribute, addable anytime — LSI is creation-time-only bait)

> *"Debit one account and credit another — both or neither"* → **DynamoDB Transactions** (ACID, 2x capacity cost)

> *"Store 2 MB documents per record"* → **S3 for the object, DynamoDB holds the pointer** (400 KB item limit)

> *"Application must always see the most recent write"* → **Strongly consistent read** (1 RCU vs 2 eventual reads)

> *"Reporting needs joins across many tables"* → **RDS/Aurora**, not DynamoDB (relational = SQL)


## Pocket card

| Keyword | Answer |
|---|---|
| Serverless NoSQL, key-value, any scale | DynamoDB |
| Joins / complex SQL | RDS or Aurora instead |
| Spiky / unknown traffic | On-Demand mode |
| Steady, predictable traffic | Provisioned (+ auto scaling) |
| Microseconds, no code change | DAX |
| Multi-region active-active | Global Tables (needs Streams) |
| React to item changes | Streams → Lambda |
| Auto-expire items free | TTL |
| Query by another attribute, existing table | GSI (LSI = creation-time trap) |
| Atomic multi-item | Transactions (2x cost) |
| Restore to any second, 35 days | PITR |
| Item > 400 KB | S3 + pointer |
| 1 RCU | 1 strong or 2 eventual reads ≤ 4 KB |
| 1 WCU | 1 write ≤ 1 KB |

DynamoDB gives you millisecond answers forever — but when even milliseconds are too slow, you reach for the in-memory layer, and that's where ElastiCache (Section 11) picks up the story.
