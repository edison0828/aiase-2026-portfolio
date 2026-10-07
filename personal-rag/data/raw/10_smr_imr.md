# SMR and IMR

作者：Edison Lin
類型：個人研究筆記
主題：高密度磁記錄變體對系統設計的影響

SMR 透過部分重疊磁軌來提高密度，但代價是寫入管理變得更複雜。某些區域需要順序化寫入，這使得 host 若仍用傳統隨機覆寫思維操作裝置，就容易付出高額整理成本。這個情況與 zoned storage 的設計思維高度相通。

IMR 等更進一步的排列策略也反映相似訊號：裝置密度提升後，host 端軟體更需要理解寫入規則與資料佈局。於是研究問題會轉向 metadata/data 分離、更新聚合與 workload-aware placement。

這類裝置的重要性，在於它們逼迫系統研究從抽象化便利性重新回到媒體限制本身。對 file system 與 object placement 的設計尤其有啟發性。
