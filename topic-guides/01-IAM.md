# Section 1: IAM — Identity and Access Management

## The idea

Every single thing that happens in AWS — launching a server, reading a file, deleting a database — starts with the same two questions: **who are you?** and **are you allowed to do that?** IAM (Identity and Access Management) is the service that answers both. It's the front door, the ID checker, and the rulebook, all in one — and it's **free** and **global** (not tied to any region).

Here's the analogy to carry through this whole section: **AWS is a giant office building.** IAM hands out the badges. A **user** is a permanent employee badge with your name on it. A **group** is a department — everyone in "Developers" gets whatever the department is allowed. A **role** is a **temporary costume**: a visitor's vest that anyone (a person, a server, another company) can put on for a while, gain its powers, and then take off. And **policies** are the written rules pinned to the wall saying which badges open which doors.

That "temporary costume" idea is the single most exam-tested concept in IAM, so let's start there.

## Users, groups, roles

| Identity | What it is | When to use |
|---|---|---|
| **User** | Permanent identity for one human (or one legacy app), with a password and/or long-lived access keys | A specific person who needs AWS access |
| **Group** | A bucket of users that share policies. Groups contain **only users** — never other groups, never roles | Manage permissions by team, not per person |
| **Role** | An identity with permissions but **no password and no permanent keys**. It's *assumed* — put on like a costume — and hands out **temporary credentials** | Services, cross-account access, federated humans |

**The golden rule: never put long-lived access keys on compute.** If an EC2 instance needs to read from S3, you do NOT create a user, generate access keys, and paste them into a config file on the box. Keys on a server can leak, never rotate themselves, and show up in every "what's wrong with this architecture?" exam question. Instead:

- **EC2 → attach an instance role** (delivered via an *instance profile*). The instance fetches auto-rotating temporary credentials from its metadata — no keys ever touch the disk.
- **Lambda → execution role.** Same idea: the function assumes a role every time it runs.
- **ECS tasks → task role.** Same pattern again.

Two defaults worth knowing cold:

- A **brand-new IAM user has NO permissions** (implicit deny) until a policy is attached — *"new user can't launch EC2"* → attach a policy/add to a group.
- **Access keys** (access key ID + secret) are the **long-term credentials** of a user (or root) used to sign **CLI/SDK/API** calls. **Attaching a policy does NOT create access keys** — they're generated separately. Rule of thumb: **groups manage humans' permissions, roles manage services'**.

**THE trap:** any answer choice that says *"store access keys on the instance / in the AMI / in environment variables / in the code"* is wrong. The right answer is always **the role**. If the exam says "credentials found hardcoded in an application on EC2" — the fix is *attach an IAM role to the instance*.

## Policy JSON anatomy

A policy is a JSON document. You don't need to write one on the exam, but you must be able to *read* one. Four load-bearing parts:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowReadReports",
    "Effect": "Allow",
    "Action": ["s3:GetObject", "s3:ListBucket"],
    "Resource": "arn:aws:s3:::finance-reports/*",
    "Condition": {
      "Bool": { "aws:MultiFactorAuthPresent": "true" }
    }
  }]
}
```

- **Effect** — `Allow` or `Deny`. That's it, two values.
- **Action** — which API calls (`s3:GetObject`, `ec2:*`...). Service prefix + verb.
- **Resource** — which things, named by **ARN** (Amazon Resource Name — AWS's globally unique ID string for every object it manages).
- **Condition** — optional "only if" clauses: only with MFA, only from this IP range, only over HTTPS.

Resource-based policies (we'll meet them next) add a **Principal** field — *who* the statement applies to — because the policy isn't attached to an identity, so it has to name one.

## How AWS decides yes or no

Memorize this evaluation logic — it's worth several exam questions:

1. **Default is implicit deny.** Nothing is allowed until something allows it.
2. An **Allow** in an applicable policy opens the door.
3. An **explicit Deny ALWAYS wins.** Over any Allow, anywhere, no exceptions, full stop.

And for a request to succeed, it must pass through **every applicable gate**:

```
Request ──► SCP (org ceiling) ──► Resource policy ──► Permission
            allows?               allows?*             boundary allows?
                                                          │
                                              Identity policy allows? ──► ✔ Allowed
   any explicit DENY anywhere ─────────────────────────────────────────► ✘ Denied
