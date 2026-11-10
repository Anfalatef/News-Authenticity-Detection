from app.db.connection import SessionLocal
from app.db.models import Article, Chunk

def main():
    s = SessionLocal()
    try:
        article = s.query(Article).order_by(Article.article_id.desc()).first()
        if not article:
            print("No articles found.")
            return

        print("ARTICLE:", article.article_id, article.title)
        print("URL:", article.url)
        print("-" * 80)

        chunks = (
            s.query(Chunk)
            .filter(Chunk.article_id == article.article_id)
            .order_by(Chunk.chunk_index.asc())
            .limit(5)
            .all()
        )

        for c in chunks:
            text = c.chunk_text.replace("\n", " ").strip()
            preview = text[:220] + ("..." if len(text) > 220 else "")
            print(f"[chunk_index={c.chunk_index}] len={len(c.chunk_text)}")
            print(preview)
            print("-" * 80)

    finally:
        s.close()

if __name__ == "__main__":
    main()
