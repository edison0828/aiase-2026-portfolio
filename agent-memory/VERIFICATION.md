# 公開版驗證紀錄

日期：2026-10-07。測試與語料都是公開整理新增，不沿用課程 benchmark 或評分結果。

## 執行環境與指令

macOS、Python 3.12.14，核心流程只使用標準函式庫。未安裝語意模型，未呼叫 API。所有持久化測試都指定暫存路徑，不使用家目錄的既有記憶檔。

```text
python -m unittest discover -s tests -v
Ran 5 tests — OK

python examples/toy_retrieval.py
microscope sketches -> demo-optics
basil watering -> demo-garden
clarinet samples -> demo-audio
hiking routes -> demo-map
Toy lexical matches at rank 1: 4/4
```

## 檢查內容

- 5 筆虛構記錄、4 個刻意使用相同字詞的查詢；相關記錄排在第一筆。
- 空輸入、K=0 與同分時的穩定排序。
- JSON 保存中文、重新載入與 id 去重。
- 不同 CLI 程序之間保存、取回及組成注入文字。
- 小預算時省略過長記錄；這只檢查粗估規則，未用模型 tokenizer 驗證。

4/4 是刻意簡單範例的檢查結果，不是一般化測試，也不支持 hybrid 優於 BM25。未測試 `memory/hybrid.py` 的模型載入與語意排序，未測試 Pi 整合、長期多程序寫入、當機復原或真實 Agent 任務。原報告與自動評測的 hybrid 結果不一致，公開版不引用其提升數字。
