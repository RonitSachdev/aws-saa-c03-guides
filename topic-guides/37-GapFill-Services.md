# Section 37: The Gap-Fill Services (small but tested)

## The idea

You've built the skyscrapers — EC2, S3, VPC, RDS. This section is the **spice rack**: dozens of small jars you'll each use once, but when the recipe calls for saffron, only saffron will do. Each of these services shows up on the exam **once or twice**, almost always as a pure **keyword-match** question. You don't need depth; you need to hear the signal word and slap the right label on it. That makes this the highest points-per-minute section you'll study — easy marks hiding in plain sight.

Read each entry as: *signal keyword → service*. That's genuinely how the questions work.

## Migration & messaging

**Amazon MQ** — managed **ActiveMQ / RabbitMQ** message broker. Signal: *"existing application uses **MQTT / AMQP / JMS** (industry-standard messaging protocols) and must migrate with **minimal rewrite**."* THE trap: for **new** applications, AWS wants **SQS/SNS** — MQ is only for lifting existing broker-based apps.

**Application Migration Service (MGN)** — the **lift-and-shift (rehost)** tool. Installs an agent on your on-prem servers, does **continuous block-level replication** into AWS, then you **cut over** to EC2 with minutes of downtime. Signal: *"migrate servers to AWS with minimal changes."*

**Elastic Disaster Recovery (DRS)** — MGN's twin, but for **DR instead of migration**: same continuous replication, but you only launch the recovery instances when disaster strikes. **RPO in seconds, RTO in minutes**, and it's cheap while idle. Signal: *"cost-effective disaster recovery for physical/virtual/cloud servers."*

**DMS + SCT** — **Database Migration Service** moves databases (and can do **ongoing replication**, source stays live during migration). If the engines differ — Oracle → Aurora — that's a **heterogeneous** migration and you add the **Schema Conversion Tool (SCT)** first. Same engine = DMS alone; **different engine = DMS + SCT**. DMS's **Basic Schema Copy** creates only tables and primary keys. It skips **secondary indexes, foreign keys and stored procedures**, so it's fine for a test run but **not suitable for production**. Use SCT for the full schema.

**Migration toolkit at a glance:**

| Need | Service |
|---|---|
| Inventory on-prem servers, dependencies and utilization **before** planning a migration | **Application Discovery Service** |
| One dashboard to **track migration progress** across tools | **Migration Hub** |
| Rehost **servers**: an agent replicates whole disks | **MGN** (its Replication Agent). Legacy name: CloudEndure Migration |
| Move **files** (NFS/SMB/HDFS) to S3/EFS/FSx, including straight into Glacier Deep Archive | **DataSync** |
| Move **databases**, minimal downtime, ongoing replication | **DMS** (+ **SCT** for schema/code) |
| Huge offline transfer, you bring your own drives to an AWS site | **AWS Data Transfer Terminal**: physical locations to plug in and upload at high speed |

THE trap: **Replication Agent vs DataSync** = **servers vs files**. Use MGN's agent to move a whole machine. Use DataSync to move a file share.

**Look-alikes that are NOT queues:**

| Service | What it really is |
|---|---|
| **SQS** | Decoupling message queue (cloud-native) |
| **Amazon MQ** | Managed broker for **existing** JMS/AMQP/MQTT/STOMP apps |
| **Data Firehose** | **Delivers** streaming data into S3/Redshift/OpenSearch. It's a pipe, not a queue. |
| **AppStream 2.0** | Streams **individual desktop applications** to a browser |
| **WorkSpaces** | A full managed **virtual desktop** (Windows/Linux VDI) |

**The 7 Rs of migration** — one line each:

| R | Meaning |
|---|---|
| **Rehost** | Lift-and-shift, no changes (MGN) |
| **Replatform** | Lift-and-tinker (e.g., self-managed MySQL → RDS) |
| **Repurchase** | Drop it, buy SaaS instead |
| **Refactor** | Re-architect for cloud (e.g., monolith → serverless) |
| **Relocate** | Move VMware wholesale (VMware Cloud on AWS) |
| **Retain** | Leave it on-prem for now |
| **Retire** | Turn it off, nobody used it anyway |

