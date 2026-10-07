# Tree and Hash Indexes

作者：Edison Lin
類型：個人研究筆記
主題：B-tree 與 Hashing 的儲存觀點

樹狀索引與 hash 結構不能只從演算法角度看，還要看它們產生的 I/O pattern。B-tree 類結構擅長範圍查詢與有序遍歷，但更新可能導致節點分裂、合併與較分散的寫入。這在某些介質上會轉成隨機寫成本與 metadata 更新負擔。

Hash 結構對 point lookup 很有效，但不擅長範圍查詢，也可能因 rehash 或碰撞處理帶來額外成本。若 workload 幾乎都是查單點 key，hash 可能合理；但若需要 ordered scan 或長期維護局部性，樹狀結構仍有優勢。

對儲存系統研究來說，索引結構不是抽象資料結構課題，而是 workload、storage media 與 persistence strategy 的共同結果。
