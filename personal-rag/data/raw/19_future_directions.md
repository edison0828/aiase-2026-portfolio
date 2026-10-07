# Future Directions

作者：Edison Lin
類型：個人研究筆記
主題：未來值得追蹤的新興儲存系統方向

未來幾個值得持續追蹤的方向包括 storage-aware AI infrastructure、device-aware file systems、KV stores 與更好的 observability。AI 工作負載往往受制於資料搬移與 I/O pipeline，因此未來儲存系統不只要追求 throughput，還要思考資料供應穩定度、checkpoint 成本與訓練資料流。

Device-aware file systems 與 KV stores 則代表上層軟體對介質差異的理解會越來越重要。不同裝置規則若能被看見，就可以把 allocation、compaction、placement 與 durability policy 做得更貼近實際成本。

另一個重要方向是可觀測性。若無法觀察 GC、compaction、queueing 與 tail latency 之間的關係，很多最佳化都只會停留在表面。這也是未來 RAG corpus 很值得補進的文獻主題。
