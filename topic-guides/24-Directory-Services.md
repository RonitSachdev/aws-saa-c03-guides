# Section 24: Directory Services

## The idea

First, what *is* Active Directory? If you've never worked in a Windows shop: **Active Directory (AD)** is Microsoft's on-premises system that acts as the **corporate phonebook plus the master keyring**. It stores every **user, computer, and group** in the company, and when Alice logs into her laptop, AD is what checks her password and decides which shared drives and printers she can use. Users log into a **domain** (like `corp.example.com`), and nearly every large enterprise on Earth runs it. Related jargon: **LDAP** is the standard protocol for talking to directories like AD; **domain join** means enrolling a machine into the AD domain so it obeys its rules.

Now the cloud problem: your company moves workloads to AWS, but the phonebook still lives in the on-prem server room. Windows services in AWS — **FSx for Windows File Server, Amazon WorkSpaces (virtual desktops), RDS for SQL Server** — all *need* a directory to authenticate against. AWS gives you **three options**, and the exam tests whether you can pick the right one from a scenario.

The analogy: your on-prem AD is the head office's filing room.
- **AWS Managed Microsoft AD** = build a **full branch-office filing room** in AWS, and optionally connect it to head office with a trusted courier route.
- **AD Connector** = install only a **phone line**: every lookup rings head office; nothing is stored in the branch.
- **Simple AD** = a **budget photocopy** of a filing room — works for small stuff, but it's not the real Microsoft thing.

### The three options (the table to memorize)

| | **AWS Managed Microsoft AD** | **AD Connector** | **Simple AD** |
|---|---|---|---|
| What it really is | **REAL Microsoft AD** running in AWS | A **PROXY** — just forwards auth requests | **Samba-based** AD-compatible clone |
| Users stored in AWS? | Yes | **No — nothing stored in AWS** | Yes |
| Works with on-prem AD? | Yes — **TRUST relationship** (two-way trust; use users from **both** sides) | Yes — it *only* redirects to on-prem | **NO trust** — standalone only |
| MFA support | **Yes** | Yes (via on-prem RADIUS) | **No MFA** |
| Best for | **Full AD features in the cloud**; EC2 domain join; RDS/FSx integration; hybrid via trust | **"Keep all identities on-prem"**, let AWS services authenticate against them | **Cheap basic LDAP**, small orgs, **< 5,000 users** |

Jargon check: a **trust relationship** means two separate AD forests agree to honor each other's logins — cloud AD trusts on-prem AD and vice versa (**two-way trust**), so users from *either* directory can access resources on *either* side, without syncing passwords into the cloud.

```
 Managed Microsoft AD          AD Connector              Simple AD
 ┌─────────────────┐         ┌──────────────┐         ┌──────────────┐
 │  Full AD in AWS │◀═trust═▶│  proxy only  │────────▶│ standalone   │
 │  (users stored) │  on-prem│ (no users in │  on-prem│ Samba clone  │
 │                 │    AD   │     AWS)     │    AD   │ no trust/MFA │
 └─────────────────┘         └──────────────┘         └──────────────┘
   full copy w/ trust        phone line to HQ           budget clone
```

### How the exam distinguishes them

- **Managed Microsoft AD** is the answer when the scenario needs *actual AD machinery in AWS*: **EC2 Windows domain join**, **MFA**, seamless integration with **RDS for SQL Server / FSx for Windows / WorkSpaces**, or a **trust with on-prem** so both user sets work. Phrase to spot: *"full AD features in the cloud"* or *"trust with on-prem"*.
- **AD Connector** is the answer when compliance or policy says **identities must never be stored in the cloud**. It's a pipe, not a directory — every authentication is redirected to the on-prem domain controllers. (Corollary: if the VPN/Direct Connect link to on-prem dies, authentication dies with it.)
- **Simple AD** is the answer when the words are **"lowest cost"**, **"basic LDAP"**, **"small organization"** — and *nothing* in the scenario mentions trust, MFA, or on-prem integration. It offers a **subset** of Managed AD: user accounts and group memberships, **group policies**, secure connections to (domain-joined) EC2, and **Kerberos-based SSO**.
- **AD Connector** is AWS's **"directory gateway"** — and for a company already running a corporate AD, it's usually the **easiest integration**. Bonus: once connected, you can **assign IAM roles to AD users/groups** so they reach the AWS console with their AD logins (no IAM users).
- Where it sits in the identity map: **Directory Service** = directory integration for **Windows/AD workloads and domain-joined EC2**; **IAM Identity Center** = workforce SSO to AWS accounts; **Cognito** = app customers. (Directory Service historically also offered **Amazon Cloud Directory**, a non-AD graph directory — legacy, rarely tested.)
- **Amazon WorkSpaces** = managed cloud **virtual desktops (VDI)**, Windows or Linux, scaling to thousands of workers — "full desktop" (vs **AppStream 2.0** = stream a single app). It authenticates against one of the three directories.

