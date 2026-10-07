# ZNS: Avoiding the Block Interface Tax for Flash-based SSDs

- Year: 2021
- Venue: ATC 2021
- Research focus: zoned storage interface
- Status: first-pass summary

## Problem
- The traditional block interface hides flash erase-block behavior at substantial cost.
- Supporting arbitrary overwrite semantics forces SSDs to spend capacity on over-provisioning, DRAM on mapping tables, and effort on garbage collection.
- Host software also ends up fighting device behavior indirectly without explicit control.

## Key Idea
- ZNS groups logical blocks into zones that can be read randomly but written sequentially and reset between rewrites.
- The interface exposes more of the media-management structure to host software while leaving reliability management inside the device.
- This removes much of the block-interface tax and enables host software to specialize layout and write policy.

## Device / Media Assumption
- Flash-based SSDs where erase-block boundaries and write-ordering constraints matter.
- Assumes the host is willing to take on more responsibility in exchange for efficiency and predictability.

## Software Layer
- Storage interface design between SSD and host.
- Modified host software such as F2FS and RocksDB to exploit zoned semantics.

## Workload and Evaluation
- Multi-threaded overwrite experiments on identical hardware exposed as block SSD versus ZNS SSD.
- Zone-specialized F2FS and RocksDB.
- Focus on throughput, tail latency, and interface-level efficiency.

## Metrics
- Throughput.
- 99.9th-percentile random-read latency.
- Effective over-provisioning and resource overhead reduction.

## Strengths
- One of the clearest papers showing how a new interface can shift work across the host-device boundary.
- Strong fit with both file systems and KV stores.
- Makes device-aware design much more concrete than prior flash-aware tuning alone.

## Limitations
- Requires substantial host software changes and new operational discipline.
- Benefits depend on applications and file systems being rewritten or adapted for zones.
- Sequential-write constraints may complicate adoption for legacy software.

## Relation to My Topic
- This is one of the most central papers for my project.
- It directly embodies cross-layer storage-system design and the trade-off between abstraction and control.
- It also connects my flash/FTL notes with newer device-aware file-system and RocksDB directions.

## Memorable Quotes or Claims
- Reports 2x higher write throughput and 2x to 4x lower 99.9th-percentile random-read latency for the specialized RocksDB setup.
- Frames the problem as avoiding the block-interface tax.

## Follow-up Questions
- Which classes of applications benefit most from ZNS, and which remain awkward to port?
- How much host complexity is acceptable before the interface becomes too burdensome?
- What abstractions should sit above ZNS so more applications can benefit without custom rewrites?
