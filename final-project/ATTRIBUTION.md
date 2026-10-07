# 來源與公開版整理

原作業作者為林冠宇（GitHub：`edison0828`），課程為 AIASE 2026「生成式 AI 應用系統與工程」。本目錄是課程作業的公開作品整理版，不是原始 Classroom 倉庫的完整鏡像。

## 原始專案的來源

原始 `report.md` 註明單人完成，並明確揭露下列來源：

- 課程 starter 提供 repository structure、dev set、reference tasks、skill skeleton 與 `run_dev.py` grading helpers。學生在此基礎上實作、強化 Basic／Pairwise skills，另建立 Open Track skill 與測試。
- OpenAI Codex 協助撰寫 harness、測試、報告草稿及除錯指令；最終版本依課程規格與本地測試調整。公開版仍保留這項 AI 輔助說明，不宣稱完全未使用 AI。

本版本保留四個以 `edison0828` 命名的 skills，以及相關 wrapper、SQL／SLOC／analyzer／reproducer／輸出契約測試。部分測試及程式來自 starter 骨架後續增修；僅憑作業快照無法逐行重建其來源，不把整包程式或全部測試宣稱為從零原創。也未替教師提供的內容擅自新增開源授權。

## 2026-10-07 公開整理時的變更

以下為這次整理新增或調整的內容，由 Codex 協助完成，與原始課程提交區分：

1. 重新撰寫作品首頁、來源說明、驗證範圍及 `scripts/demo.py`；另建立三組 `examples/portfolio_cases/` 小型正確／錯誤程式示例。它們是展示用案例，不是課程公開或隱藏題庫。
2. Bug Hunter `analyze.py` 移除按 `task_id` 讀取課程 reference task 的程式。現在使用明確指定或從程式推斷的入口函式，搭配既有內建 probes 或呼叫者提供的 `edge_inputs`。其餘核心判斷保持原作業版本。
3. 既有測試改讀新示例；去除對 `hello-aiase` 的教師煙霧測試。保留原來的 SQL、SLOC、輸出契約及失敗案例測試目的。
4. 課程 `dev_set`、`reference-*` skills、`hello-aiase`、Classroom workflow、gateway 設定、原始評分回饋、`run_dev.py` 與 `verify_repo.py` 未納入此公開副本。原始文件仍由作者私人保留。

四個 `SKILL.md` 保留原課程使用方式及契約背景，內文的 grader、track、規格編號或評分敘述屬當時課程情境；公開版沒有隱藏評分器。SQL／Code Author／Open Reproducer 的核心 Python 實作未因作品整理而重新設計。原始 Open Track 的「minimal」名稱表示當時設計方向；公開介紹採用較精確的「候選集合內的小型失敗案例」。

## 評閱資訊的使用

原始 `AI_Review.md` 明示由課程自動化評分系統產生，供學習回饋參考。本作品不將該檔案原樣公開，也不把其中的 AI 評語、加分描述或分數當成研究成果、正式排名或獨立驗證。

原課程回饋與公開整理後的測試屬不同時間、不同案例；後者不能取代原始 gold 比對未通過的紀錄。
