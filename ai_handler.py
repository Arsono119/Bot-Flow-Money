import os
import json
import logging
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "ISI_GROQ_API_KEY_KAMU")
GROQ_MODEL = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

logger = logging.getLogger(__name__)

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
- Jawab PURE JSON aja, ga usah pake teks lain"""


def parse_transaction(text: str) -> dict | None:
    try:
        resp = requests.post(GROQ_URL, json={
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.3,
            "max_tokens": 200,
        }, headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }, timeout=30)

        data = resp.json()
        raw = data["choices"][0]["message"]["content"]
        result = json.loads(raw)

        amount = int(result["amount"])
        if amount <= 0:
            return None

        return {
            "type": result["type"],
            "amount": amount,
            "category": result.get("category", "Lainnya"),
        }
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return None


def format_rupiah(amount):
    return f"Rp{amount:,}".replace(",", ".")
