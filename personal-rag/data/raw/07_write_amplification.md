# Write Amplification

作者：Edison Lin
類型：個人研究筆記
主題：Write Amplification 與其來源

Write Amplification 是理解 SSD 行為的核心指標。當邏輯上只寫入一次資料，但裝置因為搬移有效頁面、維護映射或清理空間而進行更多實體寫入時，就會出現 WA。WA 上升代表的不只是壽命損耗，也通常意味著更高的背景負擔與更不穩定的延遲。

造成 WA 的來源可能來自碎片化更新、空間壓力、壞掉的資料佈局、metadata 與 data 混雜、或與 FTL 回收策略不相容的寫入模式。很多 flash-aware 研究其實都可被重述成降低不必要搬移與隔離不同生命週期資料。

因此在做 device-aware 設計時，研究者應把 WA 視為跨層指標，而不是只把問題丟給裝置內部。若 host 能提供更好的放置 hint，很多 background cost 就有機會下降。