## Certificates & network odds-and-ends

**ACM (AWS Certificate Manager)** — **free public TLS/SSL certificates** with **automatic renewal**, attachable to ALB, CloudFront, API Gateway. Two exam facts: a certificate for **CloudFront MUST live in us-east-1** (any region works for a regional ALB), and **you cannot export ACM public certs to install on an EC2 instance** — ACM only attaches to integrated services. ACM stores **certificates**, not passwords.

**IAM certificate store** is the **legacy** option. You upload a certificate bought from a third party into IAM. Use it only where ACM isn't supported in a Region. Otherwise prefer ACM, because IAM certs don't auto-renew.

**Egress-only Internet Gateway** — the **IPv6 "NAT gateway."** IPv6 addresses are all public, so NAT doesn't apply; this gateway lets IPv6 instances make **outbound-only** connections while blocking inbound. Signal: *"IPv6 instances need outbound internet, no inbound."*

**Route 53 Resolver endpoints** — hybrid DNS plumbing. **Inbound endpoint**: **on-prem → VPC** DNS queries (your datacenter resolves AWS private names). **Outbound endpoint**: **VPC → on-prem** DNS queries (AWS resolves your corporate names). Remember it from the VPC's point of view: which way are the *queries coming*?

## Edge & hybrid infrastructure

| Service | One-liner | Signal keyword |
|---|---|---|
| **Outposts** | AWS-managed racks physically installed **in YOUR datacenter** | "data residency," "must stay on-premises but use AWS APIs" |
| **Local Zones** | AWS extension in a **metro city** near your users | "**single-digit millisecond** latency to users in Los Angeles" |
| **Wavelength** | AWS compute embedded in **5G telecom networks** | "5G," "mobile edge" |

## Analytics family

| Service | One-liner | Signal keyword |
|---|---|---|
| **Glue** | **Serverless ETL** (extract-transform-load) + **Data Catalog** + crawlers that auto-discover schemas | "serverless data preparation/catalog" |
| **EMR** | Managed **Hadoop/Spark** cluster; use **Spot for task nodes** to cut cost | "**Apache Spark**," "big data frameworks" |
| **MSK** | Managed **Apache Kafka** | the word "**Kafka**" — that's it |
| **Athena** | SQL queries directly on S3, pay per query (you know this one) | "query S3 with SQL" |
| **QuickSight** | **BI dashboards** and visualizations | "business dashboards for management" |
| **Lake Formation** | Build a **data lake** fast + **fine-grained (row/column) access control** | "central data lake with granular permissions" |
| **AppFlow** | Move data from **SaaS apps (Salesforce, Slack) → S3/Redshift**, no code | "Salesforce data into S3" |

THE trap: "streaming" alone → Kinesis; but "**Kafka**" named explicitly → **MSK**. AWS respects the proper noun.

**Compute/analytics chooser — "which engine runs this job?"**

| Job | Best service |
|---|---|
| Scheduled or parallel scripts, lots of containerized batch jobs | **AWS Batch** |
| Spark/Hadoop with full framework control | **EMR** (managed clusters) |
| Serverless ETL, CSV → Parquet, schema discovery | **Glue** |
| Event-driven short code | **Lambda** |
| Data warehouse / complex BI SQL | **Redshift** |
| Stream processing | **Kinesis** |
| Interactive ad-hoc SQL on S3 | **Athena** |
| Workflow orchestration | **Step Functions** |
| Copy database data into S3/Redshift | **DMS** |
| Export a DynamoDB table to S3 | DynamoDB **Export to S3**, or the **Glue DynamoDB connector** inside an ETL job |

THE trap: **Glue vs EMR**. Both transform data in S3. **"Least operational overhead"** or "serverless" points to **Glue**. "Need Spark/Hadoop control, custom frameworks" points to **EMR**. Glue jobs are batch ETL, not real-time.

