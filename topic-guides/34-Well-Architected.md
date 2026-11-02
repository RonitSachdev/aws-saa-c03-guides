# Section 34: Well-Architected Framework

## The idea

The Well-Architected Framework is AWS's answer to "what does *good* look like in the cloud?" Think of it as a **building inspector's checklist**: a house can stand up and still fail inspection — bad wiring, no fire exits, a heating bill that eats you alive. The framework's **six pillars** are the six things the inspector checks, and on the exam they don't appear as their own questions so much as the *lens* a question forces you to look through.

## The six pillars

| Pillar | One-line essence | Flagship services |
|---|---|---|
| **Operational Excellence** | Run and improve: everything as code, small reversible changes | CloudFormation, CloudWatch |
| **Security** | Least privilege, defense in depth, encrypt everywhere | IAM, KMS, GuardDuty |
| **Reliability** | Survive failures, recover automatically, stop guessing capacity | Multi-AZ, Auto Scaling Groups, Route 53 |
| **Performance Efficiency** | Right tool for the job, serverless-first, go global | Lambda, CloudFront, ElastiCache |
| **Cost Optimization** | Pay only for what you use, and measure it | Cost Explorer, Savings Plans, Spot |
| **Sustainability** | Maximize utilization, minimize wasted compute | Graviton, serverless |

A memory hook: **"SO CRPS"** doesn't sing, so try this instead — **"Operations Secure Reliable Performance Costs Sustainably"**, or just picture the inspector's walkthrough: *how you run it, how you lock it, how it survives, how fast it goes, what it costs, what it burns.*

Quick flavor of each:

- **Operational Excellence** — infrastructure as code (CloudFormation), frequent small deployments you can roll back, learn from every failure.
- **Security** — apply least privilege (grant only what's needed), defend in layers (WAF + security groups + NACLs), encrypt at rest and in transit.
- **Reliability** — assume everything fails; design so nobody notices. Multi-AZ, health checks, auto-recovery.
- **Performance Efficiency** — don't run a database on EC2 when RDS exists; cache with CloudFront/ElastiCache; experiment often.
- **Cost Optimization** — right-size, use Spot for interruptible work, Savings Plans for steady work, and *look at the bill* (Cost Explorer).
- **Sustainability** — the newest pillar: fewer idle servers, efficient hardware (Graviton), serverless where possible.

**The Well-Architected Tool** is a **free questionnaire in the console**: you answer questions about a workload, pillar by pillar, and it produces an **improvement plan**. "Review our architecture against best practices at no cost" → WA Tool.

**Lookalike tools — which question does each answer?**

| Tool | Question it answers |
|---|---|
| **Well-Architected Tool** | *"Is my **architecture** designed correctly?"* It reviews the workload across all six pillars. |
| **Compute Optimizer** | *"Are my **resources** the right **size**?"* It rightsizes EC2, EBS, Lambda and ASGs only. |
| **Trusted Advisor** | *"Is anything in my **account** misconfigured right now?"* It runs automated checks for cost, security, fault tolerance, performance and service limits. |

## The exam angle (this is the real payoff)

Pillars almost never show up as "which pillar is this?" Instead they hide in the **qualifier** of the question: "**MOST cost-effective** solution," "improve the **reliability**," "with the **LEAST operational overhead**." That qualifier is the tiebreaker — typically **two answers would technically work**, and the pillar keyword tells you which one AWS wants.

**THE trap: answering the *working* solution instead of the *qualified* solution.** If two options both solve the problem, the capitalized adjective picks the winner. Read it first, not last.

## Question patterns

> *"Two solutions both meet requirements; question asks for the MOST cost-effective"* → **the cheaper one that still works** (Cost Optimization is steering — e.g., Spot over On-Demand for fault-tolerant batch)

> *"Improve reliability of a single-AZ database"* → **Enable Multi-AZ** (Reliability pillar: survive AZ failure with automatic failover)

> *"LEAST operational overhead to run containers"* → **Fargate over EC2 launch type** (Operational Excellence/managed-first: no servers to patch)

> *"Improve performance for global users"* → **CloudFront** (Performance Efficiency: go global, cache at the edge)

> *"Ensure the architecture follows AWS best practices at no additional cost"* → **AWS Well-Architected Tool** (free console questionnaire → improvement plan)

> *"Get recommendations to improve a workload's reliability, security and cost based on AWS best practices"* → **Well-Architected Tool** (whole-design review; Compute Optimizer only resizes resources)

> *"Reduce the environmental impact of the workload"* → **Graviton instances / serverless** (Sustainability: maximize utilization)

## Pocket card

| Keyword | Answer |
|---|---|
| IaC, small reversible changes | Operational Excellence (CloudFormation) |
| Least privilege, encrypt everywhere | Security (IAM, KMS, GuardDuty) |
| Survive failure, stop guessing capacity | Reliability (Multi-AZ, ASG, Route 53) |
| Right tool, serverless-first, edge | Performance Efficiency (Lambda, CloudFront) |
| Pay for what you use, measure spend | Cost Optimization (Cost Explorer, Savings Plans, Spot) |
| Maximize utilization, Graviton | Sustainability |
| Free best-practices review | Well-Architected Tool |
| Right-size instances (not design) | Compute Optimizer |
| "MOST cost-effective / LEAST overhead" | The qualifier picks between two working answers |

Keep those qualifiers in your peripheral vision — they matter most in the next section's territory: disaster recovery, where cost versus recovery speed *is* the whole question.
