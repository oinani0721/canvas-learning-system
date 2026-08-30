"""条件 (c) 的可核验证据: 在 7692 真库上铺双 vault + 四类子组,
用**真实生产读方法**读一次, 打印实际返回的组归属。"""
import asyncio, os
from app.clients.neo4j_client import Neo4jClient
from app.graphiti.group_id_compat import to_physical_group_id as P

URI = os.getenv("NEO4J_TEST_URI", "bolt://127.0.0.1:7692")
PFX = "provec"
A, B = f"vault:{PFX}_a", f"vault:{PFX}_b"
AB = f"vault:{PFX}_ab"                       # 近似前缀的另一个 vault
GROUPS = {
    "A 根组":            P(A),
    "A canvas 子组":     P(f"{A}:board_x"),
    "A semantic 影子组": P(f"{A}:semantic"),
    "A punycode 子组":   P(f"{A}:特征值与特征向量"),
    "B 根组":            P(B),
    "近似前缀 vault":     P(AB),
}
USER = f"{PFX}_user"

async def main():
    c = Neo4jClient(uri=URI, user="neo4j", password="testpassword", use_json_fallback=False)
    await c.initialize()
    assert not c.is_fallback_mode, "降级了, 证据无效"
    clean = f"MATCH (n) WHERE n.group_id STARTS WITH 'vault__{PFX}' DETACH DELETE n"
    for q in (clean, f"MATCH (c:Concept) WHERE c.name STARTS WITH '{PFX}' DETACH DELETE c",
              f"MATCH (u:User) WHERE u.id STARTS WITH '{PFX}' DETACH DELETE u"):
        await c.run_query(q)
    await c.run_query("MERGE (u:User {id:$u})", u=USER)
    for label, gid in GROUPS.items():
        await c.run_query("""
            MERGE (x:Concept {name:$n, group_id:$g}) SET x.id=$n
            WITH x MATCH (u:User {id:$u})
            MERGE (u)-[r:LEARNED {group_id:$g}]->(x)
            SET r.score=1, r.review_count=1, r.timestamp='2026-08-30T00:00:00',
                r.next_review = datetime() - duration('P1D')
        """, n=f"{PFX}_{label}", g=gid, u=USER)

    print("铺的数据 (物理组 → 概念名):")
    for label, gid in GROUPS.items():
        print(f"  {gid:52} {PFX}_{label}")

    print(f"\n用 A vault 根组 ({A}) 调**生产方法** get_review_suggestions 读一次:")
    rows = await c.get_review_suggestions(user_id=USER, limit=50, group_id=A)
    got = sorted(r["concept"] for r in rows if r["concept"].startswith(PFX))
    for n in got:
        print(f"  ✅ 返回  {n}")
    for label in GROUPS:
        if f"{PFX}_{label}" not in got:
            print(f"  ⛔ 未返回 {PFX}_{label}")

    expect = {f"{PFX}_{k}" for k in GROUPS if k.startswith("A ")}
    print(f"\n判定:")
    print(f"  保召回 (A 四类组全在)  : {'PASS' if expect <= set(got) else 'FAIL'}  缺 {sorted(expect - set(got))}")
    print(f"  零泄漏 (B / 近似前缀不在): {'PASS' if not (set(got) - expect) else 'FAIL'}  多 {sorted(set(got) - expect)}")
    print(f"  同一个结果集同时成立    : {'PASS' if set(got) == expect else 'FAIL'}")

    for q in (clean, f"MATCH (c:Concept) WHERE c.name STARTS WITH '{PFX}' DETACH DELETE c",
              f"MATCH (u:User) WHERE u.id STARTS WITH '{PFX}' DETACH DELETE u"):
        await c.run_query(q)
    await c.cleanup()

asyncio.run(main())
