from PyQt6 import QtWidgets
from PyQt6.QtCore import QFileSystemWatcher
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

import pandas as pd
import os

class MatplotlibWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Tạo Figure và Canvas
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        # Toolbar tương tác
        self.toolbar = NavigationToolbar(self.canvas, self)

        #Marker cho điểm
        self.cursor_dot, = self.ax.plot([], [], 'o', color='green', markersize=6, label="Cursor")  # nút màu xanh

        # Layout tổng
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)

        # Dữ liệu ban đầu
        self.iterations = []
        self.cl_values = []
        self.cd_values = []

        self.cl_line, = self.ax.plot([], [], label="CL", color="blue")
        self.cd_line, = self.ax.plot([], [], label="CD", color="red")

        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(0, 1.5)
        self.ax.set_xlabel("Iterations")
        self.ax.set_ylabel("Coefficient Values")
        self.ax.set_title("Real-time CL and CD Update")
        self.ax.legend()
        # Format trục X và Y để chỉ hiển thị số nguyên
        self.ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x)}"))


        # Theo dõi file
        self.file_watcher = QFileSystemWatcher()
        self.file_watcher.fileChanged.connect(self.update_plot)

        self.canvas.mpl_connect("motion_notify_event", self.mouse_move_event)
        self.coord_label = QtWidgets.QLabel("Tọa độ:")
        self.layout.addWidget(self.coord_label)

    def path(self, history_file_path):
        self.history_file = history_file_path
        if os.path.exists(self.history_file):
            self.file_watcher.addPath(self.history_file)

    def update_plot(self):
        iterations, cl_values, cd_values = self.read_history()

        if iterations:
            self.cl_line.set_data(iterations, cl_values)
            self.cd_line.set_data(iterations, cd_values)

            self.ax.set_xlim(0, max(iterations) + 10)
            self.ax.set_ylim(0, max(max(cl_values), max(cd_values)) + 0.5)

            self.canvas.draw()

            if not self.file_watcher.files():
                self.file_watcher.addPath(self.history_file)

    def read_history(self):
        if os.path.exists(self.history_file):
            try:
                data = pd.read_csv(self.history_file)
                data.columns = data.columns.str.replace('"', '', regex=True).str.strip()
                data = data[pd.to_numeric(data['Inner_Iter'], errors='coerce').notna()]
                data['Inner_Iter'] = data['Inner_Iter'].astype(int)
                data = data[data['Inner_Iter'] > 0]
                return data['Inner_Iter'].tolist(), data['CL'].tolist(), data['CD'].tolist()
            except Exception as e:
                print(f"Lỗi khi đọc file history: {e}")
            return [], [], []
        else:
            print(f"File {self.history_file} không tồn tại!")
            return [], [], []
        
    def mouse_move_event(self, event):
        """Hiển thị tọa độ dữ liệu gần nhất với con trỏ chuột và vẽ marker"""
        if event.inaxes and self.iterations:
            x = event.xdata

            # Tìm index gần nhất
            closest_index = min(range(len(self.iterations)), key=lambda i: abs(self.iterations[i] - x))

            closest_iter = self.iterations[closest_index]
            cl = self.cl_values[closest_index]
            cd = self.cd_values[closest_index]

            self.coord_label.setText(
                f"Tại Iter = {closest_iter}:  CL = {cl:.4f}, CD = {cd:.4f}"
            )

            # Vẽ lại marker tại vị trí gần nhất
            self.cursor_dot.set_data([closest_iter], [cl])  # Hoặc dùng [cd] nếu muốn marker CD
            self.canvas.draw()
        else:
            self.coord_label.setText("Tọa độ:")
            self.cursor_dot.set_data([], [])  # Ẩn marker
            self.canvas.draw()



