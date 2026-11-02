# Section 28: CloudFormation

## The idea

Imagine you bake a spectacular cake once by improvising — a pinch of this, a swirl of that. Now bake an identical one next week. You can't; you never wrote it down. Clicking around the AWS console is improvised baking. **CloudFormation is the written recipe**: you describe your entire infrastructure — VPCs, EC2, RDS, IAM roles, everything — in a **YAML or JSON template**, and AWS "cooks" it for you. A running instance of a recipe is called a **stack**.

This is **Infrastructure as Code (IaC)** — AWS's native answer to Terraform, and it can model third-party resources too: templates live in version control, deploy identically to dev/test/prod or to a new region, and delete cleanly in one command. If creation fails partway, CloudFormation **rolls back automatically by default** — no half-baked cakes left in the oven.

## Template anatomy (know the section names)

| Section | Job |
|---|---|
| **Parameters** | Inputs at deploy time (instance size, env name) |
| **Mappings** | Lookup tables, e.g. the right AMI ID per region |
| **Conditions** | "Only create this in prod" logic |
| **Resources** | **The only REQUIRED section** — what actually gets built |
| **Outputs** | Values to surface after creation; **Export** them and another stack reads them with **Fn::ImportValue** (cross-stack references) |

Intrinsic function one-liners: **!Ref** = reference a parameter/resource, **!GetAtt** = grab an attribute of a resource (like an instance's DNS name), **!Sub** = substitute variables into a string.

## Features → scenarios (this is the exam meat)

- **Change Sets** — a **preview** of exactly what an update would create/modify/delete *before* you apply it. "Team wants to see what a stack update will do first" → Change Set.
- **Stack Policies** — protect specific resources within a stack **from being modified by stack updates**.
- **Drift Detection** — answers "did someone hand-edit our resources in the console?" Compares live reality to the template. "Detect manual changes" → Drift Detection.
- **StackSets** — deploy **one template to MANY accounts and regions** in one operation. "Roll out a security baseline across the whole organization" → StackSets.
- **Nested Stacks** — stacks inside stacks; package common patterns (a standard VPC, say) as reusable components.
- **DeletionPolicy** — per-resource instruction for stack deletion: **Retain** (keep the resource) or **Snapshot** (snapshot it first — works for RDS, EBS, etc.). "Keep the database when the stack is deleted" → DeletionPolicy: Retain.

**Resource attributes (the "policy" family):**

| Attribute | When it acts | What it does | Cue |
|---|---|---|---|
| **CreationPolicy** (+ **cfn-signal**) | **CREATE** | Stack **waits** for N success signals (with a timeout) before marking the resource complete; the instance runs the **`cfn-signal` helper script** once software is installed/configured | "Don't continue until the app on EC2 is actually running" — memory hook: **CREATE + WAIT** |
| **DependsOn** | Create/delete order | Forces resource B to be created **after** resource A | "Resource must exist before another" — ordering only |
| **UpdatePolicy** | **UPDATE** of an ASG (etc.) | How updates roll out: **rolling update** in batches or replacing the ASG | "Update ASG instances in batches without downtime" |
| **UpdateReplacePolicy** | **UPDATE that replaces** a resource | **Retain**/**Snapshot** the *old* physical resource instead of deleting it | "Keep the old DB when an update forces replacement" |
| **DeletionPolicy** | **Stack DELETE** (or resource removal) | Retain / Snapshot / Delete | "Keep data when stack is deleted" |

THE trap: **DependsOn only orders creation — it doesn't know whether the software inside the instance works.** "Wait until the application is installed and running before stack creation proceeds" → **CreationPolicy + cfn-signal**, not DependsOn.

THE trap: manual console edits to stack-managed resources don't update the template — they create *drift*, and the next stack update can stomp them. The cure is Drift Detection (to find it) and discipline (to stop it).

**CDK in one line:** the Cloud Development Kit lets you write infrastructure in **Python/TypeScript/Java**, which *compiles down to CloudFormation templates*. "Developers want to define infrastructure in a real programming language with loops and logic" → **CDK**.

**Elastic Beanstalk contrast:** Beanstalk is web-app-shaped automation — hand it code, it builds the standard web stack (and uses CloudFormation underneath). CloudFormation itself can build **any** infrastructure in any shape. Beanstalk = specific meal deal; CloudFormation = whole grocery store.

## Question patterns

> *"Team must review what changes a template update will make before applying it"* → **Change Sets** (preview = change set, always)

> *"Deploy standardized security/compliance resources to all accounts in an organization, across regions"* → **CloudFormation StackSets** (one template → many accounts/regions)

> *"Ensure the RDS database is not deleted when the stack is torn down"* → **DeletionPolicy: Retain** (or Snapshot if they want a final copy)

> *"Determine whether anyone modified stack resources manually via the console"* → **Drift Detection** (template vs. reality diff)

> *"Developers prefer defining infrastructure in TypeScript/Python rather than YAML"* → **AWS CDK** (code that compiles to CloudFormation)

> *"Deploy identical environments repeatedly across regions with no manual steps"* → **CloudFormation templates** (the core IaC pitch)

> *"Prevent accidental updates to a critical resource during stack updates"* → **Stack Policy** (update-protection inside a stack)

> *"Reuse a common VPC pattern across many templates"* → **Nested Stacks** (componentize the recipe)

> *"Stack must not proceed until software on the EC2 instance is installed and running"* → **CreationPolicy + cfn-signal** (DependsOn only orders resources)

> *"Make sure the database is created before the app server resource"* → **DependsOn**

> *"Roll out a new launch template to an ASG in batches during a stack update"* → **UpdatePolicy (AutoScalingRollingUpdate)**

> *"An update replaces the RDS instance; keep the old one"* → **UpdateReplacePolicy: Retain/Snapshot**

## Pocket card

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
| Wait for app install during CREATE | CreationPolicy + cfn-signal |
| Resource ordering | DependsOn |
| Rolling ASG update | UpdatePolicy |
| Keep old resource on replacement | UpdateReplacePolicy |

You now know how to stamp out infrastructure across many accounts — next comes the question of who governs all those accounts, which is Organizations and Control Tower territory.
