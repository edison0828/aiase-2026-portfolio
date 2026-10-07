# LSM and KV Stores

作者：Edison Lin
類型：個人研究筆記
主題：LSM-tree、KV store 與 compaction 取捨

LSM-tree 的強項是把寫入先聚合在記憶體，再批次 flush 成較大單位的磁碟結構。這讓寫入吞吐通常很好，也很適合 update-heavy workload。代價則是 compaction 帶來的背景 I/O、讀放大、寫放大與空間放大問題。

當底層裝置是 SSD 或更複雜的新介質時，compaction 與 device background tasks 之間可能互相干擾。於是研究者需要問的不只是 compaction policy 怎麼調，而是 compaction 與裝置特性是否匹配、何時該做分層放置、以及 tail latency 是否因此惡化。

KV store 研究因此天然適合和 storage systems 結合。index design、cache strategy、flush policy、compaction scheduling 與 persistence model 都需要一起看，不能只把裝置當成黑盒子。
