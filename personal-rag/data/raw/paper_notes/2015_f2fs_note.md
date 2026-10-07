# F2FS: A New File System for Flash Storage

- Year: 2015
- Venue: FAST 2015
- Research focus: flash-aware file system
- Status: first-pass summary

## Problem
- Existing Linux file systems such as Ext4 were designed around HDD-era assumptions and do not align well with flash behavior.
- Mobile and SSD workloads generate many small random writes and frequent `fsync`, which can trigger internal fragmentation and unstable performance inside flash storage devices.

## Key Idea
- F2FS adopts a log-structured, append-friendly design specifically tuned for modern flash storage.
- It uses flash-conscious data structures and policies so that host-side writes are laid out in a way that is easier for the underlying device and FTL to handle.
- The paper positions F2FS as a practical Linux file system, not just a research prototype.

## Device / Media Assumption
- Modern NAND flash storage devices such as eMMC, UFS, and SSDs.
- The device still exposes a block interface through an FTL, but flash media limitations remain visible through performance degradation under certain workloads.

## Software Layer
- Linux kernel file system layer.
- File-system-level allocation, logging, and cleaning policy over block-interface flash storage.

## Workload and Evaluation
- Synthetic workloads including iozone and SQLite-heavy patterns.
- Realistic mobile and server workloads.
- Compared primarily against Ext4 on mobile systems and SSD-equipped server systems.

## Metrics
- Throughput.
- Elapsed time for realistic workloads.
- Relative speedup against Ext4 on SATA SSD and PCIe SSD platforms.

## Strengths
- Strongly grounded in real flash characteristics rather than generic log-structured arguments.
- Practical impact: F2FS became a widely deployed production file system.
- Demonstrates that file-system policy can materially improve performance even when an FTL already exists underneath.

## Limitations
- Still operates over the traditional block interface, so some device internals remain hidden from the host.
- Does not remove the fundamental block-interface tax later highlighted by ZNS work.
- Performance results are tied to the flash devices and workloads available at the time.

## Relation to My Topic
- This is a baseline paper for flash-aware software design.
- It connects directly to my interest in how file systems should adapt to flash/SSD behavior rather than treating storage as a uniform abstraction.
- It is also a useful reference point before reading ZNS, which moves even more responsibility to host software.

## Memorable Quotes or Claims
- Reports up to 3.1x improvement over Ext4 on iozone and 2x on SQLite in the evaluated mobile system.
- Shows that a flash-conscious file system can improve both mobile and server SSD workloads.

## Follow-up Questions
- Which F2FS design choices remain useful once the device exposes zoned semantics directly?
- How much of F2FS's gain comes from better host-side layout versus simply avoiding specific Ext4 behaviors?
- What happens when F2FS is combined with newer storage interfaces such as ZNS?
