# 結合確定性驗證的 AI 程式生成與除錯 Skills

這是我在成大「生成式 AI 應用系統與工程」課程中完成的期末專案，使用 Hermes Agent 的 skill 機制，把模型的文字輸出接到可以實際檢查的工具流程。公開版本整理了四組 skill、驗證程式與測試，並以另外撰寫的小型示例取代課程的參考題目。

我想處理的問題很直接：模型能寫出看似合理的 SQL 或 Python，但這不代表欄位存在、邊界條件正確，或最後輸出符合系統需要的格式。因此，我把生成、檢查及結果輸出分成不同步驟，讓錯誤可以被觀察，也讓模型有明確的修正依據。

## 我實作的部分

| Skill | 主要做法 | 在這份作品中可檢查的內容 |
|---|---|---|
| Text2SQL | 先對齊資料表與欄位，再產生 SQLite 查詢 | 單一 SELECT 規則、SQL 字串／註解處理、`EXPLAIN` 語法與欄位檢查、結果 JSON |
| Code Author | 由任務規格產生 Python，執行自測後再輸出 | 入口函式、AST import 檢查、SLOC、給定與內建邊界測資 |
| Bug Hunter | 以實際測資結果搭配 AST 提供錯誤證據 | 錯誤輸出、例外、逾時，以及對已知題型的錯誤行號與類型提示 |
| Open Reproducer | 從候選測資中尋找可重現失敗的小型輸入 | 輸入、預期值、實際值或例外，以及未發現失敗時的結果 |

四組目錄都位於 [`skills/`](skills/)。`SKILL.md` 是交給 Hermes 的流程描述；其中的 Python helpers 負責可重複的檢查。課程提供的框架、我補強的部分與 Codex 輔助範圍，詳見 [來源與整理說明](ATTRIBUTION.md)。

## 在本機執行

以下流程不需 API key，也不會呼叫模型。使用 Python 3.10 以上；實際驗證環境記錄在 [CHECKS.md](CHECKS.md)。程式的逾時機制使用 POSIX signal，建議在 macOS 或 Linux 執行。

```bash
cd final-project
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/demo.py
python -m pytest -q
```

離線示例先檢查有效 SQL 與不存在的欄位，再將自行撰寫的正確／錯誤二分搜尋程式交給 self-test、Bug Hunter 與 Reproducer。每一步的輸出都會列出。需要保存時可使用：

```bash
python scripts/demo.py --output evidence/offline-demo.json
```

這個示例驗證的是工具與契約，不包含 LLM 產生程式的成功率。若已自行設定 Hermes，可將四組 skills 加入自己的環境；這份作品不附課程 gateway、權杖或模型服務設定。

## 目前結果與界限

公開整理後的實際檢查記錄放在 [`evidence/`](evidence/)，評估範圍另見 [CHECKS.md](CHECKS.md)。這些是本機功能測試，不是課程隱藏測試、模型比較或正式效能評測。

- Reproducer 搜尋的是有限候選測資，按輸入大小回傳第一個失敗案例，不保證全域最小，也不能由測試通過推論任意程式皆正確。
- 候選 Python 會被 `exec` 執行；請只執行自己檢查過的可信示例。這些 helpers 沒有提供執行不可信程式所需的安全隔離。

各工具的適用範圍、原始評閱的未通過項目，以及後續可以改善的地方，都保留在 [CHECKS.md](CHECKS.md)。

## 整理後的目錄

```text
skills/                     四組學生 skills 與 helpers
scripts/                    相容輸出工具、公開版離線示例
tests/                      保留及調整的功能測試
examples/portfolio_cases/   公開整理時新寫的示例，非課程題庫
evidence/                   本次本機驗證輸出
ATTRIBUTION.md              來源、AI 輔助與公開版變更
CHECKS.md                   驗證方法與範圍
```
