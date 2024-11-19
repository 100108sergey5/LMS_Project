import sys
import sqlite3
import re
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QListWidget, QTextEdit, QHBoxLayout
)
from PyQt6.QtGui import QFont  # QFont - менять шрифты


# Создание diary.sqlite если она не создана до этого
def create_database():
    con = sqlite3.connect('diary.sqlite')
    cur = con.cursor()

    # Таблицы:
    # Пользователи
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')  # users(id | username | password)

    # Записи пользователей
    cur.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')  # records(id записи | id пользователя, чья запись | содержимое)

    con.commit()
    con.close()


# Регистрация
def add_user(username, password):
    con = sqlite3.connect('diary.sqlite')
    cur = con.cursor()
    try:
        cur.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        con.commit()
        return True
    except sqlite3.IntegrityError:  # Если username не уникален, как требует sqlite
        return False
    finally:
        con.close()


# Вход в профиль пользователя с его записями
def verify_user(username, password):
    con = sqlite3.connect('diary.sqlite')
    cur = con.cursor()
    cur.execute('SELECT id FROM users WHERE username = ? AND password = ?', (username, password))
    user = cur.fetchone()
    con.close()
    return user[0] if user else None


# Добавляем запись в базу данных
def add_record(user_id, content):
    con = sqlite3.connect('diary.sqlite')
    cur = con.cursor()
    cur.execute('INSERT INTO records (user_id, content) VALUES (?, ?)', (user_id, content))
    con.commit()
    con.close()


# Получаем записи пользователя из sqlite
def get_records(user_id):
    con = sqlite3.connect('diary.sqlite')
    cur = con.cursor()
    cur.execute('SELECT id, content FROM records WHERE user_id = ?', (user_id,))
    records = cur.fetchall()
    con.close()
    return records


# Редактирование записи
def edit_record(record_id, new_content):
    con = sqlite3.connect('diary.sqlite')
    cur = con.cursor()
    cur.execute('UPDATE records SET content = ? WHERE id = ?', (new_content, record_id))
    con.commit()
    con.close()


# Делитнуть запись
def delete_record(record_id):
    con = sqlite3.connect('diary.sqlite')
    cur = con.cursor()
    cur.execute('DELETE FROM records WHERE id = ?', (record_id,))
    con.commit()

    con.commit()
    con.close()


# Допустимые символы в пароле/имени пользователя.
# Сказать честно - не сильно шарю за них, но я где-то такую конструкцию нашёл, пока искал как реализовать.
def is_valid_input(username, password):
    pattern = r'^[a-zA-Z0-9_]+$'  # Такую структуру нашёл для проверки символов
    return re.match(pattern, username) and re.match(pattern, password)  # import re (Regular expressions)


# Окно регистрации
class RegistrationApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Регистрация и Вход")
        self.setGeometry(500, 500, 100, 100)
        self.UIFont = QFont('Bahnschrift Light', 16)  # Шрифт, размер шрифта
        self.UIFontButtons = QFont('Bahnschrift Light', 8)  # Шрифт под кнопки
        self.layout = QVBoxLayout()

        self.username_label = QLabel("Имя пользователя:")
        self.username_label.setFont(self.UIFont)
        self.username_input = QLineEdit()
        self.layout.addWidget(self.username_label)
        self.layout.addWidget(self.username_input)

        self.password_label = QLabel("Пароль:")
        self.password_label.setFont(self.UIFont)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.layout.addWidget(self.password_label)
        self.layout.addWidget(self.password_input)

        self.register_button = QPushButton("Регистрация")
        self.register_button.setFont(self.UIFontButtons)
        self.register_button.clicked.connect(self.register_user)
        self.layout.addWidget(self.register_button)

        self.login_button = QPushButton("Вход")
        self.login_button.setFont(self.UIFontButtons)
        self.login_button.clicked.connect(self.login_user)
        self.layout.addWidget(self.login_button)

        self.setLayout(self.layout)

    def register_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not is_valid_input(username, password):
            QMessageBox.warning(self, "Ошибка",
                                "Имя пользователя или пароль содержат недопустимые символы!.")
            return

        if username and password:
            if add_user(username, password):
                QMessageBox.information(self, "Успех", "Пользователь зарегистрирован!")
                self.username_input.clear()
                self.password_input.clear()
            else:
                QMessageBox.warning(self, "Ошибка", "Имя пользователя уже существует.")
        else:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля.")

    def login_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if username and password:
            user_id = verify_user(username, password)
            if user_id:
                QMessageBox.information(self, "Успех", "Вход выполнен!")
                self.open_diary(user_id)
            else:
                QMessageBox.warning(self, "Ошибка", "Неверное имя пользователя или пароль.")
        else:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля.")

    def open_diary(self, user_id):
        self.diary_page = DiaryPage(user_id)
        self.diary_page.show()
        self.close()


