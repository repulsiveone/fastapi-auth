# FastAPI Auth API 🔑

Этот проект представляет собой API авторизации, реализованный с использованием FastAPI. Он предоставляет возможности регистрации, аутентификации и управления пользователями. Вы можете использовать этот проект как через HTTP API, так и в качестве библиотеки в вашем Python-коде.

## Установка и использование библиотеки 

:gear:  В разработке :gear:

## Использование через HTTP

В проекте используется аутентификация на основе JWT (JSON Web Tokens). JWT — это стандарт для создания токенов доступа, которые позволяют безопасно передавать информацию между клиентом и сервером.

Access Token: Короткоживущий токен, который используется для доступа к защищенным ресурсам.  
Access Token хранится на стороне клиента в localStorage
```
localStorage.setItem('access_token', accessToken);
```

Для отправки запросов на защищенные эндпоинты необходимо передавать Access Token:
```
headers: {
        'Authorization': `Bearer ${token}`,
    },
```

Refresh Token: Долгоживущий токен, который используется для получения нового Access Token после истечения его срока действия.

### Аутентификация пользователя

### Пример на JavaScript
```
// Функция для аутентификации
async function login(username, password) {
    const response = await fetch('http://localhost:8002/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            username: username,
            password: password,
        }),
    });

    if (!response.ok) {
        throw new Error('Ошибка при аутентификации');
    }

    const data = await response.json();
    const accessToken = data.access_token;

    // Сохраняем access_token в localStorage
    localStorage.setItem('access_token', accessToken);

    return accessToken;
}
```

### Использование ролей для ограничения доступа:
```
@router.post('/admin')
async def admin(_ = Depends(require_role("admin"))):
```
Функия require_role используется для проверки, соответствует ли роль пользователя.  
По умолчанию создается три роли:  
-admin  
-moderator  
-user

## Запуск с помощью Docker
Для начала необходимо настроить файл .env. 

Создайте файл .env в корне вашего проекта и заполните переменными.
```
POSTGRES_USER=...
POSTGRES_PASSWORD=...
POSTGRES_DB=...
# обязательно использовать асинхронную базу данных
DATABASE_URL=...
BROKER_URL=...

JWT_SECRET_KEY=...
JWT_REFRESH_SECRET_KEY=...
```
Для удобства развертывания проекта используется Docker. Чтобы запустить проект, выполните:
```
docker-compose up -d --build
```
После запуска контейнера API будет доступен по адресу: http://localhost:8002

## Тестирование
В проекте используются автоматические тесты для проверки корректности работы API. Тесты написаны с использованием pytest-asyncio и охватывают основные сценарии использования.  
Чтобы запустить тесты, выполните следующую команду в корневой директории проекта:
```
pytest ./src/tests
```
вы также можете запустить тесты с помощью Docker
```
docker-compose exec web pytest .
```
