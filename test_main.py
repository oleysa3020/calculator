import pytest
from unittest.mock import patch, MagicMock
from main import CurrencyConverterApp


@pytest.fixture
def app():
    """Фикстура для создания экземпляра приложения"""
    app = CurrencyConverterApp()
    app.withdraw()
    yield app
    app.destroy()


def test_calculate_loan_success(app):
    """Проверяет правильность вычисления кредита"""
    app.loan_var.set("100000")
    app.loan_time_var.set("12")
    app.annual_interest_var.set("15")

    app.calculate_loan()

    assert "9025.83" in app.monthly_label.cget("text")
    assert "108309.97" in app.loan_sum_label.cget("text")
    assert "8309.97" in app.interest_label.cget("text")


def test_calculate_loan_invalid_loan_amount(app):
    """Проверяет на наличие ошибок, если введена неправильная сумма кредита"""
    app.loan_var.set("-1000")
    app.loan_time_var.set("12")
    app.annual_interest_var.set("15")

    app.log_text.delete("1.0", "end")

    app.calculate_loan()

    log_content = app.log_text.get("1.0", "end")
    assert "Ошибка: Сумма кредита должна быть больше 0." in log_content
    assert "Ежемесячный платеж: 0" in app.monthly_label.cget("text")


@patch("main.get_saved_rate")
def test_convert_success(mock_get_saved_rate, app):
    """Проверяет успешность конвертации"""
    mock_get_saved_rate.return_value = 80.0

    app.loan_var.set("10000")
    app.target_var.set("USD")

    app.convert()

    assert "125.00 USD" in app.result_label.cget("text")


@patch("main.get_saved_rate")
def test_convert_none_rate(mock_get_saved_rate, app):
    """Проверяет конвертацию, когда курс является None (или 0.0)"""
    mock_get_saved_rate.return_value = 0.0

    app.loan_var.set("10000")
    app.target_var.set("USD")
    app.log_text.delete("1.0", "end")

    app.convert()

    log_content = app.log_text.get("1.0", "end")
    assert "Ошибка: Курс для USD не найден." in log_content


@patch("main.get_saved_rate")
def test_convert_exception(mock_get_saved_rate, app):
    """Проверяет обработку исключений (например, ввели букву вместо суммы)"""
    app.loan_var.set("ABCDEF")
    app.target_var.set("USD")
    app.log_text.delete("1.0", "end")

    app.convert()

    log_content = app.log_text.get("1.0", "end")
    assert "Ошибка: Введите сумму кредита цифрами" in log_content


@patch("main.fetch_rates")
@patch("main.save_rate")
def test_update_db_success(mock_save_rate, mock_fetch_rates, app):
    """Проверяет успешность обновления БД"""
    mock_fetch_rates.return_value = {
        "Date": "2026-11-14",
        "Valute": {"USD": {"Value": 90.0}, "EUR": {"Value": 100.0}},
    }

    app.log_text.delete("1.0", "end")
    app.update_db()

    assert mock_save_rate.call_count == 2

    log_content = app.log_text.get("1.0", "end")
    assert "Успешно обновлено 2 валют" in log_content


@patch("main.fetch_rates")
def test_update_db_empty_rates(mock_fetch_rates, app):
    """Проверяет обновление БД пустым списком курсов"""
    mock_fetch_rates.return_value = {}

    app.log_text.delete("1.0", "end")
    app.update_db()

    log_content = app.log_text.get("1.0", "end")
    assert "Ошибка: Не удалось получить данные от API." in log_content
