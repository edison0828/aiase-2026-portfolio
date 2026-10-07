# P2CACHE: Exploring Tiered Memory for In-Kernel File Systems Caching

- Year: 2023
- Venue: ATC 2023
- Research focus: tiered memory caching
- Status: first-pass summary

## Problem
- Legacy kernel file systems are difficult to retrofit cleanly for fast byte-addressable persistent memory.
- PM-specific file systems are not yet mature enough for universal adoption, leaving a gap between hardware capability and practical deployment.

## Key Idea
- P2CACHE introduces an in-kernel caching mechanism for a tiered DRAM + PM memory system.
- It uses PM to serve writes for immediate durability and strong crash consistency, while DRAM serves most reads for high performance.
- The design is an evolutionary path for legacy kernel file systems rather than a clean-slate PMFS.

## Device / Media Assumption
- Tiered memory system with both persistent memory and DRAM.
- PM is fast and byte-addressable but not an automatic drop-in replacement for existing block-oriented file-system assumptions.

## Software Layer
- In-kernel caching path for legacy file systems.
- Synchronization between DRAM and PM.

## Workload and Evaluation
- Legacy file systems under PM-aware caching.
- Realistic workloads including RocksDB on Ext4 in the paper's evaluation.
- Emphasis on both performance and crash-consistency benefits.

## Metrics
- Throughput and end-to-end performance.
- Crash-consistency and durability characteristics.
- Comparison against baseline legacy file-system behavior.

## Strengths
- Practical migration strategy for existing kernel file systems.
- Clean articulation of read/write asymmetry across DRAM and PM.
- Makes PM adoption possible without demanding immediate replacement of the full file-system stack.

## Limitations
- Adds kernel complexity and cache-management policy burden.
- Benefits depend on the specific PM/DRAM hierarchy and workload shape.
- It does not eliminate every legacy-file-system assumption; it works around them.

## Relation to My Topic
- P2CACHE is useful because it shows an incremental, system-level response to emerging memory/storage media.
- It fits my theme of cross-layer co-design and practical adoption paths.
- It also complements SPFS by showing a different way to combine PM with legacy software.

## Memorable Quotes or Claims
- Reports dramatic gains, including roughly 200x for RocksDB on Ext4 in the evaluated setup.
- Seeks PM-like durability and crash consistency without requiring a fully PM-native file system.

## Follow-up Questions
- Which workloads benefit most from putting writes on PM and reads on DRAM?
- How does P2CACHE interact with existing page-cache and journaling behavior?
- Could a similar tiered design be applied to SSD/NVM or zoned-device hierarchies?
