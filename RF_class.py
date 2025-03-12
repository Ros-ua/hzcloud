import re
import sys
import asyncio
import random
from random import randint
from telethon import events
from addons import qHash
import datetime
import threading

class RF:
    bot_id = 577009581
    is_run = False
    rf_message = None
    is_in_caves = is_in_gh = is_has_hil = is_has_res = False
    cave_leader_id = 715480502
    my_health = my_max_health = 12022
    hp = "/bind_wear_1723376879927d"
    chv = "/bind_wear_1741678312790d"
    tomat_id = 278339710
    kroha_id = 353501977
    tamplier_id = 681431333
    john_id = 562559122
    pchelka_id = 255360779
    ded_id = 1757434874

    your_name = "Ros_Hangzhou"

    def __init__(self, client):
        self.client = client
        self.group = [[False, False, False, False] for _ in range(6)]
        self.my_group_pos = -1
        self.health_re = re.compile(r"Здоровье пополнено \D+(\d+)/(\d+)")
        self.battle_re = re.compile(r"^Сражение с .*$")
        self.damage_re = re.compile(r"(\d+)$")
        self.arrival_re = re.compile(r'.*прибудешь через\s*(\d+)\s*мин\.\s*(\d+(?:\.\d+)?)\s*сек\.')
        self.last_talisman_info = None  # (type, level)
        self.players = {
            "Нежный 🍅": self.tomat_id,
            "🐾ᏦᎮᎧχᏗ": self.kroha_id,
            "𝕴𝖆𝖒𝖕𝖑𝖎𝖊𝖗": self.tamplier_id,
            "John Doe": self.john_id,
            "๖ۣۜᗯαsͥpwͣoͫℝt🐝": self.pchelka_id,
            "kingRagnar🤴🏼": self.ded_id
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
        self.common_cave()
        self.fast_cave = False
        self.hp_12022 = "/bind_wear_172337681533126"  # 12022 HP
        self.hp_10425 = "/bind_wear_17281182669012i"  # 10425 HP
        self.hp_8952 = "/bind_wear_17281183336251s"   # 8952 HP
        self.hp_7434 = "/bind_wear_1728118388328p"    # 7434 HP
        self.hp_5852 = "/bind_wear_1728118474616c"    # 5852 HP
        self.hp_5139 = "/bind_wear_171967083952510"   # 5139 HP
        self.last_bind = None
        self.after_bind = None
        self.cave_task_running = False
        self.last_set_kingRagnar = None
        self.waiting_for_captcha = False  # Флаг ожидания капчи
        self.is_moving = False  # Добавляем этот флаг
        self.move_timer = None
        self.in_castle = False  # Флаг нахождения в замке
        self.v_terminale = False
        self.kopka = False
        self.last_energy_message = None
        self.got_reward = None
        self.is_training = False
        self.extra_hil = True
        self.mobs = True
        self.extra_hill_hp = 300   # Здоровье, при котором используется экстренный хил
        self.ned_hill_hp = 1300    # Здоровье, при котором нужен обычный хил
        self.bezvgroup = -1002220238697  # ID группы "без в"
        self.group59 = -1001323974021  # ID группы "59" 
        self.pvpgoheal = 5000
        self.go_term_Aquilla = False  # флаг по умолчанию
        self.go_term_Basilaris = False   # флаг по умолчанию
        self.terminal_type = None





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
        
        # Лечимся, если здоровье ниже 300

        if self.my_health <= self.extra_hill_hp and self.is_has_hil and self.extra_hil:

            await self.rf_message.click(0)
            self.is_has_hil = self.extra_hil = False
            print(f"Здоровье критически низкое ({self.my_health}). Отправляем запрос на хил.")
            print(f"Статус has_hil обновлен: {self.is_has_hil}")  # Добавлен вывод статуса has_hil

        # Логика смены снаряжения в зависимости от текущего здоровья
        elif self.extra_hill_hp <= self.my_health <= self.ned_hill_hp:

            await asyncio.sleep(10)  # Ждем 10 секунды
            if not self.isPlayerDead() and self.last_bind != self.hp_12022 and self.is_has_hil and self.extra_hil:  # Перенесено сюда
                self.is_has_hil = False
                await self.client.send_message(self.bot_id, self.hp_12022)  # Надеваем 12022 HP
                print(f"Сменили бинд на: {self.hp_12022} (макс. здоровье: 12022)")
                await asyncio.sleep (1)
                await self.rf_message.click(0)  # Выполняем клик
                self.my_health = self.my_max_health = 12022
                self.last_bind = self.hp_12022
                print(f"Статус has_hil обновлен: {self.is_has_hil}")  # Добавлен вывод статуса has_hil

        elif self.ned_hill_hp < self.my_health <= 5139:  # Если здоровье между 1300 и 5139
            if self.last_bind != self.hp_5139:
                await self.client.send_message(self.bot_id, self.hp_5139)  # Надеваем 5139 HP
                print(f"Сменили бинд на: {self.hp_5139} (макс. здоровье: 5139)")
                self.last_bind = self.hp_5139
        elif 5139 < self.my_health <= 5852:  # Если здоровье между 5139 и 5852
            if self.last_bind != self.hp_5852:
                await self.client.send_message(self.bot_id, self.hp_5852)  # Надеваем 5852 HP
                print(f"Сменили бинд на: {self.hp_5852} (макс. здоровье: 5852)")
                self.last_bind = self.hp_5852
        elif 5852 < self.my_health <= 7434:  # Если здоровье между 5852 и 7434
            if self.last_bind != self.hp_7434:
                await self.client.send_message(self.bot_id, self.hp_7434)  # Надеваем 7434 HP
                print(f"Сменили бинд на: {self.hp_7434} (макс. здоровье: 7434)")
                self.last_bind = self.hp_7434
        elif 7434 < self.my_health <= 8952:  # Если здоровье между 7434 и 8952
            if self.last_bind != self.hp_8952:
                await self.client.send_message(self.bot_id, self.hp_8952)  # Надеваем 8952 HP
                print(f"Сменили бинд на: {self.hp_8952} (макс. здоровье: 8952)")
                self.last_bind = self.hp_8952
        elif 8952 < self.my_health <= 10425:  # Если здоровье между 8952 и 10425
            if self.last_bind != self.hp_10425:
                await self.client.send_message(self.bot_id, self.hp_10425)  # Надеваем 10425 HP
                print(f"Сменили бинд на: {self.hp_10425} (макс. здоровье: 10425)")
                self.last_bind = self.hp_10425
        elif 10425 < self.my_health < 12022:  # Если здоровье между 10425 и 12022
            if self.last_bind != self.hp_12022:
                await self.client.send_message(self.bot_id, self.hp_12022)  # Надеваем 12022 HP
                print(f"Сменили бинд на: {self.hp_12022} (макс. здоровье: 12022)")
                self.last_bind = self.hp_12022
        else:
            print(f"Здоровье достаточно высокое ({self.my_health}). Лечение не требуется.")


    async def set_moving_flag(self, duration):
        self.is_moving = True
        self.in_castle = False
        self.is_nacheve_active = False
        self.kopka = False  # Сбрасываем флаг замка при начале движения
        if self.move_timer:
            self.move_timer.cancel()
        self.move_timer = asyncio.create_task(self.reset_moving_flag(duration))

    async def reset_moving_flag(self, duration):
        await asyncio.sleep(duration)
        self.is_moving = False

    async def msg_parce(self, message):
        if not self.is_run:
            return

        lstr = message.message.split('\n')
        val = qHash(lstr[0])
        if val == 0:
            return
        print(val, lstr[0])

        # в пещерах
        if any(phrase in line for line in lstr for phrase in [
            "булочка"
        ]):    
            print("булочка")
        elif any(phrase in line for line in lstr for phrase in [
            "ты мертв, дождись пока воскреснешь"
        ]):    
            self.is_has_hil = self.extra_hil = True
            self.after_bind = self.hp_12022
        elif any(phrase in line for line in lstr for phrase in [
            "Вы больше не можете лечиться"
        ]):    
            self.is_has_hil = self.extra_hil = False
            self.after_bind = self.hp_12022
        
        elif any(phrase in line for line in lstr for phrase in [
            "Ваша группа наткнулась"
        ]):
            await asyncio.sleep(10)
            if self.is_in_caves:  # Изменено на self.is_in_caves
                await self.client.send_message(self.bot_id, "⚖️Проверить состав")
                await asyncio.sleep(20)
                self.last_bind = self.after_bind
                
                # Добавляем проверку текущего здоровья перед autoHeal
                await self.client.send_message(self.bot_id, "/hero")
                await asyncio.sleep(1)  # Ждем ответа от бота
                response = await self.client.get_messages(self.bot_id, limit=1)
                
                if response:
                    health_line = next((line for line in response[0].text.split('\n') if '❤Здоровье:' in line), None)
                    if health_line:
                        match = re.search(r'❤Здоровье:\s*(\d+)', health_line)
                        if match:
                            self.my_health = int(match.group(1))
                            print(f"Текущее здоровье перед autoHeal: {self.my_health}")
                            
                            # Специальная логика: если здоровье ниже extra_hill_hp, ведем себя как между extra и ned
                            if self.my_health < self.extra_hill_hp:  # Например, 100 HP < 300
                                print(f"Здоровье ({self.my_health}) ниже {self.extra_hill_hp}, применяем логику как для {self.extra_hill_hp}-{self.ned_hill_hp}")
                                await asyncio.sleep(8)  # Ждем 8 секунд, как в случае между extra и ned
                                if not self.isPlayerDead() and self.last_bind != self.hp_12022 and self.is_has_hil and self.extra_hil:
                                    self.is_has_hil = False
                                    await self.client.send_message(self.bot_id, self.hp_12022)  # Надеваем 12022 HP
                                    print(f"Сменили бинд на: {self.hp_12022} (макс. здоровье: 12022)")
                                    await asyncio.sleep(1)
                                    await self.rf_message.click(0)  # Выполняем клик для хила
                                    self.my_health = self.my_max_health = 12022
                                    self.last_bind = self.hp_12022
                                    print(f"Статус has_hil обновлен: {self.is_has_hil}")
                                return  # Завершаем выполнение блока после хила
                        else:
                            print("Не удалось извлечь здоровье из строки")
                    else:
                        print("Не найдена строка с информацией о здоровье")
                else:
                    print("Не получен ответ от бота на /hero")
                
                await self.autoHeal()  # Вызываем autoHeal() для всех остальных случаев

        if any(phrase in lstr[0] for phrase in [
            "Панель управления", 
            "Ты направляешься в пещеры на фуникулере",
            "Ты направляешься в пещеры на санях",
        ]):
            self.is_in_caves = self.is_has_hil = self.is_has_res = self.extra_hil = True
            self.my_health = self.my_max_health = 12022
            self.after_bind = self.hp_12022
            await asyncio.sleep(randint(4, 6))
            await self.client.send_message(self.bot_id, "⚖️Проверить состав")
            print("в пещерах")

        elif any(phrase in line for line in lstr for phrase in [
            "Здоровье пополнено",
        ]):
            self.is_has_hil = False  
            self.after_bind = self.hp_12022
            print(f"Статус has_hil обновлен: {self.is_has_hil}")  # Добавлен вывод статуса has_hil
            self.waiting_for_captcha = False  # Флаг ожидания капчи

        elif any(phrase in line for line in lstr for phrase in [
            "Ты снова жив",
            "Вы больше не можете воскрешаться",
        ]):
            self.reset_health()
            print(self.my_health, self.my_max_health)
            self.after_bind = self.hp_12022
        #     # на новый год 
        #     if not self.is_in_caves:  # Используем существующее условие
        #         await asyncio.sleep(1)
        #         await self.client.send_message(self.bot_id, "🌋 Краговые шахты")

        elif any(
            phrase in line for line in lstr for phrase in [
                "Ожидай завершения",
            ]
        ) or any(re.search(r"одержал победу над .*Ros_Hangzhou", line) for line in lstr):
            await asyncio.sleep(5)
            if self.is_has_res and self.is_in_caves:  # Проверяем, что is_has_res равно True и мы в пещерах
                self.is_has_res = False
                await asyncio.sleep(10)
                await self.client.send_message(self.bot_id, self.hp_12022)  # Надеваем бинд на самое большое HP
                await asyncio.sleep(3)  # Ждем 3 секунды перед кликом
                await self.rf_message.click(1)
                self.my_health = self.my_max_health = 12022  # Устанавливаем значения для my_health и my_max_health
                print(self.my_health, self.my_max_health)
                self.last_bind = self.hp_12022
        elif "Сражение с" in lstr[0] and not any("Рюкзак" in line for line in lstr):
            self.in_battle = True   
        elif "К сожалению ты умер" in lstr:
            self.in_battle = False     

        elif "Ваша группа замерзнет через 5 минут" in lstr[0]:
            await asyncio.sleep(1)
            await self.rf_message.click(2)

        elif "Ваша группа восстановила силы" in lstr[0]:
            if self.fast_cave:  # Проверка значения fast_ceve
                await asyncio.sleep(1)
                await self.rf_message.click(2)
        elif "Ваша группа прибудет в ген. штаб через" in lstr[0]:
            print("чувачок, ты закончил пещеру")
            await asyncio.sleep(1)
            self.fast_cave = False
            await self.client.send_message(self.bot_id, RF.hp)  # переодеться для мобов
            await self.check_arrival()
        elif lstr[0].startswith("Состав:"):
            print("что там по составу")
            # Проверка баллов
            score_line = lstr[1]  # Предполагаем, что баллы находятся на второй строке
            if "Баллы:" in score_line:
                score = int(score_line.split(":")[1].strip().split()[0])  # Извлекаем значение баллов
                if score == 11:
                    self.fast_cave = True  # Устанавливаем флаг fast_cave в True
                    print("Установлен флаг fast_cave в True, баллы равны 11.")
                else:
                    print(f"Баллы не равны 11, текущее значение: {score}")  # Отладочное сообщение
            await asyncio.sleep(1)
            await self.check_group_list(lstr)
            # await asyncio.sleep(2)
            await self.vihod_s_caves(lstr)
            # await asyncio.sleep(2)
            await self.hp_in_caves(lstr)
            # await asyncio.sleep(2)
            await self.hp_in_caves_kingRagnar(lstr)
            # await asyncio.sleep(2)
            await self.time_cave(lstr)


        elif lstr[0].endswith("не в ген. штабе]"):
            # Проверяем, есть ли 🐾ᏦᎮᎧχᏗ в сообщении
            if "🐾ᏦᎮᎧχᏗ" in lstr[0]:
                await message.forward_to(self.bezvgroup)  # специальная группа для 🐾ᏦᎮᎧχᏗ без в 
            else:
                await message.forward_to(self.group59)  # стандартная группа для остальных 59

            # Ищем всех игроков, упомянутых в сообщении
            players_not_in_gh = re.findall(r'(Нежный 🍅|🐾ᏦᎮᎧχᏗ|𝕴𝖆𝖒𝖕𝖑𝖎𝖊𝖗|John Doe|๖ۣۜᗯαsͥpwͣoͫℝt🐝|kingRagnar🤴🏼)', lstr[0])
            if players_not_in_gh:
                for player in players_not_in_gh:
                    if player in self.players:
                        print(f"{player} не в ген. штабе")
                        await self.client.send_message(self.players[player], "Давайте в ген. штаб")
            if self.mobs:  # Проверяем, включен ли флаг для мобов
                await self.client.send_message(self.bot_id, "🔥 61-65 Лес пламени")  # для мобов
            else:
                print("bag bag bag")  # для данжей
        elif "Если ты хочешь вернуть группу" in lstr[0]:
            await self.client.send_message(self.bot_id, "22")


        # #     тесты
        # elif "Содержимое" in lstr[0]:
        #     print("bag bag bag")
        #     # asyncio.create_task(self.time_cave())  # Сохраняем ссылку на задачу
        #     await self.time_cave()
        #     self.cave_task = asyncio.create_task(self.time_cave())  # Сохраняем ссылку на задачу
        # asyncio.create_task(self.time_cave())  # Сохраняем ссылку на задачу
        #     self.cave_task_running = True  # Устанавливаем флаг, что задача запущена
        #     await self.client.send_message(715480502, "Задача time_cave запущена.")  # Отправляем сообщение
        # elif "усилители" in lstr[0]:  # Проверяем наличие слова "усилители"
        #     if self.cave_task_running:  # Проверяем, запущена ли задача
        #         print("Остановка задачи time_cave.")
        #         self.cave_task.cancel()  # Отменяем задачу
        #         self.cave_task_running = False  # Сбрасываем флаг
        #         print("Задача time_cave отменена.")
        #         await self.client.send_message(715480502, "Задача time_cave отменена.")  # Отправляем сообщение
        #     # Получаем текущее время на сервере
        #     current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #     await self.client.send_message(715480502, f"Текущее время на сервере: {current_time}")
       
       
        # на страже
        elif "Бой с боссом будет происходить в автоматическом режиме." in lstr[0]:
            print("дошел до стража")
            await self.straj()
        elif "Босс еще не появился. Проход в локацию закрыт!" in lstr[0]:  # если умер на страже и снова хочешь идти на стража
            await asyncio.sleep(1)
            await self.client.send_message(self.bot_id, "🔥 61-65 Лес пламени")

        # на чв
        elif "Ты был убит!" in lstr[0]:  # Добавлено условие для проверки фразы
            print("Персонаж был убит!")
            await self.client.send_message(self.bot_id, RF.chv)
            await self.check_arrival()

        elif any(phrase in line for line in lstr for phrase in [
            "Алтарь Эйви",
            "Алтарь Тир",
        ]):
            self.got_reward = False  # Сбрасываем флаг получения награды
            if self.go_term_Aquilla:  # проверка флага
                await asyncio.sleep(5)
                await self.client.send_message(self.bot_id, "🤖 Терминал Aquilla")
            else:
                # Если флаг не сработал, вызываем nacheve()
                await self.nacheve()
            self.terminal_type = "🤖 Терминал Aquilla"  # Определяем тип терминала

        elif any(phrase in line for line in lstr for phrase in [
            "Алтарь Иса",
            "Алтарь Гебо",
        ]):
            self.got_reward = False  # Сбрасываем флаг получения награды
            if self.go_term_Basilaris:  # проверка флага
                await asyncio.sleep(5)
                await self.client.send_message(self.bot_id, "👩‍🚀 Терминал Basilaris")
            else:
                # Если флаг не сработал, вызываем nacheve()
                await self.nacheve()
            self.terminal_type = "👩‍🚀 Терминал Basilaris"  # Определяем тип терминала

        elif any(phrase in line for line in lstr for phrase in [
            "Ты направляешься к терминалу",
        ]):
            await asyncio.sleep(1)
            # Используем переменную terminal_type для отправки сообщения Валере
            message = f"буду в {self.terminal_type} через тик"
            await self.client.send_message(self.tamplier_id, message)
            # Отправляем в группу 59 только если терминал Aquilla
            if self.terminal_type == "🤖 Терминал Aquilla":
                await self.client.send_message(self.group59, message)

            # await self.client.send_message(self.bezvgroup, "🤖 Терминал Aquilla") # пересылка алтаря без в


        elif any(phrase in line for line in lstr for phrase in [
            "Ты прибыл к алтарю",
            "ты можешь перейти к терминалу только из алтаря",
        ]):
            self.got_reward = False  # Сбрасываем флаг получения награды
            await self.nacheve()

        elif any(phrase in line for line in lstr for phrase in [
            "бой за терминал будет происходить автоматически",
        ]):
            self.v_terminale = True
            self.got_reward = False  # Сбрасываем флаг получения награды
            await self.nacheve()

        # Обрабатываем фразу о бронзе
        elif any("Бронза уже у тебя в рюкзаке" in line for line in lstr):  # Проверяем фразу о бронзе
            # self.mobs = False  # Устанавливаем флаг для данжей
            # await self.client.send_message(715480502, "Ходим в данжи")  # Сообщение об изменении флага
            # await self.client.send_message(self.bezvgroup, "Ходим в данжи")  # Сообщение об изменении флага без в
            # await self.client.send_message(self.group59, "Ходим в данжи")  # Сообщение об изменении флага 59
            if not self.got_reward:  # Проверка, что got_reward был False
                self.got_reward = True  # Устанавливаем флаг получения награды

                # Общие действия
                await asyncio.sleep(1)  # Задержка перед следующим действием
                await self.client.send_message(self.bot_id, RF.hp)  # Переодеться для мобов
                asyncio.create_task(self.set_nacheve_inactive_after_delay())  # Устанавливаем флаг через 2 минуты


        # Обрабатываем фразу о героическом сражении
        elif any("За то, что ты героически сражался" in line for line in lstr):  # Проверяем вхождение подстроки
            if not self.got_reward:  # Проверка, что got_reward был False
                self.got_reward = True  # Устанавливаем флаг получения награды

                # Общие действия
                await asyncio.sleep(1)  # Задержка перед следующим действием
                await self.client.send_message(self.bot_id, RF.hp)  # Переодеться для мобов
                asyncio.create_task(self.set_nacheve_inactive_after_delay())  # Устанавливаем флаг через 2 минуты



        elif any(phrase in line for line in lstr for phrase in [
            "Ты прибыл в краговые шахты",
            "пока не началась война",
            "Ты прибыл на"
        ]):
            await asyncio.sleep(1)
            await self.client.send_message(self.bot_id, "⛏Рудник")
        elif "[на время боевых действий проход закрыт]" in lstr[0]:
            print("Проход закрыт. Подготовка к выбору алтаря.")
            await self.prepare_for_caves()
            await asyncio.sleep(1)
            altar_to_send = self.cmd_altar if self.cmd_altar else self.choose_random_altar()
            await self.client.send_message(self.bot_id, altar_to_send)
            # await self.client.send_message(self.group59, altar_to_send) # пересылка алтаря в группу 59
            await self.client.send_message(self.tamplier_id, altar_to_send) # пересылка алтаря Валере
            # await self.client.send_message(self.bezvgroup, altar_to_send) # пересылка алтаря без в 


        elif "Ты прибыл в ⛏рудник." in lstr[0]:
            await asyncio.sleep(1)
            await self.client.send_message(self.bot_id, "🖲 Установить АБУ")
            
        elif any(phrase in line for line in lstr for phrase in ["После боевых действий ты снова сможешь"]):
            if not any([self.is_in_caves, self.kopka, self.is_moving, self.waiting_for_captcha]):
                await asyncio.sleep(15)
                await self.client.send_message(self.bot_id, RF.chv)
                await asyncio.sleep(3)
                await self.client.send_message(self.bot_id, "💖 Пополнить здоровье")
                print("Отправлено сообщение: 💖 Пополнить здоровье")
                await self.wait_for_health_refill()
                await self.client.send_message(self.bot_id, "🌋 Краговые шахты")
                self.pvpgoheal = 5000 
                self.go_term_Aquilla = False
                self.go_term_Basilaris = False
        elif any(phrase in line for line in lstr for phrase in [
            "Удачи!"
        ]):  
            self.is_nacheve_active = True


              # на мобах
        elif any(phrase in line for line in lstr for phrase in  [
            "пойти в 61-65 Лес пламени", 
            "что хочешь отправиться в пещеры?",
            "попробуй"
            ]):
            await asyncio.sleep(1)
            await message.click(0)
        elif "Что будем делать?" in lstr[-1] or "Ты наткнулся на" in lstr[-1]:
            print("будем бить")
            await asyncio.sleep(1)
            await self.client.send_message(self.bot_id, "🔪 Атаковать")

        elif any(phrase in line for line in lstr for phrase in ["Энергия: 🔋0/5", "[недостаточно энергии]"]):
            print("нет энергии")
            await self.handle_no_energy()
        elif any(phrase in line for line in lstr for phrase in [f"Энергия: 🔋{i}/5" for i in range(1, 5)]):
            print("есть энергия")
            
            # Ищем строку с информацией о здоровье во всём сообщении с учётом возможных пробелов и символов
            health_line = next((line for line in lstr if re.search(r"Здоровье: ❤\d+/\d+", line)), None)
            
            if health_line:
                # Извлекаем текущее здоровье
                health_match = re.search(r"Здоровье: ❤(\d+)/\d+", health_line)
                if health_match:
                    current_health = int(health_match.group(1))
                    print(f"Текущее здоровье: {current_health}")
                    
                    # Проверяем, меньше ли здоровье 8000
                    if current_health < 8000:
                        await self.handle_energy_found()
                    else:
                        print("Здоровье больше или равно 8000, отправляем сообщение 🐺По уровню.")
                        await asyncio.sleep(1)
                        await self.client.send_message(self.bot_id, "🐺По уровню")
                else:
                    print("Не удалось извлечь здоровье из строки.")
            else:
                print("Строка с информацией о здоровье не найдена.")


        elif any(f"+1 к энергии 🔋{i}/5" in lstr[0] for i in range(1, 6)):
            self.last_energy_message = message  # Сохраняем сообщение о получении энергии
            
            # Проверяем, увеличилась ли энергия на 4 или 5
            if any(f"+1 к энергии 🔋{i}/5" in lstr[0] for i in (4, 5)):
                await self.handle_energy()  # Вызываем обработчик энергии только для 4 и 5



        # # данжи

        elif "Ты уверен, что хочешь попробовать пройти данж" in lstr[0]:
            await asyncio.sleep(1)
            await message.click(0)
            await self.dangego()
        elif any(phrase in line for line in lstr for phrase in  [
            "Общая добыча:", 
            ]):
            # Пересылаем сообщение
            forwarded_message = await message.forward_to(5596818972)  # результат данж пересылка 

            # Ждём 5 секунд
            await asyncio.sleep(5)

            # Удаляем оба сообщения
            await forwarded_message.delete()

        
        # misc
        elif val == 1550650437:  # ⚒ Кузня - 5 ур.
            await self.craft_rec(lstr)
        elif val == 2509085174:  # Рецепты:
            return
        elif any(phrase in line for line in lstr for phrase in  [
            "данное действие можно выполнять только из ген. штаба",
            "В данную локацию можно перейти из ген. штаба!",
            "У тебя нет"
            ]):
            await asyncio.sleep(1)
            await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
            if self.mobs:  # Проверяем, включен ли флаг для мобов
                await self.check_arrival()  # для мобов
            else:
                await self.check_arrival_dange()  # для данжей

        elif any(phrase in lstr[0] for phrase in [
            "⚠️Прежде чем выполнять какие-то действия в игре",
            "Введите, пожалуйста, текст с картинки."
        ]):
            print("Капча получена")
            await self.client.send_message(715480502, "Капча получена")  # Отправляем сообщение
            self.waiting_for_captcha = True # Флаг ожидания капчи
            # sys.exit()
        elif (match := self.arrival_re.search(lstr[0])):  # Проверяем совпадение для строки прибытия
            minutes = int(match.group(1))
            seconds = float(match.group(2))
            duration = int(minutes * 60 + seconds)
            self.waiting_for_captcha = False  # Сбрасываем флаг ожидания капчи
            self.v_terminale =  False
            await self.set_moving_flag(duration)
            print(f"Движение начато: {lstr[0]}, продолжительность: {duration} секунд")
        elif "Ты прибыл в замок" in lstr[0]:
            self.in_castle = True
            print("Прибыли в замок")
        elif "Ты успешно установил" in lstr[0]:
            self.kopka = True
            print("поставил абу")
        elif "Ты закончил тренировку" in lstr[0]:
            self.is_training = False
            await asyncio.sleep(1)
            await self.client.send_message(self.bot_id, "🔥 61-65 Лес пламени")
        elif "Ты начал тренировку" in lstr[0]:
            self.is_training = True
        # elif "Как долго ты хочешь тренировать питомца" in lstr[0]:
        #     await asyncio.sleep(1)
        #     await self.client.send_message(self.bot_id, "1")
        elif "Начать тренировку?" in lstr[-1]:
            await message.click(0)











        if not message.buttons:
            if val == 3190963077:  # ✨Добыча:
                await message.forward_to(self.group59) #группа 59
                # await message.forward_to(self.bezvgroup) #группа без В
            else:
                await self.checkHealth(lstr)
            return

        if val == 3190963077:  # ✨Добыча:
            self.rf_message = message
            await asyncio.sleep(2)
            await self.client.send_message(self.bot_id, "⚖️Проверить состав")
            return
        

    async def set_nacheve_inactive_after_delay(self):
        await asyncio.sleep(120)  # Ожидание 2 минуты
        self.is_nacheve_active = False

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
                
                # Проверка, выполняется ли действие
                if any(phrase in lstr[0] for phrase in [
                    "ты уже выполняешь",
                    "дождись пока воскреснешь"
                ]):
                    print("Действие уже выполняется, завершение функции")
                    return  # Завершение функции, если действие уже выполняется

                # Проверка других условий
                elif any(phrase in lstr[0] for phrase in [
                    "Ты дошел до локации.",
                    "Вы уже находитесь в данной локации.",
                    "Ваша группа вернулась в ген. штаб!" ,
                    "Ты снова жив👼"
                ]):    
                    self.is_in_caves = False  # Сбрасываем флаг здесь
                    await asyncio.sleep(2)
                    await self.client.send_message(self.bot_id, "💖 Пополнить здоровье")
                    await self.wait_for_health_refill()
                    await self.client.send_message(self.bot_id, "🔥 61-65 Лес пламени")
                    return
            await asyncio.sleep(1)



    async def arrival_hil(self):  # ходим на моба
        print("arrival_hil")

        while True:
            last_message = await self.client.get_messages(self.bot_id, limit=1)
            if last_message:
                lstr = last_message[0].message.split('\n')
                if any(phrase in lstr[0] for phrase in [
                    "Ты дошел до локации.",
                    "Вы уже находитесь в данной локации.",
                    "Ваша группа вернулась в ген. штаб!" ,
                    "Ты снова жив👼",
                    "успешно надел комлект"
                ]):    
                    await asyncio.sleep(2)
                    await self.client.send_message(self.bot_id, "💖 Пополнить здоровье")
                    await self.wait_for_health_refill()
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



        # Проверка HP терминала Aquilla
        for line in lstr:

            # Проверка HP терминала Basilaris
            if "Basilaris терминал:" in line:
                # Извлечение значения HP из строки
                hp_info = line.split('❤')[1].split('/')[0].strip()
                basilaris_hp = int(hp_info)
                print(f"Basilaris HP: {basilaris_hp}")

                # Проверка, если HP меньше 20 000
                if basilaris_hp < 20000:
                    self.go_term_Basilaris = False
                    print("HP Basilaris меньше 20000, прекращаем ходить.")


            if "Aquilla терминал:" in line:
                # Извлечение значения HP из строки
                hp_info = line.split('❤')[1].split('/')[0].strip()
                aquilla_hp = int(hp_info)
                print(f"Aquilla HP: {aquilla_hp}")

                # Проверка, если HP меньше 20 000
                if aquilla_hp < 20000:
                    self.go_term_Aquilla = False
                    print("HP Aquilla меньше 20000, прекращаем ходить.")


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
                # Если персонаж в терминале, не выбираем случайный алтарь
                if not self.v_terminale:
                    self.cmd_altar = self.choose_random_altar()
                    print(f"Алтари не найдены, выбран случайный алтарь: {self.cmd_altar}")
                else:
                    self.cmd_altar = None  # Не выбираем и не посылаем, если персонаж в терминале
                    print("Находимся в терминале, алтарь не выбран.")

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
                    await self.client.send_message(self.tamplier_id, self.cmd_altar) # пересылка алтаря Валере
                    # await self.client.send_message(self.bezvgroup, self.cmd_altar) # пересылка алтаря без в 


                    self.cmd_altar = None

                # Добавляем задержку в xx секунд перед следующей итерацией
                print("Ожидание 6 секунд перед следующей проверкой...")
                await asyncio.sleep(6)

        finally:
            # Убираем обработчик событий
            self.client.remove_event_handler(handle_rf_info)
            self.is_nacheve_active = False
            print("Завершаем работу на чв")


    async def calculate_pvp_health(self, lstr):
        """
        Метод для расчета здоровья после PvP-боя.
        Теперь мы отправляем команду /hero, получаем ответ и обновляем self.my_health.
        """
        # Отправляем команду /hero и ждем 1 секунду, чтобы бот успел ответить
        await self.client.send_message(self.bot_id, "/hero")
        await asyncio.sleep(1)  # Можно увеличить задержку, если бот отвечает медленно
        
        # Получаем последнее сообщение от бота
        response = await self.client.get_messages(self.bot_id, limit=1)

        if response:
            # Ищем строку с информацией о здоровье
            health_line = next((line for line in response[0].text.split('\n') if '❤Здоровье:' in line), None)
            
            if health_line:
                # Извлекаем текущее здоровье
                match = re.search(r'❤Здоровье:\s*(\d+)', health_line)
                if match:
                    self.my_health = int(match.group(1))  # Обновляем основное здоровье
                    print(f"Текущее здоровье обновлено: {self.my_health}")
                else:
                    print("Не удалось извлечь здоровье из ответа.")
            else:
                print("Не найдено информации о здоровье в ответе.")
        else:
            print("Не получено сообщение от бота.")

    async def process_bot_message(self, lstr):
        # Проверка сообщения о смерти или времени восстановления
        if lstr[-1].endswith("минут.") or "дождись пока воскреснешь" in lstr[0] or "был убит ядерной ракетой" in lstr[0]:
            print("Обнаружено сообщение о времени. Вызываем gokragi()")
            await self.gokragi()
            self.is_nacheve_active = False
            return True

        # Проверка на победу над противником
        if any("Ты одержал победу над" in line for line in lstr):
            print("Победа в бою. Проверяем здоровье.")
            
            # Вызываем метод для получения текущего здоровья
            await self.calculate_pvp_health(lstr)
            
            # Логика принятия решения на основе здоровья
            if self.my_health > self.pvpgoheal:
                print("Здоровье больше self.pvpgoheal. Переходим к следующему алтарю.")
                fight_message = f"Дерёмся дальше. Осталось здоровья: {self.my_health}"
                # await self.client.send_message(self.bezvgroup, fight_message)  # пересылка без в 
                await self.client.send_message(self.tamplier_id, fight_message)  # пересылка Валере
                return False  # Переход к следующему терминалу
            else:
                print("Здоровье меньше или равно self.pvpgoheal. Отправляемся в ген. штаб для хила.")
                await asyncio.sleep(2)
                await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
                
                # Добавляем информацию о текущем здоровье
                health_message = f"Ушел на отхил после пвп. Осталось здоровья: {self.my_health}"
                # await self.client.send_message(self.bezvgroup, health_message)  # пересылка без в 
                await self.client.send_message(self.tamplier_id, health_message)  # пересылка Валере
                await self.gokragi()
                self.is_nacheve_active = False
                return True
                

        # Проверка на начало пути
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
            damage_type = None  # Track specific damage type

            # Получаем последние сообщения
            last_messages = await self.client.get_messages(self.bot_id, limit=2)
            print(f"Проанализировано сообщений: {len(last_messages)}")

            for index, message in enumerate(last_messages):
                lstr = message.message.split('\n')

                # Показать содержимое lstr[0] и lstr[-1] для каждого сообщения
                print(f"Сообщение {index + 1}:")
                print(f"    lstr[0]: {lstr[0]}")
                print(f"    lstr[-1]: {lstr[-1]}")

                # Проверка на получение урона
                damage_dict = {
                    "Страж": ["Страж нанес", "Страж Отравил тебя"],
                    "аргол": ["аргол нанес", "аргол Отравил тебя"],
                    "Варасса": ["Варасса нанес", "Варасса Отравил тебя"],
                    "Трашер": ["Трашер нанес", "Трашер Отравил тебя"],
                }

                for boss, phrases in damage_dict.items():
                    if any(phrase in lstr[0] for phrase in phrases):
                        # Определение damage_type в зависимости от босса
                        if boss == "Страж":
                            damage_type = "💦Водяное направление"
                        elif boss == "аргол":
                            damage_type = "💦Водяное направление'"
                        elif boss == "Варасса":
                            damage_type = "💦Водяное направление''"
                        elif boss == "Трашер":
                            damage_type = "💦Водяное направление'''"

                        print(f"Продолжение работы со стражем straj - получен урон от {boss}")
                        is_damaged = True
                        continue

                # Проверка на смерть персонажа
                if "воскреснешь через" in lstr[0]:
                    if "Трашер" in lstr[0]:
                        print("Конец работы со стражем straj - персонаж погиб от Трашера")
                        damage_type = "💦Водяное направление'''"
                    elif "Варасса" in lstr[0]:
                        print("Конец работы со стражем straj - персонаж погиб от Варассы")
                        damage_type = "💦Водяное направление''"
                    elif "аргол" in lstr[0]:
                        print("Конец работы со стражем straj - персонаж погиб от Аргола")
                        damage_type = "💦Водяное направление'"
                    elif "Страж" in lstr[0]:
                        print("Конец работы со стражем straj - персонаж погиб от Стража")
                        damage_type = "💦Водяное направление"

                    is_dead = True
                    break

                if any(phrase in line for line in lstr for phrase in [
                    "Ты дошел до локации.",
                    "Твоя добыча с босса",
                    "Ты направляешься в ген. штаб",
                    ]): 
                    print("конец работы на страже")
                    return

            if is_dead:
                print("Персонаж погиб, ожидаем возрождения")

                # Ожидаем восстановления жизни
                while True:
                    last_message = await self.client.get_messages(self.bot_id, limit=1)
                    if last_message:
                        lstr = last_message[0].message.split('\n')
                        if "Ты снова жив" in lstr[0]:
                            print("Персонаж снова жив")
                            await asyncio.sleep(2)
                            await self.client.send_message(self.bot_id, damage_type)
                            print(f"Отправлено сообщение: {damage_type}")
                            return
                    await asyncio.sleep(1)

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
                            await self.client.send_message(self.bot_id, damage_type)
                            print("Отправлено сообщение: 💦Водяное направление")
                            return
                    await asyncio.sleep(1)

            print("Ни одно из условий не выполнено, повторная проверка через 10 секунд")


    async def wait_for_health_refill(self):
        await asyncio.sleep(3)
        
        # Если появилась капча - ждём её решения
        if self.waiting_for_captcha:
            print("Обнаружена капча при пополнении здоровья...")
            while self.waiting_for_captcha:
                print("Проверка статуса капчи...")
                await asyncio.sleep(20)  # Проверяем каждые 20 секунд
            print("Капча решена, продолжаем...")

        # Ожидание пополнения здоровья после решения капчи
        while True:
            last_message = await self.client.get_messages(self.bot_id, limit=2)
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
        await self._craft_and_process_result()

        return True

    async def _craft_and_process_result(self):
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


                continue
            



    def common_cave(self):
        print("Устанавливаем обработчик сообщений для common_cave")
        
        @self.client.on(events.NewMessage(from_users=[278339710, 715480502, 353501977, 681431333, 562559122, 255360779, 5596818972, 1757434874]))
        async def handle_specific_user_messages(event):
            if event.is_private:  # Проверяем, что сообщение пришло из личного чата
                print(f"Получено новое личное сообщение от пользователя {event.sender_id}: {event.message.text}")
                
                message_text = event.message.text.lower().strip()
                print(f"Преобразованный текст сообщения: {message_text}")
                
                # Проверяем текст сообщения и выполняем соответствующие действия
                if "_банка" in message_text or "_банку" in message_text or "_пить" in message_text:
                    print("Отправляем команду /drink_102")
                    await self.client.send_message(self.bot_id, "/drink_102")
                    await event.message.delete()  # Удаляем сообщение
                elif "_гш" in message_text:  
                    if self.kopka:  
                        print("Отправляем комплект hp_12022")
                        await self.client.send_message(self.bot_id, self.hp_12022)  # Используем переменную hp_12022 для надевания
                        self.my_health = self.my_max_health = 12022  # Устанавливаем текущее и максимальное здоровье на 12022
                        print(f"Здоровье обновлено: {self.my_health}/{self.my_max_health}")
                        await asyncio.sleep(5)
                        print("Отправляем команду /go_to_gsh")
                        await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
                        await self.arrival_hil()  # Вызываем arrival_hil после отправки в ген. штаб
                    else:
                        await self.client.send_message(self.bot_id, self.hp_12022)
                        self.my_health = self.my_max_health = 12022  # Устанавливаем текущее и максимальное здоровье на 12022
                        await asyncio.sleep(2)
                        await self.client.send_message(self.bot_id, "💖 Пополнить здоровье")
                    await event.message.delete()  # Удаляем сообщение
                elif "_пещера" in message_text:  
                    if self.kopka:  
                        print("Отправляем комплект hp_12022")
                        await self.client.send_message(self.bot_id, self.hp_12022)  # Используем переменную hp_12022 для надевания
                        self.my_health = self.my_max_health = 12022  # Устанавливаем текущее и максимальное здоровье на 12022
                        print(f"Здоровье обновлено: {self.my_health}/{self.my_max_health}")
                        await asyncio.sleep(5)
                        print("Отправляем команду /go_to_gsh")
                        await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
                        await self.arrival_hil()  # Вызываем arrival_hil после отправки в ген. штаб
                        await asyncio.sleep(2)
                        await self.client.send_message(self.bot_id, "🚠 Отправиться в пещеры")
                    else:
                        await self.client.send_message(self.bot_id, self.hp_12022)
                        self.my_health = self.my_max_health = 12022  # Устанавливаем текущее и максимальное здоровье на 12022
                        await asyncio.sleep(2)
                        await self.client.send_message(self.bot_id, "💖 Пополнить здоровье")
                        await asyncio.sleep(2)
                        await self.client.send_message(self.bot_id, "🚠 Отправиться в пещеры")

                    await event.message.delete()  # Удаляем сообщение
                elif "_шаг" in message_text:  
                    await asyncio.sleep(1)  
                    await self.rf_message.click(2)
                    await event.message.delete()  # Удаляем сообщение
                elif "_мобы" in message_text:  
                    self.mobs = True  # Устанавливаем флаг для мобов
                    await self.client.send_message(715480502, "Ходим на мобов")  # Сообщение об изменении флага
                    await self.client.send_message(self.bot_id, RF.hp)  # переодеться для мобов
                    await event.message.delete()  # Удаляем сообщение
                elif "_данжи" in message_text:  
                    self.mobs = False  # Устанавливаем флаг для данжей
                    await self.client.send_message(715480502, "Ходим в данжи")  # Сообщение об изменении флага
                    # await self.client.send_message(self.bot_id, RF.chv)
                    await event.message.delete()  # Удаляем сообщение
                elif "_выход" in message_text:  
                    await asyncio.sleep(1)  
                    await self.rf_message.click(3)
                    await event.message.delete()  # Удаляем сообщение
                elif "_рес" in message_text:  
                    if self.is_has_res:  # Проверяем, что is_has_res равно True
                            self.is_has_res = False
                            await asyncio.sleep(randint(14, 20))
                            await self.client.send_message(self.bot_id, self.hp_12022)  # Надеваем бинд на самое большое HP
                            await asyncio.sleep(3)  # Ждем 3 секунды перед кликом
                            await self.rf_message.click(1)
                            print(self.my_health, self.my_max_health)
                            self.my_health = self.my_max_health = 12022  # Устанавливаем значения для my_health и my_max_health
                            self.last_bind = self.hp_12022
                            await event.message.delete()  # Удаляем сообщение
                elif "_состав" in message_text:  
                    await asyncio.sleep(1)  
                    await self.client.send_message(self.bot_id, "⚖️Проверить состав")
                    await event.message.delete()  # Удаляем сообщение
                elif "_моб" in message_text:  
                    await asyncio.sleep(1)  
                    await self.client.send_message(self.bot_id, "🔥 61-65 Лес пламени")
                    await event.message.delete()  # Удаляем сообщение
                elif "_данж" in message_text:
                    if self.is_moving:
                        # Если движение активно, отправляем сообщение пользователю
                        await self.client.send_message(
                            event.sender_id,  # ID пользователя, который отправил команду
                            "Данж будет в течении пары минут"
                        )
                        # Ждем, пока self.kopka станет True
                        while not self.kopka:
                            await asyncio.sleep(5)  # Проверяем каждые 5 секунд
                        # Отправляем команду боту
                        await asyncio.sleep(2)  # Ждем 2 секунды
                        await self.client.send_message(self.bot_id, "🔥 61-65 Лес пламени")

                    else:
                        # Если движение не активно, выполняем команду
                        await asyncio.sleep(1)
                        if self.kopka:  # Проверяем значение self.kopka
                            await self.client.send_message(self.bot_id, "🔥 61-65 Лес пламени")
                            # Отправляем сообщение пользователю
                            await self.client.send_message(
                                event.sender_id,  # ID пользователя, который отправил команду
                                "Данж будет через 1 минуту."
                            )
                        else:
                            await self.client.send_message(self.bot_id, "/go_dange_10014")
                    await event.message.delete()  # Удаляем сообщение
                elif "_хил" in message_text:  
                    if self.last_bind != self.hp_12022 and self.is_has_hil:
                        self.is_has_hil = False
                        await asyncio.sleep(5)  # Ждем 3 секунды
                        await self.client.send_message(self.bot_id, self.hp_12022)  # Надеваем 12022 HP
                        await asyncio.sleep(3)  # Ждем 3 секунды перед кликом
                        await self.rf_message.click(0)  # Выполняем клик
                        print(f"Сменили бинд на: {self.hp_12022} (макс. здоровье: 12022)")
                        self.my_health = self.my_max_health = 12022
                        self.last_bind = self.hp_12022
                        await event.message.delete()  # Удаляем сообщение
                elif "_энка" in message_text:  
                    if self.last_energy_message:  # Проверяем, что last_energy_message не None
                        await self.last_energy_message.forward_to(self.bezvgroup)  # Пересылаем сохраненное сообщение
                    else:
                        await self.client.send_message(self.bezvgroup, "ещё не капнуло")  # Отправляем сообщение в группу
                    await event.message.delete()  # Удаляем сообщение

                elif "_акры+" in message_text or "_акры-" in message_text:
                    # Управляем флагом Aquilla
                    self.go_term_Aquilla = "_акры+" in message_text
                    
                    # Отправляем сообщение об изменении флага
                    if self.go_term_Aquilla:
                        await self.client.send_message(715480502, "Включен флаг Aquilla")
                    else:
                        await self.client.send_message(715480502, "Выключен флаг Aquilla")
                    
                    await event.message.delete()  # Удаляем сообщение

                elif "_белки+" in message_text or "_белки-" in message_text:
                    # Управляем флагом Basilaris
                    self.go_term_Basilaris = "_белки+" in message_text
                    
                    # Отправляем сообщение об изменении флага
                    if self.go_term_Basilaris:
                        await self.client.send_message(715480502, "Включен флаг Basilaris")
                    else:
                        await self.client.send_message(715480502, "Выключен флаг Basilaris")
                    
                    await event.message.delete()  # Удаляем сообщение

                elif "_терм+" in message_text or "_терм-" in message_text:
                    # Управляем обоими флагами (Aquilla и Basilaris)
                    target_value = "_терм+" in message_text
                    self.go_term_Aquilla = target_value
                    self.go_term_Basilaris = target_value
                    
                    # Отправляем сообщение об изменении флагов
                    if target_value:
                        await self.client.send_message(715480502, "Включены оба флага (Aquilla и Basilaris)")
                    else:
                        await self.client.send_message(715480502, "Выключены оба флага (Aquilla и Basilaris)")
                    
                    await event.message.delete()  # Удаляем сообщение

                elif "_heal" in message_text:  # Проверяем наличие команды
                    new_value = int(message_text.split()[-1])
                    self.pvpgoheal = new_value  # Устанавливаем новое значение
                    await self.client.send_message(715480502, f"Хил установлен на: {self.pvpgoheal}")  # Сообщение с новым значением
                    await event.message.delete()  # Удаляем сообщение
                elif "_chv" in message_text:  # Проверяем наличие команды
                    new_value = message_text.split()[-1]  # Получаем последнее слово, это и будет новый value
                    RF.chv = new_value  # Устанавливаем новое значение переменной chv
                    await event.message.delete()  # Удаляем сообщение

                elif "_фаст+" in message_text:
                    self.fast_cave = True
                    await self.client.send_message(715480502, "Включен флаг fast_cave")
                    await event.message.delete()
                elif "_фаст-" in message_text:
                    self.fast_cave = False
                    await self.client.send_message(715480502, "Выключен флаг fast_cave")
                    await event.message.delete()

                elif "появится страж" in message_text:
                    print("Получено сообщение о появлении стража через 15 минут")
                    if self.kopka and not self.waiting_for_captcha:
                        print("self.kopka = True и self.waiting_for_captcha = False, отправляем сообщение '🔥 61-65 Лес пламени'")
                        await self.client.send_message(self.bot_id, "🔥 61-65 Лес пламени")


                elif "страж появился" in message_text:
                    print("Страж появился, отправляем сообщение '🏛 В ген. штаб'")
                    if self.kopka and not self.waiting_for_captcha: # Добавляем проверку kopka и waiting_for_captcha
                        await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
                        await asyncio.sleep(5)  # Проверяем каждые 5 секунд

                        # Ждем, пока персонаж не перестанет двигаться
                        while self.is_moving:
                            print("Персонаж все еще двигается, ждем...")
                            await asyncio.sleep(5)  # Проверяем каждые 5 секунд
                        print("Персонаж перестал двигаться.")
                        await asyncio.sleep(5)  # Проверяем каждые 5 секунд

                        await self.client.send_message(self.bot_id, "💦Водяное направление")



                else:
                    print("Точное совпадение с ключевыми словами не обнаружено")


        print("Обработчик сообщений для common_cave успешно установлен")
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


        should_exit = False
        if alive_count == 1 and total_health < 2400:
            should_exit = True
            reason = "остался 1 живой с менее чем 2400 HP"
        elif alive_count > 1 and total_health < 3500:
            should_exit = True
            reason = f"осталось {alive_count} живых с суммарным здоровьем менее 3500 HP"


        if should_exit and not alive_has_heal and not group_has_res:
            message = f"{'Ты лидер' if self.is_cave_leader else 'Ты не лидер'}, пора на выход. Общее здоровье: {total_health}, нет хилок у живых и ресов в группе"
            await self.client.send_message(715480502, message)
            print(message)
            
            if self.is_cave_leader:
                for member_id in group_members:
                    if member_id != 715480502:
                        await self.client.send_message(member_id, "Выходим из пещеры")
                        print(f"Отправлено сообщение участнику {member_id}: Выходим из пещеры")
                await asyncio.sleep(10) 
                await self.rf_message.click(3)
                
        else:
            print(f"Ещё рано на выход. Общее здоровье: {total_health}, Живых: {alive_count}")


    async def hp_in_caves(self, lstr):
        print(f"Привет, я в пещерах. Текущий бинд: {self.after_bind}")
        # Проверяем, находимся ли мы в пещерах
        if not self.is_in_caves:
            print("Ты не в пещерах, выход из функции.")
            return
        
        # Ищем информацию о персонаже Ros_Hangzhou
        for line in lstr:
            if "Ros_Hangzhou" in line:
                health_info = re.search(r"❤️(\d+)/\d+", line)
                if health_info:
                    current_health = int(health_info.group(1))
                    print(f"Текущее здоровье {self.your_name}: {current_health}")

                # Логика смены сетов в зависимости от текущего здоровья

                if 100 < current_health <= 5139:  # Если здоровье между 100 и 5139
                    if self.after_bind != self.hp_5139:
                        await self.client.send_message(self.bot_id, self.hp_5139)  # Надеваем 5139 HP
                        print(f"Сменили бинд на: {self.hp_5139} (макс. здоровье: 5139)")
                        self.after_bind = self.hp_5139
                elif 5139 < current_health <= 5852:  # Если здоровье между 5139 и 5852
                    if self.after_bind != self.hp_5852:
                        await self.client.send_message(self.bot_id, self.hp_5852)  # Надеваем 5852 HP
                        print(f"Сменили бинд на: {self.hp_5852} (макс. здоровье: 5852)")
                        self.after_bind = self.hp_5852
                elif 5852 < current_health <= 7434:  # Если здоровье между 5852 и 7434
                    if self.after_bind != self.hp_7434:
                        await self.client.send_message(self.bot_id, self.hp_7434)  # Надеваем 7434 HP
                        print(f"Сменили бинд на: {self.hp_7434} (макс. здоровье: 7434)")
                        self.after_bind = self.hp_7434
                elif 7434 < current_health <= 8952:  # Если здоровье между 7434 и 8952
                    if self.after_bind != self.hp_8952:
                        await self.client.send_message(self.bot_id, self.hp_8952)  # Надеваем 8952 HP
                        print(f"Сменили бинд на: {self.hp_8952} (макс. здоровье: 8952)")
                        self.after_bind = self.hp_8952
                elif 8952 < current_health <= 10425:  # Если здоровье между 8952 и 10425
                    if self.after_bind != self.hp_10425:
                        await self.client.send_message(self.bot_id, self.hp_10425)  # Надеваем 10425 HP
                        print(f"Сменили бинд на: {self.hp_10425} (макс. здоровье: 10425)")
                        self.after_bind = self.hp_10425
                elif 10425 < current_health < 12022:  # Если здоровье между 10425 и 12022
                    if self.after_bind != self.hp_12022:
                        await self.client.send_message(self.bot_id, self.hp_12022)  # Надеваем 12022 HP
                        print(f"Сменили бинд на: {self.hp_12022} (макс. здоровье: 12022)")
                        self.after_bind = self.hp_12022
                break


    async def hp_in_caves_kingRagnar(self, lstr):
        print(f"Привет, kingRagnar в пещерах")
        # Проверяем, находимся ли мы в пещерах
        if not self.is_in_caves:
            print("Ты не в пещерах, выход из функции.")
            return

        for line in lstr:
            if "kingRagnar" in line:  # Проверяем, что это сообщение для kingRagnar
                health_info = re.search(r"❤️(\d+)/\d+", line)
                if health_info:
                    current_health = int(health_info.group(1))
                    print(f"Текущее здоровье kingRagnar: {current_health}")

                    # Логика смены сетов для kingRagnar
                    if 10500 <= current_health <= 11500:  # Сет1
                        new_set = "Сет1"
                    elif 9500 <= current_health < 10500:  # Сет2
                        new_set = "Сет2"
                    elif 8000 <= current_health < 9500:  # Сет3
                        new_set = "Сет3"
                    elif 7000 <= current_health < 8000:  # Сет4
                        new_set = "Сет4"
                    elif 5700 <= current_health < 7000:  # Сет5
                        new_set = "Сет5"
                    elif 0 <= current_health < 5700:  # Сет6
                        new_set = "Сет6"
                    else:
                        new_set = None

                    # Отправляем сообщение только если сет изменился
                    if new_set and new_set != self.last_set_kingRagnar:
                        await self.client.send_message(self.players["kingRagnar🤴🏼"], new_set)
                        print(f"Отправлено сообщение: {new_set}")
                        self.last_set_kingRagnar = new_set  # Обновляем last_set

                    print(f"Текущий сет: {self.last_set_kingRagnar}")
                    break

    async def time_cave(self, lstr):  # Добавлен параметр lstr
        # Проверка, является ли текущий пользователь лидером
        self.is_cave_leader = any("/group_guild_join_715480502" in line for line in lstr)
        if not self.is_cave_leader:
            print("Ты не пативод, time_cave не работает.")  # Добавлен вывод, если не пативод
        print(f"{'Ты пативод' if self.is_cave_leader else 'Ты не пативод'}")
        
        if self.cave_task_running:
            print("Задача time_cave уже запущена.")  # Отладочное сообщение
            # await self.client.send_message(715480502, "Задача time_cave уже запущена.")  # Отправка сообщения
            return

        
        self.cave_task_running = True  # Устанавливаем флаг, что задача запущена
        print("Метод time_cave запущен.")
        await self.client.send_message(715480502, "Метод time_cave запущен.")  # Отправка сообщения

        
        # Константы для времени
        CHECK_HOUR = 20
        CHECK_MINUTE = 55

        while True:
            now = datetime.datetime.now()
            print(f"Текущее время: {now}")
            await self.client.send_message(715480502, f"Текущее время на сервере: {now}")  # Отправка сообщения
            next_check = now.replace(hour=CHECK_HOUR, minute=CHECK_MINUTE, second=0, microsecond=0)

            if now >= next_check:
                next_check += datetime.timedelta(days=1)
                print("Устанавливаем время следующей проверки на следующий день.")
                await self.client.send_message(715480502, f"Устанавливаем время следующей проверки на следующий день: {next_check}")  # Отправка сообщения

            wait_time = (next_check - now).total_seconds()
            print(f"Ожидание до следующего {CHECK_HOUR}:{CHECK_MINUTE}: {wait_time} секунд.")
            await self.client.send_message(715480502, f"Ожидание до следующего {CHECK_HOUR}:{CHECK_MINUTE}: {wait_time} секунд.")  # Отправка сообщения
            await asyncio.sleep(wait_time)

            # Условие выхода из цикла (например, по какому-то флагу)
            if not self.is_in_caves or not self.is_cave_leader:  # Если не в пещере или не лидер, выходим из цикла
                await self.client.send_message(715480502, "Вы не были в пещере или не нажали кнопку.")  # Сообщение о том, что не нажали
                await asyncio.sleep(3)
                await self.client.send_message(self.bot_id, "/daily")
                break

            # Если `self.is_moving` активен, ждем, пока он не станет `False`
            while self.is_moving:
                await asyncio.sleep(2)  # Проверяем каждую секунду

            await asyncio.sleep(randint(10, 50))
            await self.rf_message.click(3)
            await asyncio.sleep(5)
            await self.client.send_message(self.bot_id, "/daily")
            await self.client.send_message(715480502, "Вы были в пещере и нажали кнопку.")  # Сообщение о нажатии
            break  # Выход из цикла сразу после нажатия кнопки
        self.cave_task_running = False  # Сбрасываем флаг, когда задача завершена

    async def prepare_for_caves(self):
        print("Начало prepare_for_caves()")
        try:
            # Получаем последнее сообщение с информацией об алтарях
            messages = await self.client.get_messages(-1001284047611, limit=1)
            print(f"Количество полученных сообщений: {len(messages)}")
            if messages:
                print(f"Получено сообщение из чата -1001284047611:")
                print(f"ID сообщения: {messages[0].id}")
                print(f"Дата сообщения: {messages[0].date}")
                print(f"Текст сообщения: {messages[0].text[:200]}...")  # Выводим первые 200 символов
                await self.parce_4v_logs(messages[0].text)
            else:
                print("Не удалось получить сообщение из чата -1001284047611")
        except Exception as e:
            print(f"Произошла ошибка при получении сообщения: {e}")
        
        if self.cmd_altar:
            print(f"Выбран алтарь: {self.cmd_altar}")
        else:
            print("Не удалось получить информацию об алтарях. Будет выбран случайный алтарь при необходимости.")
        print("Конец prepare_for_caves()")

    def choose_random_altar(self):
        return random.choice([
            "🧝‍♀Алтарь Дагаз", 
            "👩‍🚀Алтарь Гебо", 
            "👩‍🚀Алтарь Иса", 
            "🧝‍♀Алтарь Исс", 
            "🤖Алтарь Эйви", 
            "🤖Алтарь Тир"
        ])


    async def handle_no_energy(self):
        print("нет энергии")
        await asyncio.sleep(5)
        await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
        await self.gokragi()

    async def handle_energy_found(self):
        print("есть энергия")
        await asyncio.sleep(5)
        await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
        if self.mobs:  # Проверяем, включен ли флаг для мобов
            await self.check_arrival()  # для мобов
        else:
            await self.gokragi()  # для данжей


    async def handle_energy(self):
        # Проверяем начальные флаги
        if self.waiting_for_captcha or self.is_moving:
            print("Уже ожидаем решения капчи или в движении...")
            return

        # Обработка в пещерах
        if self.is_in_caves:
            if self.is_cave_leader:
                print("Восполнение энергии в пещерах (лидер)")
                await asyncio.sleep(1)
                await self.rf_message.click(2)
            else:
                print("Пересылка сообщения о восполнении энергии в группу")
            return

        # Обработка вне пещер
        if not (self.is_nacheve_active or self.is_training or self.in_castle):
            print("Восполнение энергии вне пещер")
            await asyncio.sleep(1)
            await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
            
            # Ждем 3 секунды и проверяем появление капчи
            await asyncio.sleep(3)
            
            # Если появилась капча - ждём её решения
            if self.waiting_for_captcha:
                print("Обнаружена капча, ожидаем решения...")
                while self.waiting_for_captcha:
                    print("Проверка статуса капчи...")
                    await asyncio.sleep(20)  # Проверяем каждые 20 секунд
                print("Капча решена, продолжаем...")
            
            # После решения капчи или если её не было - проверяем прибытие
            if self.mobs:  # Проверяем, включен ли флаг для мобов
                await self.check_arrival()         # для мобов
            else:
                await self.check_arrival_dange()    # для данжей

