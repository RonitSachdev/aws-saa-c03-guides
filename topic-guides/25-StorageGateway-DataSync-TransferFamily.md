# Section 25: Storage Gateway, DataSync & Transfer Family

## The idea

Here's the hybrid-storage problem: your on-prem servers speak the old languages — **NFS and SMB file shares** (network drives), **iSCSI block volumes** (raw disks over the network), **tape backups**. Meanwhile the cheap, infinite storage lives in AWS. The servers can't be rewritten overnight, so you need cloud storage that **looks local** to them.

The analogy: your office has a cramped filing room, and you've rented an infinite warehouse across town (S3). Three different companies help you use it:

- **Storage Gateway** = a **magic filing cabinet** installed in your office. It looks and behaves like a normal cabinet, but its drawers secretly extend into the warehouse — frequently used folders stay in the drawer (**local cache**), everything else lives across town. This is an **ONGOING bridge** — it stays forever.
- **DataSync** = a **professional moving company**. They show up, load the truck, move your files to the warehouse fast and carefully (labels and permissions intact), and leave. **Migration**, one-time or on a schedule.
- **Transfer Family** = a **staffed loading dock** on the warehouse itself, so outside partners can keep delivering packages the old way (**SFTP**) while everything lands directly in S3.

Jargon check: **NFS** (Network File System, the Linux share protocol), **SMB** (Server Message Block, the Windows share protocol), **iSCSI** (block storage — raw disk — over the network), **SFTP/FTPS/FTP** (classic file-transfer protocols).

### Storage Gateway — the ongoing hybrid bridge

Deployed as a **VM (or hardware appliance) on-premises**, backed by cloud storage, with a **local cache** for low-latency access to hot data. Four flavors — the exam tests which flavor fits:

| Type | Protocol | Backed by | The exam phrase |
|---|---|---|---|
| **S3 File Gateway** | NFS / SMB | **S3** (real objects!) | *"Replace the NAS; files in S3; keep local file access"* |
| **FSx File Gateway** | SMB | **FSx for Windows** | Low-latency on-prem access to FSx Windows shares |
| **Volume Gateway — Cached** | iSCSI | **Primary data in S3**, hot cache local | *"Expand on-prem storage capacity"* — the disk is bigger than your building |
| **Volume Gateway — Stored** | iSCSI | **Primary data LOCAL**, async **snapshots to S3** | *"Low-latency access to the ENTIRE dataset"* + cloud backup / DR |
| **Tape Gateway** | iSCSI VTL | S3 → **Glacier** | *"Replace physical tape backup infrastructure"* — near-verbatim question |

```
 Volume Gateway, the two minds:

 CACHED: cloud is primary          STORED: local is primary
 ┌──────────┐                      ┌──────────────┐
 │ S3 (ALL) │◀── everything        │ Local (ALL)  │◀── everything
 └────▲─────┘                      └──────┬───────┘
      │ hot cache                         │ async snapshots
 ┌────┴─────┐                      ┌──────▼───────┐
 │local cache│  → grow capacity    │  S3 (backup) │  → DR, full-speed local
 └──────────┘                      └──────────────┘
```

**Memory hook:** Cached = **capacity** (cloud holds it all); Stored = **speed + safety** (local holds it all, cloud holds the backup).

THE trap: *"low-latency access to the FULL dataset"* → **Stored**, not Cached — a cache only keeps the hot slice; if latency must be low for *everything*, everything must live locally.

Also worth a point: **Tape Gateway** presents a **Virtual Tape Library (VTL)** so existing backup software (Veeam, NetBackup) keeps working unchanged — the tapes are just... S3 and Glacier now. Any scenario with the word **"tape"** ends at Tape Gateway. Archived virtual tapes can go to **S3 Glacier Flexible Retrieval or S3 Glacier Deep Archive**. *"Lowest-cost long-term tape archive"* → **Deep Archive**.

More gateway facts:

- Storage Gateway exists to **connect existing on-prem storage and apps to cloud storage**. It's **not an application migration tool** (for servers, use Application Migration Service).
- It's **bandwidth-efficient**: it transfers **only changed data** and **compresses** it on the way.
- **Volume Gateway** backs volumes up as **point-in-time EBS snapshots**, so you can restore them as EBS volumes in AWS. That's handy for **backup, DR, and migration** of block data.

### DataSync — the moving company

