# Top Decision Pairs — "X vs Y" (most-tested distinctions)

| Choose between | Rule of thumb |
|---|---|
| RDS Multi-AZ vs Read Replica | Multi-AZ = HA/failover (standby not readable). Read Replica = scale reads (async, can be cross-region). |
| Security Group vs NACL | SG: stateful, allow-only, instance level. NACL: stateless, allow+deny, subnet level → **block an IP = NACL**. |
| Gateway vs Interface Endpoint | Gateway = S3 & DynamoDB only, free, route table. Interface = most other services, ENI, paid, PrivateLink. |
| NAT Gateway vs NAT Instance | NAT GW managed, HA within AZ → **one per AZ**. |
| VPC Peering vs Transit Gateway | Peering is non-transitive, 1:1. TGW = hub-and-spoke, transitive. |
| ALB vs NLB vs GWLB | ALB = L7, path/host routing. NLB = L4, static IP, extreme perf. GWLB = third-party appliances. |
| CloudFront vs Global Accelerator | CloudFront = HTTP(S) caching CDN. GA = static anycast IPs, TCP/UDP, no caching. |
| CNAME vs Alias | Apex domain / AWS resource target = **Alias** (free for AWS targets). |
| SQS vs SNS vs Kinesis vs EventBridge | SQS = queue/decouple. SNS = pub/sub fan-out. Kinesis = ordered real-time stream, replay. EventBridge = event bus, SaaS/AWS events, rules. |
| SQS Standard vs FIFO | Standard = unlimited throughput, at-least-once. FIFO = ordering + exactly-once, limited throughput. |
| Secrets Manager vs Parameter Store | Auto-rotation = Secrets Manager. Cheap config = Parameter Store. |
| KMS vs CloudHSM | KMS managed multi-tenant. CloudHSM = FIPS 140-2 L3, single-tenant, you manage keys. |
| WAF vs Shield | WAF = L7 rules (SQLi, XSS, rate). Shield = DDoS (Standard L3/L4 free; Advanced paid + response team). |
| Cognito User Pool vs Identity Pool | User Pool = sign-in/JWT. Identity Pool = temporary AWS credentials. |
| EBS vs EFS vs Instance Store | EBS = single-AZ block. EFS = shared Linux NFS, multi-AZ. Instance store = ephemeral, fastest. |
| FSx Windows vs Lustre vs EFS | Windows/SMB/AD = FSx Windows. HPC/S3-linked = Lustre. Linux shared = EFS. |
| EC2 pricing | Steady 1–3 yr = Reserved/Savings Plan. Interruptible = Spot. Unpredictable short = On-Demand. Compliance/licence = Dedicated Host. |
| S3 IA vs One Zone-IA vs Intelligent-Tiering | One Zone only for re-creatable data. IT only for unknown/changing access. Known pattern → lifecycle rule. |
| Glacier classes | Instant (ms), Flexible (minutes–12 h), Deep Archive (12–48 h, cheapest). |
| DynamoDB GSI vs LSI | LSI only at table creation. Otherwise GSI. |
| DAX vs ElastiCache | DAX = DynamoDB microsecond cache, no code change to queries. |
| Redis vs Memcached | Redis = persistence, replication, HA, rich types. Memcached = simple, multithread. |
| Aurora Global vs Aurora Replicas | Global = cross-region DR, <1 s lag, fast promotion. |
| Redshift vs Athena | Redshift = data warehouse cluster. Athena = serverless SQL on S3. |
| Snowball vs DataSync vs DX | Offline/huge/poor network = Snow. Online file transfer = DataSync. Ongoing dedicated link = DX. |
| Direct Connect vs Site-to-Site VPN | DX = private, consistent, NOT encrypted. VPN = encrypted, fast to set up, internet. |
| CloudTrail vs CloudWatch vs Config | Trail = who did what (API). CloudWatch = metrics/logs/alarms. Config = resource config history/compliance. |
| SCP vs Permission Boundary | SCP = org/account guardrail (not on mgmt account). Boundary = max perms for one IAM entity. |
| Lambda vs Fargate vs Batch | >15 min or long-running containers → Fargate/Batch. |
| API Gateway types | REST (full features, usage plans) vs HTTP (cheaper) vs WebSocket; 29 s timeout. |
| Beanstalk deployments | All-at-once (fastest, downtime) → Rolling → Rolling+batch → Immutable → Blue/green (swap). |
| DR strategies | Backup&Restore (cheapest, slowest) → Pilot Light → Warm Standby → Multi-site active/active (fastest, most costly). |
| Reserved Instances vs Savings Plans | Savings Plans more flexible (Compute SP spans EC2/Fargate/Lambda). |

> Verify any row you are unsure of against the full guide before relying on it.