```

*(Fine print you don't need for the exam: within the same account, a resource-policy Allow alone can be enough. The pattern you DO need: an SCP or explicit Deny blocks everything downstream.)*

**THE trap:** *"A user's policy clearly says Allow, but the action fails."* The answer is always one of: **an explicit Deny somewhere**, **an SCP on the account** (common when the question mentions AWS Organizations), or **a permission boundary** clipping the identity policy. Allow + Deny = Deny. Every time.

## The policy types table

| Policy type | Attached to | What it does |
|---|---|---|
| **Identity-based** | User, group, or role | The everyday "what can this identity do" |
| **Resource-based** | The resource itself (S3 bucket policy, SQS queue policy...) | "Who can touch *me*" — has a `Principal`, enables cross-account grants |
| **Permission boundary** | A user or role | A **maximum ceiling** for that one identity. Grants nothing itself — effective perms = identity policy ∩ boundary |
| **SCP** (Service Control Policy) | Accounts/OUs in **AWS Organizations** | An **org-wide ceiling**. Grants nothing; caps everyone in the account — **including the account's root user** |
| **Session policy** | Passed when assuming a role | Shrinks that one session's permissions even further |
| **ACL** (Access Control List) | S3 buckets/objects | **Legacy** S3-only mechanism. Can't use JSON conditions and **cannot grant to users in its own account** — AWS says avoid; use bucket policies. Don't confuse with **Network ACLs** (a VPC subnet firewall — totally unrelated) |

Ceilings vs grants, one line: **boundary = ceiling for one identity; SCP = ceiling for a whole account; neither grants anything by itself.**

Exam scenario for boundaries: *"Developers may create their own IAM roles, but must never be able to create roles more powerful than X"* → **permission boundary** (require it on every role they create).

**Execution role vs resource-based policy (Lambda, and the same logic everywhere):**

| Question the policy answers | Policy | Example |
|---|---|---|
| **"Who can invoke/touch ME?"** | **Resource-based policy** on the function | Allow S3 / API Gateway / another account to invoke the Lambda |
| **"What can I access?"** | **Execution role** (identity policy) | Lambda reading S3, writing DynamoDB, calling KMS/SQS |

**THE trap:** when Lambda calls another service, AWS evaluates the **execution role**, not the function ARN. **KMS permissions follow the principal** — the key policy/grant must name the **execution role**, not the Lambda function. Likewise for ECS tasks, grant access through the **task role**, not a resource policy naming the task.

## STS and roles: how the costume gets put on

**STS (Security Token Service)** is the coat-check counter that hands out costumes. When anything calls **`sts:AssumeRole`**, STS returns **temporary credentials** — an access key, secret key, and session token — valid for a limited time (15 minutes to 12 hours, **default 1 hour**), after which they expire on their own. Temporary, auto-expiring, nothing to rotate or leak long-term: that's why roles beat users for anything automated.

Every role has TWO policies, and the exam loves this:

- **Permissions policy** — what the costume lets you do.
- **Trust policy** — **who is allowed to put the costume on.** It's a resource-based policy on the role itself, naming the trusted principal (a service like `ec2.amazonaws.com`, another account, a SAML provider).

**THE trap:** *"Role has the right permissions but the user/service can't assume it"* → check the **trust policy**. Permissions say what the role can do; trust says who can wear it.

## Cross-account access

Company A's auditors need to read Company B's S3 bucket. The canonical recipe:

1. **Account B (the target)** creates a role with the needed permissions.
2. B sets the role's **trust policy** to trust Account A (and can require MFA or an `ExternalId` — an agreed secret string used with third parties to block the "confused deputy" problem).
3. **Account A's users** get permission to call `sts:AssumeRole` on that role's ARN.
4. They assume it, get temporary credentials, do the work, credentials expire.

No shared passwords, no duplicated users, no keys emailed around. *"Give another AWS account access"* → **cross-account role + trust policy**, essentially always. (Fine for a handful of accounts; for **dozens of accounts** and a workforce, move up to **Organizations + IAM Identity Center**.)

**Cross-account S3 specifically:** a **bucket policy** can grant other accounts (or specific IAM principals) access to all or some objects; an **ACL** can grant only to **whole AWS accounts** (not to individual users) and is legacy. Prefer the bucket policy or a cross-account role.

## IAM Identity Center (the artist formerly known as AWS SSO)

One human, twelve AWS accounts, twelve passwords? No. **IAM Identity Center** gives your workforce **single sign-on (SSO): one login, a portal, and access to multiple AWS accounts** (plus business apps) — under the hood it just assumes roles in each account for you.

It also **federates**: connect your existing corporate identity provider — **Okta, Azure AD / Microsoft Entra ID, or on-prem Active Directory** — via **SAML 2.0** (Security Assertion Markup Language, the standard XML handshake that lets one system vouch "yes, this is Alice" to another). Employees keep their corporate password; AWS never stores it; someone leaves the company, disable them once in the IdP and every AWS door closes.

**Signal decoding:** *"employees already have Active Directory / Okta credentials and shouldn't get separate IAM users"* or *"single sign-on across many AWS accounts"* → **IAM Identity Center**. (For federating *app customers* — sign in with Google/Facebook — that's **Amazon Cognito**, a different topic.)

### The federation flavors

| Flavor | How it works | Exam signal |
|---|---|---|
| **SAML 2.0 federation** | Corporate IdP that speaks SAML 2.0 (e.g., **Microsoft AD FS**, Okta, Entra ID) asserts identity → role assumed via `AssumeRoleWithSAML` / Identity Center | "Corporate login, IdP is SAML-compatible" |
| **Custom identity broker** | Your own app authenticates users against the **non-SAML** store (e.g., on-prem **LDAP**), then calls **STS** (`AssumeRole` / `GetFederationToken`) to hand out temporary credentials | "Identity store is **not SAML 2.0-compatible**" |
| **Web identity federation** | Login with Amazon/Facebook/Google or any **OIDC** IdP → temporary creds (today: via **Cognito**) — no custom sign-in code | "Mobile/web app users, social login" |
| **AD Connector + IAM roles** | Existing on-prem AD stays put; **assign IAM roles to AD users/groups** for console access | "Use existing AD accounts for AWS console" |

Memory hook: **SAML available → Identity Center; no SAML → identity broker + STS.** All of these are **enterprise identity federation** — users authenticate in their own network and reach AWS **without new IAM users**. IAM itself is **not** for managing thousands of mobile-app users — that's Cognito.

### IAM database authentication

**RDS MySQL/PostgreSQL (and Aurora)** can authenticate DB logins with **IAM instead of a password**: the app (e.g., EC2 using its **instance profile**) generates a short-lived **auth token** (15 min), connects over **SSL** (traffic encrypted), and access is **managed centrally in IAM**. MySQL users map to it via the **`AWSAuthenticationPlugin`**. *"No DB passwords, centrally managed access, EC2 role connects to RDS"* → **IAM DB authentication**.

### IAM certificate store (legacy)

IAM can hold **SSL/TLS server certificates** and use them in any Region — but **only certificates from an external CA** (it can't issue them) and you must renew manually. It's the legacy fallback for Regions/cases without **ACM**; today **use ACM** (free, auto-renewing).

## MFA and the root account

**MFA (multi-factor authentication)** = password *plus* a second factor (authenticator app, hardware key). Policies can demand it via the condition key **`aws:MultiFactorAuthPresent`** — e.g., deny `s3:DeleteObject` unless it's `true`. *"Require MFA for destructive/sensitive actions"* → that condition key.

The **root account** (the email you created the account with) can do absolutely everything and can't be restricted by IAM policies (only an SCP can cap it, and never in the org's management account). Best practice, exam-tested verbatim:

- **Enable MFA on root** immediately.
- **Delete root access keys** (never create them).
- **Don't use root for daily work** — create an admin IAM identity instead.
- Root only for the handful of root-only tasks (closing the account, changing support plans...).

**Root-only tasks** (the exam lists these as "requires the root user"): change **account name, root email or root password**; change the **support plan**; **close the account**; **enable MFA Delete on an S3 bucket**; create **CloudFront key pairs** (legacy signed-URL keys); **sign up for GovCloud**.

**Least privilege**: start with the minimum permissions and add only as needed. And remember IAM is **global** — users, groups, roles, and policies exist once and apply in every Region.

Two quick tools worth a flashcard: **IAM Access Analyzer** finds resources shared with outside entities; **credentials report / access advisor** show stale users and unused permissions (the "least privilege cleanup" answers). The **IAM credential report** is an **account-wide CSV of every IAM user and their credential status** (password age/last used, access keys rotated/last used, MFA enabled) — the audit answer, not a CloudTrail or Config job.

## Question patterns

> *"An application on EC2 needs to write to DynamoDB. What's the MOST secure way to provide credentials?"* → **IAM role attached to the instance (instance profile)** — never access keys on the box.

> *"A Lambda function must read from an S3 bucket. How should it authenticate?"* → **Lambda execution role** with S3 read permissions — same costume pattern, serverless flavor.

> *"Users in Account A need temporary access to resources in Account B."* → **Create a role in Account B with a trust policy trusting Account A; users AssumeRole via STS** — "temporary" + "another account" = cross-account role.

> *"A user's identity policy allows s3:PutObject, but uploads fail with Access Denied."* → **Look for an explicit Deny — bucket policy, SCP, or permission boundary** — explicit Deny always beats Allow.

> *"An action works in a standalone account but fails in an account inside AWS Organizations."* → **A Service Control Policy is blocking it** — "Organizations" is the tell.

> *"Developers may create IAM roles for their apps, but security wants a guarantee those roles can never exceed a defined permission set."* → **Permission boundaries** — "maximum permissions" / "cannot exceed" is the signal.

> *"5,000 employees with existing Active Directory logins need access to multiple AWS accounts without creating IAM users."* → **IAM Identity Center with SAML federation to AD** — "existing corporate directory" + "multiple accounts" + "no IAM users".

> *"An application needs short-lived credentials that expire automatically."* → **STS AssumeRole** — "temporary/short-lived credentials" is literally STS's product.

> *"Require that users can only terminate EC2 instances if they've signed in with MFA."* → **Policy Condition with `aws:MultiFactorAuthPresent`** — sensitive action + MFA = that condition key.

> *"A new AWS account was just created. What should be done FIRST to secure it?"* → **Enable MFA on the root user, delete/avoid root access keys, create an admin user for daily work.**

> *"Enable MFA Delete on an S3 bucket — who can do it?"* → **Only the root user** (one of the root-only tasks).

> *"Company's on-prem LDAP directory is not SAML 2.0-compatible; employees need AWS access without IAM users."* → **Custom identity broker that authenticates against LDAP and calls STS** (no SAML = broker).

> *"A Lambda function can't decrypt with a KMS key, even though the key policy allows the Lambda function ARN."* → **Grant the Lambda execution role in the key policy** (KMS permissions follow the principal).

> *"Allow an S3 bucket in another account to trigger a Lambda function."* → **Lambda resource-based policy** ("who can invoke me").

> *"EC2 app must connect to RDS MySQL without storing a database password, with access managed centrally."* → **IAM database authentication** (instance profile → auth token over SSL).

> *"Auditor needs a list of all IAM users with password, access key, and MFA status."* → **IAM credential report**.

> *"A newly created IAM user can't perform any EC2 actions."* → **New users have no permissions by default — attach a policy / add to a group** (and attaching a policy doesn't create access keys).

## Pocket card

| Keyword in the question | Answer |
|---|---|
| EC2/app needs AWS access, "most secure" | Instance role (instance profile), never keys |
| Lambda needs permissions | Execution role |
| Hardcoded / stored access keys | Wrong — replace with a role |
| Temporary / short-lived credentials | STS AssumeRole |
| Access across AWS accounts | Role in target account + trust policy |
| Third party assumes your role safely | ExternalId in trust policy |
| Role exists but "can't be assumed" | Fix the trust policy |
| Allow exists but action denied | Explicit Deny / SCP / permission boundary |
| Org-wide restriction, applies even to root | SCP (AWS Organizations) |
| Cap max permissions of ONE user/role | Permission boundary |
| Policy on the resource, has a Principal | Resource-based policy (e.g., bucket policy) |
| Legacy S3 grant mechanism, avoid | S3 ACL (≠ Network ACL) |
| SSO, one login → many AWS accounts | IAM Identity Center |
| Federate Okta / Azure AD / corporate AD | IAM Identity Center + SAML 2.0 |
| Federate app customers (Google/Facebook login) | Cognito |
| Require MFA for an action | Condition: aws:MultiFactorAuthPresent |
| Root account | MFA on, no access keys, don't use daily |
| Who is my resource shared with externally? | IAM Access Analyzer |
| Find unused users / stale permissions | Credentials report / access advisor |
| List all users + password/key/MFA status | IAM credential report |
| MFA Delete, close account, change support plan, GovCloud | Root user only |
| Corporate IdP is SAML 2.0 (AD FS) | SAML federation / Identity Center |
| Identity store NOT SAML-compatible (LDAP) | Custom identity broker + STS |
| "Who can invoke my Lambda?" | Resource-based policy |
| "What can my Lambda access?" / KMS grant target | Execution role (permissions follow the principal) |
| DB login without password, MySQL/PostgreSQL | IAM database authentication |
| SSL certs in IAM | Legacy IAM certificate store — use ACM |
| Cross-account S3 to specific users | Bucket policy (ACL = whole accounts only) |

IAM is the "who may act" layer under everything else — next up, S3, where you'll see these same policies show up on the resource side as bucket policies.
