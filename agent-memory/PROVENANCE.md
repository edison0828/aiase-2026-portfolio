# 來源、保留範圍與公開整理

## 課程與骨架

- 課程：TAICA「生成式 AI 應用系統與工程」，2026，莊坤達。
- [官方課程倉庫](https://github.com/ktchuang/TAICA_AIASE2026)
- [HW4 說明](https://github.com/ktchuang/TAICA_AIASE2026/blob/main/homeworks/HW4.md)
- [官方 Python starter](https://github.com/ktchuang/TAICA_AIASE2026/blob/main/homeworks/HW4-python-starter.zip)

來源為 Edison Lin 的 `hw4-pi-memory-edison0828-main` 課程提交。公開整理前與所保存的官方 starter 比對：`memory/core.py`、`memory/cli.py`、`memory/__init__.py` 相同；`bm25.py` 與 `store.py` 包含完成的學生實作；`hybrid.py` 不在官方 starter 中。這項比對用於區分課程骨架、作業完成部分與本次公開整理的範圍。

保留必要的小型課程串接程式，使本人完成的 BM25、持久化模組能獨立示範。檔頭已標註其課程來源，這些 helper 不列為本人新增貢獻。

## 2026-10-07 公開整理新增或修訂

- 重寫中文 README、來源及驗證文件。
- 保留原提交的主要程式邏輯；僅將 `bm25.py`、`store.py` 已完成工作的 TODO 提示改為實際行為描述，加入來源檔頭。
- 新增 5 筆虛構記錄、4 個字詞匹配查詢及展示程式，名稱與內容均為公開整理新增。
- 新增 5 項標準函式庫 unittest；不沿用課程測試或 benchmark。
- 將必要／選配依賴分開，核心流程不需額外套件。

## 未收錄

- 原課程 benchmark、fixtures、tests、Classroom／CI 與成績／AI 評語。
- 課程提供的 Pi extension、模型服務設定及未完成的 Pi 展示說明。公開版不宣稱已驗證 Pi 整合。
- 原報告中與另一份評測紀錄不一致的 hybrid 提升數字；沒有用本次 toy 結果替代正式品質評估。
- 任何真實 session 記憶檔、對話紀錄、金鑰、模型權重或快取。

## 引用與權利範圍

BM25 是既有檢索方法，本作業是方法實作練習，不主張提出 BM25 或新的檢索理論。選配語意檢索依賴 Sentence Transformers 及 `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` 模型，未附套件或權重，應遵循其原授權。

原提交與所查課程 starter 未附可據以替全部材料重新授權的 LICENSE。保留的課程 helper 已註明來源，未將其改列本人原創，也未替混合來源內容新增統一授權；來源標註本身不另授予第三方材料的權利。
