# Daily Plan (Day 1 → Day 6 = exam eve; exam = Day 7)

Guide numbers refer to `../topic-guides/NN-*.md`.

## Day 1 — Core infrastructure (highest weight)
- **Morning:** 06 VPC (SG vs NACL, NAT per AZ, Gateway vs Interface endpoint, peering vs TGW vs PrivateLink), 01 IAM (roles, SCP vs boundary, STS)
- **Afternoon:** 02 S3 (storage classes, lifecycle, replication, encryption, Object Lock), 03 EC2 (pricing options, placement groups)
- **Evening:** 04 EBS/EFS/Instance Store, 05 ELB & Auto Scaling — pocket cards only
- **Test:** 20 practice questions on VPC + S3 + IAM

## Day 2 — Databases + caching
- **Morning:** 09 RDS/Aurora (Multi-AZ vs Read Replica = #1 question), 10 DynamoDB (DAX, GSI/LSI, Streams, Global Tables)
- **Afternoon:** 11 ElastiCache (Redis vs Memcached), 12 Other Databases (Redshift, Athena, Neptune, QLDB, DocumentDB, Keyspaces, Timestream)
- **Evening:** 26 FSx, 25 Storage Gateway / DataSync / Transfer Family, 27 Snow Family
- **Test:** 20 questions on databases + storage

## Day 3 — Decoupling, serverless, containers
- **Morning:** 17 SQS/SNS/Kinesis (heaviest single source), 18 EventBridge & Step Functions
- **Afternoon:** 13 Lambda, 16 API Gateway, 14 ECS/EKS/Fargate, 15 Elastic Beanstalk
- **Evening:** redo the Day 1 pocket cards (spaced repetition)
- **Test:** 20 questions on messaging + serverless

## Day 4 — Networking, edge, hybrid, security
- **Morning:** 07 Route 53 (routing policies, Alias vs CNAME), 08 CloudFront vs Global Accelerator, 32 Direct Connect & VPN, 33 Transit Gateway
- **Afternoon:** 20 KMS/CloudHSM, 21 Secrets Manager vs Parameter Store, 22 WAF/Shield/security services, 23 Cognito, 24 Directory Services
- **Evening:** redo Day 2 pocket cards
- **Test:** 20 questions on networking + security

## Day 5 — Management, cost, architecture, DR
- **Morning:** 19 CloudWatch/CloudTrail/Config, 28 CloudFormation, 29 Organizations/Control Tower, 30 Service Catalog/Trusted Advisor
- **Afternoon:** 31 Cost Management, 34 Well-Architected, 35 Disaster Recovery (Backup & Restore → Pilot Light → Warm Standby → Multi-site: RTO/RPO vs cost)
- **Evening:** 37 Gap-Fill Services pocket card
- **Test:** full **timed mock exam (65 q / 130 min)**; log every miss

## Day 6 — Consolidate (exam eve)
- **Morning:** review your mistakes list + mock exam wrong answers; reread [03-Top-Decision-Pairs.md](03-Top-Decision-Pairs.md)
- **Midday:** read 36 Exam Traps & Key Patterns twice; skim [02-All-Pocket-Cards.md](02-All-Pocket-Cards.md) once
- **Afternoon:** second timed mock (or 30 mixed questions) — light review only
- **Evening:** stop by early evening. Prepare ID, confirm exam time/location or online-proctor setup. Sleep.

## Exam morning (Day 7)
Re-read only: Section 36 pocket card + your mistakes list (15–20 min). Then go.
