import re
import sys
import asyncio
import random
from random import randint
from telethon import events
from addons import qHash

class RF:
    bot_id = 577009581
    is_run = False
    rf_message = None
    is_in_caves = is_in_gh = is_has_hil = is_has_res = False
    cave_leader_id = 715480502
    my_health = my_max_health = 5117
    hp = "/bind_wear_1723376879927d"
    tomat_id = 278339710
    kroha_id = 353501977
    tamplier_id = 681431333
    john_id = 562559122
    your_name = "Ros_Hangzhou"

    def __init__(self, client):
        self.client = client
        self.group = [[False, False, False, False] for _ in range(6)]
        self.my_group_pos = -1
        self.health_re = re.compile(r"Здоровье пополнено \D+(\d+)/(\d+)")
        self.battle_re = re.compile(r"^Сражение с .*$")
        self.damage_re = re.compile(r"(\d+)$")
        self.last_talisman_info = None  # (type, level)
        self.players = {
            "Нежный 🍅": self.tomat_id,
            "🐾ᏦᎮᎧχᏗ": self.kroha_id,
            "𝕴𝖆𝖒𝖕𝖑𝖎𝖊𝖗": self.tamplier_id,
            "John Doe": self.john_id
        }
        self.cmd_altar = None
        self.altar_dict = {
            0: "👩‍🚀Алтарь Иса",
            1: "👩‍🚀Алтарь Гебо",
            2: "🧝‍♀Алтарь Исс",
            3: "🧝‍♀Алтарь Дагаз",
            4: "🤖Алтарь Тир",
            5: "🤖Алтарь Эйви"
        }
        self.is_nacheve_active = self.in_battle = False  # Флаги активности nacheve и боя
        self.is_cave_leader = True
        self.kroha_pativod()



    def isIdCompare(self, id):
        return id == self.bot_id

    def isCaveLeaderIdCompare(self, id):
        return id == self.cave_leader_id

    def reset_health(self):
        self.my_health = self.my_max_health
        self.in_battle = False
        print(f"Здоровье сброшено до максимального: {self.my_health}")

    async def checkHealth(self, lstr) -> bool:
        # Проверяем, если строка содержит информацию о пополнении здоровья
        if self.updateHealth(lstr[0]):
            return True

        # Проверяем, если строка начинается с "Сражение с"
        if not self.isBattleStart(lstr[0]):
            return False

        # Проверяем, если бой с элитным мобом или если есть недостаток энергии, то пропускаем этот бой
        if self.skipBattle(lstr):
            return False

        # Пропускаем строки, которые не содержат информацию о бое или об игроке
        lstr = lstr[2:]

        # Подсчет урона, нанесенного игроку
        self.calculateDamage(lstr)

        # Проверка, если у игрока закончились жизни
        if self.isPlayerDead():
            return True  # Выходим из функции сразу, если игрок мертв

        # Проверка необходимости автохила
        await self.autoHeal()

        return True

    def updateHealth(self, line: str) -> bool:
        match = self.health_re.search(line)
        if match:
            new_health = int(match.group(1))
            new_max_health = int(match.group(2))
            print(f"Старое здоровье: {self.my_health}/{self.my_max_health}")
            self.my_health = new_health
            self.my_max_health = new_max_health
            print(f"Здоровье обновлено: {self.my_health}/{self.my_max_health}")
            return True
        return False

    def isBattleStart(self, line: str) -> bool:
        return bool(self.battle_re.search(line))

    def skipBattle(self, lstr: list) -> bool:
        return any(phrase in lstr[0] for phrase in ["Элитный", "Элитная"]) or "Энергия" in lstr[-1]

    def calculateDamage(self, lstr: list):
        if not self.in_battle:
            return
        for str_line in lstr:
            if self.my_health <= 0:
                print("Персонаж мертв, прекращаем расчет урона")
                self.in_battle = False
                return
            if not str_line or "Ты " in str_line or " нанес удар " not in str_line:
                continue
            match = self.damage_re.search(str_line)
            if match:
                self.my_health -= int(match.group(1))
                print(f"Получен урон: {match.group(1)}, текущее здоровье: {self.my_health}")

    def isPlayerDead(self) -> bool:
        if self.my_health <= 0:
            print("Здоровье равно или меньше нуля. Игрок умер.")
            self.reset_health()  # Сбрасываем здоровье до максимального только после завершения всех расчетов
            return True
        return False

    async def autoHeal(self):
        print(f"Проверка здоровья перед автолечением: {self.my_health}")
        if self.my_health <= 800 and self.is_has_hil :
            print(f"Здоровье критически низкое ({self.my_health}). Отправляем запрос на хил.")
            await self.rf_message.click(0)
            self.is_has_hil = False
        else:
            print(f"Здоровье достаточно высокое ({self.my_health}). Лечение не требуется.")

    async def msg_parce(self, message):
        if not self.is_run:
            return

        lstr = message.message.split('\n')
        val = qHash(lstr[0])
        if val == 0:
            return
        print(val, lstr[0])

        # в пещерах
        if any(phrase in lstr[0] for phrase in [
            "Панель управления", 
            "воскрешение в течение 1 минуты", 
            "Ты направляешься в пещеры на фуникулере",
        ]):
            self.is_in_caves = True
            self.is_has_hil = True
            await asyncio.sleep(randint(4, 10))
            await self.client.send_message(self.bot_id, "⚖️Проверить состав")
            print("в пещерах")
        elif any(phrase in line for line in lstr for phrase in [
            "Ты снова жив",
            "Вы больше не можете воскрешаться",
        ]):
            self.reset_health()
            print(self.my_health, self.my_max_health)
        elif any(phrase in line for line in lstr for phrase in [
            "Ожидай завершения",
        ]):
            await asyncio.sleep(randint(6, 10))
            await self.rf_message.click(1)
            self.reset_health()
            print(self.my_health, self.my_max_health)
        elif "Сражение с" in lstr[0] and not any("Рюкзак" in line for line in lstr):
            self.in_battle = True   
        elif "К сожалению ты умер" in lstr:
            self.in_battle = False     
        elif "Ваша группа замерзнет через 5 минут" in lstr[0]:
            await asyncio.sleep(1)
            await self.rf_message.click(2)
        elif "Ваша группа восстановила силы" in lstr[0]:
            await asyncio.sleep(1)
            await self.rf_message.click(2)
        elif "Ваша группа прибудет в ген. штаб через" in lstr[0]:
            print("чувачок, ты закончил пещеру")
            self.is_in_caves = False
            await asyncio.sleep(1)
            await self.client.send_message(self.bot_id, RF.hp)  # переодеться для мобов
            await self.check_arrival()
        elif lstr[0].startswith("Состав:"):
            print("что там по составу")
            await self.check_group_list(lstr)
            await asyncio.sleep(randint(10, 20))
            await self.vihod_s_caves(lstr)

        elif lstr[0].endswith("не в ген. штабе]"):
            await message.forward_to(-1001323974021)
            # Ищем всех игроков, упомянутых в сообщении
            players_not_in_gh = re.findall(r'(Нежный 🍅|🐾ᏦᎮᎧχᏗ|𝕴𝖆𝖒𝖕𝖑𝖎𝖊𝖗|John Doe)', lstr[0])
            if players_not_in_gh:
                for player in players_not_in_gh:
                    if player in self.players:
                        print(f"{player} не в ген. штабе")
                        await self.client.send_message(self.players[player], "Давайте в ген. штаб")
            await self.client.send_message(self.bot_id, "🔥 61-65 Лес пламени")  # или заменить на локацию
        elif "Если ты хочешь вернуть группу" in lstr[0]:
            await self.client.send_message(self.bot_id, "22")
            


        #     тесты
        # elif "Содержимое" in lstr[0]:
        #     print ("bag bag bag")
        #     await self.client.send_message(715480502, "bag bag bag")
       
       
        # на страже
        elif "Бой с боссом будет происходить в автоматическом режиме." in lstr[0]:
            print("дошел до стража")
            await self.straj()
        elif "Босс еще не появился. Проход в локацию закрыт!" in lstr[0]:  # если умер на страже и снова хочешь идти на стража
            await asyncio.sleep(1)
            await self.client.send_message(self.bot_id, "🔥 61-65 Лес пламени")

        # на чв
        elif any(phrase in line for line in lstr for phrase in [
            "Алтарь Эйви",
            "Алтарь Тир",
        ]):
            await asyncio.sleep(1)
            await self.client.send_message(self.bot_id, "🤖 Терминал Aquilla")
        elif any(phrase in line for line in lstr for phrase in [
            "Ты прибыл к алтарю",
             "бой за терминал будет происходить автоматически",
             "ты можешь перейти к терминалу только из алтаря",
        ]):
            await self.nacheve()
        elif "Храна. Ты был убит!" in lstr[0]:
            await self.gokragi()
        elif "Ты прибыл в краговые шахты" in lstr[0]:
            await asyncio.sleep(1)
            await self.client.send_message(self.bot_id, "⛏Рудник")
        elif "[на время боевых действий проход закрыт]" in lstr[0]:
            await asyncio.sleep(1)
            altars = [ "🧝‍♀Алтарь Дагаз", "👩‍🚀Алтарь Гебо", "👩‍🚀Алтарь Иса", "🧝‍♀Алтарь Исс" ]
            # алтари "🤖Алтарь Эйви", "🤖Алтарь Тир", 
            await self.client.send_message(self.bot_id, random.choice(altars))
        elif "Ты прибыл в ⛏рудник." in lstr[0]:
            await asyncio.sleep(1)
            await self.client.send_message(self.bot_id, "🖲 Установить АБУ")
        # elif any(phrase in lstr[0] for phrase in ["Ты прибыл к алтарю - 👩‍🚀Алтарь Гебо", "Ты прибыл к алтарю - 👩‍🚀Алтарь Иса"]):
        #     await asyncio.sleep(1)
        #     await self.client.send_message(self.bot_id, "👩‍🚀 Терминал Basilaris")


        # на мобах
        elif any(phrase in lstr[0] for phrase in ["пойти в 61-65 Лес пламени", "что хочешь отправиться в пещеры?"]):
            await asyncio.sleep(1)
            await message.click(0)
        elif "Что будем делать?" in lstr[-1]:
            print("будем бить")
            await asyncio.sleep(1)
            await self.client.send_message(self.bot_id, "🔪 Атаковать")
        elif any(phrase in line for line in lstr for phrase in ["Энергия: 🔋0/5", "[недостаточно энергии]"]):
            print("нет энергии")
            await asyncio.sleep(1)
            await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
            await self.gokragi()
        elif any(f"Энергия: 🔋{i}/5" in lstr[-1] for i in range(1, 5)):
            print("есть энергия")
            await asyncio.sleep(1)
            await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
            await self.check_arrival()
        elif any(f"+1 к энергии 🔋{i}/5" in lstr[0] for i in (4, 5)):

            if self.is_in_caves:
                if self.is_cave_leader:
                    print("Восполнение энергии в пещерах или если ты лидер пещеры")
                    await asyncio.sleep(1)
                    await self.rf_message.click(2)
                else: # Если в пещерах, но не лидер
                    print("Пересылка сообщения о восполнении энергии в группу")
                    # await message.forward_to(-1001323974021) #59 60
                    await message.forward_to(2220238697) # без В
            else:
                print("Восполнение энергии вне пещер")
                await asyncio.sleep(1)
                await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
                await self.check_arrival()




        # # данжи
        # elif any(f"+1 к энергии 🔋{i}/5" in lstr[0] for i in (4, 5)):
        #     await asyncio.sleep(1)
        #     await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
        #     await self.check_arrival_dange()
        # elif "Ты уверен, что хочешь попробовать пройти данж" in lstr[0]:
        #     await asyncio.sleep(1)
        #     await message.click(0)
        #     await self.dangego()
        # elif "Что будем делать?" in lstr[-1]:
        #     print("будем бить")
        #     await asyncio.sleep(1)
        #     await self.client.send_message(self.bot_id, "🔪 Атаковать")
        # elif any(f"Энергия: 🔋{i}/5" in lstr[-1] for i in range(1, 5)):
        #     print("есть энергия")
        #     await asyncio.sleep(1)
        #     await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
        #     await self.gokragi()  # заменил на краги
        # elif "Энергия: 🔋0/5" in lstr[-1] or "[недостаточно энергии]" in lstr[0]:
        #     print("нет энергии")
        #     await asyncio.sleep(1)
        #     await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
        #     await self.gokragi()
        
        # misc
        elif val == 1550650437:  # ⚒ Кузня - 5 ур.
            await self.craft_rec(lstr)
        elif val == 2509085174:  # Рецепты:
            return
        elif "[данное действие можно выполнять только из ген. штаба]" in lstr[0]:
            await asyncio.sleep(1)
            await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
            await self.check_arrival()
        elif any(phrase in lstr[0] for phrase in [
            "⚠️Прежде чем выполнять какие-то действия в игре",
            "Введите, пожалуйста, текст с картинки."
        ]):
            sys.exit()

        if not message.buttons:
            if val == 3190963077:  # ✨Добыча:
                await message.forward_to(-1001323974021) #группа 59
                await message.forward_to(2220238697) #группа без В
            else:
                await self.checkHealth(lstr)
            return

        if val == 3190963077:  # ✨Добыча:
            self.rf_message = message
            await asyncio.sleep(1)
            await self.client.send_message(self.bot_id, "⚖️Проверить состав")
            return


    async def check_arrival_dange(self):  # ходим данжи
        print("check_arrival_dange")

        while True:
            last_message = await self.client.get_messages(self.bot_id, limit=1)
            if last_message:
                lstr = last_message[0].message.split('\n')
                if any(condition in lstr[0] for condition in ["Ты дошел до локации.", "Вы уже находитесь в данной локации.", "Ты снова жив👼"]):
                    await self.client.send_message(self.bot_id, "/go_dange_10014")  # идти данж
                    return
            await asyncio.sleep(1)

    async def dangego(self):
        while True:
            await asyncio.sleep(10)
            dungeon_completed = False
            energy_low = False
            is_dead = False

            # Получаем все доступные сообщения
            last_messages = await self.client.get_messages(self.bot_id, limit=3)
            print(f"Проанализировано сообщений: {len(last_messages)}")

            for index, message in enumerate(last_messages):
                lstr = message.message.split('\n')

                # Показать содержимое lstr[0] и lstr[-1] для каждого сообщения
                print(f"Сообщение {index + 1}:")
                print(f"    lstr[0]: {lstr[0]}")
                print(f"    lstr[-1]: {lstr[-1]}")

                # Проверка наличия энергии и других условий
                if any(phrase in line for line in lstr for phrase in [
                    "У кого-то в группе меньше 2 единиц энергии",
                    "не в ген. штабе",
                    "уже совершает действие"
                ]):
                    print("нет энергии, кто-то не в гш или уже совершает действие")
                    energy_low = True
                    break

                # Проверка на смерть в каждой строке сообщения
                if any(phrase in line for line in lstr for phrase in ["Ты погиб от", "К сожалению вы не смогли пройти данж"]):
                    print("Ты погиб на данже")
                    is_dead = True
                    break

                if any("Вы успешно прошли" in line for line in lstr):
                    print("все в гш был данж и жив на данже")
                    dungeon_completed = True
                    continue

            if energy_low:
                print("нет энергии или кто-то не в гш")
                await asyncio.sleep(1)
                await self.client.send_message(self.bot_id, "🔥 61-65 Лес пламени")
                print("Отправлено сообщение: 🔥 61-65 Лес пламени")
                return

            if is_dead:
                print("умер на данже")
                await self.check_arrival_dange()
                print("Выполнен check_arrival_dange() после смерти")
                return

            if dungeon_completed:
                print("все в гш был данж и жив на данже")
                await asyncio.sleep(2)
                await self.client.send_message(self.bot_id, "💖 Пополнить здоровье")
                print("Отправлено сообщение: 💖 Пополнить здоровье")
                await self.wait_for_health_refill()
                await self.client.send_message(self.bot_id, "🌋 Краговые шахты")
                print("Отправлено сообщение: 🌋 Краговые шахты")
                return

            print("Ни одно из условий не выполнено, повторная проверка через 5 секунд")
            await asyncio.sleep(1)


    async def check_arrival(self):  # ходим на моба
        print("check_arrival")

        while True:
            last_message = await self.client.get_messages(self.bot_id, limit=1)
            if last_message:
                lstr = last_message[0].message.split('\n')
                if any(phrase in lstr[0] for phrase in [
                    "Ты дошел до локации.",
                    "Вы уже находитесь в данной локации.",
                    "Ваша группа вернулась в ген. штаб!" ,
                    "Ты снова жив👼"
                ]):    
                    await asyncio.sleep(2)
                    await self.client.send_message(self.bot_id, "💖 Пополнить здоровье")
                    await self.wait_for_health_refill()
                    await self.client.send_message(self.bot_id, "🔥 61-65 Лес пламени")
                    return
            await asyncio.sleep(1)

    async def gokragi(self):  # отправка на чв после смерти
        print("отправка на чв победа или рес")

        while True:
            last_message = await self.client.get_messages(self.bot_id, limit=1)
            if last_message:
                lstr = last_message[0].message.split('\n')
                if any(phrase in lstr[0] for phrase in ["Ты дошел до локации.", "Вы уже находитесь в данной локации.", "Ты снова жив👼", "Ваша группа вернулась в ген. штаб!"]):  
                    await asyncio.sleep(2)
                    await self.client.send_message(self.bot_id, "💖 Пополнить здоровье")
                    await self.wait_for_health_refill()
                    await self.client.send_message(self.bot_id, "🌋 Краговые шахты")
                    return
            await asyncio.sleep(1)








    async def parce_4v_logs(self, msg_text):

        print("Начало работы parce_4v_logs.")
        lstr = msg_text.split('\n')
        print(f"Количество строк в сообщении: {len(lstr)}")

        if len(lstr) > 24:
            l_altars = []
            if not lstr[5].endswith("Castitas"): l_altars.append(0)
            if not lstr[6].endswith("Castitas"): l_altars.append(1)
            if not lstr[14].endswith("Castitas"): l_altars.append(2)
            if not lstr[15].endswith("Castitas"): l_altars.append(3)
            if not lstr[23].endswith("Castitas"): l_altars.append(4)
            if not lstr[24].endswith("Castitas"): l_altars.append(5)

            print(f"Найденные алтари: {l_altars}")
            
            if l_altars:
                self.cmd_altar = self.altar_dict.get(random.choice(l_altars))
                print(f"Выбранный алтарь: {self.cmd_altar}")
            else:
                self.cmd_altar = random.choice(["🤖Алтарь Эйви", "🤖Алтарь Тир"])
                print(f"Алтари не найдены, выбран случайный алтарь: {self.cmd_altar}")

        print("Конец работы parce_4v_logs.")

    async def nacheve(self):
        print("работаем на чв")
        self.is_nacheve_active = True  # Устанавливаем флаг активности
        self.cmd_altar = None  # Сбрасываем выбранный алтарь при начале работы


        # Обработчик для сообщений из RF чата
        @self.client.on(events.NewMessage(chats=-1001284047611))
        async def handle_rf_info(event):
            print("Получено новое сообщение от RF чата.")
            first_line = event.message.text.split('\n')[0]
            print(f"Первая строка сообщения: {first_line}")
            await self.parce_4v_logs(event.message.text)

        try:
            while self.is_nacheve_active:
                # Обработка сообщений от бота
                bot_message = await self.client.get_messages(self.bot_id, limit=1)
                if bot_message:
                    message = bot_message[0]
                    lstr = message.message.split('\n')
                    print(f"Сообщение от бота:")
                    print(f"    lstr[0]: {lstr[0]}")
                    print(f"    lstr[-1]: {lstr[-1]}")

                    # Обработка сообщения от бота
                    if await self.process_bot_message(lstr):
                        continue

                # Проверка необходимости перехода к новому алтарю
                if self.cmd_altar:
                    print(f"Бездействие. Направляемся к новому алтарю: {self.cmd_altar}")
                    await self.client.send_message(self.bot_id, self.cmd_altar)
                    self.cmd_altar = None

                # Добавляем задержку в 10 секунд перед следующей итерацией
                print("Ожидание 10 секунд перед следующей проверкой...")
                await asyncio.sleep(10)

        finally:
            # Убираем обработчик событий
            self.client.remove_event_handler(handle_rf_info)
            self.is_nacheve_active = False
            print("Завершаем работу на чв")

    async def process_bot_message(self, lstr):

        # # Проверка, наносился ли вам урон
        # if not any("нанес удар" in line and self.your_name in line for line in lstr):
        #     print("По вам не было нанесено урона. Переходим к следующему терминалу.")
        #     self.is_nacheve_active = False 
        #     # await self.client.send_message(self.bot_id, "⛏Рудник")
        #     return False
        # Проверка победы и получения урона
        if any(phrase in line for line in lstr for phrase in ["Ты одержал победу над"]):
            if any("нанес удар" in line and self.your_name in line for line in lstr):
                print("Обнаружена победа с получением урона. Отправляемся в ген. штаб.")
                self.is_nacheve_active = False
                await asyncio.sleep(2)
                await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
                await self.gokragi()
                return True
            else:
                print("Победа без получения урона. Переходим к следующему терминалу.")
                return False  # Логика продолжит проверку cmd_altar для перехода к следующему алтарю


        if lstr[-1].endswith("минут.") or "дождись пока воскреснешь" in lstr[0] or "был убит ядерной ракетой" in lstr[0]:
            print("Обнаружено сообщение о времени. Вызываем gokragi()")
            self.is_nacheve_active = False
            await self.gokragi()
            return True

        if any(phrase in line for line in lstr for phrase in ["Бронза уже у тебя в рюкзаке."]):
            print("Обнаружена победа. Отправляемся в ген. штаб")
            self.is_nacheve_active = False
            await asyncio.sleep(2)
            await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
            await self.gokragi()
            return True

        if "Ты направляешься" in lstr[0]:
            self.is_nacheve_active = False
            return True

        return False
            

    async def straj(self):
        print("Начало работы со стражем straj")
        while True:
            await asyncio.sleep(10)
            is_dead = False
            is_damaged = False

            # Получаем последние сообщения
            last_messages = await self.client.get_messages(self.bot_id, limit=2)
            print(f"Проанализировано сообщений: {len(last_messages)}")

            for index, message in enumerate(last_messages):
                lstr = message.message.split('\n')

                # Показать содержимое lstr[0] и lstr[-1] для каждого сообщения
                print(f"Сообщение {index + 1}:")
                print(f"    lstr[0]: {lstr[0]}")
                print(f"    lstr[-1]: {lstr[-1]}")

                # Проверка на смерть персонажа
                if "воскреснешь через" in lstr[0]:
                    print("Конец работы со стражем straj - персонаж погиб")
                    is_dead = True
                    break

                # Проверка на получение урона
                if any(phrase in lstr[0] for phrase in [
                    "Страж нанес",
                    "Отравил тебя"
                ]):      
                    print("Продолжение работы со стражем straj - получен урон")
                    is_damaged = True
                    continue

                if "Ты дошел до локации." in lstr[0]:
                    print("конец работы на страже")
                    return

            if is_dead:
                print("Персонаж погиб, вызов функции gokragi")
                await self.check_arrival()
                return

            if is_damaged:
                print("Персонаж получил урон, возвращение в ген. штаб")
                await asyncio.sleep(1)
                await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
                print("Отправлено сообщение: 🏛 В ген. штаб")

                # Ожидаем достижения ген. штаба
                while True:
                    last_message = await self.client.get_messages(self.bot_id, limit=1)
                    if last_message:
                        lstr = last_message[0].message.split('\n')
                        if "Ты дошел до локации." in lstr[0]:
                            print("Достигнут ген. штаб")
                            await asyncio.sleep(2)
                            await self.client.send_message(self.bot_id, "💖 Пополнить здоровье")
                            print("Отправлено сообщение: 💖 Пополнить здоровье")
                            await self.wait_for_health_refill()
                            await self.client.send_message(self.bot_id, "💦Водяное направление")
                            print("Отправлено сообщение: 💦Водяное направление")
                            return
                    await asyncio.sleep(1)

            print("Ни одно из условий не выполнено, повторная проверка через 10 секунд")

    async def wait_for_health_refill(self):
        while True:
            last_message = await self.client.get_messages(self.bot_id, limit=1)
            if last_message:
                lstr = last_message[0].message.split('\n')
                if any("Здоровье пополнено" in line for line in lstr):
                    await asyncio.sleep(1)
                    return
            await asyncio.sleep(1)


    async def wait_for_confirmation(self):
        try:
            # Создаем Future для ожидания подтверждения
            confirmation_future = asyncio.Future()

            @self.client.on(events.NewMessage(from_users=[self.bot_id]))
            async def confirmation_handler(event):
                if "Вы успешно добавили" in event.message.text:
                    confirmation_future.set_result(True)
                    print("Получено подтверждение добавления ресурса.")
                else:
                    confirmation_future.set_result(False)
                    print("Получено сообщение, но это не подтверждение добавления ресурса.")

            # Ожидаем результат в течение 30 секунд
            result = await asyncio.wait_for(confirmation_future, timeout=30)

            # Удаляем обработчик события
            self.client.remove_event_handler(confirmation_handler)

            return result

        except asyncio.TimeoutError:
            print("Тайм-аут: не получено подтверждение в течение 30 секунд.")
            return False
    
    async def craft_rec(self, lstr):
        print("# Начинаем процесс крафта")

        # Проверяем наличие рецепта
        if "Рецепт" in lstr[2]:
            # Пропускаем первые 4 строки
            lstr = lstr[4:]
            await asyncio.sleep(2)
            # Обработка крафта рецепта
            for str_line in lstr:
                if str_line == "":
                    break
                craft_cmd = re.search(r" (/.*)$", str_line)
                if craft_cmd:
                    print(f"Отправляем команду крафта: {craft_cmd.group(1)}")
                    await self.client.send_message(self.bot_id, craft_cmd.group(1))                                
                    # Ожидание подтверждения
                    confirmation = await self.wait_for_confirmation()
                    if not confirmation:
                        print("Не получено подтверждение добавления ресурса. Прерываем крафт.")
                        return

                    await asyncio.sleep(2) 


            # Отправка команды "🔨 Скрафтить"
            await asyncio.sleep(2)
            await self.client.send_message(self.bot_id, "🔨 Скрафтить")
        else:
            # Проверяем наличие составляющих
            if any("Составляющие:" in line for line in lstr):
                await self.check_talisman(lstr)

    async def check_talisman(self, lstr):
        print("# Проверяем талисман")
        tali_type = {"☣": 0, "🔵": 1, "⚫": 2, "🔴": 3, "🟢": 4}
        pattern = r'(🔵|🟢|⚫|🔴|☣)\s*\+\s*(\d+)'

        talismans_burned = False

        for line in lstr:
            if "Составляющие:" in line:
                continue
            if "Талики сгорели💔" in line:
                talismans_burned = True
                break  # Прерываем цикл, так как талисманы сгорели

            match = re.search(pattern, line)
            if match:
                found_symbol = match.group(1)
                talisman_level = int(match.group(2))
                talisman_info = (tali_type.get(found_symbol), talisman_level)
                if talisman_info:
                    print(f"# Найден талисман: тип {found_symbol}, уровень {talisman_level}")
                    self.last_talisman_info = talisman_info  # Сохраняем информацию о последнем талисмане
                    if talisman_level < 5: #уровень заточки
                        await asyncio.sleep(1)
                        await self._insert_talisman_and_stone(*talisman_info, lstr)
                    else:
                        print("Ура! Талисман достиг максимального уровня.")
                    return talisman_info

        if talismans_burned:
            if self.last_talisman_info:
                print("# Талисманы сгорели, создаем новый талисман с уровнем 1")
                new_talisman_info = (self.last_talisman_info[0], 1)
                await self._insert_talisman_and_stone(*new_talisman_info, lstr)
                return new_talisman_info
            else:
                print("# Талисманы сгорели, но нет информации о предыдущем талисмане")
                return None

        print("# Талисман не найден, что не должно происходить в нормальной ситуации")
        return None

    async def _insert_talisman_and_stone(self, talisman_type, talisman_level, lstr):
        print(f"# Получены данные: talisman_type={talisman_type}, talisman_level={talisman_level}")
        print("# Вставка талисмана и камня")
        await asyncio.sleep(1)
        await self.client.send_message(self.bot_id, "👨‍🏭 Помощник")
        await asyncio.sleep(2)

        # Получаем последнее сообщение с кнопками
        self.rf_message = await self.get_latest_message_with_buttons()
        if not self.rf_message:
            print("# self.rf_message is None, не можем выполнить клик")
            return False

        stone_type = 8 if talisman_level < 3 else 10
        print(f"# Выбран камень типа {stone_type}")

        await self.rf_message.click(stone_type)
        await asyncio.sleep(2)

        await self.rf_message.click(talisman_type)
        await asyncio.sleep(2)

        messages = await self.get_latest_messages(limit=2)
        if any(message.split('\n')[0].startswith("❌Не было добавлено:") for message in messages):
            print("# Обнаружено 'Не было добавлено', останавливаем процесс")
            return False

        # Этот блок выполнится, только если условие выше не выполнится
        print("# Компоненты добавлены успешно, продолжаем крафт")
        await self._craft_and_process_result(lstr)

        return True

    async def _craft_and_process_result(self, lstr):
        await asyncio.sleep(1)
        print("# Крафт и проверка результата")
        await self.client.send_message(self.bot_id, "🔨 Скрафтить")

    async def get_latest_message_with_buttons(self):
        print("# Получаем последнее сообщение с кнопками")
        messages = await self.client.get_messages(self.bot_id, limit=1)
        await asyncio.sleep(2)
        for msg in messages:
            if msg.buttons:
                return msg
        return None

    async def get_latest_messages(self, limit=2):
        print("# Получаем последние сообщения")
        last_messages = await self.client.get_messages(self.bot_id, limit=2)
        await asyncio.sleep(2)
        return [message.message for message in last_messages]

    async def check_group_list(self, lstr):
        # По умолчанию считаем, что мы лидеры пещеры
        self.is_cave_leader = True

        print(" а вот что по составу")
        print(f" Моё текущее здоровье: {self.my_health}")

        # Проверка первой строки на содержание идентификатора лидера
        if not lstr or not lstr[0].endswith("/group_guild_join_715480502"):
            print("ты не пативод")
            self.is_cave_leader = False
        else:
            self.is_cave_leader = True  # Лидер пещеры
            print("ты пативод")

        lstr.reverse()
        h_id = 0

        for line in lstr:
            if not line:
                break
            in_str_find = re.search("/p_guild_exc_(\d+)", line)
            if in_str_find:
                h_id = int(in_str_find.group(1))
                continue
            in_str_find = re.search("\d\) .*\[.*\](.*)🏅\d+ур\. (.*)", line)
            if not in_str_find:
                break
            nick = in_str_find.group(1)
            if nick == "Ros_Hangzhou":
                continue
            sost = in_str_find.group(2)

            if "Мертв" in sost:
                if "🥤" in sost and self.is_cave_leader and self.is_in_caves:
                    await self.client.send_message(h_id, "Рес")

                continue

            if "💖" in sost:
                str_hp = re.search("❤️(\d+)/\d+", sost)
                helth = int(str_hp.group(1))
                if self.is_cave_leader and self.is_in_caves:
                    if helth < 1500:
                        await self.client.send_message(h_id, "Хил")
                    elif 1500 <= helth < 2000:
                        await self.client.send_message(h_id, "Шаг или хил?")


                continue
            



    def kroha_pativod(self):
        print("Устанавливаем обработчик сообщений для kroha_pativod")
        
        @self.client.on(events.NewMessage(from_users=[353501977]))
        async def handle_specific_user_messages(event):
            if event.is_private:  # Проверяем, что сообщение пришло из личного чата
                print(f"Получено новое личное сообщение от пользователя 353501977: {event.message.text}")
                
                message_text = event.message.text.lower().strip()
                print(f"Преобразованный текст сообщения: {message_text}")
                
                keywords = ['банка', 'банку', 'пить']
                
                if message_text in keywords:
                    print(f"Обнаружено точное совпадение с ключевым словом: {message_text}")
                    print("Отправляем команду /drink_102")
                    await self.client.send_message(self.bot_id, "/drink_102")
                    print("Команда /drink_102 отправлена")
                else:
                    print("Точное совпадение с ключевыми словами не обнаружено")
            else:
                print("Сообщение не из личного чата, игнорируем его.")

        print("Обработчик сообщений для kroha_pativod успешно установлен")
        print(f"Ваше текущее здоровье: {self.my_health}")
        print(f"Находитесь ли вы в пещерах: {self.is_in_caves}")
        print(f"Являетесь ли вы лидером пещер: {self.is_cave_leader}")




    async def vihod_s_caves(self, lstr):
        self.is_cave_leader = any("/group_guild_join_715480502" in line for line in lstr)
        print(f"{'Ты пативод' if self.is_cave_leader else 'Ты не пативод'}")

        if not self.is_in_caves:
            print("Ты не в пещерах")
            return
        print("Ты в пещерах")

        total_health = 0
        alive_count = 0
        alive_has_heal = False
        group_has_res = False
        group_members = []

        for line in lstr:
            if not line.strip():
                continue
            
            if member_id := re.search(r"/p_guild_exc_(\d+)", line):
                group_members.append(int(member_id.group(1)))
                continue
            
            if member_info := re.search(r"\d\) .*\[.*\](.*?)🏅\d+ур\. (.*)", line):
                nick, status = member_info.groups()
                nick = nick.strip()
                
                is_alive = "Мертв" not in status
                health = 0
                has_heal = "💖" in status
                has_res = "🥤" in status
                
                if is_alive:
                    alive_count += 1
                    if health_match := re.search(r"❤️(\d+)/\d+", status):
                        health = int(health_match.group(1))
                        total_health += health
                    alive_has_heal = alive_has_heal or has_heal
                
                # Учитываем рес у любого игрока, живого или мертвого
                group_has_res = group_has_res or has_res
                
                player_status = f"{nick}: HP {health}, {'alive' if is_alive else 'dead'}, {'has hil' if has_heal else 'no hil'}, {'has res' if has_res else 'no res'}"
                print(player_status)

        print(f"\nОбщее здоровье группы: {total_health}")
        print(f"Живых: {alive_count}, Живые с хилками: {'да' if alive_has_heal else 'нет'}, Группа с ресами: {'да' if group_has_res else 'нет'}")

        if total_health < 2000 and not alive_has_heal and not group_has_res:
            message = f"{'Ты лидер' if self.is_cave_leader else 'Ты не лидер'}, пора на выход. Общее здоровье: {total_health}, нет хилок у живых и ресов в группе"
            await self.client.send_message(715480502, message)
            print(message)
            
            if self.is_cave_leader:
                await self.rf_message.click(3)
                for member_id in group_members:
                    if member_id != 715480502:
                        await self.client.send_message(member_id, "Выходим из пещеры")
                        print(f"Отправлено сообщение участнику {member_id}: Выходим из пещеры")
        else:
            print(f"Ещё рано на выход. Общее здоровье: {total_health}, Живых: {alive_count}")