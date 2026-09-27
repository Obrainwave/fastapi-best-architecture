import enum


class VideoStatus(str, enum.Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    

class WalletTransactionType(str, enum.Enum):
    CREDIT = "credit"
    DEBIT = "debit"


class PaymentPurpose(str, enum.Enum):
    PURCHASE = "purchase"
    EXTENSION = "extension"
    WALLET_TOPUP = "wallet_topup"


class PaymentStatus(str, enum.Enum):
    CREATED = "created"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    
class PaymentMethod(str, enum.Enum):
    WALLET = "wallet"
    CARD = "card"
    

class PurchaseStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    REFUNDED = "refunded"