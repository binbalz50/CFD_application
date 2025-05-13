import os                                                           # dùng để build path
from PyQt6 import QtWidgets                                         # sử dụng QMessageBox, QProgressBar, …
from PyQt6.QtCore import QFileSystemWatcher                         # watcher folder DESIGNS
from mesh import MeshGenerator                                       # lấy code NACA và đường dẫn mesh
from init_opt_conditions import OptInit                              # class khởi tạo luồng optimize
# Box optimize ===========================================================

# Ẩn/Hiện box chọn tham số cố định
def toggle_constraint_list(self, text):
    if text == "Select value":
        self.opt_const_list.show()
    else:
        self.opt_const_list.hide()
#
# Thực thi tiến trình tối ưu sau khi nhấn nút "OPTIMIZE"
def run_optimization(self):
    #Khởi động quá trình tối ưu hóa:
    #0) Kiểm tra dv_number trước khi bắt đầu
    #1) Thiết lập đường dẫn
    #2) Thu thập input từ GUI
    #3) Khởi tạo và cấu hình luồng OptInit
    #4) Kết nối signal và bắt đầu thread
    #
    #0) Kiểm tra dv_number trước khi bắt đầu
    dv_number_str = self.dvnumber.text().strip()
    try:
        dv_number = int(dv_number_str)
    except ValueError:
        QtWidgets.QMessageBox.warning(
            self.optimize,                      # parent widget
            "Invalid DV Number",                # title
            "Please enter a valid integer for DV Number.\n"
            "E.g., 4, 6, 8, 10, …"              # ví dụ
        )
        return

    if dv_number < 2 or dv_number % 2 != 0:
        QtWidgets.QMessageBox.warning(
            self.optimize,
            "Invalid DV Number",
            "Please choose an even number (>= 2) for DV Number.\n"
            "E.g., 4, 6, 8, 10, …"
        )
        return
    # 1) Xác định paths dựa trên NACA <code> và file mesh đã sinh
    code = MeshGenerator.naca_code(
                        group=self.type_of_naca.currentText(),
                        type=self.type.currentText()
                    )
    mesh_path   = os.path.join(f'NACA_{code}', f"mesh_airfoil_{code}.su2")
    folder_name = f'NACA_{code}'

    # Tab optimize =====================================================
    # Gán thuộc tính để dùng chung giữa config optimize và tab optimize
    self.folder_name = folder_name

    # Khởi watcher để giám sát thư mục DESIGNS và folder_name
    designs_path = os.path.join(self.folder_name, 'DESIGNS')
    self.dsn_watcher = QFileSystemWatcher(self.centralwidget)
    # Luôn watch folder_name để phát hiện khi DESIGNS mới sinh
    self.dsn_watcher.addPath(self.folder_name)
    # Nếu DESIGNS đã tồn tại (ví dụ optimize chạy lần thứ hai), watch thêm
    if os.path.isdir(designs_path):
        self.dsn_watcher.addPath(designs_path)
    # Kết nối sự kiện cho cả hai path
    self.dsn_watcher.directoryChanged.connect(self.on_designs_dir_changed)
    # Tab optimize (end) ================================================

    # 2) Thu thập tham số tối ưu từ GUI
    dv_kind    = self.dvkind.currentText()                  # HICKS_HENNE / FFD_SETTING
    dv_number  = int(self.dvnumber.text() or "0")           # Số lượng DV (even)
    opt_object  = self.opt_object.currentText()              # LIFT / DRAG
    opt_const_type = self.opt_const_type.currentText()          # NONE / Select value
    if opt_const_type == "Select value":
        opt_const_list  = [item.text() for item in self.opt_const_list.selectedItems()] # Đổi qua biến opt_const_list để đổi kiểu dữ liệu list
    else:
        opt_const_list  = []                                    # không ràng buộc

    # 3) Khởi tạo luồng tối ưu (OptInit trong init_opt_conditions.py)
    from init_opt_conditions import OptInit
    self.opt_thread = OptInit(
        mesh_path       = mesh_path,
        folder_name     = folder_name,
        mach            = self.mach.text(),
        aoa             = self.aoa.text(),
        temperature     = self.temp.text(),
        pressure        = self.pressure.text(),
        dv_kind         = dv_kind,
        dv_number       = dv_number,
        opt_object      = opt_object,
        opt_const_type  = opt_const_type,
        opt_const_list  = opt_const_list,
        # Để ở đây để khi nào cần thêm vào GUI cho chỉnh sửa / thiết đặt thì sài
        solver          = "EULER",
        opt_iterations  = 100,
        opt_accuracy    = 1e-10,
        opt_bound_upper = 0.1,
        opt_bound_lower = -0.1
    )

    # 4) Kết nối các signal để UI phản hồi
    self.opt_thread.inform.connect(self.inform)  # hiện popup Success!
    self.opt_thread.finished.connect(lambda:
        self.statusbar.showMessage("Optimization complete"))
    # Hiển thị progress bar nếu muốn
    self.progress_bar()

    # 5) Bắt đầu thread
    self.opt_thread.start()

# Box optimize (end) ========================================================  