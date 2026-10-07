# SSD Evaluation

作者：Edison Lin
類型：個人研究筆記
主題：SSD 研究的評估重點

SSD 論文不能只報順序讀寫 MB/s。真正重要的是隨機 I/O、小請求、混合負載、steady-state 表現與 tail latency。尤其當系統同時有 foreground requests 與 background GC 時，只看平均值會嚴重誤判使用者體驗。

評估 SSD-aware 系統時，還應觀察 queue depth、fill level、工作集大小、preconditioning、trace length 與是否有 fsync / durability 要求。若研究主張改善 predictability，P99 和 P99.9 就必須是主要指標，而不是附錄數字。

好的實驗也會分開討論 host 端優化與 device 背景工作之間的關係。例如延遲變好，到底來自更少的邏輯 I/O，還是因為減少了 GC 干擾。這種分析會決定論文的說服力。
