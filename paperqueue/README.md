# PaperQueue CLI：論文閱讀佇列管理

作者：林冠宇（Edison Lin / edison0828）  
課程：國立成功大學「生成式 AI 應用系統與工程」，莊坤達老師，114 學年度第 2 學期  
作品類型：HW2 規格驅動開發與版本演進

PaperQueue 是以 Python 標準函式庫實作的本地命令列工具，用 JSON 保存論文資料與閱讀筆記。這份作品保留 v1、v2 兩版程式與設計文件，讓讀者能看到功能增加時，如何保留既有指令、資料格式及錯誤處理約定。

## 功能與實作

| 面向 | v1 | v2 的擴充 |
| --- | --- | --- |
| 論文管理 | 新增、列出、查看、更新、刪除 | 保留原介面 |
| 閱讀佇列 | 依優先序、閱讀狀態與年份等規則排序 | 加入標籤與最低年份篩選 |
| 筆記 | 新增筆記 | 列出與刪除單筆筆記 |
| 標籤 | 整批設定 | 增量新增與移除 |
| 匯出 | — | Markdown 匯出與既有檔案覆蓋保護 |

推薦下一篇論文的 `next` 使用明確的排序規則；本工具沒有呼叫 LLM，也沒有使用語意檢索。作業中的 AI 應用背景主要在規格驅動開發流程，以及課程 TA Agent 產生的第二階段需求。

程式分為五個模組：`main.py` 處理參數與指令分派、`service.py` 負責操作與驗證、`storage.py` 讀寫 JSON、`formatter.py` 統一輸出，`models.py` 定義資料與錯誤型別。可以對照 [v1 SDD](v1/sdd_v1.md) 和 [v2 SDD](v2/sdd_v2.md) 閱讀。

## 快速使用

建議使用 Python 3.10 或更新版本，無需安裝第三方套件。以下指令從本目錄執行；資料會寫入指定的本地檔案。

```bash
python3 v2/main.py --db ./demo.json add --title "Example Paper" --authors "Example Author" --year 2024 --tags storage,systems --priority 5
python3 v2/main.py --db ./demo.json note --id 1 --text "Review the evaluation design."
python3 v2/main.py --db ./demo.json next --tag storage
python3 v2/main.py --db ./demo.json export --output ./reading-notes.md
```

`--db` 應放在子命令之前。已有同名匯出檔案時，程式會拒絕覆寫；確定需要覆寫時才加入 `--force`。各指令參數可由 `python3 v2/main.py --help` 查閱。

## 驗證

```bash
python3 tests/smoke_cli.py
```

此腳本為 2026-10-07 整理作品集時新增，並非原課程測試或評分器。它只使用 Python 標準函式庫，於暫存目錄執行真實 CLI，再清除測試資料；不會讀取或修改使用者的論文資料庫。

驗證範圍包括原 v1 SDD 的九個連續操作案例在兩版本的輸出與退出碼、常見無效輸入、v1 資料由 v2 讀取，以及 v2 的筆記、標籤、篩選與匯出保護。它是有限案例的回歸檢查，不代表所有輸入或執行環境均已驗證。

2026-10-07 在 macOS 的 Python 3.9.6 與 Python 3.12 環境執行時，兩次均通過全部 44 次 CLI 呼叫及資料檢查。

## 來源、本人作品與 AI 協助

- [課程首頁](https://github.com/ktchuang/TAICA_AIASE2026)及 [HW2 規格](https://github.com/ktchuang/TAICA_AIASE2026/blob/main/homeworks/HW2.md)提供兩階段作業框架。
- `v1/`、`v2/` 內的五個 Python 模組、SDD 及套件清單，直接保留作者提供的作業版本，未因公開整理而修改程式行為。作品重點是 PaperQueue 的實作、模組劃分及規格到版本擴充的對應。
- v2 的四組延伸需求由課程 TA Agent 產生：筆記列出／刪除、佇列臨時篩選、增量標籤，以及資料匯出。這些要求不列為本人原創需求；課程提供的 `requirements_v2.md` 原文未重新發布。
- OpenAI Codex 協助本次作品集整理、README 與新增的 `tests/smoke_cli.py`，並協助執行回歸驗證。原作業的生成與修改歷程未隨作業快照提供。
- 本目錄省略課程 AI 評分回饋、Classroom workflow、執行快取與私人使用資料。

## 目前限制

這是本地單人使用的課程作品。JSON 儲存沒有鎖定或交易機制，不適合多個程序同時寫入；也沒有外部學術資料庫匯入、PDF 解析、全文搜尋、雲端同步或圖形介面。公開版本保留當時實作，不以完整產品或完整相容性認證呈現。

本目錄未另行指定開源授權；課程規格與其他外部材料的權利歸其原作者或機構。
