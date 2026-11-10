# All Pocket Cards — one-file rapid review

Auto-collected from each guide's "Pocket card" section. Read it top to bottom; open the full guide only when a row feels unfamiliar.

---

## Section 1: IAM — Identity and Access Management  ·  [guide](../topic-guides/01-IAM.md)

| Keyword in the question | Answer |
|---|---|
| EC2/app needs AWS access, "most secure" | Instance role (instance profile), never keys |
| Lambda needs permissions | Execution role |
| Hardcoded / stored access keys | Wrong — replace with a role |
| Temporary / short-lived credentials | STS AssumeRole |
| Access across AWS accounts | Role in target account + trust policy |
| Third party assumes your role safely | ExternalId in trust policy |
| Role exists but "can't be assumed" | Fix the trust policy |
| Allow exists but action denied | Explicit Deny / SCP / permission boundary |
| Org-wide restriction, applies even to root | SCP (AWS Organizations) |
| Cap max permissions of ONE user/role | Permission boundary |
| Policy on the resource, has a Principal | Resource-based policy (e.g., bucket policy) |
| Legacy S3 grant mechanism, avoid | S3 ACL (≠ Network ACL) |
| SSO, one login → many AWS accounts | IAM Identity Center |
| Federate Okta / Azure AD / corporate AD | IAM Identity Center + SAML 2.0 |
| Federate app customers (Google/Facebook login) | Cognito |
| Require MFA for an action | Condition: aws:MultiFactorAuthPresent |
| Root account | MFA on, no access keys, don't use daily |
| Who is my resource shared with externally? | IAM Access Analyzer |
| Find unused users / stale permissions | Credentials report / access advisor |

IAM is the "who may act" layer under everything else — next up, S3, where you'll see these same policies show up on the resource side as bucket policies.

---

## Section 2: S3 — Simple Storage Service  ·  [guide](../topic-guides/02-S3.md)

