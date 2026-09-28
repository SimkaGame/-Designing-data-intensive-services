FROM python:3.12-slim

WORKDIR ./

# Копируем и устанавливаем зависимости отдельно (кеширование слоёв)
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY ./main.py .

# Открываем порт (документация)
EXPOSE 8000

# Запускаем Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]