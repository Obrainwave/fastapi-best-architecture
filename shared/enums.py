from enum import Enum


class ModuleCode(str, Enum):
    CORE = "core" # This are the core modules that will be available to all plans
    PROCUREMENT = "procurement"
    INVENTORY = "inventory"
    SALES = "sales"
    EMPLOYEE = "employee"
    ATTENDANCE = "attendance"
    PAYROLL = "payroll"
    HR = "hr"
    FIXED_ASSETS = "fixed_assets"
    SNAILPRO = "snailpro"
    POULTRYPRO = "poultrypro"
    FEED_MILL = "feed_mill"
    MANUFACTURING = "manufacturing"
    PROCESSING = "processing"
    REPORTING = "reporting"
    AI_ANALYTICS = "ai_analytics"
    INTEGRATIONS = "integrations"
    ACCOUNTING = "accounting"

class FeatureValueType(str, Enum):
    STRING = "string"
    BOOLEAN = "boolean"
    JSON = "json"

class SubscriptionStatus(str, Enum):
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"

class BillingCycle(str, Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"

class SubscriptionEventType(str, Enum):
    CREATED = "created"
    UPGRADED = "upgraded"
    DOWNGRADED = "downgraded"
    RENEWED = "renewed"
    SUSPENDED = "suspended"
    REINSTATED = "reinstated"
    CANCELLED = "cancelled"

class EntitlementSource(str, Enum):
    PLAN = "plan"
    ADDON = "addon"
    TRIAL = "trial"

class TransactionStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"

class TaxEntityType(str, Enum):
    """Entities across modules that tax rules can be applied to."""

    # Inventory / Products
    PRODUCT = "product"              # A specific product/item
    PRODUCT_CATEGORY = "product_category"  # All items in a category

    # Procurement
    VENDOR = "vendor"                # A specific supplier/vendor
    PURCHASE_ORDER = "purchase_order"
    PURCHASE_ORDER_ITEM = "purchase_order_item"

    # Sales
    CUSTOMER = "customer"            # A specific customer
    SALES_ORDER = "sales_order"
    SALES_ORDER_ITEM = "sales_order_item"
    INVOICE = "invoice"
    INVOICE_ITEM = "invoice_item"

    # Services / Transactions
    SERVICE = "service"              # A billable service
    PAYMENT = "payment"

    # Organization & Locations
    ORGANIZATION = "organization"    # Org-level default tax rule
    WAREHOUSE = "warehouse"          # Warehouse-specific tax (e.g. different state/region)
    FARM = "farm"                    # Farm-level tax rules

    # HR / Payroll
    EMPLOYEE = "employee"
    PAYROLL_COMPONENT = "payroll_component"  # e.g. allowances, deductions

    # Fixed Assets
    ASSET = "asset"                  # Fixed asset acquisitions or disposals

    # Manufacturing / Processing
    PRODUCTION_ORDER = "production_order"
    RAW_MATERIAL = "raw_material"
