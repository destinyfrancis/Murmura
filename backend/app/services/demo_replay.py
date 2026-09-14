"""One explicitly scripted replay using the normal graph/action/report tables."""
from backend.app.utils.db import get_db

DEMO_SESSION_ID = "murmura-scripted-flood-demo"


async def ensure_demo_replay() -> None:
    """Install an idempotent, no-model example without touching existing runs."""
    async with get_db() as db:
        found = await (await db.execute(
            "SELECT id FROM simulation_sessions WHERE id=?", (DEMO_SESSION_ID,),
        )).fetchone()
        if found:
            return
        seed = "預先編寫的示範，沒有執行模型：洪水將至。船夫阿玲需要燃料，店主阿康擔心欠款，醫生阿欣要先送病人離開。"
        await db.execute(
            "INSERT INTO simulation_sessions (id,name,status,sim_mode,seed_text,scenario_type,"
            "graph_id,agent_count,round_count,current_round,llm_provider,llm_model,oasis_db_path) "
            "VALUES (?,?,'completed','kg_driven',?,'fiction',?,3,3,3,'demo','scripted','')",
            (DEMO_SESSION_ID, "示範回放 · 洪水中的村莊（預先編寫）", seed, DEMO_SESSION_ID),
        )
        actors = [("ling", "阿玲", "船夫，需要燃料"), ("hong", "阿康", "店主，擔心欠款"), ("yan", "阿欣", "醫生，要先疏散病人")]
        for key, name, description in actors:
            await db.execute(
                "INSERT INTO kg_nodes (id,session_id,title,entity_type,description,properties) "
                "VALUES (?,?,?,'Person',?,?)",
                (f"demo_{key}", DEMO_SESSION_ID, name, description, '{"source":"scripted_demo"}'),
            )
        for source, target, relation in [("ling", "hong", "需要燃料"), ("yan", "ling", "安排病人登船"), ("yan", "hong", "協商預付款")]:
            await db.execute(
                "INSERT INTO kg_edges (session_id,source_id,target_id,relation_type,source_text) VALUES (?,?,?,?,?)",
                (DEMO_SESSION_ID, f"demo_{source}", f"demo_{target}", relation, seed),
            )
        posts = [
            (1, "阿玲", "船已準備好，但沒有足夠燃料，誰可以幫忙？"),
            (2, "阿康", "上次的欠款仍未清還；如果有人先付一部分，我願意供油。"),
            (3, "阿欣", "我可以先墊付急救船的燃料，先讓病人上船，其餘欠款再談。"),
        ]
        for number, name, content in posts:
            await db.execute(
                "INSERT INTO simulation_actions (session_id,round_number,agent_id,oasis_username,"
                "action_type,platform,content,sentiment) VALUES (?,?,?,?,'post','scripted',?,'unknown')",
                (DEMO_SESSION_ID, number, number, name, content),
            )
        content = """# 示範回放：洪水中的村莊

**這份資料是預先編寫的例子，沒有呼叫模型，沒有證明湧現或預測能力。**

## 編排的互動
阿玲提出燃料短缺；阿康表明欠款顧慮；阿欣提出先墊付急救船的燃料。
你可以在左邊查看同一批角色、關係及原文。它們來自正常的圖譜、活動及報告資料表。

## 尚未知道
阿康是否接受？其他村民是否認為安排公平？舊橋能否保住？例子沒有提供答案。

## 開始自己的探索
關閉 DEMO_MODE、設定自己的模型後，回首頁貼上材料。先用小型世界比較重要選擇，再決定是否擴大。
"""
        await db.execute(
            "INSERT INTO reports (id,session_id,report_type,title,content_markdown,summary) VALUES (?,?,?,?,?,?)",
            ("murmura-scripted-flood-report", DEMO_SESSION_ID, "scripted_demo", "示範回放 · 非模型結果", content, "預先編寫；沒有執行模型。"),
        )
        await db.commit()
