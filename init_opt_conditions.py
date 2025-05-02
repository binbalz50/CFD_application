import os
import subprocess
import sys
from PyQt6.QtCore import QThread, pyqtSignal

class OptInit(QThread):
    inform = pyqtSignal(str)

    def __init__(
        self,
        mesh_path: str,
        folder_name: str,
        mach: str,
        aoa: str,
        temperature: str,
        pressure: str,
        dv_kind: str,            # HICKS_HENNE / FFD_SETTING
        dv_number: int,          # (đã kiểm là số chẵn)
        opt_object: str,         # LIFT / DRAG
        opt_const_type: str,     # NONE / Select value
        opt_const_list: list,    # list các constraint nếu có
        solver: str,             # e.g. "EULER"
        opt_iterations: int,
        opt_accuracy: float,
        opt_bound_upper: float,
        opt_bound_lower: float
    ):
        super().__init__()

        # ——— Lưu tất cả tham số vào self ———
        self.mesh_path       = mesh_path
        self.mesh_su2        = os.path.basename(mesh_path)
        self.folder_name     = folder_name

        self.mach            = mach
        self.aoa             = aoa
        self.temperature     = temperature
        self.pressure        = pressure

        self.dv_kind         = dv_kind
        self.dv_number       = dv_number
        self.opt_object      = opt_object
        self.opt_const_type  = opt_const_type
        self.opt_const_list  = opt_const_list

        self.solver          = solver
        self.opt_iterations  = opt_iterations
        self.opt_accuracy    = opt_accuracy
        self.opt_bound_upper = opt_bound_upper
        self.opt_bound_lower = opt_bound_lower

        # Đường dẫn đến file config
        self.config_path     = os.path.join(self.folder_name, 'config_opt.cfg')
        
        # Lọc tham số cố định OPT_CONSTRAINT 
        if self.opt_const_type.upper() == "NONE":
            self.opt_const_str = "NONE"
        else:
            self.opt_const_str = "( " + " ".join(self.opt_const_list) + " )"

    def generate_hhbf_definition_dv(
        # Trả về chuỗi DEFINITION_DV cho HHBF (Hicks–Henne Bump Functions) trên cánh 2D.
        self,
        dv_number: int,             #tổng số biến thiết kế (phải là số chẵn >= 2)
        variable_type: int = 30,             #mã biến HHBF (30 với SU2 mới)
        scale: float = 1.0,         #hệ số DV_VALUE
        marker: str = "airfoil",    #tên DV_MARKER
        indent: str = "    "        #chuỗi dùng để indent cho các dòng con
    ) -> str:

        # 1) Kiểm tra đầu vào       (BỎ)
        #if dv_number < 2 or dv_number % 2 != 0:
        #    raise ValueError("dv_number phải là số chẵn và >= 2")

        # 2) Mỗi mặt (0=under, 1=upper) có half biến
        half_side = dv_number // 2

        # 3) Tính các x_location chia đều trên (0,1), tránh điểm biên
        step = 1.0 / (half_side + 1)
        x_locations = [step * i for i in range(1, half_side + 1)]

        # 4) Tạo danh sách entry theo thứ tự side=0 rồi side=1
        entries = []
        for side in (0, 1):
            for x in x_locations:
                entries.append(f"( {variable_type}, {scale} | {marker} | {side}, {x:.4f} )")

        # 5) Đánh dấu “;” cho mỗi entry trừ entry cuối
        for i in range(len(entries) - 1):
            entries[i] += ";"

        # 6) Xây dựng chuỗi với xuống dòng và indent hợp lý
        definition = "DEFINITION_DV= " + "; ".join(entry.rstrip(';') for entry in entries)

        return definition

    def initial_conditions(self):
        # Đảm bảo thư mục output tồn tại
        os.makedirs(self.folder_name, exist_ok=True)
        # Nếu file config chưa tồn tại thì tạo mới
        if not os.path.exists(self.config_path):
            # Định nghĩa dv_block là phần DEFINITION_DV tạo ra từ generate_hhbf_definition_dv
            dv_block = self.generate_hhbf_definition_dv(self.dv_number)
            with open(self.config_path, 'w') as f:                      # Còn phần OPT_CONSTRAINT phải lấy data từ mô phỏng trước nữa là xong.
                f.write(f"""%
SOLVER= EULER
MATH_PROBLEM= DIRECT
RESTART_SOL= YES
%
MACH_NUMBER={self.mach}
AOA={self.aoa}
FREESTREAM_PRESSURE={self.pressure}
FREESTREAM_TEMPERATURE={self.temperature}
%
REF_ORIGIN_MOMENT_X = 0.25
REF_ORIGIN_MOMENT_Y = 0.00
REF_ORIGIN_MOMENT_Z = 0.00
REF_LENGTH= 1.0
REF_AREA= 1.0
REF_DIMENSIONALIZATION= FREESTREAM_PRESS_EQ_ONE
%
MARKER_EULER= ( airfoil )
MARKER_FAR= ( farfield )
%
MARKER_PLOTTING= ( airfoil )
MARKER_MONITORING= ( airfoil )
%
NUM_METHOD_GRAD= GREEN_GAUSS
CFL_NUMBER= 10.0
CFL_ADAPT= NO
CFL_ADAPT_PARAM= ( 1.5, 0.5, 1.0, 100.0 )
RK_ALPHA_COEFF= ( 0.66667, 0.66667, 1.000000 )
ITER= 1000
%
LINEAR_SOLVER= FGMRES
LINEAR_SOLVER_PREC= LU_SGS
LINEAR_SOLVER_ERROR= 1E-4
LINEAR_SOLVER_ITER= 2
%
MGLEVEL= 2
MGCYCLE= V_CYCLE
MG_PRE_SMOOTH= ( 1, 2, 3, 3 )
MG_POST_SMOOTH= ( 0, 0, 0, 0 )
MG_CORRECTION_SMOOTH= ( 0, 0, 0, 0 )
MG_DAMP_RESTRICTION= 1.0
MG_DAMP_PROLONGATION= 1.0
%
CONV_NUM_METHOD_FLOW= JST
JST_SENSOR_COEFF= ( 0.5, 0.02 )
TIME_DISCRE_FLOW= EULER_IMPLICIT
%
OBJECTIVE_FUNCTION= {self.opt_object}
CONV_NUM_METHOD_ADJFLOW= JST
ADJ_JST_SENSOR_COEFF= ( 0.0, 0.02 )
TIME_DISCRE_ADJFLOW= EULER_IMPLICIT
CFL_REDUCTION_ADJFLOW= 0.8
LIMIT_ADJFLOW= 1E6
%
GEO_MARKER= ( airfoil )
GEO_DESCRIPTION= AIRFOIL
GEO_MODE= FUNCTION
%
DV_KIND= HICKS_HENNE
DV_MARKER= ( airfoil )
DV_PARAM= ( 1, 0.5 )
DV_VALUE= 1.0
%
DEFORM_LINEAR_SOLVER_ITER= 500
DEFORM_NONLINEAR_ITER= 1
DEFORM_CONSOLE_OUTPUT= YES
DEFORM_LINEAR_SOLVER_ERROR= 1E-14
DEFORM_STIFFNESS_TYPE= INVERSE_VOLUME
%
CONV_RESIDUAL_MINVAL= -13
CONV_STARTITER= 10
CONV_CAUCHY_ELEMS= 100
CONV_CAUCHY_EPS= 1E-6
%
MESH_FILENAME= {self.mesh_su2}
MESH_FORMAT= SU2
MESH_OUT_FILENAME= mesh_out.su2
SOLUTION_FILENAME= solution_flow.dat
SOLUTION_ADJ_FILENAME= solution_adj.dat
TABULAR_FORMAT= CSV
CONV_FILENAME= history
RESTART_FILENAME= restart_flow.dat
RESTART_ADJ_FILENAME= restart_adj.dat
VOLUME_FILENAME= flow
VOLUME_ADJ_FILENAME= adjoint
GRAD_OBJFUNC_FILENAME= of_grad.dat
SURFACE_FILENAME= surface_flow
SURFACE_ADJ_FILENAME= surface_adjoint
SCREEN_OUTPUT= (INNER_ITER, RMS_DENSITY, RMS_ENERGY, LIFT, DRAG, MOMENT_Z, THICKNESS)
HISTORY_OUTPUT= (INNER_ITER, RMS_DENSITY, RMS_ENERGY, LIFT, DRAG, MOMENT_Z, THICKNESS, AOA)
OUTPUT_FILES = (RESTART, PARAVIEW, SURFACE_PARAVIEW, SURFACE_CSV)
%
OPT_OBJECTIVE= {self.opt_object}
OPT_CONSTRAINT= {self.opt_const_str}
OPT_GRADIENT_FACTOR= 1E-6
OPT_RELAX_FACTOR= 1E3
OPT_ITERATIONS= 100
OPT_ACCURACY= 1E-10
OPT_BOUND_UPPER= 0.1
OPT_BOUND_LOWER= -0.1
{dv_block}
""")
        # 3) Trả về đường dẫn file config vừa tạo
        return self.config_path

    def run(self):
        """Sinh config rồi gọi shape_optimization.py với các flags đầy đủ."""
        # 1) Sinh/ghi config và lấy path
        cfg_path = self.initial_conditions()

        # 2) Xác định script path và cwd
        project_root = os.path.dirname(os.path.abspath(__file__))
        script       = os.path.join(project_root, 'shape_optimization.py')
        cwd          = self.folder_name
        cfg_name     = os.path.basename(cfg_path)

        # 3) Gọi shape_optimization.py như chạy tay
        command = [
            sys.executable,
            script,
            '-g', 'CONTINUOUS_ADJOINT',
            '-o', 'SLSQP',
            '-f', cfg_name
        ]
        subprocess.run(command, check=True, cwd=cwd)

        # 4) Thông báo UI
        self.inform.emit(cfg_path)