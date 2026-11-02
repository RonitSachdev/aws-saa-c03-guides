# Section 8: CloudFront & Global Accelerator

## The idea

Here's the physics problem AWS can't wish away: **far away = slow**. Your app lives in us-east-1, your user sits in Singapore, and every request has to cross half the planet — hundreds of milliseconds of lag, packet loss on the choppy public internet, unhappy users.

AWS gives you **two opposite strategies** to fight distance, and the exam loves testing whether you can tell them apart:

1. **CloudFront: bring the CONTENT closer.** Cache copies of your files at **400+ edge locations** worldwide. Think of a **bookstore chain**: instead of every customer flying to one warehouse, the chain stocks the popular books on the shelves of local stores. First customer waits for delivery (cache miss); everyone after grabs it off the shelf (cache hit).
2. **Global Accelerator: make the JOURNEY faster.** Nothing is cached, nothing is copied. Instead, the user's traffic **enters the AWS private backbone at the nearest edge location** and rides AWS's own fiber the rest of the way — a **private highway** instead of the congested public internet. Same warehouse, much better road.

```
CloudFront:            Global Accelerator:
User → edge (CACHED!)  User → nearest edge → AWS backbone → your app
       done.                   (in the path, no caching, every packet)
```

Content closer vs journey faster. Hold on to that, and most questions solve themselves.

## CloudFront (CDN — Content Delivery Network)

- **Origins** = where CloudFront fetches the real content: **S3 buckets, ALBs, or any HTTP server** (even outside AWS).
- **TTL (Time To Live)** = how long an edge keeps a cached copy. **Longer TTL → fewer trips to the origin → less origin load** ("reduce load on origin" = increase TTL / improve caching).
- The origin can also control cache duration with **`Cache-Control: max-age`** and **`Expires`** headers. Shorter TTLs suit dynamic content; CloudFront shines for **frequently downloaded static files** cached near users.
- **Cache behaviors** = per-**URL path pattern** settings (e.g., `/images/*` cached a day, `/api/*` not cached, each possibly to a different origin).
- **Invalidation** = force-expire cached content early (e.g. `/*` for everything). It **costs money** — the cheap habit is versioned filenames (`app-v2.js`) instead. Versioning also wins because it beats **corporate proxy/browser caches** that never hear about your invalidation, shows the exact version in **access logs**, lets you **serve different versions** at once, and makes **rollback** trivial.
- **Origin Shield** = an extra, centralized **caching layer in front of your origin** (one Region chosen as the shield). Edge caches miss → they ask the shield instead of the origin, so the origin sees far fewer requests. Signal: *"improve cache hit ratio / reduce origin load across many edge locations"*.
- **CloudFront also accelerates DYNAMIC content** — even uncacheable requests benefit from riding AWS's network from the edge to the origin. Don't dismiss CloudFront just because the content isn't static.

**Locking the bucket: OAC.** If users can hit your S3 bucket directly, they bypass CloudFront (and your caching, and your paywall). **OAC (Origin Access Control)** makes the bucket private and grants CloudFront alone the right to read it.

**THE trap:** *"S3 content must be accessible ONLY via CloudFront"* → **OAC**. You'll see **OAI (Origin Access Identity)** as a distractor — it's the **legacy** mechanism (a special CloudFront identity you grant read access in the bucket policy); OAC is the modern answer.

**Paid/private content:**

