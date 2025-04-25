def style_days_open(days: int, threshold: int = 50) -> str:
    return "red" if days > threshold else "green"

def style_est_profit(option_type: str, strategy: str, current: float, entry: float) -> str:
    if option_type.lower() == "put" and current < entry and "venda" in strategy:
        return "green"

    # if option_type.lower() == "call" and current > entry and "compra" in strategy:
    #     return "green"
        

    return "default"