class DiaryPage(QWidget):  # Проще сделать отображение через 2 класса.
    def __init__(self, user_id):  # Чтоб после нажатия кнопки вход, открывалось новое окно с самим дневником.
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("Личный Дневник")
        self.setGeometry(500, 500, 400, 400)

        self.layout = QVBoxLayout()  # Layout

        self.record_list = QListWidget()
        self.record_list.itemClicked.connect(self.load_record_content)
        self.layout.addWidget(self.record_list)

        self.content_edit = QTextEdit()
        self.layout.addWidget(self.content_edit)

        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Добавить Запись")
        self.add_button.clicked.connect(self.add_record)
        button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Редактировать Запись")
        self.edit_button.clicked.connect(self.edit_record)
        button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Удалить Запись")
        self.delete_button.clicked.connect(self.delete_record)
        button_layout.addWidget(self.delete_button)

        self.layout.addLayout(button_layout)

        self.load_records()

        self.setLayout(self.layout)

    def load_records(self):
        self.record_list.clear()
        self.dictionary = {}
        records = get_records(self.user_id)
        count = 0  # Перечисление ID записей
        for record in records:
            count += 1
            self.dictionary[count] = record[0]
            if '\n' in record[1]:
                splitter = record[1].split('\n', 1)
                self.record_list.addItem(f"{count}: {splitter[0]}")  # ID, Заголовок записи
            else:
                self.record_list.addItem(f"{count}: {record[1]}")  # ID, Заголовок записи

    def load_record_content(self):
        selected_item = self.record_list.currentItem()

        if selected_item:
            record_id_str = self.dictionary.get(int(selected_item.text().split(":")[0]))
            for record in get_records(self.user_id):
                if record[0] == record_id_str:
                    content = record[1]
                    break
            self.content_edit.setPlainText(content)

    def add_record(self):
        content = self.content_edit.toPlainText().strip()
        if content:
            add_record(self.user_id, content)
            QMessageBox.information(self, "Успех", "Запись добавлена!")
            self.content_edit.clear()
            self.load_records()
        else:
            QMessageBox.warning(self, "Ошибка", "Запись не может быть пустой.")

    def edit_record(self):
        selected_item = self.record_list.currentItem()

        if selected_item:
            record_id = self.dictionary.get(int(selected_item.text().split(":")[0]))
            new_content = self.content_edit.toPlainText().strip()

            if new_content:
                edit_record(record_id, new_content)
                QMessageBox.information(self, "Успех", "Запись отредактирована!")
                self.load_records()
            else:
                QMessageBox.warning(self, "Ошибка", "Запись не может быть пустой.")
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для редактирования.")

    def delete_record(self):
        selected_item = self.record_list.currentItem()

        if selected_item:
            record_id = self.dictionary.get(int(selected_item.text().split(":")[0]))
            delete_record(record_id)
            QMessageBox.information(self, "Успех", "Запись удалена!")
            self.load_records()
            self.content_edit.clear()
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для удаления.")


if __name__ == "__main__":
    create_database()  # Создаем базу данных и таблицы
    app = QApplication(sys.argv)
    window = RegistrationApp()
    window.show()
    sys.exit(app.exec())
