import tkinter as tk
from tkinter import ttk

from db import init_db, get_saved_rate, save_rate
from api import fetch_rates

class CurrencyConverterApp(tk.Tk):
    def __init__(self)->None:
        super().__init__()
        self.title ('Конвертер валют')
        self.geometry('600x600')
        self.create_widgets()
        init_db()


    def create_widgets(self)->None:
        self.loan_var = tk.StringVar()
        loan_label = ttk.Label(self, text='Сумма кредита')
        loan_label.pack()
        loan_entry = ttk.Entry(self, textvariable=self.loan_var)
        loan_entry.pack()

        self.loan_time_var = tk.StringVar()
        time_label = ttk.Label(self, text='Срок кредита')
        time_label.pack()
        time_entry = ttk.Entry(self, textvariable=self.loan_time_var)
        time_entry.pack()

        self.annual_interest_var = tk.StringVar()
        annual_interest_label = ttk.Label(self, text='Процентная ставка')
        annual_interest_label.pack()
        annual_interest_entry = ttk.Entry(self, textvariable=self.annual_interest_var)
        annual_interest_entry.pack()

        button_credit = tk.Button(self, text='Рассчитать', command=self.calculate_loan)
        button_credit.pack()

        self.monthly_label = ttk.Label(self, text=f'Ежемесячный платеж: 0')
        self.monthly_label.pack()

        self.loan_sum_label = ttk.Label(self, text=f'Сумма всех платежей: 0')
        self.loan_sum_label.pack()

        self.interest_label = ttk.Label(self, text=f'Начисленные проценты: 0')
        self.interest_label.pack()

        self.base_var = tk.StringVar(value="RUB")
        base_label = ttk.Label(self, text='Базовая валюта: RUB')
        base_label.pack()

        self.target_var = tk.StringVar()
        self.target_entry = ttk.Combobox(self, textvariable=self.target_var)
        self.target_entry['values'] = ('USD', 'EUR', 'GBP', 'CNY')
        target_label = ttk.Label(self, text='Целевая валюта: ')
        target_label.pack()
        self.target_entry.pack()

        button_convert = tk.Button(self, text='Конвертировать', command=self.convert)
        button_convert.pack()

        self.result_label = ttk.Label(self, text=f'Результат конвертации: 0')
        self.result_label.pack()

        button_update = tk.Button(self, text='Обновить курсы', command=self.update_db)
        button_update.pack()

        self.log_text = tk.Text(self, height=5, width=40)
        self.log_text.pack()

    def log(self, message: str) -> None:
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def is_loan_invalid(self, value: float, message: str) -> bool:
        if value <= 0:
            self.log(message)
            return True

        return False

    def calculate_loan(self) -> None:
        loan_str = self.loan_var.get()
        months_str = self.loan_time_var.get()
        annual_str = self.annual_interest_var.get()

        try:
            loan = float(loan_str)
            months = float(months_str)
            annual_interest = float(annual_str)
        except ValueError:
            self.log("Ошибка: Введите числовые значения во все поля.")
            return

        if self.is_loan_invalid(loan, "Ошибка: Сумма кредита должна быть больше 0."):
            return
        if self.is_loan_invalid(months, "Ошибка: Срок кредита должен быть больше 0."):
            return
        if self.is_loan_invalid(annual_interest, "Ошибка: Процентная ставка должна быть больше 0."):
            return

        monthly_rate = annual_interest / 12 / 100

        if monthly_rate == 0:
            monthly_payment = loan / months
        else:
            monthly_payment = loan * (monthly_rate / (1 - (1 + monthly_rate) ** (-months)))

        total_sum = monthly_payment * months
        interest = total_sum - loan

        self.monthly_label.config(text=f'Ежемесячный платеж: {monthly_payment:.2f} руб.')
        self.loan_sum_label.config(text=f'Сумма всех платежей: {total_sum:.2f} руб.')
        self.interest_label.config(text=f'Начисленные проценты: {interest:.2f} руб.')

        self.log("Расчет кредита выполнен успешно.")

    def convert(self) -> None:
        try:
            amount = float(self.loan_var.get())
        except ValueError:
            self.log("Ошибка: Введите сумму кредита цифрами для конвертации.")
            return

        target_currency = self.target_var.get()
        if not target_currency:
            self.log("Ошибка: Выберите целевую валюту.")
            return

        rate = get_saved_rate(target_currency)

        if rate == 0.0:
            self.log(f"Ошибка: Курс для {target_currency} не найден. Обновите базу данных.")
            return

        result = amount / rate

        self.result_label.config(text=f'Результат конвертации: {result:.2f} {target_currency}')
        self.log(f"Конвертация выполнена: {amount} RUB -> {result:.2f} {target_currency}")

    def update_db(self) -> None:
        self.log("Начинаем обновление курсов валют...")

        data = fetch_rates()

        if not data or 'Valute' not in data:
            self.log("Ошибка: Не удалось получить данные от API.")
            return

        date_str = data['Date']

        currencies = data['Valute']
        count = 0

        for currency_code, info in currencies.items():
            rate_value = info['Value']

            save_rate(count + 1, currency_code, rate_value, date_str)
            count += 1

        self.log(f"Успешно обновлено {count} валют. Дата: {date_str}")

if __name__ == '__main__':
    app = CurrencyConverterApp()
    app.mainloop()



