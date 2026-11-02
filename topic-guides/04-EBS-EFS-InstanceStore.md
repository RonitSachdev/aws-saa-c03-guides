# Section 4: EBS, EFS & Instance Store

## The idea

Your EC2 instance needs somewhere to put its files. AWS gives you three very different kinds of "somewhere," and the exam loves making you pick between them.

Here's the analogy: think of your instance as a desk in an office.

- **EBS (Elastic Block Store)** is your **personal external hard drive** plugged into your desk. It's actually a network-attached drive (the data lives on separate storage servers, not inside your computer), but it feels local. Unplug it from one desk, plug it into another. It's *yours alone*.
- **EFS (Elastic File System)** is the **shared network folder** the whole office mounts. Everyone sees the same files at the same time.
- **Instance Store** is the **notepad glued to the desk itself**. Blazing fast to scribble on — but when you give up the desk, the notepad goes in the shredder.

Three storage types, three personalities: **private and persistent (EBS), shared (EFS), fast but disposable (Instance Store).** Let's take them in turn.

## EBS: your network-attached hard drive

Rules of the game — each one is exam-tested:

- An EBS volume lives in **exactly one Availability Zone**. To move it to another AZ, you snapshot it and restore the snapshot there. Within that AZ, AWS **automatically replicates** the volume to protect against component failure. That protection isn't cross-AZ; for that you need snapshots.
- **Elastic Volumes**: you can change a volume's **type, size, and IOPS/throughput live**, while it's attached and in use. No detach or downtime is needed.
- It attaches to **one instance at a time** — with one exception: **io1/io2 Multi-Attach**, which lets up to **16 instances in the same AZ** attach the same volume (for cluster-aware software only, not ordinary filesystems).
- It **persists independently** of the instance — the drive outlives the desk...
- ...**except** for the deletion flags: the **root volume** is created automatically and has **DeleteOnTermination = true by default** (terminate the instance, lose the root disk). **Extra attached volumes default to false** — they survive. So *"the root volume must survive termination"* → **turn DeleteOnTermination off** for the root volume.
- A freshly attached extra volume is a **raw disk**: you must **format it, mount it, and add it to /etc/fstab** yourself, or it vanishes from the mount table on reboot.

### The one axis that decides everything: IOPS vs Throughput

Every EBS question secretly asks: is this workload about **many small random operations** or **big sequential streams**?

- **IOPS** (input/output operations per second) = **lots of small, random reads/writes**. That's what **databases** do — hop around the disk grabbing tiny rows.
- **Throughput** (MB/s) = **large, sequential** reads/writes. That's **big data, log processing, ETL, streaming** — chewing through giant files front to back.

The full decision tree:

```
Random I/O? Database? Boot volume?
        │
        ▼ yes                          no ▼ (big sequential data)
      SSD                                HDD  ← cannot be a boot volume!
        │                                 │
  ≤ 16,000 IOPS?                   accessed frequently?
   │          │                     │            │
   ▼ yes      ▼ no                  ▼ yes        ▼ no (cold)
  gp3      io1/io2                 st1          sc1
 (default) (provisioned IOPS;   (throughput-  (cheapest
            io2 Block Express    optimized     EBS there is)
            → 256,000 IOPS,      HDD)
            sub-ms latency,
            Multi-Attach)
```

**The 16,000 IOPS threshold decides most questions.** Need 12,000 IOPS? gp3 does that (and cheaply). Need 50,000? Only io1/io2 can. Need up to **256,000 IOPS with sub-millisecond latency**? **io2 Block Express.** And remember: **HDD volumes (st1/sc1) can never be boot volumes.** Provisioned IOPS SSD is the pick for **> 16,000 IOPS or > 250 MiB/s per volume**. The **magnetic "standard"** volume type is **previous-generation (legacy)**, so don't choose it for new workloads.

The SSD vs HDD family at a glance:

| | **SSD** (gp2/gp3/io1/io2) | **HDD** (st1/sc1) |
|---|---|---|
| Best for | **Small, random** I/O | **Large, sequential** I/O |
| Bootable | **Yes** | **No** |
| Use cases | Transactional workloads, sustained IOPS, databases (MongoDB, Oracle, SQL Server) | Streaming, big data, data warehouses, log processing, infrequently accessed throughput data |
| Cost | Moderate / high | Low |
| Dominant performance attribute | **IOPS** | **Throughput (MiB/s)** |

**The io1 IOPS math (the 50:1 rule):** io1 volumes are **4 GiB – 16 TiB** and can be provisioned with **100 to 64,000 IOPS** on Nitro instances (32,000 on other instances). The catch: the **maximum IOPS-to-size ratio is 50:1**, so **max IOPS = size in GiB × 50**.

