import os
from PyQt6.QtWidgets import (
    QLabel, QFrame, QWidget, QVBoxLayout, QGridLayout,
    QSizePolicy, QCheckBox
)
from PyQt6.QtCore import Qt, QFileSystemWatcher
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from real_time_opt_update import RealTimeOptUpdate

# Tab Optimize ===================================================================
# Cập nhật list result cần hiển thị
def update_display_list(self, state):
    """
    Cập nhật self.current_display_sett thành list các mục đang được tick.
    state là giá trị mới của checkbox nhưng ta không cần dùng trực tiếp.
    """
    self.current_display_sett = [
        name 
        for name, cb_display in self.display_checks.items() 
        if cb_display.isChecked()
    ]
    # sau khi cập nhật list, vẽ lại display_area
    self.update_display_area()
    # ẩn/hiện các nút Settings
    self.update_setting_buttons_visibility()

# Chia ô tự động trong display_area từ current_display_sett

def update_display_area(self):
    """
    Xóa hết con của display_area rồi dựng layout mới
    dựa trên self.current_display_sett.
    """
    layout = self.display_area.layout()

    # --- clear_layout: đệ qui xóa widget & layout con ---
    def clear_layout(lay):
        for i in reversed(range(lay.count())):
            item = lay.takeAt(i)
            if item.widget():
                item.widget().setParent(None)
            elif item.layout():
                clear_layout(item.layout())
        # lúc này lay.count() == 0

    # 1) Dọn sạch cũ
    clear_layout(layout)

    sel = self.current_display_sett

    # 2) Nếu không chọn thì hiện thông báo; nếu >3 thì bỏ
    if len(sel) == 0:
        # hiển thị label ở giữa display_area
        msg = QLabel("Please select options in Display Result above")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg)
        return
    if len(sel) > 3:
        return

    # helper dựng placeholder panel
    def make_panel(name):
        # Khi là Airfoil Comparison, chèn chart vào
        if name == "Airfoil Comparison":
            return self.create_airfoil_comparison_panel()
        if name == "Residuals":
            return self.create_residual_panel()

        # Mặc định vẫn giữ placeholder cho các panel khác
        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        lbl = QLabel(name)
        panel.setLayout(QVBoxLayout())
        panel.layout().addWidget(lbl)
        return panel


    # 3) Chia layout theo số lựa chọn, tự động stretch đều
    n = len(sel)
    if n == 1:
        w = make_panel(sel[0])
        w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(w, 1)
    else:
        # với 2 và 3 panel, ta dùng Grid 2×2 để chia đều
        grid = QGridLayout()
        # bật stretch đều cho hàng và cột
        for i in range(2):
            grid.setRowStretch(i, 1)
            grid.setColumnStretch(i, 1)

        for idx, name in enumerate(sel):
            r, c = divmod(idx, 2)
            w = make_panel(name)
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            # với 3 panel, cho Residuals span cả hai cột
            if n == 3 and name == "Residuals":
                grid.addWidget(w, 1, 0, 1, 2)
            else:
                grid.addWidget(w, r, c)

        layout.addLayout(grid, 1)

# Ẩn/hiện các nút settings khi un-tick/tick chọn trong Display Result
def update_setting_buttons_visibility(self):
    """
    Hiện/ẩn các nút Settings dựa trên self.current_display_sett.
    """
    # Comparison Settings ↔ Airfoil Comparison
    if "Airfoil Comparison" in self.current_display_sett:
        self.comp_settings_btn.show()
    else:
        self.comp_settings_btn.hide()

    # Flow fields Settings ↔ Flow fields
    if "Flow fields" in self.current_display_sett:
        self.flow_settings_btn.show()
    else:
        self.flow_settings_btn.hide()

    # Residual Settings ↔ Residuals
    if "Residuals" in self.current_display_sett:
        self.resid_settings_btn.show()
    else:
        self.resid_settings_btn.hide()

# Bắt sự thay đổi trong folder DESIGNS
def on_designs_dir_changed(self, path: str):
    designs_path = os.path.join(self.folder_name, 'DESIGNS')
    if path == self.folder_name and os.path.isdir(designs_path):
        self.dsn_watcher.addPath(designs_path)
    if path == designs_path:
        # chỉ update checkbox list cho Comparison tab
        self.update_comp_dsn_checkboxes()

# Update list DSN mới theo thời gian thực trong list lựa chọn của người dùng
def update_comp_dsn_checkboxes(self):
    """
    Quét <self.folder_name>/DESIGNS, thêm checkbox mới cho mỗi DSN_xxx hiện có,
    nhưng không xóa checkbox đã tồn tại.
    """
    designs_dir = os.path.join(self.folder_name, "DESIGNS")
    if not os.path.isdir(designs_dir):
        return

    # Lấy và sắp xếp thư mục con DSN_xxx
    dsn_dirs = [
        d for d in os.listdir(designs_dir)
        if d.startswith("DSN_") and os.path.isdir(os.path.join(designs_dir, d))
    ]
    def idx(name):
        try:
            return int(name.split('_',1)[1])
        except:
            return -1

    for dsn in sorted(dsn_dirs, key=idx):
        if dsn not in self.comp_checks:
            cb = QCheckBox(dsn)
            self.comp_scroll_layout.addWidget(cb)
            self.comp_checks[dsn] = cb
            cb.stateChanged.connect(self.update_comp_list)
            # Áp dụng filter tìm kiếm nếu có
            if hasattr(self, 'comp_search') and self.comp_search.text():
                cb.setVisible(self.comp_search.text().lower() in dsn.lower())

