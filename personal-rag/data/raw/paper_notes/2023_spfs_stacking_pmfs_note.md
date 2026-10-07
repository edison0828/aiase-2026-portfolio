# On Stacking a Persistent Memory File System on Legacy File Systems

- Year: 2023
- Venue: FAST 2023
- Research focus: stacked PMFS deployment
- Status: first-pass summary

## Problem
- PM-aware file systems can deliver good performance, but replacing the entire legacy storage stack is operationally expensive.
- There is value in an incremental path that can accelerate synchronous writes using NVMM without discarding mature lower file systems.

## Key Idea
- SPFS is a stackable persistent-memory file system that uses NVMM as a persistent writeback cache for NVMM-oblivious lower file systems.
- It is intentionally lightweight, managing NVMM only while relying on the underlying file system and VFS cache for the rest.
- The paper introduces dynamic hash-table-based metadata and an extent hashing approach to keep the stackable layer efficient.

## Device / Media Assumption
- NVMM available above a lower legacy file system.
- The medium is valuable enough as a cache/persistent layer even if the full stack is not redesigned for PM.

## Software Layer
- Stackable file-system layer above a lower disk-oriented file system.
- Metadata and extent management for an NVMM-backed persistent cache path.

## Workload and Evaluation
- Focus on order-preserving small synchronous writes where NVMM can absorb latency.
- Evaluates performance improvement of lower file systems when SPFS is layered on top.

## Metrics
- I/O performance improvement.
- Efficiency of metadata and extent management.
- Benefit for synchronous-write-heavy workloads.

## Strengths
- Pragmatic adoption path instead of requiring a full replacement file system.
- Interesting design point between pure legacy compatibility and fully PM-native redesign.
- Extent hashing is a concrete systems contribution, not just an engineering wrapper.

## Limitations
- The extra layer itself can introduce complexity and may not help all workloads equally.
- Benefit is strongest when synchronous writes dominate.
- It is still a compromise architecture rather than a full redesign around PM semantics.

## Relation to My Topic
- This paper matters because my topic is not only about ideal new systems but also about migration paths.
- It shows one way to bridge emerging storage media with existing software stacks.
- It pairs well with P2CACHE as an evolutionary design rather than a clean-slate one.

## Memorable Quotes or Claims
- Reports up to 9.9x I/O performance improvement for the lower file system in the evaluated setting.
- Uses NVMM as a persistent writeback cache rather than demanding a complete PM-native stack.

## Follow-up Questions
- Which workloads benefit enough from a stackable design to justify the extra complexity?
- How should cache persistence and lower-file-system consistency be coordinated?
- How does SPFS compare against tiered-cache approaches like P2CACHE under similar workloads?
