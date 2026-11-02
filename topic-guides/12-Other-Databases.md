# Section 12: The Other Databases (keyword zoo)

## The idea

Think of a hardware store wall: fifty screwdrivers, and each one exists for exactly one screw head. You don't need to *master* any of them — you need to glance at the screw and grab the right handle. AWS's specialty databases are that wall. **Each engine has ONE identifying keyword**, and the exam question always hands you the screw. This section is pure pattern-matching: keyword in, service out.

But first, one concept from zero, because it anchors half the zoo:

### OLTP vs OLAP

- **OLTP** — OnLine **Transaction** Processing: **many small operations**. *"Fetch order #123." "Update this user's address."* Millions per day, each touching a few rows. This is your day-to-day app database: RDS, Aurora, DynamoDB. Row-based storage (grab the whole record at once).
- **OLAP** — OnLine **Analytical** Processing: **few huge scans**. *"Average revenue per region per month across five years."* One query reads billions of rows but only 3 columns. Purpose-built warehouses use **columnar storage** — data stored column-by-column, so scanning `revenue` doesn't drag every other field off disk. Massively faster for analytics, plus columns compress beautifully.

**THE trap (the cardinal sin):** *"analysts run big reporting queries against the production database and the app slows down."* Never run analytics on your prod OLTP database. The answer is always: move analytics to **Redshift** (or a Read Replica / Athena, per the scenario).

### The zoo — one call each

| Service | The ONE identifying call |
|---|---|
| **Redshift** | **Data warehouse.** Keywords: *OLAP, BI, analytics, petabyte-scale, columnar.* Load data in, point Tableau/QuickSight at it. **Redshift Spectrum** = query data **still sitting in S3** from Redshift **without loading it**. **Redshift Serverless** = same warehouse, no cluster to manage, pay per use. |
| **Athena** | **SQL directly on files in S3.** Fully **serverless**, pay **$5 per TB scanned**. Keyword: *"analyze logs in S3 with SQL, no infrastructure."* |
| **Neptune** | **Graph database.** Data that is mostly *relationships*: **social networks, recommendation engines, fraud rings, knowledge graphs.** "Friends-of-friends" → Neptune. |
| **QLDB** | **Ledger.** **Immutable, cryptographically verifiable** history — nothing can be changed or deleted, ever, and you can *prove* it. **Centralized** (one owner). |
| **Managed Blockchain** | Like QLDB but **decentralized** — **multiple parties** who don't trust each other transact **without a central authority**. QLDB vs Blockchain = one owner vs many parties. |
| **Timestream** | **Time-series** database. **IoT sensor data, telemetry, DevOps metrics** — timestamped measurements arriving forever, queried by time window. |
| **DocumentDB** | The keyword is literally **"MongoDB."** MongoDB-compatible managed document DB. See MongoDB → circle DocumentDB → move on. |
| **Keyspaces** | The keyword is literally **"Cassandra."** Apache Cassandra-compatible, serverless. |
| **OpenSearch** | **Full-text / fuzzy search** + **log analytics with dashboards** (the old Elasticsearch/Kibana). Search "runing shoes" and still find running shoes. |

### The two comparisons worth 30 extra seconds

**Athena vs Redshift** — both do SQL analytics, so which?

```
Data stays in S3, ad-hoc, occasional, zero infra  →  ATHENA
Data loaded into a warehouse, heavy repeated BI,
complex joins, dashboards all day                 →  REDSHIFT
(Middle child: query S3 FROM your existing
 Redshift cluster without loading                 →  SPECTRUM)
```

