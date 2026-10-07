# Flash-Aware File Systems

作者：Edison Lin
類型：個人研究筆記
主題：Flash-aware / Device-aware 檔案系統方向

Flash-aware file system 的核心思路，是讓軟體層主動降低會放大 FTL 成本的行為。典型策略包括減少不必要小寫入、區分 metadata 與 data、依生命周期分層放置資料、以及盡量讓寫入模式更接近裝置容易處理的形式。

Device-aware 設計則更進一步，假設 host 能取得介面規則或 hint，於是 allocation policy、buffer flushing、log layout 與 recovery path 都可重新安排。這類設計的成功條件，通常是裝置限制足夠穩定且可被上層利用。

這類研究的評估不能只報 throughput，還需要看 write amplification、GC overhead、tail latency 與不同 workload 下的退化情況，否則很容易把某些 background cost 隱藏起來。
