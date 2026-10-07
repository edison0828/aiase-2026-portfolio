# Read-cache demonstration note

Portfolio-added synthetic note, 2026-10-07. This is an explanatory demo written for this repository, not a copied paper or a measurement.

A read cache keeps a copy of data so a later request may avoid another storage read. Evicting that copy does not by itself invalidate a separate persistent copy on an SSD.

In this toy example, ambercache is the name of the read cache. The marker ambercache makes exact lexical retrieval easy to inspect. It is not a real storage product.