- **Spectrum vs Athena in one line:** Athena queries **only S3**; Spectrum **joins S3 data with tables already inside Redshift** in one query. Both handle **structured and semi-structured** files in S3.
- **Redshift is not for OLTP or session state** — it gives **sub-second-to-seconds** analytic answers, not millisecond row lookups (that's DynamoDB/ElastiCache, and DAX is microseconds).
- **Redshift DR:** enable **cross-region snapshot copy** on the cluster (pick a destination region + retention) — snapshots are then copied automatically.

**Athena cost optimization** — this appears almost **verbatim**: *"reduce Athena query costs / improve performance."* Athena bills per TB **scanned**, so scan less:
1. Convert files to **columnar formats — Parquet or ORC** (read only needed columns),
2. **Compress** the data,
3. **Partition** it (e.g., by date, so queries skip irrelevant folders).

All three shrink bytes scanned = smaller bill. Memorize the trio.

**OpenSearch combo pattern:** DynamoDB **cannot do fuzzy or full-text search** (it's a coat-check, not a librarian). The exam's fix: **DynamoDB + Streams → Lambda → OpenSearch** — writes land in DynamoDB, the change feed copies them into OpenSearch, and search queries go to OpenSearch.

**DocumentDB vs DynamoDB** — both store JSON-ish documents, so which?

| | **DocumentDB** | **DynamoDB** |
|---|---|---|
| Compatibility | **MongoDB** APIs/drivers | AWS-native API |
| Queries | **Rich ad-hoc queries + secondary indexes** on any field, aggregations | **Key-based** access (partition/sort key, GSIs) |
| Infrastructure | **Instance/cluster-based** (you size nodes) | **Serverless**, any scale |
| Pick when | Existing MongoDB app, flexible document queries | Massive scale, predictable key lookups, zero ops |

**Zoo footnotes from the field:**

- **Neptune** classic: build a **social network from user profiles and interactions** (who-knows-whom, likes, follows).
- **Timestream** is **serverless**, ingests **trillions of events per day**, and AWS pitches it as up to **1000x faster** (and cheaper) than relational DBs for time-series.
- **QLDB** = a **transparent, immutable, cryptographically verifiable transaction log**. **Legacy note:** AWS has announced **end of support for QLDB (July 2025)** and points customers to **Aurora PostgreSQL** (with audit tables) — expect it only as the "immutable ledger" keyword on older-style questions.

**Database selection cheat sheet:**

| Need | Pick |
|---|---|
| Transactional SQL, existing engine | **RDS** |
| High-performance relational, cloud-native | **Aurora** |
| Serverless NoSQL key-value | **DynamoDB** |
| Analytics / warehouse | **Redshift** |
| Global multi-region NoSQL (multi-writer) | **DynamoDB Global Tables** |
| Global relational (one writer, fast DR) | **Aurora Global Database** |

## Question patterns

> *"BI team needs a petabyte-scale data warehouse for complex analytical queries"* → **Redshift** (OLAP, columnar, built for BI)
> *"Query data in S3 from the existing Redshift cluster without loading it"* → **Redshift Spectrum** (extends the warehouse into S3)
> *"Run occasional SQL queries on ALB/VPC logs stored in S3, minimal setup"* → **Athena** (serverless SQL-on-S3)
> *"Reduce Athena costs and speed up queries"* → **Parquet/ORC + compression + partitioning** (bill = TB scanned, so scan less)
> *"Social app needs friend-of-friend recommendations / detect fraud rings"* → **Neptune** (relationships = graph)
> *"Complete, immutable, cryptographically verifiable history of financial records, single organization"* → **QLDB** (centralized ledger)
> *"Multiple companies transact without a trusted central authority"* → **Managed Blockchain** (decentralized — the QLDB foil)
> *"Millions of IoT sensor readings per minute, analyzed over time windows"* → **Timestream** (time-series)
> *"Migrate a MongoDB workload to a managed AWS service"* → **DocumentDB** (keyword match, done)
> *"Migrate a Cassandra workload"* → **Keyspaces** (keyword match, done)
> *"Product catalog needs fuzzy, typo-tolerant full-text search; data is in DynamoDB"* → **OpenSearch** (via DynamoDB Streams → Lambda; DynamoDB can't fuzzy-search)
> *"Analysts' reports are slowing the production OLTP database"* → **move analytics off prod** — to Redshift (the cardinal sin, corrected)
> *"Join historical data in S3 with current tables in the Redshift warehouse"* → **Redshift Spectrum** (Athena can't see Redshift tables)
> *"Redshift cluster must be recoverable in another region"* → **cross-region snapshot copy** (destination region + retention)
> *"MongoDB-compatible JSON documents with rich queries on many fields"* → **DocumentDB**; *"serverless key-based access at any scale"* → **DynamoDB**
> *"Build a social network from user profiles and their interactions"* → **Neptune**

## Pocket card

| Keyword | Answer |
|---|---|
| Data warehouse / OLAP / BI / petabyte | Redshift |
| Query S3 from Redshift, no loading | Redshift Spectrum |
| SQL on S3, serverless, ad-hoc / logs | Athena |
| Cut Athena cost | Parquet/ORC + compress + partition |
| Graph / social / fraud ring / recommendations | Neptune |
| Immutable verifiable ledger, centralized | QLDB |
| Decentralized, multi-party, no central authority | Managed Blockchain |
| Time-series / IoT / telemetry / metrics | Timestream |
| "MongoDB" | DocumentDB |
| "Cassandra" | Keyspaces |
| Full-text / fuzzy search, log dashboards | OpenSearch |
| Analytics choking prod OLTP DB | Move it — Redshift |
| S3 data + Redshift tables in one query | Spectrum (Athena = S3 only) |
| Redshift DR | Cross-region snapshot copy |
| MongoDB queries vs key lookups | DocumentDB vs DynamoDB |
| Session state / OLTP | Not Redshift — DynamoDB/ElastiCache |
| QLDB | Legacy (end of support 2025) |

That's every database in the toolbox sorted by screw head — now Section 13 turns to the thing that glues all these services together with code: Lambda.