| Mechanism | Scope | Signal |
|---|---|---|
| **Signed URL** | **ONE file** | "give a customer access to a single video/file"; also when clients **don't support cookies** (and legacy **RTMP** distributions) |
| **Signed Cookies** | **MANY files** | "subscribers can access the whole premium library", HLS video segments, or *"don't want to change the URLs"* |
| **S3 presigned URL** | One S3 object, **direct from S3** | "temporary access to an S3 object" — but it **bypasses CloudFront** and needs a unique URL per file (doesn't scale to many files/users) |

Keep the two locks apart: **signed URLs/cookies restrict WHO may view content**; **OAC/OAI restricts the PATH** (S3 reachable only through CloudFront). A private CloudFront site usually uses both.

**Geo Restriction** = allow-list or block-list entire **countries** at the edge. Signal: *"licensing agreements"*, *"block users from country X"*. (CloudFront isn't in your VPC — this happens at the edge.)

**Customizing at the edge** — three tools, increasing power (deep dive on the two function types in Section 13):

| Requirement | **Response headers policy** | **CloudFront Functions** | **Lambda@Edge** |
|---|---|---|---|
| Add/override response headers (security headers, CORS) | ✅ (no code) | ✅ | ✅ |
| Lightweight request manipulation (URL rewrite, redirect, header normalize) | ❌ | ✅ (cheapest, sub-ms) | ✅ |
| Inspect **User-Agent** and choose **WebP vs JPEG**, rewrite bodies, call other services | ❌ | ❌ | ✅ |

THE trap: a response headers policy **only manages response headers** — it can't make User-Agent-based decisions. Lambda@Edge also runs on the edge locations, so it's the "run code close to users" answer (e.g., Lambda@Edge + Kinesis for global clickstream collection).

**THE trap:** *"custom SSL certificate for a CloudFront distribution"* → the ACM certificate **must be in us-east-1**, no matter where anything else lives. Free exam point.

**Field-level encryption** = encrypt specific sensitive form fields (credit card number) **at the edge**, so only your final application — not even your origin infrastructure — can decrypt them.

## Global Accelerator

- Gives you **2 static anycast IP addresses** — the same two IPs work worldwide, and they **never change**. Anycast means the internet automatically routes each user to the *nearest* AWS edge announcing those IPs. **Static IPs = the whitelisting answer**: when a client's firewall team demands fixed IPs to allow, CloudFront (thousands of shifting edge IPs) can't help; GA can.
- Handles **ANY TCP or UDP traffic** — not just HTTP. Signal words: **gaming (UDP!), VoIP, IoT, MQTT**.
- **No caching, ever.** GA is a road, not a warehouse.
- **Endpoints**: ALBs, NLBs, EC2 instances and Elastic IPs — in **one or multiple Regions** (signal: *"multi-Region application traffic routing"*).
- **Instant failover (~30 seconds)**: GA sits **in the request path** and health-checks your endpoints, so when a region dies it reroutes immediately — **no DNS-cache lag**, because clients keep using the same two IPs the whole time. This is exactly the weakness of Route 53 failover (clients cache old DNS answers) solved.

## THE comparison table

| | **CloudFront** | **Global Accelerator** |
|---|---|---|
| Strategy | Content closer (cache) | Journey faster (backbone) |
| Protocol | HTTP/HTTPS | **Any TCP/UDP** |
| Caching | **Yes** — that's the point | **No** — never |
| Static IPs | No (many changing edge IPs) | **Yes — 2 static anycast IPs** |
| Failover | n/a (origin failover exists, but) | **In-path, ~30s, no DNS lag** |
| Use cases | Websites, video, APIs, downloads | Gaming, VoIP, IoT, whitelisting, instant multi-region failover |

## The three-way direction trap

The exam loves this triangle — read the **direction and protocol** of the traffic:

```
Global users DOWNLOAD/view content (HTTP)   → CloudFront
Global users UPLOAD to an S3 bucket         → S3 Transfer Acceleration
Global users use a TCP/UDP app (non-HTTP)   → Global Accelerator
```

(S3 Transfer Acceleration uses the same edge network, but for **uploads into S3** — "users worldwide upload large files to a central bucket" is its exact sentence. Pair it with **multipart upload** for big files, >100 MB.)

**Transfer Acceleration vs Global Accelerator** — both ride edge locations + the AWS backbone, but: Transfer Acceleration is **S3-only, HTTP(S), one bucket endpoint**; Global Accelerator fronts **your application** (ALB/NLB/EC2) for **any TCP/UDP** traffic and gives **static anycast IPs**. "Faster transfers to a bucket" → Transfer Acceleration; "faster/failover-proof access to an app" → GA.

### Two easy-to-miss CloudFront features (practice-test lessons)

- **Origin group** = a **primary + secondary origin** pair: when the primary returns errors, CloudFront **automatically retries against the secondary**. THE answer to "configure CloudFront for high availability / origin failover." (Geo restriction next to it is the false twin — that's country blocking, not HA.) Failover triggers on the **HTTP status codes you choose**. An Auto Scaling group can't be an origin by itself (put an ALB in front; EC2 origins should span multiple AZs), and a **Lambda@Edge function can't be a member** of an origin group.
- **Price class** = which **edge locations** your distribution uses (all = best latency, fewer = cheaper). It's a **cost dial** — it has nothing to do with routing to origins. "Reduce CloudFront costs, tolerate higher latency in some regions" → price class.

## Question patterns

> *"Serve a static website to users worldwide with low latency; the S3 bucket must not be publicly accessible"* → **CloudFront + S3 origin + OAC** (cache at edges, lock the bucket to CloudFront only).

> *"Paying subscribers should stream any video in the premium catalog"* → **Signed Cookies** (MANY files = cookies; ONE file = signed URL).

> *"Send a customer a link to download a single report"* → **Signed URL** (one file, one URL).

> *"Multiplayer game over UDP has high latency for global players"* → **Global Accelerator** (UDP rules out CloudFront instantly).

> *"Enterprise clients' firewalls require a small set of FIXED IP addresses to whitelist"* → **Global Accelerator** (2 static anycast IPs — the only global service that offers this).

> *"Multi-region app needs failover in seconds, without waiting for DNS caches"* → **Global Accelerator** (in-path health checks, same IPs before and after).

> *"Licensing forbids streaming the content in certain countries"* → **CloudFront Geo Restriction** (country-level block at the edge).

> *"Reduce the load on the origin server behind CloudFront"* → **Increase TTL / improve cache hit ratio** (more hits at the edge = fewer origin fetches).

> *"Users around the world upload large files into one S3 bucket, uploads are slow"* → **S3 Transfer Acceleration** (UPLOAD direction — not CloudFront).

> *"Attach a custom domain certificate to a CloudFront distribution"* → **ACM certificate in us-east-1** (always, regardless of your app's region).

> *"Private S3 videos served through CloudFront; links are S3 presigned URLs"* → **switch to CloudFront signed URLs/cookies** (presigned URLs bypass CloudFront)

> *"Serve WebP or JPEG depending on the browser's User-Agent"* → **Lambda@Edge** (response headers policy only sets headers)

> *"Many edge locations hammer the origin with cache misses"* → **Origin Shield**

> *"Users behind corporate proxies keep getting the old file after a deploy"* → **versioned file names** (proxies ignore CloudFront invalidations)

## Pocket card

| Keyword in question | Answer |
|---|---|
| global static content, low latency | **CloudFront** |
| "S3 only via CloudFront", private bucket | **OAC** (OAI = legacy distractor) |
| one paid file | **Signed URL** |
| whole paid library | **Signed Cookies** |
| block/allow countries | **Geo Restriction** |
| CloudFront custom cert | **ACM in us-east-1** |
| encrypt one sensitive field end-to-end | Field-level encryption |
| reduce origin load | Longer TTL / better caching |
| force-refresh cached files | Invalidation (`/*`, costs money) |
| UDP / gaming / VoIP / non-HTTP | **Global Accelerator** |
| fixed IPs for whitelisting | **Global Accelerator** (2 anycast IPs) |
| instant failover, no DNS-cache lag | **Global Accelerator** |
| global UPLOADS to S3 | **S3 Transfer Acceleration** |
| temporary access to one S3 object (no CloudFront) | S3 presigned URL |
| extra cache layer in front of origin | **Origin Shield** |
| cheap request manipulation at edge | CloudFront Functions |
| add security headers, no code | Response headers policy |
| User-Agent logic / WebP vs JPEG | **Lambda@Edge** |
| different settings per URL path | Cache behavior |

Both of these services exist to get users to your data faster — but the data itself usually lives in a database, and how you make *that* fast and failure-proof is Section 9's RDS and Aurora.
