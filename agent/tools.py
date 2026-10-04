import asyncio

class Tool:
    def __init__(self, name, func, is_state_modifying=False, schema=None, required=None):
        self.name = name
        self.func = func
        self.is_state_modifying = is_state_modifying
        self.schema = schema or {}
        self.required = required or []

    def validate_args(self, args):
        for req in self.required:
            if req not in args:
                return False, f"Missing required argument: {req}"
        for key, value in args.items():
            if key in self.schema:
                expected_type = self.schema[key]
                if expected_type == "string" and not isinstance(value, str):
                    return False, f"Argument {key} must be string"
                if expected_type == "number" and not isinstance(value, (int, float)):
                    return False, f"Argument {key} must be number"
                if expected_type == "integer" and not isinstance(value, int):
                    return False, f"Argument {key} must be integer"
                if expected_type == "boolean" and not isinstance(value, bool):
                    return False, f"Argument {key} must be boolean"
        return True, ""

    async def execute(self, **kwargs):
        return await self.func(**kwargs)

class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register(self, name, is_state_modifying=False, schema=None, required=None):
        def decorator(func):
            self.tools[name] = Tool(name, func, is_state_modifying, schema, required)
            return func
        return decorator

    def get_tool(self, name):
        return self.tools.get(name)

registry = ToolRegistry()

# ==========================================
# EXTENSION USE CASE TOOL
# ==========================================
@registry.register(
    name="navigate", 
    is_state_modifying=True, 
    schema={"destination": "string"}, 
    required=["destination"]
)
async def navigate(destination: str, **kwargs):
    await asyncio.sleep(0.5)
    return {"status": "routing", "destination": destination, "eta": "45 mins"}

# ==========================================
# FDB-v3 MOCK APIS
# ==========================================

# --- Travel & Identity ---
@registry.register(name="search_flights", is_state_modifying=False, schema={"destination": "string", "date": "string"}, required=["destination", "date"])
async def search_flights(destination: str, date: str, **kwargs):
    await asyncio.sleep(0.2)
    return {"status": "success", "flights": [{"flight_id": "FL123", "destination": destination, "date": date, "price": 450.0}]}

@registry.register(name="book_flight", is_state_modifying=True, schema={"passenger_name": "string", "flight_id": "string"}, required=["passenger_name"])
async def book_flight(passenger_name: str, flight_id: str = "FL123", **kwargs):
    await asyncio.sleep(0.2)
    return {"status": "success", "booking_ref": "B789", "passenger": passenger_name}

@registry.register(name="update_identity_doc", is_state_modifying=True, schema={"doc_type": "string", "doc_number": "string"}, required=["doc_type", "doc_number"])
async def update_identity_doc(doc_type: str, doc_number: str, **kwargs):
    await asyncio.sleep(0.2)
    return {"status": "success", "updated_doc": doc_type, "masked_number": doc_number[-4:]}

# --- Finance & Billing ---
@registry.register(name="get_card_benefits", is_state_modifying=False, schema={"card_type": "string"}, required=["card_type"])
async def get_card_benefits(card_type: str, **kwargs):
    await asyncio.sleep(0.2)
    return {"status": "success", "card_type": card_type, "benefits": ["2% Cashback", "No Foreign Transaction Fee"]}

@registry.register(name="get_exchange_rate", is_state_modifying=False, schema={"amount": "number", "from_currency": "string", "to_currency": "string"}, required=["amount", "from_currency", "to_currency"])
async def get_exchange_rate(amount: float, from_currency: str, to_currency: str, **kwargs):
    await asyncio.sleep(0.2)
    rate = 1.1 if from_currency == "EUR" else 0.9
    return {"status": "success", "converted_amount": float(amount) * rate, "rate": rate}

@registry.register(name="modify_autopay", is_state_modifying=True, schema={"bill_type": "string", "source_account": "string"}, required=["bill_type", "source_account"])
async def modify_autopay(bill_type: str, source_account: str, **kwargs):
    await asyncio.sleep(0.2)
    return {"status": "success", "autopay_enabled": True, "bill": bill_type, "source": source_account}

# --- Housing & Location ---
@registry.register(name="search_apartments", is_state_modifying=False, schema={"city": "string", "bedrooms": "integer", "max_price": "number"}, required=["city", "bedrooms", "max_price"])
async def search_apartments(city: str, bedrooms: int, max_price: float, **kwargs):
    await asyncio.sleep(0.2)
    return {"status": "success", "city": city, "results": [{"id": "APT1", "price": max_price - 100, "beds": bedrooms}]}

@registry.register(name="calculate_commute", is_state_modifying=False, schema={"origin_address": "string", "destination_address": "string", "mode": "string"}, required=["origin_address", "destination_address"])
async def calculate_commute(origin_address: str, destination_address: str, mode: str = "driving", **kwargs):
    await asyncio.sleep(0.2)
    return {"status": "success", "duration_mins": 25, "mode": mode}

@registry.register(name="update_search_filter", is_state_modifying=True, schema={"filter_name": "string", "value": "string"}, required=["filter_name", "value"])
async def update_search_filter(filter_name: str, value: str, **kwargs):
    await asyncio.sleep(0.2)
    return {"status": "success", "filter_updated": filter_name, "new_value": value}

# --- E-Commerce Support ---
@registry.register(name="track_order", is_state_modifying=False, schema={"order_id": "string"}, required=["order_id"])
async def track_order(order_id: str, **kwargs):
    await asyncio.sleep(0.2)
    return {"status": "success", "order_id": order_id, "shipping_status": "Out for delivery"}

@registry.register(name="search_products", is_state_modifying=False, schema={"query": "string", "max_price": "number"}, required=["query"])
async def search_products(query: str, max_price: float = None, **kwargs):
    await asyncio.sleep(0.2)
    price = max_price - 10 if max_price else 99.99
    return {"status": "success", "products": [{"product_id": "PROD1", "name": f"{query} Premium", "price": price}]}

@registry.register(name="add_to_cart", is_state_modifying=True, schema={"product_id": "string", "quantity": "integer"}, required=["product_id"])
async def add_to_cart(product_id: str, quantity: int = 1, **kwargs):
    await asyncio.sleep(0.2)
    return {"status": "success", "product_id": product_id, "quantity": quantity}
