def style_days_open(days: int, threshold: int = 50) -> str:
    return "red" if days > threshold else "green"

def style_est_profit(option_type: str, strategy: str, current: float, entry: float) -> str:
    option_type = option_type.lower()
    strategy = strategy.lower()

    if option_type == "put" and "venda" in strategy:
        return "green" if current < entry else "red"
    
    if option_type == "call" and "compra" in strategy:
        return "green" if current > entry else "red"

    return "default"

def format_operation_strategy(operation: str):
    return operation.replace("_", " ")