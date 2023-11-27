from fastapi import FastAPI, HTTPException, Query
from datetime import datetime
import requests

app = FastAPI()

class MutualFundInvestment:
    def __init__(self, scheme_code, purchase_date, start_date, end_date, initial_investment, final_investment):
        self.scheme_code = scheme_code
        self.purchase_date = datetime.strptime(purchase_date, "%Y-%m-%d")
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        self.initial_investment = initial_investment
        self.final_investment = final_investment

    def calculate_units_allotted(self, nav_on_purchase_date):
        units_allotted = self.initial_investment / nav_on_purchase_date
        return units_allotted

    def calculate_units_value(self, units, nav_on_redemption_date):
        units_value = units * nav_on_redemption_date
        return units_value

    def calculate_net_profit(self, units_value_on_redemption):
        net_profit = units_value_on_redemption - self.initial_investment
        return net_profit

    def calculate_profit(self):
        holding_period_years = (self.end_date - self.start_date).days / 365.25
        cagr = (self.final_investment / self.initial_investment) ** (1 / holding_period_years) - 1
        profit = self.initial_investment * (1 + cagr) ** holding_period_years - self.initial_investment
        return profit

def get_nav(api_url, date):
    response = requests.get(f"{api_url}/{date}")
    
    if response.status_code == 200:
        nav_data = response.json()
        return nav_data['data']['nav']
    else:
        raise HTTPException(status_code=response.status_code, detail=f"Error fetching NAV data. Status code: {response.status_code}")

@app.get("/profit")
def calculate_profit(
    scheme_code: str = Query(..., title="Mutual Fund Scheme Code", description="Scheme code of the mutual fund"),
    start_date: str = Query(..., title="Start Date", description="Start date of the investment"),
    end_date: str = Query(..., title="End Date", description="End date of the investment"),
    capital: float = Query(..., title="Capital", description="Initial investment amount")
):
    api_url = f"https://api.mfapi.in/mf/{scheme_code}"

    try:
        nav_on_purchase_date = get_nav(api_url, start_date)
        nav_on_redemption_date = get_nav(api_url, end_date)

        investment = MutualFundInvestment(scheme_code, start_date, start_date, end_date, capital, 0)
        units_allotted = investment.calculate_units_allotted(nav_on_purchase_date)
        units_value_on_redemption = investment.calculate_units_value(units_allotted, nav_on_redemption_date)
        net_profit = investment.calculate_net_profit(units_value_on_redemption)
        profit = investment.calculate_profit()

        return {
            "scheme_code": scheme_code,
            "start_date": start_date,
            "end_date": end_date,
            "initial_investment": capital,
            "units_allotted": units_allotted,
            "units_value_on_redemption": units_value_on_redemption,
            "net_profit": net_profit,
            "profit": profit
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
