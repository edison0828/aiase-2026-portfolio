# 來源、保留範圍與公開整理

## 課程來源

- 課程：TAICA「生成式 AI 應用系統與工程」，2026，莊坤達。
- [官方課程倉庫](https://github.com/ktchuang/TAICA_AIASE2026)
- [HW3 作業說明](https://github.com/ktchuang/TAICA_AIASE2026/blob/main/homeworks/HW3.md)

本目錄由 Edison Lin 的 `hw3-build-your-personal-rag-edison0828-main` 課程提交整理，保留 `data_update.py`、`rag_query.py`、`skill_builder.py` 與 `storage_rag/` 主要實作。作業題目與要求來自課程，不當作本人提出的新研究方法。來源說明用於區分課程要求、原提交與本次公開整理的範圍。

## 保留的資料

保留原提交 22 份個人主題筆記／文字、`paper_notes/` 的 10 份論文初讀摘要，以及 `paper_manifest.md` 官方來源清單，共 33 份文字來源。這些筆記是學習整理，不是經同儕審查的研究成果。來源清單另加註公開版不附本地 PDF；其餘筆記僅統一 UTF-8 編碼，未改寫內容。三份 `demo_*.md` 是 2026-10-07 公開整理新增的示範材料，文內已標示，無真實實驗結果。

## 2026-10-07 公開整理新增或修訂

- 重寫中文展示文件，新增 3 份示範語料、查詢範例及 3 項整合測試；非原課程評分測試。
- 預設明確選用原有 hashing 類別；語意模型改為自行啟用，移除原本「任意錯誤即靜默退回 hashing」行為，並顯示執行模式。
- 將課程代理設定改為中立的 `RAG_API_KEY`、`RAG_BASE_URL`、`RAG_CHAT_MODEL`。設定欄位改名，未替使用者填入服務或憑證。
- `.env` 載入改為在檔案存在時才匯入 python-dotenv，讓無 `.env` 的離線展示只需要 NumPy。
- 明示擷取式輸出不是模型回答；API 錯誤僅顯示錯誤類型，避免原始例外訊息夾帶服務細節。
- 修正刪除來源時處理後檔案的相對路徑；相關測試確認索引及處理文字均移除。
- 將生成文件預設放到忽略的 `artifacts/generated_skill.md`，並建立必要的輸出目錄。
- 將必要／選配套件分開列出。公開版的套件範圍不是原作業環境的完整重建鎖定檔。

## 未收錄的內容

- 10 篇完整第三方論文 PDF，以及 `data/processed/papers/` 全文抽取；僅在延伸閱讀列官方來源。
- 原先生成的 `skill.md`、向量索引、快取、模型權重及執行產物。
- 課程 AI 評語、成績、Classroom 設定、課程代理網址及任何實際憑證。
- 原語料統計與未重新驗證的效能敘述，不沿用到較小的公開示範。

## 外部元件與授權範圍

程式使用 Python／SQLite、NumPy，選配 python-dotenv、OpenAI Python SDK、PyMuPDF、Sentence Transformers、Hugging Face Hub、LiteLLM；套件及模型由使用者依自己的需求安裝，不隨本目錄散布。各元件與模型仍適用其原授權，這份整理不另授予第三方程式、論文或課程材料的權利。原提交與所查課程副本未附可據以替全部材料重新授權的 LICENSE，因此未替混合來源內容加入統一的新授權。
