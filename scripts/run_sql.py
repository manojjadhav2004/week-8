"""
Generic runner for .sql files against ecommerce.db.

Splits a .sql file into individual statements delimited by
'-- N. Title' style comments (or plain ';'-separated statements if no such
comments are found), executes each, and prints a preview of the results.

Usage:
    python3 scripts/run_sql.py sql/aggregations.sql
"""

import sys
import re
import sqlite3

DB_PATH = "ecommerce.db"


def split_named_queries(sql_text):
    """Split on '-- N. Title' headers. Falls back to ';'-splitting if none found."""
    blocks = re.split(r"\n-- (\d+)\.\s*(.+?)\n", sql_text)
    if len(blocks) > 1:
        queries = []
        i = 1
        while i < len(blocks) - 1:
            num, title, body = blocks[i], blocks[i + 1], blocks[i + 2]
            body = re.split(r"\n-- -+\n", body)[0].strip()
            if body:
                queries.append((f"{num}. {title}", body))
            i += 3
        return queries
    # Fallback: split on semicolons
    stmts = [s.strip() for s in sql_text.split(";") if s.strip() and not s.strip().startswith("--")]
    return [(f"Statement {i+1}", s) for i, s in enumerate(stmts)]


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/run_sql.py <path/to/file.sql>")
        sys.exit(1)

    sql_path = sys.argv[1]
    with open(sql_path) as f:
        sql_text = f.read()

    queries = split_named_queries(sql_text)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for title, query in queries:
        print(f"\n{'='*70}\n{title}\n{'='*70}")
        try:
            cur.execute(query)
            cols = [d[0] for d in cur.description] if cur.description else []
            rows = cur.fetchall()
            if cols:
                print(" | ".join(cols))
                print("-" * 60)
            for row in rows[:10]:
                print(" | ".join(str(v) for v in row))
            if len(rows) > 10:
                print(f"... ({len(rows)} total rows)")
        except Exception as e:
            print(f"ERROR: {e}")

    conn.close()


if __name__ == "__main__":
    main()
