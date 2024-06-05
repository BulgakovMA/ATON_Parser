import requests
import sqlite3
import plotly.express as px
import pandas as pd
from bs4 import BeautifulSoup


class Currency:
    def __init__(self, country, start_day, start_month, start_year, end_day,
                 end_month, end_year):
        self.country = country
        self.start_day = start_day
        self.start_month = start_month
        self.start_year = start_year
        self.end_day = end_day
        self.end_month = end_month
        self.end_year = end_year
        self.currency = {"Доллар США": 52148, "Евро": 52170,
                         "Фунт стерлингов": 52146,
                         "Швейцарский франк": 52133,
                         "Австралийский доллар": 52182,
                         "Азербайджанский манат": 52180,
                         "Армянский драм": 52187,
                         "Белорусский рубль": 52200, "Болгарский лев": 52197,
                         "Бразильский реал": 52174, "Венгерский форинт": 52236,
                         "Вона Республики Корея": 52074,
                         "Вьетнамский донг": 52124,
                         "Гонконгский доллар": 52235, "Грузинский лари": 52172,
                         "Датская крона": 52215, "Дирхам ОАЭ": 52139,
                         "Египетский фунт": 52145, "Индийская рупия": 52238,
                         "Индонезийская рупия": 52239,
                         "Казахстанский тенге": 52247,
                         "Канадский доллар": 52202, "Катарский риал": 52115,
                         "Киргизский сом": 52075,
                         "Китайский юань Жэньминьби": 52207,
                         "Латвийский лат": 52079, "Литовский лит": 52082,
                         "Молдавский лей": 52093,
                         "Новозеландский доллар": 52103,
                         "Новый туркменский манат": 52141,
                         "Норвежская крона": 52106,
                         "Польский злотый": 52173, "Румынский лей": 52157,
                         "СДР (спец. прав заим-я)": 52164,
                         "Сербский динар": 52178,
                         "Сингапурский доллар": 52122,
                         "Таджикский сомони": 52168,
                         "Тайландский бат": 52136, "Турецкая лира": 52158,
                         "Узбекский сум": 52150, "Украинская гривна": 52171,
                         "Чешская крона": 52214, "Шведская крона": 52132,
                         "Эстонская крона": 52220,
                         "Южноафриканский рэнд": 52127,
                         "Японская йена": 52246}
        self.connection_to_db()
        self.get_currency_codes()

    def connection_to_db(self):
        self.connection = sqlite3.connect('Currencies.db')
        self.cursor = self.connection.cursor()
        self.create_currency_list_table()

    def create_currency_list_table(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS Currency_list (
        id INTEGER PRIMARY KEY,
        country TEXT NOT NULL,
        currency TEXT NOT NULL,
        code INTEGER,
        number INTEGER
        )
        ''')
        self.create_currency_rates_table()

    def create_currency_rates_table(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS Currency_rates (
        id INTEGER PRIMARY KEY,
        date TEXT NOT NULL,
        count INTEGER,
        course INTEGER,
        change INTEGER
        )
        ''')

    def get_currency_codes(self):
        url = "https://www.iban.ru/currency-codes"
        page = requests.get(url)
        soup = BeautifulSoup(page.text, "lxml")
        line = soup.find(
            class_="table table-bordered downloads tablesorter").find(
            "tbody")
        self.currencies = []
        for j in line:
            if hasattr(j, 'find_all'):
                td = j.find_all("td")
                currency_info = {
                    "Страна": td[0].text.strip(),
                    "Валюта": td[1].text.strip(),
                    "Код": td[2].text.strip(),
                    "Номер": td[3].text.strip()
                }
                self.currencies.append(currency_info)
        self.add_currency_list_to_db()

    def add_currency_list_to_db(self):
        query = "INSERT INTO Currency_list (country, currency, code, number) VALUES (?, ?, ?, ?)"
        for currency_info in self.currencies:
            self.cursor.execute(query, (
                currency_info['Страна'], currency_info['Валюта'],
                currency_info['Код'], currency_info['Номер']))
        self.connection.commit()
        self.get_data_page()

    def get_data_page(self):
        country_code = self.currency.get(self.country)
        if country_code is None:
            return {"error": "Country not found in currency list"}

        url = f"https://www.finmarket.ru/currency/rates/?id=10148&pv=1&cur={country_code}&bd={self.start_day}&bm={self.start_month}&by={self.start_year}&ed={self.end_day}&em={self.end_month}&ey={self.end_year}&x=23&y=8#archive"
        self.page = requests.get(url)
        soup = BeautifulSoup(self.page.text, "lxml")
        line = soup.find(class_="center_column").find("tbody")
        self.data = []
        for j in line:
            td = j.find_all("td")
            self.data.append({
                "Дата": td[0].text,
                "Кол-во": td[1].text,
                "Курс": td[2].text,
                "Изменение": td[3].text
            })
        return self.check_data_in_db()

    def add_data_to_db(self, row):
        query = "INSERT INTO Currency_rates (date, count, course, change) VALUES (?, ?, ?, ?)"
        self.cursor.execute(query, (
            row['Дата'], row['Кол-во'], row['Курс'], row['Изменение']))
        self.connection.commit()

    def update_data_in_db(self, row):
        query = "UPDATE Currency_rates SET date = ?, count = ? WHERE course = ? AND change = ?"
        self.cursor.execute(query, (
            row['Дата'], row['Кол-во'], row['Курс'], row['Изменение']))
        self.connection.commit()

    def get_currency_rates(self):
        self.cursor.execute("SELECT * FROM Currency_rates")
        data_rates = self.cursor.fetchall()
        self.get_currency_list()
        return data_rates

    def get_currency_list(self):
        self.cursor.execute("SELECT * FROM Currency_list")
        data_list = self.cursor.fetchall()
        self.plot_currency_changes()
        return data_list

    def check_data_in_db(self):
        query = f"SELECT * FROM Currency_rates WHERE date = ? AND count = ? AND course = ? AND change = ?"
        for row in self.data:
            self.cursor.execute(query, (
                row['Дата'], row['Кол-во'], row['Курс'], row['Изменение']))
            result = self.cursor.fetchone()
            if result is None:
                self.add_data_to_db(row)
            else:
                self.update_data_in_db(row)
        self.get_currency_rates()

    def plot_currency_changes(self):
        self.cursor.execute("SELECT date, course, change FROM Currency_rates")
        data = self.cursor.fetchall()
        df = pd.DataFrame(data, columns=['Дата', 'Курс', 'Изменение'])
        fig = px.line(df, x='Изменение', y='Дата',
                      title='Изменение валютного курса', orientation='h')
        fig.write_image('assets/plot.png')