**Legacy workflow tools:**
- **SWF** (Simple Workflow Service) coordinates tasks and guarantees each task is assigned exactly once. It isn't serverless.
- **Data Pipeline** moved data between AWS and on-prem sources.
- For new designs, both are replaced by **Step Functions**, **Glue** or **MWAA**.

## ML one-liners (pure keyword matching)

| Service | Does | Signal |
|---|---|---|
| **Rekognition** | Analyze **images/video**: objects, people, text, scenes, activities, faces, inappropriate content | face detection, content moderation |
| **Transcribe** | **Speech → text** | call transcripts, subtitles |
| **Polly** | **Text → speech** (SSML for pronunciation). Not a chatbot, which is Lex. | "app reads articles aloud" |
| **Translate** | Language translation | "localize to 12 languages" |
| **Comprehend** | **NLP / sentiment** analysis, no ML experience needed | "customer review sentiment" |
| **Comprehend Medical** | NLP that extracts **medical info** from unstructured clinical text | "diagnoses/medications from doctors' notes" |
| **Textract** | **Extract text + data from scanned forms/invoices** — understands tables and fields, **beyond simple OCR** | "process scanned documents/forms" |
| **Kendra** | **Intelligent document search** (natural-language answers from your docs). Connectors for S3, SharePoint, Confluence and more. | "enterprise search across wikis/manuals" |
| **Fraud Detector** | Detects **online fraud** | "fake account signups," "online payment fraud" |
| **Personalize** | **Recommendations** engine | "customers also bought" |
| **Forecast** | Time-series **predictions** | "predict inventory demand" |
| **Lex** | **Chatbots** (the tech behind Alexa) | "conversational bot" |
| **SageMaker** | Build/train/deploy **custom ML models** | "data scientists need to train models" |
| **SageMaker Autopilot** | AutoML: builds and tunes models automatically from your data | "build ML models **without ML expertise**" |
| **Pinpoint** | Multichannel **marketing/engagement** messages (email, SMS, push, voice), segmentation, analytics. An **event** = a user interaction with your app. | "targeted campaigns," "track user engagement" |
| **Elastic Transcoder** (legacy → **MediaConvert**) | Convert media files in S3 into playback formats | "convert videos for mobile devices" |

