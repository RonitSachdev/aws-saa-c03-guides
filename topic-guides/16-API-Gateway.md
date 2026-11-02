# Section 16: API Gateway

## The idea

API Gateway is the **front desk of a busy office building**. Nobody wanders straight to your engineers' desks (your Lambda functions, your backends). Everyone checks in at the front desk first, where the receptionist **routes** them to the right floor, **checks their ID** (authentication), **turns away crowds** when the lobby is full (throttling), and **writes every visit in the logbook** (logging) — all *before* your code runs a single line.

That's API Gateway: a fully managed service that sits in front of your backend and handles routing, auth, rate limiting, caching, and monitoring.

Burn in the canonical serverless chain — the exam's favorite architecture:

```
Client --> CloudFront --> API Gateway --> Lambda --> DynamoDB
```

The reflex: **"no servers to manage, pay per request"** → this chain. When a question describes a REST API with zero server management, this is the answer skeleton.

## Three API types

| Type | Personality | Features | Trigger phrase |
|---|---|---|---|
| **REST API** | Full-featured flagship | **API keys, usage plans, caching, WAF, request validation** | Needs any of those features |
| **HTTP API** | Minimalist, **~70% cheaper** | Simple proxy to Lambda/HTTP, built-in **JWT** auth, low latency | **"Lowest cost"** simple Lambda proxy |
| **WebSocket API** | **Persistent two-way** connection | Server can push to clients | **"Real-time chat"**, "live push", live dashboards |

THE trap: usage plans, API keys, and caching are **REST API only**. If the question needs them, HTTP API is a distractor no matter how cheap it is.

## Endpoint types (where does it live?)

| Endpoint | For | Note |
|---|---|---|
| **Edge-Optimized** | **Globally distributed clients** | Routed through CloudFront's edge network automatically (default) |
| **Regional** | Clients in the **same region** | Or when you want to bolt on **your own CloudFront** distribution |
| **Private** | **VPC-only** access | Reached via an **Interface VPC Endpoint** — never touches the internet |

## The auth trio (guaranteed question)

Three ways to answer "who's calling?" — the exam WILL make you pick one:

| Authorizer | Use when the caller is... | Mechanism |
|---|---|---|
| **IAM / SigV4** | **AWS-native**: internal services, EC2 roles, IAM users | Requests signed with AWS credentials (Signature Version 4) |
| **Cognito User Pool authorizer** | **App users who sign in** (mobile/web app accounts) | Cognito issues a **JWT** (JSON Web Token); gateway validates it, zero custom code |
| **Lambda Authorizer** | **Custom logic**: third-party identity provider, legacy/**bespoke tokens**, weird rules | Your Lambda inspects the token and returns an IAM policy |

Hook: **IAM = machines, Cognito = your users, Lambda Authorizer = anything weird.**

## Traffic control & performance

- **Default throttle: 10,000 requests/second** per account per region. Exceed it and clients get **HTTP 429 Too Many Requests** — "clients receiving 429" → you're being throttled.
- Throttling uses a **token bucket** algorithm: a steady **rate** plus a **burst** allowance. You can set your own **per-method / per-stage rate + burst** (e.g. **1,000 req/s with a 2,000 burst**) to protect a fragile backend from spikes.
- **THE trap: ELB can't throttle.** A load balancer just spreads requests; it has no rate limits. "Protect the backend from request floods / cap request rate" → **API Gateway throttling** (or usage plans), not an ALB.
- **Pricing**: pay **per API call received + data transferred out** (plus hourly cache charges if caching is on). No minimums, no servers.
- **Usage Plans + API Keys** (REST only): per-customer request quotas and rate tiers. Trigger: **"SaaS company sells API access in Basic/Pro tiers"** → usage plans with API keys.
- **Caching**: gateway caches responses (**default TTL 300 seconds**), reducing backend load and latency. You provision the cache **per stage with a size in GB** (billed hourly). "Reduce calls hitting the backend for repeated requests" → enable API Gateway caching.
- **Tracing**: turn on **X-Ray** to follow a request from API Gateway through the backend services behind it.

## Two mechanical facts (free points)

1. **THE 29-second timeout.** API Gateway waits a **maximum of 29 seconds** for the backend. Lambda can run 15 minutes — **but not behind API Gateway**. This limit is **hard; "increase the timeout" is impossible past 29s** — any answer suggesting it is wrong. Long-running jobs go **asynchronous**: return **202 Accepted** immediately, hand the work to **SQS or Step Functions**, let the client poll or get notified.

```
Client --> API GW --202--> (immediately)
              |
              +--> SQS --> Lambda/worker (takes 2 min, nobody's waiting)
```

2. **CORS (Cross-Origin Resource Sharing).** When **browser JavaScript on one domain** calls your API on another domain and gets blocked with cross-origin errors → **enable CORS** on API Gateway. Browser + cross-domain + JS error = CORS, every time.

## Question patterns

> *"Build a REST API with no servers to manage, pay only per request"* → **API Gateway + Lambda + DynamoDB** (the canonical serverless chain)
> *"SaaS company wants to offer customers different API request limits per pricing tier"* → **Usage Plans + API Keys** (REST API only — per-customer tiers)
> *"Mobile app users must sign in before calling the API"* → **Cognito User Pool authorizer** (app users = Cognito JWTs)
> *"Company has an existing custom/third-party token system for API auth"* → **Lambda Authorizer** (custom logic = your Lambda decides)
> *"Cheapest way to expose a simple Lambda function over HTTP with JWT auth"* → **HTTP API** (~70% cheaper, minimal features)
> *"Push live updates to a real-time dashboard / chat application"* → **WebSocket API** (persistent two-way connection)
> *"API must be accessible only from within the VPC, never the internet"* → **Private endpoint + Interface VPC Endpoint**
> *"Backend process takes 2 minutes; API Gateway requests keep timing out — fix it"* → **Go async: return 202, queue to SQS/Step Functions** (29s is a hard limit; you cannot raise it)
> *"Browser JavaScript from another domain gets blocked calling the API"* → **Enable CORS** on API Gateway
> *"Clients suddenly receive HTTP 429 errors"* → **Throttling** — raise the limit or add caching/usage plans
> *"Limit requests to a legacy backend to 1,000/s while absorbing short bursts"* → **API Gateway throttling (rate + burst, token bucket)** (an ALB cannot throttle)

## Pocket card

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
| Throttle algorithm | Token bucket: rate + burst (per method/stage) |
| Rate-limit requests (not ELB) | API Gateway throttling |
| Pricing | Per API call + data transfer (+ cache GB-hours) |
| Browser cross-domain error | Enable CORS |

You just saw the fix for slow backends is "drop the work into a queue and walk away" — that queue, and the whole messaging toolbox around it, is the next section.
