# Section 6: VPC — Virtual Private Cloud

## The idea

A VPC is your own **private, fenced-off patch of the AWS cloud** — a network that belongs entirely to you. Think of it as buying a plot of land in a huge city: you decide the street layout (IP ranges), you build rooms (subnets), you decide which rooms have doors to the street (internet access), and you hire guards to check who comes and goes (security groups and NACLs). Nothing gets in or out unless *you* built a door for it.

This is the **biggest topic on the SAA-C03 exam** — networking questions are everywhere, and they're very pattern-matchable once the mental model clicks. So let's build it.

## Boxes in boxes

Everything in VPC-land nests:

```
┌──────────────── AWS Region (e.g., us-east-1) ────────────────┐
│  ┌──────────────── VPC  10.0.0.0/16 ────────────────────┐    │
│  │  ┌──── AZ-a ──────────────┐  ┌──── AZ-b ───────────┐ │    │
│  │  │ Public subnet          │  │ Public subnet       │ │    │
│  │  │  10.0.1.0/24           │  │  10.0.2.0/24        │ │    │
│  │  │  [web EC2]  [NAT GW]   │  │  [web EC2] [NAT GW] │ │    │
│  │  ├────────────────────────┤  ├─────────────────────┤ │    │
│  │  │ Private subnet         │  │ Private subnet      │ │    │
│  │  │  10.0.11.0/24          │  │  10.0.12.0/24       │ │    │
│  │  │  [app EC2]  [database] │  │  [app EC2] [db]     │ │    │
│  │  └────────────────────────┘  └─────────────────────┘ │    │
│  │            ▲ Internet Gateway (IGW) — the front door  │    │
│  └────────────┼──────────────────────────────────────────┘    │
└───────────────┼───────────────────────────────────────────────┘
                ▼  Internet
```

- **Region > VPC > subnets > instances.** A VPC lives in ONE region; a **subnet lives in ONE Availability Zone** (so multi-AZ = multiple subnets).
- **Route tables are the road signs.** Each subnet has a route table saying "traffic for X goes via Y." Change the signs, change the network. A new subnet you don't explicitly associate is automatically tied to the VPC's **main route table**.

## Public vs private: it's all about the route

- An **Internet Gateway (IGW)** is the VPC's **two-way front door** — traffic can go out AND the internet can come in (to public IPs). It has **two jobs**: be a **route-table target** for internet-bound traffic, and perform **NAT for instances with public IPv4 addresses** (the instance only knows its private IP; the IGW maps it to the public one).
- **THE definition** — memorize this exactly: a subnet is **public** if its route table has a route to the IGW (`0.0.0.0/0 → igw-xxx`). No IGW route = **private**. That's it. Not the name, not the IPs — the route.
- **"EC2 can't reach the internet" checklist** — all of these must be true: (1) an **IGW attached** to the VPC, (2) a **route to the IGW** in the subnet's route table, (3) a **public IP or Elastic IP** on the instance (nondefault subnets have auto-assign public IPv4 **off** by default), (4) **SG and NACL** allow the traffic. Troubleshoot in that spirit: *public IP/EIP first, then the route table*. Want `ping` to work? The SG/NACL must allow **ICMP** — ping isn't TCP, so opening port 80/22 doesn't help.
- **No IPv6-only VPC**: IPv4 is mandatory — every VPC needs an IPv4 CIDR, IPv6 is an optional add-on, and you can't remove all IPv4 CIDRs from an existing VPC.

### NAT Gateway — the outbound-only door

Private instances still need to download patches and call external APIs. Enter the **NAT Gateway** (Network Address Translation). Picture a **receptionist who mails letters for everyone in the building**: she takes your letter, **swaps the return address for the building's front-desk address**, and **remembers who asked** — so when the reply comes back, she hands it to the right person. But a stranger can't walk up and mail a letter *IN* to you; if nobody inside asked for it, she bins it.

That's NAT: **private instances can initiate outbound to the internet; the internet can never initiate inbound.**

Lock in these facts:

