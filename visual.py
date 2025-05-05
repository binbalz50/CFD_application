from PyQt6 import QtWidgets
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
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

    def show_mesh(self,data,code):
        mesh=pv.read(data)
        self.plot.clear()
        self.plot.add_mesh(mesh, show_edges=True, color="white", line_width=1)
        self.plot.view_xy()
        self.plot.reset_camera()
        self.plot.camera.zoom(1.3)
        self.plot.screenshot(rf"NACA_{code}\NACA_{code}_mesh.png",window_size=[1920, 1080])

    def show(self,data,field,code,dim):
        result=pv.read(data)
        
        if field.lower() == "streamlines":
            # Assuming the vector field is called "Momentum"
            vectors_name = "Velocity"
            if vectors_name not in result.array_names:
                raise ValueError(f"'{vectors_name}' vector field not found in the data.")

            # Create a line source for seeding the streamlines
            seed = pv.Line(
                pointa=(-1.0, -0.1, 0.0),
                pointb=(2.0, 0.1, 0.0),
                resolution=100
            )
            streamlines = result.streamlines_from_source(
                seed,
                vectors=vectors_name,
                integrator_type=45,  # Runge-Kutta 4-5
                integration_direction='both',
                max_time=100.0,
                initial_step_length=0.5,
                terminal_speed=1e-12
            )
            self.plot.clear()
            self.plot.add_mesh(result, color='white', opacity=0.3)
            self.plot.add_mesh(streamlines, scalars='Velocity', cmap='jet', line_width=2)

            self.plot.view_xy()
            self.plot.camera.zoom(1.3)
            self.plot.screenshot(rf"NACA_{code}\NACA_{code}_streamlines.png", window_size=[1080, 1080])


        else:
            self.plot.clear()
            self.plot.add_mesh(result, scalars=result[field], scalar_bar_args={'title': f"{field} ({dim})" , 'vertical': False}, cmap='jet', show_scalar_bar=True)
            self.plot.view_xy()
            self.plot.camera.zoom(1.3)
            self.plot.screenshot(rf"NACA_{code}\NACA_{code}_{field}.png",window_size=[1080, 1080])

