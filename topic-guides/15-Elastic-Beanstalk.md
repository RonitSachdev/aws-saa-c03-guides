# Section 15: Elastic Beanstalk

## The idea

Elastic Beanstalk is AWS saying: **"here's my code, you figure out the rest."**

Think of it as moving into a **fully furnished apartment**. You could buy land, pour a foundation, and wire the electricity yourself (raw EC2 + ASG + ALB by hand) — or you could just show up with your suitcase (your code) and everything is already set up. But here's the key difference from a hotel: **you still get the keys to every room**. You can rearrange furniture, swap appliances — nothing is locked away.

Concretely: you upload your code — **Java, Python, Node.js, .NET, Go, Ruby, PHP, or Docker** — and Beanstalk automatically provisions **EC2 instances, an Auto Scaling Group, a Load Balancer, and CloudWatch monitoring**. You didn't configure any of them, but you *can* see and tune all of them.

Two exam-critical identity facts:

- **EB is an orchestrator, NOT a black box.** You retain **full control of the underlying resources**. The identity phrase the exam loves: *"deploy a web application quickly without managing infrastructure BUT retain control over the resources."* That sentence = Beanstalk.
- **EB itself is free** — you pay only for the resources it creates (EC2, ALB, etc.).
- **Where your files go**: Beanstalk stores your **application versions (source bundles)** and, optionally, **server/instance logs** in an **S3 bucket** it creates per Region (`elasticbeanstalk-<region>-<account>`).

Config tweaks live in **`.ebextensions`** — YAML/JSON files in your code bundle that customize the environment (packages, env vars, resources).

There's also a **Worker environment**: instead of serving web traffic, it pulls jobs from an **SQS queue** — the background-processing tier of your app.

## THE tested table: deployment policies

This table is the single most-tested Beanstalk fact. Learn to match constraint → row.

| Policy | How it works | Downtime? | Capacity during deploy | Extra cost? | Rollback | Pick when... |
|---|---|---|---|---|---|---|
| **All at once** | Update every instance simultaneously | **YES** | Drops to zero briefly | No | Redeploy old version (slow) | Fastest; **dev/test, downtime OK** |
| **Rolling** | Update in batches, batch by batch | No | **Reduced** (a batch is always down) | **No** | Slow (roll batches back) | **No downtime + no extra cost** |
| **Rolling with additional batch** | Spin up one extra batch first, then roll | No | **FULL capacity maintained** | Small (one extra batch) | Slow | Can't afford reduced capacity |
| **Immutable** | Build a **whole new fleet** alongside the old, swap when healthy | No | Full | Double, briefly | **Safest: just delete new fleet** | Production, **safest rollback** |
| **Blue/Green** | Clone the entire **environment**, test it, then **swap DNS CNAMEs** | No | Full | Double while both exist | **Instant: swap CNAME back** | Test new version with real URL, instant switch |

Constraint-matching cheats:
- "Fastest, downtime acceptable" → **All at once**
- "No downtime, no additional cost" → **Rolling**
- "Must maintain full capacity" → **Rolling with additional batch**
- "Safest / easiest rollback if instances fail" → **Immutable**
- "Test new version, then instant cutover / instant rollback via DNS" → **Blue/Green (CNAME swap)**

## THE RDS trap

If you create an RDS database **inside** a Beanstalk environment, its lifecycle is **tied to the environment** — terminate or rebuild the environment, and **the database dies with it**.

```
DEV:   [ EB Environment ]           PROD:  [ EB Environment ]     [ RDS ]
       |  EC2 + ASG + ALB |                |  EC2 + ASG + ALB | -->(env vars:
       |  RDS  <-- dies    |               |                  |    conn string)
       |       with env!   |               +------------------+   lives forever
       +------------------+
```

**Production rule: RDS lives OUTSIDE the environment**, and the app gets the **connection string via environment variables**.

Migration path if you already made the mistake: take an **RDS snapshot → restore as a standalone RDS instance** → point the environment at it via env vars → enable deletion protection.

## When Beanstalk is the distractor

EB is often a wrong answer planted next to the right one:

| Question really wants | Correct answer |
|---|---|
| Fine-grained, repeatable **infrastructure as code** | **CloudFormation** |
| **Microservices at scale** / container orchestration | **ECS / EKS** |
| **Event-driven**, sub-15-minute functions | **Lambda** |

EB is for: *one classic web app, developers who want speed, control retained.*

## Question patterns

> *"Developers want to deploy code quickly without managing infrastructure but must retain full control of the underlying resources"* → **Elastic Beanstalk** (that's its identity phrase verbatim)
> *"Deploy new version as fast as possible; brief downtime is acceptable (dev environment)"* → **All at once** (speed + downtime-OK = the only reason to pick it)
> *"Deploy with no downtime and no additional cost"* → **Rolling** (batches reuse existing instances, capacity dips but nothing new is billed)
> *"Deploy with no downtime while maintaining full capacity"* → **Rolling with additional batch** (the extra batch covers the gap)
> *"Deployment must be safest possible with quick rollback if health checks fail"* → **Immutable** (bad deploy? delete the new fleet, old one untouched)
> *"Test the new version against a separate URL, then switch all traffic instantly with instant rollback"* → **Blue/Green with CNAME swap** (DNS swap both ways)
> *"Beanstalk app's database was lost when the environment was terminated — prevent this in production"* → **Create RDS outside the environment; connect via environment variables** (decouple lifecycles)
> *"Migrate a database out of an existing Beanstalk environment"* → **Snapshot the RDS instance → restore as standalone RDS** (then reconnect via env vars)
> *"Long-running background jobs from a queue alongside a Beanstalk web app"* → **Worker environment** (the SQS-consuming tier)
> *"Customize packages and configuration of Beanstalk instances at deploy time"* → **.ebextensions** (config files in the source bundle)

## Pocket card

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
| Where EB keeps app versions + logs | S3 bucket |
| Fine-grained IaC instead | CloudFormation |

Beanstalk fronts your app with a load balancer automatically — but when your "app" is an API consumed by other programs, you want a smarter front door: API Gateway, next section.
