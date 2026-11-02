# Section 21: Secrets Manager & Parameter Store

## The idea

Every app has secrets — database passwords, API keys, license codes — and the worst place for them is where developers love to put them: hardcoded in the source. AWS gives you two lockboxes, and the exam's whole game is making you pick the right one.

Picture two places to keep a spare house key. **Parameter Store** is a **key hook board in a locked closet**: cheap (free, in fact), tidy, labeled hooks arranged in neat rows — grab whatever key you need. **Secrets Manager** is a **hotel keycard system**: it costs money, but it **automatically reissues the keycards on a schedule**, so even a stolen card goes stale on its own.

Spell out the jargon: both are managed stores for configuration values and secrets, both **encrypt with KMS**, both are fetched by apps at runtime via API. **THE differentiator is AUTOMATIC ROTATION** — and it belongs to Secrets Manager alone.

## Secrets Manager — rotation is the whole point

- **Native automatic rotation**: for **RDS, Redshift, and DocumentDB** credentials, Secrets Manager rotates the password using a **built-in Lambda** it manages for you — zero custom code. For anything else, you supply a custom rotation Lambda. **The moment a question says "automatically rotate" → Secrets Manager. Always. No exceptions.**
- **$0.40 per secret per month** (+ small per-10k-API-calls fee).
- Secrets up to **64KB**.
- **Cross-account sharing** via resource policies — "share a secret with another AWS account" → Secrets Manager.
- Encrypted with **KMS**, every access logged in **CloudTrail**.
- Rotation happens **without downtime** — the app just fetches the current value at connect time. During rotation Secrets Manager keeps **multiple versions** tagged with staging labels (`AWSCURRENT`, `AWSPENDING`, `AWSPREVIOUS`); Parameter Store has no such rotation versioning.
- It stores and rotates secrets — it does **not mint short-lived tokens** (that's STS/Cognito).

## Parameter Store (SSM Parameter Store) — free and hierarchical

- **Standard tier is FREE**: up to **4KB** per parameter, **10,000 parameters**.
- **Hierarchical paths**: `/prod/db/password`, `/dev/db/password` — fetch a whole branch with one `GetParametersByPath` call, and scope IAM permissions per path ("dev can read `/dev/*` only").
- **SecureString** type = **KMS-encrypted** value — yes, Parameter Store can store encrypted secrets too.
- **Advanced tier**: **8KB**, parameter **policies** (e.g., expiration notification), higher throughput — small fee.
- **NO native rotation.** That's the dividing line.

"Store application config / feature flags / license keys / AMI IDs" or "**cheapest** option" → **Parameter Store**. It's built for broad, mostly non-secret config — URLs, AMI IDs, instance IDs, DB connection strings, environment variables — plus SecureString for **secrets that change infrequently and don't need rotation** (cheaper than Secrets Manager when you have lots of static values).

## The comparison table (memorize this)

| | **Secrets Manager** | **Parameter Store** |
|---|---|---|
| **Automatic rotation** | **YES — native for RDS/Redshift/DocumentDB** | **NO** |
| Cost | $0.40/secret/month | **FREE** (standard tier) |
| Max size | 64KB | 4KB (8KB advanced) |
| Hierarchy | flat names | **paths** `/prod/db/...` |
| Cross-account sharing | **yes** | no (standard) |
| KMS encryption | always | SecureString type |
| Built for | secrets that must rotate | config + secrets that don't |

**Widen the lens — the four "secret-ish" services the exam mixes up:**

| Service | Use it for | Rotation / renewal | Stores passwords/API keys? |
|---|---|---|---|
| **Secrets Manager** | DB credentials, API keys, tokens | **Automatic rotation** | Yes |
| **SSM Parameter Store** | App config, env vars, static secrets (SecureString) | No native rotation | Yes (SecureString) |
| **KMS** | **Encryption keys** + encrypt/decrypt operations | Key rotation only | **No** — not a secret store |
| **ACM** | Public/private **SSL/TLS certificates** for ALB, CloudFront, API Gateway | **Automatic certificate renewal** | No |

```
"rotate automatically"? ──yes──▶ Secrets Manager
        │no
"cheapest / config / hierarchy"? ──▶ Parameter Store
```

## The runtime pattern (the "fix the hardcoded password" answer)

Both integrate with **Lambda and ECS environment injection**, and the exam-blessed architecture is always the same:

```
App (EC2/Lambda/ECS)
  │  IAM role attached — NO credentials in code or env files
  ▼
GetSecretValue / GetParameter (at runtime)
  ▼
KMS decrypts transparently ──▶ app connects to DB
```

**ECS injection specifics:** in the task definition, reference a Secrets Manager secret or Parameter Store parameter in the container definition's **`secrets`** parameter (→ injected as **environment variables**) or **`secretOptions`** (→ **log driver configuration**). Works on both **EC2 and Fargate** launch types; the **task execution role** needs permission to read the secret/parameter (and the KMS key).

**THE trap:** any answer where credentials sit in code, an AMI, a config file in the repo, or a plain environment variable is wrong. The fix is **fetch at runtime via IAM role** — and if rotation is mentioned, Secrets Manager, so the password changes **without downtime** and the app never notices.

## Question patterns

> *"Automatically rotate the RDS database password every 30 days."* → **Secrets Manager** (native RDS rotation via built-in Lambda).

> *"Store application configuration values at the lowest possible cost."* → **Parameter Store standard tier** (free).

> *"Organize config per environment like /prod/db/url and /dev/db/url, with IAM scoped per environment."* → **Parameter Store hierarchical paths**.

> *"Share a database secret with an application in another AWS account."* → **Secrets Manager cross-account resource policy**.

> *"Developers hardcoded the DB password in the code — what's the fix?"* → **Secrets Manager + IAM role, app fetches at runtime** (never in code/env files).

> *"Store an encrypted license key for free."* → **Parameter Store SecureString** (KMS-encrypted, still free).

> *"Rotate credentials without application downtime."* → **Secrets Manager** — app fetches the current secret at connection time.

> *"Secret is 20KB of JSON credentials."* → **Secrets Manager** (64KB limit; Parameter Store caps at 4/8KB).

> *"Audit who accessed the database secret."* → **Either service + CloudTrail** (all API access is logged).

> *"Inject a DB password into ECS containers (EC2 or Fargate) as an environment variable."* → **`secrets` parameter in the container definition referencing Secrets Manager/Parameter Store** (`secretOptions` for log config).

> *"Store many application parameters that change rarely and need no rotation, cost-effectively."* → **Parameter Store SecureString** (Secrets Manager is overkill and costs per secret).

> *"Need SSL/TLS certificates with automatic renewal for an ALB."* → **ACM** (not Secrets Manager, not KMS).

> *"Where should encryption keys be managed?"* → **KMS** — it manages keys, it does not store passwords.

## Pocket card

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
| Many static params, no rotation, cheap | Parameter Store SecureString |
| ECS env var from a secret | `secrets` in container definition |
| ECS log driver secret | `secretOptions` |
| Encryption keys (not secrets) | KMS |
| SSL/TLS certs, auto-renew | ACM |

Keys from Section 20 encrypt these secrets, CloudTrail from Section 19 audits every peek at them — the monitoring, key, and secret stories all click together, and that's exactly how the exam will test you.
