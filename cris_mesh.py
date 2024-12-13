import os
import shutil
import subprocess
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt

class MeshGenerator: 
    def naca_code(group=None,type=None):
        if group=="NACA 4 digit":
            code=type[-4:]
        return code
    def gen_mesh(code): #generate mesh and post-processing mesh
        folder_name= f'NACA_{code}'

        if not os.path.exists(folder_name): #Create folder
            os.makedirs(folder_name)
        else:
            shutil.rmtree(folder_name)
            os.makedirs(folder_name)
        mesh_vtk=os.path.join(folder_name, f'mesh_airfoil_{code}.vtk')
        mesh_su2=os.path.join(folder_name, f'mesh_airfoil_{code}.su2')
        subprocess.run(['gmshairfoil2d', '--format', 'vtk', '--naca', code, '--output', folder_name, '--farfield', '10'], check=True)
        subprocess.run(['gmshairfoil2d', '--format', 'su2', '--naca', code, '--output', folder_name, '--farfield', '10'], check=True)
        if os.path.exists(mesh_vtk) and os.path.exists(mesh_su2) and os.path.exists(folder_name):
            return {
                "mesh_vtk": mesh_vtk,
                "mesh_su2": mesh_su2,
                "folder_name": folder_name,
            }
        else:
            msg=QtWidgets.QMessageBox()
            msg.setWindowFlags(msg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            msg.setInformativeText('Failed!')
            msg.exec()  

        
        
