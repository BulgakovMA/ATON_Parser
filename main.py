import socket
import uvicorn
from currency import Currency
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def read_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})


@app.post("/get_currency")
async def get_currency(request: Request):
    form = await request.form()
    country = form.get('country')
    start_day = int(form.get('start_day'))
    start_month = int(form.get('start_month'))
    start_year = int(form.get('start_year'))
    end_day = int(form.get('end_day'))
    end_month = int(form.get('end_month'))
    end_year = int(form.get('end_year'))

    currency_instance = Currency(country, start_day, start_month, start_year,
                                 end_day, end_month,
                                 end_year)
    currency_rates_data = currency_instance.get_currency_rates()
    currency_list_data = currency_instance.get_currency_list()
    plot_data = currency_instance.plot_currency_changes()

    return templates.TemplateResponse("currency.html", {"request": request,
                                                        "currency_rates_data": currency_rates_data,
                                                        "currency_list_data": currency_list_data,
                                                        "plot_data": plot_data})


if __name__ == "__main__":
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    uvicorn.run(app, host=ip_address, port=8000)
