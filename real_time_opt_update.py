import os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from pyvistaqt import QtInteractor
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
import pyvista as pv
import pandas as pd
import matplotlib.pyplot as plt

class RealTimeOptUpdate:
    """
    Quản lý các đường dẫn và vẽ đồ thị real-time cho quá trình tối ưu hoá airfoil.
    folder_airfoil: đường dẫn đến thư mục chứa kết quả mô phỏng airfoil gốc (ví dụ '.../NACA_0012')
    dsn_num: tên của thiết kế cụ thể (ví dụ 'DSN_001'), mặc định có thể None
    """
    def __init__(self, folder_airfoil: str, dsn_num: str = None):
        self.folder_airfoil = folder_airfoil
        self.dsn_num = dsn_num
        # --- thêm 2 thuộc tính để ghi nhớ limits ---
        self._max_dsn_count = 0
        self._global_min    = None
        self._global_max    = None
        # Nếu đã biết dsn_num, xác định thư mục DIRECT tương ứng
        if dsn_num:
            self.dsn_dir = os.path.join(self.folder_airfoil, 'DESIGNS', dsn_num, 'DIRECT')
        else:
            self.dsn_dir = None

    def lastest_dsn(self):
        """
        Quét thư mục DESIGNS để tìm DSN mới nhất (theo số thứ tự) và cập nhật self.lastest_dsn.
        Trả về tên DSN mới nhất hoặc None nếu không tìm thấy.
        """
        designs_dir = os.path.join(self.folder_airfoil, 'DESIGNS')
        try:
            items = os.listdir(designs_dir)
        except FileNotFoundError:
            self.lastest_dsn = None
            return None
        # Lọc thư mục theo tiền tố DSN_
        dsn_dirs = [d for d in items if d.startswith('DSN_') and os.path.isdir(os.path.join(designs_dir, d))]
        if not dsn_dirs:
            self.lastest_dsn = None
            return None
        # Hàm lấy số thứ tự
        def get_num(name):
            try:
                return int(name.split('_',1)[1])
            except:
                return -1
        latest = max(dsn_dirs, key=get_num)
        self.lastest_dsn = latest
        return latest

    def get_paths(self):
        """
        Trả về dict chứa đường dẫn cơ bản:
        - 'surface': baseline surface_flow.csv
        - 'field': baseline flow.vtu
        - 'history': None (baseline không dùng history)
        - 'design_surface', 'design_history', 'design_field' nếu self.dsn_dir đã thiết lập
        """
        paths = {
                    'surface': os.path.join(self.folder_airfoil, 'surface_flow.csv'),
                    'field':   os.path.join(self.folder_airfoil, 'flow.vtu'),
                    'history': None
                }
        if self.dsn_dir:
            paths.update({
                            'design_surface': os.path.join(self.dsn_dir, 'surface_flow.csv'),
                            'design_history': os.path.join(self.dsn_dir, 'history_direct.csv'),
                            'design_field':   os.path.join(self.dsn_dir, 'flow.vtu')
                        })
        return paths

    def plot_airfoil(self, comp_list: list) -> plt.Figure:
        """
        Vẽ so sánh airfoil.
        comp_list chứa các mục: 'NACA_xxxx', 'Latest Design', 'DSN_xxx'.
        """
        fig, ax = plt.subplots()
        fig, ax = plt.subplots(figsize=(6, 10))  # rộng 6 inch, cao 10 inch
        for item in comp_list:
            if item.startswith('NACA_'):
                path = os.path.join(self.folder_airfoil, 'surface_flow.csv')
                style = '-'
            elif item == 'Latest Design':
                latest = self.lastest_dsn()
                if not latest:
                    continue
                path = os.path.join(self.folder_airfoil, 'DESIGNS', latest, 'DIRECT', 'surface_flow.csv')
                style = '--'
            elif item.startswith('DSN_'):
                path = os.path.join(self.folder_airfoil, 'DESIGNS', item, 'DIRECT', 'surface_flow.csv')
                style = '--'
            else:
                continue
            if not os.path.isfile(path):
                continue
            df = pd.read_csv(path)
            ax.plot(df['x'], df['y'], style, label=item)
        ax.set_aspect('equal', 'box')
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_title('Airfoil Comparison')
        ax.set_aspect('auto')
        ax.legend()
        ax.set_ylim(-0.2, 0.3)
        ax.legend(loc='upper right')
        plt.close(fig)
        return fig

    def plot_residuals(self, metrics_list: list) -> plt.Figure:
        """
        Vẽ residuals cho tất cả DSN_xxx:
        - Trục hoành: các DSN_xxx
        - Trục tung: giá trị cuối cùng của mỗi metric trong history_direct.csv
        """
        # 1) Tìm tất cả DSN_xxx
        designs_dir = os.path.join(self.folder_airfoil, 'DESIGNS')
        try:
            all_dirs = os.listdir(designs_dir)
        except FileNotFoundError:
            dsns = []
        else:
            dsns = [d for d in all_dirs if d.startswith('DSN_') and os.path.isdir(os.path.join(designs_dir, d))]
        # Sắp xếp theo số thứ tự
        def get_num(name):
            try: return int(name.split('_',1)[1])
            except: return -1
        dsns = sorted(dsns, key=get_num)

        # 2) Thu thập dữ liệu dòng cuối
        labels = []
        data = {m: [] for m in metrics_list}
        for dsn in dsns:
            hist_path = os.path.join(self.folder_airfoil, 'DESIGNS', dsn, 'DIRECT', 'history_direct.csv')
            if not os.path.isfile(hist_path):
                continue
            df = pd.read_csv(hist_path)
            # chuẩn hóa header, loại dấu "
            df.columns = [c.strip().strip('"') for c in df.columns]
            # nếu chưa có dòng nào trong history, bỏ qua
            if df.empty:
                continue
            last = df.iloc[-1]
            labels.append(dsn)
            for m in metrics_list:
                data[m].append(last.get(m, None))

        # 3) Vẽ
        fig, ax = plt.subplots()
        for m, vals in data.items():
            ax.plot(labels, vals, marker='o', label=m)
        ax.set_xlabel('Design Iteration')
        ax.set_ylabel('Metric Value')
        ax.set_title('Residuals')
        ax.legend()
        plt.xticks(rotation=45)
        # --- X-Axis: chỉ mở rộng khi len(labels) lớn hơn trước ---
        # self._max_dsn_count: thuộc tính bạn đã thêm trong __init__
        self._max_dsn_count = max(self._max_dsn_count, len(labels))
        ax.set_xlim(-0.5, self._max_dsn_count - 0.5)

        plt.tight_layout()
        plt.close(fig)
        return fig

    def create_flow_field_visualizer(data, field, flow_airfoil, dim, folder_airfoil, latest_dsn):

        # Set up the layout for the visualizer
        panel           = QWidget()  
        panel_layout    = QVBoxLayout(panel)
        panel_plot      = QtInteractor(panel)
        panel_layout.addWidget(panel_plot.interactor)
        panel_plot.set_background('white')
        result          = pv.read(data)

        # 1) Latest design
        if flow_airfoil == "Latest Design":
            panel_plot.clear()
            panel_plot.add_mesh(result, scalars=result[field], 
                                scalar_bar_args={'title': f"{field} ({dim})" , 'vertical': False, 'position_x': 0.25, 'position_y': 0.02, 'width': 0.5, 'height': 0.05}, 
                                cmap='jet', show_scalar_bar=True)
            panel_plot.add_text(latest_dsn, font_size=14, position='upper_edge')
            panel_plot.screenshot(rf"{folder_airfoil}\DESIGNS\{latest_dsn}\{latest_dsn}_{field}.png",window_size=[1080, 1080])

        # 2) NACA_xxxx (thư mục gốc)
        elif flow_airfoil.startswith("NACA_"):
            panel_plot.clear()
            panel_plot.add_mesh(result, scalars=result[field], 
                                scalar_bar_args={'title': f"{field} ({dim})" , 'vertical': False, 'position_x': 0.25, 'position_y': 0.02, 'width': 0.5, 'height': 0.05}, 
                                cmap='jet', show_scalar_bar=True)
            panel_plot.add_text(flow_airfoil, font_size=14, position='upper_edge')
            panel_plot.screenshot(rf"{folder_airfoil}\{flow_airfoil}_{field}.png",window_size=[1080, 1080])

        # 3) DSN_xxx (thiết kế con)
        elif flow_airfoil.startswith("DSN_"):
            panel_plot.clear()
            panel_plot.add_mesh(result, scalars=result[field], 
                                scalar_bar_args={'title': f"{field} ({dim})" , 'vertical': False, 'position_x': 0.25, 'position_y': 0.02, 'width': 0.5, 'height': 0.05}, 
                                cmap='jet', show_scalar_bar=True)
            panel_plot.add_text(flow_airfoil, font_size=14, position='upper_edge')
            panel_plot.screenshot(rf"{folder_airfoil}\DESIGNS\{flow_airfoil}\{flow_airfoil}_{field}.png",window_size=[1080, 1080])

        panel_plot.view_xy()
        panel_plot.camera.focal_point = (0.5, 0, 0) 
        panel_plot.camera.zoom(15)

        return panel