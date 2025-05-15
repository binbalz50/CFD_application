import os
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

class Init(QThread):
    inform=pyqtSignal(str)
    def __init__(self,mesh_path,folder_name,solver,mach,aoa,temperature,pressure):
        super().__init__()
        self.mesh_path=mesh_path
        self.folder_name=folder_name
        self.solver=solver
        self.mach=mach
        self.aoa=aoa
        self.temperature=temperature
        self.pressure=pressure
        self.config_path=os.path.join(self.folder_name,'config.cfg')
        self.mesh_su2 = os.path.basename(self.mesh_path) #get file mesh.su2
        self.config_file=os.path.basename(self.config_path) #get file config
    
    def run(self):
        self.initial_conditions()

    def initial_conditions(self):
        with open(self.config_path,'w') as f:
            f.write(f"""
SOLVER={self.solver}
MATH_PROBLEM= DIRECT
RESTART_SOL= NO
MACH_NUMBER={self.mach}
AOA={self.aoa} 
SIDESLIP_ANGLE= 0.0
FREESTREAM_PRESSURE={self.pressure} 
FREESTREAM_TEMPERATURE={self.temperature} 
GAMMA_VALUE= 1.4
GAS_CONSTANT= 287.87
REF_ORIGIN_MOMENT_X = 0.25
REF_ORIGIN_MOMENT_Y = 0.00
REF_ORIGIN_MOMENT_Z = 0.00
REF_LENGTH= 1.0
REF_AREA= 1.0
REF_DIMENSIONALIZATION= DIMENSIONAL
MARKER_EULER= ( airfoil )
MARKER_FAR= ( farfield )
MARKER_PLOTTING = ( airfoil )
MARKER_MONITORING = ( airfoil )
MARKER_DESIGNING = ( airfoil )
NUM_METHOD_GRAD= WEIGHTED_LEAST_SQUARES
OBJECTIVE_FUNCTION= DRAG
CFL_NUMBER= 1e3
CFL_ADAPT= NO
CFL_ADAPT_PARAM= ( 0.1, 2.0, 10.0, 1e10 )
ITER= 250
LINEAR_SOLVER= FGMRES
LINEAR_SOLVER_PREC= ILU
LINEAR_SOLVER_ERROR= 1E-10
LINEAR_SOLVER_ITER= 10
MGLEVEL= 3
MGCYCLE= W_CYCLE
MG_PRE_SMOOTH= ( 1, 2, 3, 3 )
MG_POST_SMOOTH= ( 0, 0, 0, 0 )
MG_CORRECTION_SMOOTH= ( 0, 0, 0, 0 )
MG_DAMP_RESTRICTION= 1.0
MG_DAMP_PROLONGATION= 1.0
CONV_NUM_METHOD_FLOW= JST
JST_SENSOR_COEFF= ( 0.5, 0.02 )
TIME_DISCRE_FLOW= EULER_IMPLICIT
CONV_NUM_METHOD_ADJFLOW= JST
CFL_REDUCTION_ADJFLOW= 0.01
TIME_DISCRE_ADJFLOW= EULER_IMPLICIT
DV_KIND= HICKS_HENNE
DV_MARKER= ( airfoil )
DV_PARAM= ( 1, 0.5 )
DV_VALUE= 0.01
DEFORM_LINEAR_SOLVER_ITER= 500
DEFORM_NONLINEAR_ITER= 1
DEFORM_LINEAR_SOLVER_ERROR= 1E-14
DEFORM_CONSOLE_OUTPUT= YES
DEFORM_STIFFNESS_TYPE= INVERSE_VOLUME
CONV_FIELD= RMS_DENSITY
CONV_RESIDUAL_MINVAL= -8
CONV_STARTITER= 10
CONV_CAUCHY_ELEMS= 100
CONV_CAUCHY_EPS= 1E-6
SCREEN_OUTPUT=(INNER_ITER, WALL_TIME, RMS_RES, LIFT, DRAG, CAUCHY_SENS_PRESS, CAUCHY_DRAG RMS_ADJ_DENSITY RMS_ADJ_ENERGY)
HISTORY_OUTPUT= (INNER_ITER, RMS_DENSITY, RMS_ENERGY, LIFT, DRAG, MOMENT_Z, THICKNESS, AOA)
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
OUTPUT_WRT_FREQ= 250
OUTPUT_FILES= (RESTART, PARAVIEW, SURFACE_CSV)
""")    
        subprocess.run(['SU2_CFD', self.config_file], check=True, cwd=self.folder_name)
