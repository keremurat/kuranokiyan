from mcp.server.fastmcp import FastMCP
from app import dummyTool

import json
from app import get_sure_meaning, kuran_arastirma_yap
from datetime import datetime

# Initialize MCP server
mcp = FastMCP("your-mcp-name")

@mcp.tool()
async def dummy_tool(param: str) -> str:
    """
    Definition of a tool here.
    """
    # Do some awsome processing here
    awsome_response = dummyTool(param)
    if not awsome_response:
        return "No awsome response found."

    return 


@mcp.tool()
async def sure_anlami(sure_adi: str) -> str:
    """
    Girilen sure adının detaylı bilgilerini döner (anlam, ayet sayısı, iniş yeri, vb.).
    Args:
        sure_adi (str): Sure adı (ör: 'Fatiha')
    Returns:
        str: JSON formatında detaylı sure bilgileri veya hata
    """
    try:
        result = get_sure_meaning(sure_adi)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }, ensure_ascii=False, indent=2)

# Your another awsome tools can be added here
@mcp.tool()
async def kuran_arastirma(soru: str) -> str:
    """
    Kuran ile ilgili genel soruları araştırır (ör: "Kuranda hangi peygamberler var?", "Hangi surelerde Hz. Musa geçer?")
    Args:
        soru (str): Araştırılacak genel soru
    Returns:
        str: JSON formatında arama sonuçları veya hata
    """
    try:
        result = kuran_arastirma_yap(soru)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }, ensure_ascii=False, indent=2)
# @mcp.tool()
# async def another_awsome_tool(param: str) -> str:
#     """
#     Get better at AI.
#     """
#     # Do some awsome processing here
#     return "You are getting better at AI!"


if __name__ == "__main__":
    mcp.run(transport="stdio")