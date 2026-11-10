from app.db.connection import SessionLocal
from app.db.models import Chunk

def main():
    s = SessionLocal()
    try:
        rows = s.query(Chunk.chunk_text).all()
        lengths = [len(r[0]) for r in rows if r[0]]

        if not lengths:
            print("No chunks found.")
            return

        lengths.sort()
        n = len(lengths)

        avg = sum(lengths) / n
        p50 = lengths[int(n * 0.50)]
        p90 = lengths[int(n * 0.90)]
        p95 = lengths[int(n * 0.95)]
        mn = lengths[0]
        mx = lengths[-1]

        short = sum(1 for x in lengths if x < 300)
        long = sum(1 for x in lengths if x > 4000)

        print(f"chunks_count = {n}")
        print(f"min_len = {mn}")
        print(f"avg_len = {avg:.1f}")
        print(f"p50_len = {p50}")
        print(f"p90_len = {p90}")
        print(f"p95_len = {p95}")
        print(f"max_len = {mx}")
        print(f"short(<300) = {short} ({short/n*100:.1f}%)")
        print(f"long(>4000) = {long} ({long/n*100:.1f}%)")
    finally:
        s.close()

if __name__ == "__main__":
    main()
