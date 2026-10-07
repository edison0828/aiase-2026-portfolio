# NVM Introduction

作者：Edison Lin
類型：個人研究筆記
主題：NVM 對系統研究的意義

NVM 類技術的吸引力不只是更低延遲，而是它模糊了記憶體與儲存之間的邊界。若資料在斷電後可保留，且延遲顯著低於 block storage，作業系統、檔案系統、資料庫與資料結構就不一定該沿用原本的 block-oriented 假設。

對系統研究者而言，NVM 的價值在於提出新問題：資料是否應直接以 persistent pointer 方式存取？crash consistency 要落在 library、kernel 還是 application？傳統 WAL 與 page cache 還需要維持同樣形式嗎？

即使某些 NVM 技術尚未大規模普及，這些問題本身仍能推動跨層抽象與一致性模型的重新設計，因此具有長期研究價值。
