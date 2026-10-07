# WiscKey: Separating Keys from Values in SSD-conscious Storage

- Year: 2016
- Venue: FAST 2016
- Research focus: SSD-conscious KV design
- Status: first-pass summary

## Problem
- Traditional LSM-tree key-value stores suffer heavy write amplification because both keys and values participate in compaction.
- As values get repeatedly rewritten during compaction, SSD bandwidth and device lifetime are wasted.

## Key Idea
- WiscKey separates keys from values.
- Keys remain in the LSM-tree for indexing, while values are appended to a separate value log.
- This keeps compaction focused mostly on keys and metadata, significantly reducing I/O amplification.

## Device / Media Assumption
- SSDs offer strong sequential write performance and good random-read performance.
- The design explicitly assumes SSD behavior is different enough from HDDs that value-log indirection is worthwhile.

## Software Layer
- Persistent key-value store / LSM-tree engine.
- Storage engine layout and compaction policy rather than file-system policy.

## Workload and Evaluation
- Microbenchmarks for load and random lookup.
- YCSB workloads.
- Compared against LevelDB and RocksDB-style baselines.

## Metrics
- Database load time.
- Random lookup performance.
- Throughput across multiple YCSB workload mixes.
- I/O amplification reduction.

## Strengths
- Very clean cross-layer idea: use SSD-friendly random reads to avoid rewriting large values.
- Addresses write amplification at the data-layout level instead of only tuning compaction parameters.
- Highly relevant to real KV-store deployments.

## Limitations
- Introduces value-log garbage collection and additional complexity for range scans or value maintenance.
- Benefit depends on SSD random-read performance being sufficiently strong.
- Separation may complicate recovery and fragmentation management.

## Relation to My Topic
- This paper is central to my theme of storage-aware data structures.
- It shows how device characteristics can reshape KV-store layout decisions.
- It also connects directly to my interest in LSM-tree trade-offs, write amplification, and host-side layout control.

## Memorable Quotes or Claims
- Reports 2.5x to 111x faster database loading and 1.6x to 14x faster random lookups than LevelDB on the evaluated setup.
- The main contribution is reducing I/O amplification by separating keys from values.

## Follow-up Questions
- How should value-log garbage collection be coordinated with SSD internal behavior?
- Would a ZNS-aware variant of WiscKey further reduce amplification and tail latency?
- What is the trade-off between lower compaction cost and more complicated value management?
