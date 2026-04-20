import sys
import sqlite3
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import matplotlib.pyplot as plt


def init_db():
    conn = sqlite3.connect('wallet.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            amount REAL NOT NULL,
            description TEXT,
            type TEXT NOT NULL, 
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_next_id():
    conn = sqlite3.connect('wallet.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM transactions ORDER BY id ASC')
    existing_ids = [row[0] for row in cursor.fetchall()]
    
    next_id = 1
    for eid in existing_ids:
        if eid == next_id:
            next_id += 1
        else:
            break
            
    conn.close()
    return next_id

def add_transaction(amount, description, trans_type):
    conn = sqlite3.connect('wallet.db')
    cursor = conn.cursor()

    new_id = get_next_id()

    cursor.execute('INSERT INTO transactions (id, amount, description, type) VALUES (?, ?, ?, ?)',
                   (new_id, amount, description, trans_type))
    conn.commit()
    conn.close()

def get_all_transactions():
    conn = sqlite3.connect('wallet.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, amount, description, type, date FROM transactions ORDER BY id ASC')
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_transaction(trans_id):
    conn = sqlite3.connect('wallet.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transactions WHERE id = ?', (trans_id,))
    conn.commit()
    conn.close()


class Wallet(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('MyBudget')
        self.setGeometry(100, 100, 500, 600)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2f;
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit {
                background-color: #2d2d3f;
                color: #ffffff;
                border: 1px solid #3d3d4f;
                border-radius: 5px;
                padding: 5px;
                font-size: 10px;
            }
            QLineEdit:focus {
                border: 1px solid #6c5ce7;
            }
            QPushButton {
                background-color: #2d2d3f;
                color: #ffffff;
                border: 1px solid #3d3d4f;
                border-radius: 5px;
                padding: 6px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #3d3d4f;
                border-color: #6c5ce7;
            }
            QPushButton:pressed {
                background-color: #1e1e2f;
            }
            QTableWidget {
                background-color: #2d2d3f;
                color: #ffffff;
                border: 1px solid #3d3d4f;
                border-radius: 5px;
                gridline-color: #3d3d4f;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #6c5ce7;
            }
            QHeaderView::section {
                background-color: #1e1e2f;
                color: #a0a0b0;
                border: none;
                padding: 5px;
            }
            QComboBox {
                background-color: #2d2d3f;
                color: #ffffff;
                border: 1px solid #3d3d4f;
                border-radius: 5px;
                padding: 5px;
            }
        """)

        self.x_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        self.y_values = []
        
        init_db()

        self.load_existing_data_for_graph()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.balance_label = QLabel('Баланс: 0.00 ₽')
        self.balance_label.setFont(QFont("Consolas", 16, QFont.Weight.Bold))
        self.balance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.balance_label)

        input_layout = QHBoxLayout()
        
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText('Сумма')
        self.amount_input.setFont(QFont('Consolas', 10))
        self.amount_input.textChanged.connect(self.validate_input)
        input_layout.addWidget(self.amount_input)

        self.delete_id_input = QLineEdit()
        self.delete_id_input.setPlaceholderText('id для удаления')
        self.delete_id_input.setFont(QFont('Consolas', 10))
        self.delete_id_input.textChanged.connect(self.validate_input)
        input_layout.addWidget(self.delete_id_input)

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText('Описание')
        self.desc_input.setFont(QFont('Consolas', 10))
        input_layout.addWidget(self.desc_input)

        layout.addLayout(input_layout)

        btn_layout = QHBoxLayout()
        
        self.btn_income = QPushButton('Доход (+)')
        self.btn_income.setFont(QFont('Consolas', 9))
        self.btn_income.clicked.connect(lambda: self.add_record('income'))

        self.btn_delete = QPushButton('Удалить')
        self.btn_delete.setFont(QFont('Consolas', 9))
        self.btn_delete.clicked.connect(self.delete_selected)

        self.btn_expense = QPushButton('Расход (-)')
        self.btn_expense.setFont(QFont('Consolas', 9))
        self.btn_expense.clicked.connect(lambda: self.add_record('expense'))

        btn_layout.addWidget(self.btn_income)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_expense)
        layout.addLayout(btn_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Дата', 'Описание', 'Сумма', 'ID'])
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) 
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self.btn_graphic = QPushButton('Показать график')
        self.btn_graphic.setFont(QFont('Consolas', 9))
        self.btn_graphic.clicked.connect(self.show_graphic)

        layout.addWidget(self.btn_graphic)

        self.refresh_data()

    def load_existing_data_for_graph(self):
        transactions = get_all_transactions()
        self.y_values = []
        
        for t in transactions[-10:]:
            if t[3] == 'income':
                self.y_values.append(t[1])
            else:
                self.y_values.append(-t[1])


    def validate_input(self, text):
        if text and not text.replace('.', '', 1).isdigit():
            self.amount_input.setText(text[:-1])
            self.amount_input.setCursorPosition(len(text)-1)

    def add_record(self, trans_type):
        a_text = self.amount_input.text()
        d_text = self.desc_input.text()

        if not a_text:
            QMessageBox.warning(self, 'Ошибка', 'Введите сумму!')
            return

        try:
            a = float(a_text)
        except ValueError:
            QMessageBox.warning(self, 'Ошибка', 'Некорректная сумма')
            return

        if a <= 0:
            QMessageBox.warning(self, 'Ошибка', 'Сумма должна быть больше нуля')
            return
    
        add_transaction(a, d_text, trans_type)

        if trans_type == 'income':
            amount_to_add = a
        else:
            amount_to_add = -a
            
        if len(self.y_values) >= 10:
            self.y_values.pop(0)
            self.y_values.append(amount_to_add)
        else:
            self.y_values.append(amount_to_add)

        self.amount_input.clear()
        self.desc_input.clear()

        self.amount_input.clear()
        self.desc_input.clear()



        self.amount_input.clear()
        self.desc_input.clear()
        
        self.refresh_data()

    def delete_selected(self):
        id_text = self.delete_id_input.text().strip()
        
        if not id_text:
            QMessageBox.warning(self, 'Ошибка', 'Введите ID для удаления!')
            return
        
        try:
            trans_id = int(id_text)
        except ValueError:
            QMessageBox.warning(self, 'Ошибка', 'ID должен быть числом!')
            return
        
        delete_transaction(trans_id)
        self.delete_id_input.clear()
        self.refresh_data()

        self.update_y_values()
        
    def update_y_values(self):
        transactions = get_all_transactions()
        self.y_values = []
        
        for i in transactions[-10:]:
            if i[3] == 'income':
                self.y_values.append(i[1])
            else:
                self.y_values.append(-i[1])

    def calculate_balance(self, transactions):
        total = 0
        for t in transactions:
            if t[3] == 'income':
                total += t[1]
            elif t[3] == 'expense':
                total -= t[1]
        return total

    def show_graphic(self):
        if not self.y_values:
            QMessageBox.warning(self, 'Ошибка', 'Нет данных для построения графика!')
            return
            
        plt.figure(figsize=(10, 6), facecolor='#1e1e2f')
        ax = plt.gca()
        ax.set_facecolor('#2d2d3f')
        
        plt.plot(self.x_values[:len(self.y_values)], self.y_values, 
                marker='o', linewidth=2, markersize=6, color='white')
        
        plt.title('Динамика доходов и расходов', fontsize=14, color='white')
        plt.xlabel('Номер транзакции', fontsize=12, color='white')
        plt.ylabel('Сумма (₽)', fontsize=12, color='white')
        
        plt.grid(True, alpha=0.3, color='gray')
        plt.axhline(y=0, color='white', linestyle='--', alpha=0.5)
        
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['top'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.spines['right'].set_color('white')
        
        plt.tight_layout()
        plt.show()

    def refresh_data(self):
        transactions = get_all_transactions()
        
        balance = self.calculate_balance(transactions)
        self.balance_label.setText(f'Баланс: {balance:.2f} ₽')

        if balance >= 0:
            self.balance_label.setStyleSheet('color: #27ae60; margin-bottom: 10px;')
        else:
            self.balance_label.setStyleSheet('color: #c0392b; margin-bottom: 10px;')

        self.table.setRowCount(len(transactions))
        
        for row_idx, trans in enumerate(transactions):
            
            date_str = str(trans[4])[:10] if trans[4] else ''
            date_item = QTableWidgetItem(date_str)
            date_item.setFlags(Qt.ItemFlag.ItemIsEnabled)

            desc_item = QTableWidgetItem(trans[2] if trans[2] else '')
            desc_item.setFlags(Qt.ItemFlag.ItemIsEnabled)

            amount_val = trans[1]

            if trans[3] == 'expense':
                amount_str = f'{-amount_val:.2f}'
                color = QColor('#c0392b')
            
            else:
                amount_str = f'{amount_val:.2f}'
                color = QColor('#27ae60')

            amount_item = QTableWidgetItem(amount_str)
            amount_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            amount_item.setForeground(color)
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            id_item = QTableWidgetItem(str(trans[0]))
            id_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            id_item.setForeground(QColor('#95a5a6'))

            self.table.setItem(row_idx, 0, date_item)
            self.table.setItem(row_idx, 1, desc_item)
            self.table.setItem(row_idx, 2, amount_item)
            self.table.setItem(row_idx, 3, id_item)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Wallet()
    window.show()
    sys.exit(app.exec())