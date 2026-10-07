# Hardware-Software Co-Design

作者：Edison Lin
類型：個人研究筆記
主題：儲存系統中的跨層共同設計

Hardware-software co-design 的核心是不要讓硬體與軟體各自最佳化卻錯過整體最優。當裝置知道某些介質限制、回收狀態或可用 hint，而軟體知道資料生命周期、更新模式與服務等級需求時，兩邊若完全隔離，效能與可預測性常會浪費掉。

在儲存領域，典型例子包含 zoned storage、computational storage 與 NVM-aware data structures。這些方向共同說明一件事：如果介面暴露得夠好，上層就能設計更合理的 placement、scheduling 與 durability policy。

好的 co-design 論文通常同時回答三件事：暴露了哪些新介面、軟體如何利用它們、以及這樣的複雜度轉移是否值得。少了其中任一項，論文價值就會下降。
