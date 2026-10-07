# Storage Hierarchy

作者：Edison Lin
類型：個人研究筆記
主題：記憶體階層與儲存路徑

記憶體與儲存階層反映的是速度、容量、成本與持久性的交換。從 CPU cache、DRAM、SSD、HDD 到 cold storage，每一層都在承擔不同的角色。系統設計若忽略資料在層級之間移動的成本，就容易在 AI pipeline、database engine 或 checkpoint 流程中遇到瓶頸。

對儲存系統研究者來說，重點不是背誦每層媒介，而是理解資料路徑上的每一層決策如何互相作用。Page cache、block layer、I/O scheduler、device firmware 與介質限制會共同決定可見效能。這也是為什麼 storage-aware 與 device-aware 優化經常需要跨層觀察。

當新介質出現，例如 latency 更低的 NVM 或規則更顯式的 zoned storage，原本合理的抽象不一定繼續成立。這時候研究焦點就會從單純使用裝置，轉向重新設計上層軟體與介面。
