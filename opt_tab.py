import os
from PyQt6 import sip
from PyQt6.QtWidgets import (
    QLabel, QFrame, QWidget, QVBoxLayout, QGridLayout,
    QSizePolicy, QHBoxLayout, QCheckBox
)
from PyQt6.QtCore import Qt, QFileSystemWatcher
from functools import partial
from real_time_opt_update import RealTimeOptUpdate
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

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
        # Khi là Residuals, chèn chart vào
        if name == "Residuals":
            return self.create_residual_panel()
        # Khi là Flow fields, vẽ trường vật lý
        if name == "Flow fields":
            return self.create_flow_fields_panel()

    # 3) Chia layout theo số lựa chọn, tự động stretch đều
    n = len(sel)
    if n == 1:
        w = make_panel(sel[0])
        w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(w, 1)
        return

    elif n == 2:
        # Dùng HBox để chia đôi full chiều cao (thêm stretch để widget giãn đều)
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(0)
        for name in sel:
            w = make_panel(name)
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            hbox.addWidget(w, 1)   # <-- thêm stretch=1
        layout.addLayout(hbox, 1)
        return

    # Chỉ còn n == 3 ở đây
    grid = QGridLayout()
    # bật stretch đều cho 2 hàng 2 cột
    for i in range(2):
        grid.setRowStretch(i, 1)
        grid.setColumnStretch(i, 1)

    for idx, name in enumerate(sel):
        r, c = divmod(idx, 2)
        w = make_panel(name)
        w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        if name == "Residuals":
            # cho nó span 2 cột
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

# Module nhận biết sự thay đổi trong DESIGNS và folder_name để tiến hành cập nhật DSN_xxx mới vào chương trình
def on_designs_dir_changed(self, path: str):
    designs_path = os.path.join(self.folder_name, 'DESIGNS')
    # Khi thư mục DESIGNS mới xuất hiện, thêm watcher và cập nhật luôn
    if path == self.folder_name and os.path.isdir(designs_path): # Kiểm tra xem đã có thư mục con tên là DESIGNS hay chưa ? Nếu có thì lưu path của DESIGNS vào cho watcher.
        self.dsn_watcher.addPath(designs_path)
        self.update_comp_dsn_checkboxes()
        self.update_flow_airfoil_checkboxes()
    # Khi có bất kỳ DSN_xxx mới nào bên trong DESIGNS
    elif path == designs_path:
        self.update_comp_dsn_checkboxes() # Nếu đã có path của DESIGNS rồi thì chạy module update_comp_dsn_checkboxes (Update danh sách check box cho Comparison)
        self.update_flow_airfoil_checkboxes() # Nếu đã có path của DESIGNS rồi thì chạy module update_flow_airfoil_checkboxes (Update danh sách check box cho Airfoil)

# Update list DSN mới theo thời gian thực trong list lựa chọn của Comparison
def update_comp_dsn_checkboxes(self):
    """
    Quét <self.folder_name>/DESIGNS, thêm checkbox mới cho mỗi DSN_xxx hiện có,
    nhưng không xóa checkbox đã tồn tại.
    """
    designs_dir = os.path.join(self.folder_name, "DESIGNS")
    if not os.path.isdir(designs_dir):
        return # Nếu không tồn tại đường dẫn thư mục hợp lệ thì thoát khỏi hàm update_comp_dsn_checkboxes

    # Lấy và sắp xếp thư mục con DSN_xxx
    dsn_dirs = [
                d for d in os.listdir(designs_dir)
                if d.startswith("DSN_") and os.path.isdir(os.path.join(designs_dir, d))         # Nếu đúng là thư mục DSN_xxx thì nhận và lưu lại
                ]
    def idx(name):      # Nếu đọc được STT xxx thì nhận luôn, còn không thì nhận =-1
        try:
            return int(name.split('_',1)[1])
        except:
            return -1

    # Với mỗi thư mục mới thì thêm vào check box
    for dsn in sorted(dsn_dirs, key=idx):       # Duyệt qua tên trong danh sách đã sắp xếp.
        if dsn not in self.comp_checks:            # Nếu tên DSN chưa có thì thêm vào
            cb = QCheckBox(dsn)
            self.comp_scroll_layout.addWidget(cb)
            self.comp_checks[dsn] = cb
            cb.stateChanged.connect(self.update_comp_list)
            # Áp dụng filter tìm kiếm nếu có
            if hasattr(self, 'comp_search') and self.comp_search.text():
                cb.setVisible(self.comp_search.text().lower() in dsn.lower())