- The NAT Gateway **lives IN a public subnet** — it needs the IGW route itself to reach the internet. Private subnets then route `0.0.0.0/0 → nat-xxx`.
- A NAT Gateway is **per-AZ**. THE trap: one NAT Gateway shared by all AZs = a hidden single point of failure — if its AZ dies, every private subnet loses internet. *"Make NAT highly available"* → **one NAT Gateway per AZ**, each private subnet routing to its local one.
- NAT Gateway is **managed, scales automatically (up to ~45–100 Gbps), no security groups on it**, pay per hour + per GB. It's **redundant inside its AZ** (AWS handles hardware failure within the AZ — the AZ itself is still the failure domain) and supports up to **55,000 simultaneous connections to each unique destination**.
- NAT is a dumb pipe: it **cannot inspect domains/FQDNs or block malicious URLs**. *"Allow outbound only to approved domains"* → **AWS Network Firewall** (see Observability below).
- **NAT Instance** = the legacy DIY version: an EC2 instance doing NAT. It CAN have a security group, supports **port forwarding**, can double as a **bastion host**, but doesn't scale on its own — you manage/patch/size it yourself, and — THE NAT-instance answer — you must **disable the source/destination check** on it (EC2 normally drops traffic not addressed to itself; a NAT forwards other people's traffic, so the check must go).
- IPv6 has no NAT (every IPv6 address is public). The IPv6 equivalent of "outbound-only" is the **egress-only Internet Gateway**. *"IPv6 instances need outbound internet but no inbound"* → egress-only IGW.

## CIDR essentials

CIDR (Classless Inter-Domain Routing) notation like `10.0.0.0/16` means "the first 16 bits are fixed; the rest are yours" — /16 ≈ 65,536 addresses, /24 = 256.

- VPC CIDR can be **/16 (largest) to /28 (smallest)**.
- **AWS reserves 5 IP addresses in every subnet** (network, router, DNS, future, broadcast) — a /24 gives you 251 usable, not 256.
- **No-overlap rule**: VPCs you want to connect (peering, TGW, VPN to on-prem) must have **non-overlapping CIDRs**. Plan ranges up front; you can't peer 10.0.0.0/16 with 10.0.0.0/16.

## The two guards: Security Groups vs NACLs

Two firewalls, different posts, different memories:

| | Security Group (SG) | Network ACL (NACL) |
|---|---|---|
| Guards | The **instance** (its network interface) | The **subnet** boundary |
| State | **STATEFUL** — remembers | **STATELESS** — no memory |
| Rules | **Allow only** (default deny) | Allow **and DENY** |
| Order | All rules evaluated together | **Numbered**, lowest first, first match wins |
| Can reference | **Other SGs** | Only CIDR blocks |

- **Stateful** = a receptionist **with memory**: if she let your request out, she automatically lets the reply back in. With SGs you never write a rule for return traffic.
- **Stateless** = a gate guard with **no memory**: he checked the outgoing request, but the reply is a brand-new stranger to him — it needs its **own explicit rule**. Replies come back on **ephemeral ports (1024–65535)**, so NACLs need an outbound (and inbound, for the reverse direction) allow for that range. THE trap: *"requests go out but responses never return"* → **NACL is missing the ephemeral-port outbound rule**.
  - The **client's OS picks** the ephemeral range: **Linux 32768–61000**; **Windows Server 2008+ 49152–65535**; Windows Server 2003 1025–5000; **ELB, NAT Gateway and Lambda 1024–65535** — which is why "allow 1024–65535" is the safe NACL answer.
  - Worked example — *SSH from your home IP to an instance*: SG needs **inbound 22** only (stateful); the NACL needs **inbound 22 AND outbound ephemeral ports** back to your IP. (RDP is the same story on **3389**.)
