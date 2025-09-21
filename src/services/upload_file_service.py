import cloudinary
import cloudinary.uploader


class UploadFileService:
    """
    Сервіс для завантаження файлів у **Cloudinary**.

    Використовується для зберігання аватарів користувачів у хмарі з автоматичною
    генерацією URL для зображення.

    Args:
        cloud_name (str): Назва хмари Cloudinary.
        api_key (str): API ключ Cloudinary.
        api_secret (str): Секретний ключ Cloudinary.
    """

    def __init__(self, cloud_name, api_key, api_secret):
        """
        Ініціалізує сервіс Cloudinary з параметрами доступу.

        Args:
            cloud_name (str): Назва хмари Cloudinary.
            api_key (str): Публічний API-ключ Cloudinary.
            api_secret (str): Секретний ключ Cloudinary.
        """
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )

    @staticmethod
    def upload_file(file, username) -> str:
        """
        Завантажує файл у Cloudinary та повертає URL обробленого зображення.

        Args:
            file (UploadFile): Файл, отриманий через FastAPI.
            username (str): Ім’я користувача, використовується для формування public_id.

        Returns:
            str: URL завантаженого зображення (розмір 250x250, crop="fill").
        """
        public_id = f"RestApp/{username}"
        r = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
        src_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=r.get("version")
        )
        return src_url