THE trap: scanned invoice/form extraction → **Textract**, not Rekognition (images ≠ documents) and not Comprehend (that's meaning, not extraction).

## Systems Manager (SSM) suite

One service, several exam-favorite features:

- **Session Manager** — shell access to instances with **no SSH keys, no bastion host, no open port 22**, all logged. Signal: *"secure instance access without opening inbound ports."*
- **Run Command** — execute scripts **across a fleet** at once, no SSH.
- **Patch Manager** — **automated OS patching** on a schedule (maintenance windows).
- **Hybrid**: install the SSM agent on **on-premises servers** and manage them alongside EC2.
- **Automation** — runbooks for common maintenance tasks (restart, patch, create AMIs) across EC2 and other resources.
- **OpsCenter** — a central inbox of operational issues. Each issue is an **OpsItem**.
- **Fleet Manager** — a single UI to remotely manage nodes on AWS or on-prem.

**Which agent?**

| Agent | Job |
|---|---|
| **SSM Agent** | Lets Systems Manager manage the instance: Run Command, Session Manager, Patch Manager (EC2, on-prem, VMs) |
| **CloudWatch agent** | Ships **memory/disk custom metrics and logs** to CloudWatch |
| **Inspector** | Vulnerability/CVE scanning. Inspector v2 uses the **SSM Agent**; the old standalone Inspector agent is legacy. |

**AWS Health dashboards:**
- **Service Health Dashboard** shows **public** status: "is AWS down in this Region for everyone?"
- **Personal Health Dashboard**, now the **AWS Health Dashboard – your account**, shows events affecting **your** resources (e.g., scheduled maintenance on your EC2 instance).

## Developer & app services

**AWS Batch** — run **long batch jobs** as Docker containers; schedules onto EC2/Spot for you. Signal: *"job runs for hours"* — the escape hatch from **Lambda's 15-minute limit**.

**AppSync** — managed **GraphQL** API. Signal words: "**GraphQL**," "**real-time subscriptions**," "**offline sync**" for mobile. Any of the three → AppSync.

**Amplify** — full-stack web/mobile app **quickstart**: hosting, auth, backend wired together. Signal: *"frontend team wants to build and deploy quickly without managing infrastructure."*

**SES (Simple Email Service)** — send **application emails** at scale (receipts, notifications, marketing). Signal: *"application must send emails."* (SNS emails are plain-text alerts for ops; SES is for real email.)

**S3 Batch Operations** — run one operation across **billions of EXISTING objects**: copy, tag, restore, or — the exam favorite — **"encrypt all existing objects in the bucket."** Default bucket encryption only covers *new* uploads; Batch Operations fixes history.

**Aurora cloning** (recap) — **copy-on-write clone** of a production Aurora DB in minutes, no full copy, cheap. Signal: *"test against production data quickly without impacting production."*

**X-Ray** — **distributed tracing**: follow one request across microservices to find the slow/broken hop. Signal: *"identify performance bottlenecks across microservices."* (CloudWatch = metrics/logs; X-Ray = the request's journey.)

**App Runner** — fully managed service that deploys a **containerized web app or API** from source code or a container image. It handles load balancing, scaling and TLS. Signal: *"deploy a web app from a container with no infrastructure/cluster management."*

**AppConfig** (part of Systems Manager) — **safely roll out application configuration and feature flags**, with validation and gradual deployment plus automatic rollback. Signal: *"change feature flags without redeploying code."*

**Amazon Connect** — cloud **contact center**. **Contact flows** define the caller experience: IVR menus, routing to queues or agents, callbacks.

**OpsWorks** (legacy — end of life 2024) — configuration management with **managed Chef and Puppet**: automates how servers are configured, deployed and managed across **EC2 and on-prem** machines. Signal: *"Chef"*, *"Puppet"*, *"recipes/cookbooks"* → OpsWorks. (Today the answer is usually SSM State Manager.)

**The Code\* toolchain** — **CodeCommit** = managed **private Git repositories** (source control; closed to new customers in 2024 but still a valid answer). **CodeDeploy** = fully managed **deployment automation** to **EC2, Fargate, Lambda and on-prem servers**. Signal: *"automate software deployments across EC2 and on-prem"* → CodeDeploy. (For context, **User Acceptance Testing (UAT)** is the last phase of software testing — the final environment before production.)

**AWS ParallelCluster** — AWS-supported **open-source cluster management tool** to deploy and manage **HPC clusters**. Signal: *"deploy and manage an HPC cluster"* → ParallelCluster (pair with Cluster placement group + EFA from Section 3).

**Odds and ends:**
- **Device Farm**: test mobile and web apps on many real devices.
- **Lightsail**: simple VPS bundles for beginners.
- **Cloud Map**: service discovery by custom names.
- **App Mesh**: service mesh for microservices.
- **IoT Core**: connect devices securely to the cloud.

**WorkDocs** (legacy — AWS ended support in 2025) — managed document creation, editing and sharing. It was **not** for serving static or object content; that's S3.

**AWS Artifact** — self-service portal to download **AWS compliance reports** (SOC, PCI, ISO). Signal: *"auditors need proof of AWS's compliance."* No agents, no config — just the download counter for paperwork.

## Question patterns

> *"Existing on-prem app uses RabbitMQ with AMQP; migrate with minimal code changes"* → **Amazon MQ** (protocol keywords = MQ; SQS would mean rewriting)

> *"HTTPS on CloudFront with a custom domain — where's the certificate?"* → **ACM in us-east-1** (CloudFront only reads certs from N. Virginia)

> *"IPv6-only instances need outbound internet access but must block inbound"* → **Egress-only Internet Gateway** (the IPv6 answer; NAT gateway is IPv4)

> *"Automatically extract fields and tables from scanned invoices"* → **Textract** (forms/documents, beyond OCR — not Rekognition)

> *"Migrate a self-managed Apache Kafka cluster with no application changes"* → **MSK** (the word Kafka does all the work)

> *"Mobile app needs a GraphQL API with real-time data sync"* → **AppSync** (GraphQL/subscriptions/offline = AppSync every time)

> *"Automatically apply OS security patches to 500 EC2 instances monthly"* → **SSM Patch Manager** (fleet patching on a schedule)

> *"Encrypt all existing objects already stored in an S3 bucket"* → **S3 Batch Operations** (default encryption only covers new objects)

> *"Data team needs managed Apache Spark for nightly processing at low cost"* → **EMR with Spot task nodes** (Spark = EMR; Spot = cheap)

> *"Regulations require workloads to run in the company's own datacenter using AWS services"* → **Outposts** (AWS racks on your floor — data residency)

> *"Shell access to private instances without SSH keys or bastion hosts"* → **SSM Session Manager** (no port 22, fully audited)

> *"Migrate Oracle to Aurora PostgreSQL"* → **DMS + SCT** (different engines = heterogeneous = add the Schema Conversion Tool)

> *"Discover on-prem servers and their dependencies to plan a migration"* → **Application Discovery Service** (inventory first; track progress in Migration Hub)

> *"Convert CSV in S3 to Parquet with the LEAST operational overhead"* → **Glue** (serverless ETL; EMR only if you need Spark/Hadoop control)

> *"Detect fake account signups / online payment fraud"* → **Fraud Detector** (not GuardDuty, which detects AWS account threats)

> *"Build ML models without ML expertise"* → **SageMaker Autopilot** (AutoML)

> *"Roll out feature flags gradually with automatic rollback"* → **AppConfig** (not Parameter Store alone, which has no validated rollout)

> *"Deploy a containerized web app with no infrastructure management"* → **App Runner** (simpler than ECS/EKS)

> *"Be notified when AWS maintenance affects YOUR instances"* → **AWS Health Dashboard – your account** (+ EventBridge), not the public Service Health page

> *"Stream a desktop app to users' browsers"* → **AppStream 2.0** (a full desktop → WorkSpaces; neither is a queue)

## Pocket card

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
| Inventory on-prem servers pre-migration | Application Discovery Service |
| Track migration progress | Migration Hub |
| Rehost servers (agent) vs move files | MGN vs DataSync |
| DMS Basic Schema Copy | Tables + PKs only → use SCT for prod |
| Serverless ETL / CSV→Parquet | Glue |
| Spark/Hadoop control | EMR |
| Batch jobs at scale | AWS Batch |
| Online fraud | Fraud Detector |
| AutoML | SageMaker Autopilot |
| Medical text NLP | Comprehend Medical |
| Marketing campaigns, user events | Pinpoint |
| Containerized web app, zero infra | App Runner |
| Chef / Puppet | OpsWorks (legacy) |
| Private Git repos / automated deploys to EC2 + on-prem | CodeCommit / CodeDeploy |
| Deploy & manage HPC clusters | AWS ParallelCluster |
| Feature flags / safe config rollout | AppConfig |
| Maintenance runbooks | SSM Automation |
| Ops issues inbox | SSM OpsCenter (OpsItems) |
| Memory/disk metrics | CloudWatch agent (not SSM Agent) |
| "Is AWS down?" vs "Is MY resource affected?" | Service Health vs AWS Health – your account |
| Stream one app vs full desktop | AppStream 2.0 vs WorkSpaces |
| Contact center / IVR | Amazon Connect |
| Third-party cert where ACM unsupported | IAM certificate store (legacy) |
| Bring your own drives to AWS site | Data Transfer Terminal |
| SWF / Data Pipeline / CloudEndure | Legacy → Step Functions / Glue / MGN |

That's the last jar on the spice rack — you've now covered the whole SAA-C03 kitchen. Sleep well, read the last sentence first, and go collect your certificate.
