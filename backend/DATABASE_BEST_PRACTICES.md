# Database Best Practices

## 🎯 Общие принципы

Все операции с базой данных должны использовать безопасное управление транзакциями через контекстный менеджер `db_transaction` для предотвращения ошибок "current transaction is aborted".

## ✅ Правильный подход

**Используйте `db_transaction` для всех операций с БД:**

```python
from backend.utils.db_helpers import db_transaction

def my_method(self, user_id: int) -> Optional[Dict]:
    """Пример правильного использования транзакций."""
    try:
        with db_transaction(self.db) as cursor:
            cursor.execute(
                """
                SELECT id, email, full_name
                FROM users
                WHERE id = %s
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            # Транзакция автоматически COMMIT при успешном выходе из блока
        
        # Обработка данных вне транзакции
        if row:
            return {"id": row[0], "email": row[1], "full_name": row[2]}
        return None
        
    except Exception as e:
        logger.error(f"[MY-SERVICE] Error: {e}")
        return None
```

### Преимущества `db_transaction`:

1. ✅ **Автоматический ROLLBACK** перед началом каждой транзакции (очистка состояния)
2. ✅ **Автоматический COMMIT** при успешном выполнении
3. ✅ **Автоматический ROLLBACK** при любых ошибках
4. ✅ **Гарантированное закрытие курсоров** (даже при ошибках)
5. ✅ **Предотвращение ошибок** "current transaction is aborted"

## ❌ НЕПРАВИЛЬНО - Избегайте этого:

```python
# ❌ ПЛОХО - Прямая работа с курсорами
def bad_method(self):
    cursor = self.db.cursor()
    try:
        cursor.execute("SELECT ...")
        result = cursor.fetchone()
        self.db.commit()
    except Exception as e:
        self.db.rollback()  # Может оставить транзакцию в aborted состоянии
    finally:
        cursor.close()  # Может не закрыться при ошибке rollback
```

**Проблемы этого подхода:**
- ❌ Транзакция может остаться в состоянии "aborted" после ошибки
- ❌ Последующие запросы будут игнорироваться до явного ROLLBACK
- ❌ Риск утечки ресурсов при ошибках в rollback/close

## 📝 Паттерны использования

### 1. Операции чтения (SELECT)

```python
def get_user(self, user_id: int) -> Optional[Dict]:
    """Безопасное чтение данных."""
    try:
        with db_transaction(self.db) as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cursor.fetchone()
        
        # Обработка результата вне транзакции
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"[SERVICE] Error fetching user: {e}")
        return None
```

### 2. Операции записи (INSERT/UPDATE/DELETE)

```python
def create_user(self, email: str, name: str) -> Optional[int]:
    """Безопасная запись данных."""
    try:
        with db_transaction(self.db) as cursor:
            cursor.execute(
                """
                INSERT INTO users (email, full_name, created_at)
                VALUES (%s, %s, NOW())
                RETURNING id
                """,
                (email, name),
            )
            user_id = cursor.fetchone()[0]
            # Автоматический COMMIT при выходе из блока
        
        return user_id
    except Exception as e:
        logger.error(f"[SERVICE] Error creating user: {e}")
        return None
```

### 3. Несколько операций в одной транзакции

```python
def transfer_funds(self, from_id: int, to_id: int, amount: int) -> bool:
    """Несколько операций в одной транзакции."""
    try:
        with db_transaction(self.db) as cursor:
            # Списание
            cursor.execute(
                "UPDATE accounts SET balance = balance - %s WHERE id = %s",
                (amount, from_id),
            )
            # Зачисление
            cursor.execute(
                "UPDATE accounts SET balance = balance + %s WHERE id = %s",
                (amount, to_id),
            )
            # Все операции в одной транзакции - либо все успешно, либо откат
            # Автоматический COMMIT при успехе
        return True
    except Exception as e:
        logger.error(f"[SERVICE] Transfer failed: {e}")
        return False
```

### 4. Операции с условием (если результат нужен сразу)

```python
def check_and_update(self, user_id: int) -> bool:
    """Проверка с последующим обновлением."""
    try:
        with db_transaction(self.db) as cursor:
            # Проверка
            cursor.execute("SELECT status FROM users WHERE id = %s", (user_id,))
            row = cursor.fetchone()
            
            if not row or row[0] != "active":
                return False  # Ранний выход - транзакция откатится автоматически
            
            # Обновление
            cursor.execute(
                "UPDATE users SET last_action = NOW() WHERE id = %s",
                (user_id,),
            )
            # Автоматический COMMIT при успехе
        return True
    except Exception as e:
        logger.error(f"[SERVICE] Error: {e}")
        return False
```

## 🔄 Когда НЕ использовать db_transaction

**Используйте db_transaction для всех операций**, кроме случаев, когда:
- Вы работаете с SQLAlchemy ORM (он имеет свой менеджер транзакций)
- Вы используете другой уровень абстракции, который уже управляет транзакциями

## 📚 Файлы с примерами

Посмотрите на правильную реализацию в:
- `backend/services/admin_session_service.py` - все методы используют `db_transaction`
- `backend/auth.py` - все методы используют `db_transaction`

## ⚠️ Важные замечания

1. **Всегда обрабатывайте исключения** - `db_transaction` сделает rollback, но вам нужно логировать ошибки
2. **Не делайте операции вне транзакции**, которые зависят от данных внутри транзакции (если только это не постобработка)
3. **Используйте логирование** для отслеживания ошибок:
   ```python
   from backend.logger import get_logger
   logger = get_logger(__name__)
   logger.error(f"[SERVICE] Error: {e}", exc_info=True)
   ```

## 🚀 Чеклист для новых методов

Перед добавлением нового метода работы с БД убедитесь:

- [ ] Используете `from backend.utils.db_helpers import db_transaction`
- [ ] Обернули операции в `with db_transaction(self.db) as cursor:`
- [ ] Добавили обработку исключений с логированием
- [ ] Не вызываете `.cursor()`, `.commit()`, `.rollback()` напрямую
- [ ] Тестировали метод на наличие ошибок

## 📖 Дополнительная информация

- [PostgreSQL Transaction Documentation](https://www.postgresql.org/docs/current/tutorial-transactions.html)
- [psycopg2 Best Practices](https://www.psycopg.org/docs/usage.html#transactions-control)

---

**Запомните: Если вы работаете с БД в этом проекте - всегда используйте `db_transaction`!**

