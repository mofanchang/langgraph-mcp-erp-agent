# langgraph-mcp-erp-agent
# 🚀OmniAgent ERP: 基於 MCP 協議與Multiple-Ａgent的企業決策系統

本專案是一個生產級的 AI agent系統，旨在解決傳統 ERP 系統中數據孤島與決策鏈過長的問題。系統基於 LangGraph 與Model Context Protocol (MCP) 構建，實現了具備「營運嗅覺」的自動化指揮中心。

## 技術架構 (Technical Excellence)

*  Multi-Agent Orchestration：利用 LangGraph 實現有狀態的循環圖架構，精準調度專屬 Agent（Inventory, Procurement, CRM）進行複雜任務協作。
*   **混合模型策略 (Hybrid Model Strategy)**：
    *   **指揮官 (Llama 3.3 70B)**：負責高階意圖分析、跨部門結果整合與輸出品質審核 (Reflection)。
    *   **執行員 (Llama 3.1 8B)**：負責具體的工具調用與數據查詢，確保系統響應效率與低延遲。
*   **Skill-Based 工具包設計**：採用模組化的 **Skill Package** 概念，將業務邏輯（Python）與模型徹底解耦，便於系統擴展與維護。
*   **標準化數據對齊 (MCP)**：全面導入 **Model Context Protocol (MCP)**，建立 Agent 與資料庫間的標準溝通協議，確保數據的準確性與一致性。

## AI 工程防禦體系 (AI Engineering Guardrails)

針對 LLM 在企業應用中的落地痛點，本專案實作了多層防護機制：
*   **物理攔截器 (Logic Interceptors)**：在代碼層級建立關鍵字黑名單，強制攔截 Agent 的實體探索幻覺（如腦補無關商品或客戶姓名）。
*   **熔斷保護 (Meltdown Protection)**：針對 8B 模型可能的重複調用行為，設計了工具計數與上下文滑動窗口，有效防止 Token 溢位與循環報錯。
*   **自我修正機制 (Reflection node)**：在最後輸出前，由 70B 模型進行「數據真實性」校對，確保所有數字均來自資料庫。

## 系統工作流 (Workflow)

```mermaid
graph TD
    A[使用者輸入] --> B[Orchestrator 70B]
    B --> C{意圖路徑}
    C -->|庫存分析| D[Inventory Agent 8B]
    C -->|採購決策| E[Procurement Agent 8B]
    C -->|CRM/銷售| F[CRM Agent 8B]
    D & E & F --> G[Synthesizer 70B]
    G --> H[Reflection 節點 70B]
    H -->|品質通過| I[正式報表輸出]
    H -->|檢核失敗| G
