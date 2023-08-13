class Config(object):
    """ Конфигурация """

    def __init__(self):
        """ Конструктор """
        # Сообщения Windows
        self.alertToast = True
        # ID ВК алерта (Номер, None)
        self.alertID = 384297286
        # Файл алерта (Путь, None)
        self.alertFile = None
        # Временная зона
        self.utc = +0
        # Заглушка цвета
        self.color = 0
        # Количество травм для лечения
        self.injuries = 5
        # Количество аммуниции для кача
        self.ammo = 10
        # ID, Канал, Цвет, Токен, Ресурс (None или еда)
        self.params = []

        # Марго тропы
        self.params.append([619706007, 2000000010, 93, "token", None])