db_conn_error = "Error connecting to the database"
db_conf_not_success = "Database is not configured correctly"
contact_schema_fname = (
    "Ім’я контакта, мінімальна довжина 2 символи, максимальна довжина 30 символів."
)
contact_schema_lname = (
    "Прізвище контакта, мінімальна довжина 2 символи, максимальна довжина 30 символів."
)
contact_schema_email = (
    "Email контакта, мінімальна довжина 5 символи, максимальна довжина 50 символів."
)
contact_schema_phone = (
    "Телефон контакта, мінімальна довжина 10 символи, максимальна довжина 15 символів."
)
contact_schema_birthday = "Дата народження контакта, формат дати YYYY-MM-DD."
contact_schema_add_info = "Додаткова інформація, максимальна довжина 255 символів."
validate_birthday = "Дата народження не може бути в майбутньому."
contact_not_found = "Контакт не знайдений."

user_schema_name = (
    "Ім'я користувача, мінімальна довжина 3 символи, максимальна довжина 30 символів."
)
user_schema_password = (
    "Пароль користувача, мінімальна довжина 8 символи, максимальна довжина 20 символів."
)

authenticate_wrong_user = "Невірне ім’я або пароль"
user_exists = "Такий користувач вже зареєстрований"
mail_exists = "Користувач з таким e-mail вже зареєстрований"
email_tel_exists = "Інший контакт вже має цей email або телефон"
invalid_token = "Невірний токен"
revoked_token = "Токен відкликано"
validate_credentials = "Не вдалося перевірити облікові дані"
invalid_refresh_token = "Невірний рефреш-токен"
role_access = "Недостатньо прав доступу"

email_not_confirm = "Електронна адреса не підтверджена"
email_confirmed_success = "Вітаю, електронну пошту підтверджено"
email_has_confirmed = "Ваша електронна пошта вже підтверджена"
check_email = "Перевірте свою електронну пошту для підтвердження"
password_reset_success = "Вітаю, скидання пароля успішне!"
user_not_found = "Корстувача не знайдено"
password_reset_email_sent = "Надіслано електронний лист для скидання пароля"
request_limit = "Перевищено ліміт запитів. Спробуйте пізніше."
