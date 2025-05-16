import os
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

class Init(QThread):
    inform=pyqtSignal(str)
    def __init__(self,mesh_path,folder_name,solver,mach,aoa,temperature,pressure,dyn_viscosity,Re,ref_length,turb_kind,flow):
        super().__init__()
        self.mesh_path=mesh_path
        self.folder_name=folder_name
        self.solver=solver
        self.mach=mach
        self.aoa=aoa
        self.temperature=temperature
        self.pressure=pressure
        self.dyn_viscosity=dyn_viscosity
        self.Re=Re
        self.config_path=os.path.join(self.folder_name,'config.cfg')
        self.mesh_su2 = os.path.basename(self.mesh_path) #get file mesh.su2
        self.config_file=os.path.basename(self.config_path) #get file config
        self.ref_length=ref_length
        self.turb_kind=turb_kind
        self.flow=flow

    def run(self):
        self.initial_conditions()

    def initial_conditions(self):
        if self.flow == 'Inviscid Flow':
            with open(self.config_path,'w') as f:
                f.write(f"""
% ------------- DIRECT, ADJOINT, AND LINEARIZED PROBLEM DEFINITION ------------%
%
% Physical governing equations (EULER, NAVIER_STOKES,
%                               WAVE_EQUATION, HEAT_EQUATION, FEM_ELASTICITY,
%                               POISSON_EQUATION)
SOLVER= {self.solver}
%
% Mathematical problem (DIRECT, CONTINUOUS_ADJOINT)
MATH_PROBLEM= DIRECT
%
% Restart solution (NO, YES)
RESTART_SOL= NO

% ----------- COMPRESSIBLE AND INCOMPRESSIBLE FREE-STREAM DEFINITION ----------%
%
% Mach number (non-dimensional, based on the free-stream values)
MACH_NUMBER= {self.mach}
%
% Angle of attack (degrees)
AOA= {self.aoa}
%
% Free-stream pressure (101325.0 N/m^2 by default, only Euler flows)
FREESTREAM_PRESSURE= {self.pressure}
%
% Free-stream temperature (273.15 K by default)
FREESTREAM_TEMPERATURE= {self.temperature}

% -------------- COMPRESSIBLE AND INCOMPRESSIBLE FLUID CONSTANTS --------------%
%
% Ratio of specific heats (1.4 (air), only for compressible flows)
GAMMA_VALUE= 1.4
%
% Specific gas constant (287.87 J/kg*K (air), only for compressible flows)
GAS_CONSTANT= 287.87

% ---------------------- REFERENCE VALUE DEFINITION ---------------------------%
%
% Reference origin for moment computation
REF_ORIGIN_MOMENT_X = 0.25
REF_ORIGIN_MOMENT_Y = 0.00
REF_ORIGIN_MOMENT_Z = 0.00
%
% Reference length for pitching, rolling, and yawing non-dimensional moment
REF_LENGTH= 1.0
%
% Reference area for force coefficients (0 implies automatic calculation)
REF_AREA= 1.0
%
% Flow non-dimensionalization (DIMENSIONAL, FREESTREAM_PRESS_EQ_ONE,
%                              FREESTREAM_VEL_EQ_MACH, FREESTREAM_VEL_EQ_ONE)
REF_DIMENSIONALIZATION= DIMENSIONAL

% ----------------------- BOUNDARY CONDITION DEFINITION -----------------------%
%
% Marker of the Euler boundary (NONE = no marker)
MARKER_EULER= ( airfoil )
%
% Marker of the far field (NONE = no marker)
MARKER_FAR= ( farfield )

% ------------------------ SURFACES IDENTIFICATION ----------------------------%
%
% Marker(s) of the surface in the surface flow solution file
MARKER_PLOTTING = ( airfoil )
%
% Marker(s) of the surface where the non-dimensional coefficients are evaluated.
MARKER_MONITORING = ( airfoil )
%
% Marker(s) of the surface where obj. func. (design problem) will be evaluated
MARKER_DESIGNING = ( airfoil )

% ------------- COMMON PARAMETERS TO DEFINE THE NUMERICAL METHOD --------------%
%
% Numerical method for spatial gradients (GREEN_GAUSS, WEIGHTED_LEAST_SQUARES)
NUM_METHOD_GRAD= WEIGHTED_LEAST_SQUARES
%
% Objective function in optimization problem (DRAG, LIFT, SIDEFORCE, MOMENT_X,
%                                             MOMENT_Y, MOMENT_Z, EFFICIENCY,
%                                             EQUIVALENT_AREA, NEARFIELD_PRESSURE,
%                                             FORCE_X, FORCE_Y, FORCE_Z, THRUST,
%                                             TORQUE, FREE_SURFACE, TOTAL_HEATFLUX,
%                                             MAXIMUM_HEATFLUX, INVERSE_DESIGN_PRESSURE,
%                                             INVERSE_DESIGN_HEATFLUX)
OBJECTIVE_FUNCTION= DRAG
%
% Courant-Friedrichs-Lewy condition of the finest grid
CFL_NUMBER= 1e3
%
% Adaptive CFL number (NO, YES)
CFL_ADAPT= NO
%
% Parameters of the adaptive CFL number (factor down, factor up, CFL min value,
%                                        CFL max value )
CFL_ADAPT_PARAM= ( 0.1, 2.0, 10.0, 1e10 )
%
% Number of total iterations
ITER= 250

% ------------------------ LINEAR SOLVER DEFINITION ---------------------------%
%
% Linear solver for implicit formulations (BCGSTAB, FGMRES)
LINEAR_SOLVER= FGMRES
%
% Preconditioner of the Krylov linear solver (JACOBI, LINELET, LU_SGS)
LINEAR_SOLVER_PREC= ILU
%
% Minimum error of the linear solver for implicit formulations
LINEAR_SOLVER_ERROR= 1E-10
%
% Max number of iterations of the linear solver for the implicit formulation
LINEAR_SOLVER_ITER= 10

% -------------------------- MULTIGRID PARAMETERS -----------------------------%
%
% Multi-Grid Levels (0 = no multi-grid)
MGLEVEL= 3
%
% Multi-grid cycle (V_CYCLE, W_CYCLE, FULLMG_CYCLE)
MGCYCLE= W_CYCLE
%
% Multi-Grid PreSmoothing Level
MG_PRE_SMOOTH= ( 1, 2, 3, 3 )
%
% Multi-Grid PostSmoothing Level
MG_POST_SMOOTH= ( 0, 0, 0, 0 )
%
% Jacobi implicit smoothing of the correction
MG_CORRECTION_SMOOTH= ( 0, 0, 0, 0 )
%
% Damping factor for the residual restriction
MG_DAMP_RESTRICTION= 1.0
%
% Damping factor for the correction prolongation
MG_DAMP_PROLONGATION= 1.0

% -------------------- FLOW NUMERICAL METHOD DEFINITION -----------------------%
%
% Convective numerical method
%
CONV_NUM_METHOD_FLOW= JST
%
% 2nd and 4th order artificial dissipation coefficients
JST_SENSOR_COEFF= ( 0.5, 0.02 )
%
% Time discretization (RUNGE-KUTTA_EXPLICIT, EULER_IMPLICIT, EULER_EXPLICIT)
TIME_DISCRE_FLOW= EULER_IMPLICIT

% ---------------- ADJOINT-FLOW NUMERICAL METHOD DEFINITION -------------------%
%
% Convective numerical method (JST, LAX-FRIEDRICH, ROE)
CONV_NUM_METHOD_ADJFLOW= JST
%
% Reduction factor of the CFL coefficient in the adjoint problem
CFL_REDUCTION_ADJFLOW= 0.01
%
% Time discretization (RUNGE-KUTTA_EXPLICIT, EULER_IMPLICIT)
TIME_DISCRE_ADJFLOW= EULER_IMPLICIT
% ------------------------- INPUT/OUTPUT INFORMATION --------------------------%
% Mesh input file
MESH_FILENAME= {self.mesh_su2}
%
% Mesh input file format (SU2, CGNS, NETCDF_ASCII)
MESH_FORMAT= SU2
%
% Mesh output file
MESH_OUT_FILENAME= mesh_out.su2
%
% Restart flow input file
SOLUTION_FILENAME= solution_flow.dat
%
% Restart adjoint input file
SOLUTION_ADJ_FILENAME= solution_adj.dat
%
% Output file format (TECPLOT, CSV)
TABULAR_FORMAT= CSV
%
% Output file convergence history (w/o extension)
CONV_FILENAME= history
%
% Output file restart flow
RESTART_FILENAME= restart_flow.dat
%
% Output file restart adjoint
RESTART_ADJ_FILENAME= restart_adj.dat
%
% Output file flow (w/o extension) variables
VOLUME_FILENAME= flow
%
% Output file adjoint (w/o extension) variables
VOLUME_ADJ_FILENAME= adjoint
%
% Output Objective function gradient (using continuous adjoint)
GRAD_OBJFUNC_FILENAME= of_grad.dat
%
% Output file surface flow coefficient (w/o extension)
SURFACE_FILENAME= surface_flow
%
% Output file surface adjoint coefficient (w/o extension)
SURFACE_ADJ_FILENAME= surface_adjoint
%
% Writing solution file frequency
OUTPUT_WRT_FREQ= 250
%
% Output file format
OUTPUT_FILES= (RESTART, PARAVIEW, SURFACE_CSV)
""")    
            subprocess.run(['SU2_CFD', self.config_file], check=True, cwd=self.folder_name)
        elif self.flow == 'Viscous Flow':
            with open(self.config_path,'w') as f:
                f.write(f"""
% ------------- DIRECT, ADJOINT, AND LINEARIZED PROBLEM DEFINITION ------------%
%
% Physical governing equations (EULER, NAVIER_STOKES,
%                               WAVE_EQUATION, HEAT_EQUATION, FEM_ELASTICITY,
%                               POISSON_EQUATION)          
SOLVER= {self.solver}
%
% Specify turbulence model (NONE, SA, SA_NEG, SST)
KIND_TURB_MODEL= {self.turb_kind}
%
% Mathematical problem (DIRECT, CONTINUOUS_ADJOINT)
MATH_PROBLEM= DIRECT
%
% Restart solution (NO, YES)
RESTART_SOL= NO

% -------------------- COMPRESSIBLE FREE-STREAM DEFINITION --------------------%
%
% Mach number (non-dimensional, based on the free-stream values)
MACH_NUMBER= {self.mach}
%
% Angle of attack (degrees, only for compressible flows)
AOA= {self.aoa}
%
% Side-slip angle (degrees, only for compressible flows)
SIDESLIP_ANGLE= 0.0
%
% Init option to choose between Reynolds (default) or thermodynamics quantities
% for initializing the solution (REYNOLDS, TD_CONDITIONS)
INIT_OPTION= REYNOLDS
%
% Free-stream option to choose between density and temperature (default) for
% initializing the solution (TEMPERATURE_FS, DENSITY_FS)
FREESTREAM_OPTION= TEMPERATURE_FS
%
% Free-stream temperature (288.15 K by default)
FREESTREAM_TEMPERATURE= 288.15
%
% Reynolds number (non-dimensional, based on the free-stream values)
REYNOLDS_NUMBER= {self.Re}
%
% Reynolds length (1 m by default)
REYNOLDS_LENGTH= {self.ref_length}

% ---- IDEAL GAS, POLYTROPIC, VAN DER WAALS AND PENG ROBINSON CONSTANTS -------%
%
% Different gas model (STANDARD_AIR, IDEAL_GAS, VW_GAS, PR_GAS)
FLUID_MODEL= STANDARD_AIR
%
% Ratio of specific heats (1.4 default and the value is hardcoded
%                          for the model STANDARD_AIR)
GAMMA_VALUE= 1.4
%
% Specific gas constant (287.058 J/kg*K default and this value is hardcoded 
%                        for the model STANDARD_AIR)
GAS_CONSTANT= 287.058

% --------------------------- VISCOSITY MODEL ---------------------------------%
%
% Viscosity model (SUTHERLAND, CONSTANT_VISCOSITY, POLYNOMIAL_VISCOSITY, FLAMELET).
VISCOSITY_MODEL= CONSTANT_VISCOSITY
%
% Molecular Viscosity that would be constant (1.716E-5 by default)
MU_CONSTANT= {self.dyn_viscosity}

% --------------------------- THERMAL CONDUCTIVITY MODEL ----------------------%
%
% Conductivity model (CONSTANT_CONDUCTIVITY, CONSTANT_PRANDTL).
CONDUCTIVITY_MODEL= CONSTANT_PRANDTL
%
% Laminar Prandtl number (0.72 (air), only for CONSTANT_PRANDTL)
PRANDTL_LAM= 0.72
%
% Turbulent Prandtl number (0.9 (air), only for CONSTANT_PRANDTL)
PRANDTL_TURB= 0.90

% ---------------------- REFERENCE VALUE DEFINITION ---------------------------%
%
% Reference origin for moment computation
REF_ORIGIN_MOMENT_X = 0.25
REF_ORIGIN_MOMENT_Y = 0.00
REF_ORIGIN_MOMENT_Z = 0.00
%
% Reference length for pitching, rolling, and yawing non-dimensional moment
REF_LENGTH= 0.64607
%
% Reference area for force coefficients (0 implies automatic calculation)
REF_AREA= 0
%
% Compressible flow non-dimensionalization (DIMENSIONAL, FREESTREAM_PRESS_EQ_ONE,
%                              FREESTREAM_VEL_EQ_MACH, FREESTREAM_VEL_EQ_ONE)
REF_DIMENSIONALIZATION= FREESTREAM_VEL_EQ_ONE

% ----------------------- BOUNDARY CONDITION DEFINITION -----------------------%
%
% Marker of the Euler boundary (NONE = no marker)
MARKER_EULER= ( airfoil )
%
% Marker of the far field (NONE = no marker)
MARKER_FAR= ( farfield )

% ------------- COMMON PARAMETERS DEFINING THE NUMERICAL METHOD ---------------%
%
% Numerical method for spatial gradients (GREEN_GAUSS, WEIGHTED_LEAST_SQUARES)
NUM_METHOD_GRAD= GREEN_GAUSS
%
% Courant-Friedrichs-Lewy condition of the finest grid
CFL_NUMBER= 100.0
%
% Adaptive CFL number (NO, YES)
CFL_ADAPT= NO
%
% Parameters of the adaptive CFL number (factor down, factor up, CFL min value,
%                                        CFL max value )
CFL_ADAPT_PARAM= ( 1.5, 0.5, 25.0, 100000.0 )
%
% Runge-Kutta alpha coefficients
RK_ALPHA_COEFF= ( 0.66667, 0.66667, 1.000000 )
%
% Number of total iterations
ITER= 999999

% ------------------------ LINEAR SOLVER DEFINITION ---------------------------%
%
% Linear solver for the implicit (or discrete adjoint) formulation (BCGSTAB, FGMRES)
LINEAR_SOLVER= FGMRES
%
% Preconditioner of the Krylov linear solver (NONE, JACOBI, LINELET)
LINEAR_SOLVER_PREC= ILU
%
% Min error of the linear solver for the implicit formulation
LINEAR_SOLVER_ERROR= 1E-10
%
% Max number of iterations of the linear solver for the implicit formulation
LINEAR_SOLVER_ITER= 10

% -------------------------- MULTIGRID PARAMETERS -----------------------------%
%
% Multi-Grid Levels (0 = no multi-grid)
MGLEVEL= 0
%
% Multi-grid cycle (V_CYCLE, W_CYCLE, FULLMG_CYCLE)
MGCYCLE= V_CYCLE
%
% Multi-grid pre-smoothing level
MG_PRE_SMOOTH= ( 1, 1, 1, 1 )
%
% Multi-grid post-smoothing level
MG_POST_SMOOTH= ( 0, 0, 0, 0 )
%
% Jacobi implicit smoothing of the correction
MG_CORRECTION_SMOOTH= ( 0, 0, 0, 0 )
%
% Damping factor for the residual restriction
MG_DAMP_RESTRICTION= 0.7
%
% Damping factor for the correction prolongation
MG_DAMP_PROLONGATION= 0.7

% -------------------- FLOW NUMERICAL METHOD DEFINITION -----------------------%
%
% Convective numerical method
CONV_NUM_METHOD_FLOW= JST
%
% 2nd and 4th order artificial dissipation coefficients for
%     the JST method ( 0.5, 0.02 by default )
JST_SENSOR_COEFF= ( 0.5, 0.02 )
%
% Time discretization (RUNGE-KUTTA_EXPLICIT, EULER_IMPLICIT, EULER_EXPLICIT)
TIME_DISCRE_FLOW= EULER_IMPLICIT

% -------------------- TURBULENT NUMERICAL METHOD DEFINITION ------------------%
%
% Convective numerical method (SCALAR_UPWIND)
CONV_NUM_METHOD_TURB= SCALAR_UPWIND
%
% Monotonic Upwind Scheme for Conservation Laws (TVD) in the turbulence equations.
%           Required for 2nd order upwind schemes (NO, YES)
MUSCL_TURB= NO
%
% Slope limiter (VENKATAKRISHNAN, MINMOD)
SLOPE_LIMITER_TURB= VENKATAKRISHNAN
%
% Time discretization (EULER_IMPLICIT)
TIME_DISCRE_TURB= EULER_IMPLICIT

% --------------------------- CONVERGENCE PARAMETERS --------------------------%
%
% Convergence criteria (CAUCHY, RESIDUAL)
CONV_FIELD= DRAG
%
% Start convergence criteria at iteration number
CONV_STARTITER= 10
%
% Number of elements to apply the criteria
CONV_CAUCHY_ELEMS= 100
%
% Epsilon to control the series convergence
CONV_CAUCHY_EPS= 1E-6
%

% ------------------------- INPUT/OUTPUT INFORMATION --------------------------%
%
% Mesh input file
MESH_FILENAME= {self.mesh_su2}
%
% Mesh input file format (SU2, CGNS, NETCDF_ASCII)
MESH_FORMAT= SU2
%
% Mesh output file
MESH_OUT_FILENAME= mesh_out.su2
%
% Restart flow input file
SOLUTION_FILENAME= solution_flow.dat
%
% Restart adjoint input file
SOLUTION_ADJ_FILENAME= solution_adj.dat
%
% Output file format (PARAVIEW, TECPLOT, STL)
TABULAR_FORMAT= CSV
%
% Output file convergence history (w/o extension) 
CONV_FILENAME= history
%
% Output file restart flow
RESTART_FILENAME= restart_flow.dat
%
% Output file restart adjoint
RESTART_ADJ_FILENAME= restart_adj.dat
%
% Output file flow (w/o extension) variables
VOLUME_FILENAME= flow
%
% Output file adjoint (w/o extension) variables
VOLUME_ADJ_FILENAME= adjoint
%
% Output objective function gradient (using continuous adjoint)
GRAD_OBJFUNC_FILENAME= of_grad.dat
%
% Output file surface flow coefficient (w/o extension)
SURFACE_FILENAME= surface_flow
%
% Output file surface adjoint coefficient (w/o extension)
SURFACE_ADJ_FILENAME= surface_adjoint
%
%
% Screen output
SCREEN_OUTPUT= (INNER_ITER, WALL_TIME, RMS_DENSITY, RMS_NU_TILDE, LIFT, DRAG)
""")
            subprocess.run(['SU2_CFD', self.config_file], check=True, cwd=self.folder_name)
