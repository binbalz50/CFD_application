import os
import shutil
import subprocess
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class MeshGenerator(QThread):
    mesh_generated = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    
    def __init__(self,group,type,mesh_type,mode,wall_spacing):
        super().__init__()
        self.code = self.naca_code(group,type)
        self.mesh_type=mesh_type
        self.mode=mode
        self.wall_spacing=wall_spacing


    @staticmethod 
    def naca_code(group=None,type=None):
        if group=="NACA 4 digit":
            code=type[-4:]
        return code
    
    def run(self):
        self.gen_mesh()

    def gen_mesh(self): #generate mesh and post-processing mesh
        folder_name= f'NACA_{self.code}'

        if not os.path.exists(folder_name): #Create folder
            os.makedirs(folder_name)
        else:
            shutil.rmtree(folder_name)
            os.makedirs(folder_name)
        if self.mesh_type == "structural":
            if self.mode=="inviscid":
                subprocess.run(['gmshairfoil2d', '--format', 'vtk', '--naca', self.code, '--output', folder_name, '--structural', '--no_bl', '--ext_mesh_size', '0.5'], check=True) 
                subprocess.run(['gmshairfoil2d', '--format', 'su2', '--naca', self.code, '--output', folder_name, '--structural', '--no_bl', '--ext_mesh_size', '0.5'], check=True)
            elif self.mode=="viscos":
                subprocess.run(['gmshairfoil2d', '--format', 'vtk', '--naca', self.code, '--output', folder_name, '--structural', '--first_layer',  f'{self.wall_spacing}', '--ext_mesh_size', '0.5'], check=True) 
                subprocess.run(['gmshairfoil2d', '--format', 'su2', '--naca', self.code, '--output', folder_name, '--structural', '--first_layer', f'{self.wall_spacing}', '--ext_mesh_size', '0.5'], check=True)
        if self.mesh_type == "farfield":
            if self.mode=="inviscid":
                subprocess.run(['gmshairfoil2d', '--format', 'vtk', '--naca', self.code, '--output', folder_name, '--farfield', '10', '--no_bl', '--ext_mesh_size', '0.5'], check=True) 
                subprocess.run(['gmshairfoil2d', '--format', 'su2', '--naca', self.code, '--output', folder_name, '--farfield', '10', '--no_bl', '--ext_mesh_size', '0.5'], check=True)
            elif self.mode=="viscos": 
                subprocess.run(['gmshairfoil2d', '--format', 'vtk', '--naca', self.code, '--output', folder_name, '--farfield', '10', '--first_layer',  f'{self.wall_spacing}', '--ext_mesh_size', '0.5'], check=True) 
                subprocess.run(['gmshairfoil2d', '--format', 'su2', '--naca', self.code, '--output', folder_name, '--farfield', '10', '--first_layer', f'{self.wall_spacing}', '--ext_mesh_size', '0.5'], check=True)
        if self.mesh_type == "box":
            if self.mode=="inviscid":
                subprocess.run(['gmshairfoil2d', '--format', 'vtk', '--naca', self.code, '--output', folder_name, '--box', '12x4', '--no_bl'], check=True) 
                subprocess.run(['gmshairfoil2d', '--format', 'su2', '--naca', self.code, '--output', folder_name, '--box',  '12x4', '--no_bl'], check=True)
            elif self.mode=="viscos":
                subprocess.run(['gmshairfoil2d', '--format', 'vtk', '--naca', self.code, '--output', folder_name, '--box', '12x4', '--first_layer', f'{self.wall_spacing}'], check=True) 
                subprocess.run(['gmshairfoil2d', '--format', 'su2', '--naca', self.code, '--output', folder_name, '--box', '12x4', '--first_layer', f'{self.wall_spacing}'], check=True)    
        mesh_vtk=os.path.join(folder_name, f'mesh_airfoil_{self.code}.vtk')
        mesh_su2=os.path.join(folder_name, f'mesh_airfoil_{self.code}.su2')
        if os.path.exists(mesh_vtk) and os.path.exists(mesh_su2) and os.path.exists(folder_name):
            print(mesh_vtk)
            self.mesh_generated.emit( {
                "mesh_vtk": mesh_vtk,
                "mesh_su2": mesh_su2,
            })
        else:
            msg=QtWidgets.QMessageBox()
            msg.setWindowFlags(msg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            msg.setInformativeText('Failed!')
            msg.exec()

    
        
        
        
