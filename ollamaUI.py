import sys
import json
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QMessageBox, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont


class OllamaChatWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ollama 对话交互 by：1ight")
        self.resize(1900, 1240)
        self.init_ui()

    def init_ui(self):
        # Apple-style color palette (简洁风格)
        self.setStyleSheet("""
            QWidget {
                background-color: #F9F9F9;
            }
            QTextEdit {
                background: #FFFFFF;
                border-radius: 18px;
                border: 1px solid #E5E5EA;
                padding: 18px;
                color: #222;
                font-size: 22px;
            }
            QLineEdit {
                background: transparent;
                border: none;
                font-size: 22px;
                color: #222;
            }
            QPushButton {
                background-color: #007AFF;
                border-radius: 16px;
                border: none;
                font-size: 22px;
                color: #FFFFFF;
                font-weight: bold;
                min-width: 80px;
                min-height: 44px;
                padding: 6px 16px;
            }
            QPushButton:pressed {
                background-color: #005BBB;
            }
            QLabel#TitleLabel {
                color: #111;
                font-size: 38px;
                font-weight: 700;
                letter-spacing: 1px;
            }
            QLabel#ChatLabel {
                color: #888;
                font-size: 22px;
                font-weight: 600;
                margin-bottom: 8px;
            }
            QLabel#StatusLabel {
                color: #888;
                font-size: 20px;
                font-style: italic;
                margin-top: 8px;
                margin-bottom: 0px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(12)

        # Title
        title_label = QLabel("Ollama 对话交互")
        title_label.setObjectName("TitleLabel")
        title_label.setFont(QFont("San Francisco", 36, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Chat label
        chat_label = QLabel("对话内容：")
        chat_label.setObjectName("ChatLabel")
        chat_label.setFont(QFont("San Francisco", 22, QFont.Bold))
        layout.addWidget(chat_label)

        # Chat area
        self.chat_edit = QTextEdit()
        self.chat_edit.setReadOnly(True)
        self.chat_edit.setFont(QFont("San Francisco", 22))
        self.chat_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.chat_edit.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.chat_edit, stretch=8)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignLeft)
        self.status_label.setFont(QFont("San Francisco", 20, QFont.StyleItalic))
        layout.addWidget(self.status_label)

        # === 输入条整体容器 ===
        input_bar = QFrame()
        input_bar.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #E5E5EA;
                border-radius: 22px;
            }
        """)
        input_bar_layout = QHBoxLayout(input_bar)
        input_bar_layout.setContentsMargins(12, 6, 12, 6)  # 内边距
        input_bar_layout.setSpacing(8)

        # 输入框
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("请输入您的问题...")
        self.input_edit.setFont(QFont("San Francisco", 22))
        self.input_edit.setFixedHeight(44)
        self.input_edit.returnPressed.connect(self.on_send)
        input_bar_layout.addWidget(self.input_edit, alignment=Qt.AlignVCenter)

        # 发送按钮
        self.send_btn = QPushButton("发送")
        self.send_btn.setFont(QFont("San Francisco", 22, QFont.Bold))
        self.send_btn.setFixedSize(88, 44)
        self.send_btn.clicked.connect(self.on_send)
        input_bar_layout.addWidget(self.send_btn, alignment=Qt.AlignVCenter)

        layout.addWidget(input_bar)
        self.setLayout(layout)

    def on_send(self):
        user_input = self.input_edit.text().strip()
        if not user_input:
            QMessageBox.warning(self, "提示", "请输入内容后再发送。")
            return

        self.append_message("用户", user_input)
        self.input_edit.clear()
        self.input_edit.setDisabled(True)
        self.send_btn.setDisabled(True)
        self.status_label.setText("Ollama 正在思考中...")

        QApplication.processEvents()  # 刷新UI

        QTimer.singleShot(100, lambda: self._do_query(user_input))

    def _do_query(self, user_input):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            response = self.query_ollama(user_input)
            if response is not None:
                formatted = self.format_response(response)
                self.append_message("Ollama", formatted)
                self.status_label.setText("Ollama 已思考完成")
            else:
                self.append_message("Ollama", "未能获取有效回复。")
                self.status_label.setText("Ollama 已思考完成")
        except Exception as e:
            self.append_message("Ollama", f"请求出错: {e}")
            self.status_label.setText("Ollama 已思考完成")
        finally:
            QApplication.restoreOverrideCursor()
            self.input_edit.setDisabled(False)
            self.send_btn.setDisabled(False)
            self.input_edit.setFocus()

    def append_message(self, sender, message):
        self.chat_edit.moveCursor(self.chat_edit.textCursor().End)
        if sender == "用户":
            html = f"""
            <div style="display:flex; justify-content:flex-start; margin:8px 0; width:100%;">
                <div style="background:transparent; border-radius:12px; padding:10px 16px; max-width:70%; text-align:left;">
                    <span style="color:#222; font-size:22px;"><b>You：</b>{message}</span>
                </div>
            </div>
            """
        elif sender == "Ollama":
            html = f"""
            <div style="display:flex; justify-content:flex-start; margin:8px 0; width:100%;">
                <div style="background:transparent; border-radius:12px; padding:10px 16px; max-width:70%; text-align:left;">
                    <span style="color:#222; font-size:22px;"><b>Ollama：</b>{message}</span>
                </div>
            </div>
            """
        else:
            html = f"""
            <div style="display:flex; justify-content:flex-start; margin:8px 0; width:100%;">
                <div style="background:transparent; border-radius:12px; padding:10px 16px; max-width:70%; text-align:left;">
                    <span style="color:#222; font-size:22px;">{message}</span>
                </div>
            </div>
            """
        self.chat_edit.setAlignment(Qt.AlignLeft)
        self.chat_edit.insertHtml(html)
        self.chat_edit.insertHtml("<br>")
        self.chat_edit.verticalScrollBar().setValue(self.chat_edit.verticalScrollBar().maximum())

    def query_ollama(self, prompt):
        url = "http://0.0.0.0:11434/api/generate"
        payload = {
            "model": "qwen3:30b",
            "prompt": prompt,
            "stream": False
        }
        headers = {"Content-Type": "application/json"}
        resp = requests.post(url, data=json.dumps(payload), headers=headers, timeout=None)
        if resp.status_code == 200:
            return resp.json()
        else:
            return None

    def format_response(self, resp_json):
        response_text = resp_json.get("response", "")
        import re
        response_text = re.sub(r"<think>.*?</think>\s*", "", response_text, flags=re.DOTALL)
        return response_text.replace('\n', '<br>')


def main():
    app = QApplication(sys.argv)
    win = OllamaChatWidget()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
