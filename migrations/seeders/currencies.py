import uuid

from sqlalchemy import text

CURRENCIES = [
    {"code": "NGN", "name": "Nigerian Naira", "symbol": "₦"},
    {"code": "USD", "name": "US Dollar", "symbol": "$"},
    {"code": "EUR", "name": "Euro", "symbol": "€"},
    {"code": "GBP", "name": "British Pound Sterling", "symbol": "£"},
    {"code": "CAD", "name": "Canadian Dollar", "symbol": "C$"},
    {"code": "AUD", "name": "Australian Dollar", "symbol": "A$"},
    {"code": "NZD", "name": "New Zealand Dollar", "symbol": "NZ$"},
    {"code": "CHF", "name": "Swiss Franc", "symbol": "CHF"},
    {"code": "JPY", "name": "Japanese Yen", "symbol": "¥"},
    {"code": "CNY", "name": "Chinese Yuan", "symbol": "¥"},
    {"code": "INR", "name": "Indian Rupee", "symbol": "₹"},
    {"code": "PKR", "name": "Pakistani Rupee", "symbol": "₨"},
    {"code": "ZAR", "name": "South African Rand", "symbol": "R"},
    {"code": "KES", "name": "Kenyan Shilling", "symbol": "KSh"},
    {"code": "GHS", "name": "Ghanaian Cedi", "symbol": "GH₵"},
    {"code": "UGX", "name": "Ugandan Shilling", "symbol": "USh"},
    {"code": "TZS", "name": "Tanzanian Shilling", "symbol": "TSh"},
    {"code": "RWF", "name": "Rwandan Franc", "symbol": "RF"},
    {"code": "XOF", "name": "West African CFA Franc", "symbol": "CFA"},
    {"code": "XAF", "name": "Central African CFA Franc", "symbol": "FCFA"},
    {"code": "AED", "name": "UAE Dirham", "symbol": "د.إ"},
    {"code": "SAR", "name": "Saudi Riyal", "symbol": "﷼"},
    {"code": "QAR", "name": "Qatari Riyal", "symbol": "QR"},
    {"code": "KWD", "name": "Kuwaiti Dinar", "symbol": "KD"},
    {"code": "BHD", "name": "Bahraini Dinar", "symbol": "BD"},
    {"code": "OMR", "name": "Omani Rial", "symbol": "OMR"},
    {"code": "TRY", "name": "Turkish Lira", "symbol": "₺"},
    {"code": "SGD", "name": "Singapore Dollar", "symbol": "S$"},
    {"code": "HKD", "name": "Hong Kong Dollar", "symbol": "HK$"},
    {"code": "MYR", "name": "Malaysian Ringgit", "symbol": "RM"},
    {"code": "THB", "name": "Thai Baht", "symbol": "฿"},
    {"code": "IDR", "name": "Indonesian Rupiah", "symbol": "Rp"},
    {"code": "PHP", "name": "Philippine Peso", "symbol": "₱"},
    {"code": "BRL", "name": "Brazilian Real", "symbol": "R$"},
    {"code": "MXN", "name": "Mexican Peso", "symbol": "$"},
]

async def seed_currencies(session):
    for cur in CURRENCIES:
        check_stmt = text("SELECT id FROM currencies WHERE code = :code")
        result = await session.execute(check_stmt, {"code": cur["code"]})

        currency = result.scalar_one_or_none()
        
        if currency is None:
            stmt = text("""
                INSERT INTO currencies (id, code, name, symbol, is_active) 
                VALUES (CAST(:id AS UUID), :code, :name, :symbol, :is_active) 
            """)
            await session.execute(stmt, {
                "id": str(uuid.uuid4()),
                "code": cur["code"],
                "name": cur["name"],
                "symbol": cur["symbol"],
                "is_active": True
            })
    await session.commit()
