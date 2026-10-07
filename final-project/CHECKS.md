# 驗證紀錄與適用範圍

## 本次公開版驗證

日期：2026-10-07。環境：CPython **3.12.14**、macOS（Darwin／arm64），pytest **8.3.3**、radon **6.0.1**。執行時將虛擬環境加入 PATH，因此包含真正呼叫 radon 的測試。

| 檢查 | 實際結果 | 可支持的結論 |
|---|---|---|
| `python -m pytest -q` | **36 passed，0 skipped** | 保留與調整後的 SQL、SLOC、analyzer、reproducer、JSON 輸出契約測試通過 |
| `python scripts/demo.py` | **8/8 檢查通過** | 四組離線 helpers 能處理示例中的正確／錯誤案例 |

完整輸出保存在 [pytest.txt](evidence/pytest.txt)、[offline-demo.json](evidence/offline-demo.json)，執行環境另存為 [environment.json](evidence/environment.json)。測試沒有呼叫 Hermes、外部模型或 API，也沒有使用課程題庫或參考程式。

測試程式原本會讀取課程 reference tasks 的部分，已改為讀取這次新寫的三組示例；題型仍屬工具原先支援的範圍。這能確認公開副本解除課程資料相依後仍可運作，不能推論對未知程式也有相同比例的成功率。

## 工具能檢查什麼

**Text2SQL。** 以記憶體內的 SQLite schema 配合 `EXPLAIN` 檢查查詢語法與欄位／表名；另限制單一 SELECT，拒絕 DDL、DML、PRAGMA 與 WITH。它沒有對自然語言語意進行正確性證明，也沒有比較查詢結果與標準答案。本工具會執行輸入的 schema DDL，因此 schema 也應來自可信來源。

**Code Author。** 檢查語法、入口函式、靜態 import、SLOC 與有限測資。測試依賴題目要求及 expected 值正確；少數測試通過不足以保證完整正確性。缺少 radon 時原程式會使用較簡單的行數估算，本次驗證則有安裝 radon。

**Bug Hunter。** 主要將五種已知任務的測資結果與 AST 模式連結成錯誤報告。未知函式可以使用直接傳給 `analyze.py` 的 `edge_inputs`，但通用預設輸入不一定符合它的合法輸入域；錯誤行號與分類也屬啟發式判斷。`run.py` 的原有簡化介面沒有轉傳自訂 `edge_inputs`，有此需求時應直接使用 analyzer。

**Open Reproducer。** 對 `merge_intervals`、`binary_search`、`parse_csv_line`、`unique_paths`、`kth_smallest` 有內建測資，其他函式可提供含 expected 值的 `candidate_inputs`。它按 JSON 輸入長度排列候選，找到首個失敗即停止；沒有 delta debugging 或一般化輸入縮減，也未實作由 `bug_hint` 自動推導測資。未找到失敗表示本次候選沒有觸發錯誤，不表示程式正確。

`confidence` 保留原作業契約：由呼叫者提供或依分支給固定值，沒有經過機率校準，不能當成正確率。

## 執行環境的界限

這些工具會以 `exec` 執行候選程式。Code Author 與 Bug Hunter 並未隔離候選程式的檔案或網路存取；Open Reproducer 的 builtins 白名單也不是安全沙箱。逾時主要包住函式呼叫，沒有完整限制模組初始化、記憶體或其他資源；POSIX signal 在 Windows 不提供相同保障。

公開示例僅執行隨倉庫附上的小型可信程式。若未來要讓其他人提交任意程式，需要另外建立程序／容器隔離、資源限制與可靠的終止機制，不能直接對外開放現有 runner。

## 原始課程回饋與後續方向

原課程自動回饋指出，Open Track 的合法輸出與重複執行一致性通過，自宣告 gold 比對則未通過。原始完整評分輸出不在公開副本，本次也沒有重跑課程隱藏評測，因此不宣稱已修復當時所有失分原因。

後續可改善的項目包括：統一三個 Python 工具重複維護的 probes、區分「沒有找到錯誤」與「缺少合適測資」、讓未知題型明確要求可信測試 oracle，以及建立隔離執行環境。這些是後續方向，不列為本次已完成的成果。
