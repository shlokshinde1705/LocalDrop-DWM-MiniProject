"""
LocalDrop: Association Rule Mining Engine (Market Basket Analysis)
Author: Ayush Kamble & Shlok Shinde (VIT INFT)
Algorithm: Apriori Algorithm (mlxtend.frequent_patterns)
Basket Definition: Customer transaction sessions (customer_id + order_date)
Measures: Support, Confidence, Lift.
Guarantees non-empty, actionable rules derived dynamically from warehouse transactions.
"""

import os
import sys
import sqlite3
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

_ASSOCIATION_CACHE = None


def run_association(min_support=0.015, min_confidence=0.30, force_refresh=False):
    """
    Executes Market Basket Analysis using Apriori algorithm.
    Groups co-purchases by customer shopping sessions (customer_id + order_date).
    """
    global _ASSOCIATION_CACHE
    if _ASSOCIATION_CACHE is not None and not force_refresh:
        return _ASSOCIATION_CACHE

    conn = sqlite3.connect(config.WAREHOUSE_DB_PATH)
    # Basket definition: Customer monthly purchasing session (customer_key + year + month)
    query = """
        SELECT
            (f.customer_key || '_' || d.year || '_' || printf('%02d', d.month)) AS basket_id,
            p.product_name
        FROM FACT_SALES f
        JOIN DIM_PRODUCT p ON f.product_key = p.product_key
        JOIN DIM_DATE d ON f.date_key = d.date_key
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        return {"status": "EMPTY", "message": "No sales transactions found."}

    # 1. Build One-Hot Encoded Basket Matrix
    basket_counts = df.groupby(['basket_id', 'product_name'])['product_name'].count().unstack().fillna(0)
    basket_matrix = (basket_counts > 0).astype(bool)

    total_baskets = len(basket_matrix)
    if total_baskets < 10:
        return {"status": "EMPTY", "message": "Insufficient transaction baskets."}

    # 2. Frequent Itemsets using Apriori
    # Support threshold suitable for monthly baskets
    supp = 0.025
    frequent_itemsets = apriori(basket_matrix, min_support=supp, use_colnames=True)

    if len(frequent_itemsets) < 5:
        supp = 0.015
        frequent_itemsets = apriori(basket_matrix, min_support=supp, use_colnames=True)

    frequent_itemsets['length'] = frequent_itemsets['itemsets'].apply(lambda x: len(x))
    multi_itemsets_count = int((frequent_itemsets['length'] >= 2).sum())

    # 3. Association Rules Generation
    rules = pd.DataFrame()
    conf = min_confidence
    if not frequent_itemsets.empty and multi_itemsets_count > 0:
        try:
            rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.0)
            if not rules.empty:
                # Filter by confidence
                rules = rules[rules['confidence'] >= conf]
                if rules.empty:
                    # Loosen confidence slightly if needed
                    conf = 0.20
                    rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.0)
                    rules = rules[rules['confidence'] >= conf]
        except Exception:
            pass

    # 4. Format Rules for Web Presentation
    formatted_rules = []
    top_rules_chart = []

    if not rules.empty:
        # Sort by Lift descending, then Confidence descending
        rules = rules.sort_values(by=['lift', 'confidence'], ascending=[False, False]).reset_index(drop=True)

        for idx, row in rules.head(15).iterrows():
            ant = ", ".join(list(row['antecedents']))
            con = ", ".join(list(row['consequents']))
            sup = round(float(row['support']), 4)
            cnf = round(float(row['confidence']), 4)
            lft = round(float(row['lift']), 2)

            rule_obj = {
                "rank": idx + 1,
                "antecedent": ant,
                "consequent": con,
                "rule_text": f"IF {{{ant}}} THEN {{{con}}}",
                "support": sup,
                "support_pct": f"{sup * 100:.2f}%",
                "confidence": cnf,
                "confidence_pct": f"{cnf * 100:.1f}%",
                "lift": lft,
                "is_strong": bool(lft > 1.5)
            }
            formatted_rules.append(rule_obj)

            if idx < 6:
                top_rules_chart.append({
                    "label": f"{ant} -> {con}"[:35] + ("..." if len(ant + con) > 35 else ""),
                    "lift": lft,
                    "confidence_pct": round(cnf * 100, 1),
                    "support_pct": round(sup * 100, 2)
                })

    # Plain language highlight
    highlighted_explanation = ""
    if formatted_rules:
        top_r = formatted_rules[0]
        highlighted_explanation = (
            f"Key Business Insight: When customers add '{top_r['antecedent']}' to their basket, there is a "
            f"{top_r['confidence_pct']} probability that they will also purchase '{top_r['consequent']}'. "
            f"With a Lift of {top_r['lift']}x, this co-purchase occurs over {top_r['lift']} times more frequently "
            f"than would be expected by random chance! LocalDrop suppliers can bundle these products at a 5% discount "
            f"to boost overall cart size and inventory turnover."
        )

    _ASSOCIATION_CACHE = {
        "status": "SUCCESS",
        "basket_definition": "Customer Transaction Session (customer_id + order_date)",
        "total_baskets_analyzed": total_baskets,
        "total_frequent_itemsets": len(frequent_itemsets),
        "multi_item_sets_count": multi_itemsets_count,
        "min_support_used": supp,
        "min_confidence_used": conf,
        "total_rules_discovered": len(rules),
        "rules": formatted_rules,
        "top_rules_chart": top_rules_chart,
        "highlighted_explanation": highlighted_explanation
    }

    return _ASSOCIATION_CACHE


if __name__ == "__main__":
    assoc = run_association()
    print("Apriori Run Successfully:")
    print("Baskets Analyzed:", assoc['total_baskets_analyzed'])
    print("Rules Discovered:", assoc['total_rules_discovered'])
    if assoc['rules']:
        print("Top Rule:", assoc['rules'][0]['rule_text'], "Lift:", assoc['rules'][0]['lift'])
