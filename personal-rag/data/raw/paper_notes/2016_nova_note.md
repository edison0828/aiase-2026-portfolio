# NOVA: A Log-structured File System for Hybrid Volatile/Non-volatile Main Memories

- Year: 2016
- Venue: FAST 2016
- Research focus: persistent memory filesystem
- Status: first-pass summary

## Problem
- Existing disk-oriented file systems introduce software overheads that hide the performance benefits of persistent memory.
- Several early NVM file systems either keep too much legacy overhead or weaken consistency guarantees too much for real applications.

## Key Idea
- NOVA is a log-structured file system for hybrid DRAM + non-volatile main memory systems.
- It maintains separate logs for each inode to improve concurrency.
- File data is stored outside the log, keeping logs compact while still providing strong metadata and data consistency properties.

## Device / Media Assumption
- Byte-addressable non-volatile memory on the memory bus, paired with conventional DRAM.
- PM/NVM is fast enough that traditional disk-path software overhead becomes a dominant bottleneck.

## Software Layer
- File system for hybrid volatile/non-volatile main memory.
- Metadata logging, recovery, and DRAM-assisted indexing/lookups.

## Workload and Evaluation
- Write-intensive workloads and comparisons against state-of-the-art file systems.
- Also compares against systems with similarly strong consistency guarantees.
- Focuses on concurrency and consistent persistence semantics.

## Metrics
- Throughput improvement.
- Consistency guarantee strength.
- Overhead relative to other PM-aware and disk-oriented file systems.

## Strengths
- Very influential baseline for PM file systems.
- Strong combination of performance and consistency rather than choosing only one.
- Per-inode logs are a clean way to reduce contention.

## Limitations
- Keeps some metadata structures in DRAM, so lookup acceleration comes with recovery/rebuild trade-offs.
- Tailored to PM/NVM rather than general block storage.
- Later PMFS work explores more aggressive userspace or hardware-assisted designs.

## Relation to My Topic
- NOVA anchors the NVM-aware branch of my topic.
- It shows how a new medium can force a redesign of file-system data paths and consistency mechanisms.
- It also serves as an important baseline for papers like MadFS and ctFS.

## Memorable Quotes or Claims
- Reports 22% to 216x throughput improvement on write-intensive workloads over compared file systems.
- Emphasizes strong consistency without falling back to disk-era overhead.

## Follow-up Questions
- Which NOVA design ideas remain essential in newer PMFS work?
- How costly is the DRAM metadata dependence during recovery or crash handling?
- How should NOVA-like ideas interact with application-level libraries or userspace file systems?