THE trap: *"connect Simple AD to on-prem AD with a trust"* → **can't**. Simple AD supports **no trust and no MFA** — the moment either word appears, Simple AD is eliminated.

THE trap: *"AD Connector as a standalone directory"* → also can't. A phone line with no head office on the other end connects to nothing — **AD Connector requires an existing on-prem AD**.

### The common pairing pattern

Remember this trio, because it fuels most directory questions: **FSx for Windows File Server, Amazon WorkSpaces, and RDS for SQL Server (Windows Authentication) all require a directory.** The question is rarely "do I need a directory?" — it's *which* of the three options fits the constraints given. FSx + "use our existing on-prem identities" → Managed AD with a trust, or AD Connector. FSx + "need MFA and cloud-resident AD" → Managed Microsoft AD.

**Memory hook:** **Managed AD = full copy with trust; Connector = phone line to on-prem; Simple = budget clone.**

## Question patterns

> *"Deploy FSx for Windows File Server; users must authenticate with existing on-prem AD identities"* → **Managed Microsoft AD with a trust, or AD Connector** (both let on-prem identities work; pick whichever the options offer).

> *"Security policy requires that no user identities are stored in the cloud"* → **AD Connector** (proxy only — all auth redirected on-prem, nothing stored in AWS).

> *"Small company needs a low-cost, basic LDAP-compatible directory for one application"* → **Simple AD** (cheap Samba standalone, fine under ~5,000 users).

> *"EC2 Windows instances must join a domain, and MFA is required"* → **AWS Managed Microsoft AD** (real AD: domain join + MFA; Simple AD has neither MFA nor trust).

> *"Establish a two-way trust between AWS and the on-premises domain so users on both sides access resources"* → **Managed Microsoft AD** (the only option supporting trust relationships).

> *"RDS for SQL Server with Windows Authentication for corporate users"* → **Managed Microsoft AD** (RDS integrates with it directly; add a trust for on-prem users).

> *"WorkSpaces desktops authenticating against on-prem AD without replicating the directory"* → **AD Connector** (phone line: auth flows back on-prem).

> *"Employees should sign into the AWS console with their existing corporate AD credentials, with the least effort"* → **AD Connector + IAM roles mapped to AD users/groups** (or Identity Center with AD as the source).

> *"Provide thousands of workers with secure Windows/Linux cloud desktops"* → **Amazon WorkSpaces** (VDI; needs a directory).

## Pocket card

| Keyword | Answer |
|---|---|
| Full AD features in AWS | Managed Microsoft AD |
| Trust relationship with on-prem | Managed Microsoft AD (two-way trust) |
| MFA + domain join | Managed Microsoft AD |
| No identities stored in cloud | AD Connector |
| Proxy / redirect auth to on-prem | AD Connector |
| Low cost, basic LDAP, small org | Simple AD |
| No trust, no MFA | Simple AD's limits |
| FSx Windows / WorkSpaces / RDS SQL Server | All need a directory — pick from the three |
| Existing corporate AD, easiest integration | AD Connector ("directory gateway") |
| AD users into AWS console | AD Connector + IAM roles for AD users/groups |
| Simple AD features | Users/groups, group policies, EC2 domain join, Kerberos SSO |
| Cloud virtual desktops (VDI) | Amazon WorkSpaces |
| Memory hook | Full copy w/ trust / phone line / budget clone |

Directories solve *who* on-prem users are in the cloud — next we solve where their *files* live, with the hybrid storage bridge crew: Storage Gateway, DataSync, and Transfer Family.