# Update list DSN mới theo thời gian thực trong list lựa chọn của cột Airfoil trong Flow fields
def update_flow_airfoil_checkboxes(self):
    """
    Quét folder …/DESIGNS, với mỗi DSN_xxx mới sẽ thêm một QCheckBox vào cột Airfoil.
    """
    designs_dir = os.path.join(self.folder_name, "DESIGNS")
    if not os.path.isdir(designs_dir):
        return

    # Lọc và sắp xếp thư mục con bắt đầu bằng DSN_
    dsn_dirs = [
        d for d in os.listdir(designs_dir)
        if d.startswith("DSN_") and os.path.isdir(os.path.join(designs_dir, d))
    ]
    def idx(name):
        try:
            return int(name.split('_',1)[1])
        except:
            return -1

    # Với mỗi DSN chưa có checkbox, tạo mới và nối signal
    for dsn in sorted(dsn_dirs, key=idx):
        if dsn not in self.flow_airfoil_checks:
            cb = QCheckBox(dsn)
            # flow_airfoil_scroll_layout là layout chứa các checkbox Airfoil
            self.flow_airfoil_scroll_layout.addWidget(cb)
            self.flow_airfoil_checks[dsn] = cb
            # partial(self._on_flow_airfoil_changed, dsn) để slot biết tên DSN
            cb.stateChanged.connect(partial(self._on_flow_airfoil_changed, dsn))
    
    # Sau khi thêm xong, đồng bộ trạng thái:
    if self.current_flow_airfoil:
        for name, cb in self.flow_airfoil_checks.items():
            if name not in self.current_flow_airfoil:
                cb.setEnabled(False)

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
    # Nếu panel Residuals đang bật, redraw nó (Sửa lại)
    if "Residuals" in getattr(self, "current_display_sett", []):
        self.update_display_area()

# Cập nhật list comparison
def update_comp_list(self, state):
    # Cập nhật danh sách comparison
    self.current_comp_sett = [
        name for name, cb in self.comp_checks.items()
        if cb.isChecked()
    ]
    # Nếu panel Airfoil Comparison đang hiển thị, refresh nó (Chưa hiểu)
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

def filter_flow_airfoil_checks(self, text: str):
    """
    Lọc các checkbox Airfoil trong Flow fields dựa trên chuỗi text nhập vào ô Find…
    """
    text_lower = text.lower()
    for name, cb in self.flow_airfoil_checks.items():
        # nếu tên Airfoil chứa chuỗi tìm, hiển thị; ngược lại ẩn
        cb.setVisible(text_lower in name.lower())

# Plot airfoil_comparison ====================================================================
def create_airfoil_comparison_panel(self) -> QWidget:
    """
    Tạo panel chứa đồ thị Airfoil Comparison.
    Dựa vào self.current_comp_sett (list các chuỗi user tick ở Comparison Settings).
    """
    # 1) Xác định folder gốc, chưa có thì hiện bảo chạy simulation đi đã
    folder = getattr(self, "folder_name", None)
    if not folder:
        placeholder = QWidget()
        lbl     = QLabel("Please run simulation")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout  = QVBoxLayout(placeholder)
        layout.addWidget(lbl)
        return placeholder

    # 2) Khởi tạo updater và gọi plot_airfoil
    updater   = RealTimeOptUpdate(folder)
    # Nếu user chưa chọn gì, vẽ baseline mặc định (Sửa lại)
    comp_list = self.current_comp_sett or [self.baseline_label]
    fig       = updater.plot_airfoil(comp_list)

    # 3) Embed vào canvas và container
    canvas = FigureCanvas(fig)
    canvas.draw()
    canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    # 4) Đóng gói canvas vào widget Qt
    container = QWidget()
    layout    = QVBoxLayout(container)
    layout.addWidget(canvas)
    return container

# Plot residual_panel ====================================================================
def create_residual_panel(self) -> QWidget:
    folder = getattr(self, "folder_name", None)
    if not folder:
        return QWidget()

    # 1) Chuẩn bị updater + metrics
    updater = RealTimeOptUpdate(folder)
    metrics = self.current_resid_sett or list(self.resid_checks.keys())

    # 2) Tạo container + layout giữ canvas
    container = QWidget()
    layout    = QVBoxLayout(container)

    # 3) Khởi flag chưa vẽ
    self._resid_initialized = False
    self._resid_canvas      = None

    # 4) Định nghĩa refresh closure với if/else
    def refresh(_path=None):
        # nếu đã vẽ rồi thì remove canvas cũ
        if self._resid_initialized and self._resid_canvas:
            old = self._resid_canvas
            layout.removeWidget(old)
            old.setParent(None)
            old.deleteLater()

        # tạo canvas mới từ figure mới
        fig       = updater.plot_residuals(metrics)
        canvas    = FigureCanvas(fig)
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # thêm vào layout
        layout.addWidget(canvas)

        # lưu lại để lần sau remove
        self._resid_canvas      = canvas
        self._resid_initialized = True

    # 5) Tạo watcher để gọi refresh mỗi khi folder thay đổi
    designs_path = os.path.join(folder, "DESIGNS")
    paths = [folder]
    if os.path.isdir(designs_path):
        paths.append(designs_path)

    watcher = QFileSystemWatcher(paths, container)
    watcher.directoryChanged.connect(refresh)

    # 6) Lưu reference để tránh GC
    self._resid_watcher = watcher

    # 7) Vẽ lần đầu
    refresh()

    return container

