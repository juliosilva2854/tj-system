"""Backfill idempotente: desnormaliza product_name/product_sku nos documentos de estoque.
Preenche apenas onde estiver ausente e o produto ainda existir na colecao products.
Executar uma unica vez apos o deploy da correcao de integridade referencial.
"""
import asyncio
from database import db


async def run():
    total = 0
    updated = 0
    cursor = db.inventory.find({}, {"_id": 0})
    async for it in cursor:
        total += 1
        if it.get('product_name'):
            continue
        prod = await db.products.find_one({"id": it['product_id']}, {"_id": 0})
        if not prod:
            continue
        await db.inventory.update_one(
            {"id": it['id']},
            {"$set": {"product_name": prod.get('name', ''), "product_sku": prod.get('sku', '')}},
        )
        updated += 1
    print(f"Inventory docs: {total} | atualizados com nome/sku: {updated}")


if __name__ == "__main__":
    asyncio.run(run())