- Neither guard reads HTTP payloads: SGs, NACLs (and Route 53) **cannot stop SQL injection or XSS** — that's **WAF**.
- **SG referencing**: instead of IPs, an SG rule can say "allow port 3306 **from the app-tier's security group**." *"Only app servers may reach the database"* → **DB SG allows inbound from the app SG** — elegant, survives IP changes.
- SGs **cannot deny**. THE trap: *"block traffic from a specific malicious IP"* → **NACL DENY rule** (a SG physically has no deny button).

## VPC Endpoints — private hallways to AWS services

Normally, a private instance calling S3 would go out through NAT → internet → S3. Wasteful and exposed. VPC Endpoints let you reach AWS services **without leaving the AWS network**:

| | Gateway Endpoint | Interface Endpoint (PrivateLink) |
|---|---|---|
| Services | **S3 and DynamoDB ONLY** | Nearly **any** AWS service (+ SaaS) |
| Cost | **FREE** | Paid (per hour + per GB) |
| How | A **route-table entry** | An **ENI** (private network card) in your subnet |
| Reach | **VPC-local only** — NOT usable from peered VPCs or on-prem | **IS reachable** over peering / Transit Gateway / VPN |

- *"Private EC2 needs to reach S3, cheapest / most secure way"* → **Gateway Endpoint**, NOT a NAT Gateway. (NAT charges per GB; Gateway Endpoints are free.) This question is practically guaranteed.
- Because Interface Endpoints work across peering/TGW/VPN, the **centralized endpoints pattern** puts them in one shared VPC for many VPCs to use. And yes — an **S3 *interface* endpoint exists** specifically for the *"on-premises servers need private S3 access"* case, since the Gateway one can't be reached from on-prem.
- Gateway endpoint setup = create it **and associate it with the VPC route table** (*"keep DynamoDB traffic off the public internet"* → DynamoDB gateway endpoint + route-table association). Everything else — **SQS, SNS, Kinesis, Secrets Manager, SSM, KMS…** — uses an **interface** endpoint.
- An interface endpoint is literally an **ENI with a private IP from your subnet**.
- **Endpoint policies** are a second lock alongside bucket policies: one endpoint policy can restrict *which* S3 buckets the VPC may reach, while the bucket policy (`aws:sourceVpce`) restricts *who* may reach the bucket.
- Endpoints are **regional** (no inter-region endpoint), connect you to **AWS services — not to other VPCs**, and **can't be created in Wavelength Zones**.

## Connecting VPCs: three very different tools

### VPC Peering — a 1:1 cable

A direct private link between exactly two VPCs (cross-account and cross-region work fine).

- **NOT transitive**: A↔B and B↔C does NOT give A↔C. Every pair needs its own peering + route-table entries.
- **No CIDR overlap allowed.**
- **Inter-region peering** works — a private connection between VPCs in different Regions over the AWS backbone. (An NLB can even register **IP targets** in a peered VPC across Regions.)
- **No edge-to-edge routing**: a peered VPC **can't borrow the other VPC's "edges"** — its Site-to-Site VPN / Direct Connect to on-prem, its IGW, its NAT device, or its gateway endpoint. Picture it:

  ```
  VPC B 10.0.0.0/16 ──peering── VPC A 172.16.0.0/16 ──VPN or DX── Corporate network
          └──────────────── ✗ B cannot reach corporate through A ────────────┘
  ```

  So peering is **never the answer for on-prem connectivity**; B needs its own VPN/DX, or put everything behind a **Transit Gateway**.
- Cheap (free to create; you pay data transfer). Great for **2–3 VPCs**.
- The mesh math kills it: full mesh of n VPCs = **n(n−1)/2** connections. **10 VPCs = 45 peerings.** 25 VPCs = 300. Nobody manages that → …

### Transit Gateway (TGW) — the hub

A regional **hub-and-spoke router**: attach VPCs, **Site-to-Site VPNs, and Direct Connect**, and everything can talk **transitively** through the hub — one attachment per VPC instead of a mesh.

- Share it **cross-account with AWS RAM** (Resource Access Manager).
- **Peer TGWs across regions** for a global network.
- The **only AWS service supporting multicast**.
- **Per-attachment route tables** let you segment: e.g., prod VPCs can't reach dev VPCs even though both hang off the hub.
- Keyword: *"many VPCs (and/or on-prem) need to communicate, minimal management"* → **Transit Gateway**. "Many" starts around 4+; at 25 it's not even a question.

