import os
from PIL import Image, ImageTk  # Import Pillow for handling images
import math
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Circle
from UrKR.UrKR import robot
import numpy as np
from time import sleep

class DrawingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("APPLIED MATHEMATICS LABORATORY")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)  # Handle window close event
        self.root.config(bg="white")

        # Initialize variables
        self.points = []
        self.preview_circle = None
        self.preview_line = None
        self.sander_radius_mm = 9.5
        self.end_tolerance_mm = 2
        self.motion_cid = None

        # Create matplotlib figure and axis
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlim(0, 300)
        self.ax.set_ylim(0, 300)
        self.ax.set_aspect('equal', adjustable='box')
        self.ax.set_title("Click to define path. Double-click to finish.")
        self.ax.set_xlabel("X (mm)")
        self.ax.set_ylabel("Y (mm)")
        self.ax.set_xticks(range(38, 286, 25))
        self.ax.set_yticks(range(38, 286, 25))
        self.ax.grid(True)

        # Add a label at the top of the window
        self.title_label = ttk.Label(root, text="Flat Drawing Demonstration", font=("Transducer CPP Uppercase", 22), background="white", foreground="#005030")
        self.title_label.grid(row=0, column=0, columnspan=2, pady=10)

        # Embed the matplotlib figure in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=1, column=0, columnspan=2)

        self.draw_button = tk.Button(
            root, 
            text="Draw with robot", 
            font = ("Transducer CPP Uppercase", 12, "bold"), 
            bg="#005030", 
            fg="white",
            command=self.finalize_path)
        self.draw_button.grid(row=2, column=0, padx=20, pady=20)

        self.reset_button = tk.Button(
            root, 
            text="Reset for new path", 
            font = ("Transducer CPP Uppercase", 12, "bold"),
            bg="#005030",
            fg="white",
            command=self.reset_plane)
        self.reset_button.grid(row=2, column=1, padx=20, pady=20)

        # Add a canvas for the PNG log graphic
        self.log_canvas = tk.Canvas(root, width=609, height=150, bg="white", highlightthickness=0)  # Remove the border
        self.log_canvas.grid(row=3, column=0, columnspan=2, pady=10)

        # Load and display the PNG file
        self.load_logo_image("Sci-math-primary-2c-green-rgb.png")  # Replace with the actual path to your PNG file

        # Connect matplotlib events
        self.cid_click = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        self.motion_cid = self.fig.canvas.mpl_connect('motion_notify_event', self.onmotion)

    def load_logo_image(self, image_path):
        """Load and display the PNG log graphic on the canvas."""
        try:
            # Open the image using Pillow
            image = Image.open(image_path)
            # Resize the image to fit the canvas (optional)
            image = image.resize((609, 150))
            # Convert the image to a PhotoImage
            self.log_image = ImageTk.PhotoImage(image)
            # Display the image on the canvas
            self.log_canvas.create_image(0, 0, anchor="nw", image=self.log_image)
        except Exception as e:
            print(f"Error loading image: {e}")

    def on_close(self):
        print("Closing the application...")
        self.root.quit()  # Stop the main loop
        self.root.destroy()  # Destroy the tkinter root window

    def onclick(self, event):
        if event.xdata is not None and event.ydata is not None:
            # Check if the user double-clicked near the last point
            if len(self.points) > 0:
                last_x, last_y = self.points[-1]
                distance = math.sqrt((event.xdata - last_x) ** 2 + (event.ydata - last_y) ** 2)
                if distance <= self.end_tolerance_mm:
                    print("End of path detected. Stopping preview features.")
                    self.stop_preview()
                    return

            self.points.append((event.xdata, event.ydata))
            self.ax.plot(event.xdata, event.ydata, 'ro')
            if self.preview_line:
                self.preview_line.set_color('red')
                self.preview_line = None
            self.fig.canvas.draw()

    def onmotion(self, event):
        if self.preview_circle and (self.preview_circle in self.ax.patches):
            self.preview_circle.remove()
        if event.xdata is not None and event.ydata is not None:
            self.preview_circle = Circle((event.xdata, event.ydata), self.sander_radius_mm, color='red', alpha=0.2)
            self.ax.add_patch(self.preview_circle)

            if len(self.points) > 0:
                if self.preview_line:
                    self.preview_line.remove()
                x_vals = [self.points[-1][0], event.xdata]
                y_vals = [self.points[-1][1], event.ydata]
                self.preview_line, = self.ax.plot(x_vals, y_vals, 'b--')
            self.fig.canvas.draw()

    def stop_preview(self):
        if self.motion_cid:
            self.fig.canvas.mpl_disconnect(self.motion_cid)
        if self.preview_circle and (self.preview_circle in self.ax.patches):
            self.preview_circle.remove()
        if self.preview_line:
            self.preview_line.remove()
        self.fig.canvas.draw()

    def finalize_path(self):
        # Save the plot
        images_folder = os.path.join(os.getcwd(), "images")
        os.makedirs(images_folder, exist_ok=True)
        image_path = os.path.join(images_folder, "defined_path.png")
        self.fig.savefig(image_path)
        print(f"Plot saved to {image_path}")

        # Send the path to the robot
        self.send_to_robot()

    def reset_plane(self):
        # Clear the points and reset the plane
        self.points = []
        self.ax.clear()
        self.ax.set_xlim(0, 300)
        self.ax.set_ylim(0, 300)
        self.ax.set_aspect('equal', adjustable='box')
        self.ax.set_title("Click to define path. Double-click to finish.")
        self.ax.set_xlabel("X (mm)")
        self.ax.set_ylabel("Y (mm)")
        self.ax.set_xticks(range(0, 301, 25))
        self.ax.set_yticks(range(0, 301, 25))
        self.ax.grid(True)
        self.fig.canvas.draw()

        # Reconnect the motion event
        self.motion_cid = self.fig.canvas.mpl_connect('motion_notify_event', self.onmotion)

    def send_to_robot(self):
        # Initialize the robot connection
        Gibbs = robot('192.168.99.228')
        Gibbs.Connect()

        # Define speeds and accelerations
        linear_speed_ms = 0.15
        linear_accel_ms = 0.5
        joint_speed_rads = 1.6
        joint_accel_radss = 1.6
        hover_height_m = 0.010
        homeJ = np.deg2rad([-71.85, -84.38, -123.96, -61.69, 90.0, 19.45])
        
        payload_kg = 0.010
        payload_cz_m = [0.0, 0.0, 0.0]
        tcp_m = [0.0, 0.0, 0.100, 0.0, 0.0, 0.0]

        grid_frame = [-0.145, -0.575, 0.0, 0.0, 3.141, 0.0]

        Gibbs.SetScriptName("draw_in_2D")
        Gibbs.SetPayload(payload_kg,payload_cz_m)
        Gibbs.SetTCP(tcp_m)
        Gibbs.SetRefFrame(grid_frame)

        Gibbs.AddMove('J', 'J', pose=homeJ, speed=joint_speed_rads, accel=joint_accel_radss)

        x_m = self.points[0][0] / 1000.0; y_m = self.points[0][1] / 1000.0
        # Approach the first point with a hover height + 100 mm
        Gibbs.AddMove('L', 'P', pose=[-x_m, y_m, -(hover_height_m+0.1), 0.0, 0.0, 0.0],
                          speed=linear_speed_ms, accel=0.5*linear_accel_ms, blendRadius=0.0, poseTrans=True)
        # Move to the first point with a hover height
        Gibbs.AddMove('L', 'P', pose=[-x_m, y_m, -hover_height_m, 0.0, 0.0, 0.0],
                          speed=linear_speed_ms, accel=linear_accel_ms, blendRadius=0.000, poseTrans=True)
        Gibbs.AddSleep(1)

        # Draw path with a hover height
        for (x, y) in self.points[:-1]:
            x_m = x / 1000.0
            y_m = y / 1000.0
            print(f"Moving to ({x_m:0.3f}, {y_m:0.3f})")
            Gibbs.AddMove('L', 'P', pose=[-x_m, y_m, -hover_height_m, 0.0, 0.0, 0.0],
                          speed=linear_speed_ms, accel=linear_accel_ms, blendRadius=0.005, poseTrans=True)
        # Last point with 0 blend radius to avoid jerky stop.
        x_m = self.points[-1][0] / 1000.0; y_m = self.points[-1][1] / 1000.0
        Gibbs.AddMove('L', 'P', pose=[-x_m, y_m, -hover_height_m, 0.0, 0.0, 0.0],
                          speed=linear_speed_ms, accel=linear_accel_ms, blendRadius=0.000, poseTrans=True)
        Gibbs.AddSleep(1)

        x_m = self.points[-1][0] / 1000.0; y_m = self.points[-1][1] / 1000.0
        # Retract from the last point with a hover height + 100 mm
        Gibbs.AddMove('L', 'P', pose=[-x_m, y_m, -hover_height_m-0.1, 0.0, 0.0, 0.0],
                          speed=linear_speed_ms, accel=0.5*linear_accel_ms, blendRadius=0.0, poseTrans=True)

        # Return to home position
        Gibbs.AddMove('J', 'J', pose=homeJ, speed=joint_speed_rads, accel=joint_accel_radss)
        Gibbs.SendScript()
        sleep(3)
        Gibbs.Disconnect()

if __name__ == "__main__":
    root = tk.Tk()
    app = DrawingApp(root)
    root.mainloop()
