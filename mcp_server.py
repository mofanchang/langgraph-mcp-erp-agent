# mcp_server.py
from mcp.server.fastmcp import FastMCP

# 建立 FastMCP Server 實例
mcp = FastMCP("ERP MCP Server")

# =====================================================================
# [PROPRIETARY IMPLEMENTATION HIDDEN]
# 企業資料庫連線與核心演算法（庫存、採購、CRM）已隱藏。
# 此處僅展示 MCP (Model Context Protocol) 工具註冊架構，供面試/架構展示參考。
# =====================================================================

@mcp.tool()
def check_stock(product_id_or_name: str) -> dict:
    """[Mock] 查詢特定商品的當前庫存狀態"""
    return {"status": "Implementation Hidden"}

@mcp.tool()
def check_expiry(days_threshold: int = 7) -> list:
    """[Mock] 掃描效期低於閾值的商品清單"""
    return [{"status": "Implementation Hidden"}]

@mcp.tool()
def calc_order_qty(product_id: str) -> dict:
    """[Mock] 根據歷史消耗率與安全庫存水位計算最佳訂購量"""
    return {"status": "Implementation Hidden"}

@mcp.tool()
def get_supplier_info(target: str) -> dict:
    """[Mock] 獲取指定商品或供應商的聯絡資訊與 Lead Time"""
    return {"status": "Implementation Hidden"}

@mcp.tool()
def get_customer_info(customer_id_or_name: str) -> dict:
    """[Mock] 查詢特定客戶的分級與歷史消費紀錄"""
    return {"status": "Implementation Hidden"}

@mcp.tool()
def search_customers(query: str) -> list:
    """[Mock] 模糊搜尋客戶名單"""
    return [{"status": "Implementation Hidden"}]

@mcp.tool()
def analyze_sales(months: int = 3) -> dict:
    """[Mock] 計算指定月份內的總營收與年增率 (YoY)"""
    return {"status": "Implementation Hidden"}

if __name__ == "__main__":
    print("[INFO] ERP MCP Server (Skeleton Mode) 啟動在 http://localhost:8000")
    mcp.run(transport="sse")