### PrivateLink — a service window, not a network marriage

Peering/TGW **merge networks** — everything can reach everything. PrivateLink instead opens **one service window**: the provider puts an **NLB** in front of their app and creates an **endpoint service**; consumers create an **interface endpoint** in their own VPC and reach *that one service, one-direction, and nothing else*.

- **Overlapping CIDRs are fine** (no routing between networks — it's just an ENI).
- Scales to **thousands of consumer VPCs** without route-table sprawl.
- Keywords: *"SaaS provider exposes a service to many customer VPCs"*, *"partner must access ONE API only, not our whole network"* → **PrivateLink**.

Quick chooser: **2–3 VPCs, full network access → Peering. Many VPCs + VPN/DX, transitive → TGW. Expose one service, no network merge, CIDRs overlap → PrivateLink.**

## Observability & admin access

- **VPC Flow Logs** capture traffic **metadata** — source/destination IP, port, protocol, **ACCEPT or REJECT** — to CloudWatch Logs or S3. Not packet contents. Use for *"why is this connection failing?"* (look for REJECTs → an SG/NACL is blocking) and security analysis. Need the **full packets**? That's **Traffic Mirroring** (copies inbound/outbound packets from an instance's ENI to another instance's ENI, an **NLB with a UDP listener**, or a **Gateway Load Balancer with a UDP listener**). Memory hook: *network traffic? → Flow Logs; application logs? → CloudWatch Logs.*
- **AWS Network Firewall** = the inline, **stateful** VPC firewall with **deep packet inspection** (Suricata-based IPS): filters traffic through the IGW, NAT GW, VPN or DX, does **FQDN/domain allow- and deny-lists**, and detects protocols like HTTPS regardless of port. It's deployed at the **VPC level (not per subnet)**, can't attach directly to an ALB, and can't by itself restrict S3 bucket access to one VPC (that's an endpoint + bucket policy). Full coverage in Section 22.
- **Network Access Analyzer** only **reports** unintended network access paths against your compliance rules — **no packet inspection, no blocking**.
- **Bastion host** = a DIY **EC2 jump box in a public subnet**: you SSH to it, then hop to private instances. You build, patch, and guard it. The SG chain: bastion's SG allows port 22 **from your corporate IP only**; private instances' SG allows 22 **from the bastion's SG**.
- **SSM Session Manager** = the modern answer: shell access through the Systems Manager agent — **no open port 22, no public IP, no bastion, every session logged** (CloudTrail/S3). THE tie-breaker: *"MOST secure way to administer private instances"* → **Session Manager**, not a bastion.
- **VPC Sharing (via RAM)**: one account owns the VPC, other accounts launch resources into its subnets — **many accounts, one network**, no peering needed. *"Central network team, application accounts deploy into shared subnets"* → VPC sharing. Precisely: the owner shares **subnets** (not the VPC object) with participant accounts **in the same AWS Organization**. RAM also shares **Transit Gateways, Route 53 Resolver rules and License Manager configurations**.
- **Legacy, for recognition only**: the old **VPC wizard** offered four layouts — single public subnet; public + private (NAT); public + private + hardware VPN; private-only + hardware VPN (there was **no "public-only + VPN"** option). **ClassicLink** linked pre-VPC **EC2-Classic** instances to a VPC; EC2-Classic is retired.

## Question patterns

