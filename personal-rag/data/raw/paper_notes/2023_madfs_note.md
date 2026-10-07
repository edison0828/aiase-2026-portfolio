# MadFS: Per-File Virtualization for Userspace Persistent Memory Filesystems

- Year: 2023
- Venue: FAST 2023
- Research focus: userspace PMFS
- Status: first-pass summary

## Problem
- Persistent memory can be accessed from userspace directly, but many PM file systems still keep metadata management and synchronization in the kernel.
- Kernel involvement and crash-safe cross-process coordination remain significant overheads.

## Key Idea
- MadFS uses per-file virtualization to move a complete set of file functionalities into userspace.
- It embeds insensitive metadata into the file itself, uses copy-on-write-friendly metadata organization, and introduces user-level lock-free optimistic concurrency control.
- The design tries to reduce both kernel crossings and synchronization bottlenecks.

## Device / Media Assumption
- Persistent memory directly accessible from userspace with near-DRAM performance.
- The medium is fast enough that kernel boundary and metadata synchronization overheads dominate.

## Software Layer
- Userspace persistent-memory file system library.
- Metadata management, crash consistency, and concurrency control.

## Workload and Evaluation
- Concurrent workloads.
- Real applications including YCSB on LevelDB and TPC-C on SQLite.
- Compared against ext4-DAX and NOVA.

## Metrics
- Throughput under concurrency.
- Application-level speedup.
- Scalability of synchronization/control path.

## Strengths
- Pushes PMFS design further into userspace while still taking integrity and concurrency seriously.
- Good example of how metadata placement decisions affect performance.
- Strong real-application evaluation makes it relevant beyond microbenchmarks.

## Limitations
- More complex trust and integrity model because more logic moves to userspace.
- Per-file virtualization may complicate some cross-file operations or global policies.
- PMFS-specific assumptions may limit transferability to slower block devices.

## Relation to My Topic
- MadFS fits my topic because it treats software overhead, not just device latency, as the core optimization target.
- It is a good follow-up to NOVA and ctFS in the PM-aware file-system line.
- It also reinforces my interest in metadata placement, concurrency control, and user/kernel boundary design.

## Memorable Quotes or Claims
- Reports up to 3.6x throughput of ext4-DAX on concurrent workloads.
- Reports up to 48% speedup for YCSB on LevelDB and 85% for TPC-C on SQLite versus NOVA.

## Follow-up Questions
- Which metadata really must remain in the kernel, and which can safely move to userspace?
- How robust is the optimistic concurrency model under contention and crash-heavy scenarios?
- Can similar per-file virtualization ideas help non-PM storage paths too?
