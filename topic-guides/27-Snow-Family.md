# Section 27: Snow Family

## The idea

Here's a physics problem AWS can't engineer away: **bandwidth**. Try to upload 100 TB over a 100 Mbps connection and the math says roughly **100+ days** — and that's if nobody else touches the network. Amazon's solution is delightfully low-tech: *never underestimate the bandwidth of a truck full of hard drives*. AWS ships you a ruggedized, encrypted storage box; you copy your data onto it locally at LAN speed; you ship it back; AWS loads it into S3.

**Rule of thumb the exam loves:** if transferring over the network would take **more than about a week**, use a Snow device instead.

The second superpower: Snow devices carry **compute**. They can run EC2 instances and Lambda functions on-board, which means you can process data at places with no internet at all — ships at sea, mines, military bases, remote research stations. That's "edge computing."

## The device lineup

| Device | Capacity | When |
|---|---|---|
| **Snowcone** | 8–14 TB | Tiny, rugged, ships anywhere (even drone-deliverable); small edge sites |
| **Snowball Edge Storage Optimized** | ~80 TB usable | **The workhorse** — migrations of ~50–500 TB (order several) |
| **Snowball Edge Compute Optimized** | Less storage, more CPU + **optional GPU** | Edge processing: run EC2/Lambda where there's no connectivity |
| **Snowmobile** | Up to **100 PB** | An actual **45-foot shipping-container** truck for **exabyte-scale** moves (several trucks); consider at **>10 PB** |

**Snowball Edge Storage Optimized specs** (worth recognizing): **80 TB usable HDD**, **40 vCPUs**, **1 TB SATA SSD**, and up to **40 Gb** networking. Snowball Edge was offered in three configurations: **Storage Optimized**, **Compute Optimized**, and **Compute Optimized with GPU**.

Extra flavor points:
- **Snowcone** comes with the **DataSync agent preinstalled** — copy data on it, and it can sync back online later, or you ship it.
- Multiple Snowballs can be ordered in parallel for big jobs (e.g., 200 TB ≈ 3 × 80 TB Snowball Edge Storage Optimized).
- **AWS OpsHub** = the **GUI application** for managing Snow devices (no CLI wrestling required).

## The process

1. **Order** the device in the AWS console.
2. AWS **ships** it to you.
3. You connect it locally and **copy data — encrypted automatically with KMS** (Key Management Service). Keys never live on the device in usable form.
4. **Ship it back** (E Ink label updates itself).
5. AWS **loads the data into S3**, then securely wipes the device.

THE trap: **Snowball cannot import directly into S3 Glacier.** Data always lands in **S3 first**; if you want Glacier, you attach an **S3 lifecycle rule** that transitions the objects afterward. Any answer choice saying "import from Snowball straight to Glacier" is wrong — reliably tested. (By contrast, **DataSync** can write online **directly to S3 Glacier Deep Archive**; see Section 25. Shipped data = S3 first; network copy = straight into the archive class.)

**Edge computing angle:** Snowball Edge Compute Optimized (with optional GPU) runs EC2 AMIs and Lambda locally. Scenario smells: "vessel collecting sensor data with intermittent connectivity," "remote facility must process video before transfer." Process on the device, ship or sync results later.

## Question patterns

> *"Migrate 200 TB, the site has a 100 Mbps link, deadline in 3 weeks"* → **Snowball Edge Storage Optimized** (network math = months, so ship devices — a few 80 TB units)

> *"Decommission an entire datacenter: multiple petabytes (>10 PB) to AWS"* → **Snowmobile** (past ~10 PB, send the truck)

> *"Research ship must run analysis on collected data with no internet connectivity"* → **Snowball Edge Compute Optimized** (compute at the disconnected edge; GPU if ML is mentioned)

> *"Company wants to archive 80 TB directly into S3 Glacier using Snowball"* → **Import to S3, then lifecycle rule to Glacier** (Snowball can't write to Glacier directly — THE trap)

> *"Small remote clinic needs to transfer ~8–10 TB from a space- and power-constrained site"* → **Snowcone** (tiny footprint, tiny capacity)

> *"Transfer 40 TB once; would take 6 weeks over the existing connection"* → **Snowball Edge** (>1 week over the wire → Snow family)

> *"Manage Snow devices with a graphical interface"* → **AWS OpsHub** (the Snow GUI)

## Pocket card

| Keyword | Answer |
|---|---|
| Transfer would take > 1 week | Snow family |
| 8–14 TB, tiny/rugged/edge | Snowcone |
| 50–500 TB migration | Snowball Edge Storage Optimized |
| Process data offline / GPU at edge | Snowball Edge Compute Optimized |
| > 10 PB, up to 100 PB | Snowmobile |
| Straight to Glacier? | No — S3 first + lifecycle rule |
| Encryption on device | KMS, automatic |
| GUI for Snow devices | OpsHub |
| Preinstalled DataSync agent | Snowcone |
| Snowball Edge Storage Optimized specs | 80 TB HDD, 40 vCPU, 1 TB SSD, 40 Gb |
| Exabyte-scale, 45-ft container | Snowmobile |
| Straight to Deep Archive, online | DataSync (not Snow) |

Once your data (and everything else) is in AWS, you'll want to build environments the same way twice without clicking — that's CloudFormation's whole reason to exist.
