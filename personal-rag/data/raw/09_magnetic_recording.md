# Magnetic Recording

作者：Edison Lin
類型：個人研究筆記
主題：為什麼磁碟仍值得研究

即使 SSD 已經成為主流，高容量、低成本與冷資料場景仍讓磁碟保有重要位置。從研究角度看，磁碟特別有價值的地方在於它清楚展示介質限制如何推動軟體設計。當面積密度逼近限制，裝置與 host 之間的管理責任也會改變。

現代資料中心裡，HDD 仍大量用於冷資料、備份與成本敏感場景。這代表研究者不應把 storage systems 等同於 SSD systems。很多資料放置、分層與可預測性問題在磁碟世界仍然存在，只是 trade-off 不同。

因此理解磁碟不只是歷史補充，而是幫助我們建立更完整的 storage design intuition，尤其是在 heterogeneous storage hierarchy 的情境下。