**AWS DataSync** is the **migration / scheduled-transfer engine**: **one-time or scheduled** sync from on-prem **NFS/SMB** into **S3, EFS, or FSx**. You install an **agent** on-prem, and DataSync moves data fast (it's built for TB-scale over the network) while **preserving file metadata and permissions**, with **bandwidth throttling** so you don't flatten the office internet during business hours. Bonus fact the exam likes: DataSync also moves data **between AWS storage services** — S3 ↔ EFS ↔ FSx — no agent needed for that. DataSync can also **write directly into any S3 storage class, including S3 Glacier Deep Archive**. *"Move on-prem archive files straight to Deep Archive over the network"* → **DataSync**, with no lifecycle hop needed. (DataSync moves **files**. To migrate whole **servers**, use the **replication agent of Application Migration Service (MGN)**.)

**THE distinction of this whole section:**

- **DataSync = MOVE the data** (one-time migration or scheduled copy — the truck leaves).
- **Storage Gateway = ongoing hybrid ACCESS** (the bridge stays; on-prem apps keep reading/writing after — or instead of — migrating).

THE trap: *"migrate 50 TB from on-prem NAS to S3, preserving permissions"* offers "S3 File Gateway" as a shiny wrong answer. A gateway is for *continuing access*, not bulk moves — a **migration** with **metadata preserved** is **DataSync**, every time. Flip side: *"keep using on-prem apps against files that must live in S3"* → gateway, not DataSync.

### Transfer Family — the managed SFTP dock

**AWS Transfer Family** = a fully managed **SFTP / FTPS / FTP endpoint** in front of **S3 or EFS**. Your partners keep their crusty-but-beloved SFTP scripts; the files land straight in your bucket. *"Partners upload via SFTP, must keep their existing workflow"* → **Transfer Family** — and **never** the distractor "run an SFTP server on EC2" (that's undifferentiated heavy lifting the exam always wants you to reject).

### One pointer

Everything above assumes a network path. If the scenario is **offline, or the data is so huge the network math doesn't work** (weeks of transfer time, remote sites, limited bandwidth), that's the **Snow Family** — Section 27's story.

A newer option sits in between: **AWS Data Transfer Terminal**. These are **physical AWS locations** (in select cities) where you **bring your own storage devices** and plug them into a high-throughput connection to upload data to AWS, for example S3. You carry the data in instead of having AWS ship a device to you.

| Option | How the data travels | Signal |
|---|---|---|
| **S3 Transfer Acceleration** | Over the internet, via the nearest **edge location** | Long-distance uploads to one bucket |
| **DataSync** | Over your network (agent) | Online migration/sync, metadata kept |
| **Data Transfer Terminal** | **You physically bring your drives** to an AWS facility | Large dataset, drives in hand, need it uploaded fast without ordering a device |
| **Snow Family** | **AWS ships you a device**, which you ship back | Offline / remote / network would take > 1 week |

## Question patterns

> *"Company wants to eliminate its physical tape backup infrastructure but keep existing backup software"* → **Tape Gateway** (virtual tape library → S3/Glacier; software sees tapes).

> *"Replace an aging NAS; store files in S3 but keep low-latency local access over SMB/NFS"* → **S3 File Gateway** (cloud-backed share with local cache).

> *"Migrate 50 TB from an on-prem NAS to S3, preserving file permissions and metadata, minimal effort"* → **DataSync** (migration engine; preserves metadata; gateway is for ongoing access, not moves).

> *"Business partners upload files via SFTP and cannot change their workflow; files must land in S3"* → **Transfer Family** (managed SFTP endpoint — never build SFTP on EC2).

> *"On-prem app needs low-latency access to the ENTIRE dataset, with backups to AWS for DR"* → **Volume Gateway — Stored** (full data local, async snapshots to S3).

> *"On-prem storage is running out of space; extend capacity while keeping frequently used data fast"* → **Volume Gateway — Cached** (primary in S3, hot cache local).

> *"Copy files nightly from on-prem SMB shares to EFS, with bandwidth throttling"* → **DataSync** (scheduled transfers + throttling are its signature features).

> *"Low-latency on-prem access to file shares stored on FSx for Windows File Server"* → **FSx File Gateway**.

> *"Transfer data between S3 and EFS within AWS"* → **DataSync** (works AWS-to-AWS too, agentless).

> *"Archive virtual tapes at the lowest possible cost"* → **Tape Gateway → S3 Glacier Deep Archive**.

> *"Copy on-prem archive files directly into S3 Glacier Deep Archive over the network"* → **DataSync** (writes straight to the Deep Archive storage class).

> *"Team has hard drives full of data and wants to upload them at high speed at an AWS facility"* → **AWS Data Transfer Terminal** (bring your own device; Snow = AWS ships a device to you).

## Pocket card

| Keyword | Answer |
|---|---|
| Replace tape backups | Tape Gateway (VTL → S3/Glacier) |
| NAS replacement, files in S3, local access | S3 File Gateway |
| SMB cache for FSx Windows | FSx File Gateway |
| Extend on-prem capacity, primary in cloud | Volume Gateway — Cached |
| Full dataset local + snapshots to cloud | Volume Gateway — Stored |
| Migrate / scheduled sync, preserve permissions | DataSync |
| Bandwidth throttling, on-prem agent | DataSync |
| S3 ↔ EFS ↔ FSx transfers | DataSync |
| Partners upload via SFTP/FTPS/FTP | Transfer Family (never SFTP-on-EC2) |
| Ongoing hybrid access vs. one-time move | Storage Gateway vs. DataSync |
| Offline / massive data, no bandwidth | Snow Family (Section 27) |
| Cheapest tape archive tier | Tape Gateway → Glacier Deep Archive |
| Gateway sends only changed, compressed data | Storage Gateway (bandwidth-efficient) |
| Volume Gateway backups restorable in AWS | EBS snapshots |
| Online copy straight to Deep Archive | DataSync |
| Migrate servers (not files) | Application Migration Service, not DataSync/Gateway |
| Bring your own drives to an AWS facility | Data Transfer Terminal |

That's the online bridge to the cloud sorted — when the pipe is too small for the payload, you put the data on a truck, and that's where the Snow Family rolls in.
