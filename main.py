from PyQt6 import QtCore, QtWidgets
from PyQt6.QtGui import QPalette, QBrush, QPixmap
from PyQt6.QtCore import Qt
# Tab Optimize
from functools import partial
from PyQt6.QtWidgets import QScrollArea, QLineEdit, QToolButton, QMenu, QWidgetAction, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QFrame, QGridLayout, QSizePolicy
# Tab Optimize (end)
from mesh import MeshGenerator
from visual import *
from init_conditions import Init
from realTimeAeroCoeffsUpdate import MatplotlibWidget
# Tab Optimize
from real_time_opt_update import RealTimeOptUpdate
import opt_tab_support
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtCore import QFileSystemWatcher
# Tab Optimize (end)
import run_optimize  # Optimize khởi chạy
import os
from report import *
import re

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
class Ui_group(object):
    def setupUi(self, group):
        group.setObjectName("group")
        group.resize(1920, 1080)
        self.centralwidget = QtWidgets.QWidget(parent=group)
        self.centralwidget.setObjectName("centralwidget")
        
        #Ảnh nền cho app
        palette = QPalette()
        pixmap = QPixmap(resource_path("pic/pic1.png"))
        scaled_pixmap = pixmap.scaled( # Scale ảnh theo kích thước group
        group.size(),
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation
        )
        palette.setBrush(QPalette.ColorRole.Window, QBrush(scaled_pixmap))
        group.setAutoFillBackground(True)
        group.setPalette(palette)
        
        # Main layout 
        self.main_layout = QtWidgets.QHBoxLayout(self.centralwidget)
        
        # Left side - Input box layout 
        self.left_layout = QtWidgets.QVBoxLayout()
        self.main_layout.addLayout(self.left_layout, 1)  # 1 part for input boxes

        # Right side - VisualizerWidget 
        self.tabs = QTabWidget(self.centralwidget)  # Tạo QTabWidget với parent là centralwidget

        # Tạo các VisualizerWidget làm nội dung cho từng tab
        self.tab1 = VisualizerWidget(self.centralwidget)
        self.tab2 = VisualizerWidget(self.centralwidget)
        self.tab3 = MatplotlibWidget(self.centralwidget)
 
        # Thêm tab1 và tab2 vào QTabWidget
        self.tabs.addTab(self.tab1, "Mesh")
        self.tabs.addTab(self.tab2, "Results")
        self.tabs.addTab(self.tab3, "Residuals")
        self.tabs.setStyleSheet("""
                                     QTabWidget::pane {
                                     border: none;
                                     }
                                     QTabBar::tab {
                                     background-color: rgba(255, 255, 255, 120);  /* Nền của các tab */
                                     color: black;             /* Màu chữ của tab */
                                     padding: 5px;
                                     border-radius: 10px;
                                     margin-top: 25px;             /* Khoảng cách nội dung trong tab */  /* Viền màu xám nhạt */     
                                     }
                                     QTabBar::tab:selected {
                                     background-color: white;  /* Nền trắng khi tab được chọn */
                                     color: black;              /* Màu chữ khi tab được chọn */
                                     }
                                     QTabBar::tab:hover {
                                     background-color: rgba(255, 255, 255, 200);  /* Nền sáng hơn khi di chuột */
                                     border: none;
                                     }
                                     """)

        # Thêm QTabWidget vào layout chính (1 part cho box, 5 part cho visual)
        self.main_layout.addWidget(self.tabs, 5)

        # Mesh box (generate section)
        self.mesh = QtWidgets.QGroupBox(parent=self.centralwidget)
        self.mesh.setFlat(False)
        self.mesh.setCheckable(False)
        self.mesh.setObjectName("mesh")
        self.mesh.setStyleSheet("""
                                QGroupBox {
                                background-color: rgba(255, 255, 255, 100);  /* Nền trắng */
                                border: 1px solid gray;   /* Viền xung quanh */ 
                                border-radius: 10px         /* Khoảng cách phía trên */
                                }                              
                                QGroupBox::title {
                                subcontrol-origin: margin;
                                subcontrol-position: top left;
                                padding: 5px 10px;
                                background-color: rgba(255, 255, 255, 170);  /* Nền trắng cho tiêu đề */
                                color: black;  /* Màu chữ của tiêu đề */    
                                border-top-left-radius: 10px;                       
                                }
                                """)

  
       # 3. Tạo QTabWidget bên trong GroupBox
        self.mesh_tabs = QtWidgets.QTabWidget()
        self.mesh_tabs.setStyleSheet("""
                                     QTabWidget::pane {
                                     border: none;
                                     }
                                     QTabBar::tab {
                                     background-color: rgba(255, 255, 255, 120);  /* Nền của các tab */
                                     color: black;             /* Màu chữ của tab */
                                     padding: 5px;
                                     border-radius: 10px;
                                     margin-top: 25px;             /* Khoảng cách nội dung trong tab */  /* Viền màu xám nhạt */     
                                     }
                                     QTabBar::tab:selected {
                                     background-color: white;  /* Nền trắng khi tab được chọn */
                                     color: black;              /* Màu chữ khi tab được chọn */
                                     }
                                     QTabBar::tab:hover {
                                     background-color: rgba(255, 255, 255, 200);  /* Nền sáng hơn khi di chuột */
                                     border: none;
                                     }
                                     """)
        self.left_layout.addWidget(self.mesh)

        # 4. Tạo tab 1: Cấu hình lưới
        self.mesh_tab = QtWidgets.QWidget()
        self.mesh_layout = QtWidgets.QGridLayout(self.mesh_tab)
        

        # 5. Tạo tab 2: Hiển thị lưới
        self.refine_tab = QtWidgets.QWidget()
        self.refine_layout = QtWidgets.QVBoxLayout(self.refine_tab)

        # 6. Thêm 2 tab vào QTabWidget
        self.mesh_tabs.addTab(self.mesh_tab, "Model")
        self.mesh_tabs.addTab(self.refine_tab, "Refinement")
        self.mesh_tabs.setTabVisible(1,False)

        # 7. Thêm GroupBox vào layout chính
        self.layout = QtWidgets.QVBoxLayout(self.mesh)
        self.layout.addWidget(self.mesh_tabs)

        # Chọn mesh
        self.mesh_type = QtWidgets.QLabel(parent=self.mesh_tab)
        self.mesh_type.setGeometry(QtCore.QRect(225, 10, 80, 20))
        self.mesh_type.setObjectName("mesh type")
        self.mesh_type.setText("Mesh type")

        # Tạo buttons cho C-shape, farfield và box mesh
        self.c_shape = QtWidgets.QRadioButton("C-shape ", parent=self.mesh_tab)
        self.farfield = QtWidgets.QRadioButton("Farfield", parent= self.mesh_tab)
        self.box = QtWidgets.QRadioButton("Box", parent= self.mesh_tab)
        self.c_shape.setGeometry(QtCore.QRect(225, 20, 100, 50))
        self.farfield.setGeometry(QtCore.QRect(225, 50, 100, 50))
        self.box.setGeometry(QtCore.QRect(225, 80, 100, 50))
        self.c_shape.toggled.connect(self.update_mesh)
        self.farfield.toggled.connect(self.update_mesh)
        self.box.toggled.connect(self.update_mesh)
        

        # Tạo buttons cho inviscid và turbulent
        self.radio_inviscid = QtWidgets.QRadioButton("Inviscid", parent=self.mesh_tab)
        self.radio_turbulent = QtWidgets.QRadioButton("Turbulent", parent= self.mesh_tab)
        self.radio_inviscid.setChecked(True)
        self.radio_turbulent.setGeometry(QtCore.QRect(120, 110, 100, 50))
        self.radio_inviscid.setGeometry(QtCore.QRect(20, 110, 100, 50))
        self.radio_turbulent.toggled.connect(self.updateTabVisibility)
        self.radio_inviscid.toggled.connect(self.updateTabVisibility)

        #Nhóm các nút
        self.mesh_type = QtWidgets.QButtonGroup(self.mesh_tab)
        self.mesh_type.addButton(self.c_shape)
        self.mesh_type.addButton(self.farfield)
        self.mesh_type.addButton(self.box)
        self.c_shape.setChecked(True)
        self.flow_group = QtWidgets.QButtonGroup()
        self.flow_group.addButton(self.radio_inviscid)
        self.flow_group.addButton(self.radio_turbulent)

        # Nút GENERATE
        self.generate = QtWidgets.QPushButton(parent=self.mesh_tab)
        self.generate.setGeometry(QtCore.QRect(10, 150, 200, 50))
        self.generate.setObjectName("generate")
        self.generate.setStyleSheet("""
            QPushButton {
                background-color: white;
                font-size: 16px;
                color: black;
            }
        """)
        
        # Nút REPORT
        self.report = QtWidgets.QPushButton(parent=self.mesh_tab)
        self.report.setGeometry(QtCore.QRect(215, 150, 70, 50))
        self.report.setObjectName("report")
        self.report.setStyleSheet("""
            QPushButton {
                background-color: white;
                font-size: 16px;
                color: black;
            }
        """)
        self.report.hide()
        
        # Box chọn loại airfoil
        self.type_of_naca = QtWidgets.QComboBox(parent=self.mesh_tab)
        self.type_of_naca.setGeometry(QtCore.QRect(10, 30, 200, 30))
        self.type_of_naca.setEditable(True)
        self.type_of_naca.setObjectName("type_of_naca")
        self.type_of_naca.setStyleSheet("""
                                QComboBox{
                                background-color: white;  /* Nền trắng */
                                border: 1px solid gray;   /* Viền xung quanh */
                                border-radius: 5px;
                                padding: 5px;
                                }
                                """)
        self.type_of_naca.addItem("")
        self.type_of_naca.addItem("")
        self.type_of_naca.addItem("")

        # Box chọn tên airfoil
        self.type = QtWidgets.QComboBox(parent=self.mesh_tab)
        self.type.setGeometry(QtCore.QRect(10, 90, 200, 30))
        self.type.setEditable(True)
        self.type.setCurrentText("")
        self.type.setDuplicatesEnabled(False)
        self.type.setObjectName("type")
        self.type.setStyleSheet("""
                                QComboBox{
                                background-color: white;  /* Nền trắng */
                                border: 1px solid gray;   /* Viền xung quanh */
                                border-radius: 5px;
                                padding: 5px;
                                }
                                """)
        
        # Box chọn loại airfoil do người dùng nhập
        self.type_line = QtWidgets.QLineEdit(parent=self.mesh_tab)
        self.type_line.setGeometry(self.type.geometry())
        self.type_line.setObjectName("type_line")
        self.type_line.setStyleSheet("")
        self.type_line.hide()

        self.type_of_naca.currentTextChanged.connect(self.airfoil_type)

        self.label = QtWidgets.QLabel(parent=self.mesh_tab)
        self.label.setGeometry(QtCore.QRect(20, 10, 81, 16))
        self.label.setObjectName("select group")

        self.label_2 = QtWidgets.QLabel(parent=self.mesh_tab)
        self.label_2.setGeometry(QtCore.QRect(20, 70, 71, 16))
        self.label_2.setObjectName("select airfoil")

        # Tab tính toán wall spacing
        self.input = QtWidgets.QLabel(parent=self.refine_tab)
        self.input.setGeometry(QtCore.QRect(0, 0, 70, 20))
        self.input.setText("Input")

        self.ouput = QtWidgets.QLabel(parent=self.refine_tab)
        self.ouput.setGeometry(QtCore.QRect(155, 0, 70, 20))
        self.ouput.setText("Output")

        self.mach1 = QtWidgets.QLineEdit(parent=self.refine_tab)
        self.mach1.setGeometry(QtCore.QRect(0, 20, 100, 25))
        self.mach1.setObjectName("velocity")
        self.mach1.setPlaceholderText("Mach number")
        self.mach1.setStyleSheet("""
                                QLineEdit{
                                background-color: white;  /* Nền trắng */
                                border: 1px solid gray;   /* Viền xung quanh */
                                border-radius: 5px;
                                padding: 5px;
                                }
                                """)

        self.temperature = QtWidgets.QLineEdit(parent=self.refine_tab)
        self.temperature.setGeometry(QtCore.QRect(0, 60, 100, 25))
        self.temperature.setObjectName("temperature")
        self.temperature.setPlaceholderText("Temperature")
        self.temperature_label = QtWidgets.QLabel(parent=self.refine_tab)
        self.temperature_label.setGeometry(QtCore.QRect(105, 60, 100, 25))
        self.temperature_label.setText('(K)')
        self.temperature.setStyleSheet("""
                                QLineEdit{
                                background-color: white;  /* Nền trắng */
                                border: 1px solid gray;   /* Viền xung quanh */
                                border-radius: 5px;
                                padding: 5px;
                                }
                                """)

        self.density = QtWidgets.QLineEdit(parent=self.refine_tab)
        self.density.setGeometry(QtCore.QRect(0, 100, 100, 25))
        self.density.setObjectName("density")
        self.density.setPlaceholderText("Freestresm density")
        self.density_label = QtWidgets.QLabel(parent=self.refine_tab)
        self.density_label.setGeometry(QtCore.QRect(105, 100, 100, 25))
        self.density_label.setText('(kg/m3)')
        self.density.setStyleSheet("""
                                QLineEdit{
                                background-color: white;  /* Nền trắng */
                                border: 1px solid gray;   /* Viền xung quanh */
                                border-radius: 5px;
                                padding: 5px;
                                }
                                """)

        self.dyn_viscousity = QtWidgets.QLineEdit(parent=self.refine_tab)
        self.dyn_viscousity.setGeometry(QtCore.QRect(0, 140, 100, 25))
        self.dyn_viscousity.setObjectName("velocity")
        self.dyn_viscousity.setPlaceholderText("Dynamic viscosity")
        self.dyn_viscousity_label = QtWidgets.QLabel(parent=self.refine_tab)
        self.dyn_viscousity_label.setGeometry(QtCore.QRect(105, 140, 100, 25))
        self.dyn_viscousity_label.setText('(kg/ms)')
        self.dyn_viscousity.setStyleSheet("""
                                QLineEdit{
                                background-color: white;  /* Nền trắng */
                                border: 1px solid gray;   /* Viền xung quanh */
                                border-radius: 5px;
                                padding: 5px;
                                }
                                """)

        self.ref_length = QtWidgets.QLineEdit(parent=self.refine_tab)
        self.ref_length.setGeometry(QtCore.QRect(0, 180, 100, 25))
        self.ref_length.setObjectName("velocity")
        self.ref_length.setPlaceholderText("Reference length")
        self.ref_length_label = QtWidgets.QLabel(parent=self.refine_tab)
        self.ref_length_label.setGeometry(QtCore.QRect(105, 180, 100, 25))
        self.ref_length_label.setText('(m)')
        self.ref_length.setStyleSheet("""
                                QLineEdit{
                                background-color: white;  /* Nền trắng */
                                border: 1px solid gray;   /* Viền xung quanh */
                                border-radius: 5px;
                                padding: 5px;
                                }
                                """)

        self.y_plus = QtWidgets.QLineEdit(parent=self.refine_tab)
        self.y_plus.setGeometry(QtCore.QRect(0, 220, 100, 25))
        self.y_plus.setObjectName("velocity")
        self.y_plus.setPlaceholderText("Desired y+")
        self.y_plus.setStyleSheet("""
                                QLineEdit{
                                background-color: white;  /* Nền trắng */
                                border: 1px solid gray;   /* Viền xung quanh */
                                border-radius: 5px;
                                padding: 5px;
                                }
                                """)

        self.wall = QtWidgets.QLineEdit(parent=self.refine_tab)
        self.wall.setGeometry(QtCore.QRect(155, 20, 100, 25))
        self.wall.setObjectName("velocity")
        self.wall.setPlaceholderText("Wall spacing")
        self.wall_label = QtWidgets.QLabel(parent=self.refine_tab)
        self.wall_label.setGeometry(QtCore.QRect(260, 19, 100, 30))
        self.wall_label.setText('(m)')
        self.wall.setStyleSheet("""
                                QLineEdit{
                                background-color: white;  /* Nền trắng */
                                border: 1px solid gray;   /* Viền xung quanh */
                                border-radius: 5px;
                                padding: 5px;
                                }
                                """)

        self.Re = QtWidgets.QLineEdit(parent=self.refine_tab)
        self.Re.setGeometry(QtCore.QRect(155, 60, 100, 25))
        self.Re.setObjectName("velocity")
        self.Re.setPlaceholderText("Reynolds number")
        self.Re.setStyleSheet("""
                                QLineEdit{
                                background-color: white;  /* Nền trắng */
                                border: 1px solid gray;   /* Viền xung quanh */
                                border-radius: 5px;
                                padding: 5px;
                                }
                                """)

        self.cal = QtWidgets.QPushButton(parent=self.refine_tab)
        self.cal.setGeometry(QtCore.QRect(170, 100, 70, 40))
        self.cal.setText("COMPUTE")
        self.cal.setStyleSheet("""
            QPushButton {
                background-color: white;
                font-size: 12px;
                color: black;
            }
        """)

        # Hộp thoại điều kiện ban đầu
        self.groupBox = QtWidgets.QGroupBox(parent=self.centralwidget)
        self.groupBox.setObjectName("groupBox")
        self.left_layout.addWidget(self.groupBox)
        self.groupBox.hide()  # Ẩn đi khi tạo lưới
        self.groupBox.setStyleSheet("""
                                    QGroupBox {
                                    background-color: rgba(255, 255, 255, 100);  /* Nền trắng */
                                    border: 1px solid gray;   /* Viền xung quanh */
                                    border-radius: 10px;
                                    }                                
                                    QGroupBox::title {
                                    subcontrol-origin: margin;
                                    subcontrol-position: top left;
                                    padding: 5px 10px;
                                    background-color: rgba(255, 255, 255, 170);  /* Nền trắng cho tiêu đề */
                                    color: black;  /* Màu chữ của tiêu đề */
                                    font: bold 30px;  /* Kiểu chữ đậm, kích thước 16px */    
                                    border-top-left-radius: 10px;                       
                                    }
                                    """)
        

        self.mach = QtWidgets.QLineEdit(parent=self.groupBox)
        self.mach.setGeometry(QtCore.QRect(20, 90, 200, 25))
        self.mach.setText("")
        self.mach.setStyleSheet("""
                                QLineEdit{
                                background-color: white;  /* Nền trắng */
                                border: 1px solid gray;   /* Viền xung quanh */
                                border-radius: 5px;
                                padding: 5px;
                                }
                                """)
        self.mach.setObjectName("mach")

        self.aoa = QtWidgets.QLineEdit(parent=self.groupBox)
        self.aoa.setGeometry(QtCore.QRect(20, 120, 200, 25))
        self.aoa.setText("")
        self.aoa.setStyleSheet("""
                                QLineEdit{
                                background-color: white;  /* Nền trắng */
                                border: 1px solid gray;   /* Viền xung quanh */
                                border-radius: 5px;
                                padding: 5px;
                                }
                                """)
        self.aoa.setObjectName("aoa")

        self.temp = QtWidgets.QLineEdit(parent=self.groupBox)
        self.temp.setGeometry(QtCore.QRect(20, 150, 200, 25))
        self.temp.setText("")
        self.temp.setStyleSheet("""
                                QLineEdit{
                                background-color: white;  /* Nền trắng */
                                border: 1px solid gray;   /* Viền xung quanh */
                                border-radius: 5px;
                                padding: 5px;
                                }
                                """)
        self.temp.setObjectName("temp")

        self.pressure = QtWidgets.QLineEdit(parent=self.groupBox)
        self.pressure.setGeometry(QtCore.QRect(20, 180, 200, 25))
        self.pressure.setText("")
        self.pressure.setStyleSheet("""
                                QLineEdit{
                                background-color: white;  /* Nền trắng */
                                border: 1px solid gray;   /* Viền xung quanh */
                                border-radius: 5px;
                                padding: 5px;
                                }
                                """)
        self.pressure.setObjectName("pressure")

        self.solver = QtWidgets.QComboBox(parent=self.groupBox)
        self.solver.setGeometry(QtCore.QRect(20, 55, 200, 30))
        self.solver.setEditable(False)
        self.solver.setObjectName("solver")
        self.solver.addItem("")
        self.solver.addItem("")
        self.solver.addItem("")
        self.solver.addItem("")
        self.solver.addItem("")
        self.solver.addItem("")
        self.solver.setStyleSheet("""
                                QComboBox{
                                background-color: white;  /* Nền trắng */
                                border: 1px solid gray;   /* Viền xung quanh */
                                border-radius: 5px;
                                padding: 5px;
                                }
                                """)

        self.label_3 = QtWidgets.QLabel(parent=self.groupBox)
        self.label_3.setGeometry(QtCore.QRect(25, 35, 50, 25))
        self.label_3.setObjectName("solver")

        self.label_4 = QtWidgets.QLabel(parent=self.groupBox)
        self.label_4.setGeometry(QtCore.QRect(230, 120, 50, 25))
        self.label_4.setObjectName("degree")

        self.label_5 = QtWidgets.QLabel(parent=self.groupBox)
        self.label_5.setGeometry(QtCore.QRect(230, 150, 50, 25))
        self.label_5.setObjectName("(K)")

        self.label_6 = QtWidgets.QLabel(parent=self.groupBox)
        self.label_6.setGeometry(QtCore.QRect(230, 180, 50, 25))
        self.label_6.setObjectName("(Pa)")

        self.label_7 = QtWidgets.QLabel(parent=self.groupBox)
        self.label_7.setGeometry(QtCore.QRect(20, 208, 200, 20))
        self.label_7.setText("Turbulence Model")

        self.sst = QtWidgets.QCheckBox("SST", parent=self.groupBox)
        self.sst.setGeometry(QtCore.QRect(125, 203, 100, 30))
        
        self.sa = QtWidgets.QCheckBox("Spalart-Allmaras", parent=self.groupBox)
        self.sa.setGeometry(QtCore.QRect(170, 203, 150, 30))


        # Nút RUN
        self.run = QtWidgets.QPushButton(parent=self.groupBox)
        self.run.setGeometry(QtCore.QRect(20, 230, 200, 50))
        self.run.setObjectName("run")
        self.run.setStyleSheet("""
            QPushButton {
                background-color: white;
                font-size: 16px;
                color: black;
            }
        """)
