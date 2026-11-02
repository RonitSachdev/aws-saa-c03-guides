# Section 11: ElastiCache

## The idea

Imagine a librarian who keeps getting asked the same question: *"What time do you close?"* The first time, she walks to the back office, checks the policy binder, walks back — thirty seconds. After the hundredth ask, she tapes a sticky note to the front desk: **"We close at 9."** Now every answer takes half a second. She didn't make the binder faster — she stopped consulting it for questions she'd already answered. **That sticky note is a cache.**

A **cache** keeps the answers to repeated questions in **RAM** (memory) instead of making the database work them out again. RAM is roughly **1000x faster** than a disk-based database query — your response times drop from milliseconds to **microseconds**, and your database stops sweating.

**ElastiCache** is AWS's managed cache service. It runs one of two open-source engines for you — **Redis** or **Memcached** — handling patching, monitoring, and failover. One crucial fact up front: **ElastiCache REQUIRES application code changes.** Your app must be written to check the cache first. (Contrast with **DAX**, which is API-compatible with DynamoDB and needs **zero** code changes — a distinction the exam adores.)

The flow your app implements:

```
App request
    │
    ▼
[Check ElastiCache] ──hit──► return in MICROSECONDS ✔
    │
   miss
    │
    ▼
[Query database] ──► get result ──► write into cache ──► return
                                    (next asker gets the sticky note)
```

### Redis vs Memcached — the only table you need

| Capability | **Redis** | **Memcached** |
|---|---|---|
| Persistence (survives restart) | ✔ | ✘ |
| Replication + **Multi-AZ automatic failover** | ✔ | ✘ |
| Backup & restore | ✔ | ✘ |
| **Sorted sets** (leaderboards) | ✔ | ✘ |
| Pub/sub messaging | ✔ | ✘ |
| Multi-threaded, dead-simple | ✘ | ✔ |
| **HIPAA-eligible** (classic exam answer) | ✔ | ✘ |
| **Redis AUTH** password + in-transit encryption | ✔ | ✘ |
| Cross-region replicas (**Global Datastore**) | ✔ | ✘ |
| **Auto Discovery** of nodes via one Configuration Endpoint | (cluster-mode endpoint instead) | ✔ |

The rule of thumb: if the question asks for **ANY** grown-up feature — durability, failover, backup, leaderboard, pub/sub — the answer is **Redis**. If it says *"simplest possible cache, data loss is acceptable, multithreaded"* → **Memcached**. Redis wins about 90% of exam appearances.

**When to use ElastiCache at all:** **repeated reads**, a **database bottleneck**, or **session storage** — needing **sub-millisecond** latency. Typical use cases: caching, session stores, gaming, geospatial, real-time analytics, lightweight queuing. It *is* a key-value store, but the exam treats it as a **cache in front of a database**, not the primary system of record (for a durable key-value primary store, think DynamoDB).

**Redis extras worth a neuron:**

- **Cluster mode** = data **sharded** across multiple node groups for write/memory scale.
- **Global Datastore** = write in one region, read from **up to 2 cross-region replica clusters** — low-latency global reads and a **DR** option (promote a secondary).
- **Securing Redis:** create the cluster with **`--transit-encryption-enabled`** and **`--auth-token`** → clients must present the **Redis AUTH** password over TLS. **At-rest encryption** only protects data on disk/backups — it does **not** authenticate clients. (Newer Redis 7+ also supports IAM auth, but **Redis AUTH** is the classic exam answer.)
- **Memcached Auto Discovery:** clients connect to a **single Configuration Endpoint** and automatically learn about nodes being added/removed.
- **Not serverless — classically:** ElastiCache (like RDS and Neptune) was node-based; **ElastiCache Serverless** now exists, but in "fully serverless stack" questions DynamoDB/DAX is still the safer pick.

**Free question alert:** *"gaming leaderboard with real-time ranking"* → **Redis sorted sets**. Sorted sets keep members ordered by score automatically — top-10 lookups are instant. If you see "leaderboard," you're done reading.

### The session store pattern

Picture a web tier behind an **ALB and Auto Scaling Group**. A user logs in; server #3 remembers her session — in its own memory. Then the ASG scales in, terminates server #3, and she's suddenly logged out. That's the exam giveaway phrase: **"users are logged out when instances are terminated/scaled in."**

