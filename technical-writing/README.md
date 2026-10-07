# 系統研究與新興儲存技術導覽

作者：林冠宇（Edison Lin / edison0828）  
課程：國立成功大學「生成式 AI 應用系統與工程」，莊坤達老師，114 學年度第 2 學期  
作品類型：HW1 技術文章與 Markdown 文件實作

## 閱讀作品

[從系統研究到新興儲存裝置：一篇給未來研究生的技術導覽](article.md)

這篇文章從系統設計的取捨出發，整理記憶體階層、SSD 與 FTL、NVM、檔案系統及索引結構之間的關係，並以表格、Mermaid 圖和概念程式輔助說明。適合先讀第 2 節的設計取捨、第 4 節的 SSD／FTL，以及第 11 節如何把問題轉成研究假設。

本作品可呈現的工作是技術概念的整理、文章組織，以及 Markdown 文件的撰寫與渲染。原作業使用 Pandoc 產生 HTML，另附 PDF；此作品集保留可直接閱讀與追蹤修改的 Markdown 原文。

## 作品範圍

文章屬於入門技術導覽。第 11 節的資料放置策略是研究思考範例，程式也明示為概念展示；其中的 GC、寫入放大與延遲比較仍是待完成項目。因此，這份文章沒有提供 SSD 模擬器、裝置韌體實作或量測結果。

原文末尾列出 NVMe、Linux Kernel Documentation、USENIX 與 ACM Digital Library 等入門閱讀入口。這些入口不是逐項技術主張的論文引註；將本文延伸成正式研究報告時，仍需補上具體文獻並核對細節。

## 來源與整理方式

- [課程首頁](https://github.com/ktchuang/TAICA_AIASE2026)與 [HW1 作業規格](https://github.com/ktchuang/TAICA_AIASE2026/blob/main/homeworks/HW1.md)提供課程背景及作業要求。
- `article.md` 直接保留作者提供之原作業 `content.md`，未更改文章內容。
- 原文沒有嵌入第三方圖片；文中的圖以 Mermaid 或文字表示。本目錄沒有重新發布外部圖片或課程教材。
- 本次作品集目錄整理與 README 撰寫由 OpenAI Codex 協助。原作業的生成與修改歷程未隨作業快照提供。
- 教師評分回饋、GitHub Classroom 自動評分設定及衍生 HTML／PDF 未納入本目錄。

本目錄未另行指定開源授權；外部參考資料的權利歸其原作者或機構。
