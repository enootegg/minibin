import ctypes
import sys
import os
import threading
import time
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMainWindow
from PyQt6.QtGui import QIcon, QAction

class SHQUERYRBINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("i64Size", ctypes.c_int64),
        ("i64NumItems", ctypes.c_int64)
    ]

def resource_path(relative_path):
    """ Отримує правильний шлях до файлу (для PyInstaller) """
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    full_path = os.path.join(base_path, relative_path)
    
    # print(f"Шлях до ресурсу: {full_path}")  # Лог для перевірки
    if not os.path.exists(full_path):
        print(f"⚠️ Файл не знайдено: {full_path}")
    
    return full_path

def load_icon(icon_path):
    """ Завантаження іконки з перевіркою існування файлу """
    full_path = resource_path(icon_path)
    if not os.path.exists(full_path):
        print(f"⚠️ Іконка не знайдена: {full_path}")
        return QIcon()  # Порожня іконка, щоб уникнути помилок
    return QIcon(full_path)

def show_notification(title, message, icon_path=None):
    # """ Показує повідомлення в системному треї """
    # print(f"🔔 Повідомлення: {title} - {message}")
    tray_icon.showMessage(title, message, load_icon(icon_path), 1000)

def empty_recycle_bin():
    # """ Очищення кошика """
    # print("🗑 Очищення кошика...")
    SHEmptyRecycleBin = ctypes.windll.shell32.SHEmptyRecycleBinW
    flags = 0x01  # SHERB_NOCONFIRMATION

    result = SHEmptyRecycleBin(None, None, flags)

    if result == 0:
        show_notification("Кошик", "Кошик очищено.", "icons/minibin-kt-empty.ico")
    else:
        show_notification("Кошик", f"Помилка очищення: {result}", "icons/minibin-kt-full.ico")

    update_icon()

def open_recycle_bin():
    # """ Відкриває кошик Windows """
    # print("📂 Відкриття кошика...")
    os.startfile("shell:RecycleBinFolder")

def exit_program():
    # """ Завершення програми """
    # print("🚪 Вихід з програми...")
    QApplication.quit()

def update_icon():
    # """ Оновлює іконку трея в залежності від стану кошика """
    # print("🔄 Оновлення іконки...")
    if is_recycle_bin_empty():
        tray_icon.setIcon(load_icon("icons/minibin-kt-empty.ico"))
        # print("✅ Кошик порожній")
    else:
        tray_icon.setIcon(load_icon("icons/minibin-kt-full.ico"))
        # print("❌ Кошик НЕ порожній")

def is_recycle_bin_empty():
    # """ Перевіряє, чи кошик порожній """
    # print("🔍 Перевірка кошика...")
    rbinfo = SHQUERYRBINFO()
    rbinfo.cbSize = ctypes.sizeof(SHQUERYRBINFO)
    result = ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(rbinfo))

    if result != 0:
        print(f"⚠️ Помилка перевірки кошика. Код: {result}")
        return False

    return rbinfo.i64NumItems == 0

def periodic_update():
    """ Періодичне оновлення іконки кожні 3 секунди """
    while True:
        update_icon()
        time.sleep(3)

if __name__ == "__main__":
    # print("🚀 Запуск програми...")

    app = QApplication(sys.argv)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("⚠️ Системний трей недоступний. Програма завершується.")
        sys.exit(1)

    # print("✅ Системний трей доступний")

    # Головне вікно (необхідне для стабільної роботи PyQt)
    window = QMainWindow()
    window.setWindowTitle("Фонове вікно")
    window.setGeometry(100, 100, 200, 100)

    tray_icon = QSystemTrayIcon()
    tray_icon.setIcon(load_icon("icons/minibin-kt-empty.ico"))
    tray_icon.setVisible(True)

    # print("📌 Створено системний трей")

    tray_menu = QMenu()
    open_action = QAction("Відкрити кошик", triggered=open_recycle_bin)
    empty_action = QAction("Очистити кошик", triggered=empty_recycle_bin)
    exit_action = QAction("Вихід", triggered=exit_program)

    tray_menu.addAction(open_action)
    tray_menu.addAction(empty_action)
    tray_menu.addAction(exit_action)

    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()

    # print("📜 Меню трея додано")

    # Запуск оновлення іконки в окремому потоці
    update_thread = threading.Thread(target=periodic_update, daemon=True)
    update_thread.start()

    # print("⏳ Запущено оновлення кожні 3 секунди")

    # Відображення прихованого вікна (запобігає аварійному завершенню програми)
    window.showMinimized()
    window.hide()

    sys.exit(app.exec())
