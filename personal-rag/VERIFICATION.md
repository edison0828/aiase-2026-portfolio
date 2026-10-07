# 公開版驗證紀錄

日期：2026-10-07。這是公開整理新增的功能檢查，不是原課程評分，也不是研究品質評測。

## 執行環境

- macOS、Python 3.12.14、NumPy 2.3.5。
- 使用已存在的本機 Python 環境，未為此驗證安裝套件。
- 明確指定 `EMBEDDING_PROVIDER=hashing`，停用模型下載，未設定生成模型端點或金鑰；未建立 `.env`。
- 測試在暫存副本中執行，結束後移除索引與處理文字。

## 實際執行與結果

```text
python -m unittest discover -s tests -v
Ran 3 tests — OK
```

1. 建立索引、查詢並顯示 hashing／擷取式模式；以 `ambercache evicting persistent copy` 取得示範筆記及來源段落。
2. 未改動時跳過索引更新；修改後確認新文字已進入 SQLite；刪除後確認索引片段及處理後文字均移除。
3. 無生成模型時輸出 `artifacts/generated_skill.md`，包含來源清單與擷取式模式說明。

另以預設切分參數在暫存副本完整重建：

```text
Embedding backend: hashing (HashingFallbackEmbedder)
Indexed 36 changed source(s), removed 0 source(s), and wrote 37 chunk(s).
```

36 份來源由原提交的 33 份文字來源加上 3 份新增 demo 組成。37 chunks 是此次公開版的結果，非原課程含 PDF 語料的統計。

## 結果如何解讀

測試確認資料流程與來源資訊能運作，沒有測量一般問題的檢索品質。單詞 `ambercache` 在全部語料上曾因 hashing 碰撞而把來源清單排在示範筆記之前；展示改用四個明確字詞，並保留碰撞限制說明。這個選擇只方便檢查流程，不能當作準確率提升。

以下未在本次驗證：Sentence Transformers／LiteLLM 語意嵌入、外部生成模型 API、`.env` 套件載入、PDF 抽取、模型切換後的既存索引相容性、效能及人工標註品質評估。測試未使用私人資料或真實服務金鑰。
