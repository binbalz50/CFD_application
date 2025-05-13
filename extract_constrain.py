import os
import csv
import subprocess

def extract_constraints(folder: str, mesh: str) -> dict:
    """
    Trả về dict chứa các biến constraint:
      - AIRFOIL_THICKNESS (tính qua SU2_GEO)
      - DRAG (CD), LIFT (CL), MOMENT_Z (CMz), AOA (AoA)
    """
    results = {}

    # 1) Tính độ dày cánh qua SU2_GEO → airfoil_dimension.csv
    cfg_path   = os.path.join(folder, "geo.cfg")
    csv_thick  = os.path.join(folder, "airfoil_dimension.csv")
    cfg_content =   f"""% SU2_GEO config -- airfoil thickness
MESH_FILENAME={mesh}
MESH_FORMAT=SU2
%
MARKER_EULER=( airfoil )
MARKER_FAR=( farfield )
%
GEO_MARKER=(airfoil)
GEO_DESCRIPTION=AIRFOIL
GEO_LOCATION_STATIONS=(0.0)
GEO_BOUNDS=(0.0,1.0)
GEO_NUMBER_STATIONS=1
GEO_MODE=FUNCTION
%
VALUE_OBJFUNC_FILENAME=airfoil_dimension.csv
TABULAR_FORMAT=CSV
"""
    os.makedirs(folder, exist_ok=True)
    with open(cfg_path, 'w') as f:
        f.write(cfg_content) # Viết file geo.cfg

    subprocess.run(['SU2_GEO', os.path.basename(cfg_path)], cwd=folder, check=True) # Chạy SU2_GEO cho geo.cfg mới sinh ra

    with open(csv_thick, newline='') as f:
        reader = csv.DictReader(f)
        row = next(reader)
    results['AIRFOIL_THICKNESS'] = row['AIRFOIL_THICKNESS'].strip() #Lưu giá trị AIRFOIL_THICKNESS vào trong results['AIRFOIL_THICKNESS']

    # 2) Đọc history.csv cho DRAG, LIFT, MOMENT_Z, AOA
    hist_path = os.path.join(folder, 'history.csv') # Path của file history.csv
    with open(hist_path, newline='') as f:
        reader = csv.reader(f)
        header = next(reader) # Đọc Header của history.csv
        cols = [h.strip().strip('"') for h in header]
        last = None
        for r in reader:
            last = r # Lặp cho tới khi tới dòng cuối cùng.

    # map trực tiếp tên cột history.csv → biến trong GUI
    indices = {
                'DRAG':     cols.index('CD'),
                'LIFT':     cols.index('CL'),
                'MOMENT_Z': cols.index('CMz'),
                'AOA':      cols.index('AoA'),
              }
    results['DRAG']     = last[indices['DRAG']].strip()
    results['LIFT']     = last[indices['LIFT']].strip()
    results['MOMENT_Z'] = last[indices['MOMENT_Z']].strip()
    results['AOA']      = last[indices['AOA']].strip()

    # Gán giá trị cho các biến để trả về cho init_opt_conditions
    thickness = float(results['AIRFOIL_THICKNESS'])
    cd        = float(results['DRAG'])
    cl        = float(results['LIFT'])
    cmz       = float(results['MOMENT_Z'])
    aoa       = float(results['AOA'])

    return thickness, cd, cl, cmz, aoa