# Plot flow fields ====================================================================
def create_flow_fields_panel(self) -> QWidget:

    # 1) Kiểm tra folder simulation, chưa có thì hiện bảo chạy simulation đi đã
    folder = getattr(self, 'folder_name', None)
    if not folder or not os.path.isdir(folder):
        placeholder = QWidget()
        lbl         = QLabel("Please run simulation")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout      = QVBoxLayout(placeholder)
        layout.addWidget(lbl)
        return placeholder

    # 2) Kiểm tra user đã chọn Airfoil và Flow field chưa
    selections  = getattr(self, 'current_flow_airfoil', [])
    fields      = getattr(self, 'current_flow_fields', [])
    if not selections or not fields:
        placeholder = QWidget()
        lbl     = QLabel("Please choose 1 Airfoil and 1 Flow field")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout  = QVBoxLayout(placeholder)
        layout.addWidget(lbl)
        return placeholder
    
    # Kiểm tra flow.vtu của DSN_xxx đã tồn tại chưa
    #sel_air   = selections[0]
    #file_path = os.path.join(folder, "DESIGNS", sel_air, "DIRECT", "flow.vtu")
    #if not sel_air.startswith("NACA_") and not os.path.isfile(file_path):
    #    placeholder = QWidget()
    #    lbl = QLabel("Please choose other one. This one not done yet")
    #    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    #    layout = QVBoxLayout(placeholder)
    #    layout.addWidget(lbl)
    #    return placeholder

    # 3) Xác định đường dẫn .vtu
    updater     = RealTimeOptUpdate(folder)
    latest      = updater.lastest_dsn()
    sel_air     = selections[0]
    sel_field   = fields[0]

    if sel_air == "Latest Design":
        data_path = os.path.join(folder, "DESIGNS", latest, "DIRECT", "flow.vtu") if latest else os.path.join(folder, "flow.vtu") # Nếu Lastest có DSN_xxx thì lấy còn ko thì trả về đường dẫn của NACA
    elif sel_air.startswith("NACA_"):
        data_path = os.path.join(folder, "flow.vtu")
    else:
        data_path = os.path.join(folder, "DESIGNS", sel_air, "DIRECT", "flow.vtu")

    # 4) Thiết lập dim (Đơn vị)
    if sel_field    == "Pressure":      dim = "Pa"
    elif sel_field  == "Temperature":   dim = "K"
    elif sel_field  == "Velocity":      dim = "m/s"
    else:                               dim = ""  # streamlines không cần unit hiển thị

    # 5) Tạo panel và layout
    panel = QWidget()
    layout = QVBoxLayout(panel)

    # 6) Gọi vào hàm RealTimeOptUpdate
    vtk_widget = RealTimeOptUpdate.create_flow_field_visualizer(
        data            = data_path,
        field           = sel_field,
        flow_airfoil    = sel_air,
        dim             = dim,
        folder_airfoil  = folder,
        latest_dsn      = latest
    )
    vtk_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    layout.addWidget(vtk_widget, 1)

    return panel

def _on_flow_airfoil_changed(self, name: str, state: int):
    """
    Khi user chọn/bỏ chọn Airfoil:
    - Nếu chọn, disable hết airfoil khác và lưu vào self.current_flow_airfoil
    - Nếu bỏ chọn, enable lại tất cả và clear list
    """
    if state == Qt.CheckState.Checked.value:
        # disable tất cả airfoil khác
        for n, cb in self.flow_airfoil_checks.items():
            if n != name:
                cb.setEnabled(False)
        self.current_flow_airfoil = [name]
    else:
        # enable lại tất cả airfoil
        for cb in self.flow_airfoil_checks.values():
            cb.setEnabled(True)
        self.current_flow_airfoil = []
    # Cập nhật lại vùng hiển thị sau mỗi lần chọn/bỏ chọn
    self.update_display_area()

def _on_flow_field_changed(self, name: str, state: int):
    """
    Khi user chọn/bỏ chọn Flow field:
    - Nếu chọn, disable hết field khác và lưu vào self.current_flow_fields
    - Nếu bỏ chọn, enable lại tất cả và clear list
    """
    if state == Qt.CheckState.Checked.value:
        # disable tất cả field khác
        for n, cb in self.flow_field_checks.items():
            if n != name:
                cb.setEnabled(False)
        self.current_flow_fields = [name]
    else:
        # enable lại tất cả field
        for cb in self.flow_field_checks.values():
            cb.setEnabled(True)
        self.current_flow_fields = []
    # Cập nhật lại vùng hiển thị sau mỗi lần chọn/bỏ chọn
    self.update_display_area()

# Tab Optimize (end) =============================================================