# Cập nhật list residuals
def update_resid_list(self, state):
    """
    Cập nhật self.current_resid_sett thành list các mục residual đang được tick
    và refresh display_area nếu Residuals đang hiển thị.
    """
    self.current_resid_sett = [
        name 
        for name, cb_resid in self.resid_checks.items() 
        if cb_resid.isChecked()
    ]
    # Nếu panel Residuals đang bật, redraw nó
    if "Residuals" in getattr(self, "current_display_sett", []):
        self.update_display_area()

# Cập nhật list comparison
def update_comp_list(self, state):
    # Cập nhật danh sách comparison
    self.current_comp_sett = [
        name for name, cb in self.comp_checks.items()
        if cb.isChecked()
    ]
    # Nếu panel Airfoil Comparison đang hiển thị, refresh nó
    if "Airfoil Comparison" in getattr(self, "current_display_sett", []):
        self.update_display_area()

# Ô tìm kiếm airfoil cho comparison
def filter_comp_checks(self, text_comp):
    # Chuyển input thành lowercase
    text_lower = text_comp.lower()
    # Duyệt qua tất cả checkbox
    for name, cb_comp in self.comp_checks.items():
        # Nếu tên chứa chuỗi tìm, hiển thị; ngược lại ẩn
        cb_comp.setVisible(text_lower in name.lower())

# Cập nhật list airfoil trong flow fields
def _on_flow_airfoil_changed(self, name, state):
    """
    name: chuỗi key tương ứng của checkbox,
    state: Qt.Checked (2) hoặc Qt.Unchecked (0)
    """
    if state == Qt.CheckState.Checked.value:
        # disable các cb khác
        for n, cb in self.flow_airfoil_checks.items():
            if n != name:
                cb.setEnabled(False)
        self.current_flow_airfoil = [name]
    else:
        # re-enable tất cả khi bỏ chọn
        for cb in self.flow_airfoil_checks.values():
            cb.setEnabled(True)
        self.current_flow_airfoil = []

# Cập nhật list flow field trong flow fields
def _on_flow_field_changed(self, name, state):
    if state == Qt.CheckState.Checked.value:
        for n, cb in self.flow_field_checks.items():
            if n != name:
                cb.setEnabled(False)
        self.current_flow_fields = [name]
    else:
        for cb in self.flow_field_checks.values():
            cb.setEnabled(True)
        self.current_flow_fields = []

# Plot airfoil_comparison
def create_airfoil_comparison_panel(self) -> QWidget:
    """
    Tạo panel chứa đồ thị Airfoil Comparison.
    Dựa vào self.current_comp_sett (list các chuỗi user tick ở Comparison Settings).
    """
    # 1) Xác định folder gốc: ưu tiên attribute đã set lúc optimize
    folder = getattr(self, "folder_name", None)
    if not folder:
        code = ''.join(filter(str.isdigit, self.type.currentText()))
        folder = f"NACA_{code}"

    # 2) Khởi tạo updater và gọi plot_airfoil
    updater   = RealTimeOptUpdate(folder)
    # Nếu user chưa chọn gì, vẽ baseline mặc định
    comp_list = self.current_comp_sett or [self.baseline_label]
    fig       = updater.plot_airfoil(comp_list)

    # 3) Embed vào canvas và container
    canvas = FigureCanvas(fig)
    canvas.draw()
    canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    container = QWidget()
    layout    = QVBoxLayout(container)
    layout.addWidget(canvas)
    return container

# Plot residual_panel

def create_residual_panel(self) -> QWidget:
    # 1) Xác định folder root (dùng folder_name do run_optimization gán)
    folder = getattr(self, "folder_name", None)
    if not folder:
        return QWidget()

    # 2) Khởi RealTimeOptUpdate và vẽ lần đầu
    updater = RealTimeOptUpdate(folder)
    # lấy metrics user đã tick hoặc dùng mặc định
    metrics = self.current_resid_sett or list(self.resid_checks.keys())
    fig = updater.plot_residuals(metrics)
    canvas = FigureCanvas(fig)
    canvas.draw()
    canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    # 3) Tạo watcher chỉ để theo dõi folder DESIGNS
    designs_path = os.path.join(folder, 'DESIGNS')
    # nếu DESIGNS chưa tồn tại, tạo watcher chờ nó xuất hiện
    paths = [folder]
    if os.path.isdir(designs_path):
        paths.append(designs_path)
    self.residual_watcher = QFileSystemWatcher(paths)
    # mỗi khi DESIGNS hay folder gốc thay đổi, redraw chart
    self.residual_watcher.directoryChanged.connect(
        lambda _path: self._on_residuals_dir_changed(canvas, updater, metrics)
    )

    # 4) Đóng gói canvas vào widget Qt
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.addWidget(canvas)
    return container

def _on_residuals_dir_changed(self, canvas: FigureCanvas, 
                                updater: RealTimeOptUpdate,
                                metrics: list):
    """
    Slot được gọi khi DESIGNS thay đổi; chỉ redraw lại phần plot residuals.
    """
    # 1) Lấy figure mới
    new_fig = updater.plot_residuals(metrics)
    # 2) Thay figure cũ của canvas
    canvas.figure = new_fig
    # 3) Vẽ lại lên màn hình
    canvas.draw()

# Tab Optimize (end) =============================================================