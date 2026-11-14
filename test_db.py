import pytest
import sqlite3
import tempfile
import os
from unittest.mock import patch

from db import init_db, save_rate, get_saved_rate, DB_NAME


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()

    original_db_name = DB_NAME

    with patch('db.DB_NAME', temp_file.name):
        init_db()
        yield temp_file.name

    try:
        os.unlink(temp_file.name)
    except (PermissionError, FileNotFoundError):
        pass


@pytest.fixture
def sample_data():
    """Sample data for testing"""
    return {
        'id': 1,
        'currency': 'USD',
        'rate': 1.0
    }


def test_init_db_creates_table(temp_db):
    """Проверяет создание таблицы"""
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rates';")
        result = cursor.fetchone()

        assert result is not None
        assert result[0] == 'rates'


def test_save_rate_new_record(temp_db, sample_data):
    """Проверяет добавление новой записи"""
    save_rate(
        sample_data['id'],
        sample_data['currency'],
        sample_data['rate'],
        "2026-11-14 12:00:00"
    )

    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, currency, rate FROM rates WHERE currency = ?', (sample_data['currency'],))
        row = cursor.fetchone()

    assert row is not None
    assert row[0] == sample_data['id']
    assert row[1] == sample_data['currency']
    assert row[2] == sample_data['rate']

def test_save_rate_update_existing(temp_db, sample_data):
    """Проверяет обновление существующего поля"""
    save_rate(
        sample_data['id'],
        sample_data['currency'],
        sample_data['rate'],
        "2026-11-14 12:00:00"
    )

    save_rate(
        sample_data['id'],
        sample_data['currency'],
        2.5,
        "2026-11-14 12:00:00"
    )

    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT rate FROM rates WHERE currency = ?', (sample_data['currency'],))
        row = cursor.fetchone()

        cursor.execute('SELECT COUNT(*) FROM rates')
        count = cursor.fetchone()[0]

    assert row is not None
    assert row[0] == 2.5
    assert count == 1

def test_save_rate_date_format(temp_db, sample_data):
    """Проверяет формат даты"""
    date_str = "2026-11-14 15:30:00"

    save_rate(
        sample_data['id'],
        sample_data['currency'],
        sample_data['rate'],
        date_str
    )

    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT fetched_at FROM rates WHERE currency = ?', (sample_data['currency'],))
        row = cursor.fetchone()

    assert row is not None
    assert row[0] == date_str

def test_save_rate_multiple_currencies(temp_db):
    """Проверяет разный набор валют"""
    save_rate(1, 'USD', 90.0, "2026-11-14 12:00:00")
    save_rate(2, 'EUR', 100.0, "2026-11-14 12:00:00")

    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM rates')
        count = cursor.fetchone()[0]

        cursor.execute("SELECT rate FROM rates WHERE currency = 'USD'")
        usd_rate = cursor.fetchone()[0]

    assert count == 2
    assert usd_rate == 90.0


def test_save_rate_edge_cases(temp_db):
    """Проверяет разные диапазоны значений"""
    save_rate(1, 'BIG', 999999999.99, "2026-11-14 12:00:00")
    save_rate(2, 'SMALL', 0.0001, "2026-11-14 12:00:00")
    save_rate(3, 'ZERO', 0.0, "2026-11-14 12:00:00")
    save_rate(4, 'NEGATIVE', -15.5, "2026-11-14 12:00:00")

    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT rate FROM rates WHERE currency = 'BIG'")
        big_rate = cursor.fetchone()[0]

        cursor.execute("SELECT rate FROM rates WHERE currency = 'SMALL'")
        small_rate = cursor.fetchone()[0]

        cursor.execute("SELECT rate FROM rates WHERE currency = 'ZERO'")
        zero_rate = cursor.fetchone()[0]

        cursor.execute("SELECT rate FROM rates WHERE currency = 'NEGATIVE'")
        negative_rate = cursor.fetchone()[0]

    assert big_rate == 999999999.99
    assert small_rate == 0.0001
    assert zero_rate == 0.0
    assert negative_rate == -15.5

