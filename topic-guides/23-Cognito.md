# Section 23: Cognito

## The idea

Your mobile app has a million *customers* — not employees, customers. They need to sign up, log in, maybe with Google or Facebook, and then... upload photos to S3. Two very different problems just walked in: **"who are you?"** and **"what AWS stuff may you touch?"** Amazon Cognito answers both, with two deliberately different pieces.

Here's the analogy that carries the whole section: think of an office building. At the front desk there's a **login box** — you prove who you are and get a **visitor badge** (that's the **User Pool**, and the badge is a **JWT token**). But the badge alone doesn't open doors. You take it to the **exchange desk**, which swaps your badge for a **physical keycard** that actually opens specific rooms (that's the **Identity Pool**, and the keycard is a set of **temporary AWS credentials**).

Jargon check before we dive in:
- **JWT** = JSON Web Token — a signed blob of text proving "this user authenticated, here's who they are."
- **STS** = AWS Security Token Service — the service that mints short-lived AWS credentials.
- **IdP** = Identity Provider — anything that vouches for identity (Google, Facebook, a corporate SAML server).

### The core distinction (THE thing to know)

| | **User Pools** | **Identity Pools** |
|---|---|---|
| Question answered | **AUTHENTICATION** — *who are you?* | **AUTHORIZATION for AWS** — *what AWS resources may you touch?* |
| What it is | A **user directory**: sign-up, sign-in, password resets | A **credential exchange desk** |
| What it returns | **JWT tokens** | **Temporary AWS credentials** (via **STS**) |
| Extras | **Hosted UI** (pre-built login pages), **MFA**, **social login** (Google/Facebook/Apple), **SAML** enterprise IdPs | **Guest / unauthenticated access**, fine-grained per-user IAM permissions |
| Plugs into | **API Gateway** and **ALB** as an **authorizer** | S3, DynamoDB, any AWS API — directly from the app |

THE trap: the exam says *"users need to access S3 directly from the mobile app"* and offers "Cognito User Pools" as a tempting answer. A JWT can't call S3 — **only AWS credentials can**. Direct AWS resource access → **Identity Pools**.

### The classic flow (draw this in your head)

```
 User logs in (email / Google / SAML)
        │
        ▼
 ┌─────────────┐   JWT token   ┌───────────────┐   swap via STS   ┌──────────────────┐
 │  User Pool   │ ────────────▶ │ Identity Pool │ ───────────────▶ │ Temp AWS creds    │
 │ (login box)  │               │ (exchange desk)│                  │ (access key etc.) │
 └─────────────┘               └───────────────┘                  └──────────────────┘
                                                                          │
                                                                          ▼
                                                        App calls S3 / DynamoDB DIRECTLY
```

Note the Identity Pool is generous about what it accepts: tokens from a **User Pool**, from **social providers** directly, or from **SAML** — it's an exchange desk for *any* recognized badge.

### The clever bits worth exam points

- **Authorizers**: a **Cognito User Pool authorizer on API Gateway** validates the JWT before your backend ever runs — "authenticate API users without writing auth code" → User Pool authorizer. ALB can also authenticate through Cognito before forwarding requests.
- **Guest access**: Identity Pools support **unauthenticated identities** — "let users browse content *before* signing up" → Identity Pool guest access.
- **Guests need Identity Pools specifically**: plain STS has no notion of an anonymous guest — Identity Pools mint guest credentials. But Identity Pools **don't manage authentication** (no sign-up/sign-in/passwords) — that's always the User Pool or an external IdP.
- **Web identity federation** (Login with Amazon, Facebook, Google, any **OIDC** IdP) is today done through Cognito — no custom sign-in code, no identities to manage yourself. (Legacy **AWS Mobile Hub** used to wire this up for mobile apps; it's retired in favor of **Amplify**.)
- **No direct CloudFront integration**: User Pools plug into **API Gateway and ALB**, but **not natively into a CloudFront distribution** — protecting CloudFront content needs **signed URLs/cookies** or **Lambda@Edge** validating the JWT.
- **Per-user permissions with policy variables**: an IAM policy attached via the Identity Pool can use `${cognito-identity.amazonaws.com:sub}` so each user can only reach `s3://bucket/${their-own-id}/*`. **"Each user accesses only their own folder"** → Identity Pool + **IAM policy variables**. One policy, a million users, zero per-user setup.

### Cognito vs IAM Identity Center — don't mix up the audiences

THE trap: *"employees need single sign-on to AWS accounts"* → that's your **workforce**, and the answer is **IAM Identity Center** (the successor to AWS SSO), *not* Cognito. The rule:

- **Customers of your app** (millions of external users) → **Cognito**
- **Employees / workforce** signing into AWS accounts and business apps → **IAM Identity Center**

If the humans in the question get a paycheck from the company, Cognito is the wrong answer.

## Question patterns

> *"Mobile app needs user sign-up, sign-in, and login with Google and Facebook"* → **Cognito User Pools** (directory + social login + hosted UI).

> *"Authenticated app users must upload files directly to S3 from the device"* → **Cognito Identity Pools** (JWT → STS → temporary AWS credentials; only creds can call S3).

> *"Allow users to browse limited content without creating an account"* → **Identity Pool unauthenticated (guest) access**.

> *"Authenticate users of a REST API on API Gateway without custom code"* → **Cognito User Pool authorizer** (API Gateway validates the JWT for you).

> *"Each user may only read and write objects in their own S3 prefix"* → **Identity Pool + IAM policy variables** (`${cognito-identity...:sub}` scopes one policy per user).

> *"Company employees need SSO access to multiple AWS accounts"* → **IAM Identity Center, NOT Cognito** (workforce = Identity Center; customers = Cognito).

> *"Enterprise customers must log into your SaaS app with their corporate SAML identity provider"* → **User Pools with SAML federation** (still authentication — still the login box).

> *"Add MFA to your application's customer logins"* → **User Pools** (MFA lives where authentication lives).

> *"Use Cognito Identity Pools to handle user sign-up and password management"* → **Wrong — Identity Pools don't authenticate; use User Pools** (Identity Pools only hand out AWS creds).

> *"Authenticate users with Cognito directly on a CloudFront distribution"* → **Not natively supported — use ALB/API Gateway with a User Pool, or Lambda@Edge / signed cookies** in front of CloudFront.

> *"Mobile app users log in with Amazon/Facebook/Google (OIDC) without custom sign-in code"* → **Web identity federation via Cognito**.

## Pocket card

| Keyword | Answer |
|---|---|
| Sign-up / sign-in / user directory | User Pools |
| JWT tokens | User Pools |
| Social login (Google/Facebook/Apple), SAML | User Pools (federation) |
| Hosted UI, MFA | User Pools |
| API Gateway / ALB authorizer | User Pool authorizer |
| Temporary AWS credentials for app users | Identity Pools (via STS) |
| Direct app access to S3/DynamoDB | Identity Pools |
| Guest / unauthenticated access | Identity Pools |
| Each user only their own folder | Identity Pool + IAM policy variables |
| Employees SSO to AWS accounts | IAM Identity Center (never Cognito) |
| Identity Pools for sign-in/passwords? | No — User Pools authenticate |
| Cognito + CloudFront natively? | No — ALB/API GW, or Lambda@Edge |
| Social/OIDC login, no custom code | Web identity federation (Cognito) |
| AWS Mobile Hub | Legacy — now Amplify |
| Memory hook | User Pool = login box (JWT); Identity Pool = exchange desk (creds) |

Cognito handles your app's *customers* — but when the identities live in a corporate Active Directory, you're in the next section's territory: Directory Services.
