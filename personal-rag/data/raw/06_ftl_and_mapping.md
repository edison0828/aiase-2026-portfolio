# FTL and Mapping

作者：Edison Lin
類型：個人研究筆記
主題：Flash Translation Layer 與映射管理

FTL 是 SSD 的核心。它負責把邏輯位址轉成實體位置，同時協調 garbage collection、wear leveling、bad block management 與部分容量保留策略。換句話說，SSD 不是被動媒體，而是帶有韌體與演算法的主動系統元件。

不同映射策略會影響記憶體消耗、更新成本與回收複雜度。更細粒度的映射通常帶來更好的彈性，但 metadata 成本也更高。當 workload 呈現大量小更新或短生命週期資料時，映射與回收策略之間的互動尤其重要。

理解 FTL 的價值，在於它說明為什麼 host 端的資料佈局、sync pattern 與生命周期分離策略會改變裝置行為。很多所謂的 SSD optimization，本質上都在處理 host 與 FTL 之間的協調問題。
