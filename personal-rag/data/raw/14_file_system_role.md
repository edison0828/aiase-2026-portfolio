# File System Role

作者：Edison Lin
類型：個人研究筆記
主題：檔案系統為何能決定儲存體驗

檔案系統不是單純的存檔 API。它負責命名空間、block allocation、metadata 維護、crash consistency 與 layout policy。這些決策會直接改變裝置看到的 I/O pattern，因此也決定了背景整理、延遲穩定度與壽命消耗。

在新興儲存裝置情境中，file system 尤其重要，因為它位於應用與裝置之間的關鍵邊界。若檔案系統忽略 Flash 或 zoned storage 限制，就可能用不合理的更新模式去觸發昂貴背景工作。反之，若檔案系統能區分 metadata、data 與生命周期，就更有機會改善可預測性。

因此很多 storage research 的真正戰場其實不在單純裝置 benchmark，而是在 file system policy 是否能把硬體特性轉成對應的軟體行為。