| io1 volume size | Max provisionable IOPS |
|---|---|
| 10 GiB | 10 × 50 = **500 IOPS** |
| 100 GiB | 5,000 IOPS |
| 640 GiB | **32,000 IOPS** (the non-Nitro ceiling) |
| 1,280 GiB+ | 64,000 IOPS (the Nitro ceiling) |

Worked trap: *"a 10 GiB io1 volume provisioned with 1,000 IOPS"* is impossible, because 1,000 > 10 × 50. (**io2** allows **500 IOPS per GiB**.)

**gp2 fine print (legacy, but still asked):** 1 GiB – 16 TiB, at 3 IOPS/GiB with a **100 IOPS floor** (volumes ≤ 33.33 GiB) and a **16,000 IOPS ceiling**. Small volumes **burst to 3,000 IOPS** using credits.

**RAID on EBS (configured inside the OS, not by AWS):**

| | RAID 0 (striping) | RAID 1 (mirroring) |
|---|---|---|
| Goal | **Performance**: combined IOPS/throughput of all volumes | **Redundancy**: same data written to 2 volumes |
| Fault tolerance | **None**: lose one volume, lose the array | Survives a volume loss |
| Exam signal | "more IOPS/throughput than one volume gives" | "mirror the data on two volumes" |

(RAID is an **EBS** technique. EFS is a managed network file system and isn't assembled into a RAID array.)

### gp2 vs gp3: the free-money question

| | gp2 (old) | gp3 (new) |
|---|---|---|
| IOPS | **chained to size: 3 IOPS per GB**, bursts to 3,000 | **baseline 3,000 IOPS + 125 MB/s at ANY size** |
| Scaling performance | must grow the volume to grow IOPS | **provision IOPS and throughput independently** |
| Price | baseline | **~20% cheaper** |

On gp2, wanting more IOPS meant buying storage you didn't need. gp3 broke that chain. So the moment a question mentions **gp2**, the answer is almost always **"migrate to gp3"**. And *"needs more IOPS without paying for more storage"* → **gp3** (independent provisioning). It's the exam's favorite free lunch.

### Snapshots: the time machine

- Snapshots are **incremental backups stored in S3** — only changed blocks after the first one, so they're cheap. Taking a snapshot is **point-in-time and non-blocking**: the volume keeps serving **reads and writes** while the snapshot is in progress.
- You can **copy a snapshot to another region** — that's the answer to **cross-region disaster recovery** ("back up EBS data to another region" → snapshot, copy it over).
- **Snapshot Archive tier**: **~75% cheaper**, but restore takes **24–72 hours**. Keyword: "rarely restored, minimize snapshot cost."
- **Recycle Bin**: retention rules that catch accidentally deleted snapshots so you can recover them.
- **Fast Snapshot Restore (FSR)**: normally a volume restored from a snapshot is lazily loaded (first read of each block is slow). FSR pre-warms it for **full performance instantly — but it's expensive**. Keyword: "no latency on first access after restore."
- **Data Lifecycle Manager (DLM)**: **automates** snapshot creation, retention, and deletion on a schedule. "Automate EBS backups" → DLM.
- **DLM vs AWS Backup:** DLM covers **EBS snapshots and EBS-backed AMIs only**. If the question spans **several services** (EBS + RDS + DynamoDB + EFS…) or wants central, cross-account backup policies, the answer is **AWS Backup** (see Section 35).

### Encryption: the snapshot-copy dance

Encryption is sticky in the happy direction: **an encrypted volume produces encrypted snapshots, and encrypted snapshots produce encrypted volumes.** Everything downstream inherits it, with essentially no performance cost.

But **you cannot flip encryption on for an existing unencrypted volume in place**. The exam's required choreography:

```
unencrypted volume → snapshot it → COPY the snapshot (enable encryption
on the copy) → create a new volume from the encrypted copy → swap it in
```

Any question about "encrypt an existing EBS volume" is testing whether you know this **snapshot → copy-encrypted → restore** dance.

Encryption fine print:

- **What's covered:** data **at rest** on the volume, data **in transit between the instance and the volume**, all **snapshots** created from it, and all **volumes created from those snapshots**.
- **The crypto:** **AES-256** with **KMS keys**. EBS supports only **symmetric** KMS keys, never asymmetric ones.
- **Encryption by default** is a **per-Region account setting**. Once you turn it on, every new volume and snapshot copy in that Region is encrypted, and you **can't opt out for an individual volume**. The **instance type must support EBS encryption** (all current-generation types do). Signal: *"ensure ALL new EBS volumes are encrypted with no per-launch effort"* → **enable EBS encryption by default**.

## EFS: the shared network folder

**EFS (Elastic File System)** is a managed **NFS** (Network File System — the classic Linux shared-folder protocol) file system. The personality traits:

- **Mounted by many instances at once, across multiple AZs.** This is the whole point — EBS is one-instance-one-AZ; EFS is the office-wide shared drive.
- **Linux ONLY.** THE trap: **Windows instances cannot mount EFS. Windows shared storage → FSx for Windows File Server** (SMB protocol, Active Directory integration). Read the OS in the question before answering "EFS."
- **Elastic**: it auto-grows and shrinks; **you pay per GB actually used**, no capacity planning.
- Pricier per GB than EBS — but you buy zero unused space, and lifecycle tiers claw back cost.
- **POSIX-compliant** (standard Linux file permissions and semantics). It scales from **GB to PB**, serves **thousands of concurrent instances**, and can be mounted by **ECS tasks, Lambda**, and **on-premises servers** (over Direct Connect/VPN).
- **Latency:** EBS has the **lowest latency**. EFS is a network file system, so expect **higher latency than EBS**. S3 has no low-latency file operations at all. EFS has **no native "present S3 objects as files"** integration; that's **FSx for Lustre**.

Dials you can turn (exam wants recognition, not depth):

| Dial | Options | Pick when |
|---|---|---|
| Performance mode | **General Purpose** (default) / **Max I/O** | Max I/O = thousands of concurrent clients, tolerate higher latency (big data) |
| Throughput mode | **Elastic** (recommended) / Provisioned / Bursting | Elastic = auto-scales throughput, the modern default |
| Lifecycle | Standard → **Infrequent Access (IA)** → **Archive** | Auto-move cold files to cheaper tiers → big savings (~90%+ on IA) |

**The signature use case:** a fleet of instances behind an Auto Scaling Group that must all see the same files — **user uploads, CMS content, WordPress wp-content**. "Multiple EC2 instances need shared access to the same files (Linux)" → **EFS**, every time.

## Instance Store: the notepad glued to the desk

**Instance Store** is physical disk **inside the host machine itself** — no network hop at all. Consequences:

- **Fastest storage EC2 offers** — NVMe instance store reaches **millions of IOPS**, far beyond anything EBS can do.
- **EPHEMERAL** (temporary): data is **lost when the instance stops, hibernates, or terminates** — though it **survives a reboot** (a reboot stays on the same host; a stop can move you to a different one, and someone else's desk has a different notepad).
- **Cannot be detached, cannot be snapshotted** through EBS mechanisms, size is fixed by the instance type.

Legit uses: **cache, buffer, scratch space, temp processing files**, or data that's **replicated at the application layer** anyway (Cassandra nodes replicate to each other, so losing one node's local disk is survivable).

**THE trap:** *"highest possible IOPS AND data must persist"* — instance store wins the IOPS contest but flunks persistence. The answer is **io2 (Block Express) EBS**. The word **"persist"** disqualifies instance store instantly.

## The five-storage lineup

| Storage | One-liner |
|---|---|
| **Instance Store** | Fastest, physical, ephemeral — cache/scratch/replicated data only |
| **EBS** | Network block device, one instance (mostly), one AZ, persistent — boot volumes and databases |
| **EFS** | Shared NFS folder, multi-AZ, many Linux instances, pay-per-use — shared content |
| **FSx** | Managed third-party file systems — **Windows (SMB/AD)**, or Lustre for HPC |
| **S3** | Object storage over HTTP — not a disk at all; apps talk to it via API, effectively unlimited |

Match the storage need to the service:

| Need | Service |
|---|---|
| **Temporary** storage (scratch, buffers, queues, caches) | **Instance Store** |
| **Multi-instance** (shared) storage | **EFS** |
| **Highly durable** storage | **S3** or **EFS** (EBS gets there via snapshots stored in S3) |
| **Static data / web content** | **S3** (no web server needed) or EFS |

Neither an instance store nor a standard EBS volume can be **shared across instances** (io1/io2 Multi-Attach is the narrow exception). Shared means EFS or FSx.

## Question patterns

> *"Database needs 12,000 IOPS, cost-effective"* → **gp3** (under the 16,000 line, and gp3 provisions IOPS cheaply)

> *"Critical database needs 50,000 IOPS"* → **io1/io2** (past 16,000, only provisioned-IOPS SSD plays; sub-ms or 256k IOPS → io2 Block Express)

> *"Sequential processing of large log files, throughput-focused, cost-effective"* → **st1** (big + sequential = HDD; frequent access = st1, cold archive = sc1 — and neither can boot)

> *"gp2 volume needs more IOPS but not more storage"* → **migrate to gp3** (gp2 chains IOPS to size; gp3 provisions them independently and is ~20% cheaper)

> *"Fleet of Linux instances in an ASG must share uploaded files"* → **EFS** (many mounters + multi-AZ + NFS = the shared folder)

> *"Windows instances need shared storage with Active Directory integration"* → **FSx for Windows File Server** (EFS is Linux-only — THE trap)

> *"Fastest possible storage for temporary scratch/cache data"* → **Instance Store** ("temporary" unlocks it; millions of IOPS, ephemeral is fine here)

> *"High IOPS storage whose data must persist after the instance stops"* → **io2 EBS, not instance store** ("persist" disqualifies the notepad)

> *"Data volume must survive instance termination"* → **DeleteOnTermination = false** (root defaults true, extra volumes default false — check which one the question means)

> *"Encrypt an existing unencrypted EBS volume"* → **snapshot → copy with encryption enabled → create volume from the encrypted copy** (no in-place flip exists)

> *"Back up EBS volumes to another region for DR, automatically"* → **DLM-scheduled snapshots + cross-region snapshot copy** (snapshots live in S3 and copy across regions)

> *"Multiple instances must attach the same block volume in one AZ (cluster software)"* → **io1/io2 Multi-Attach** (up to 16 instances, same AZ — block storage, not a file system)

> *"Reduce cost of EFS for files untouched for months"* → **lifecycle policy to EFS IA/Archive** (same trick as S3 tiering, applied to the shared folder)

> *"Maximum IOPS for a 10 GiB io1 volume?"* → **500 IOPS** (50:1 ratio: 10 × 50)

> *"Combine several EBS volumes for more I/O performance than one volume can give; redundancy not required"* → **RAID 0** (striping. RAID 1 = mirroring for redundancy)

> *"Guarantee every new EBS volume in the Region is encrypted"* → **Enable EBS encryption by default** (Region setting; no per-volume opt-out)

> *"Change an in-use volume from gp2 to gp3 and add IOPS without downtime"* → **Elastic Volumes** (modify type/size/IOPS live)

> *"Automate backups of EBS, RDS, and DynamoDB from one place"* → **AWS Backup, not DLM** (DLM = EBS snapshots/AMIs only)

> *"Shared file storage for ECS tasks and on-prem Linux servers, POSIX permissions"* → **EFS**

## Pocket card

| Keyword | Answer |
|---|---|
| random I/O / database / boot volume | SSD (gp3 or io1/io2) |
| large sequential / big data / throughput MB/s | HDD (st1/sc1) — never bootable |
| ≤ 16,000 IOPS | gp3 |
| > 16,000 IOPS | io1/io2 |
| 256,000 IOPS / sub-millisecond | io2 Block Express |
| frequent sequential (logs, ETL) | st1 |
| coldest, cheapest EBS | sc1 |
| gp2 mentioned at all | migrate to gp3 (~20% cheaper) |
| more IOPS without more storage | gp3 (independent provisioning) |
| multiple instances, one block volume, same AZ | io1/io2 Multi-Attach (max 16) |
| root disk survives termination | DeleteOnTermination = false |
| new extra volume unusable | format + mount + fstab |
| move volume across AZ/region | snapshot → (copy) → restore |
| cheap rarely-restored snapshots | Snapshot Archive (75% off, 24–72 hr restore) |
| recover deleted snapshot | Recycle Bin |
| instant full performance from snapshot | Fast Snapshot Restore (expensive) |
| automate snapshot schedules | Data Lifecycle Manager |
| encrypt existing volume | snapshot → copy-encrypted → restore |
| shared files, many Linux instances, multi-AZ | EFS (NFS, pay per GB used) |
| shared files, Windows / SMB / Active Directory | FSx for Windows (never EFS) |
| HPC parallel file system | FSx for Lustre |
| thousands of concurrent EFS clients | Max I/O performance mode |
| EFS throughput default | Elastic mode |
| cut EFS cost on cold files | lifecycle to IA / Archive |
| fastest storage / temp / cache / scratch | Instance Store (ephemeral) |
| instance store + stop/terminate | data gone (reboot survives) |
| high IOPS + must persist | io2 EBS, not instance store |
| Cassandra/replicated data, local speed | Instance Store is OK |
| io1 max IOPS | size (GiB) × 50; up to 64,000 (Nitro) |
| io2 IOPS ratio | 500 IOPS per GiB |
| > 16,000 IOPS or > 250 MiB/s | Provisioned IOPS SSD (io1/io2) |
| magnetic "standard" volume | legacy previous-gen, avoid |
| change type/size/IOPS live | Elastic Volumes |
| stripe volumes for performance | RAID 0 (no redundancy) |
| mirror volumes for redundancy | RAID 1 |
| all new volumes encrypted automatically | EBS encryption by default (per Region) |
| EBS encryption keys | KMS symmetric only, AES-256 |
| I/O during snapshot | continues normally |
| multi-service centralized backups | AWS Backup (DLM = EBS only) |
| POSIX shared FS for ECS / on-prem | EFS |
| lowest-latency storage (persistent) | EBS (EFS higher, S3 not for low-latency file ops) |

You now know where an instance keeps its data — next up, S3 takes storage out of the instance entirely and into the world of objects, buckets, and eleven nines of durability.
