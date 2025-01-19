# Користиме Python 3.9 како основна слика
FROM python:3.9-slim

# Поставување на работната директорија
WORKDIR /app

# Копирање на зависностите
COPY requirements.txt requirements.txt

# Инсталирање на зависностите
RUN pip install --no-cache-dir -r requirements.txt

# Копирање на целиот проект
COPY . .

# Експонирање на портата (пример: 5003)
EXPOSE 5003

# Стартување на апликацијата
CMD ["python", "app.py"]
