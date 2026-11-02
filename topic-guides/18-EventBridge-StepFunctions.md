# Section 18: EventBridge & Step Functions

## The idea

Modern AWS apps are event-driven: something happens somewhere ("an order was placed", "it's 2 AM", "a Zendesk ticket was created"), and something else needs to react. Two services own this space, and the exam loves both.

Picture a **railway control room**. **EventBridge** is the switchboard operator: trains (events) roll in from every direction — AWS services, outside SaaS companies, your own apps — and the operator reads each train's manifest and routes it down the right track to the right destination. **Step Functions** is the station master with a clipboard: it doesn't route random trains, it runs one *planned journey* from start to finish — "stop here, wait there, if the signal is red take the branch line, retry the crossing three times" — and writes down every step in a logbook.

Spell out the jargon: **EventBridge** (formerly **CloudWatch Events** — same engine, bigger brand) is a serverless **event bus**: a pipe that receives structured JSON events and matches them against **rules** to decide where they go. **Step Functions** is a **workflow orchestrator**: you define a **state machine** (a flowchart in JSON) that coordinates Lambda functions and other services step by step.

## EventBridge: the event router of AWS

The flow is always the same three-parter:

```
 SOURCES                    BUS + RULES                 TARGETS
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│ AWS services │──event──▶│  Event bus   │──match──▶│ Lambda       │
│ SaaS partners│          │  Rule: does  │          │ SQS / SNS    │
│ (Zendesk,    │          │  the event   │          │ Step Functions│
│  Datadog...) │          │  pattern     │          │ Kinesis      │
│ Custom apps  │          │  match?      │          │ ...20+ more  │
└──────────────┘          └──────────────┘          └──────────────┘
```

- **Sources**: nearly every AWS service emits events ("EC2 instance state changed to stopped"), **SaaS partners** like Zendesk, Datadog, Auth0, Shopify deliver events straight onto a **partner event bus**, and your own apps can `PutEvents` custom events.
- **Rules** do **content-based filtering**: match on **any field** of the event JSON — source, detail-type, or deep inside the payload ("only orders where `amount > 1000`" style pattern matching). This rich filtering is EventBridge's signature move.
- **Targets**: Lambda, SQS, SNS, Step Functions, Kinesis, ECS tasks, another event bus... one rule can fan to multiple targets.

Extra features the exam pokes at:

- **Scheduled rules = serverless cron.** "Run a Lambda every night at 2 AM" → EventBridge schedule (cron or rate expression) → Lambda. **No EC2 instance running crontab** — that's the wrong answer every time.
- **Archive + replay**: record events on a bus, then **replay** them later — perfect for reprocessing after a bug fix.
- **Schema registry**: EventBridge discovers event structures and generates code bindings, so developers know what fields to expect.
- **Cross-account event buses**: send events from account A's bus to account B's bus — the standard pattern for centralizing events in a multi-account org.

**THE trap: EventBridge vs SNS.** Both "send events to targets", so exams bait you. **EventBridge** = **rich content filtering, AWS-service and SaaS event routing, scheduling, archive/replay**. **SNS** = **massive fan-out push** (millions of subscribers, mobile push, SMS, email). "Route events from a SaaS provider" or "filter on event content" → EventBridge. "Fan one message out to huge numbers of subscribers" → SNS.

## Step Functions: the workflow orchestrator

A **state machine** is your flowchart; each box is a **state**:

| State | What it does | Exam cue |
|---|---|---|
| **Task** | Do work (invoke Lambda, ECS, DynamoDB, etc.) | the worker step |
| **Choice** | If/else branching | "different path based on result" |
| **Wait** | Pause for time or until a timestamp | "wait 3 days then..." |
| **Parallel** | Run branches at the same time | "simultaneously" |
| **Map** | For-each over an array of items | "process each item in a list" |
| **Retry/Catch** | **Exponential backoff retries built in** | "retry with backoff **without custom code**" |

That last row is gold: *"retry failed steps with exponential backoff without writing custom retry code"* → **Step Functions**, full stop.

**THE trap: Lambda-chaining.** The scenario: a multi-step process where Lambda A calls Lambda B calls Lambda C, and it's fragile, or the whole thing needs **more than 15 minutes** (the Lambda hard timeout), or the business needs **error handling and an audit of every step**. The answer is **never** "Lambdas calling Lambdas" — it's **Step Functions orchestrating the Lambdas**. You get visual workflow, per-step retry, and full execution history for free.