The fix: make the web tier **stateless** by moving sessions to a shared, fast store outside the instances — **ElastiCache for Redis** (or DynamoDB). Any server can now handle any request.

```
Users → ALB → [EC2] [EC2] [EC2]  ← stateless, disposable
                 └─────┴─────┘
                       ▼
              ElastiCache (Redis)  ← sessions live here
```

### Caching strategies — when do you write the sticky note?

- **Lazy loading** (cache-aside): populate the cache **on a read miss**. Like writing a cheat sheet *during* the exam — you only jot down answers to questions actually asked. Efficient (only hot data is cached), but data can be **stale** if the database changes underneath, and every miss pays a penalty.
- **Write-through**: update the cache **on every WRITE** to the database. Cache is **never stale**, reads always hit — but you do double writes and cache plenty of data nobody ever reads.
- **TTL** (time-to-live) on cached entries is the middle ground: stale data expires automatically after N seconds.

**THE trap:** *"stale data is unacceptable"* (prices, inventory) → **write-through**, not lazy loading.

### The read-offloader triangle

Three services all claim to "reduce database read load" — the scenario tells you which:

| Read pattern | Answer |
|---|---|
| **Repeated, identical** reads (same product page 10,000x) | **ElastiCache** |
| **Diverse / complex / analytical** queries (each one different — caching can't help) | **Read Replica** |
| DynamoDB + **"no code changes"** | **DAX** |

**THE trap:** *"month-end reporting queries slow down the app"* → those queries are all *different*, so a cache never hits. Route them to a **Read Replica**.

## Question patterns

> *"Popular product pages generate thousands of identical reads that overload RDS"* → **ElastiCache** (repeated reads belong in memory)
> *"Real-time gaming leaderboard with player rankings"* → **Redis sorted sets** (ranking is built in — free points)
> *"Users get logged out when the Auto Scaling Group terminates instances"* → **store sessions in ElastiCache for Redis** (make the web tier stateless)
> *"Cache must survive a node failure without data loss"* → **Redis** (replication + Multi-AZ failover; Memcached has neither)
> *"Simplest cache, multithreaded, losing cached data is fine"* → **Memcached** (the only time it wins)
> *"Cached prices must never be out of date"* → **write-through** (cache updated on every write; lazy loading can serve stale)
> *"Long analytical/reporting queries slow the production database"* → **Read Replica**, not a cache (diverse queries never hit cache)
> *"Speed up DynamoDB reads without modifying the application"* → **DAX** (ElastiCache would require code changes)
> *"Publish/subscribe messaging between app components using the cache layer"* → **Redis** (pub/sub is Redis-only)
> *"Highly available in-memory database for HIPAA-regulated data"* → **ElastiCache for Redis** (HIPAA-eligible + Multi-AZ)
> *"Require a password for clients connecting to the cache, encrypted in transit"* → **Redis AUTH** (`--transit-encryption-enabled` + `--auth-token`; at-rest encryption doesn't authenticate)
> *"Low-latency cache reads in another region, plus cache DR"* → **Redis Global Datastore**
> *"Clients must find Memcached nodes automatically as the cluster scales"* → **Auto Discovery** (Configuration Endpoint)

## Pocket card

| Keyword | Answer |
|---|---|
| Repeated identical reads hammering DB | ElastiCache |
| Leaderboard / ranking | Redis sorted sets |
| Sessions / stateless web tier | Redis (or DynamoDB) |
| Durability, failover, backup, pub/sub | Redis |
| Simplest, multithreaded, loss OK | Memcached |
| Never-stale cache | Write-through |
| Stale-tolerant, cache only hot data | Lazy loading (+ TTL) |
| Diverse/analytical read offload | Read Replica |
| DynamoDB + no code change | DAX |
| Microseconds | Any in-memory cache (ElastiCache/DAX) |
| HIPAA in-memory store | Redis |
| Cache password / AUTH | Redis AUTH + in-transit encryption |
| Cross-region cache replicas / DR | Redis Global Datastore |
| Memcached node discovery | Auto Discovery (Configuration Endpoint) |

You now own the "make reads fast" toolbox — next, Section 12 hands you the keyword zoo of specialty databases, where each engine exists to win exactly one kind of question.
