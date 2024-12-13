import os
import subprocess
from PyQt6 import QtWidgets

class Init():

    def initial_conditions(solver,mach,aoa,temperature,pressure,mesh_path,folder_name):
        config_path=os.path.join(folder_name,'config.cfg')
        result_path=os.path.join(folder_name,'flow.vtu')
        mesh_su2 = os.path.basename(mesh_path) #get file mesh.su2
        config_file=os.path.basename(config_path) #get file config
        if not os.path.exists(config_path):
            with open(config_path,'w') as f:
               f.write(f"""
SOLVER={solver}
MATH_PROBLEM= DIRECT
RESTART_SOL= NO
MACH_NUMBER={mach}
AOA={aoa} 
SIDESLIP_ANGLE= 0.0
FREESTREAM_PRESSURE={pressure} 
FREESTREAM_TEMPERATURE={temperature} 
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
MESH_FILENAME= {mesh_su2}
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
OPT_OBJECTIVE= DRAG * 0.001
OPT_CONSTRAINT= ( LIFT > 0.328188 ) * 0.001; ( MOMENT_Z > 0.034068 ) * 0.001; ( AIRFOIL_THICKNESS > 0.11 ) * 0.001
DEFINITION_DV= ( 30, 1.0 | airfoil | 0, 0.05 ); ( 30, 1.0 | airfoil | 0, 0.10 ); ( 30, 1.0 | airfoil | 0, 0.15 ); ( 30, 1.0 | airfoil | 0, 0.20 ); ( 30, 1.0 | airfoil | 0, 0.25 ); ( 30, 1.0 | airfoil | 0, 0.30 ); ( 30, 1.0 | airfoil | 0, 0.35 ); ( 30, 1.0 | airfoil | 0, 0.40 ); ( 30, 1.0 | airfoil | 0, 0.45 ); ( 30, 1.0 | airfoil | 0, 0.50 ); ( 30, 1.0 | airfoil | 0, 0.55 ); ( 30, 1.0 | airfoil | 0, 0.60 ); ( 30, 1.0 | airfoil | 0, 0.65 ); ( 30, 1.0 | airfoil | 0, 0.70 ); ( 30, 1.0 | airfoil | 0, 0.75 ); ( 30, 1.0 | airfoil | 0, 0.80 ); ( 30, 1.0 | airfoil | 0, 0.85 ); ( 30, 1.0 | airfoil | 0, 0.90 ); ( 30, 1.0 | airfoil | 0, 0.95 ); ( 30, 1.0 | airfoil | 1, 0.05 ); ( 30, 1.0 | airfoil | 1, 0.10 ); ( 30, 1.0 | airfoil | 1, 0.15 ); ( 30, 1.0 | airfoil | 1, 0.20 ); ( 30, 1.0 | airfoil | 1, 0.25 ); ( 30, 1.0 | airfoil | 1, 0.30 ); ( 30, 1.0 | airfoil | 1, 0.35 ); ( 30, 1.0 | airfoil | 1, 0.40 ); ( 30, 1.0 | airfoil | 1, 0.45 ); ( 30, 1.0 | airfoil | 1, 0.50 ); ( 30, 1.0 | airfoil | 1, 0.55 ); ( 30, 1.0 | airfoil | 1, 0.60 ); ( 30, 1.0 | airfoil | 1, 0.65 ); ( 30, 1.0 | airfoil | 1, 0.70 ); ( 30, 1.0 | airfoil | 1, 0.75 ); ( 30, 1.0 | airfoil | 1, 0.80 ); ( 30, 1.0 | airfoil | 1, 0.85 ); ( 30, 1.0 | airfoil | 1, 0.90 ); ( 30, 1.0 | airfoil | 1, 0.95 )
                            """)    
                          
        subprocess.run(['SU2_CFD', config_file],check=True,cwd=folder_name) #run su2
