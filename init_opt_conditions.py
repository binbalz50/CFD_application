import os
import subprocess
import sys
from PyQt6.QtCore import QThread, pyqtSignal
from extract_constrain import extract_constraints # Nhận giá trị constrain thu được từ extract_constrain.py

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

        # chuẩn bị các biến chứa giá trị
        self.constrain_thickness = None
        self.constrain_cd        = None
        self.constrain_cl        = None
        self.constrain_cmz       = None
        self.constrain_aoa       = None

        self.opt_const_str   = ""
        self.cl_driver_definition = "%"


        self.solver          = solver
        self.opt_iterations  = opt_iterations
        self.opt_accuracy    = opt_accuracy
        self.opt_bound_upper = opt_bound_upper
        self.opt_bound_lower = opt_bound_lower

        # Đường dẫn đến file config_opt.cfg
        self.config_path     = os.path.join(self.folder_name, 'config_opt.cfg')
        
        # Lấy giá trị OPT_CONSTRAINT nếu người dùng yêu cầu ===================
    def parse_constraints(self):
        """
        1) Gọi extract_constraints → unpack 5 giá trị float
        2) Gán vào self.constrain_*
        3) Build self.opt_const_str & self.cl_driver_definition
        """
        # 1) Lấy 5 giá trị constrain từ extract_constrain.py về
        thickness, cd, cl, cmz, aoa = extract_constraints(
            self.folder_name,
            self.mesh_su2
        )

        # 2) Gán vào thuộc tính (Để tạm, có thể cần dùng Ko thì có thể xóa đi)
        self.constrain_thickness = thickness
        self.constrain_cd        = cd
        self.constrain_cl        = cl
        self.constrain_cmz       = cmz
        self.constrain_aoa       = aoa

        # 3) lưu vào dict chung
        self.constraint_results = {
            'AIRFOIL_THICKNESS': thickness,
            'DRAG':               cd,
            'LIFT':               cl,
            'MOMENT_Z':           cmz,
            'AOA':                aoa
        }

        # 3) Build OPT_CONSTRAINT dựa trên opt_const_list
        if self.opt_const_type.upper() == 'NONE' or not self.opt_const_list: # Nếu không có constrain thì để opt_const_str là NONE
            self.opt_const_str = 'NONE'
        else:
            parts = [] # List rỗng để gom các điều kiện
            for var in self.opt_const_list:
                if var == 'LIFT':
                    continue # Bỏ qua biến LIFT trong opt_const_list đẩy sang CL DRIVER xử lý
                val = self.constraint_results.get(var)
                if val is None:
                    continue # Bỏ qua nếu val không có (Không có giá trị ở trong biến var tương ứng)
                op = '>' if var == 'AIRFOIL_THICKNESS' else '<' # Với AIRFOIL_THICKNESS thì luôn > một giá trị (Ko mỏng quá), còn lại phải < một giá trị
                parts.append(f"( {var} {op} {val} ) * 0.001") # Tạo điều kiện
            self.opt_const_str = ' ; '.join(parts) if parts else 'NONE' # Ghép các điều kiện lại với nhau (Nếu không có điều kiện nào có giá trị thì trả về NONE)

        # 4) Tạo khối CL DRIVER nếu người dùng chọn constrain LIFT
        if 'LIFT' in self.opt_const_list and self.constraint_results.get('LIFT') is not None:
            target_cl = self.constraint_results['LIFT']
            self.cl_driver_definition = (
                "% -------------------------- CL DRIVER DEFINITION -----------------------------%\n"
                "FIXED_CL_MODE= YES\n"
                f"TARGET_CL= {target_cl}\n"
                "DCL_DALPHA= 0.2\n"
                "UPDATE_AOA_ITER_LIMIT= 100\n"
                "ITER_DCL_DALPHA= 500\n"
                "EVAL_DOF_DCX= NO\n"
                "%\n"
            )
        else:
            self.cl_driver_definition = '%'
        # Lấy giá trị OPT_CONSTRAINT nếu người dùng yêu cầu (end) ==============

    # Phần thiết đặt riêng cho FFD bổ sung vào format config chung ở dưới.
    def ffd_config(self) -> str:

        #FFD_DEGREE
        """
        Sinh dòng FFD_DEGREE cho cấu hình 2D:
        FFD_DEGREE= (x_degree, y_degree, 0)
        với y_degree cố định = 1
        và x_degree = (dv_number/2) - 1
        """
        # dv_number luôn chẵn
        half = self.dv_number // 2
        x_degree = half - 1
        y_degree = 1
        ffd_degree = f"FFD_DEGREE= ({x_degree}, {y_degree}, 0)"

        # Khối FREE-FORM DEFORMATION PARAMETERS
        self.ffd_param = "\n".join([
            "% -------------------- FREE-FORM DEFORMATION PARAMETERS -----------------------%",
            "FFD_TOLERANCE= 1E-10",
            "FFD_ITERATIONS= 500",
            "FFD_DEFINITION= (BOX, -0.05, -0.1, 0.0, 1.05, -0.1, 0.0, 1.05, 0.1, 0.0, -0.05, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 ,0.0, 0.0, 0.0 ,0.0)",
            "FFD_CONTINUITY= 2ND_DERIVATIVE"
        ])

        # Khối COMPRESSIBLE AND INCOMPRESSIBLE FLUID CONSTANTS
        self.fluid_constrain = "GAMMA_VALUE= 1.4\nGAS_CONSTANT= 287.87"

        return ffd_degree

    # Phần chứa các giá trị thay đổi khi lựa chọn giữa FFD và HHBF
    def ffd_vs_hhbf_config(self) -> None: # Hàm sẽ không trả về gì (None)
        """
        Thiết lập các thuộc tính sau dựa vào self.dv_kind:
          - self.dv_param        : tuple hoặc float
          - self.dv_value        : float
          - self.opt_iterations  : int
          - self.opt_bound_upper : float
          - self.opt_bound_lower : float
        """
        kind = self.dv_kind.upper()
        if kind == 'HICKS_HENNE':
            # DV_PARAM = (1, 0.5)
            self.dv_param        = (1, 0.5)
            # DV_VALUE = 1.0
            self.dv_value        = 1.0
            # OPT_ITERATIONS = 100
            self.opt_iterations  = 100
            # OPT_BOUND_UPPER = 0.1
            self.opt_bound_upper = 0.1
            # OPT_BOUND_LOWER = -0.1
            self.opt_bound_lower = -0.1
            # REF_DIMENSIONALIZATION = FREESTREAM_PRESS_EQ_ONE
            #self.ref_dimensionalization = "FREESTREAM_PRESS_EQ_ONE"
        else:  # FFD_SETTING
            # DV_PARAM = (1.0)
            self.dv_param        = (1.0)
            # DV_VALUE = 0.0
            self.dv_value        = 0.0
            # OPT_ITERATIONS = 200
            self.opt_iterations  = 200
            # OPT_BOUND_UPPER = 1e10
            self.opt_bound_upper = 1e10
            # OPT_BOUND_LOWER = -1e10
            self.opt_bound_lower = -1e10
            # REF_DIMENSIONALIZATION = DIMENSIONAL
            #self.ref_dimensionalization = "DIMENSIONAL"


    # Tạo chuỗi definition_dv của HHBF
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

    # Tạo chuỗi definition_dv của FFD
    def generate_ffd_definition_dv(
        self,
        dv_number: int,
        variable_type: int = 19,
        scale: float = 1.0,
        marker: str = "airfoil",
        box: str = "BOX",
        lower: float = 0.0,
        upper: float = 1.0,
    ) -> str:
        """
        Sinh khối DEFINITION_DV cho FFD:
        DEFINITION_DV= (variable_type, scale | marker | box, i_idx, j_idx, lower, upper);
                       …
        dv_number: tổng số biến thiết kế (chẵn)
        i_idx chạy từ 0 đến half-1, j_idx = 0 (nửa đầu), j_idx = 1 (nửa sau)
        """
        half = dv_number // 2
        entries = []
        # j = 0: nửa đầu
        for i in range(half): # Cho i chạy từ 0 tới half với j_idx = 0 trước
            entries.append(f"( {variable_type}, {scale} | {marker} | {box}, {i}, 0, {lower}, {upper} )")
        # j = 1: nửa sau
        for i in range(half): # Sau đó cho i chạy từ 0 tới half với j_idx = 1
            entries.append(f"( {variable_type}, {scale} | {marker} | {box}, {i}, 1, {lower}, {upper} )")
        # Thêm dấu chấm phẩy cho mọi entry trừ entry cuối cùng
        for idx in range(len(entries) - 1):
            entries[idx] += ";"
        # Nối thành chuỗi
        dv_block = "DEFINITION_DV= " + " ".join(entries)
        return dv_block

    def initial_conditions(self):
        # Đảm bảo thư mục output tồn tại
        os.makedirs(self.folder_name, exist_ok=True)
        # build OPT_CONSTRAINT + CL_DRIVER
        self.parse_constraints()
        # Khởi tạo các biến dv_param, dv_value, opt_iterations,… từ dv_kind
        self.ffd_vs_hhbf_config()
        # Nếu file config chưa tồn tại thì tạo mới
        if not os.path.exists(self.config_path):
            # Thêm vào file config nếu là FFD_SETTING
            if self.dv_kind.upper() == 'FFD_SETTING':
                ffd_degree = self.ffd_config()
                # Hai dòng này cho vào đây cho vui (Thực ra để nhớ ở trên đã gán rồi)
                self.ffd_param = self.ffd_param
                self.fluid_constrain = self.fluid_constrain
            else:                                           # nếu không phải FFD thì để trống
                ffd_degree = "%"
                self.ffd_param = "%"
                self.fluid_constrain = "%"
            # Chọn definition_dv sao cho đúng loại (FFD hoặc HHBF)
            if self.dv_kind.upper() == 'FFD_SETTING':
                dv_block = self.generate_ffd_definition_dv(self.dv_number)
            else:
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
{self.fluid_constrain}
%
REF_ORIGIN_MOMENT_X = 0.25
REF_ORIGIN_MOMENT_Y = 0.00
REF_ORIGIN_MOMENT_Z = 0.00
REF_LENGTH= 1.0
REF_AREA= 1.0
REF_DIMENSIONALIZATION = DIMENSIONAL
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
ITER= 3000
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
DV_KIND= {self.dv_kind}
DV_MARKER= ( airfoil )
DV_PARAM= {self.dv_param}
DV_VALUE= {self.dv_value}
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
OPT_ITERATIONS= {self.opt_iterations}
OPT_ACCURACY= 1E-10
OPT_BOUND_UPPER= {self.opt_bound_upper}
OPT_BOUND_LOWER= {self.opt_bound_lower}
{dv_block}
%
{self.cl_driver_definition}
%
{self.ffd_param}
{ffd_degree}
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

        # 3) Gọi shape_optimization.py để chạy optimize
        command = [
            sys.executable,
            script,
            '-g', 'CONTINUOUS_ADJOINT',
            '-f', cfg_name
            #python <path>\shape_optimization.py -g CONTINUOUS_ADJOINT -f <path>\config_opt.cfg
        ]
        subprocess.run(command, check=True, cwd=cwd)

        # 4) Thông báo UI
        self.inform.emit(cfg_path)