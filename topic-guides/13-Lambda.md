# Section 13: Lambda

## The idea

Imagine a contractor who **materializes on your doorstep the instant the doorbell rings**, does exactly one job, vanishes — and bills you only for the minutes he existed. No salary, no idle time, no office. Ring the bell a thousand times at once? A thousand contractors materialize in parallel. **That's Lambda: code without a computer.**

Spell it out: Lambda is **serverless compute**. You upload a **function** (your code), tell AWS what **event** triggers it (an S3 upload, an API call, a schedule), and AWS runs it — provisioning, scaling, and patching invisible to you. You pay **per millisecond of execution**, and it **scales automatically per event**. No traffic = no cost. This is *event-driven* architecture: things happen, code reacts.

### Hard limits — where half the traps live

| Limit | Value |
|---|---|
| **Max execution time** | **15 MINUTES** |
| Memory | **128 MB – 10 GB** |
| CPU | **scales WITH memory** (no separate CPU knob) |
| Ephemeral `/tmp` storage | up to **10 GB** |
| Deployment package | **50 MB zipped / 250 MB unzipped** |
| Container image | up to **10 GB** |
| Default concurrency per region | **1,000** (raisable) |

**THE trap:** *"a 2-hour video processing job"* → **NOT Lambda** — 15-minute ceiling. Answer: **AWS Batch** or **ECS/Fargate**. **Step Functions** is only right if the work can be **divided into chunks under 15 minutes each**.

**THE trap (the counterintuitive favorite):** *"CPU-bound Lambda function is slow — how to speed it up?"* → **increase the memory**. There's no CPU setting; **more memory = more CPU**. It reads like a wrong answer. It's the right one.

### Three ways a Lambda gets invoked

Think of how mail reaches you: someone **hands it to you and waits** for a reply, someone **drops it through the slot** and leaves, or **you walk to the PO box** and collect a batch.

1. **Synchronous** (hand-delivered): the caller **waits** for the result. Classic: **API Gateway** → Lambda. Errors go straight back to the caller.
2. **Asynchronous** (through the slot): the source **PUSHES** the event and walks away — **S3, SNS, EventBridge**. Lambda queues it, and on failure **retries twice**, then the event is **gone** — unless you configure a **DLQ (dead-letter queue) or failure destination**. **THE trap:** *"asynchronously invoked events are lost on failure"* → **add a DLQ / on-failure destination**.
3. **Event Source Mapping** (PO box): for **SQS, Kinesis, and DynamoDB Streams**, the source doesn't knock — **Lambda PULLS**, polling the stream/queue and grabbing records **in batches**. Failed batches go **back to the queue** and eventually to the **queue's own DLQ**. Push vs pull: knockers (S3/SNS/EventBridge) vs buckets you must visit (SQS/Kinesis/Streams).

### Cold starts and the two "concurrencies"

First invocation after idle, AWS must materialize the contractor — load runtime + code. That pause is a **cold start**, and it shows up as *"sporadic latency spikes after periods of inactivity."*

Two similarly-named settings, opposite jobs — hook: **P = Pre-warmed, R = Restricted**:

- **Provisioned Concurrency** = **Pre-warmed** instances always ready → **kills cold starts**. Answer to latency questions.
- **Reserved Concurrency** = a **Restricted cap** on how many copies can run at once → **protects downstream systems** (e.g., a fragile legacy database that dies past 50 connections).

### Lambda in a VPC

By default Lambda runs outside your VPC and can reach the internet but not your private resources. Put it **in the VPC** (it gets an **ENI** — Elastic Network Interface — in your subnet) and it can reach private RDS... but **it LOSES internet access**. Need both? **NAT Gateway** (or VPC endpoints for AWS services).

And whenever **Lambda talks to RDS**: hundreds of short-lived functions each opening their own DB connection will exhaust the database. The answer is **RDS Proxy** — a connection pooler that shares a warm pool of connections. Lambda + RDS in the same sentence → **RDS Proxy**, always.

### Odds and ends the exam sprinkles in

