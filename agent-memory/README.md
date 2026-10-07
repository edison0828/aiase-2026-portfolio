# Agent 記憶檢索練習

這個專案來自「生成式 AI 應用系統與工程」HW4。我在課程提供的 Python 骨架中完成 BM25 計分與 JSON 持久化，讓記錄可以保存、跨程序取回，再整理成提供給模型的文字。另加入 `memory/hybrid.py`，探索將字詞匹配與向量相似度結合。

本次驗證以 **Python 記憶模組**為主，Pi 整合仍待後續測試。來源分工及本次新增材料見 [來源說明](PROVENANCE.md)。

## 實作分工

| 部分 | 來源與作用 |
| --- | --- |
| `memory/bm25.py` | tokenizer 來自課程；作業完成 BM25 計分與穩定排序。 |
| `memory/store.py` | 類別骨架來自課程；作業完成 JSON 載入、寫回與 id 去重。 |
| `memory/hybrid.py` | 原提交新增的選配模組，結合正規化的 BM25 與 cosine similarity。 |
| `memory/core.py`、`cli.py`、`__init__.py` | 課程提供的串接／介面程式，保留必要部分並標註，非本人新增成果。 |
| `examples/`、`tests/` | 2026-10-07 公開整理新增的虛構案例與驗證，並非課程 benchmark。 |

## 離線執行

Python 3.10 以上即可，核心展示及測試只使用標準函式庫。在本目錄執行：

```bash
python examples/toy_retrieval.py
python -m unittest discover -s tests -v
```

展示資料只有 5 筆虛構記錄、4 個刻意含相同字詞的查詢；預期 4 題都會把指定記錄排在第一筆。這是方便檢查流程的例子，**不是語意理解、一般化能力或混合檢索效果的證據**。

也可以測試不同 CLI 程序間的資料保存。以下為 macOS／Linux shell 範例，`PI_MEMORY_PATH` 指向本地檔案：

```bash
export PI_MEMORY_PATH="$PWD/.local-memory/observations.json"
python -m memory.cli capture --summary "The fictional map editor exports GeoJSON." --tags maps
python -m memory.cli retrieve --query GeoJSON --k 1
python -m memory.cli inject --query GeoJSON --budget 100
```

Windows PowerShell 可先設定 `$env:PI_MEMORY_PATH="$PWD/.local-memory/observations.json"`，再執行同樣的 Python 指令。範例沒有真實對話或個人資料；若自行加入真實記錄，請把記憶檔留在版本控制之外。未設定路徑時，原課程介面預設使用家目錄下 `.pi-memory.json`。

## 混合檢索是選配研究練習

`memory/hybrid.py` 對 BM25 分數與向量 cosine similarity 各自做 min-max 正規化，再加權相加；預設權重是 0.65／0.35。它與核心 `retrieve()` 分開，**CLI 仍使用 BM25**。

若自行試用，可安裝 `requirements-optional.txt`，再從 Python 使用 `HybridRetriever`。這會載入 Sentence Transformers，首次執行可能下載模型。此次公開整理未安裝模型、未驗證此選配路徑，也不宣稱上述權重最佳或 hybrid 已優於 BM25。原作業報告與自動評測對 hybrid 的結果不同，因此未把那些提升數字放入公開作品介紹。

## 驗證與目前限制

2026-10-07 通過 5 項公開整理新增測試，包含虛構查詢、同分排序、重新載入與去重、跨 CLI 程序保存／取回，以及很小的文字預算。另執行新範例，4 個查詢皆找到預期的第一筆記錄。完整範圍見 [驗證紀錄](VERIFICATION.md)。

目前每次查詢都掃描全部記錄；JSON 寫入未提供多程序協作或當機復原保證。載入損壞的 JSON 時會視為空資料，後續寫入可能覆蓋舊檔，故此版本不適合保存唯一副本的重要記錄。token 預算以字元數粗估，不能視為模型 tokenizer 的嚴格限制。BM25 沒有相關性門檻，零分項目也可能出現在前 K 筆；產生注入文字不代表 Agent 已使用或正確理解這些內容。
