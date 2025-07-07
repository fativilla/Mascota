import cv2
from PIL import Image, ImageTk
import tkinter as tk

class Pet:
    def __init__(self, root):
        self.root = root
        self.root.overrideredirect(True)  # Elimina la barra de título
        self.root.wm_attributes('-transparentcolor', 'white')  # Fondo transparente
        self.root.config(bg='white')  # Color que se hará transparente
        
        self.video_path = "unicorn.mp4"
        self.cap = cv2.VideoCapture(self.video_path)

        # ¡Primero crea el Label y luego empaquétalo!
        self.label = tk.Label(root, bg='white')  # Label vacío inicialmente
        self.label.pack()  # Ahora sí empaquetamos
        
        # Bind del doble clic (Button-1 es clic izquierdo, Double-Button-1 es doble clic)
        self.label.bind("<Double-Button-1>", self.cerrar_ventana)
        
        self.update_video()

    def update_video(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convertir a RGB
            img = Image.fromarray(frame).resize((100, 100))
            imgtk = ImageTk.PhotoImage(image=img)
            self.label.config(image=imgtk)
            self.label.image = imgtk  # ¡Referencia para evitar garbage collection!
        else:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reiniciar video
        
        self.root.after(30, self.update_video)  # Actualizar cada 30ms
    def cerrar_ventana(self, event):  # Función para cerrar la ventana
        self.root.destroy()  # Cierra la ventana completamente
root = tk.Tk()
root.geometry("100x100+50+50")  # Tamaño + posición inicial
pet = Pet(root)
root.mainloop()