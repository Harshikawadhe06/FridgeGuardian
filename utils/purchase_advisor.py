def generate_purchase_advice(conn, user_id):

    consumed_items = conn.execute(
        """
        SELECT item_name,
               SUM(CASE WHEN status='consumed' THEN 1 ELSE 0 END) as consumed_count,
               SUM(CASE WHEN status='wasted' THEN 1 ELSE 0 END) as wasted_count
        FROM items
        WHERE user_id=?
        GROUP BY item_name
        """,
        (user_id,)
    ).fetchall()

    buy_more = []
    buy_less = []

    for item in consumed_items:

        consumed = item["consumed_count"]
        wasted = item["wasted_count"]

        total = consumed + wasted

        if total == 0:
            continue

        score = consumed / total

        if score >= 0.7:
            buy_more.append(item["item_name"])

        elif score <= 0.4:
            buy_less.append(item["item_name"])

    return buy_more[:3], buy_less[:3]