# Performance Metrics

作者：Edison Lin
類型：個人研究筆記
主題：儲存系統常見評估指標

儲存系統研究不能只看平均吞吐量。平均值很容易掩蓋掉尾延遲、steady-state 行為與背景整理成本。對 SSD、LSM-tree、或任何有 compaction / garbage collection 的系統來說，P99 latency 往往比平均 latency 更能反映真實使用體驗。

常見指標包括 throughput、average latency、P99 latency、write amplification、read amplification、space amplification、GC overhead、cache hit rate 與 recovery time。若研究涉及 host-device 協調，還應觀察背景工作和前景請求的競爭關係。

好的評估不只比較絕對數字，也會說明 workload 型態、資料大小、操作比例、fill level、執行時間與暖機方式。否則 benchmark 很容易只測到裝置暫態行為，而不是長時間穩態表現。
