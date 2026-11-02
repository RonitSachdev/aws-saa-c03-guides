# Section 33: Transit Gateway

## The idea

Remember VPC peering? It connects exactly **two** VPCs — a **1:1 cable** between two buildings. And it's **non-transitive**: if A peers with B and B peers with C, A still *cannot* reach C. Every pair needs its own cable.

Now do the math. Full connectivity between n VPCs needs **n(n-1)/2** peering connections. **10 VPCs = 45 peerings.** 25 VPCs = 300. Add on-premises links and you have a plate of spaghetti nobody can debug.

**Transit Gateway (TGW)** is the **airport hub**. Instead of every city flying direct to every other city, everyone flies through the hub. Each VPC, VPN, or Direct Connect link gets **one attachment** to the TGW, and the hub routes between all of them — a **star topology** with **transitive routing** (A can reach C through the hub, no direct cable needed).

## What you can attach

| Attachment | Note |
|---|---|
| **VPCs** | Thousands, one attachment each |
| **Site-to-Site VPN** | On-prem via internet |
| **Direct Connect** | Via a **transit VIF** |
| **Another TGW** | **TGW peering** for cross-region hubs |

- **Cross-account sharing**: share a TGW with other AWS accounts using **AWS RAM** (Resource Access Manager) — one hub for the whole organization.
- **Route tables per attachment = segmentation.** Give prod and dev different TGW route tables and **prod can't see dev**, even though both hang off the same hub. This is how you isolate environments while still routing everyone to on-premises.
- **THE trap: TGW is the ONLY AWS service that supports IP multicast.** See the word "multicast" → answer is Transit Gateway, done.
- **Appliance mode**: keeps both directions of a traffic flow going through the *same* network appliance (firewall/inspection VPC) — the keyword for centralized traffic inspection.

### Transit VPC — the legacy DIY hub

Before TGW, the pattern was a **transit VPC**: a hub VPC running **VPN appliances on EC2** that you build, patch and scale yourself, with spoke VPCs and data centers VPN-ing into it (it could span Regions). TGW is the **managed replacement** — one connection per VPC, on-prem network or remote office. If an option says "transit VPC", treat it as the **more-operational-overhead** distractor.

**The connectivity chooser** (where hubs fit):

| Need | Answer |
|---|---|
| Two VPCs, simple | VPC Peering (incl. inter-region) |
| Many VPCs/accounts/Regions + on-prem, transitive | **Transit Gateway** (+ DX via transit VIF for cost/bandwidth) |
| Branch offices talking to each other over VPN | VPN CloudHub (Section 32) |
| Legacy self-managed hub | Transit VPC |

## Cost reality check

TGW charges **per attachment per hour + per GB processed**. VPC peering has **no hourly charge** (just data transfer). So:

- **2–3 VPCs** that just need to talk → **peering is still the right answer** (cheaper, simpler).
- **Many VPCs, on-prem connectivity, transitive routing** → TGW earns its keep.

## TGW vs PrivateLink (quick recap)

- **TGW / peering = network marriage**: the whole networks join; everything routable can talk.
- **PrivateLink = service window**: expose ONE service through a small hatch; consumer sees only that endpoint, nothing else. "Expose one service to 100 customer VPCs, no network merge, overlapping CIDRs fine" → PrivateLink, not TGW.

## Question patterns

> *"25 VPCs and on-premises datacenter need centralized connectivity"* → **Transit Gateway** (hub-and-spoke kills the n(n-1)/2 mesh)

> *"VPC A peers with B, B peers with C, but A can't reach C"* → **Transit Gateway** (peering is non-transitive; TGW routes transitively)

> *"Prod VPCs must not communicate with dev VPCs, but all need on-prem access"* → **TGW with separate route tables per attachment** (segmentation at the hub)

> *"Application requires IP multicast"* → **Transit Gateway** (the only service that supports it)

> *"Just 2 VPCs need to communicate at lowest cost"* → **VPC peering** (free hourly, TGW would be overkill)

> *"Share the network hub across 50 AWS accounts"* → **TGW shared via AWS RAM**

> *"Connect hub networks in us-east-1 and eu-west-1"* → **TGW peering** (cross-region hub-to-hub)

> *"Replace a transit VPC of EC2 VPN appliances with less operational overhead"* → **Transit Gateway**

> *"All inter-VPC traffic must pass through a firewall appliance"* → **TGW with appliance mode** (symmetric flows through the inspection VPC)

## Pocket card

| Keyword | Answer |
|---|---|
| Many VPCs + on-prem, central hub | Transit Gateway |
| Transitive routing | Transit Gateway (peering can't) |
| n(n-1)/2 peering explosion | Transit Gateway |
| Multicast | Transit Gateway (only one) |
| Isolate prod/dev at the hub | TGW route tables |
| Cross-account TGW | Share via AWS RAM |
| Cross-region hubs | TGW peering |
| DX into TGW | Transit VIF |
| Only 2–3 VPCs, cheapest | VPC peering |
| Expose one service, no network merge | PrivateLink (not TGW) |
| Self-managed EC2 VPN hub (legacy) | Transit VPC → replace with TGW |
| Branch office ↔ branch office over VPN | VPN CloudHub (not TGW) |

That's the plumbing done — next we zoom all the way out to how AWS wants you to *think* about architecture: the Well-Architected Framework.
