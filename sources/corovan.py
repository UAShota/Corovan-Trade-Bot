import random
import sys
from datetime import *
from random import shuffle

from corovan_config import *
from engine import *


class Camel(object):
    """ Класс рабочего """

    def __init__(self):
        """ Конструктор """
        self.power = 0
        self.speed = 0
        self.hp = 0
        self.ammo = 0
        self.gold = 0
        self.injuries = 0
        self.action = ""
        self.hours = 0
        self.mins = 0
        self.secs = 0
        self.walkHunt = 0
        self.walkTree = 0
        self.walkFish = 0
        self.walkCloth = 0
        self.walkStone = 0
        self.walkIron = 0
        self.walkGround = 0


class CorovanCamel(Engine):
    """ Движок обработки команд """

    # Текущая версия
    VERSION = 1.82

    # Идентификатор игрового бота
    GAME_BOT_ID = -183457719

    # Простой
    STATE_NONE = 1
    # Ищем постройку для работы
    STATE_WALK = 2
    # Смотрим склад
    STATE_STOR = 3
    # Работаем
    STATE_WORK = 4
    # Ждать команды
    STATE_COMM = 5
    # Идет скидывать статы
    STATE_REST = 6
    # Идет лечиться
    STATE_HEAL = 7
    # Идет на стены
    STATE_WALL = 8

    def __init__(self, lock, config: dict, id: int, channel: int, color: int, token: str, action: str):
        """ Конструктор """
        super().__init__(config, str(id), lock, token, color)
        self.id = id
        self.channel = channel
        self.defaction = action
        self.state = self.STATE_NONE
        self.time = datetime.min
        self.step = 0
        self.cmd = None
        self.upgrade = None
        self.defence = False
        self.wall = False
        self.door = False
        self.drop = False
        self.heartbeat = None
        self.ammo = 0
        self.worker = Camel()
        self.rules = []
        self.rules.append([self.doCheckAttack, self.compile(r"^🔥Ваше поселение подверглось осаде")])
        self.rules.append([self.doCheckAttackWall, self.compile(r"^🛡Стена.+?👥Защитников: (\d+)\/(\d+)")])
        self.rules.append([self.doCheckAttackAccept, self.compile(r"^👥\[id%s\|.+? защитникам города" % id)])
        self.rules.append([self.doCheckAttackDone, self.compile(r"^🔥Битва за поселение.+?(🗡Победа|☠Поражение)")])
        self.rules.append([self.doCheckAttackDoor, self.compile(r"^‼ВНИМАНИЕ‼.В поселении начали открывать ворота")])
        self.rules.append([self.doCheckWork, self.compile(r"^⚕\[id%s\|.+? (лекарь).+?⌛Время ожидания: (\d+) час" % id)])
        self.rules.append([self.doCheckWork, self.compile(r"^🙏🏻\[id%s\|.+? (монастыре).+?⌛Время ожидания: (\d+) час" % id)])
        self.rules.append([self.doCheckWork, self.compile(r"^[^👁]\[id%s\|.+?, (сердцу Глубин)?.+⌛Время работы: (\d+) час." % id)])
        self.rules.append([self.doCome, self.compile(r"^\[id%s\|.+? давай (.+)" % id)])
        self.rules.append([self.doSay, self.compile(r"^\[id%s\|.+? пробуй (.+)" % id)])
        self.rules.append([self.doReply, self.compile(r"^\[id%s\|.+? дай (.+)" % id)])
        self.rules.append([self.doDouble, self.compile(r"^\[id%s\|.+? нажмите кнопку повторно" % id)])
        self.rules.append([self.doDone, self.compile(r"\[id%s\|.+?, Вы успешно вернулись" % id)])
        self.rules.append([self.doDrop, self.compile(r"вышел прямо к вашему поселению")])
        self.rules.append([self.doDrop, self.compile(r"обнаружили недалеко от поселения")])
        self.rules.append([self.doDrop, self.compile(r"прямо рядом с поселением")])
        self.rules.append([self.doHeal, self.compile(r"^⚕Лечебница.+?Занято коек: (\d+)/(\d+)")])
        self.rules.append([self.doLeave, self.compile(r"^\[id%s\|.+? стой" % id)])
        self.rules.append([self.doPickup, self.compile(r"^.Добыт.? \d+ единиц.?\s")])
        self.rules.append([self.doStart, self.compile(r"погнали")])
        self.rules.append([self.doStart, self.compile(r"^корован старт")])
        self.rules.append([self.doStop, self.compile(r"стопэ")])
        self.rules.append([self.doStop, self.compile(r"^корован стоп")])
        self.rules.append([self.doUpradeWant, self.compile(r"^\[id%s\|.+? надо (.+?) до" % id)])
        self.rules.append([self.doUpradeAccept, self.compile(r"^⚒\[id%s\|.+? работа над улучшением началась" % id)])
        self.rules.append([self.doViewAbbat, self.compile(r"^\[id%s\|.+?, выберите характеристику, которую хотите уменьшить" % id)])
        self.rules.append([self.doViewProfile, self.compile(r"^👑?\[id%s\|.+👊.+?(\d+).+?🖐.+?(\d+).+?❤.+?(\d+).+?🌕(\d+).+🥋(\d+).+🖤.+?(\d+).+⛏Текущее занятие:.+\*(.+?)\*(?:.+\(осталось: (?:(\d+) час\. )?(?:(\d+) мин\. )?(?:(\d+) сек\. \))?)?" % id)])
        self.rules.append([self.doViewStorage, self.compile(r"^Ресурсов на складе:.🌲Дерево: (\d+).🍙Камень: (\d+).🧣Ткань: (\d+).📏Железо: (\d+).🍗Еда: (\d+)")])
        self.rules.append([self.doViewWorking, self.compile(r"🍖(?:⚒|(\d+)/(\d+)).+?🌲(?:⚒|(\d+)/(\d+)).+?🐟(?:⚒|(\d+)/(\d+)).+?🧣(?:⚒|(\d+)/(\d+)).+?🍙(?:⚒|(\d+)/(\d+)).+?📏(?:⚒|(\d+)/(\d+)).+?💀(?:⚒|(\d+)/(\d+))")])
        self.rules.append([self.doViewTrade, self.compile(r"^\[id%s\|.+, торговец также имеет.+?🌕Цена: (\d+) золота" % id)])

        self.caption("Сorovan v%s" % self.VERSION, True)
        self.thread(self.run)

    def connected(self):
        """ Подключенно """
        if not self.heartbeat:
            self.name = self.getName()
            self.heartbeat = Thread(target=self.checkHeartbeat)
            self.heartbeat.start()
        return

    def run(self):
        """ Жизненный цикл """
        # Команды в личку с себя
        if self.event.peer_id == self.id:
            self.work(False)
        # Команды с чата
        elif self.event.peer_id == self.channel:
            self.work(False)
        # Команды с алертера
        elif self.event.peer_id == self.config.alertID:
            self.work(False)
        return

    def getName(self):
        """ Очеловечивание """
        tmpResult = self.session.method("users.get", {"user_ids": self.id})
        tmpResult = tmpResult[0]
        return "%s %s" % (tmpResult["first_name"], tmpResult["last_name"])

    def go(self, cmd: str, state: int = STATE_NONE):
        """ Выполнение команды """
        if state and (self.state != self.STATE_COMM):
            self.state = state
        # Запомним последнюю команду
        self.cmd = cmd
        # Подождем
        time.sleep(random.randint(200, 300) / 100)
        self.send(cmd)
        time.sleep(random.randint(200, 300) / 100)

    def checkWork(self):
        """ Обзор работы """
        if self.state != self.STATE_NONE:
            return False
        # Состояние простоя
        self.log("Идем искать работу")
        self.go("@dngworld 🏜'Местность", self.STATE_WALK)
        # Ход найден
        return True

    def checkAbbat(self):
        """ Обзор монастыря """
        if not self.defaction or self.step % 2 == 0:
            return False
        # Посчитаемся
        tmpCmd = None
        tmpHavePower = self.worker.power > 10
        tmpHaveSpeed = self.worker.speed > 10
        tmpHaveHp = self.worker.hp > 10
        # Определим самоистязание для силы
        if self.defaction == "сила":
            if tmpHaveSpeed:
                tmpCmd = "@dngworld 🖐'"
            elif tmpHaveHp:
                tmpCmd = "@dngworld ❤'"
        # Определим самоистязание для ловкости
        elif self.defaction == "ловкость":
            if tmpHavePower:
                tmpCmd = "@dngworld 👊'"
            elif tmpHaveHp:
                tmpCmd = "@dngworld ❤'"
        # Определим самоистязание для хп
        elif self.defaction == "хп":
            if tmpHavePower:
                tmpCmd = "@dngworld 👊'"
            elif tmpHaveSpeed:
                tmpCmd = "@dngworld 🖐'"
        # Если качать нечего - выходим
        if not tmpCmd:
            return False
        # Отправим искать монастырь
        self.log("Иду в монастырь для кача %s" % self.defaction)
        self.go("@dngworld 🏚'Поселение")
        self.go("@dngworld 'Монастырь", self.STATE_REST)
        self.cmd = tmpCmd
        # Ход найден
        return True

    def checkHeal(self):
        """ Обзор лечебницы """
        if self.worker.injuries < self.config.injuries:
            return False
        # Отправим искать монастырь
        self.log("Иду в больничку")
        self.go("@dngworld 🏚'Поселение")
        self.go("@dngworld 'Лечебница", self.STATE_HEAL)
        # Ход найден
        return True

    def checkAmmo(self):
        """ Обзор торгового поста """
        if self.worker.ammo >= self.config.ammo:
            return False
        self.go("@dngworld 🏚'Поселение")
        self.go("@dngworld 'Торговый пост")
        # Ход найден
        return False

    def checkUpgrade(self):
        """ Улучшение здания """
        if not self.upgrade:
            return False
        # Откроем опции
        if self.upgrade == "тропы":
            self.go("@dngworld 'Открыть уровень")
        else:
            self.go("@dngworld 'Улучшить %s" % self.upgrade)
        # Запулим
        self.go("@dngworld 'Улучшать %s" % self.upgrade)
        self.upgrade = None
        # Ход найден
        return True

    def checkDefense(self):
        """ Улучшение здания """
        if not self.defence:
            return False
        # Отправим на стены
        self.log("Иду на стены")
        self.go("@dngworld 🏚'Поселение")
        self.go("@dngworld 'Стена", self.STATE_WALL)
        # Ход найден
        return True

    def checkHeartbeat(self):
        """ Самопроверка что делает персонаж """
        tmpTodayFunc = datetime.today
        while True:
            tmpToday = tmpTodayFunc()
            if self.state != self.STATE_COMM and tmpToday > self.time:
                self.time = tmpToday + timedelta(minutes=int(random.randint(30, 60)))
                self.send("@dngworld 🎭'Персонаж")
            self.sleep(random.randint(180, 300), "сердцебиения")

    def doViewProfile(self, match: dict):
        """ Проверка своего состояния """
        if self.state == self.STATE_COMM:
            return
        else:
            self.state = self.STATE_NONE
        # Считаем параметры
        self.worker.power = self.toInt(match[1])
        self.worker.speed = self.toInt(match[2])
        self.worker.hp = self.toInt(match[3])
        self.worker.gold = self.toInt(match[4])
        self.worker.ammo = self.toInt(match[5])
        self.worker.injuries = self.toInt(match[6])
        self.worker.action = match[7]
        self.worker.hours = self.toInt(match[8])
        self.worker.mins = self.toInt(match[9])
        self.worker.secs = self.toInt(match[10])
        # Если время есть - запишем
        if self.worker.secs:
            self.state = self.STATE_WORK
            self.time = datetime.today() + timedelta(hours=self.worker.hours, minutes=self.worker.mins, seconds=self.worker.secs)
            self.log("Продлеваем время ожидания работы до %s " % self.toUTC(self.time))
        # Проверим нападение на деревню
        elif self.checkDefense():
            return
        # Если простаиваем - глянем строения
        elif self.checkUpgrade():
            return
        # Для раненных проверим лечебницу
        elif self.checkHeal():
            return
        # Для золота проверим покупку амуниции
        elif self.checkAmmo():
            return
        # Для фермеров глянем склад, иначе самоистязание
        elif self.checkAbbat():
            return
        # Ничего не нашли, идем на работы
        return self.checkWork()

    def doViewTrade(self, match: dict):
        """ Проверка торгпоста """
        tmpCost = self.toInt(match[1])
        if tmpCost > self.worker.gold:
            return
        # Купим
        time.sleep(random.randint(2000, 3000) / 100)
        self.send("@dngworld 'Купить за %s" % tmpCost)

    def doViewWorking(self, match: dict):
        """ Проверка строений """
        if self.state != self.STATE_WALK:
            return
        # Считаем параметры
        self.worker.walkHunt = self.toInt(match[2]) - self.toInt(match[1])
        self.worker.walkTree = self.toInt(match[4]) - self.toInt(match[3])
        self.worker.walkFish = self.toInt(match[6]) - self.toInt(match[5])
        self.worker.walkCloth = self.toInt(match[8]) - self.toInt(match[7])
        self.worker.walkStone = self.toInt(match[10]) - self.toInt(match[9])
        self.worker.walkIron = self.toInt(match[12]) - self.toInt(match[11])
        self.worker.walkGround = self.toInt(match[14]) - self.toInt(match[13])
        # Глянем склад
        self.go("@dngworld 👝'Склад", self.STATE_STOR)

    def doViewAbbat(self, match: dict):
        """ Обзор монастыря """
        if self.state != self.STATE_REST:
            return
        time.sleep(random.randint(2000, 3000) / 100)
        self.send(self.cmd)

    def doViewStorage(self, match: dict):
        """ Отправка на работу """
        if self.state != self.STATE_STOR:
            return
        # Определим что качать
        if self.defaction:
            self.doWalkStore(match)
        else:
            self.doWalkSelf(match)
        return

    def doWalkStore(self, match: dict):
        """ Отправка на работу для кача склада """
        self.log("Иду работать по специальности %s" % self.defaction)
        # Разберем
        tmpTree = int(self.toInt(match[1]) / 2)
        tmpStone = int(self.toInt(match[2]) / 2)
        tmpCloth = self.toInt(match[3])
        tmpIron = self.toInt(match[4])
        tmpEat = int(self.toInt(match[5]) / 2)
        # Приоритет ловкость
        if self.worker.walkGround and (self.worker.ammo < self.config.ammo):
            self.go("@dngworld 'Подземные тропы")
            self.go("@dngworld 'Спуститься вниз")
            return
        elif self.defaction == "ловкость":
            if self.worker.walkFish and (tmpEat <= tmpCloth or not self.worker.walkCloth):
                self.go("@dngworld 'Берег")
                self.go("@dngworld 'На рыбалку")
                return
            elif self.worker.walkCloth:
                self.go("@dngworld 'Берег")
                self.go("@dngworld 'Выращивать лен")
                return
                # Приоритет сила
        elif self.defaction == "сила":
            if self.worker.walkHunt and (tmpEat <= tmpTree or not self.worker.walkTree):
                self.go("@dngworld 'Чаща")
                self.go("@dngworld 'На охоту")
                return
            elif self.worker.walkTree:
                self.go("@dngworld 'Чаща")
                self.go("@dngworld 'Рубить деревья")
                return
        # Приоритет хп
        elif self.defaction == "хп":
            if self.worker.walkStone and (tmpStone <= tmpIron or not self.worker.walkIron):
                self.go("@dngworld 'Горы")
                self.go("@dngworld 'Колоть камни")
                return
            elif self.worker.walkIron:
                self.go("@dngworld 'Горы")
                self.go("@dngworld 'Добывать руду")
                return
        # Приоритета нет
        else:
            return self.doWalkSelf(match)
        # Ничего не нашли
        self.log("Все доступные рабочие места заняты")

    def doWalkSelf(self, match: dict):
        """ Отправка на работу для кача статов """
        self.log("Иду работать на уравнивание стат")
        # Разберем
        tmpSort = []
        tmpSort.append([self.worker.power, "p"])
        tmpSort.append([self.worker.speed, "s"])
        tmpSort.append([self.worker.hp, "h"])
        tmpSort.append([sys.maxsize, "u"])
        tmpSort.sort()
        # Разберем
        tmpTree = int(self.toInt(match[1]) / 2)
        tmpStone = int(self.toInt(match[2]) / 2)
        tmpCloth = self.toInt(match[3])
        tmpIron = self.toInt(match[4])
        tmpEat = int(self.toInt(match[5]) / 2)
        # Поищем
        for tmpVal, tmpType in tmpSort:
            if tmpType == "p":
                if self.worker.walkTree and (tmpTree <= tmpEat or not self.worker.walkHunt):
                    self.go("@dngworld 'Чаща")
                    self.go("@dngworld 'Рубить деревья")
                    return
                elif self.worker.walkHunt:
                    self.go("@dngworld 'Чаща")
                    self.go("@dngworld 'На охоту")
                    return
            elif tmpType == "s":
                if self.worker.walkFish and (tmpEat <= tmpCloth or not self.worker.walkCloth):
                    self.go("@dngworld 'Берег")
                    self.go("@dngworld 'На рыбалку")
                    return
                elif self.worker.walkCloth:
                    self.go("@dngworld 'Берег")
                    self.go("@dngworld 'Выращивать лен")
                    return
            elif tmpType == "h":
                if self.worker.walkStone and (tmpStone <= tmpIron or not self.worker.walkIron):
                    self.go("@dngworld 'Горы")
                    self.go("@dngworld 'Колоть камни")
                    return
                elif self.worker.walkIron:
                    self.go("@dngworld 'Горы")
                    self.go("@dngworld 'Добывать руду")
                    return
            elif tmpType == "u":
                if self.worker.walkGround:
                    self.go("@dngworld 'Подземные тропы")
                    self.go("@dngworld 'Спуститься вниз")
                    return
        # Ничего не нашли
        self.log("Не нашел работу")

    def doCheckAttack(self, match: dict):
        """ Проверка нападения """
        self.defence = True
        self.wall = False
        self.door = False

    def doCheckAttackWall(self, match: dict):
        """ Попытка встать на защиту """
        if self.state != self.STATE_WALL:
            return False
        # Посчитаем места
        tmpCount = self.toInt(match[1])
        tmpLimit = self.toInt(match[2])
        # Обработка разовая
        self.defence = False
        # Попробуем встать на защиту либо откроем двери
        if tmpCount < tmpLimit:
            self.go("@dngworld 'На защиту")
        elif not self.door:
            self.go("@dngworld 'Открыть ворота")
        return

    def doCheckAttackDoor(self, match: dict):
        """ Ворота уже открываются """
        self.defence = False
        self.door = True

    def doCheckAttackDone(self, match: dict):
        """ Бой завершен """
        if self.wall:
            self.sleep(random.randint(500, 20000) // 100, "Слезаю со стены")
            self.go("@dngworld 🎭'Персонаж")
            self.go("@dngworld 'Отменить")
        # Сбросим состояния
        self.wall = False
        self.defence = False
        self.door = False

    def doCheckAttackAccept(self, match: dict):
        """ Успешное влезание на стену """
        self.wall = True
        self.state = self.STATE_WORK
        self.time = datetime.today() + timedelta(hours=12)
        self.log("Стою на стене до %s" % self.toUTC(self.time))

    def doCheckWork(self, match: dict):
        """ Проверка отправки """
        tmpGround = match[1]
        tmpHours = self.toInt(match[2])
        # Определим ротацию
        if tmpGround:
            self.step = 0
        else:
            self.step += 1
        # Сдвинем время
        self.state = self.STATE_WORK
        self.time = datetime.today() + timedelta(hours=tmpHours)
        self.log("Шаг: %s на %s час. Время: %s " % (self.step, tmpHours, self.toUTC(self.time)))

    def doCome(self, match: dict):
        """ Просьба выполнить команду """
        self.go("@dngworld %s" % match[1])

    def doSay(self, match: dict):
        """ Просьба выполнить команду """
        self.go(match[1])

    def doReply(self, match: dict):
        """ Просьба выполнить команду """
        time.sleep(random.randint(2000, 3000) / 1000)
        self.send(match[1], reply=self.event.message_id)

    def doDouble(self, match: dict):
        """ Повтор нажатия кнопки """
        if self.cmd:
            self.go(self.cmd)
            self.go("@dngworld 🎭'Персонаж")
        return

    def doHeal(self, match: dict):
        """ Учет коек в лечебнице """
        if self.state != self.STATE_HEAL:
            return
        # Посчитаем койки
        tmpCount = self.toInt(match[1])
        tmpLimit = self.toInt(match[2])
        # Есть ли свободные места
        if tmpCount < tmpLimit:
            self.go("@dngworld 'Лечить травмы")
        else:
            self.time = datetime.today() + timedelta(hours=1)
            self.log("Жду койку в %s" % self.toUTC(self.time))
        return

    def doLeave(self, match: dict):
        """ Отмена действий бота """
        if self.state != self.STATE_NONE:
            self.go("@dngworld 🎭'Персонаж")
            self.go("@dngworld 'Отменить", self.STATE_NONE)
        self.doStop(match)

    def doDrop(self, match: dict):
        """ Учет дропа вещи """
        self.drop = True
        # Если не работаем - сразу заберем
        if self.state != self.STATE_WORK:
            self.go("@dngworld 'Забрать")
        return

    def doPickup(self, match: dict):
        """ Учет подбора вещи """
        self.drop = False

    def doDone(self, match: dict):
        """ Работа окончена """
        if self.state != self.STATE_COMM:
            self.state = self.STATE_NONE
            self.log("Закончили работу, ждем сердцебиения")
        else:
            self.log("Закончили работу, ждем команды запуска")
        # Проверим лежащий дроп
        if self.drop:
            self.send("@dngworld 'Забрать")
        return

    def doUpradeWant(self, match: dict):
        """ Проверка строений """
        self.log("Принято задание на постройку %s" % match[1])
        self.upgrade = match[1]

    def doUpradeAccept(self, match: dict):
        """ Начат апгрейд """
        self.state = self.STATE_WORK
        self.time = datetime.today() + timedelta(hours=1)
        self.log("Начал апгрейд до %s" % self.toUTC(self.time))

    def doStart(self, match: dict):
        """ Проверка строений """
        self.state = self.STATE_NONE
        self.send("-> корован запущен", self.id)

    def doStop(self, match: dict):
        """ Проверка строений """
        self.state = self.STATE_COMM
        self.send("-> корован остановлен", self.id)


# Создадим
tmpConfig = Config()
# Смешаем оловянных солдатиков
shuffle(tmpConfig.params)
# Создадим объекты
tmpLock = threading.Lock()
for tmpId, tmpChannel, tmpColor, tmpToken, tmpAction in tmpConfig.params:
    CorovanCamel(tmpLock, tmpConfig, tmpId, tmpChannel, tmpColor, tmpToken, tmpAction).sleep(random.randint(5000, 15000) // 1000, "для запуска следующего")
