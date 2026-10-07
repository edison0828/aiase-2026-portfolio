# Design Space

作者：Edison Lin
類型：個人研究筆記
主題：設計空間與系統取捨

設計空間是系統研究最重要的思考框架之一。當我們設計儲存系統時，通常有多個可行方案，每個方案會在成本、吞吐量、延遲、開發複雜度與相容性之間做不同平衡。研究價值往往來自清楚描述這些 trade-off，而不是只展示某個 benchmark 上的單一最好結果。

在新興儲存裝置情境裡，設計空間通常還會受到介質限制影響，例如 write granularity、erase unit、wear leveling、zone append 規則、或 persistent memory 的 crash consistency 要求。這些硬體條件會決定哪些抽象合理、哪些資料結構需要重設、哪些 background tasks 會成為 bottleneck。

閱讀論文時應優先問三件事：目標 workload 是什麼、作者優化哪個指標、以及代價轉移到了哪一層。如果這三件事說不清楚，系統貢獻通常也不夠紮實。
