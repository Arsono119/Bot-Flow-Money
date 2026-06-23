import json
import re
from openai import OpenAI
from config import GROQ_API_KEY, GROQ_MODEL

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

SYSTEM_PROMPT = """Kamu adalah asisten pencatat keuangan yang santai dan gaul.

Tugasmu: dari teks user, tentukan:
- type: "income" (pemasukan) atau "expense" (pengeluaran)
- amount: jumlah dalam RUPIAH (integer, tanpa titik/koma)
- category: kategorinya. Contoh: Makanan, Transport, Gaji, Belanja, Hiburan, Tagihan, Kesehatan, Jastip, Lainnya

Aturan:
- "beli", "bayar", "pesan", "topup", "iseng" → expense
- "gajian", "bonus", "jual", "terima", "kiriman", "receh" → income
- "rb" = 000 (25rb → 25000), "jt" = 000000 (2jt → 2000000)
- Kalau nominal disebut "dua ribu" ubah ke angka 2000
- Kategorikan secara logis
- Jawab PURE JSON aja, ga usah pake teks lain

Contoh:
User: "beli nasi goreng 25rb"
→ {"type": "expense", "amount": 25000, "category": "Makanan"}

User: "gajian 5jt"
→ {"type": "income", "amount": 5000000, "category": "Gaji"}

User: "tadi jualan baju laku 150rb"
→ {"type": "income", "amount": 150000, "category": "Jualan"}

User: "bayar listrik 350rb"
→ {"type": "expense", "amount": 350000, "category": "Tagihan"}

User: "dapet kiriman dari mama 200rb"
→ {"type": "income", "amount": 200000, "category": "Kiriman"}

User: "naik grab 15rb"
→ {"type": "expense", "amount": 15000, "category": "Transport"}

User: "jajan cilok 5rb"
→ {"type": "expense", "amount": 5000, "category": "Makanan"}"""


def parse_transaction(text: str) -> dict | None:
    try:
        resp = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=200,
        )
        result = json.loads(resp.choices[0].message.content)

        amount = int(result["amount"])
        if amount <= 0:
            return None

        return {
            "type": result["type"],
            "amount": amount,
            "category": result.get("category", "Lainnya"),
        }
    except Exception as e:
        return None


def format_rupiah(amount):
    return f"Rp{amount:,}".replace(",", ".")