**Standard vs Express workflows** — memorize this table:

| | **Standard** | **Express** |
|---|---|---|
| Max duration | **1 YEAR** | **5 minutes** |
| Pricing | per **state transition** | per execution/duration (cheaper at volume) |
| Execution history | full **audit history** in console | CloudWatch Logs only |
| Fit | long-running, **human approval**, audit-heavy | **high-volume, short** (IoT ingestion, streaming) |

"Workflow includes a **human approval step**" or "runs for days" → **Standard**. "**Hundreds of thousands of short IoT events** per second, cost-sensitive" → **Express**.

Why it survives failures: Step Functions **maintains application state** — it tracks exactly which step each execution is on and logs the data passed between steps, so if a network fails or a component hangs, the workflow **resumes where it left off**. It stitches together Lambda, **Fargate/ECS**, SageMaker, DynamoDB, and more.

### SWF — the legacy orchestrator

**Amazon SWF (Simple Workflow Service)** is the older, **non-serverless** way to coordinate multi-step work across **distributed** components: a managed **state tracker and task coordinator**. You run the workers yourself (typically on **EC2** or on-prem).

| Actor | Role |
|---|---|
| **Workflow starter** | Kicks off a workflow execution (e.g. the app when an order is placed) |
| **Decider** | Holds the **control logic** — decides which task runs next |
| **Activity worker** | Does the actual task (can even be a **human** step) |

- Guarantee to remember: SWF **assigns each task exactly once and never duplicates it**.
- It manages workflows — it is **not** a monitoring/notification service.
- Classic SWF-flavored scenarios: a **multi-step, multi-decision e-commerce checkout**, orchestrating **distributed business processes** with **EC2 + SWF**, media processing pipelines.

THE trap: on the modern exam, **Step Functions is the default answer** for orchestration (serverless, visual, built-in retries). Pick **SWF** only when the question explicitly needs it — **external signals** into a running workflow, **child workflows**, or an existing SWF/legacy setup. Want serverless *batch jobs* instead of orchestration? That's **AWS Batch**.

## Question patterns

> *"Run a cleanup Lambda every night at 2 AM without managing servers."* → **EventBridge scheduled rule → Lambda** (serverless cron, no EC2 crontab).

> *"Ingest events from Zendesk/Datadog into AWS and route them to Lambda."* → **EventBridge partner event bus** (SaaS integration is EventBridge's exclusive turf).

> *"Order workflow needs retries, error handling, and a manual approval step that may take days."* → **Step Functions Standard** (up to 1 year + human-in-the-loop).

> *"Multi-step data pipeline of Lambdas exceeds 15 minutes end to end."* → **Step Functions** (orchestrate, don't chain — Lambda's 15-min cap is per function, the workflow can run far longer).

> *"Process each item in an array of records as a separate step."* → **Map state** (built-in for-each).

> *"Need an audit trail showing the input/output of every step of each execution."* → **Step Functions Standard** execution history.

> *"Route only events where a specific JSON field matches a value, to different targets."* → **EventBridge rule with content-based filtering**.

> *"Millions of short-lived, high-frequency workflow executions at lowest cost."* → **Step Functions Express**.

> *"Reprocess last week's events after fixing a bug."* → **EventBridge archive + replay**.

> *"Retry a failing step with exponential backoff, no custom retry code."* → **Step Functions Retry** (built into the state definition).

> *"Workflow must resume exactly where it left off after a component hangs or the network fails."* → **Step Functions** (tracks state + logs data between steps).

> *"Coordinate tasks across distributed EC2 workers; each task must be assigned exactly once, never duplicated; uses deciders and activity workers."* → **Amazon SWF** (legacy; otherwise prefer Step Functions).

> *"New serverless orchestration of multiple services with branching and retries."* → **Step Functions** (not SWF — SWF isn't serverless).

## Pocket card

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
| Resume after failure / app state tracking | Step Functions |
| Starter / decider / activity worker | SWF (legacy) |
| Task assigned once, never duplicated | SWF |
| SWF vs new serverless workflow | Step Functions by default |

EventBridge decides *which* work should happen when an event arrives; Step Functions makes sure multi-step work *finishes correctly* — and next we meet the services that watch everything else: CloudWatch, CloudTrail, and Config.
