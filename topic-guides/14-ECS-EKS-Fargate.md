# Section 14: ECS, EKS & Fargate

## The idea

Before containers, shipping software was chaos. Your app worked on your laptop, then exploded on the server because the server had a different Python version, a missing library, a different OS. The dreaded phrase: **"but it works on my machine!"**

Containers fix this the same way shipping containers fixed global trade. Before standardized steel boxes, dock workers hand-loaded barrels, crates, and sacks — slow, fragile, different for every ship. Then someone said: *put everything in an identical steel box, and every crane, ship, and truck in the world handles it the same way.* A software container is that steel box: your **app plus its entire environment** (runtime, libraries, config, OS dependencies) packaged into one **image**. If it runs in the container on your laptop, it runs identically anywhere.

On the compute spectrum, containers are the **middle ground between Lambda and EC2**: more control and longer-running than Lambda (no 15-minute limit), less babysitting than raw EC2.

But now a new problem: real applications run *hundreds* of containers. Who restarts one when it crashes? Who spreads them across machines? Who wires them to the load balancer? Doing this by hand is like being a harbor master directing every crane manually. You need an **orchestrator** — a robotic harbor master. AWS gives you two: **ECS** (Elastic Container Service — AWS's own, simple) and **EKS** (Elastic Kubernetes Service — managed Kubernetes, the open-source industry standard).

## ECS vocabulary — learn these four words cold

| ECS term | What it is | Analogy |
|---|---|---|
| **Task Definition** | JSON blueprint: which image, CPU/RAM, ports, env vars, IAM roles | The recipe |
| **Task** | One running copy of that definition | A dish cooked from the recipe |
| **Service** | Keeps N tasks running, replaces crashed ones, wires them to an ALB | The babysitter |
| **Cluster** | Logical grouping of the infrastructure the tasks run on | The kitchen |

## Launch types: EC2 vs Fargate

```
                 ECS or EKS (the orchestrator brain)
                        /              \
             EC2 launch type       Fargate launch type
             ----------------      ---------------------
             YOU manage the        NO instances visible.
             instances (patch,     Declare CPU + RAM per
             scale, choose type)   task. AWS runs it.
             + GPUs possible       + zero server mgmt
             + Spot instances      + Fargate Spot for
               for cost tricks       interruptible work
                                   - NO GPUs (!)
```

- **EC2 launch type**: containers run on EC2 instances *you* manage. You pick instance types, you patch, you can use **Spot instances** for cost savings, and — crucially — you can attach **GPUs**.
- **Fargate**: **serverless containers**. You declare CPU and memory per task; AWS provisions invisible compute. The moment an exam question says **"no server management"** or "without managing infrastructure" for containers → **Fargate**.

**THE trap: Fargate does NOT support GPUs.** "Containerized ML inference needing GPUs" → **EC2 launch type**, never Fargate. This nuance is tested.

**Misconception to kill:** Fargate is **not a third orchestrator**. It's a compute layer that plugs into **BOTH ECS and EKS**. ECS/EKS decide *what* runs; Fargate is one option for *where* it runs.

## When EKS? Only two signals

Default to **ECS** unless the question says:
1. **"Already using Kubernetes"** (on-prem k8s migration, existing k8s tooling/manifests), or
2. **"Portability / multi-cloud / avoid vendor lock-in"** (Kubernetes runs anywhere; ECS is AWS-only).

No k8s keyword? **ECS.** It's simpler and AWS-native. (*"Docker containers, no Kubernetes needed"* → ECS; *"Kubernetes + serverless / no nodes"* → **EKS on Fargate**.)

### EKS fine print the exam pulls from

- **Control plane**: in EKS, **AWS runs the Kubernetes control plane across multiple AZs** (HA, patched for you); you run (or Fargate runs) the worker nodes.
- **On-premises flavors**: **EKS Anywhere** = run EKS-distribution Kubernetes on **your own hardware** — **you** manage the clusters (control plane included). **ECS Anywhere** = register on-prem servers as ECS capacity, managed from the ECS control plane. **EKS Connector** = only **registers/views** an external Kubernetes cluster (any provider) in the EKS console — it does not manage it.
- **Node autoscaling**: **Cluster Autoscaler** scales nodes through **Auto Scaling groups** (fixed instance types per node group). **Karpenter** provisions nodes **directly**, choosing the right instance type/size per pending pods dynamically — faster, better bin-packing, **less operational overhead** → the modern answer for *"efficient EKS node scaling, minimal ops."*
- **Access control**: **authentication = IAM** (AWS IAM Authenticator; IAM principals mapped via the **`aws-auth` ConfigMap**, auto-created with managed node groups / `eksctl`, now also **EKS access entries**); **authorization = Kubernetes RBAC** (Roles/RoleBindings). *"Give an IAM role read-only access to one namespace"* → map it in aws-auth/access entries **+** a Kubernetes RBAC Role.

## ECR — the image warehouse

**ECR (Elastic Container Registry)** stores your container images (like Docker Hub, but private and IAM-integrated). Bonus exam fact: ECR does **image vulnerability scanning** — "scan container images for CVEs" → **ECR scanning**.

## THE role trap pair (guaranteed points)

Two IAM roles per task, constantly confused:

| Role | Used by | For | Symptom when wrong |
|---|---|---|---|
| **Task Execution Role** | ECS agent (plumbing) | **LAUNCHING**: pull image from ECR, write logs to CloudWatch | "Task fails to start / **can't pull image**" |
| **Task Role** | Your app code inside | What the **app does once running**: S3, DynamoDB, SQS calls | "**App gets AccessDenied** calling DynamoDB" |

Hook: **Execution = getting the container up. Task Role = what the app does once it's up.**

Both are **IAM roles** (trusted by `ecs-tasks.amazonaws.com`) — not resource-based policies. Secrets go in the task definition's **`secrets`** parameter (Secrets Manager / Parameter Store), read by the **execution role** — see Section 21.

## Networking and scaling facts

- **awsvpc network mode**: every task gets its **own ENI** (Elastic Network Interface — its own private IP) and therefore its **own security group**. "Per-container security group" → awsvpc. (Required mode on Fargate.)
- **ALB dynamic port mapping**: on the EC2 launch type, an Application Load Balancer can route to **multiple tasks of the same service on one instance**, each on a random host port. No manual port juggling.
- **Service Auto Scaling**: scale task count on **CPU, memory, or SQS queue depth**. Target-tracking predefined metrics: **`ECSServiceAverageCPUUtilization`**, **`ECSServiceAverageMemoryUtilization`**, **`ALBRequestCountPerTarget`**.
- **Fargate Spot**: discounted Fargate for **interruption-tolerant** workloads.
- **Pricing**: **Fargate** bills for the **vCPU + memory requested** per task (per second); the **EC2 launch type** has **no extra ECS charge** — you pay for the EC2 instances (and EBS) whether tasks fill them or not.
- **Shared persistent storage** across tasks (EC2 or Fargate, multi-AZ) → mount **EFS** in the task definition.
- **App Runner**: even simpler than ECS/Fargate for a containerized web app/API — see Section 37.

## The compute ladder (which service for which job)

| Signal in question | Answer |
|---|---|
| Event-driven, runs **< 15 min** | Lambda |
| Containers, **no infrastructure management** | Fargate |
| Containers needing **GPU / deep instance control / Spot** | ECS on EC2 |
| **Kubernetes** / multi-cloud portability | EKS |
| Classic web app, "just deploy my code" | Elastic Beanstalk |
| Full OS control, custom everything | EC2 |

## Question patterns

> *"Run containers without managing any servers or clusters of instances"* → **Fargate** (the phrase "no server management" is the trigger)
> *"Company runs Kubernetes on-premises and wants to migrate to AWS with minimal changes"* → **EKS** ("already Kubernetes" is one of only two EKS signals)
> *"ECS task fails to start; error pulling image from ECR"* → **Task Execution Role** (launch plumbing = execution role)
> *"Application inside the container gets AccessDenied calling DynamoDB"* → **Task Role** (app-level permissions once running)
> *"Containerized GPU-based ML inference, minimize management"* → **ECS on EC2 launch type** (Fargate has NO GPUs)
> *"Automatically scan container images for vulnerabilities"* → **ECR image scanning** (built into the registry)
> *"Assign a dedicated security group to each container/task"* → **awsvpc network mode** (per-task ENI = per-task SG)
> *"Avoid vendor lock-in / portable across clouds"* → **EKS** (Kubernetes is the portability play)
> *"Cost-optimize fault-tolerant containerized batch jobs on Fargate"* → **Fargate Spot** (interruptible = Spot)
> *"Scale container count based on messages waiting in a queue"* → **ECS Service Auto Scaling on SQS queue depth**
> *"Run Kubernetes on our own data-center hardware with EKS tooling"* → **EKS Anywhere** (you manage the cluster)
> *"View on-prem/other-cloud Kubernetes clusters in the EKS console"* → **EKS Connector** (view only)
> *"Scale EKS worker nodes efficiently, right-sized instance types, least ops"* → **Karpenter** (not Cluster Autoscaler + ASGs)
> *"Grant an IAM role access to specific Kubernetes namespaces"* → **aws-auth ConfigMap / access entries (authN) + Kubernetes RBAC (authZ)**
> *"Containers in several AZs need a shared file system"* → **EFS volume** in the task definition
> *"Kubernetes workloads with no nodes to manage"* → **EKS on Fargate**

## Pocket card

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
| EKS control plane | AWS-managed, multi-AZ |
| Kubernetes on own hardware | EKS Anywhere (you manage) |
| On-prem servers as ECS capacity | ECS Anywhere |
| See external k8s clusters in console | EKS Connector |
| Dynamic right-sized EKS nodes | Karpenter (vs Cluster Autoscaler → ASGs) |
| EKS authN / authZ | IAM (aws-auth) / Kubernetes RBAC |
| Fargate pricing | vCPU + memory requested |
| ECS on EC2 pricing | No extra charge — pay for instances |
| Shared storage across tasks | EFS |
| ECS target-tracking metrics | ECSServiceAverageCPU/MemoryUtilization, ALBRequestCountPerTarget |

Once your containers are running, the next question is: what if you don't even want to think about containers — you just want to hand AWS your code? That's Elastic Beanstalk, up next.
