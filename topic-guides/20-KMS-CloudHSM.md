# Section 20: KMS & CloudHSM

## The idea

Encryption is easy to say and hard to do well — the hard part is never the math, it's **key management**: where do keys live, who can use them, how do you rotate them, and how do you prove who touched them?

Picture a **bank vault with a signing register**. **KMS** (**Key Management Service**) is the bank's shared vault: your keys live in safe-deposit boxes, the bank's staff (AWS) run the vault, almost every AWS service knows how to walk up to it, and **every single time a key is used, it's written in the register** — that register is **CloudTrail**, and that audit trail is **KMS's superpower**. **CloudHSM** is different: it's you renting an **entire private vault room** — dedicated hardware, your rules, and even the bank staff **cannot see inside**.

Spell out the jargon: **KMS** stores and manages **encryption keys** centrally; it integrates with essentially every AWS service (S3, EBS, RDS, Lambda env vars...). **HSM** = **Hardware Security Module**, a tamper-resistant physical device that performs crypto operations.

## KMS key types

| Type | Cost | Rotation | Control |
|---|---|---|---|
| **AWS-managed** (`aws/s3` etc.) | free | automatic | none — AWS runs it |
| **Customer-managed key (CMK)** | **$1/month** | **optional auto-rotation (yearly)** | full: your key policy, disable/delete |
| **AWS-owned** | invisible | — | none; shared across accounts, you never see it |

Need control — your own key policy, cross-account grants, rotation you can point to in an audit → **customer-managed key**.

**Key policies + IAM: BOTH must allow.** Access to use a key = the **key policy** says yes **and** the caller's **IAM policy** says yes. A user with `kms:*` in IAM still gets denied if the key policy doesn't permit them.

**KMS permissions follow the principal.** When Lambda/ECS/EC2 uses a key, the caller is the **role** (execution role, task role, instance role) — grant *that* role in the key policy, not the function or instance ARN. KMS is IAM-based: there's **no username/password** to "enable encryption".

