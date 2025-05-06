import os
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
        ax.legend()
        plt.close(fig)
        return fig

    def plot_residuals(self, metrics_list: list) -> plt.Figure:
        """
        Vẽ summary residuals cho tất cả DSN_xxx:
        - Trục hoành: các DSN_xxx
        - Trục tung: giá trị cuối cùng của mỗi metric trong history_direct.csv
        metrics_list ví dụ: ['CL','CD','MOMENT_Z']
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
        ax.set_title('Residuals Summary')
        ax.legend()
        plt.xticks(rotation=45)
        # --- X-Axis: chỉ mở rộng khi len(labels) lớn hơn trước ---
        # self._max_dsn_count: thuộc tính bạn đã thêm trong __init__
        self._max_dsn_count = max(self._max_dsn_count, len(labels))
        ax.set_xlim(-0.5, self._max_dsn_count - 0.5)

        # --- Y-Axis: chỉ mở rộng nếu giá trị vượt ngưỡng cũ ---
        all_vals = [v for vals in data.values() for v in vals if v is not None]
        if all_vals:
            ymin_now, ymax_now = min(all_vals), max(all_vals)
            # nâng cấp global_min / global_max nếu cần
            if self._global_min is None or ymin_now < self._global_min:
                self._global_min = ymin_now
            if self._global_max is None or ymax_now > self._global_max:
                self._global_max = ymax_now

            diff = self._global_max - self._global_min
            margin = diff * 0.1 if diff else abs(self._global_max) * 0.1
            ax.set_ylim(self._global_min - margin,
                        self._global_max + margin)

        plt.tight_layout()
        plt.close(fig)
        return fig