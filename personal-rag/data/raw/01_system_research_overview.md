# System Research Overview

作者：Edison Lin
類型：個人研究筆記
主題：系統研究與新興儲存裝置的關聯

系統研究的核心不是單點最佳化，而是在真實限制下協調硬體、軟體與工作負載。對儲存系統而言，問題通常來自整體資料路徑，而不是單一元件規格。例如 SSD 明明很快，但如果上層產生大量小寫入、metadata 更新頻繁、或背景整理與應用 I/O 互相干擾，尾延遲仍然可能很差。

這份知識庫聚焦在新興儲存裝置如何改變系統設計。重點不是列出所有裝置，而是理解裝置特性如何向上影響檔案系統、KV store、索引結構、資料放置策略與效能評估方法。這也是之後 paper collection 的核心篩選原則。

當研究對象從傳統 block device 延伸到 zoned storage、NVM、computational storage 或更細緻的 FTL-aware 設計時，研究問題通常會變成跨層問題。好的 RAG 系統應該能回答的不只是定義題，而是 trade-off、方法論、評估指標與研究脈絡。
