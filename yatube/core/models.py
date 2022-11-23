from django.db import models


class PubDateModel(models.Model):
    """Абстрактная модель. Добавляет дату создания и фильтр по ней."""
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        abstract = True
        ordering = ['-pub_date']