# Tab Optimize ===================================================================
    # Tạo tab mới cho Optimize
        self.tab4 = QtWidgets.QWidget(self.centralwidget)
        self.tab4.setObjectName("Optimize")
        self.tabs.addTab(self.tab4, "Optimize")
        self.tab4_layout = QVBoxLayout(self.tab4)
        self.tab4_layout.setContentsMargins(5,5,5,5)
        self.tab4.setStyleSheet("""
                                    QWidget {
                                    background-color: white;
                                    } 
                                    """)

    # Tạo menu bar
        self.menu_bar = QFrame(self.tab4)
        self.menu_bar.setObjectName("menu_bar")
        self.menu_bar.setFrameShape(QFrame.Shape.StyledPanel)

        self.menu_bar.setFixedHeight(40) # Chiều cao cố định (ví dụ 40px) đủ cho 1 dòng text / nút

        # Thiết đặt layout ngang
        self.menu_bar_layout = QHBoxLayout(self.menu_bar)
        self.menu_bar_layout.setContentsMargins(5,0,5,0)
        self.menu_bar_layout.setSpacing(10)
        self.menu_bar_layout.setAlignment(Qt.AlignmentFlag.AlignLeft) # Chỉnh layout nút căn lề trái

        self.tab4_layout.addWidget(self.menu_bar, stretch=0) # Thêm menu_bar vào layout chính, stretch 0 (không giãn)

    # Tạo vùng hiển thị results
        self.display_area = QFrame(self.tab4)
        self.display_area.setLayout(QVBoxLayout()) # Tự động chia ô khi chọn phần hiển thị trong Display Result Setting
        self.display_area.setObjectName("display_area")
        self.display_area.setFrameShape(QFrame.Shape.StyledPanel)
        self.tab4_layout.addWidget(self.display_area, stretch=1) # Vùng này sẽ giãn chiếm hết không gian còn lại

    # Nút Display Result
        # Tạo nút Display Result
        self.display_btn = QToolButton(self.menu_bar)
        self.display_btn.setText("Display Result")
        self.display_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)     # Popup Setting ra
        self.display_btn.setFixedWidth(100)             # Giới hạn độ rộng
        self.menu_bar_layout.addWidget(self.display_btn)

        menu_display = QMenu(self.display_btn) # Tạo Menu Display Result “thả xuống”

        # Tạo một QWidget làm khung settings
        sett_display_widget = QWidget()
        sett_display_layout = QVBoxLayout(sett_display_widget)
        sett_display_layout.setContentsMargins(8, 8, 8, 8)
        sett_display_layout.setSpacing(6)

        # Thêm 3 tùy chọn hiển thị cho Display Result Setting
        sett_display_layout.addWidget(QLabel("<b>Display Settings</b>"))
        self.cb_airfoil_compar = QCheckBox("Show Airfoil Comparison")
        sett_display_layout.addWidget(self.cb_airfoil_compar)
        self.cb_flow    = QCheckBox("Show Flow fields")
        sett_display_layout.addWidget(self.cb_flow)
        self.cb_res     = QCheckBox("Show Residuals")
        sett_display_layout.addWidget(self.cb_res)

        # Lưu các check box vào biến display_checks
        self.display_checks = {
                                "Airfoil Comparison": self.cb_airfoil_compar,
                                "Flow fields"       : self.cb_flow,
                                "Residuals"         : self.cb_res,
                                }

        self.current_display_sett = [] # Khởi tạo list lưu trạng thái hiện tại là chưa check ô nào hết

        for cb_display in self.display_checks.values():
            cb_display.stateChanged.connect(self.update_display_list) # Kết nối tới update_display_list mỗi khi người dùng tick/un-tick
            self.update_display_area() # Vẽ placeholder ban đầu (Thêm Please select options in Display Result above ngay khi mới mở)

        # Đóng gói widget này thành QAction để chèn vào menu_display
        display_widget_action = QWidgetAction(self.display_btn)
        display_widget_action.setDefaultWidget(sett_display_widget)
        menu_display.addAction(display_widget_action)

        self.display_btn.setMenu(menu_display) # Gán menu_display cho nút

    # Menu Bar chia chức năng:
        # Thêm kẻ dọc chia đôi Display Result với Result Settings:
        self.separator = QFrame(self.menu_bar)
        self.separator.setFrameShape(QFrame.Shape.VLine)
        self.separator.setFrameShadow(QFrame.Shadow.Sunken)
        self.separator.setLineWidth(1)
        self.separator.setContentsMargins(5, 0, 5, 0)
        self.menu_bar_layout.addWidget(self.separator)

        # Hiện Label “Result Settings:” sau Display Result
        self.result_label = QLabel("Result Settings:", self.menu_bar)
        self.menu_bar_layout.addWidget(self.result_label)

        # Nút Comparison
        self.comp_settings_btn = QToolButton(self.menu_bar)
        self.comp_settings_btn.setText("Comparison Settings")
        self.comp_settings_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.comp_settings_btn.setFixedWidth(150)
        self.menu_bar_layout.addWidget(self.comp_settings_btn)
        self.comp_settings_btn.hide() # Ẩn khi không tick Display

        # Dropdown menu
        menu_comp = QMenu(self.comp_settings_btn)
        comp_widget = QWidget()
        comp_layout = QVBoxLayout(comp_widget)
        comp_layout.setContentsMargins(8,8,8,8)
        comp_layout.setSpacing(6)

        # Header
        hdr = QLabel("Multiple choices")
        f = hdr.font(); f.setItalic(True); hdr.setFont(f)
        comp_layout.addWidget(hdr)

        # Search box
        self.comp_search = QLineEdit()
        self.comp_search.setPlaceholderText("Find…")
        self.comp_search.textChanged.connect(self.filter_comp_checks) # Kết nối comp_search với module lọc filter_comp_checks
        comp_layout.addWidget(self.comp_search)

        # Scroll area cho checkbox
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0,0,0,0)
        scroll_layout.setSpacing(4)
        scroll.setWidget(scroll_content)
        scroll.setFixedHeight(hdr.fontMetrics().height()*6 + 12) # Cho hiển thị 6 dòng checkbox
        comp_layout.addWidget(scroll)

        # Thêm các check box vào trong Scroll area
        # 1) Checkbox “Latest Design”
        self.cb_latest_design = QCheckBox("Latest Design")
        scroll_layout.addWidget(self.cb_latest_design)

        # 2) Checkbox baseline – NACA_{code}
        code = ''.join(filter(str.isdigit, self.type.currentText()))
        self.baseline_label = f"NACA_{code}"
        self.cb_naca_code = QCheckBox(self.baseline_label)
        scroll_layout.addWidget(self.cb_naca_code)

        # Khởi tạo dict để gom check box của Comparison
        self.comp_checks = {
            "Latest Design": self.cb_latest_design,
            self.baseline_label: self.cb_naca_code,
        }
        # Khởi tạo list lưu lựa chọn comparison (tránh AttributeError)
        self.current_comp_sett = []
        for name, cb in self.comp_checks.items():
            cb.stateChanged.connect(self.update_comp_list) # Kết nối các items trong dict comp_checks tới module cập nhật check box update_comp_list

        self.comp_scroll_layout = scroll_layout # Lưu scroll_layout để sau này cập nhật DSN_xxx

        # Đóng gói vào menu comparison
        comp_action = QWidgetAction(self.comp_settings_btn)
        comp_action.setDefaultWidget(comp_widget)
        menu_comp.addAction(comp_action)
        self.comp_settings_btn.setMenu(menu_comp)

    # Nút Flow fields
        self.flow_settings_btn = QToolButton(self.menu_bar)
        self.flow_settings_btn.setText("Flow fields Settings")
        self.flow_settings_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.flow_settings_btn.setFixedWidth(140)
        self.menu_bar_layout.addWidget(self.flow_settings_btn)
        self.flow_settings_btn.hide() # Ẩn khi không tick Display

        menu_flow = QMenu(self.flow_settings_btn) # Tạo menu dropdown

        # Widget chứa layout 2 cột
        flow_widget = QWidget()
        flow_layout = QHBoxLayout(flow_widget)
        flow_layout.setContentsMargins(8,8,8,8)
        flow_layout.setSpacing(10)

        # --- Cột 1: Airfoil ---
        col1 = QWidget()
        col1_layout = QVBoxLayout(col1)
        lbl1 = QLabel("Airfoil")         # Tiêu đề
        col1_layout.addWidget(lbl1)
        note1 = QLabel("Select one")        # Chú thích
        f1 = note1.font(); f1.setItalic(True); note1.setFont(f1)
        col1_layout.addWidget(note1)

        # Scroll area
        sa1 = QScrollArea()
        sa1.setWidgetResizable(True)
        cont1 = QWidget()
        lay1 = QVBoxLayout(cont1)
        lay1.setContentsMargins(0,0,0,0); lay1.setSpacing(4)
        # Checkbox nhóm Airfoil
        self.cb_ff_latest = QCheckBox("Latest Design")
        self.cb_ff_naca_code   = QCheckBox("NACA_{code}")
        for cb in (self.cb_ff_latest, self.cb_ff_naca_code):
            lay1.addWidget(cb)
        sa1.setWidget(cont1)
        sa1.setFixedHeight(lbl1.fontMetrics().height()*6 + 12) # Hiện 6 dòng check box trong Scroll area
        col1_layout.addWidget(sa1)

        # Giữ dict + list cho Airfoil
        self.flow_airfoil_checks = {
            "Latest Design": self.cb_ff_latest,
            "NACA_{code}"  : self.cb_ff_naca_code,
        }
        self.current_flow_airfoil = []  # Ban đầu không tick box nào hết
        # Chưa hiểu ======
        # Kết nối ràng buộc chọn 1
        for name, cb in self.flow_airfoil_checks.items():
            # truyền name vào slot, slot nhận (name, state)
            cb.stateChanged.connect(partial(self._on_flow_airfoil_changed, name))
        # Chưa hiểu (end)======

        # --- Separator giữa 2 cột ---
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        flow_layout.addWidget(col1)
        flow_layout.addWidget(sep)

        # --- Cột 2: Flow fields ---
        col2 = QWidget()
        col2_layout = QVBoxLayout(col2)
        lbl2 = QLabel("Flow fields")
        col2_layout.addWidget(lbl2)
        note2 = QLabel("Select one")
        f2 = note2.font(); f2.setItalic(True); note2.setFont(f2)
        col2_layout.addWidget(note2)

        # Scroll area
        sa2 = QScrollArea()
        sa2.setWidgetResizable(True)
        cont2 = QWidget()
        lay2 = QVBoxLayout(cont2)
        lay2.setContentsMargins(0,0,0,0); lay2.setSpacing(4)
        # Checkbox nhóm Flow fields
        self.cb_ff_press = QCheckBox("Pressure")
        self.cb_ff_temp  = QCheckBox("Temperature")
        self.cb_ff_vel   = QCheckBox("Velocity")
        for cb in (self.cb_ff_press, self.cb_ff_temp, self.cb_ff_vel):
            lay2.addWidget(cb)
        sa2.setWidget(cont2)
        sa2.setFixedHeight(lbl2.fontMetrics().height()*6 + 12)
        col2_layout.addWidget(sa2)

        # Giữ dict + list cho Flow fields
        self.flow_field_checks = {
            "Pressure"   : self.cb_ff_press,
            "Temperature": self.cb_ff_temp,
            "Velocity"   : self.cb_ff_vel,
        }
        self.current_flow_fields = []
        # Chưa hiểu ======
        for name, cb in self.flow_field_checks.items():
            cb.stateChanged.connect(partial(self._on_flow_field_changed, name))
        # Chưa hiểu (end)======
        flow_layout.addWidget(col2)

        # Đóng gói widget vào menu và gán cho nút
        action_flow = QWidgetAction(self.flow_settings_btn)
        action_flow.setDefaultWidget(flow_widget)
        menu_flow.addAction(action_flow)
        self.flow_settings_btn.setMenu(menu_flow)

    # Nút Residuals
        self.resid_settings_btn = QToolButton(self.menu_bar)
        self.resid_settings_btn.setText("Residual Settings")
        self.resid_settings_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.resid_settings_btn.setFixedWidth(150)
        self.menu_bar_layout.addWidget(self.resid_settings_btn)
        self.resid_settings_btn.hide() # Ẩn khi không tick Display

        menu_resid = QMenu(self.resid_settings_btn) # Tạo menu thả xuống cho Residual Settings

        # Widget chứa nội dung setting
        resid_widget = QWidget()
        resid_layout = QVBoxLayout(resid_widget)
        resid_layout.setContentsMargins(8, 8, 8, 8)
        resid_layout.setSpacing(6)

        # Dòng ghi chú in nghiêng
        header = QLabel("Multiple choices")
        font = header.font()
        font.setItalic(True)
        header.setFont(font)
        resid_layout.addWidget(header)

        # 4 checkbox cho residual settings
        self.cb_CL     = QCheckBox("CL")
        self.cb_CD     = QCheckBox("CD")
        self.cb_MZ     = QCheckBox("MOMENT_Z")
        self.cb_T      = QCheckBox("AIRFOIL_THICKNESS")
        for cb_resid in (self.cb_CL, self.cb_CD, self.cb_MZ, self.cb_T):
            resid_layout.addWidget(cb_resid)

        # Lưu các checkbox vào dict để quản lý
        self.resid_checks = {
            "CL"                : self.cb_CL,
            "CD"                : self.cb_CD,
            "MOMENT_Z"          : self.cb_MZ,
            "AIRFOIL_THICKNESS" : self.cb_T,
        }
        # Khởi tạo list lưu trạng thái
        self.current_resid_sett = []

        # Kết nối tới module cập nhật update_resid_list mỗi khi tick/un-tick
        for cb_resid in self.resid_checks.values():
            cb_resid.stateChanged.connect(self.update_resid_list)

        # Đóng gói widget thành QAction rồi thêm vào menu
        resid_action = QWidgetAction(self.resid_settings_btn)
        resid_action.setDefaultWidget(resid_widget)
        menu_resid.addAction(resid_action)

        # Gán menu cho nút
        self.resid_settings_btn.setMenu(menu_resid)

