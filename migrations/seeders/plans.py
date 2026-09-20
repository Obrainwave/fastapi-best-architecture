from app.models.plan import Plan
from app.models.plan_feature import PlanFeature
from app.shared.enums import FeatureValueType, ModuleCode
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def seed_plans(session: AsyncSession):
    # Fetch existing plans
    result = await session.execute(select(Plan))
    existing_plans = {plan.code: plan for plan in result.scalars().all()}
    
    print("Seeding plans and features...")
    
    # 1. Define Plans and their Features
    plan_defs = {
        "free": {
            "name": "Free Plan",
            "monthly_price": 0.00,
            "yearly_price": 0.00,
            "discount_percent": 0.0,
            "tier_level": 1,
            "is_active": True,
            "is_default": True,
            "description": "The perfect plan for getting started.",
            "features": [
                {"key": "modules", "type": FeatureValueType.JSON, "value": [ModuleCode.CORE.value, ModuleCode.INVENTORY.value, ModuleCode.EMPLOYEE.value, ]},
                {"key": "max_users", "type": FeatureValueType.JSON, "value": 1},
                {"key": "ai_analytics_credits", "type": FeatureValueType.JSON, "value": 0},
                {"key": "priority_support", "type": FeatureValueType.BOOLEAN, "value": False}
            ]
        },
        "premium": {
            "name": "Premium Plan",
            "monthly_price": 5000.00,
            "yearly_price": 50000.00,
            "discount_percent": 10.0,
            "tier_level": 2,
            "is_active": True,
            "is_default": False,
            "description": "Advanced features for growing businesses.",
            "features": [
                {"key": "modules", "type": FeatureValueType.JSON, "value": [ModuleCode.CORE.value, ModuleCode.INVENTORY.value, ModuleCode.SALES.value, ModuleCode.EMPLOYEE.value, ModuleCode.ATTENDANCE.value, ModuleCode.ACCOUNTING.value, ModuleCode.PROCUREMENT.value, ModuleCode.REPORTING.value]},
                {"key": "max_users", "type": FeatureValueType.JSON, "value": 10},
                {"key": "ai_analytics_credits", "type": FeatureValueType.JSON, "value": 100},
                {"key": "priority_support", "type": FeatureValueType.BOOLEAN, "value": True}
            ]
        },
        "enterprise": {
            "name": "Enterprise Plan",
            "monthly_price": 20000.00,
            "yearly_price": 200000.00,
            "discount_percent": 10.0,
            "tier_level": 3,
            "is_active": True,
            "is_default": False,
            "description": "Maximum power and unlimited potential.",
            "features": [
                {"key": "modules", "type": FeatureValueType.JSON, "value": [m.value for m in ModuleCode]},
                {"key": "max_users", "type": FeatureValueType.JSON, "value": 500},
                {"key": "ai_analytics_credits", "type": FeatureValueType.JSON, "value": 10000},
                {"key": "priority_support", "type": FeatureValueType.BOOLEAN, "value": True}
            ]
        }
    }
    
    plans_to_add = []
    
    # Ensure all plans exist and have correct pricing
    for code, data in plan_defs.items():
        if code not in existing_plans:
            plan = Plan(
                code=code,
                name=data["name"],
                monthly_price=data.get("monthly_price", 0.0),
                yearly_price=data.get("yearly_price", 0.0),
                discount_percent=data.get("discount_percent", 0.0),
                tier_level=data["tier_level"],
                is_active=data["is_active"],
                is_default=data["is_default"],
                description=data["description"]
            )
            plans_to_add.append(plan)
            existing_plans[code] = plan
        else:
            plan = existing_plans[code]
            plan.name = data["name"]
            plan.monthly_price = data.get("monthly_price", 0.0)
            plan.yearly_price = data.get("yearly_price", 0.0)
            plan.discount_percent = data.get("discount_percent", 0.0)
            plan.tier_level = data["tier_level"]
            plan.description = data.get("description", plan.description)
            
    if plans_to_add:
        session.add_all(plans_to_add)
        await session.flush()
        
    features_to_add = []
    
    # Check and add features for each plan
    for code, data in plan_defs.items():
        plan = existing_plans[code]
        
        # Get existing feature keys for this specific plan
        feat_result = await session.execute(
            select(PlanFeature.feature_key).where(PlanFeature.plan_id == plan.id)
        )
        existing_feature_keys = set(feat_result.scalars().all())
        
        for feat in data["features"]:
            if feat["key"] not in existing_feature_keys:
                features_to_add.append(
                    PlanFeature(
                        plan_id=plan.id,
                        feature_key=feat["key"],
                        value_type=feat["type"],
                        value=feat["value"]
                    )
                )
                
    if features_to_add:
        session.add_all(features_to_add)

    await session.commit()
    print("Successfully updated and seeded plans and features.")