def test_save_rate_database_connection_error(sample_data):
    """Проверяет разрыв соединения с БД"""
    with patch('db.sqlite3.connect') as mock_connect:
        mock_connect.side_effect = sqlite3.OperationalError("Database connection failed")

        with pytest.raises(sqlite3.OperationalError):
            save_rate(
                sample_data['id'],
                sample_data['currency'],
                sample_data['rate'],
                "2026-11-14 12:00:00"
            )


def test_save_rate_commit_error(sample_data):
    """Проверяет ошибку при коммите данных в БД"""
    with patch('db.sqlite3.connect') as mock_connect:
        mock_conn = mock_connect.return_value

        mock_cursor = mock_conn.cursor.return_value

        mock_conn.__enter__.return_value = mock_conn

        mock_conn.commit.side_effect = sqlite3.OperationalError("Commit failed")

        with pytest.raises(sqlite3.OperationalError):
            save_rate(
                sample_data['id'],
                sample_data['currency'],
                sample_data['rate'],
                "2026-11-14 12:00:00"
            )

def test_save_rate_parameter_types(temp_db):
    """Проверяет разные типы данных параметров"""
    save_rate(
        id=1,
        target_currency="USD",
        rate=92.5,
        date_str="2026-11-14"
    )

    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, currency, rate, fetched_at FROM rates WHERE currency = ?', ("USD",))
        row = cursor.fetchone()

    assert row is not None
    assert isinstance(row[0], int)
    assert isinstance(row[1], str)
    assert isinstance(row[2], float)
    assert isinstance(row[3], str)
    assert row[2] == 92.5


def test_save_rate_sql_injection_protection(temp_db):
    """Проверяет защиту на SQL-инъекции"""
    malicious_currency = "USD'; DROP TABLE rates; --"

    save_rate(1, malicious_currency, 1.0, "2026-11-14 12:00:00")

    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT currency FROM rates WHERE id = 1')
        row = cursor.fetchone()

    assert row is not None
    assert row[0] == malicious_currency

def test_get_saved_rate_success(temp_db, sample_data):
    """Проверяет успешность получения данных из БД"""
    save_rate(sample_data['id'], sample_data['currency'], sample_data['rate'], "2026-11-14")
    rate = get_saved_rate(sample_data['currency'])
    assert rate == sample_data['rate']

def test_get_saved_rate_default_currency(temp_db):
    """Проверяет получение курса стандартной валюты"""
    save_rate(1, 'USD', 92.5, "2026-11-14")
    rate = get_saved_rate('USD')
    assert rate == 92.5

def test_get_saved_rate_nonexistent_currency(temp_db):
    """Проверяет получение несуществующей валюты"""
    rate = get_saved_rate('XYZ')
    assert rate == 0.0

def test_get_saved_rate_empty_database(temp_db):
    """Проверяет получение данных из пустой БД"""
    rate = get_saved_rate('USD')
    assert rate == 0.0


def test_get_saved_rate_multiple_currencies(temp_db):
    """Проверяет получение множества валют"""
    save_rate(1, 'USD', 90.0, "2026-11-14")
    save_rate(2, 'EUR', 100.0, "2026-11-14")

    usd_rate = get_saved_rate('USD')
    eur_rate = get_saved_rate('EUR')

    assert usd_rate == 90.0
    assert eur_rate == 100.0


def test_get_saved_rate_case_sensitivity(temp_db):
    """Проверяет чувствительность написания параметров"""
    save_rate(1, 'USD', 90.0, "2026-11-14")

    rate = get_saved_rate('usd')

    assert rate == 0.0


def test_get_saved_rate_sql_injection_protection(temp_db):
    """Проверяет защиту на SQL-инъекции при получении"""
    save_rate(1, 'USD', 90.0, "2026-11-14")

    malicious = "USD' OR '1'='1"
    rate = get_saved_rate(malicious)

    assert rate == 0.0


def test_get_saved_rate_database_connection_error():
    """Проверяет разрыв соединения с БД"""
    with patch('db.sqlite3.connect') as mock_connect:
        mock_connect.side_effect = sqlite3.OperationalError("Connection failed")

        with pytest.raises(sqlite3.OperationalError):
            get_saved_rate('USD')