- **Execution role**: the **IAM role attached to the function** IS its permissions. "Lambda can't write to DynamoDB" → fix the execution role.
- **Execution role vs resource-based policy** — two directions, two documents:
  - **Resource-based (function) policy** = **who can invoke ME** (S3, SNS, API Gateway, another account). *"S3 can't trigger the function"* / *"cross-account invoke"* → add permission to the **function policy**.
  - **Execution role** = **what I can access**. When the function calls S3, DynamoDB, SQS, or **KMS**, AWS evaluates the **execution role** (the principal is the assumed role session, not the function ARN). So a **KMS key policy** or bucket policy must grant the **execution role**, not "the Lambda function."
- **Layers**: package **shared libraries/dependencies** once, reuse across functions.
- **Container images**: deploy Lambda as a container up to **10 GB** — the answer when dependencies blow past the 250 MB zip limit.
- **Environment variables**: config outside code; encrypt secrets with **KMS**. They're **encrypted at rest by default**, but anyone with console/`GetFunctionConfiguration` access **sees them in plaintext** — real secrets (DB passwords, API keys) belong in **Secrets Manager / Parameter Store**, fetched at runtime.
- **EventBridge scheduled rule → Lambda** = **serverless cron**. Any *"run a task every night at 2 AM without servers"* → this.

### Code at the edge: Lambda@Edge vs CloudFront Functions

Both run code at CloudFront edge locations; the split is muscle vs speed:

| | **Lambda@Edge** | **CloudFront Functions** |
|---|---|---|
| Runtime | Node.js/Python, up to seconds | JavaScript only, **sub-millisecond** |
| **Network calls** | **YES** | **NO** |
| Hooks | **viewer + origin** request/response | **viewer** request/response only |
| Cost | baseline | **~1/6 the price** |
| Use | **JWT/auth validation, origin selection**, real logic | **header manipulation, URL rewrites/redirects** — trivial tweaks at massive scale |

Rule: *needs external calls or real logic* → **Lambda@Edge**; *trivial header/URL tweak on every request* → **CloudFront Functions**.

## Question patterns

> *"90-minute video transcoding job — can it run on Lambda?"* → **No — AWS Batch / Fargate** (15-minute hard limit; Step Functions only if divisible into <15-min steps)
> *"Generate a thumbnail whenever an image lands in S3"* → **S3 event notification → Lambda** (the canonical async trigger)
> *"API is fast normally but has latency spikes after idle periods"* → **Provisioned Concurrency** (Pre-warmed = no cold starts)
> *"Lambda scaling overwhelms a legacy database that handles only 50 connections"* → **Reserved Concurrency** cap (Restricted) — and mention **RDS Proxy**
> *"Lambda must query an RDS database in a private subnet"* → **attach Lambda to the VPC + RDS Proxy** (add NAT if it still needs internet)
> *"CPU-intensive function is too slow"* → **increase memory** (CPU scales with memory — the counterintuitive one)
> *"Run a cleanup script every night at 2 AM, no servers"* → **EventBridge schedule → Lambda** (serverless cron)
> *"Validate JWT tokens / call an external auth service at the edge"* → **Lambda@Edge** (network calls allowed; CF Functions can't)
> *"Rewrite URLs or add security headers on millions of requests, cheapest"* → **CloudFront Functions** (sub-ms, ~1/6 price, no network)
> *"Asynchronously invoked function fails and events disappear"* → **DLQ / on-failure destination** (async retries twice, then drops)
> *"Lambda should process SQS messages"* → **Event Source Mapping** (Lambda pulls in batches; failures return to the queue)
> *"S3 in another account must invoke the function"* → **Resource-based (function) policy** (who can invoke me)
> *"Lambda gets AccessDenied decrypting with a KMS key"* → **Grant the execution role in the key policy / role policy** (the role is the principal, not the function)
> *"Store a DB password for Lambda so console users can't read it"* → **Secrets Manager / Parameter Store SecureString**, not plain env vars

## Pocket card

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
| Who can invoke the function | Resource-based (function) policy |
| Lambda → KMS/S3/DynamoDB access checked against | Execution role (not function ARN) |
| Secrets visible in env vars | Secrets Manager / Parameter Store |
| Edge + network calls / JWT | Lambda@Edge |
| Edge header/URL tweak, cheapest | CloudFront Functions |
| Max runtime / memory / concurrency | 15 min / 10 GB / 1,000 default |

Lambda is the glue of every serverless diagram you've built so far — CloudFront to API Gateway to Lambda to DynamoDB — and with these four sections you now own that entire stack end to end.