# Tab Optimize (end) =============================================================
  
        # Box optimize ======================================================================

        # Thêm khối Optimization vào giao diện
        self.optimize = QtWidgets.QGroupBox(parent=self.centralwidget)
        self.optimize.setFlat(False)
        self.optimize.setCheckable(False)
        self.optimize.setObjectName("optimize")
        self.left_layout.addWidget(self.optimize)
        self.optimize.setStyleSheet("""
                                    QGroupBox {
                                    background-color: rgba(255, 255, 255, 100);  /* Nền trắng */
                                    border: 1px solid gray;   /* Viền xung quanh */
                                    border-radius: 10px;
                                    }                                
                                    QGroupBox::title {
                                    subcontrol-origin: margin;
                                    subcontrol-position: top left;
                                    padding: 5px 10px;
                                    background-color: rgba(255, 255, 255, 170);  /* Nền trắng cho tiêu đề */
                                    color: black;  /* Màu chữ của tiêu đề */
                                    font: bold 30px;  /* Kiểu chữ đậm, kích thước 16px */    
                                    border-top-left-radius: 10px;                       
                                    }
                                     QPushButton {
                                    background-color: white;
                                    font-size: 16px;
                                    color: black;
                                    }
                                    """)
        self.optimize.hide()  # Ẩn đi khi tạo lưới
        # Loại Design Variable (dvkind)
        # Tên
        self.label_dvkind = QtWidgets.QLabel(parent=self.optimize)
        self.label_dvkind.setGeometry(QtCore.QRect(20, 30, 150, 20))
        # Ô chọn
        self.dvkind = QtWidgets.QComboBox(parent=self.optimize)
        self.dvkind.setGeometry(QtCore.QRect(20, 50, 200, 30))
        self.dvkind.setEditable(False)
        self.dvkind.setObjectName("dvkind")
        self.dvkind.addItem("")
        self.dvkind.addItem("")
        self.dvkind.setStyleSheet("""
                                QComboBox{
                                background-color: white;  /* Nền trắng */
                                border: 1px solid gray;   /* Viền xung quanh */
                                border-radius: 5px;
                                padding: 5px;
                                }
                                """)
        #
        # Số lượng Design Variables (Tạm thời yêu cầu lấy số chẵn (Đều 2 mặt) - Lẻ mặt trên dưới để sau làm thêm)
        # Tên
        self.label_dvnumber = QtWidgets.QLabel(parent=self.optimize)
        self.label_dvnumber.setGeometry(QtCore.QRect(20, 80, 150, 20))
        # Ô điền
        self.dvnumber = QtWidgets.QLineEdit(parent=self.optimize)
        self.dvnumber.setGeometry(QtCore.QRect(20, 100, 200, 25))
        self.dvnumber.setText("")
        self.dvnumber.setObjectName("dvnumber")
        self.dvnumber.setStyleSheet("""
                                QLineEdit{
                                background-color: white;  /* Nền trắng */
                                border: 1px solid gray;   /* Viền xung quanh */
                                border-radius: 5px;
                                padding: 5px;
                                }
                                """)
        #
        # Thông số cần tối ưu (Optimization objective) (opt_object)
        # Tên
        self.label_opt_object = QtWidgets.QLabel(parent=self.optimize)
        self.label_opt_object.setGeometry(QtCore.QRect(20, 125, 180, 20))
        # Ô chọn
        self.opt_object = QtWidgets.QComboBox(parent=self.optimize)
        self.opt_object.setGeometry(QtCore.QRect(20, 145, 200, 31))
        self.opt_object.setEditable(False)
        self.opt_object.setObjectName("opt_object")
        self.opt_object.addItem("")
        self.opt_object.addItem("")
        self.opt_object.setStyleSheet("""
                                QComboBox{
                                background-color: white;  /* Nền trắng */
                                border: 1px solid gray;   /* Viền xung quanh */
                                border-radius: 5px;
                                padding: 5px;
                                }
                                """)
        #
        # Tham số cố định (Optimization constraint) (opt_const)
        # Tên
        self.label_opt_const_type = QtWidgets.QLabel(parent=self.optimize)
        self.label_opt_const_type.setGeometry(QtCore.QRect(20, 175, 180, 20))
        # Ô chọn
        # Có chọn Optimization constraint hay không ?
        self.opt_const_type = QtWidgets.QComboBox(parent=self.optimize)
        self.opt_const_type.setGeometry(QtCore.QRect(20, 195, 200, 30))
        self.opt_const_type.setObjectName("opt_const_type")
        self.opt_const_type.setStyleSheet("""
                                QComboBox{
                                background-color: white;  /* Nền trắng */
                                border: 1px solid gray;   /* Viền xung quanh */
                                border-radius: 5px;
                                padding: 5px;
                                }
                                """)
        # Multi-select Optimization constraint
        self.opt_const_list = QtWidgets.QListWidget(parent=self.optimize)
        self.opt_const_list.setGeometry(QtCore.QRect(20, 230, 200, 80))
        self.opt_const_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)
        self.opt_const_list.setStyleSheet("""
                                          QListWidget {
                                          background-color: rgba(255, 255, 255, 170);
                                          border: 1px solid gray;
                                          border-radius: 5px;
                                          padding: 5px;
                                          font-size: 13px;
                                          }
                                          QListWidget::item:selected {
                                          background-color: #cce4ff;  /* Màu nền khi chọn */
                                          color: black;
                                          }
                                          QListWidget::item:hover {
                                          background-color: #e6f2ff;  /* Màu khi di chuột tới */
                                          }
                                          """)
        self.opt_const_list.hide()  # Ẩn lúc chưa chọn opt_const_type là select value
        self.opt_const_type.currentTextChanged.connect(self.toggle_constraint_list)  # Ẩn/Hiện box chọn tham số cố định
        #
        # Nút Run Optimize
        self.optimize_button = QtWidgets.QPushButton(parent=self.optimize)
        self.optimize_button.setGeometry(QtCore.QRect(20, 235, 200, 50))
        self.optimize_button.setObjectName("optimize_button")
        self.optimize_button.clicked.connect(self.run_optimization) # Kết nối nút với chức năng

        # Box optimize (end) ==================================================================
        # Ẩn/Hiện box chọn tham số cố định

        # Các trường quan sát trong tab 2
        self.field = QtWidgets.QComboBox(parent=self.tab2)
        self.field.setGeometry(QtCore.QRect(10, 10, 100, 30))
        self.field.setEditable(False)
        self.field.setCurrentText("Pressure")
        self.field.setDuplicatesEnabled(False)
        self.field.setObjectName("field")
        self.field.addItems(["Pressure", "Temperature", "Velocity", "Streamlines"])
        self.field.setStyleSheet("""
                                 QComboBox { 
                                 background-color: white;
                                 border: none
                                 font-size: 12px;
                                 }
                                 QComboBox::drop-down {
                                 color: black;
                                 subcontrol-origin: padding;
                                 subcontrol-position: top right;
                                 width: 20px;
                                 }
                                 QComboBox QAbstractItemView {
                                 background-color: white;
                                 selection-background-color: #cce4ff;
                                 selection-color: black;
                                 border: 1px solid #aaa;
                                 font-size: 15px;
                                 }
                                 """)


        self.res=MatplotlibWidget()

        group.setCentralWidget(self.centralwidget)

        # Thanh trạng thái khi chạy các quá trình
        self.statusbar = QtWidgets.QStatusBar(parent=group)
        self.statusbar.setObjectName("statusbar")
        group.setStatusBar(self.statusbar)

        group.showMaximized()

        self.retranslateUi(group)
        QtCore.QMetaObject.connectSlotsByName(group)

        # Kết nối các nút với chức năng
        self.generate.clicked.connect(lambda: self.groupBox.show())
        self.generate.clicked.connect(lambda: self.left_layout.setStretch(0, 1))  # self.mesh
        self.generate.clicked.connect(lambda: self.left_layout.setStretch(1, 1))  # self.boundary_box
        self.generate.clicked.connect(self.progress_bar)
        self.generate.clicked.connect(self.airfoil)
        self.report.clicked.connect(self.export_report)
        self.run.clicked.connect(self.sim)
        self.run.clicked.connect(self.progress_bar)
        self.run.clicked.connect(lambda: self.report.show())
        self.run.clicked.connect(lambda: self.optimize.show())
        self.run.clicked.connect(lambda: self.left_layout.setStretch(2, 1))
        self.run.clicked.connect(lambda: self.residuals())
        self.field.activated.connect(self.show)
        #self.cal.clicked.connect(self.compute())

    def toggle_constraint_list(self, text):
        if text == "Select value":
            self.opt_const_list.show()
        else:
            self.opt_const_list.hide()

    def compute(self):
        self.vel=(self.mach1)


    def updateTabVisibility(self):
        if self.radio_inviscid.isChecked():
            self.mesh_tabs.setTabVisible(1,False)
        elif self.radio_turbulent.isChecked():
            self.mesh_tabs.setTabVisible(1,True)
    
    def update_mesh(self):
        self.meshing = str
        if self.c_shape.isChecked():
            self.meshing="c-shape"
        elif self.farfield.isChecked():
            self.meshing="farfield"
        elif self.box.isChecked():
            self.meshing="box"
        return self.meshing

    def export_report(self): # Xuất báo cáo 
        code=MeshGenerator.naca_code(group=self.type_of_naca.currentText(),type=self.type.currentText())
        self.export = export(mach=self.mach.text(), 
                             aoa=self.aoa.text(), 
                             temp=self.temp.text(), 
                             pressure=self.pressure.text(), 
                             data=self.type.currentText(), 
                             csv_path=rf"NACA_{code}\history.csv", 
                             mesh_path=rf"NACA_{code}\NACA_{code}_mesh.png",
                             field_path=rf"NACA_{code}\NACA_{code}_{self.field.currentText()}.png",
                             plot_path=rf"NACA_{code}\plot.png",
                             )
        self.inform_success()

    def progress_bar(self): #Định nghĩa thanh tiến trình 
        # Tạo progress bar
        self.progress = QtWidgets.QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(0)
        self.statusbar.addPermanentWidget(self.progress)  # Thêm vào status bar


    def retranslateUi(self, group): #Đặt tên cho các item 
        _translate = QtCore.QCoreApplication.translate
        group.setWindowTitle(_translate("group", "Airfoil CFD Simulation"))

        self.generate.setText(_translate("group", "GENERATE"))
        self.report.setText(_translate("group", "REPORT"))
        self.type_of_naca.setItemText(0, _translate("group", "NACA 4 digit"))
        self.type_of_naca.setItemText(1, _translate("group", "NACA 5 digit"))
        self.type_of_naca.setItemText(2, _translate("group", "Others"))
        self.label.setText(_translate("group", "Select group"))
        self.label_2.setText(_translate("group", "Select airfoil"))

        self.optimize.setTitle(_translate("group", "Optimization"))

        self.mesh.setTitle(_translate("group", "Mesh"))
        self.groupBox.setTitle(_translate("group", "Initial Conditions"))
        self.mach.setPlaceholderText(_translate("group", "Mach number"))
        self.aoa.setPlaceholderText(_translate("group", "AOA"))
        self.temp.setPlaceholderText(_translate("group", "Temperature"))
        self.pressure.setPlaceholderText(_translate("group", "Pressure"))

        self.solver.setItemText(0, _translate("group", "EULER"))
        self.solver.setItemText(1, _translate("group", "NAVIER-STOKES"))
        self.solver.setItemText(2, _translate("group", "WAVE EQUATION"))
        self.solver.setItemText(3, _translate("group", "HEAT EQUATION"))
        self.solver.setItemText(4, _translate("group", "FEM ELASTICITY"))
        self.solver.setItemText(5, _translate("group", "POISSON EQUATION"))

        self.label_3.setText(_translate("group", "Solver"))
        self.label_4.setText(_translate("group", "(Degree)"))
        self.label_5.setText(_translate("group", "(K)"))
        self.label_6.setText(_translate("group", "(Pa)"))
        self.run.setText(_translate("group", "RUN"))

        # Box optimize ===========================================================

        # Tên box Optimization
        self.optimize.setTitle(_translate("group", "Optimization"))
        #
        # Item của Optimize
        # Item trong box Design Variable kind
        self.label_dvkind.setText("Design Variable kind:")  # Tên box
        self.dvkind.setItemText(0, _translate("group", "HICKS_HENNE"))
        self.dvkind.setItemText(1, _translate("group", "FFD_SETTING"))
        #
        # Số lượng Design Variable
        self.label_dvnumber.setText("DV Number (even number):")  # Tên box
        #
        # Item trong box Optimization objective
        self.label_opt_object.setText("Optimization objective:")  # Tên box
        self.opt_object.setItemText(0, _translate("group", "LIFT"))
        self.opt_object.setItemText(1, _translate("group", "DRAG"))
        #
        # Item trong box Optimization constraint
        self.label_opt_const_type.setText(
            "Optimization constraint:")  # Tên box
        # Có chọn Optimization constraint hay không ?
        self.opt_const_type.addItems(["NONE", "Select value"])
        # Multi-select Optimization constraint
        self.opt_const_list.addItems(
            ["LIFT", "DRAG", "MOMENT_Z", "AIRFOIL_THICKNESS"])
        #
        # Nút Run Optimize
        self.optimize_button.setText("OPTIMIZE")

        # Box optimize (end) =====================================================


        # Danh sách các airfoil có sẵn
        airfoils = ["NACA 0012", "NACA 2412", "NACA 63206", "NACA 63209"]

        # Tạo completer và gán vào QLineEdit
        completer = QCompleter(airfoils)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)  # Không phân biệt hoa/thường
        self.type_line.setCompleter(completer)

    def inform_success(self): #Box thông báo sau khi hoàn thành
        msg=QtWidgets.QMessageBox()
        msg.setWindowFlags(msg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        msg.setInformativeText('Success!')
        msg.exec()

    def inform_failed(self): #Box thông báo sau khi hoàn thành
        msg=QtWidgets.QMessageBox()
        msg.setWindowFlags(msg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        msg.setInformativeText('Failed!')
        msg.exec()
        
    def airfoil_type(self, group): #Chọn loại airfoil
        if group == "NACA 4 digit":
            self.type.show()
            self.type.clear()
            self.type_line.hide()
            self.type.addItems(["NACA 0012", "NACA 2412"])
        elif group == "NACA 5 digit":
            self.type.show()
            self.type.clear()
            self.type_line.hide()
            self.type.addItems(["NACA 63206", "NACA 63209"])
        elif group == "Others":
            self.type.hide()
            self.type_line.show()
            # Danh sách các airfoil có sẵn có trong database
            airfoils = ["NACA 0010", "NACA 2345", "NACA JQKA", "NACA 6868"]
            # Tạo completer và gán vào QLineEdit
            completer = QCompleter(airfoils)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)  # Không phân biệt hoa/thường
            self.type_line.setCompleter(completer)
    
    def airfoil(self): #Generate and post-processing mesh
        self.gen=MeshGenerator(group=self.type_of_naca.currentText(), type=self.type.currentText(), mesh_type=self.update_mesh())
        self.gen.mesh_generated.connect(self.on_mesh_generated) #Transmit mesh file data
        self.gen.start()
        self.gen.finished.connect(self.inform_success)
        self.gen.finished.connect(lambda: self.progress.hide())
        self.gen.finished.connect(lambda: self.tabs.setCurrentIndex(0)) 
        self.gen.finished.connect(lambda: self.tab1.show_mesh(data=self.data["mesh_vtk"], code=''.join(re.findall(r'\d+', self.type.currentText()))))
    def on_mesh_generated(self, data): #Create plug for data from mesh_generated 
        self.data=data

    def sim(self): #Run simulation
        code=MeshGenerator.naca_code(group=self.type_of_naca.currentText(),type=self.type.currentText())
        mesh_path = os.path.join(f'NACA_{code}', f"mesh_airfoil_{code}.su2" ) 
        self.run=Init(solver=self.solver.currentText(),mach=self.mach.text(),aoa=self.aoa.text(),temperature=self.temp.text(),pressure=self.pressure.text(), mesh_path=mesh_path, folder_name=f'NACA_{code}')
        self.run.start()
        self.run.finished.connect(self.inform_success)  
        self.run.finished.connect(lambda: self.progress.hide())
        self.run.finished.connect(lambda: self.tabs.setCurrentIndex(1)) 
        self.run.finished.connect(self.show)
    def show(self):
        code=MeshGenerator.naca_code(group=self.type_of_naca.currentText(),type=self.type.currentText())
        file_path = os.path.join(f'NACA_{code}', 'flow.vtu')
        if not os.path.exists(file_path):
            self.inform_failed()
            return  # dừng luôn nếu không có file
        try:
            self.tab2.show(
            data=file_path,
            field=self.field.currentText(),
            dim=self.dimension(),
            code=''.join(re.findall(r'\d+', self.type.currentText()))
        )
        except Exception as e:
            print(f"Lỗi khi hiển thị dữ liệu: {e}")
            self.inform_failed()

    def dimension(self):
        if self.field.currentText() == "Pressure":
            self.dim = "Pa"
        elif self.field.currentText() == "Temperature":
            self.dim = "K"
        elif self.field.currentText() == "Velocity":
            self.dim = "m/s"
        return self.dim

    def residuals(self): #Plot đồ thị thể hiện tiến trình hội tụ 
        code=MeshGenerator.naca_code(group=self.type_of_naca.currentText(),type=self.type.currentText())
        self.tab3.plot(history_file_path=os.path.join(f'NACA_{code}', 'history.csv'))      

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
        # Gán thuộc tính để dùng chung
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
        self.opt_thread.inform.connect(self.inform_success)  # hiện popup Success!
        self.opt_thread.finished.connect(lambda:self.statusbar.showMessage("Optimization complete"))
        self.opt_thread.finished.connect(lambda:self.progress.hide())
        # Hiển thị progress bar nếu muốn
        self.progress_bar()

        # 5) Bắt đầu thread
        self.opt_thread.start()
        #cfg_path = self.opt_thread.initial_conditions()
        #QtWidgets.QMessageBox.information(
        #    self.optimize,
        #    "Config Generated",
        #    f"Config file has been created at:\n{cfg_path}"
        #)
        #return

    # Box optimize (end) ========================================================                  
 
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    group = QtWidgets.QMainWindow()
    # Tab Optimize ===============================================================
    for name in [
        'update_display_list', 'update_display_area', 'update_setting_buttons_visibility',
        'on_designs_dir_changed', 'update_comp_dsn_checkboxes', 'update_resid_list',
        'update_comp_list', 'filter_comp_checks',
        '_on_flow_airfoil_changed', '_on_flow_field_changed',
        'create_airfoil_comparison_panel', 'create_residual_panel',
        '_on_residuals_dir_changed' 
    ]:
        setattr(Ui_group, name, getattr(opt_tab_support, name))
    # Tab Optimize (end) =========================================================
    for name in ['toggle_constraint_list', 'run_optimization']: setattr(Ui_group, name, getattr(run_optimize, name)) # Optimize khởi chạy
    ui = Ui_group()
    ui.setupUi(group)
    group.show()
    sys.exit(app.exec())
