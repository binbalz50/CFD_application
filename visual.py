from PyQt6 import QtWidgets
from PyQt6.QtWidgets import *
from pyvistaqt import QtInteractor
import pyvista as pv

class VisualizerWidget(QtWidgets.QWidget):
    # Add any additional methods for interacting with the plotter here
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set up the layout for the visualizer
        self.layout = QtWidgets.QVBoxLayout(self)

        # Create the QtInteractor
        self.plot = QtInteractor(self)
        
        # Add the plotter to the layout
        self.layout.addWidget(self.plot.interactor)

        # Optionally set some settings for the plotter
        self.plot.set_background('white')

    def show_mesh(self,data):
        mesh=pv.read(data)
        self.plot.clear()
        self.plot.add_mesh(mesh, show_edges=True, color="white", line_width=1)
        self.plot.view_xy()
        self.plot.reset_camera()
        self.plot.camera.zoom(1.3)
        self.plot.screenshot("mesh.png",window_size=[1080, 1080])

    def show(self,data,field):
        result=pv.read(data)
        field_name=result[field]
        self.plot.clear()
        self.plot.add_mesh(result, scalars=field_name, scalar_bar_args={'title': f"{field}" , 'vertical': False}, cmap='jet', show_scalar_bar=True)
        self.plot.view_xy()
