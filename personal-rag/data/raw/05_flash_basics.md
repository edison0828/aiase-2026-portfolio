# Flash Basics

作者：Edison Lin
類型：個人研究筆記
主題：Flash 與 SSD 的基本限制

NAND Flash 和 DRAM 的差異不只在揮發性。Flash 的寫入與擦除粒度不同，不能像 RAM 一樣原地覆寫，因此裝置內部必須透過搬移、映射更新與背景回收來完成看似簡單的 write。這個限制直接改變了效能穩定度與壽命管理方式。

理解 Flash 時，應同時關注 page、block、program / erase cycle 與 over-provisioning。這些概念決定了裝置在高填充率、碎片化寫入或混合讀寫場景下的行為。實務上，規格表上的順序讀寫速度遠不足以說明真實工作負載的表現。

對系統研究而言，Flash 最重要的訊息是介質本身已經帶有複雜管理邏輯，因此 host 軟體若完全忽略裝置特性，往往會把某些成本放大到不可接受的程度。