| Keyword | Answer |
|---|---|
| Frequently accessed / hot | S3 Standard |
| Lives < 30 days | Standard (minimum-duration charges kill the rest) |
| Infrequent + instant retrieval | Standard-IA |
| "Can be regenerated / secondary copy" | One Zone-IA |
| "Unknown / unpredictable access" | Intelligent-Tiering |
| Known pattern over time | Lifecycle rule (beats Intelligent-Tiering) |
| Archive + milliseconds retrieval | Glacier Instant Retrieval |
| Archive + minutes-to-hours OK | Glacier Flexible (Expedited 1–5 min / Std 3–5 hr / Bulk 5–12 hr) |
| Cheapest, 12+ hr retrieval OK | Glacier Deep Archive (never faster than 12 hr) |
| Object > 5 GB (or > 100 MB) | Multipart upload (required / recommended) |
| Accidental delete/overwrite protection | Versioning (+ MFA Delete for root-MFA-gated deletes) |
| Copy to another region, DR/compliance | CRR (versioning on both sides) |
| Aggregate logs / copy within region | SRR |
| Replicate EXISTING objects | S3 Batch Replication |
| Default encryption, zero effort | SSE-S3 |
| "Audit key usage" / control rotation | SSE-KMS (in CloudTrail) |
| KMS request costs too high | S3 Bucket Key (~99% fewer KMS calls, coarser audit) |
| Customer supplies key per request | SSE-C (HTTPS mandatory) |
| "AWS must never see plaintext" | Client-side encryption |
| Encrypt in transit / enforce HTTPS | Deny aws:SecureTransport = false |
| Encrypt EXISTING objects | S3 Batch Operations |
| WORM, "not even root can delete" | Object Lock — Compliance mode |
| WORM, privileged users may bypass | Object Lock — Governance mode |
| "Lawsuit," indefinite hold | Legal Hold |
| Temporary download link, no AWS account | Presigned URL (creator's perms, ≤ 7 days) |
| Public policy exists but access fails | Block Public Access is on |
| S3 reachable only via CloudFront | OAC |
| Who accessed — cheap/complete/delayed | S3 Server Access Logs (different bucket! + Athena) |
| Who accessed — real-time + IAM identity | CloudTrail data events |
| More requests/sec | More prefixes (3,500 PUT / 5,500 GET per prefix) |
| Global UPLOADS to one bucket | Transfer Acceleration (pay only if faster) |
| Global DOWNLOADS | CloudFront |
| Download part of an object | Byte-range fetch |
| "When object uploaded, trigger..." | Event notification → Lambda/SQS/SNS/EventBridge |
| SQL on ONE object | S3 Select |
| SQL across S3 data sets | Athena |

S3's bucket policies are just Section 1's resource-based policies wearing a storage hat — and its classes ladder is the warm-up for the same cost-vs-speed reasoning you'll reuse on EBS, EFS, and Glacier-style questions everywhere else on the exam.

---

## Section 3: EC2 — Elastic Compute Cloud  ·  [guide](../topic-guides/03-EC2.md)

| Keyword | Answer |
|---|---|
| general purpose / balanced | M family |
| spiky, mostly idle / CPU credits | T family (burstable) |
| t3 slow after sustained load | credits exhausted → M/C family or Unlimited mode |
| bill increased during spike | T Unlimited mode overage |
| batch / encoding / HPC compute | C family |
| in-memory analytics / cache | R family |
| SAP HANA | X family |
| high local NVMe IOPS | I family |
| dense local HDD storage | D family |
| ML training | P family (GPU) |
| graphics / ML inference | G family / Inf |
| price-performance / cost / sustainability + ARM-friendly | Graviton (g suffix, e.g. m7g) |
| short-term, unpredictable, < 1 year | On-Demand |
| steady 24/7 for 1–3 years | Reserved Instance (up to 72%) |
| RI but family may change | Convertible RI (66%) |
| guarantee capacity in an AZ | Zonal RI / Capacity Reservation |
| commit $/hr, any family/region + Fargate/Lambda | Compute Savings Plan |
| commit $/hr, one family one region, max discount | EC2 Instance Savings Plan |
| interruptible / fault-tolerant / cheapest (up to 90%) | Spot (2-min warning) |
| database / cannot tolerate interruption | never Spot |
| baseline + surge, optimize cost | RI/SP baseline + Spot surge |
| BYOL / per-socket / per-core licenses | Dedicated Host |
| hardware isolation only, cheaper | Dedicated Instance |
| lowest latency / HPC / same rack | Cluster placement group |
| few critical instances, isolate failures (max 7/AZ) | Spread placement group |
| Hadoop / Cassandra / Kafka at scale | Partition placement group |
| failover keeping same private IP (same AZ) | move the ENI |
| separate management network / dual-homed | multiple ENIs |
| public IP changed after stop/start | Elastic IP |
| avoid EIPs / static entry point best practice | ELB + DNS or Global Accelerator |
| run script once at launch | user data (runs as root) |
| instance info from inside / SSRF protection | metadata at 169.254.169.254 / enforce IMDSv2 |
| preserve RAM state across stop | Hibernate (RAM → encrypted EBS root) |

Every EC2 instance needs disks to boot from and store data on — that's EBS, EFS, and Instance Store, up next in Section 4.

---

## Section 4: EBS, EFS & Instance Store  ·  [guide](../topic-guides/04-EBS-EFS-InstanceStore.md)

| Keyword | Answer |
|---|---|
| random I/O / database / boot volume | SSD (gp3 or io1/io2) |
| large sequential / big data / throughput MB/s | HDD (st1/sc1) — never bootable |
| ≤ 16,000 IOPS | gp3 |
| > 16,000 IOPS | io1/io2 |
| 256,000 IOPS / sub-millisecond | io2 Block Express |
| frequent sequential (logs, ETL) | st1 |
| coldest, cheapest EBS | sc1 |
| gp2 mentioned at all | migrate to gp3 (~20% cheaper) |
| more IOPS without more storage | gp3 (independent provisioning) |
| multiple instances, one block volume, same AZ | io1/io2 Multi-Attach (max 16) |
| root disk survives termination | DeleteOnTermination = false |
| new extra volume unusable | format + mount + fstab |
| move volume across AZ/region | snapshot → (copy) → restore |
| cheap rarely-restored snapshots | Snapshot Archive (75% off, 24–72 hr restore) |
| recover deleted snapshot | Recycle Bin |
| instant full performance from snapshot | Fast Snapshot Restore (expensive) |
| automate snapshot schedules | Data Lifecycle Manager |
| encrypt existing volume | snapshot → copy-encrypted → restore |
| shared files, many Linux instances, multi-AZ | EFS (NFS, pay per GB used) |
| shared files, Windows / SMB / Active Directory | FSx for Windows (never EFS) |
| HPC parallel file system | FSx for Lustre |
| thousands of concurrent EFS clients | Max I/O performance mode |
| EFS throughput default | Elastic mode |
| cut EFS cost on cold files | lifecycle to IA / Archive |
| fastest storage / temp / cache / scratch | Instance Store (ephemeral) |
| instance store + stop/terminate | data gone (reboot survives) |
| high IOPS + must persist | io2 EBS, not instance store |
| Cassandra/replicated data, local speed | Instance Store is OK |

You now know where an instance keeps its data — next up, S3 takes storage out of the instance entirely and into the world of objects, buckets, and eleven nines of durability.

---

## Section 5: Elastic Load Balancing & Auto Scaling  ·  [guide](../topic-guides/05-ELB-AutoScaling.md)

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

One layer down from the load balancer sits the network it all lives in — subnets, gateways, and firewalls — which is exactly where Section 6 (VPC) picks up.

---

## Section 6: VPC — Virtual Private Cloud  ·  [guide](../topic-guides/06-VPC.md)

| Keyword | Answer |
|---|---|
| Public subnet definition | Route to IGW |
| Outbound-only internet for private subnet | NAT Gateway (in a public subnet) |
| NAT high availability | One NAT Gateway per AZ |
| NAT instance fix | Disable source/dest check |
| IPv6 outbound-only | Egress-only IGW |
| Reserved IPs per subnet | 5 |
| VPC CIDR size | /16 to /28 |
| Block a specific IP | NACL (deny) |
| Stateful / instance-level | Security Group |
| Stateless / subnet-level / ephemeral ports | NACL |
| Tier-to-tier access control | SG referencing another SG |
| S3/DynamoDB private + free | Gateway Endpoint |
| Endpoint reachable from on-prem/peered VPC | Interface Endpoint (PrivateLink) |
| 2–3 VPCs, full access | VPC Peering (not transitive!) |
| Many VPCs + VPN/DX, transitive hub | Transit Gateway (RAM to share, only multicast) |
| One service, overlapping CIDRs, SaaS | PrivateLink (NLB + endpoint service) |
| Traffic metadata, accept/reject | Flow Logs |
| Full packet capture | Traffic Mirroring |
| Most secure admin access | SSM Session Manager |
| One network, many accounts | VPC Sharing via RAM |

You now own the network — next up are the roads leading into it from the outside world: Route 53, Direct Connect, and Site-to-Site VPN, plus the load balancers from Section 5 that stand at its public doors.

---

## Section 7: Route 53  ·  [guide](../topic-guides/07-Route53.md)

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

Route 53 hands out addresses and steps aside — but when the exam demands *instant* global failover with fixed IPs, you need something that stays in the path, which is exactly where Section 8's Global Accelerator picks up.

---

## Section 8: CloudFront & Global Accelerator  ·  [guide](../topic-guides/08-CloudFront-GlobalAccelerator.md)

| Keyword in question | Answer |
|---|---|
| global static content, low latency | **CloudFront** |
| "S3 only via CloudFront", private bucket | **OAC** (OAI = legacy distractor) |
| one paid file | **Signed URL** |
| whole paid library | **Signed Cookies** |
| block/allow countries | **Geo Restriction** |
| CloudFront custom cert | **ACM in us-east-1** |
| encrypt one sensitive field end-to-end | Field-level encryption |
| reduce origin load | Longer TTL / better caching |
| force-refresh cached files | Invalidation (`/*`, costs money) |
| UDP / gaming / VoIP / non-HTTP | **Global Accelerator** |
| fixed IPs for whitelisting | **Global Accelerator** (2 anycast IPs) |
| instant failover, no DNS-cache lag | **Global Accelerator** |
| global UPLOADS to S3 | **S3 Transfer Acceleration** |

Both of these services exist to get users to your data faster — but the data itself usually lives in a database, and how you make *that* fast and failure-proof is Section 9's RDS and Aurora.

---

## Section 9: RDS & Aurora  ·  [guide](../topic-guides/09-RDS-Aurora.md)

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

You now know how to keep the database standing and fast — but when the exam's read traffic is the *same* hot data thousands of times per second, even fifteen replicas is the wrong answer, and that's where caching with ElastiCache takes over.

---

## Section 10: DynamoDB  ·  [guide](../topic-guides/10-DynamoDB.md)

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

---

## Section 11: ElastiCache  ·  [guide](../topic-guides/11-ElastiCache.md)

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

You now own the "make reads fast" toolbox — next, Section 12 hands you the keyword zoo of specialty databases, where each engine exists to win exactly one kind of question.

---

## Section 12: The Other Databases (keyword zoo)  ·  [guide](../topic-guides/12-Other-Databases.md)

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

That's every database in the toolbox sorted by screw head — now Section 13 turns to the thing that glues all these services together with code: Lambda.

---

## Section 13: Lambda  ·  [guide](../topic-guides/13-Lambda.md)

| Keyword | Answer |
|---|---|
| Job > 15 minutes | NOT Lambda → Batch / Fargate |
| Divisible into <15-min steps | Step Functions |
| CPU-bound slow function | Increase memory |
| Cold start latency | Provisioned Concurrency (Pre-warmed) |
| Protect downstream / cap invocations | Reserved Concurrency (Restricted) |
| Lambda + RDS | RDS Proxy (+ VPC config) |
| VPC Lambda lost internet | NAT Gateway / VPC endpoints |
| Async failures lost | DLQ / failure destination |
| SQS / Kinesis / DDB Streams | Event Source Mapping (pull, batches) |
| S3 / SNS / EventBridge | Async push (2 retries) |
| Serverless cron | EventBridge schedule → Lambda |
| Shared dependencies | Layers |
| Deps > 250 MB | Container image (10 GB) |
| Function permissions | Execution role |
| Edge + network calls / JWT | Lambda@Edge |
| Edge header/URL tweak, cheapest | CloudFront Functions |
| Max runtime / memory / concurrency | 15 min / 10 GB / 1,000 default |

Lambda is the glue of every serverless diagram you've built so far — CloudFront to API Gateway to Lambda to DynamoDB — and with these four sections you now own that entire stack end to end.

---

## Section 14: ECS, EKS & Fargate  ·  [guide](../topic-guides/14-ECS-EKS-Fargate.md)

| Keyword | Answer |
|---|---|
| "No server management" + containers | Fargate |
| "Already using Kubernetes" / "multi-cloud" | EKS |
| GPUs for containers | EC2 launch type (never Fargate) |
| Can't pull image / can't write logs | Task Execution Role |
| App AccessDenied to AWS service | Task Role |
| Recipe / blueprint | Task Definition |
| Keeps N copies running + ALB | Service |
| Image storage + CVE scanning | ECR |
| Per-task ENI + security group | awsvpc mode |
| Cheap interruptible Fargate | Fargate Spot |
| Multiple same-service tasks, one instance | ALB dynamic port mapping |

Once your containers are running, the next question is: what if you don't even want to think about containers — you just want to hand AWS your code? That's Elastic Beanstalk, up next.

---

## Section 15: Elastic Beanstalk  ·  [guide](../topic-guides/15-Elastic-Beanstalk.md)

| Keyword | Answer |
|---|---|
| "Quickly deploy, no infra mgmt, KEEP control" | Elastic Beanstalk |
| Fastest deploy, downtime OK | All at once |
| No downtime, no extra cost | Rolling |
| No downtime, full capacity | Rolling + additional batch |
| Safest rollback (delete new fleet) | Immutable |
| DNS CNAME swap, instant rollback | Blue/Green |
| DB died with environment | Create RDS OUTSIDE env (env vars) |
| Move DB out of env | Snapshot → standalone RDS |
| SQS-driven background tier | Worker environment |
| Instance/env customization files | .ebextensions |
| Beanstalk pricing | Free — pay for resources only |
| Fine-grained IaC instead | CloudFormation |

Beanstalk fronts your app with a load balancer automatically — but when your "app" is an API consumed by other programs, you want a smarter front door: API Gateway, next section.

---

## Section 16: API Gateway  ·  [guide](../topic-guides/16-API-Gateway.md)

| Keyword | Answer |
|---|---|
| Serverless REST API | API GW + Lambda + DynamoDB |
| API keys / usage plans / caching / WAF | REST API (only) |
| Lowest cost, simple proxy, JWT | HTTP API |
| Real-time / chat / live push | WebSocket API |
| Global clients | Edge-Optimized endpoint |
| VPC-only API | Private endpoint (Interface Endpoint) |
| AWS-service callers | IAM / SigV4 auth |
| App users sign in | Cognito User Pool authorizer |
| Custom/third-party tokens | Lambda Authorizer |
| 429 errors | Throttling (default 10,000 req/s) |
| Backend > 29 seconds | Async: 202 + SQS/Step Functions |
| Cache TTL default | 300 seconds |
| Browser cross-domain error | Enable CORS |

You just saw the fix for slow backends is "drop the work into a queue and walk away" — that queue, and the whole messaging toolbox around it, is the next section.

---

## Section 17: SQS, SNS & Kinesis — the messaging block  ·  [guide](../topic-guides/17-SQS-SNS-Kinesis.md)

| Keyword | Answer |
|---|---|
| Decouple / buffer spikes | SQS |
| One message → one worker, PULL | SQS |
| Processed twice | Increase visibility timeout (default 30s) |
| Poison messages | DLQ + MaxReceiveCount |
| Empty-poll cost | Long polling (20s) |
| Strict order + exactly-once | FIFO (300 / 3,000 msg/s) |
| Message > 256 KB | S3 + pointer |
| Retention | 4 days default / 14 max |
| One → many, PUSH, instant | SNS (stores nothing) |
| Notify many, durably | SNS → multiple SQS (fan-out) |
| Multiple consumers, same data, replay | Kinesis Data Streams (24h–365d) |
| Shard throughput | 1 MB/s in, 2 MB/s out, order per shard |
| Stream → S3, zero code, ~60s | Firehose (S3/Redshift/OpenSearch/Splunk) |
| MQTT / AMQP / JMS / RabbitMQ | Amazon MQ |
| Workers scale on queue depth | ASG + CloudWatch queue metric |

Every architecture you've built so far — containers, Beanstalk apps, API Gateway backends — becomes bulletproof the moment you slide one of these buffers between its pieces; decoupling is the quiet superpower behind almost every correct SAA-C03 answer.

---

## Section 18: EventBridge & Step Functions  ·  [guide](../topic-guides/18-EventBridge-StepFunctions.md)

| Keyword | Answer |
|---|---|
| Serverless cron / "nightly job" | EventBridge scheduled rule |
| SaaS events (Zendesk, Datadog) | EventBridge partner event bus |
| Content-based event filtering | EventBridge rule |
| Replay past events | EventBridge archive + replay |
| Cross-account event routing | EventBridge cross-account bus |
| Huge fan-out push / SMS / mobile | SNS (not EventBridge) |
| Multi-step workflow, retries, audit | Step Functions |
| Workflow > 15 min | Step Functions (not Lambda chain) |
| Human approval / up to 1 year | Standard workflow |
| High-volume short IoT / < 5 min | Express workflow |
| For-each over items | Map state |
| Branching logic | Choice state |
| Backoff retries, no code | Built-in Retry |

EventBridge decides *which* work should happen when an event arrives; Step Functions makes sure multi-step work *finishes correctly* — and next we meet the services that watch everything else: CloudWatch, CloudTrail, and Config.

---

## Section 19: CloudWatch, CloudTrail & AWS Config  ·  [guide](../topic-guides/19-CloudWatch-CloudTrail-Config.md)

| Keyword | Answer |
|---|---|
| Performance, health, alarms | CloudWatch |
| Who did what / API audit | CloudTrail |
| Config history / compliance | AWS Config |
| EC2 memory or disk-space metric | CloudWatch agent (not default) |
| Count log pattern → alarm | Metric filter |
| Query logs interactively | Logs Insights |
| Real-time log streaming | Subscription filter → Kinesis/Lambda |
| Too many alarms / noise | Composite alarm |
| S3 object-level "who" | CloudTrail data events (opt-in) |
| Logs beyond 90 days | Trail → S3, multi-region |
| Tamper-proof logs | Log file integrity validation |
| Unusual API spike | CloudTrail Insights |
| Auto-fix noncompliance | Config + SSM remediation |
| PREVENT actions | SCP (never Config) |
| Trace across microservices | X-Ray |

Now you know who's watching the house — next comes who holds the keys: KMS and CloudHSM.

---

## Section 20: KMS & CloudHSM  ·  [guide](../topic-guides/20-KMS-CloudHSM.md)

| Keyword | Answer |
|---|---|
| Audit every key use | KMS + CloudTrail |
| Free, AWS-rotated key | AWS-managed key |
| Your policies, $1/mo, yearly rotation | Customer-managed key |
| Encrypt > 4KB | Envelope encryption / GenerateDataKey |
| Delete key now | Impossible — 7–30 day wait (disable instead) |
| Encrypt/decrypt across Regions | Multi-Region keys |
| Cut KMS costs on S3 | S3 Bucket Key |
| FIPS 140-2 Level 3 | CloudHSM |
| "AWS cannot see keys" / dedicated hardware | CloudHSM |
| SSL offload / own CA | CloudHSM |
| Access needs key policy AND IAM | Both must allow |

You now hold the keys — next, the safes where applications keep their passwords: Secrets Manager and Parameter Store.

---

## Section 21: Secrets Manager & Parameter Store  ·  [guide](../topic-guides/21-SecretsManager-ParameterStore.md)

| Keyword | Answer |
|---|---|
| "Automatic rotation" (any phrasing) | Secrets Manager |
| RDS/Redshift/DocumentDB creds | Secrets Manager (built-in rotation Lambda) |
| Cheapest / free config store | Parameter Store standard |
| Hierarchical paths /prod/... | Parameter Store |
| Cross-account secret sharing | Secrets Manager |
| Encrypted param, free | Parameter Store SecureString |
| > 8KB secret | Secrets Manager (64KB) |
| Hardcoded password fix | Secrets Manager + IAM role runtime fetch |
| Rotation without downtime | Secrets Manager |
| $0.40/secret/month | Secrets Manager |

Keys from Section 20 encrypt these secrets, CloudTrail from Section 19 audits every peek at them — the monitoring, key, and secret stories all click together, and that's exactly how the exam will test you.

---

## Section 22: WAF, Shield & the Security Service Zoo  ·  [guide](../topic-guides/22-WAF-Shield-SecurityServices.md)

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

You've now got the security crew sorted — next up, the service that decides who your app's *users* even are: Cognito.

---

## Section 23: Cognito  ·  [guide](../topic-guides/23-Cognito.md)

| Keyword | Answer |
|---|---|
| Sign-up / sign-in / user directory | User Pools |
| JWT tokens | User Pools |
| Social login (Google/Facebook/Apple), SAML | User Pools (federation) |
| Hosted UI, MFA | User Pools |
| API Gateway / ALB authorizer | User Pool authorizer |
| Temporary AWS credentials for app users | Identity Pools (via STS) |
| Direct app access to S3/DynamoDB | Identity Pools |
| Guest / unauthenticated access | Identity Pools |
| Each user only their own folder | Identity Pool + IAM policy variables |
| Employees SSO to AWS accounts | IAM Identity Center (never Cognito) |
| Memory hook | User Pool = login box (JWT); Identity Pool = exchange desk (creds) |

Cognito handles your app's *customers* — but when the identities live in a corporate Active Directory, you're in the next section's territory: Directory Services.

---

## Section 24: Directory Services  ·  [guide](../topic-guides/24-Directory-Services.md)

| Keyword | Answer |
|---|---|
| Full AD features in AWS | Managed Microsoft AD |
| Trust relationship with on-prem | Managed Microsoft AD (two-way trust) |
| MFA + domain join | Managed Microsoft AD |
| No identities stored in cloud | AD Connector |
| Proxy / redirect auth to on-prem | AD Connector |
| Low cost, basic LDAP, small org | Simple AD |
| No trust, no MFA | Simple AD's limits |
| FSx Windows / WorkSpaces / RDS SQL Server | All need a directory — pick from the three |
| Memory hook | Full copy w/ trust / phone line / budget clone |

Directories solve *who* on-prem users are in the cloud — next we solve where their *files* live, with the hybrid storage bridge crew: Storage Gateway, DataSync, and Transfer Family.

---

## Section 25: Storage Gateway, DataSync & Transfer Family  ·  [guide](../topic-guides/25-StorageGateway-DataSync-TransferFamily.md)

| Keyword | Answer |
|---|---|
| Replace tape backups | Tape Gateway (VTL → S3/Glacier) |
| NAS replacement, files in S3, local access | S3 File Gateway |
| SMB cache for FSx Windows | FSx File Gateway |
| Extend on-prem capacity, primary in cloud | Volume Gateway — Cached |
| Full dataset local + snapshots to cloud | Volume Gateway — Stored |
| Migrate / scheduled sync, preserve permissions | DataSync |
| Bandwidth throttling, on-prem agent | DataSync |
| S3 ↔ EFS ↔ FSx transfers | DataSync |
| Partners upload via SFTP/FTPS/FTP | Transfer Family (never SFTP-on-EC2) |
| Ongoing hybrid access vs. one-time move | Storage Gateway vs. DataSync |
| Offline / massive data, no bandwidth | Snow Family (Section 27) |

That's the online bridge to the cloud sorted — when the pipe is too small for the payload, you put the data on a truck, and that's where the Snow Family rolls in.

---

## Section 26: FSx Family  ·  [guide](../topic-guides/26-FSx.md)

| Keyword | Answer |
|---|---|
| Windows / SMB / NTFS / AD / .NET | FSx for Windows File Server |
| HPC / ML training / rendering / GB/s | FSx for Lustre |
| Process S3 data as files | FSx for Lustre (S3 integration) |
| Temporary + cheapest Lustre | Scratch deployment |
| Long-term Lustre | Persistent deployment |
| NetApp / SnapMirror | FSx for NetApp ONTAP |
| NFS + SMB + iSCSI together | FSx for NetApp ONTAP |
| ZFS | FSx for OpenZFS |
| Plain Linux shared storage | EFS (not FSx at all) |

FSx moves files at specialty speed — but when the data is too big to move over a wire at all, you put it on a truck, which is exactly where the Snow Family comes in.

---

## Section 27: Snow Family  ·  [guide](../topic-guides/27-Snow-Family.md)

| Keyword | Answer |
|---|---|
| Transfer would take > 1 week | Snow family |
| 8–14 TB, tiny/rugged/edge | Snowcone |
| 50–500 TB migration | Snowball Edge Storage Optimized |
| Process data offline / GPU at edge | Snowball Edge Compute Optimized |
| > 10 PB, up to 100 PB | Snowmobile |
| Straight to Glacier? | No — S3 first + lifecycle rule |
| Encryption on device | KMS, automatic |
| GUI for Snow devices | OpsHub |
| Preinstalled DataSync agent | Snowcone |

Once your data (and everything else) is in AWS, you'll want to build environments the same way twice without clicking — that's CloudFormation's whole reason to exist.

---

## Section 28: CloudFormation  ·  [guide](../topic-guides/28-CloudFormation.md)

| Keyword | Answer |
|---|---|
| Preview changes before update | Change Sets |
| Many accounts + regions, one template | StackSets |
| Keep data on stack delete | DeletionPolicy Retain / Snapshot |
| Detect manual console edits | Drift Detection |
| Infra in Python/TypeScript | CDK |
| Protect resource during updates | Stack Policy |
| Reusable template components | Nested Stacks |
| Share values between stacks | Outputs + Export / ImportValue |
| Only required template section | Resources |
| Failed creation | Automatic rollback (default) |

You now know how to stamp out infrastructure across many accounts — next comes the question of who governs all those accounts, which is Organizations and Control Tower territory.

---

## Section 29: AWS Organizations & Control Tower  ·  [guide](../topic-guides/29-Organizations-ControlTower.md)

| Keyword | Answer |
|---|---|
| Block actions org-wide / by OU | SCP |
| SCP grants permissions? | Never — ceiling only (needs IAM allow too) |
| SCP vs management account | Doesn't apply — exempt |
| One bill, shared RI/SP discounts | Consolidated billing |
| Automated governed multi-account setup | Control Tower |
| Self-service standardized new accounts | Account Factory |
| Preventive guardrail | SCP (blocks) |
| Detective guardrail | Config rule (flags) |
| Share subnets / TGW / resolver rules | RAM |
| Admin denied in member account | Check the SCP |

Governance says which accounts may do what — the next layer down is letting teams safely launch only pre-approved infrastructure, which is Service Catalog's job.

---

## Section 30: Service Catalog & Trusted Advisor  ·  [guide](../topic-guides/30-ServiceCatalog-TrustedAdvisor.md)

| Keyword | Answer |
|---|---|
| Self-service approved stacks, minimal IAM | Service Catalog |
| Product / portfolio | Service Catalog terms (CFN template / group of products) |
| Idle / unused / unattached resources | Trusted Advisor (Cost) |
| Approaching quota warning | Trusted Advisor (Service Limits) |
| Open SGs, root MFA check | Trusted Advisor (Security) |
| Full checks locked | Business/Enterprise support plan |
| Five pillars | Cost, Performance, Security, Fault Tolerance, Service Limits |

Trusted Advisor tells you the bill *could* be smaller — the cost management tool zoo in the next section is how you actually see, alert on, and shrink it.

---

## Section 31: Cost Management Tools  ·  [guide](../topic-guides/31-Cost-Management.md)

| Keyword | Answer |
|---|---|
| Visualize / analyze spend, forecast | Cost Explorer |
| Alert at % of budget | AWS Budgets |
| Most detailed / line items / SQL | CUR + Athena |
| Unusual spike, ML detection | Cost Anomaly Detection |
| Rightsize EC2/EBS/Lambda | Compute Optimizer |
| Cost per team / chargeback | Cost Allocation Tags (activate first) |
| RI / Savings Plan buy advice | Cost Explorer |
| Custom internal billing views | Billing Conductor |

That closes out the governance-and-cost corner of the exam — from here, every scenario about "who pays, who sees, who's warned" should feel like matching verbs to vending machines.

---

## Section 32: Direct Connect & VPN  ·  [guide](../topic-guides/32-DirectConnect-VPN.md)

| Keyword | Answer |
|---|---|
| Encrypted tunnel, quick, cheap | Site-to-Site VPN |
| VGW + CGW | Site-to-Site VPN components (AWS + customer side) |
| Consistent bandwidth, dedicated | Direct Connect |
| Setup in hours | VPN |
| Setup in weeks–months | Direct Connect |
| Encrypt Direct Connect | VPN over DX |
| Cost-effective DX backup | Site-to-Site VPN |
| One DX → many VPCs/regions | Direct Connect Gateway |
| Remote workers → VPC | Client VPN |
| Private VIF / Public VIF / Transit VIF | VPC / public services / Transit Gateway |

You now know how ONE office connects to AWS — next up, what happens when dozens of VPCs and offices all need to talk to each other without a wiring nightmare: Transit Gateway.

---

## Section 33: Transit Gateway  ·  [guide](../topic-guides/33-Transit-Gateway.md)

| Keyword | Answer |
|---|---|
| Many VPCs + on-prem, central hub | Transit Gateway |
| Transitive routing | Transit Gateway (peering can't) |
| n(n-1)/2 peering explosion | Transit Gateway |
| Multicast | Transit Gateway (only one) |
| Isolate prod/dev at the hub | TGW route tables |
| Cross-account TGW | Share via AWS RAM |
| Cross-region hubs | TGW peering |
| DX into TGW | Transit VIF |
| Only 2–3 VPCs, cheapest | VPC peering |
| Expose one service, no network merge | PrivateLink (not TGW) |

That's the plumbing done — next we zoom all the way out to how AWS wants you to *think* about architecture: the Well-Architected Framework.

---

## Section 34: Well-Architected Framework  ·  [guide](../topic-guides/34-Well-Architected.md)

| Keyword | Answer |
|---|---|
| IaC, small reversible changes | Operational Excellence (CloudFormation) |
| Least privilege, encrypt everywhere | Security (IAM, KMS, GuardDuty) |
| Survive failure, stop guessing capacity | Reliability (Multi-AZ, ASG, Route 53) |
| Right tool, serverless-first, edge | Performance Efficiency (Lambda, CloudFront) |
| Pay for what you use, measure spend | Cost Optimization (Cost Explorer, Savings Plans, Spot) |
| Maximize utilization, Graviton | Sustainability |
| Free best-practices review | Well-Architected Tool |
| "MOST cost-effective / LEAST overhead" | The qualifier picks between two working answers |

Keep those qualifiers in your peripheral vision — they matter most in the next section's territory: disaster recovery, where cost versus recovery speed *is* the whole question.

---

## Section 35: Disaster Recovery  ·  [guide](../topic-guides/35-Disaster-Recovery.md)

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

You now hold the full toolbox — time to sharpen it against the exam's favorite tricks: the classic traps and must-know combos.

---

## Section 36: Classic Traps & Must-Know Combos  ·  [guide](../topic-guides/36-Exam-Traps-KeyPatterns.md)

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

Traps mapped, combos memorized — one last sweep remains: the small-but-tested gap-fill services that each show up for one or two easy points.

---

## Section 37: The Gap-Fill Services (small but tested)  ·  [guide](../topic-guides/37-GapFill-Services.md)

| Keyword | Answer |
|---|---|
| MQTT / AMQP / JMS, minimal rewrite | Amazon MQ |
| Lift-and-shift servers (rehost) | MGN |
| DR replication, RPO seconds | Elastic Disaster Recovery (DRS) |
| DB migration, different engines | DMS + SCT |
| Free auto-renewing TLS certs | ACM |
| CloudFront certificate region | us-east-1 (always) |
| IPv6 outbound-only | Egress-only Internet Gateway |
| On-prem → VPC DNS | Resolver inbound endpoint |
| VPC → on-prem DNS | Resolver outbound endpoint |
| AWS racks in your datacenter | Outposts |
| Single-digit ms to a metro city | Local Zones |
| 5G edge | Wavelength |
| Serverless ETL + catalog | Glue |
| Spark / Hadoop | EMR |
| Kafka | MSK |
| BI dashboards | QuickSight |
| Data lake + fine-grained access | Lake Formation |
| SaaS → S3 | AppFlow |
| Images/video analysis | Rekognition |
| Speech → text / text → speech | Transcribe / Polly |
| Sentiment | Comprehend |
| Scanned forms/invoices | Textract |
| Intelligent doc search | Kendra |
| Recommendations / forecasts / chatbots | Personalize / Forecast / Lex |
| Custom ML | SageMaker |
| No-SSH access / fleet scripts / auto-patching | Session Manager / Run Command / Patch Manager |
| Batch jobs > 15 min, Docker | AWS Batch |
| GraphQL, offline sync | AppSync |
| Full-stack quickstart | Amplify |
| Application emails | SES |
| Bulk ops on existing S3 objects | S3 Batch Operations |
| Instant prod DB copy for testing | Aurora cloning |
| Distributed tracing | X-Ray |
| Compliance reports for auditors | AWS Artifact |

That's the last jar on the spice rack — you've now covered the whole SAA-C03 kitchen. Sleep well, read the last sentence first, and go collect your certificate.