What KMS is (and isn't): it holds **keys** and does encryption operations for files, strings, S3 objects, EBS, secrets — it does **not store secrets** themselves. **Secrets Manager always encrypts with a KMS key** (your CMK or the default `aws/secretsmanager`), so Secrets Manager depends on KMS. Lambda **environment variables are KMS-encrypted at rest by default**, but anyone with console access to the function can still read them — for real secrets, encrypt with a CMK using **encryption helpers** or, better, use Secrets Manager.

## Envelope encryption — the ≤4KB rule

**KMS will only directly encrypt data up to 4KB.** For anything bigger, use the **GenerateDataKey** pattern (**envelope encryption**):

```
 You: "GenerateDataKey" ──▶ KMS
 KMS returns: ┌─ plaintext data key  (use it to encrypt your 100MB locally, then discard)
              └─ encrypted data key  (store it next to the ciphertext)
 Decrypt later: send encrypted data key ─▶ KMS unwraps it ─▶ decrypt locally
```

The big data never travels to KMS; KMS only wraps/unwraps the small **data key**. "Encrypt a large file with KMS" → **envelope encryption / GenerateDataKey**, never "KMS encrypts it directly".

## Deletion, multi-Region, and Bucket Keys

**THE trap: there is NO immediate key deletion.** Scheduling deletion imposes a **mandatory 7–30 day waiting period** (default 30). Any answer that "deletes the KMS key immediately" is wrong — deleting a key makes everything it encrypted unrecoverable, so AWS forces you to wait. Need to stop use *right now*? **Disable** the key (instant, reversible).

**Multi-Region keys**: the **same key material** replicated into other Regions with matching key IDs — **encrypt in one Region, decrypt in another**. The use cases: **DynamoDB global tables, cross-Region disaster recovery**, client-side encryption for globally moving data.

**S3 Bucket Key recap**: instead of one KMS call per object, S3 uses a short-lived bucket-level key → **far fewer KMS API calls → cheaper** (KMS request costs drop ~99%), at the price of **coarser CloudTrail audit granularity** (you see bucket-key events, not one event per object).

## CloudHSM — when the shared vault isn't enough

**CloudHSM** = **dedicated, single-tenant** hardware security modules in your VPC.

- **FIPS 140-2 LEVEL 3** validated — **KMS is Level 2**. The moment a question says "Level 3", the answer is CloudHSM. (FIPS 140-2 is the US government's crypto-module security standard; Level 3 adds physical tamper-resistance requirements.)
- **YOU manage the keys; AWS has no access to them** — AWS manages the hardware only.
- Use cases: strict **regulatory/compliance** mandates, **BYOK**-style full key custody, **SSL/TLS offload**, running your own certificate authority.

- **KMS custom key store**: authorize KMS to use **your CloudHSM cluster** as the key backend — you keep KMS's service integrations and CloudTrail audit, while key material lives in single-tenant HSMs you control.
- CloudHSM stores **keys**, not passwords/secrets (that's Secrets Manager).
- **THE trap:** run **at least two HSMs in different AZs**. With a single HSM, keys created since the last **daily backup** can be lost — and if you lose your HSM credentials, **AWS cannot recover your keys**.

**Decision rule:** "AWS must not be able to access the keys" / "FIPS 140-2 Level 3" / "dedicated hardware" → **CloudHSM**. Everything else — integration, audit, low cost, ease → **KMS**.

## Question patterns

> *"Security team must audit every use of an encryption key."* → **KMS + CloudTrail** (every key use is logged — KMS's superpower).

> *"Encrypt a 100MB file using KMS."* → **Envelope encryption via GenerateDataKey** (KMS only encrypts ≤4KB directly).

> *"A compromised key must be deleted immediately."* → **Impossible — 7–30 day mandatory waiting period; disable it now instead**.

> *"Compliance requires FIPS 140-2 Level 3 validated modules."* → **CloudHSM** (KMS is Level 2).

> *"Keys must be inaccessible even to AWS."* → **CloudHSM** (single-tenant, customer-controlled).

> *"Encrypt data in us-east-1, decrypt the same ciphertext in eu-west-1 (DR/global tables)."* → **KMS multi-Region keys**.

> *"Keys must rotate automatically every year under company control."* → **Customer-managed key with auto-rotation enabled**.

> *"KMS request costs exploded from millions of S3 objects with SSE-KMS."* → **Enable S3 Bucket Key** (fewer KMS calls; accept coarser audit).

> *"User has full IAM KMS permissions but still gets AccessDenied on a key."* → **Key policy doesn't allow them — BOTH key policy and IAM must permit**.

> *"Want KMS integration with S3/EBS, but key material must live in dedicated HSMs you control."* → **KMS custom key store backed by CloudHSM**.

> *"CloudHSM must not lose keys if an HSM fails."* → **Cluster of 2+ HSMs across AZs** (a single HSM risks keys created since the last daily backup).

> *"Lambda needs to decrypt with a CMK — what goes in the key policy?"* → **The Lambda execution role** (permissions follow the principal).

> *"Sensitive values in Lambda environment variables are visible in the console."* → **Encrypt with a CMK via encryption helpers, or move them to Secrets Manager** (default encryption is at rest only).

## Pocket card

| Keyword | Answer |
|---|---|
| Audit every key use | KMS + CloudTrail |
| Free, AWS-rotated key | AWS-managed key |
| Your policies, $1/mo, yearly rotation | Customer-managed key |
| Encrypt > 4KB | Envelope encryption / GenerateDataKey |
| Delete key now | Impossible — 7–30 day wait (disable instead) |
| Encrypt/decrypt across Regions | Multi-Region keys |
| Cut KMS costs on S3 | S3 Bucket Key |
| FIPS 140-2 Level 3 | CloudHSM |
| "AWS cannot see keys" / dedicated hardware | CloudHSM |
| SSL offload / own CA | CloudHSM |
| Access needs key policy AND IAM | Both must allow |
| Lambda/ECS uses a key | Grant the role (permissions follow the principal) |
| KMS + your own HSMs | Custom key store (CloudHSM) |
| CloudHSM high availability | 2+ HSMs in different AZs |
| Lost CloudHSM credentials | Keys unrecoverable — AWS can't help |
| Store passwords? | Not KMS/CloudHSM — Secrets Manager |

You now hold the keys — next, the safes where applications keep their passwords: Secrets Manager and Parameter Store.
