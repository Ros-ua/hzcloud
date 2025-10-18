import re
import sys
import asyncio
import random
from random import randint
from telethon import events
from addons import qHash
import datetime
import threading
import RF_config  # Добавить в начало файла с остальными импортами
import time
#       ^\s*$\n            в поиске
class RF:
    # Берем настройки из конфига
    cave_leader_id = RF_config.cave_leader_id
    hp = RF_config.hp
    chv = RF_config.chv
    your_name = RF_config.your_name
    directions = [
        "💦Водяное направление",
        "💨Воздушное направление", 
        "⛰Земляное направление"
    ]
    def __init__(self, client):
        self.client = client
        # === ВСЕ ЧТО РАВНО TRUE ===
        self.is_cave_leader = self.extra_hil = self.mobs = self.active = self.go_to_heal = True
        # === ВСЕ ЧТО РАВНО FALSE ===
        self.is_run = self.na_straj = self.is_player_dead = self.fast_cave = self.cave_task_running = self.waiting_for_captcha = self.is_moving = self.in_castle = self.v_terminale = self.kopka = self.is_training = self.cave_message_pinned = self.prem = self.go_term_Aquilla = self.go_term_Basilaris = self.go_term_Castitas = self.is_in_caves = self.is_in_gh = self.is_has_hil = self.is_has_res = self.is_nacheve_active = self.in_battle = False
        # === ВСЕ ЧТО РАВНО NONE ===
        self.cave_buttons_message = self.killed_on_chv = self.rf_message = self.last_talisman_info = self.cmd_altar = self.last_bind = self.after_bind = self.last_set_kingRagnar = self.move_timer = self.last_energy_message = self.got_reward = self.terminal_type = self.steps = self.cave_message_id = self.last_step = None
        # === ЧИСЛА ===
        self.bot_id = 577009581
        self.tomat_id = 278339710
        self.kroha_id = 353501977
        self.tamplier_id = 681431333
        self.john_id = 562559122
        self.pchelka_id = 255360779
        self.ded_id = 1757434874
        self.ros_id = 715480502
        self.zatochka = 5
        self.extra_hill_hp = 300
        self.ned_hill_hp = 1500
        self.bezvgroup = -1002220238697
        self.group59 = -1001323974021
        self.location = "🔥 61-65 Лес пламени"  # Локация по умолчанию
        # === КОНФИГ И ВЫЧИСЛЕНИЯ ===
        self.pvp_binds = RF_config.pvp_binds
        self.hp_binds = RF_config.hp_binds
        self.folt_binds = RF_config.folt_binds
        self.my_health = self.my_max_health = self.hp_binds[0][0]
        # === ПУСТЫЕ КОЛЛЕКЦИИ ===
        self.experience_history = []
        # === СЛОВАРИ ===
        self.players = {
            "Нежный 🍅": self.tomat_id,
            "🐾ᏦᎮᎧχᏗ": self.kroha_id,
            "𝕴𝖆𝖒𝖕𝖑𝖎𝖊𝖗": self.tamplier_id,
            "John Doe": self.john_id,
            "๖ۣۜᗯαsͥpwͣoͫℝt🐝": self.pchelka_id,
            "👨‍🦳Пенсионер☠️": self.ded_id,
            "Ros_Hangzhou": self.ros_id
        }
        self.altar_dict = {
            0: "👩‍🚀Алтарь Иса",
            1: "👩‍🚀Алтарь Гебо",
            2: "🧝‍♀Алтарь Исс",
            3: "🧝‍♀Алтарь Дагаз",
            4: "🤖Алтарь Тир",
            5: "🤖Алтарь Эйви"
        }
        # === РЕГУЛЯРНЫЕ ВЫРАЖЕНИЯ ===
        self.health_re = re.compile(r"Здоровье пополнено \D+(\d+)/(\d+)")
        self.battle_re = re.compile(r"^Сражение с .*$")
        self.damage_re = re.compile(r"(\d+)$")
        self.arrival_re = re.compile(r'.*прибудешь через\s*(\d+)\s*мин\.\s*(\d+(?:\.\d+)?)\s*сек\.')
        # === УСЛОВНАЯ НАСТРОЙКА ===
        if self.your_name == "👨‍🦳Пенсионер☠️":
            self.mob_heal = 2000
            self.pvpgoheal = 3500
        elif self.your_name == "๖ۣۜᗯαsͥpwͣoͫℝt🐝":
            self.mob_heal = 4000
            self.pvpgoheal = 4500
        elif self.your_name == "Ros_Hangzhou":
            self.mob_heal = 4000
            self.pvpgoheal = 4500
        else:
            self.mob_heal = 6400
            self.pvpgoheal = 4500
        # === ИНИЦИАЛИЗАЦИЯ КОМПОНЕНТОВ ===
        self.common_cave()
        self.setup_war_listener()
    def isIdCompare(self, id):
        return id == self.bot_id
    async def autoHeal(self):
        print(f"Проверка здоровья перед автолечением: {self.my_health}")
        # Проверяем, что персонаж не мертв
        if self.is_player_dead:
            print("Персонаж мертв. Автолечение невозможно.")
            return
        # Если здоровье равно максимальному, возможно недавнее воскрешение - пропускаем смену сетов
        if self.my_health == self.my_max_health:
            print(f"Здоровье максимальное ({self.my_health}), пропускаем смену сетов (возможно недавнее воскрешение)")
            return
        # Лечимся, если здоровье ниже 300
        if self.my_health <= self.extra_hill_hp and self.is_has_hil and self.extra_hil:
            await self.cave_buttons_message.click(0)
            self.is_has_hil = self.extra_hil = False
            print(f"Здоровье критически низкое ({self.my_health}). Отправляем запрос на хил.")
            print(f"Статус has_hil обновлен: {self.is_has_hil}")
        # Логика смены снаряжения в зависимости от текущего здоровья
        elif self.extra_hill_hp <= self.my_health <= self.ned_hill_hp:
            await asyncio.sleep(15)  # Ждем 15 секунд
            if not self.is_player_dead and self.last_bind != self.hp_binds[0][1] and self.is_has_hil and self.extra_hil:
                self.is_has_hil = False
                await self.client.send_message(self.bot_id, self.hp_binds[0][1])  # Максимальный HP-сет
                await self.wait_for_set_change() #жалоба
                print(f"Сменили бинд на: {self.hp_binds[0][1]} (макс. здоровье: {self.hp_binds[0][0]})")
                await asyncio.sleep(1)
                await self.cave_buttons_message.click(0)  # Выполняем клик
                self.my_health = self.my_max_health = self.hp_binds[0][0]
                self.last_bind = self.hp_binds[0][1]
                print(f"Статус has_hil обновлен: {self.is_has_hil}")
        # Универсальная логика выбора HP-сета на основе кортежа
        elif self.ned_hill_hp < self.my_health < self.hp_binds[0][0]:  # От 1300 до максимального HP
            # Ищем минимальный подходящий HP-сет (как в hp_in_caves для движения)
            selected_cmd = None
            selected_threshold = float('inf')
            for threshold, cmd in self.hp_binds:
                if self.my_health <= threshold and threshold < selected_threshold:
                    selected_cmd = cmd
                    selected_threshold = threshold
            # Меняем сет, если он отличается от текущего
            if selected_cmd and self.last_bind != selected_cmd:
                await self.client.send_message(self.bot_id, selected_cmd)
                print(f"Сменили бинд на: {selected_cmd} (макс. здоровье: {selected_threshold})")
                self.last_bind = selected_cmd
        else:
            print(f"Здоровье достаточно высокое ({self.my_health}). Лечение не требуется.")
    async def change_bind_based_on_health(self):
        if self.my_health <= self.pvpgoheal:
            return  # ниже порога – не трогаем
        # Ищем МИНИМАЛЬНЫЙ подходящий сет (наименьший HP >= текущего HP)
        selected_cmd = None
        selected_threshold = float('inf')  # Начинаем с бесконечности
        for threshold, bind_cmd in self.pvp_binds:
            if self.my_health <= threshold and threshold < selected_threshold:
                selected_cmd = bind_cmd
                selected_threshold = threshold
        # Если не нашли подходящий в pvp_binds, берем максимальный (первый)
        if not selected_cmd:
            max_threshold, max_bind = self.pvp_binds[0]
            selected_cmd = max_bind
            selected_threshold = max_threshold
            print(f"Сменили бинды на: {selected_cmd} (здоровье выше всех порогов)")
        else:
            print(f"Сменили бинды на: {selected_cmd} (здоровье ≤ {selected_threshold})")
        await self.client.send_message(self.bot_id, selected_cmd)
        await self.wait_for_set_change() #работает
        await asyncio.sleep(1)
    async def hp_in_caves(self, lstr):
        print(f"Привет, я в пещерах. Текущий бинд: {self.after_bind}")
        if not self.is_in_caves:
            print("Ты не в пещерах, выход из функции.")
            return
        if self.is_player_dead:
            print("Персонаж мертв. Автолечение невозможно.")
            return
        for line in lstr:
            if self.your_name in line:
                # сначала проверяем смерть, даже если нет строки с сердцем
                if "Мертв" in line:
                    print(f"{self.your_name} мертв. Пропускаем смену сетов.")
                    return
                health_info = re.search(r"❤️(\d+)/\d+", line)
                if not health_info:
                    print(f"Не удалось получить здоровье для {self.your_name}, пропускаем.")
                    return
                current_health = int(health_info.group(1))
                print(f"Текущее здоровье {self.your_name}: {current_health}")
                # выбираем набор биндов в зависимости от режима
                if not self.is_moving:
                    # режим остановки: сначала PVP-сеты, потом HP как резерв
                    selected_cmd = None
                    selected_threshold = float('inf')
                    for threshold, cmd in self.pvp_binds:
                        if current_health <= threshold and threshold < selected_threshold:
                            selected_cmd = cmd
                            selected_threshold = threshold
                    if not selected_cmd:
                        selected_threshold = float('inf')
                        for threshold, cmd in self.hp_binds:
                            if current_health <= threshold and threshold < selected_threshold:
                                selected_cmd = cmd
                                selected_threshold = threshold
                    mode = "PVP-сет" if any(selected_threshold == t for t, _ in self.pvp_binds) else "резерв HP-сет"
                    print(f"Режим остановки: {mode}")
                else:
                    # режим движения: только HP-сеты
                    selected_cmd = None
                    selected_threshold = float('inf')
                    for threshold, cmd in self.hp_binds:
                        if current_health <= threshold and threshold < selected_threshold:
                            selected_cmd = cmd
                            selected_threshold = threshold
                    print("Режим движения: используем минимальный подходящий HP-сет")
                if selected_cmd and self.after_bind != selected_cmd:
                    try:
                        await self.client.send_message(self.bot_id, selected_cmd)
                        print(f"Сменили бинд на {selected_threshold} HP: {selected_cmd}")
                        self.after_bind = selected_cmd
                    except Exception as e:
                        print(f"Ошибка при отправке команды смены сета: {e}")
                elif selected_cmd:
                    print(f"Сет уже надет: {selected_cmd} ({selected_threshold} HP)")
                else:
                    print(f"Не найден подходящий сет для HP: {current_health}")
                break  # вышли после обработки нужного персонажа
    def isCaveLeaderIdCompare(self, id):
        return id == self.cave_leader_id
    def reset_health(self):
        self.my_health = self.my_max_health = self.hp_binds[0][0]
        self.in_battle = False
        self.is_player_dead = False  # Сбрасываем флаг смерти
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
        if self.is_player_dead:
            # self.reset_health()  # Сбрасываем здоровье до максимального только после завершения всех расчетов
            return False  # Выходим из функции сразу, если игрок мертв
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
                self.is_player_dead = True  # Устанавливаем флаг смерти
                return
            if not str_line or "Ты " in str_line or " нанес удар " not in str_line:
                continue
            match = self.damage_re.search(str_line)
            if match:
                self.my_health -= int(match.group(1))
                print(f"Получен урон: {match.group(1)}, текущее здоровье: {self.my_health}")
                # Проверяем, не умер ли игрок после получения урона
                if self.my_health <= 0:
                    self.is_player_dead = True  # Устанавливаем флаг смерти
                    print("Здоровье равно или меньше нуля. Игрок умер.")
    async def set_moving_flag(self, duration):
        self.is_moving = True
        self.killed_on_chv = False
        self.na_straj = False
        self.in_castle = False
        self.is_nacheve_active = False
        self.kopka = False  # Сбрасываем флаг замка при начале движения
        if self.move_timer:
            self.move_timer.cancel()
        self.move_timer = asyncio.create_task(self.reset_moving_flag(duration))
    async def reset_moving_flag(self, duration):
        await asyncio.sleep(duration)
        self.is_moving = False
    # Добавить метод в класс:
    async def _delayed_restart(self):
        # Ожидаем пока self.kopka станет True
        while not self.kopka:
            print("Ожидание завершения копки...")
            await asyncio.sleep(5)
        print("Копка завершена, перезапуск через 1 минуту")
        await asyncio.sleep(60)
        await self.client.disconnect()
        import os, sys
        os.execv(sys.executable, [sys.executable] + sys.argv)
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
            "_булочка"
        ]):    
            print("булочка")
            await self.client.send_message(self.cave_leader_id, "булочка")
        elif any(phrase in line for line in lstr for phrase in [
            "Ты уже находишься в данной локации!"
        ]):
            await asyncio.sleep(1)
            # await self.client.send_message(self.bot_id, "🤖Алтарь Тир")
            await self.client.send_message(self.bot_id, "👩‍🚀Алтарь Иса")
        elif (lstr[-1].endswith("и воскреснешь через 10 минут.") or lstr[-1].startswith("Ты одержал победу над")) and self.in_castle:
            await message.forward_to(self.group59) 
        elif any("Посейдона был активирован автоматическим пожертвованием!" in line for line in lstr) and not self.is_in_caves:
            print("Обнаружено автоматическое пожертвование Посейдона")
            asyncio.create_task(self._delayed_restart())
        elif any(phrase in line for line in lstr for phrase in [
            "ты мертв, дождись пока воскреснешь"
        ]):    
            self.is_has_hil = self.extra_hil = True
            self.after_bind = self.hp_binds[0][1]
        elif any(phrase in line for line in lstr for phrase in [
            "Вы больше не можете лечиться"
        ]):    
            self.is_has_hil = self.extra_hil = False
            self.after_bind = self.hp_binds[0][1]
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
                        await asyncio.sleep(3)  # Ждем ответа от бота
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
                                        if not self.is_player_dead and self.last_bind != self.hp_binds[0][1] and self.is_has_hil and self.extra_hil:
                                            self.is_has_hil = False
                                            await self.client.send_message(self.bot_id, self.hp_binds[0][1])  # Надеваем {self.hp_binds[0][0]}) HP
                                            await self.wait_for_set_change() #жалоба повтор
                                            print(f"Сменили бинд на: {self.hp_binds[0][1]} (макс. здоровье: {self.hp_binds[0][0]}))")
                                            await asyncio.sleep(1)
                                            await self.cave_buttons_message.click(0)  # Выполняем клик для хила
                                            self.my_health = self.my_max_health = self.hp_binds[0][0]
                                            self.last_bind = self.hp_binds[0][1]
                                            print(f"Статус has_hil обновлен: {self.is_has_hil}")
                                        # Ждем 90 секунд и делаем клик, если все еще в пещере
                                        await asyncio.sleep(90)
                                        if self.is_in_caves and self.is_cave_leader and not self.is_moving:
                                            await self.cave_buttons_message.click(2)
                                            print("Выполнен клик (2) после 90 секунд ожидания")
                                        return  # Завершаем выполнение блока после хила
                                else:
                                    print("Не удалось извлечь здоровье из строки")
                            else:
                                print("Не найдена строка с информацией о здоровье")
                        else:
                            print("Не получен ответ от бота на /hero")
                        await self.autoHeal()  # Вызываем autoHeal() для всех остальных случаев
                        # Ждем 90 секунд и делаем клик, если все еще в пещере (для случаев с autoHeal)
                        await asyncio.sleep(90)
                        if self.is_in_caves and self.is_cave_leader and not self.is_moving:
                            await self.cave_buttons_message.click(2)
                            print("Выполнен клик (2) после autoHeal и 90 секунд ожидания")
        if any(phrase in lstr[0] for phrase in [
            "Панель управления", 
            "Ты направляешься в пещеры на фуникулере",
            "Ты направляешься в пещеры на санях",
        ]):
            self.is_in_caves = self.is_has_hil = self.is_has_res = self.extra_hil = True
            self.my_health = self.my_max_health = self.hp_binds[0][0]
            self.after_bind = self.hp_binds[0][1]
            self.steps = 0  # Начинаем отслеживать шаги с 0
            await asyncio.sleep(randint(4, 6))
            await self.client.send_message(self.bot_id, "⚖️Проверить состав")
            print("в пещерах")
        elif any(phrase in lstr[0] for phrase in [
            "Пещеры заснеженных гор. Пещера",
            "Ты прибыл в пещеру №"
        ]):
            if self.steps is not None:
                self.steps += 1  # Увеличиваем счетчик шагов
                print(f"Пройдено шагов: {self.steps}")            
        elif any(phrase in line for line in lstr for phrase in [
            "Здоровье пополнено",
        ]):
            self.is_has_hil = False  
            self.after_bind = self.hp_binds[0][1]
            print(f"Статус has_hil обновлен: {self.is_has_hil}")  # Добавлен вывод статуса has_hil
            self.waiting_for_captcha = False  # Флаг ожидания капчи
        elif any(phrase in line for line in lstr for phrase in [
            "Ты снова жив",
            "Вы больше не можете воскрешаться",
        ]):
            self.after_bind = self.last_bind = self.hp_binds[0][1]
            self.my_health = self.my_max_health = self.hp_binds[0][0]
            self.reset_health()
            self.kopka = False
            print(self.my_health, self.my_max_health)
            # на новый год идти в краги после реса
            if not self.is_in_caves and not self.na_straj and not self.in_castle and not self.waiting_for_captcha and not self.is_nacheve_active:  # Используем существующее условие
                await asyncio.sleep(3)
                await self.client.send_message(self.bot_id, "🌋 Краговые шахты")
        elif any(
            phrase in line for line in lstr for phrase in [
                "Ожидай завершения",
            ]
        ) or any(re.search(rf"одержал победу над .*{self.your_name}", line) for line in lstr):           
            self.my_health = self.my_max_health = self.hp_binds[0][0]
            self.after_bind = self.last_bind = self.hp_binds[0][1]  # Обновляем текущий бинд
            self.is_player_dead = True
            await asyncio.sleep(5)
            if self.is_has_res and self.is_in_caves:  # Проверяем, что is_has_res равно True и мы в пещерах
                self.is_has_res = False
                await asyncio.sleep(5)
                await self.client.send_message(self.bot_id, self.hp_binds[0][1])  # Надеваем бинд на самое большое HP
                await self.wait_for_set_change() #жалоба
                await asyncio.sleep(1)  # Ждем 3 секунды перед кликом
                await self.cave_buttons_message.click(1)
                print(self.my_health, self.my_max_health)
        elif "Сражение с" in lstr[0] and not any("Рюкзак" in line for line in lstr):
            self.in_battle = True   
        elif any("К сожалению ты умер" in line for line in lstr):
            self.in_battle = False     
        elif "Ваша группа замерзнет через 5 минут" in lstr[0]:
            await asyncio.sleep(1)
            await self.cave_buttons_message.click(2)
        elif "Ваша группа восстановила силы" in lstr[0]:
            if self.fast_cave:  # Проверка значения fast_ceve
                await asyncio.sleep(1)
                await self.cave_buttons_message.click(2)
        elif lstr[0].endswith("✅"): 
            await asyncio.sleep(1)
            await self.client.send_message(self.group59, "Капча пройдена")  # Отправляем сообщение
        # ── новое условие для пересылки «Ты направляешься в замок» ──
        elif lstr[0].startswith("Ты направляешься в замок"):
            await message.forward_to(self.group59)   # пересылаем в группу 59
            print("Переслано сообщение о направлении в замок")
        elif "Ваша группа прибудет в ген. штаб через" in lstr[0]:
            print("чувачок, ты закончил пещеру")
            await asyncio.sleep(5)
            self.fast_cave = False
            self.is_in_caves = False
            # Извлечение значения duration из сообщения
            match = re.search(r"через\s*(\d+)\s*мин", lstr[0])
            if match:
                duration = int(match.group(1)) * 60  # Преобразуем минуты в секунды
                await self.set_moving_flag(duration)  # Устанавливаем флаг движения
            await self.client.send_message(self.bot_id, RF.hp)  # переодеться для мобов
            await self.check_arrival()
            self.steps = None  # Сбрасываем счетчик шагов
            self.cave_message_id = None  # Сбрасываем ID сообщения
            self.cave_message_pinned = False  # Сбрасываем флаг закрепления
            self.experience_history = []  # Добавлено: сброс истории опыта
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
            # await self.hp_in_caves_kingRagnar(lstr)
            # await asyncio.sleep(2)
            await self.time_cave(lstr)
            # await self.cave_profit(lstr)
        elif lstr[0].endswith("не в ген. штабе]"):
            # Проверяем, есть ли 🐾ᏦᎮᎧχᏗ в сообщении
            if "🐾ᏦᎮᎧχᏗ" in lstr[0]:
                await message.forward_to(self.bezvgroup)  # специальная группа для 🐾ᏦᎮᎧχᏗ без в 
            else:
                await message.forward_to(self.group59)  # стандартная группа для остальных 59
            # Ищем всех игроков, упомянутых в сообщении
            players_not_in_gh = re.findall(r'(Нежный 🍅|🐾ᏦᎮᎧχᏗ|𝕴𝖆𝖒𝖕𝖑𝖎𝖊𝖗|John Doe|๖ۣۜᗯαsͥpwͣoͫℝt🐝|👨‍🦳Пенсионер☠️)', lstr[0])
            if players_not_in_gh:
                for player in players_not_in_gh:
                    if player in self.players:
                        print(f"{player} не в ген. штабе")
                        await self.client.send_message(self.players[player], "Давайте в ген. штаб")
            if self.mobs:  # Проверяем, включен ли флаг для мобов
                await self.client.send_message(self.bot_id, self.location)  # для мобов
            else:
                print("bag bag bag")  # для данжей
        elif "Если ты хочешь вернуть группу" in lstr[0]:
            await asyncio.sleep(2)
            await self.client.send_message(self.bot_id, "22")
        # если сообщение начинается на "🏅Топ по уровню"
        elif lstr[0].startswith("🏅Топ по уровню"):
            gerain_score = None
            avada_score = None
            ros_score = None
            for line in lstr:
                if "GERAIN" in line:
                    match = re.search(r"\d+\((\d+)\)ур", line)
                    if match:
                        gerain_score = int(match.group(1))
                elif "AvadaKedavra" in line:
                    match = re.search(r"\d+\((\d+)\)ур", line)
                    if match:
                        avada_score = int(match.group(1))
                elif self.your_name in line:
                    match = re.search(r"\d+\((\d+)\)ур", line)
                    if match:
                        ros_score = int(match.group(1))
            if gerain_score is not None and avada_score is not None and ros_score is not None:
                # Разница GERAIN - player name
                diff_gerain_ros = gerain_score - ros_score
                # Разница AvadaKedavra - player name
                diff_avada_ros = avada_score - ros_score
                msg = (
                    f"Разница с GERAIN : {diff_gerain_ros}\n"
                    f"Разница с AvadaKedavra : {diff_avada_ros}"
                )
                await self.client.send_message(self.cave_leader_id, msg)
        # на страже
        elif "Бой с боссом будет происходить в автоматическом режиме." in lstr[0]:
            print("дошел до стража")
            self.na_straj = True
            await self.straj()
        elif "Босс еще не появился. Проход в локацию закрыт!" in lstr[0]:  # если умер на страже и снова хочешь идти на стража
            await asyncio.sleep(1)
            await self.client.send_message(self.bot_id, self.location)
        # на чв
        elif "Ты был убит!" in lstr[0]:  # Добавлено условие для проверки фразы
            # Проверяем, если в ожидании капчи
            if self.waiting_for_captcha:
                print("Ожидание CAPTCHA, действия не выполняются.")
                return  # Прерываем выполнение, если ожидаем CAPTCHA
            print("Персонаж был убит!")
            # await self.client.send_message(self.bot_id, RF.chv)
            await self.check_arrival()
        elif any(phrase in line for line in lstr for phrase in [
            "Алтарь Хагал",
        ]):
            self.got_reward = False  # Сбрасываем флаг получения награды
            await asyncio.sleep(5)
            await self.client.send_message(self.bot_id, "🧝‍♀ Терминал Castitas")  # Отправляем сообщение в терминал
            self.terminal_type = "🧝‍♀ Терминал Castitas"  # Определяем тип терминала
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
            # await self.client.send_message(self.tamplier_id, message)
            # Отправляем в группу 59 только если терминал Aquilla или Castitas
            # if self.terminal_type in ["🤖 Терминал Aquilla", "🧝‍♀ Терминал Castitas"]:
            #     await self.client.send_message(self.group59, message)
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
            await asyncio.sleep(1)
            if self.terminal_type == "🧝‍♀ Терминал Castitas":
                await self.nacheve()
            elif self.terminal_type in ["🤖 Терминал Aquilla", "👩‍🚀 Терминал Basilaris"]:
                await self.vterminale()
            # if self.your_name == "👨‍🦳Пенсионер☠️":
            #     await asyncio.sleep(1)
            #     # await self.nacheve()
            #     await self.vterminale()
            # elif self.your_name == "Ros_Hangzhou":
            #     await asyncio.sleep(1)
            #     # await self.nacheve()
            #     await self.vterminale()
            # elif self.your_name == "𝕴𝖆𝖒𝖕𝖑𝖎𝖊𝖗":
            #     await asyncio.sleep(1)
            #     # await self.nacheve()
            #     await self.vterminale()
            # elif self.your_name == "๖ۣۜᗯαsͥpwͣoͫℝt🐝":
            #     await asyncio.sleep(1)
            #     # await self.nacheve()
            #     await self.vterminale()
        elif any(phrase in line for line in lstr for phrase in [
            "Адена уже на твоем счете.",
        ]):
            print("Получена Адена")
            if self.your_name in [
                # "👨‍🦳Пенсионер☠️",
                "Ros_Hangzhou",
                # "𝕴𝖆𝖒𝖕𝖑𝖎𝖊𝖗",
                "๖ۣۜᗯαsͥpwͣoͫℝt🐝",
            ]:
                self.location = "🏔 Этер"
                print(f"Локация изменена на: {self.location}")
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
            # await self.client.send_message(self.tamplier_id, altar_to_send) # пересылка алтаря Валере
            # await self.client.send_message(self.bezvgroup, altar_to_send) # пересылка алтаря без в 
        elif "Ты прибыл в ⛏рудник." in lstr[0]:
            self.kopka = True
            await asyncio.sleep(1)
            await self.client.send_message(self.bot_id, "🖲 Установить АБУ")
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
            await asyncio.sleep(1)
            await self.client.send_message(self.bot_id, RF.hp)
            await self.wait_for_set_change()
            await asyncio.sleep(1)
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
                    # Проверяем, меньше ли здоровье self.mob_heal
                    if current_health < self.mob_heal:
                        # Переодеваем в сет для мобов перед energy_found
                        await asyncio.sleep(2)
                        await self.client.send_message(self.bot_id, RF.hp)
                        await self.wait_for_set_change()
                        await asyncio.sleep(2)                        
                        await self.handle_energy_found()
                    else:
                        print(f"Здоровье больше или равно {self.mob_heal}, отправляем сообщение 🐺По уровню.")
                        # Выбираем минимальный подходящий HP-сет (чуть больше чем текущее здоровье)
                        selected_cmd = None
                        selected_threshold = float('inf')
                        for threshold, cmd in self.hp_binds:
                            if current_health <= threshold and threshold < selected_threshold:
                                selected_cmd = cmd
                                selected_threshold = threshold
                        if selected_cmd:
                            await asyncio.sleep(2)
                            await self.client.send_message(self.bot_id, selected_cmd)
                            await self.wait_for_set_change()
                            await asyncio.sleep(2)
                        await asyncio.sleep(2)
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
            # "У тебя нет" # использовать на хелоуин
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
            await self.client.send_message(self.group59, "Капча получена")  # Отправляем сообщение
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
            # Добавляем проверку нахождения в пещерах и отправку проверки состава
            if self.is_in_caves:
                await asyncio.sleep(5)  # Ждем 5 секунд
                await self.client.send_message(self.bot_id, "⚖️Проверить состав")
                print("Отправлено сообщение: ⚖️Проверить состав (из-за движения в пещере)")
        elif "Ты прибыл в замок" in lstr[0]:
            self.in_castle = True
            print("Прибыли в замок")
        elif "Ты успешно установил" in lstr[0]:
            self.prem = True
            print("поставил абу")
        elif "У тебя нет АБУ" in lstr[0]:
            self.prem = False
            print("нет абу")
        elif "Ты закончил тренировку" in lstr[0]:
            self.is_training = False
            await asyncio.sleep(1)
            await self.client.send_message(self.bot_id, self.location)
        elif "Ты начал тренировку" in lstr[0]:
            self.is_training = True
        # elif "Как долго ты хочешь тренировать питомца" in lstr[0]:
        #     await asyncio.sleep(1)
        #     await self.client.send_message(self.bot_id, "1")
        elif "Начать тренировку?" in lstr[-1]:
            await message.click(0)
        elif any(phrase in line for line in lstr for phrase in [
            "Доп. к характеристикам персонажа",
        ]):
            await message.forward_to(1033007754)
        if not getattr(message, "buttons", None):
            if val == 3190963077:  # ✨Добыча:
                await message.forward_to(self.group59)  # группа 59
                # await message.forward_to(self.bezvgroup)  # группа без В
            else:
                await self.checkHealth(lstr)
            return
        if val == 3190963077:  # ✨Добыча:
            self.rf_message = message
            self.cave_buttons_message = message  # ← сохраняем кнопки отдельно
            await asyncio.sleep(2)
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
                await self.client.send_message(self.bot_id, self.location)
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
        # Если в ожидании капчи, то сразу выходим
        if self.waiting_for_captcha:
            return
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
                    if not self.waiting_for_captcha:
                        await self.client.send_message(self.bot_id, "💖 Пополнить здоровье")
                        await self.wait_for_health_refill()
                        await self.client.send_message(self.bot_id, self.location)
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
        # Проверка HP терминалов Basilaris и Aquilla
        for line in lstr:
            if "Basilaris терминал:" in line:
                hp_info = line.split('❤')[1].split('/')[0].strip()
                basilaris_hp = int(hp_info)
                print(f"Basilaris HP: {basilaris_hp}")
                if basilaris_hp < 12000 and basilaris_hp > 1:
                    self.go_to_heal = False
                    self.go_term_Basilaris = False
                    self.go_term_Aquilla = False
                    self.go_term_Castitas = False
                    print("HP Basilaris меньше 12000, прекращаем ходить.")
            if "Aquilla терминал:" in line:
                hp_info = line.split('❤')[1].split('/')[0].strip()
                aquilla_hp = int(hp_info)
                print(f"Aquilla HP: {aquilla_hp}")
                if aquilla_hp < 12000 and aquilla_hp > 1:
                    self.go_to_heal = False
                    self.go_term_Aquilla = False
                    self.go_term_Basilaris = False
                    self.go_term_Castitas = False
                    print("HP Aquilla меньше 12000, прекращаем ходить.")
            if len(lstr) > 24:
                if self.go_term_Castitas and not lstr[10].endswith(" 0"):
                    self.cmd_altar = "🧝‍♀Алтарь Хагал"
                    print(f"Значение в 10-й строке не заканчивается на '0', выбран алтарь: {self.cmd_altar}")
                else:
                    # Обычная логика выбора алтаря с учётом флага self.active
                    l_altars = []
                    if self.active:
                        if not lstr[5].endswith("Castitas"): l_altars.append(0)
                        if not lstr[6].endswith("Castitas"): l_altars.append(1)
                        if not lstr[14].endswith("Castitas"): l_altars.append(2)
                        if not lstr[15].endswith("Castitas"): l_altars.append(3)
                        if not lstr[23].endswith("Castitas"): l_altars.append(4)
                        if not lstr[24].endswith("Castitas"): l_altars.append(5)
                    else:
                        if not lstr[5].endswith("Castitas"): l_altars.append(0)
                        if not lstr[6].endswith("Castitas"): l_altars.append(1)
                        if not lstr[14].endswith("Castitas"): l_altars.append(2)
                        if not lstr[15].endswith("Castitas"): l_altars.append(3)
                        if not lstr[23].endswith("Castitas"): l_altars.append(4)
                        if not lstr[24].endswith("Castitas"): l_altars.append(5)         
                    if l_altars:
                        self.cmd_altar = self.altar_dict.get(random.choice(l_altars))
                        print(f"Найденные алтари: {l_altars}, выбран случайный алтарь: {self.cmd_altar}")
                    else:
                        if not self.v_terminale:
                            self.cmd_altar = self.choose_random_altar()
                            print(f"Алтари не найдены, выбран случайный алтарь: {self.cmd_altar}")
                        else:
                            self.cmd_altar = None
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
                    # await self.client.send_message(self.tamplier_id, self.cmd_altar) # пересылка алтаря Валере
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
        Теперь мы ждем завершения всех побед в серии, а потом отправляем /hero.
        """
        # Настройки ожидания
        wait_interval = 5  # сколько секунд ждем между проверками
        max_total_wait = 60  # максимальное общее время ожидания
        total_waited = 0
        print(f"Начинаем ожидание завершения серии побед...")
        # Запоминаем ID последнего сообщения, чтобы искать только новые
        messages_before = await self.client.get_messages(self.bot_id, limit=1)
        last_checked_message_id = messages_before[0].id if messages_before else 0
        # Цикл ожидания с проверкой новых побед
        while total_waited < max_total_wait:
            await asyncio.sleep(wait_interval)
            total_waited += wait_interval
            # Проверяем есть ли новые сообщения
            new_messages = await self.client.get_messages(self.bot_id, limit=10)
            new_victory_found = False
            # Ищем новые сообщения о победе
            for message in new_messages:
                if message.id > last_checked_message_id:
                    message_text = message.text or message.message
                    if message_text and "Ты одержал победу над" in message_text:
                        print(f"Обнаружена дополнительная победа! Сбрасываем таймер (прошло {total_waited}s)")
                        new_victory_found = True
                        last_checked_message_id = message.id
                        total_waited = 0  # ВАЖНО: сбрасываем счетчик времени
                        break
            # Если новых побед не было - выходим из цикла
            if not new_victory_found:
                print(f"За {wait_interval}s новых побед не было. Отправляем /hero")
                break
        if total_waited >= max_total_wait:
            print(f"Достигнуто максимальное время ожидания {max_total_wait}s. Отправляем /hero")
        # Теперь отправляем /hero и получаем информацию о здоровье
        # Получаем последнее сообщение перед отправкой команды для сравнения
        messages_before = await self.client.get_messages(self.bot_id, limit=1)
        last_message_id_before = messages_before[0].id if messages_before else 0
        await self.client.send_message(self.bot_id, "/hero")
        print("Отправлена команда /hero, ожидаем ответ от бота...")
        # Ждем новое сообщение от бота максимум 60 секунд
        max_wait_time = 60  # максимальное время ожидания
        check_interval = 2   # интервал проверки
        waited_time = 0
        while waited_time < max_wait_time:
            await asyncio.sleep(check_interval)
            waited_time += check_interval
            # Получаем последнее сообщение
            response = await self.client.get_messages(self.bot_id, limit=1)
            if response and response[0].id > last_message_id_before:
                # Получили новое сообщение, проверяем содержит ли оно информацию о здоровье
                message_text = response[0].text or response[0].message
                if '❤Здоровье:' in message_text:
                    # Ищем строку с информацией о здоровье
                    health_line = next((line for line in message_text.split('\n') if '❤Здоровье:' in line), None)
                    # Извлекаем текущее здоровье
                    match = re.search(r'❤Здоровье:\s*(\d+)', health_line)
                    self.my_health = int(match.group(1))
                    print(f"Текущее здоровье обновлено: {self.my_health} (ожидали {waited_time}s)")
                    return
                else:
                    print(f"Получено сообщение без информации о здоровье, продолжаем ждать... ({waited_time}s)")
            else:
                print(f"Ждем ответ от бота... ({waited_time}s)")
        print(f"Бот не ответил за {max_wait_time} секунд, возможно лаги или проблемы с ботом.")
        # Можно добавить дополнительную логику или повторную попытку
    async def process_bot_message(self, lstr):
        # Проверка сообщения о смерти или времени восстановления
        if lstr[-1].endswith("минут.") or "дождись пока воскреснешь" in lstr[0] or "был убит ядерной ракетой" in lstr[0]:
            print("Обнаружено сообщение о времени. Вызываем gokragi()")
            self.killed_on_chv = True
            await asyncio.sleep(2)
            await self.client.send_message(self.bot_id, RF.chv)
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
                # await self.client.send_message(self.tamplier_id, fight_message)  # пересылка Валере
                await asyncio.sleep(1)
                # Динамическая смена оборудования
                await self.change_bind_based_on_health()
                await asyncio.sleep(3)
                return False  # Переход к следующему терминалу
            else:
                if self.go_to_heal:
                    print("Здоровье меньше или равно self.pvpgoheal. Отправляемся в ген. штаб для хила.")
                    await asyncio.sleep(2)
                    await self.client.send_message(self.bot_id, RF.chv)
                    await self.wait_for_set_change() #не проверено
                    await asyncio.sleep(1)
                    await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
                    # Добавляем информацию о текущем здоровье
                    health_message = f"Ушел на отхил после пвп. Осталось здоровья: {self.my_health}"
                    # await self.client.send_message(self.bezvgroup, health_message)  # пересылка без в 
                    # await self.client.send_message(self.tamplier_id, health_message)  # пересылка Валере
                    await self.gokragi()
                    self.is_nacheve_active = False
                    return True
                else:
                    await self.client.send_message(self.bot_id, RF.chv)
                    await self.wait_for_set_change() # не проверено
                    await asyncio.sleep(1)
                    # Проверяем имя пользователя для команды drink_103
                    if self.your_name in ["Ros_Hangzhou", "๖ۣۜᗯαsͥpwͣoͫℝt🐝"]:
                        await self.client.send_message(self.bot_id, "/drink_103")
                        await asyncio.sleep(3)
                    else:
                        # Если имя не подходит, можно использовать альтернативную команду или просто пропустить
                        print(f"Пользователь {self.your_name} не имеет доступа к команде /drink_103")
                        # Или можно добавить альтернативную логику здесь
                    return False               
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
                            damage_type = random.choice(RF.directions)
                        elif boss == "аргол":
                            damage_type = random.choice(RF.directions) + "'"
                        elif boss == "Варасса":
                            damage_type = random.choice(RF.directions) + "''"
                        elif boss == "Трашер":
                            damage_type = random.choice(RF.directions) + "'''"
                        print(f"Продолжение работы со стражем straj - получен урон от {boss}")
                        is_damaged = True
                        continue
                # Проверка на смерть персонажа
                if "воскреснешь через" in lstr[0]:
                    if "Трашер" in lstr[0]:
                        print("Конец работы со стражем straj - персонаж погиб от Трашера")
                        damage_type = random.choice(RF.directions) + "'''"
                    elif "Варасса" in lstr[0]:
                        print("Конец работы со стражем straj - персонаж погиб от Варассы")
                        damage_type = random.choice(RF.directions) + "''"
                    elif "аргол" in lstr[0]:
                        print("Конец работы со стражем straj - персонаж погиб от Аргола")
                        damage_type = random.choice(RF.directions) + "'"
                    elif "Страж" in lstr[0]:
                        print("Конец работы со стражем straj - персонаж погиб от Стража")
                        damage_type = random.choice(RF.directions)
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
                            print(f"Отправлено сообщение: {damage_type}")
                            return
                    await asyncio.sleep(1)
            print("Ни одно из условий не выполнено, повторная проверка через 10 секунд")
    async def wait_for_health_refill(self):
        await asyncio.sleep(2)
        # Если появилась капча - ждём её решения
        if self.waiting_for_captcha:
            print("Обнаружена капча при пополнении здоровья...")
            while self.waiting_for_captcha:
                print("Проверка статуса капчи...")
                await asyncio.sleep(20)  # Проверяем каждые 20 секунд
            print("Капча решена, продолжаем...")
            # await self.client.send_message(self.group59, "Капча пройдена")  # Отправляем сообщение
        # Ожидание пополнения здоровья после решения капчи
        while True:
            last_message = await self.client.get_messages(self.bot_id, limit=2)
            if last_message:
                lstr = last_message[0].message.split('\n')
                if any("Здоровье пополнено" in line for line in lstr):
                    await asyncio.sleep(0.1)
                    return
            await asyncio.sleep(1)
    async def wait_for_set_change(self):
        # Ожидание смены сета
        while True:
            last_message = await self.client.get_messages(self.bot_id, limit=2)
            if last_message:
                lstr = last_message[0].message.split('\n')
                if any("Ты успешно надел комлект!" in line for line in lstr):
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
            print(" Илье оно нафиг не надо")
            # Проверяем наличие составляющих
            # if any("Составляющие:" in line for line in lstr):
            #     await self.check_talisman(lstr)
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
                    if talisman_level < self.zatochka:  # уровень заточки
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
        if not lstr or not lstr[0].endswith(f"/group_guild_join_{self.cave_leader_id}"):
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
            if nick == self.your_name:
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
    def setup_war_listener(self):
        print("Устанавливаем обработчик сообщений для setup_war_listener")
        @self.client.on(events.NewMessage(chats=-1001284047611))
        async def on_war_start(event):
            if self.waiting_for_captcha:
                return  # Выходим из функции, ничего не обрабатываем
            lines = event.message.text.splitlines()
            if any("Война в краговых шахтах началась!" in ln for ln in lines):
                print("Обнаружено начало войны в крагах!")
                # self.pvpgoheal = 4500
                self.active = False
                self.go_to_heal = True
                # Логика для различных типов пользователей
                if self.your_name == "𝕴𝖆𝖒𝖕𝖑𝖎𝖊𝖗":
                    self.go_term_Basilaris = True
                    self.go_term_Castitas = False
                    self.go_term_Aquilla = False
                elif self.your_name == "Ros_Hangzhou":
                    self.go_term_Basilaris = True
                    self.go_term_Castitas = True
                    self.go_term_Aquilla = False
                elif self.your_name == "👨‍🦳Пенсионер☠️":
                    self.go_term_Basilaris = True
                    self.go_term_Castitas = True
                    self.go_term_Aquilla = False        
                elif self.your_name == "๖ۣۜᗯαsͥpwͣoͫℝt🐝":
                    self.go_term_Basilaris = True
                    self.go_term_Castitas = False
                    self.go_term_Aquilla = False
                #  Запускаем таймер для изменения pvpgoheal через 38 минут
                asyncio.create_task(self.pvp_heal_timer())                
                if not any([self.is_in_caves, self.kopka, self.is_moving]):
                    await asyncio.sleep(12)
                    await self.client.send_message(self.bot_id, RF.chv)
                    await self.wait_for_set_change() #работает
                    await asyncio.sleep(1)
                    await self.client.send_message(self.bot_id, "💖 Пополнить здоровье")
                    print("Отправлено сообщение: 💖 Пополнить здоровье")
                    await self.wait_for_health_refill()
                    await self.client.send_message(self.bot_id, "🌋 Краговые шахты")
            if any("Война окончена!" in ln for ln in lines):
                await asyncio.sleep(70)
                if not self.is_moving and not self.killed_on_chv:
                    await self.client.send_message(self.bot_id, "⛏Рудник")
                await asyncio.sleep(900)  # 15 минут = 900 секунд
                if not self.is_in_caves and not self.waiting_for_captcha:
                    await self.client.send_message(self.bot_id, RF.hp)  # Переодеться для мобов
                # # await self.wait_for_set_change() #работает
                # await asyncio.sleep(1)
                # if self.is_nacheve_active and not self.is_moving:
                #     await asyncio.sleep(3)  # Задержка перед следующим действием
                #     await self.client.send_message(self.bot_id, "⛏Рудник")
                # else:
                #     await asyncio.sleep(3)
                #     await self.client.send_message(self.bot_id, "⛏Рудник")
            if any(("Castitas одолела" in ln or "Castitas не смогла одолеть" in ln or "Босс" in ln and "пал!" in ln) for ln in lines):
                if not self.is_in_caves:
                    await asyncio.sleep(15)
                    await self.client.send_message(self.bot_id, RF.hp)
                    await self.wait_for_set_change() #работает
                    await asyncio.sleep(1)
                    if not self.is_moving and not self.in_castle:
                        await asyncio.sleep(5)
                        await self.client.send_message(self.bot_id, self.location)
            if any("Осада замков закончилась" in ln for ln in lines):
                self.in_castle = False
                if not self.is_in_caves and not self.waiting_for_captcha and not self.kopka and not self.is_moving:
                    await asyncio.sleep(5)
                    await self.client.send_message(self.bot_id, RF.hp)
                    await self.wait_for_set_change() 
                    await asyncio.sleep(2)
                    await self.client.send_message(self.bot_id, self.location)
            if any("Страж будет уязвим для атак расы" in ln and "Castitas" in ln for ln in lines):
                print("Получено сообщение о появлении стража через 15 минут")
                if not self.is_in_caves and not self.is_moving and not self.in_castle:
                    print("Отправляем сообщение '🔥 61-65 Лес пламени'")
                    await self.client.send_message(self.bot_id, self.location)
            if any("Он уязвим только для атак расы" in ln and "Castitas" in ln for ln in lines):
                print("Страж появился")
                if not self.is_in_caves and not self.in_castle:
                    # Выбираем случайное направление
                    chosen_direction = random.choice(RF.directions)
                    print(f"Выбрано направление: {chosen_direction}")
                    if self.kopka:
                        print("Копка активна, отправляем сообщение '🏛 В ген. штаб'")
                        await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
                        await asyncio.sleep(5)
                        await self.client.send_message(self.bot_id, RF.chv)
                        await self.wait_for_set_change() #работает
                        await asyncio.sleep(1)
                        while self.is_moving:
                            print("Персонаж все еще двигается, ждем...")
                            await asyncio.sleep(5)
                        print("Персонаж перестал двигаться.")
                        await asyncio.sleep(5)
                        await self.client.send_message(self.bot_id, chosen_direction)
                    else:
                        await self.client.send_message(self.bot_id, RF.chv)
                        await self.wait_for_set_change() #работает
                        await asyncio.sleep(1)  
                        print(f"Копка не активна, сразу отправляем '{chosen_direction}'")
                        await self.client.send_message(self.bot_id, chosen_direction)
            elif any("Стальной аргол для расы" in ln and "Castitas" in ln for ln in lines):
                print("Аргол появился")
                if not self.is_in_caves and not self.in_castle:
                    # Выбираем случайное направление
                    chosen_direction = random.choice(RF.directions)
                    print(f"Выбрано направление: {chosen_direction}")
                    if self.kopka:
                        print("Копка активна, отправляем сообщение '🏛 В ген. штаб'")
                        await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
                        await asyncio.sleep(5)
                        await self.client.send_message(self.bot_id, RF.chv)
                        await self.wait_for_set_change()
                        await asyncio.sleep(1)
                        while self.is_moving:
                            print("Персонаж все еще двигается, ждем...")
                            await asyncio.sleep(5)
                        print("Персонаж перестал двигаться.")
                        await asyncio.sleep(5)
                        await self.client.send_message(self.bot_id, chosen_direction + "'")
                    else:
                        await self.client.send_message(self.bot_id, RF.chv)
                        await self.wait_for_set_change()
                        await asyncio.sleep(1)  
                        print(f"Копка не активна, сразу отправляем '{chosen_direction}'")
                        await self.client.send_message(self.bot_id, chosen_direction + "'")
            elif any("Варасса для расы" in ln and "Castitas" in ln for ln in lines):
                print("Варасса появилась")
                if not self.is_in_caves and not self.in_castle:
                    # Выбираем случайное направление
                    chosen_direction = random.choice(RF.directions)
                    print(f"Выбрано направление: {chosen_direction}")
                    if self.kopka:
                        print("Копка активна, отправляем сообщение '🏛 В ген. штаб'")
                        await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
                        await asyncio.sleep(5)
                        await self.client.send_message(self.bot_id, RF.chv)
                        await self.wait_for_set_change()
                        await asyncio.sleep(1)
                        while self.is_moving:
                            print("Персонаж все еще двигается, ждем...")
                            await asyncio.sleep(5)
                        print("Персонаж перестал двигаться.")
                        await asyncio.sleep(5)
                        await self.client.send_message(self.bot_id, chosen_direction + "''")
                    else:
                        await self.client.send_message(self.bot_id, RF.chv)
                        await self.wait_for_set_change()
                        await asyncio.sleep(1)  
                        print(f"Копка не активна, сразу отправляем '{chosen_direction}''")
                        await self.client.send_message(self.bot_id, chosen_direction + "''")
            elif any("Трашер для расы" in ln and "Castitas" in ln for ln in lines):
                print("Трашер появился")
                if not self.is_in_caves and not self.in_castle:
                    # Выбираем случайное направление
                    chosen_direction = random.choice(RF.directions)
                    print(f"Выбрано направление: {chosen_direction}")
                    if self.kopka:
                        print("Копка активна, отправляем сообщение '🏛 В ген. штаб'")
                        await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
                        await asyncio.sleep(5)
                        await self.client.send_message(self.bot_id, RF.chv)
                        await self.wait_for_set_change()
                        await asyncio.sleep(1)
                        while self.is_moving:
                            print("Персонаж все еще двигается, ждем...")
                            await asyncio.sleep(5)
                        print("Персонаж перестал двигаться.")
                        await asyncio.sleep(5)
                        await self.client.send_message(self.bot_id, chosen_direction + "'''")
                    else:
                        await self.client.send_message(self.bot_id, RF.chv)
                        await self.wait_for_set_change()
                        await asyncio.sleep(1)  
                        print(f"Копка не активна, сразу отправляем '{chosen_direction}'''")
                        await self.client.send_message(self.bot_id, chosen_direction + "'''")
            # Обработка предупреждения о войне через час
            if any("Война в краговых шахтах начнется через час!" in ln for ln in lines):
                print("Обнаружено предупреждение о войне через час!")
                # Запускаем таймер на 57 минут
                asyncio.create_task(self.war_preparation_timer())
    async def pvp_heal_timer(self):
        """Таймер для изменения pvpgoheal через 43 минуты после начала войны"""
        print("Запущен таймер pvpgoheal на 43 минуты")
        await asyncio.sleep(41 * 60)  # 41 минута в секундах 
        self.go_to_heal = False
        self.go_term_Aquilla = False
        self.go_term_Basilaris = False   
        self.go_term_Castitas = False
        await asyncio.sleep(2 * 60)  # 2 минуты в секундах (итого 43 минуты)
        self.go_to_heal = True
        print("Через 43 минуты после начала войны установлено go_to_heal = True")
    async def war_preparation_timer(self):
        """Таймер подготовки к войне - проверяем kopka через 25, 46 и 58 минут"""
        print("Запущен таймер подготовки к войне")
        # Если в ожидании капчи, то сразу выходим
        # if self.waiting_for_captcha:
        #     return
        # Ждём 25 минут и проверяем kopka и prem
        await asyncio.sleep(25 * 60)  # 25 минут в секундах
        if self.kopka and not self.prem and not self.waiting_for_captcha:
            print("Через 25 минут kopka=True и prem=False, отправляем в Лес пламени")
            await self.client.send_message(self.bot_id, self.location)
        else:
            if not self.kopka:
                print("Через 25 минут kopka=False")
            if self.prem:
                print("Через 25 минут prem=True (есть АБУ)")
        # Ждём ещё 21 минуту (итого 46 минут от начала)
        await asyncio.sleep(21 * 60)
        if self.kopka and self.prem and not self.waiting_for_captcha:
            print("Через 46 минут kopka=True и prem=True, отправляем в Лес пламени")
            await self.client.send_message(self.bot_id, self.location)
        else:
            if not self.kopka:
                print("Через 46 минут kopka=False")
            if not self.prem:
                print("Через 46 минут prem=False (нет АБУ)")
        # Ждём ещё 12 минут (итого 58 минут от начала)
        await asyncio.sleep(12 * 60)
        if self.kopka and not self.waiting_for_captcha:
            print("Через 58 минут kopka=True, отправляем в ген. штаб")
            await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
        else:
            print("Через 58 минут kopka=False, остаёмся на месте")
    def common_cave(self):
        print("Устанавливаем обработчик сообщений для common_cave")
        @self.client.on(events.NewMessage(from_users=[self.tomat_id, self.ros_id, self.kroha_id, self.tamplier_id, self.john_id, self.pchelka_id, 5596818972, self.ded_id]))
        async def handle_specific_user_messages(event):
            if event.is_private:  # Проверяем, что сообщение пришло из личного чата
                print(f"Получено новое личное сообщение от пользователя {event.sender_id}: {event.message.text}")
                message_text = event.message.text.lower().strip()
                print(f"Преобразованный текст сообщения: {message_text}")
                # Проверяем текст сообщения и выполняем соответствующие действия
                if "_банка" in message_text or "_банку" in message_text or "_пить" in message_text:
                    # Проверяем, что отправитель не является cave leader
                    if event.sender_id == self.cave_leader_id:
                        print(f"Команда _банка от cave leader {event.sender_id} игнорируется")
                        return
                    print("Отправляем команду /drink_102")
                    await self.client.send_message(self.bot_id, "/drink_102")
                    await event.message.delete()  # Удаляем сообщение
                elif any(key in message_text for key in [
                    "_🕌 нова", "_🕌 мира", "_🕌 антарес", "_🕌 фобос", "_🕌 арэс", 
                    "_🕌 торн", "_🕌 кастор", "_🕌 конкорд", "_🕌 гром", "_🕌 алькор", 
                    "_🏯 беллатрикс", "_🏯 иерихон", "_🏯 цефея", "_🏯 супер нова", 
                    "_🏰 альдебаран", "_🏰 бетельгейзе"
                ]):                    
                # Проверяем, что отправитель не является cave leader
                    if event.sender_id == self.cave_leader_id:
                        print(f"Команда замка от cave leader {event.sender_id} игнорируется")
                        return
                  # Словарь команд замков
                    castle_commands = {
                        "_🕌 нова": "🕌 Нова",
                        "_🕌 мира": "🕌 Мира",
                        "_🕌 антарес": "🕌 Антарес",
                        "_🕌 фобос": "🕌 Фобос",
                        "_🕌 арэс": "🕌 Арэс",
                        "_🕌 торн": "🕌 Торн",
                        "_🕌 кастор": "🕌 Кастор",
                        "_🕌 конкорд": "🕌 Конкорд",
                        "_🕌 гром": "🕌 Гром",
                        "_🕌 алькор": "🕌 Алькор",
                        "_🏯 беллатрикс": "🏯 Беллатрикс",
                        "_🏯 иерихон": "🏯 Иерихон",
                        "_🏯 цефея": "🏯 Цефея",
                        "_🏯 супер нова": "🏯 Супер нова",
                        "_🏰 альдебаран": "🏰 Альдебаран",
                        "_🏰 бетельгейзе": "🏰 Бетельгейзе"
                    }
                  # Находим соответствующую команду
                    castle_command = None
                    for key, value in castle_commands.items():
                        if key in message_text:
                            castle_command = value
                            break
                    if castle_command:
                        if self.kopka:  
                            print(f"Отправляем комплект chv для замка {castle_command}")
                            await self.client.send_message(self.bot_id, RF.chv)
                            await self.wait_for_set_change()
                            await asyncio.sleep(1)
                            print(f"Отправляем команду в ген. штаб")
                            await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
                            await self.arrival_hil()
                            await asyncio.sleep(2)
                            await self.client.send_message(self.bot_id, castle_command)
                        else:
                            await self.client.send_message(self.bot_id, RF.chv)
                            await self.wait_for_set_change()
                            await asyncio.sleep(1)
                            await self.client.send_message(self.bot_id, "💖 Пополнить здоровье")
                            await asyncio.sleep(3)
                            await self.client.send_message(self.bot_id, castle_command)
                        await event.message.delete()
                elif "_фольт" in message_text:
                    # Проверяем, что отправитель не является cave leader
                    # if event.sender_id == self.cave_leader_id:
                    #     print(f"Команда _фольт от cave leader {event.sender_id} игнорируется")
                    #     return
                    # Проверяем наличие фольт биндов
                    if hasattr(self, 'folt_binds') and self.folt_binds:
                        print("Отправляем команду folt_binds")
                        await self.client.send_message(self.bot_id, self.folt_binds[0][1])
                    else:
                        print("Фольт бинды не настроены, просто удаляем сообщение")
                    await event.message.delete()  # Удаляем сообщение
                elif "_гш" in message_text and not self.waiting_for_captcha:  
                    if self.kopka:  
                        print("Отправляем комплект hp_{self.hp_binds[0][0]})")
                        await self.client.send_message(self.bot_id, self.hp_binds[0][1])  # Используем переменную hp_{self.hp_binds[0][0]}) для надевания
                        await self.wait_for_set_change() #работает
                        await asyncio.sleep(1)
                        self.my_health = self.my_max_health = self.hp_binds[0][0]
                        print(f"Здоровье обновлено: {self.my_health}/{self.my_max_health}")
                        print("Отправляем команду /go_to_gsh")
                        await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
                        await self.arrival_hil()  # Вызываем arrival_hil после отправки в ген. штаб
                    else:
                        await self.client.send_message(self.bot_id, self.hp_binds[0][1])
                        await self.wait_for_set_change() #работает
                        await asyncio.sleep(1)
                        self.my_health = self.my_max_health = self.hp_binds[0][0]
                        await self.client.send_message(self.bot_id, "💖 Пополнить здоровье")
                    await event.message.delete()  # Удаляем сообщение
                elif "_стоп" in message_text or "_стой" in message_text:
                    if self.is_moving:
                        await self.client.send_message(self.bot_id, "🏃‍♂️Отменить переход")
                    await event.message.delete()  # Удаляем сообщение
                elif "_краги" in message_text:  
                    # Проверяем, что отправитель не является cave leader
                    if event.sender_id == self.cave_leader_id:
                        print(f"Команда _краги от cave leader {event.sender_id} игнорируется")
                        return  
                    await self.client.send_message(self.bot_id, "🌋 Краговые шахты")
                    await event.message.delete()  # Удаляем сообщение
                elif "_restart" in message_text:
                    print("Получена команда перезапуска")
                    await event.message.delete()  # Удаляем сообщение
                    msg = await self.client.send_message(event.chat_id, "Ver.becccl3.18.10")
                    await asyncio.sleep(5)
                    await msg.delete()  # Удаляем сообщение о версии
                    await asyncio.sleep(1)
                    await self.client.disconnect()
                    import os, sys
                    os.execv(sys.executable, [sys.executable] + sys.argv) #перезапуск скрипта
                elif "_пещера" in message_text:  
                    # Проверяем, что отправитель не является cave leader
                    if event.sender_id == self.cave_leader_id:
                        print(f"Команда _хил от cave leader {event.sender_id} игнорируется")
                        return                    
                    if self.kopka:  
                        print("Отправляем комплект hp_{self.hp_binds[0][0]})")
                        await self.client.send_message(self.bot_id, self.hp_binds[0][1])  # Используем переменную hp_{self.hp_binds[0][0]}) для надевания
                        await self.wait_for_set_change() #работает 
                        await asyncio.sleep(1)
                        self.my_health = self.my_max_health = self.hp_binds[0][0]
                        print(f"Здоровье обновлено: {self.my_health}/{self.my_max_health}")
                        await asyncio.sleep(5)
                        print("Отправляем команду /go_to_gsh")
                        await self.client.send_message(self.bot_id, "🏛 В ген. штаб")
                        await self.arrival_hil()  # Вызываем arrival_hil после отправки в ген. штаб
                        await asyncio.sleep(2)
                        await self.client.send_message(self.bot_id, "🚠 Отправиться в пещеры")
                    else:
                        await self.client.send_message(self.bot_id, self.hp_binds[0][1])
                        await self.wait_for_set_change() #работает 
                        await asyncio.sleep(1)
                        self.my_health = self.my_max_health = self.hp_binds[0][0]
                        await self.client.send_message(self.bot_id, "💖 Пополнить здоровье")
                        await asyncio.sleep(3)
                        await self.client.send_message(self.bot_id, "🚠 Отправиться в пещеры")
                    await event.message.delete()  # Удаляем сообщение
                elif "_шаг" in message_text:  
                    if not self.is_in_caves:
                        return
                    await asyncio.sleep(1)  
                    await self.cave_buttons_message.click(2)
                    await event.message.delete()  # Удаляем сообщение
                elif "_мобы" in message_text:  
                    self.mobs = True
                    self.location = "🔥 61-65 Лес пламени"  # Добавьте эту строку
                    await self.client.send_message(self.bot_id, RF.hp)
                    await self.wait_for_set_change()
                    await asyncio.sleep(1)
                    await event.message.delete()
                elif "_этер" in message_text:
                    self.mobs = True  # или False, в зависимости от вашей логики
                    self.location = "🏔 Этер"
                    await self.client.send_message(self.bot_id, RF.hp)
                    await self.wait_for_set_change()
                    await asyncio.sleep(1)
                    await event.message.delete()
                elif "_данжи" in message_text:  
                    self.mobs = False  # Устанавливаем флаг для данжей
                    # await self.client.send_message(self.cave_leader_id, "Ходим в данжи")  # Сообщение об изменении флага
                    # await self.client.send_message(self.bot_id, RF.chv)
                    await event.message.delete()  # Удаляем сообщение
                elif "_выход" in message_text:  
                    # Проверяем, что отправитель не является cave leader
                    if event.sender_id == self.cave_leader_id:
                        print(f"Команда _хил от cave leader {event.sender_id} игнорируется")
                        return
                    await asyncio.sleep(1)  
                    await self.rf_message.click(3)
                    await event.message.delete()  # Удаляем сообщение
                elif "_рес" in message_text:  
                    # Проверяем, что отправитель не является cave leader
                    if event.sender_id == self.cave_leader_id:
                        print(f"Команда _рес от cave leader {event.sender_id} игнорируется")
                        return
                    # if self.is_has_res:  # Проверяем, что is_has_res равно True
                    self.is_has_res = False
                    await asyncio.sleep(randint(14, 20))
                    await self.client.send_message(self.bot_id, self.hp_binds[0][1])  # Надеваем бинд на самое большое HP
                    await self.wait_for_set_change()
                    await asyncio.sleep(1)
                    await self.cave_buttons_message.click(1)
                    print(self.my_health, self.my_max_health)
                    self.my_health = self.my_max_health = self.hp_binds[0][0]
                    self.last_bind = self.hp_binds[0][1]
                    await event.message.delete()  # Удаляем сообщение
                elif "_состав" in message_text:  
                    await asyncio.sleep(1)  
                    await self.client.send_message(self.bot_id, "⚖️Проверить состав")
                    # Ожидаем сообщение, начинающееся с "Состав:"
                    while True:
                        await asyncio.sleep(0.1)  # Добавите задержку 
                        last_message = await self.client.get_messages(self.bot_id, limit=1)
                        if last_message:
                            message_text_check = last_message[0].message.split('\n')[0]
                            if message_text_check.startswith("Состав:"):
                                print(f"Получено сообщение о составе: {message_text_check}")
                                break
                    # Ждем 1 секунду
                    await asyncio.sleep(2)
                    # Отправляем второе сообщение
                    await self.client.send_message(self.bot_id, "⚖️ Проверить состав")
                    await event.message.delete()  # Удаляем сообщение
                elif "_моб" in message_text:  
                    if self.is_in_caves:
                        return
                    await asyncio.sleep(1)  
                    await self.client.send_message(self.bot_id, self.location)
                    await event.message.delete()  # Удаляем сообщение
                elif "_булочка" in message_text:  
                    await asyncio.sleep(1)  
                    # await self.client.send_message(self.cave_leader_id, "булочка")
                    self.is_in_caves = self.is_has_hil = self.is_has_res = self.extra_hil = True
                    await event.message.delete()  # Удаляем сообщение
                    await asyncio.sleep(10)
                    # if self.is_in_caves:  # Изменено на self.is_in_caves
                    await self.client.send_message(self.bot_id, "⚖️Проверить состав")
                    await asyncio.sleep(20)
                    self.last_bind = self.after_bind
                    # Добавляем проверку текущего здоровья перед autoHeal
                    await self.client.send_message(self.bot_id, "/hero")
                    await asyncio.sleep(3)  # Ждем ответа от бота
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
                                    if not self.is_player_dead and self.last_bind != self.hp_binds[0][1] and self.is_has_hil and self.extra_hil:
                                        self.is_has_hil = False
                                        await self.client.send_message(self.bot_id, self.hp_binds[0][1])  # Надеваем {self.hp_binds[0][0]}) HP
                                        await self.wait_for_set_change() #надо проверить
                                        await asyncio.sleep(1)
                                        print(f"Сменили бинд на: {self.hp_binds[0][1]} (макс. здоровье: {self.hp_binds[0][0]}))")
                                        await self.rf_message.click(0)  # Выполняем клик для хила
                                        self.my_health = self.my_max_health = self.hp_binds[0][0]
                                        self.last_bind = self.hp_binds[0][1]
                                        print(f"Статус has_hil обновлен: {self.is_has_hil}")
                                    return  # Завершаем выполнение блока после хила
                            else:
                                print("Не удалось извлечь здоровье из строки")
                        else:
                            print("Не найдена строка с информацией о здоровье")
                    else:
                        print("Не получен ответ от бота на /hero")
                    await self.autoHeal()  # Вызываем autoHeal() для всех остальных случаев
                elif "_данж" in message_text:
                    # Проверяем, что отправитель не является cave leader
                    if event.sender_id == self.cave_leader_id:
                        print(f"Команда _хил от cave leader {event.sender_id} игнорируется")
                        return
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
                        await self.client.send_message(self.bot_id, self.location)
                    else:
                        # Если движение не активно, выполняем команду
                        await asyncio.sleep(1)
                        if self.kopka:  # Проверяем значение self.kopka
                            await self.client.send_message(self.bot_id, self.location)
                            # Отправляем сообщение пользователю
                            await self.client.send_message(
                                event.sender_id,  # ID пользователя, который отправил команду
                                "Данж будет через 1 минуту."
                            )
                        else:
                            await self.client.send_message(self.bot_id, "/go_dange_10014")
                    await event.message.delete()  # Удаляем сообщение
                elif "_хил" in message_text:  
                    # Проверяем, что отправитель не является cave leader
                    if event.sender_id == self.cave_leader_id:
                        print(f"Команда _хил от cave leader {event.sender_id} игнорируется")
                        return
                    if self.last_bind != self.hp_binds[0][1] and self.is_has_hil:
                        self.is_has_hil = False
                        await asyncio.sleep(5)  # Ждем 3 секунды
                        await self.client.send_message(self.bot_id, self.hp_binds[0][1])  # Надеваем {self.hp_binds[0][0]}) HP
                        await self.wait_for_set_change() #надо проверить
                        await asyncio.sleep(1)
                        await self.cave_buttons_message.click(0)  # Выполняем клик
                        print(f"Сменили бинд на: {self.hp_binds[0][1]} (макс. здоровье: {self.hp_binds[0][0]}))")
                        self.my_health = self.my_max_health = self.hp_binds[0][0]
                        self.last_bind = self.hp_binds[0][1]
                        await event.message.delete()  # Удаляем сообщение
                elif "_энка" in message_text:  
                    if self.last_energy_message:  # Проверяем, что last_energy_message не None
                        if self.your_name in ["𝕴𝖆𝖒𝖕𝖑𝖎𝖊𝖗", ]:
                            # Для специального пользователя всегда отправляем в bezvgroup
                            forwarded_msg = await self.last_energy_message.forward_to(self.bezvgroup)
                        else:
                            # Для остальных пользователей проверяем пещеры
                            if self.is_in_caves:
                                forwarded_msg = await self.last_energy_message.forward_to(self.group59)
                            else:    
                                forwarded_msg = await self.last_energy_message.forward_to(1033007754)
                        # Удаляем переслаанное сообщение через 3 секунды
                        await asyncio.sleep(3)
                        await forwarded_msg.delete()
                    else:
                        if self.your_name in ["𝕴𝖆𝖒𝖕𝖑𝖎𝖊𝖗", ]:
                            # Для специального пользователя всегда отправляем в bezvgroup
                            sent_msg = await self.client.send_message(self.bezvgroup, "ещё не капнуло")
                        else:
                            # Для остальных пользователей проверяем пещеры
                            if self.is_in_caves:
                                sent_msg = await self.client.send_message(self.group59, "ещё не капнуло")
                            else:
                                sent_msg = await self.client.send_message(1033007754, "ещё не капнуло")
                        # Удаляем отправленное сообщение через 3 секунды
                        await asyncio.sleep(3)
                        await sent_msg.delete()
                    await event.message.delete()  # Удаляем исходное сообщение
                elif "_акры+" in message_text or "_акры-" in message_text:
                    # Управляем флагом Aquilla
                    self.go_term_Aquilla = "_акры+" in message_text
                    # Отправляем сообщение об изменении флага
                    # if self.go_term_Aquilla:
                    #     await self.client.send_message(self.cave_leader_id, "Включен флаг Aquilla")
                    # else:
                    #     await self.client.send_message(self.cave_leader_id, "Выключен флаг Aquilla")
                    await event.message.delete()  # Удаляем сообщение
                elif "_белки+" in message_text or "_белки-" in message_text:
                    # Управляем флагом Basilaris
                    self.go_term_Basilaris = "_белки+" in message_text
                    # Отправляем сообщение об изменении флага
                    # if self.go_term_Basilaris:
                    #     await self.client.send_message(self.cave_leader_id, "Включен флаг Basilaris")
                    # else:
                    #     await self.client.send_message(self.cave_leader_id, "Выключен флаг Basilaris")
                    await event.message.delete()  # Удаляем сообщение
                elif "_наш+" in message_text or "_наш-" in message_text:
                    # Управляем флагом Castitas
                    self.go_term_Castitas = "_наш+" in message_text
                    # Отправляем сообщение об изменении флага
                    # if self.go_term_Castitas:
                    #     await self.client.send_message(self.cave_leader_id, "Включен флаг Castitas")
                    # else:
                    #     await self.client.send_message(self.cave_leader_id, "Выключен флаг Castitas")
                    await event.message.delete()  # Удаляем сообщение
                elif "_терм+" in message_text or "_терм-" in message_text:
                    # Управляем обоими флагами (Aquilla и Basilaris)
                    target_value = "_терм+" in message_text
                    self.go_term_Aquilla = target_value
                    self.go_term_Basilaris = target_value
                    # Отправляем сообщение об изменении флагов
                    # if target_value:
                    #     await self.client.send_message(self.cave_leader_id, "Включены оба флага (Aquilla и Basilaris)")
                    # else:
                    #     await self.client.send_message(self.cave_leader_id, "Выключены оба флага (Aquilla и Basilaris)")
                    await event.message.delete()  # Удаляем сообщение
                elif "_гебо" in message_text:
                    # Проверяем, что отправитель не является cave leader
                    if event.sender_id == self.cave_leader_id:
                        print(f"Команда _гебо от cave leader {event.sender_id} игнорируется")
                        return
                    self.go_term_Basilaris = True
                    if self.is_moving:
                        await asyncio.sleep(1)
                        while self.is_moving:
                            print("Персонаж все еще двигается, ждем...")
                            await asyncio.sleep(5)
                        print("Персонаж перестал двигаться.")
                        await asyncio.sleep(5)
                    else:
                        await asyncio.sleep(1)
                    await self.client.send_message(self.bot_id, "👩‍🚀Алтарь Гебо")
                    await event.message.delete()  # Удаляем сообщение
                elif "_эйви" in message_text:
                    # Проверяем, что отправитель не является cave leader
                    if event.sender_id == self.cave_leader_id:
                        print(f"Команда _эйви от cave leader {event.sender_id} игнорируется")
                        return
                    self.go_term_Aquilla = True
                    if self.is_moving:
                        await asyncio.sleep(1)
                        while self.is_moving:
                            print("Персонаж все еще двигается, ждем...")
                            await asyncio.sleep(5)
                        print("Персонаж перестал двигаться.")
                        await asyncio.sleep(5)
                    else:
                        await asyncio.sleep(1)
                    await self.client.send_message(self.bot_id, "🤖Алтарь Эйви")
                    await event.message.delete()  # Удаляем сообщение
                elif "_тир" in message_text:
                    # Проверяем, что отправитель не является cave leader
                    if event.sender_id == self.cave_leader_id:
                        print(f"Команда _тир от cave leader {event.sender_id} игнорируется")
                        return
                    self.go_term_Aquilla = True
                    if self.is_moving:
                        await asyncio.sleep(1)
                        while self.is_moving:
                            print("Персонаж все еще двигается, ждем...")
                            await asyncio.sleep(5)
                        print("Персонаж перестал двигаться.")
                        await asyncio.sleep(5)
                    else:
                        await asyncio.sleep(1)
                    await self.client.send_message(self.bot_id, "🤖Алтарь Тир")
                    await event.message.delete()  # Удаляем сообщение
                elif "_иса" in message_text:
                    # Проверяем, что отправитель не является cave leader
                    if event.sender_id == self.cave_leader_id:
                        print(f"Команда _иса от cave leader {event.sender_id} игнорируется")
                        return
                    self.go_term_Basilaris = True
                    if self.is_moving:
                        await asyncio.sleep(1)
                        while self.is_moving:
                            print("Персонаж все еще двигается, ждем...")
                            await asyncio.sleep(5)
                        print("Персонаж перестал двигаться.")
                        await asyncio.sleep(5)
                    else:
                        await asyncio.sleep(1)
                    await self.client.send_message(self.bot_id, "👩‍🚀Алтарь Иса")
                    await event.message.delete()  # Удаляем сообщение
                elif "_исс" in message_text:
                    # Проверяем, что отправитель не является cave leader
                    if event.sender_id == self.cave_leader_id:
                        print(f"Команда _исс от cave leader {event.sender_id} игнорируется")
                        return
                    if self.is_moving:
                        await asyncio.sleep(1)
                        while self.is_moving:
                            print("Персонаж все еще двигается, ждем...")
                            await asyncio.sleep(5)
                        print("Персонаж перестал двигаться.")
                        await asyncio.sleep(5)
                    else:
                        await asyncio.sleep(1)
                    await self.client.send_message(self.bot_id, "🧝‍♀Алтарь Исс")
                    await event.message.delete()  # Удаляем сообщение
                elif "_дагаз" in message_text:
                    # Проверяем, что отправитель не является cave leader
                    if event.sender_id == self.cave_leader_id:
                        print(f"Команда _дагаз от cave leader {event.sender_id} игнорируется")
                        return
                    if self.is_moving:
                        await asyncio.sleep(1)
                        while self.is_moving:
                            print("Персонаж все еще двигается, ждем...")
                            await asyncio.sleep(5)
                        print("Персонаж перестал двигаться.")
                        await asyncio.sleep(5)
                    else:
                        await asyncio.sleep(1)
                    await self.client.send_message(self.bot_id, "🧝‍♀Алтарь Дагаз")
                    await event.message.delete()  # Удаляем сообщение 
                elif "_хагал" in message_text:
                    # Проверяем, что отправитель не является cave leader
                    if event.sender_id == self.cave_leader_id:
                        print(f"Команда _хагал от cave leader {event.sender_id} игнорируется")
                        return
                    self.go_term_Castitas = True
                    if self.is_moving:
                        await asyncio.sleep(1)
                        while self.is_moving:
                            print("Персонаж все еще двигается, ждем...")
                            await asyncio.sleep(5)
                        print("Персонаж перестал двигаться.")
                        await asyncio.sleep(5)
                    else:
                        await asyncio.sleep(1)
                    await self.client.send_message(self.bot_id, "🧝‍♀Алтарь Хагал")
                    await event.message.delete()  # Удаляем сообщение
                elif "_heal" in message_text:  # Проверяем наличие команды
                    new_value = int(message_text.split()[-1])
                    self.pvpgoheal = new_value  # Устанавливаем новое значение
                    # await self.client.send_message(self.cave_leader_id, f"Хил установлен на: {self.pvpgoheal}")  # Сообщение с новым значением
                    await event.message.delete()  # Удаляем сообщение
                elif "_chv" in message_text:  # Проверяем наличие команды
                    new_value = message_text.split()[-1]  # Получаем последнее слово, это и будет новый value
                    RF.chv = new_value  # Устанавливаем новое значение переменной chv
                    await event.message.delete()  # Удаляем сообщение
                elif "_zatochka" in message_text:
                    new_value = message_text.split()[-1]
                    if new_value.isdigit():
                        self.zatochka = int(new_value)
                    await event.message.delete()
                elif "_фаст+" in message_text:
                    self.fast_cave = True
                    # await self.client.send_message(self.cave_leader_id, "Включен флаг fast_cave")
                    await event.message.delete()
                elif "_фаст-" in message_text:
                    self.fast_cave = False
                    # await self.client.send_message(self.cave_leader_id, "Выключен флаг fast_cave")
                    await event.message.delete()
                elif "_active+" in message_text or "_active-" in message_text:
                    # Управляем флагом active
                    self.active = "_active+" in message_text
                    # Когда флаг активен
                    if self.active:
                        self.go_term_Aquilla = False
                        self.go_term_Basilaris = False
                        # await self.client.send_message(self.cave_leader_id, "Флаг active включен")
                    else:
                        self.go_term_Aquilla = True
                        self.go_term_Basilaris = True
                        # await self.client.send_message(self.cave_leader_id, "Флаг active выключен")
                    await event.message.delete()  # Удаляем сообщение
                else:
                    print("Точное совпадение с ключевыми словами не обнаружено")
        print("Обработчик сообщений для common_cave успешно установлен")
        print(f"Ваше текущее здоровье: {self.my_health}")
        print(f"Находитесь ли вы в пещерах: {self.is_in_caves}")
        print(f"Являетесь ли вы лидером пещер: {self.is_cave_leader}")
    async def vihod_s_caves(self, lstr):
        self.is_cave_leader = any(f"/group_guild_join_{self.cave_leader_id}" in line for line in lstr)
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
        elif alive_count > 1 and total_health < 4000:
            should_exit = True
            reason = f"осталось {alive_count} живых с суммарным здоровьем менее 4000 HP"
        if should_exit and not alive_has_heal and not group_has_res:
            message = f"{'Ты лидер' if self.is_cave_leader else 'Ты не лидер'}, пора на выход. Общее здоровье: {total_health}, нет хилок у живых и ресов в группе"
            # await self.client.send_message(self.cave_leader_id, message)
            print(message)
            if self.is_cave_leader:
                for member_id in group_members:
                    if member_id != self.cave_leader_id:
                        await self.client.send_message(member_id, "Выходим из пещеры _фольт")
                        print(f"Отправлено сообщение участнику {member_id}: Выходим из пещеры _фольт")
                await asyncio.sleep(15) 
                await self.rf_message.click(3)
        else:
            print(f"Ещё рано на выход. Общее здоровье: {total_health}, Живых: {alive_count}")
    async def hp_in_caves_kingRagnar(self, lstr):
        print(f"Привет, kingRagnar в пещерах")
        # ✅ Устанавливаем флаг cave_leader
        self.is_cave_leader = any(f"/group_guild_join_{self.cave_leader_id}" in line for line in lstr)
        # ✅ Работаем если в пещерах ИЛИ лидер
        if not (self.is_in_caves and self.is_cave_leader):
            print("Ты не в пещерах или не лидер — выход из функции.")
            return
        for line in lstr:
            if "👨‍🦳Пенсионер☠️" in line:  # Проверяем, что это сообщение для kingRagnar
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
                        await self.client.send_message(self.players["👨‍🦳Пенсионер☠️"], new_set)
                        print(f"Отправлено сообщение: {new_set}")
                        self.last_set_kingRagnar = new_set  # Обновляем last_set
                    print(f"Текущий сет: {self.last_set_kingRagnar}")
                    break
    async def time_cave(self, lstr):  # Добавлен параметр lstr
        # Проверка, является ли текущий пользователь лидером
        self.is_cave_leader = any(f"/group_guild_join_{self.cave_leader_id}" in line for line in lstr)
        if not self.is_cave_leader:
            print("Ты не пативод, time_cave не работает.")  # Добавлен вывод, если не пативод
        print(f"{'Ты пативод' if self.is_cave_leader else 'Ты не пативод'}")
        if self.cave_task_running:
            print("Задача time_cave уже запущена.")  # Отладочное сообщение
            # await self.client.send_message(self.cave_leader_id, "Задача time_cave уже запущена.")  # Отправка сообщения
            return
        self.cave_task_running = True  # Устанавливаем флаг, что задача запущена
        print("Метод time_cave запущен.")
        # await self.client.send_message(self.cave_leader_id, "Метод time_cave запущен.")  # Отправка сообщения
        # Константы для времени
        CHECK_HOUR = 20
        CHECK_MINUTE = 55
        while True:
            now = datetime.datetime.now()
            print(f"Текущее время: {now}")
            # await self.client.send_message(self.cave_leader_id, f"Текущее время на сервере: {now}")  # Отправка сообщения
            next_check = now.replace(hour=CHECK_HOUR, minute=CHECK_MINUTE, second=0, microsecond=0)
            if now >= next_check:
                next_check += datetime.timedelta(days=1)
                print("Устанавливаем время следующей проверки на следующий день.")
                # await self.client.send_message(self.cave_leader_id, f"Устанавливаем время следующей проверки на следующий день: {next_check}")  # Отправка сообщения
            wait_time = (next_check - now).total_seconds()
            print(f"Ожидание до следующего {CHECK_HOUR}:{CHECK_MINUTE}: {wait_time} секунд.")
            # await self.client.send_message(self.cave_leader_id, f"Ожидание до следующего {CHECK_HOUR}:{CHECK_MINUTE}: {wait_time} секунд.")  # Отправка сообщения
            await asyncio.sleep(wait_time)
            # Условие выхода из цикла (например, по какому-то флагу)
            if not self.is_in_caves or not self.is_cave_leader:  # Если не в пещере или не лидер, выходим из цикла
                # await self.client.send_message(self.cave_leader_id, "Вы не были в пещере или не нажали кнопку.")  # Сообщение о том, что не нажали
                if not self.waiting_for_captcha:  # Если не ждём капчу, отправляем /daily
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
            # await self.client.send_message(self.cave_leader_id, "Вы были в пещере и нажали кнопку.")  # Сообщение о нажатии
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
        if self.active:
            return random.choice([
                "🧝‍♀Алтарь Дагаз", 
                "👩‍🚀Алтарь Гебо", 
                "👩‍🚀Алтарь Иса", 
                "🧝‍♀Алтарь Исс", 
                "🤖Алтарь Эйви", 
                "🤖Алтарь Тир"
            ])
        else:
            return random.choice([
                "👩‍🚀Алтарь Гебо", 
                # "🧝‍♀Алтарь Дагаз", 
                # "🤖Алтарь Эйви", 
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
        if not (self.is_nacheve_active or self.is_training or self.in_castle or self.v_terminale):
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
                # await self.client.send_message(self.group59, "Капча пройдена")  # Отправляем сообщение
            # После решения капчи или если её не было - проверяем прибытие
            if self.mobs:  # Проверяем, включен ли флаг для мобов
                await self.check_arrival()         # для мобов
            else:
                await self.check_arrival_dange()    # для данжей
    async def cave_profit(self, lstr):
        # ✅ Устанавливаем флаг cave_leader
        self.is_cave_leader = any(f"/group_guild_join_{self.ros_id}" in line for line in lstr)
        # ✅ Работаем если в пещерах ИЛИ лидер
        if not (self.is_in_caves and self.is_cave_leader):
            print("Ты не в пещерах или не лидер — выход из функции.")
            return
        reward_line = next((line for line in lstr if "🌕Опыт:" in line), None)
        if reward_line:
            match = re.search(r"🌕Опыт:\s*(\d+)\((\d+)\)", reward_line)
            if match:
                total_experience = int(match.group(1))
                experience_points = int(match.group(2))
                if self.steps is not None and self.steps > 0:
                    # Проверяем, изменилось ли количество шагов с прошлого вызова
                    if self.last_step is not None and self.steps == self.last_step:
                        print("Количество шагов не изменилось, пропускаем обновление графика.")
                        return
                    experience_per_step = experience_points / self.steps
                    self.experience_history.append(experience_per_step)
                    # Обновляем предыдущее количество шагов
                    self.last_step = self.steps
                    # Генерируем ASCII-графику
                    ascii_graph = self.generate_ascii_graph(self.experience_history[-40:])  # Последние 40 значений
                    efficiency_message = "Выгодно" if experience_per_step > 22500 else "Не выгодно"
                    message_text = f"```\nОпыт за шаг: {experience_per_step:.2f} ({efficiency_message})\n{ascii_graph}\n```"
                    print(message_text)
                    # Обновляем сообщение с графиком
                    if self.cave_message_id is None:
                        message = await self.client.send_message(self.cave_leader_id, message_text)
                        self.cave_message_id = message.id
                        if not self.cave_message_pinned:
                            await self.client.pin_message(self.cave_leader_id, message.id)
                            self.cave_message_pinned = True
                    else:
                        await self.client.edit_message(self.cave_leader_id, self.cave_message_id, message_text)
                else:
                    print("Количество шагов равно 0 или не установлено.")
        else:
            print("Не найдена строка с информацией об опыте.")
    def generate_ascii_graph(self, data):
        if not data:
            return "Нет данных для графика"
        # Настройки графика
        width = len(data)  # Ширина графика соответствует количеству точек
        height = 12
        max_value = max(data) if data else 1
        min_value = min(data) if data else 0
        value_range = max_value - min_value if max_value != min_value else 1  # Предотвращаем деление на ноль
        # Нормализация данных
        normalized = [(x - min_value) / value_range for x in data]
        # Генерация графика
        graph = []
        for y in range(height, 0, -1):
            line = []
            for x in normalized:
                scaled = x * (height - 1)
                if scaled >= y - 1:
                    line.append("█")
                else:
                    line.append("░")  # Используем полупрозрачный символ
            graph.append("".join(line))
        # Добавляем оси и метки с фиксированной шириной
        x_axis = "—" * width
        y_labels = [f"{int(min_value + (value_range * y/height)):6d}" for y in range(height, 0, -1)]  # Фиксированная ширина
        graph_with_labels = [f"{y_labels[i]} | {graph[i]}" for i in range(height)]
        graph_with_labels.append(f"       | {x_axis}")
        # Создаем линию для меток оси X
        x_label_line = " " * 9
        for i in range(width):
            if i % 2 == 0:  # Ставим метку на каждом втором шаге для компактности
                x_label_line += f"{i}"
            else:
                x_label_line += " "
        graph_with_labels.append(x_label_line)
        return "\n".join(graph_with_labels)
    async def vterminale(self):
        print("работаем в терминале")
        self.is_nacheve_active = True
        self.cmd_altar = None  # не нужен, но для совместимости сбрасываем
        @self.client.on(events.NewMessage(chats=-1001284047611))
        async def handle_rf_info(event):
            print("Получено новое сообщение от RF чата.")
            first_line = event.message.text.split('\n')[0]
            print(f"Первая строка сообщения: {first_line}")
            await self.parce_4v_logs(event.message.text)
        try:
            while self.is_nacheve_active:
                bot_message = await self.client.get_messages(self.bot_id, limit=1)
                if bot_message:
                    message = bot_message[0]
                    lstr = message.message.split('\n')
                    print(f"Сообщение от бота:")
                    print(f"    lstr[0]: {lstr[0]}")
                    print(f"    lstr[-1]: {lstr[-1]}")
                    # Только обработка побед/смертей/переходов
                    if await self.process_bot_message(lstr):
                        continue
                print("Ожидание 6 секунд перед следующей проверкой (терминал)...")
                await asyncio.sleep(6)
        finally:
            self.client.remove_event_handler(handle_rf_info)
            self.is_nacheve_active = False
            print("Завершаем работу в терминале")