> *"Block all traffic from a specific IP address"* → **NACL deny rule** (security groups can't deny)

> *"Only the app tier may connect to the database"* → **DB security group allows inbound from the app tier's SG** (SG-to-SG reference)

> *"Private EC2 must access S3 privately at the lowest cost"* → **Gateway VPC Endpoint** (free — NAT Gateway is the expensive decoy)

> *"25 VPCs plus on-premises via VPN must all communicate"* → **Transit Gateway** (peering mesh = 300 connections; TGW is the hub)

> *"Expose one application to a partner VPC; CIDR ranges overlap"* → **PrivateLink** (NLB + endpoint service; overlap doesn't matter)

> *"Single NAT Gateway — make the design highly available"* → **One NAT Gateway per AZ**, each private subnet routing to its local one

> *"Private instances need to download OS updates"* → **NAT Gateway in the public subnet** + private route `0.0.0.0/0 → NAT`

> *"Most secure way for admins to access private instances"* → **SSM Session Manager** (no port 22, no bastion, fully logged)

> *"Determine why traffic to an instance is being rejected"* → **VPC Flow Logs** (metadata shows ACCEPT/REJECT; full packets = Traffic Mirroring)

> *"IPv6-only instances need outbound internet, no inbound"* → **Egress-only Internet Gateway** (IPv6's "NAT")

> *"NAT instance stopped forwarding traffic"* → **Disable the source/destination check**

> *"Outbound requests succeed but responses never arrive"* → **NACL missing outbound ephemeral-port (1024–65535) rule** (stateless!)

> *"New EC2 in a public subnet can't be reached from the internet"* → **check public IP/EIP first, then the IGW route** (nondefault subnets don't auto-assign public IPs)

> *"Instance is reachable on HTTP but ping fails"* → **allow ICMP** in the SG/NACL

> *"VPC B is peered with VPC A, which has a VPN to on-prem; B can't reach on-prem"* → **expected — no edge-to-edge routing**; give B its own VPN/DX or use a **Transit Gateway**

> *"Restrict private instances' outbound traffic to approved domains only"* → **AWS Network Firewall** (NAT Gateway can't filter FQDNs)

> *"Create an IPv6-only VPC"* → **not possible** — an IPv4 CIDR is always required

> *"Private subnet must reach SQS/SNS/Kinesis privately"* → **Interface endpoint** (gateway endpoints are S3/DynamoDB only)

## Pocket card

| Keyword | Answer |
|---|---|
| Public subnet definition | Route to IGW |
| Outbound-only internet for private subnet | NAT Gateway (in a public subnet) |
| NAT high availability | One NAT Gateway per AZ |
| NAT instance fix | Disable source/dest check |
| IPv6 outbound-only | Egress-only IGW |
| Reserved IPs per subnet | 5 |
| VPC CIDR size | /16 to /28 |
| Block a specific IP | NACL (deny) |
| Stateful / instance-level | Security Group |
| Stateless / subnet-level / ephemeral ports | NACL |
| Tier-to-tier access control | SG referencing another SG |
| S3/DynamoDB private + free | Gateway Endpoint |
| Endpoint reachable from on-prem/peered VPC | Interface Endpoint (PrivateLink) |
| 2–3 VPCs, full access | VPC Peering (not transitive!) |
| Many VPCs + VPN/DX, transitive hub | Transit Gateway (RAM to share, only multicast) |
| One service, overlapping CIDRs, SaaS | PrivateLink (NLB + endpoint service) |
| Traffic metadata, accept/reject | Flow Logs |
| Full packet capture | Traffic Mirroring |
| Most secure admin access | SSM Session Manager |
| One network, many accounts | VPC Sharing via RAM |
| IGW's two jobs | Route target + NAT for public IPv4 |
| Ping fails | Allow ICMP |
| Linux / Windows 2008+ ephemeral ports | 32768–61000 / 49152–65535 |
| Peered VPC using the other's VPN/DX/IGW | ✗ No edge-to-edge routing |
| Peering across Regions | Inter-region VPC peering |
| Domain/FQDN egress filtering, deep packet inspection | Network Firewall (not NAT GW) |
| Report unintended access, no inspection | Network Access Analyzer |
| IPv6-only VPC | Not possible |
| Restrict which buckets the VPC can reach | VPC endpoint policy |

You now own the network — next up are the roads leading into it from the outside world: Route 53, Direct Connect, and Site-to-Site VPN, plus the load balancers from Section 5 that stand at its public doors.
