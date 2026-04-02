import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
from pynput import mouse, keyboard
from pynput.mouse import Button, Listener as MouseListener
from pynput.keyboard import Key, Listener as KeyboardListener
import pynput.mouse as mouse_control
import os

class MouseRecorder:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Grabador y Reproductor de Mouse")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # Variables
        self.recording = False
        self.actions = []
        self.start_time = 0
        self.mouse_listener = None
        self.keyboard_listener = None
        self.reproducing = False
        self.stop_reproduction = False
        self.reproduction_keyboard_listener = None  # Nuevo listener para reproducción
        
        self.setup_ui()
        
    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título
        title_label = ttk.Label(main_frame, text="Grabador de Acciones del Mouse", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Frame de grabación
        record_frame = ttk.LabelFrame(main_frame, text="Grabación", padding="10")
        record_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.record_button = ttk.Button(record_frame, text="Iniciar Grabación", 
                                       command=self.toggle_recording)
        self.record_button.grid(row=0, column=0, padx=(0, 10))
        
        self.status_label = ttk.Label(record_frame, text="Listo para grabar")
        self.status_label.grid(row=0, column=1)
        
        # Información de grabación
        info_label = ttk.Label(record_frame, 
                              text="Presiona F9 para detener la grabación", 
                              font=("Arial", 8))
        info_label.grid(row=1, column=0, columnspan=2, pady=(5, 0))
        
        # Frame de reproducción
        play_frame = ttk.LabelFrame(main_frame, text="Reproducción", padding="10")
        play_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Número de repeticiones
        ttk.Label(play_frame, text="Repeticiones:").grid(row=0, column=0, sticky=tk.W)
        self.repeat_var = tk.StringVar(value="1")
        repeat_spinbox = ttk.Spinbox(play_frame, from_=1, to=100, width=10, 
                                    textvariable=self.repeat_var)
        repeat_spinbox.grid(row=0, column=1, padx=(5, 0), sticky=tk.W)
        
        # Velocidad de reproducción
        ttk.Label(play_frame, text="Velocidad:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.speed_var = tk.DoubleVar(value=1.0)
        self.speed_scale = ttk.Scale(play_frame, from_=0.1, to=5.0, 
                                    variable=self.speed_var, orient=tk.HORIZONTAL, 
                                    length=200)
        self.speed_scale.grid(row=1, column=1, padx=(5, 0), pady=(10, 0), sticky=(tk.W, tk.E))
        
        self.speed_label = ttk.Label(play_frame, text="1.0x")
        self.speed_label.grid(row=1, column=2, padx=(5, 0), pady=(10, 0))
        
        # Actualizar etiqueta de velocidad
        self.speed_var.trace('w', self.update_speed_label)
        
        # Botones de reproducción
        button_frame = ttk.Frame(play_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=(15, 0))
        
        self.play_button = ttk.Button(button_frame, text="Reproducir", 
                                     command=self.start_reproduction)
        self.play_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="Detener", 
                                     command=self.stop_reproduction_func, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1)
        
        # Información de reproducción - MODIFICADO
        info_reproduction_label = ttk.Label(play_frame, 
                                          text="Durante la reproducción: F9 o ESPACIO para detener", 
                                          font=("Arial", 8))
        info_reproduction_label.grid(row=3, column=0, columnspan=3, pady=(5, 0))
        
        # Frame de archivo
        file_frame = ttk.LabelFrame(main_frame, text="Archivo", padding="10")
        file_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(file_frame, text="Guardar", command=self.save_actions).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(file_frame, text="Cargar", command=self.load_actions).grid(row=0, column=1)
        
        # Lista de acciones
        list_frame = ttk.LabelFrame(main_frame, text="Acciones Grabadas", padding="10")
        list_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Scrollbar y Listbox
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.actions_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=8)
        self.actions_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.config(command=self.actions_listbox.yview)
        
        # Botón limpiar
        ttk.Button(list_frame, text="Limpiar Lista", 
                  command=self.clear_actions).grid(row=1, column=0, pady=(10, 0))
        
        # Configurar grid weights
        main_frame.columnconfigure(1, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
    def update_speed_label(self, *args):
        speed = self.speed_var.get()
        self.speed_label.config(text=f"{speed:.1f}x")
        
    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()
            
    def start_recording(self):
        self.recording = True
        self.actions = []
        self.start_time = time.time()
        self.record_button.config(text="Grabando...", state=tk.DISABLED)
        self.status_label.config(text="Grabando... (F9 para detener)")
        self.actions_listbox.delete(0, tk.END)
        
        # Iniciar listeners
        self.mouse_listener = MouseListener(
            on_move=self.on_mouse_move,
            on_click=self.on_mouse_click,
            on_scroll=self.on_mouse_scroll
        )
        
        self.keyboard_listener = KeyboardListener(
            on_press=self.on_key_press_recording
        )
        
        self.mouse_listener.start()
        self.keyboard_listener.start()
        
    def stop_recording(self):
        self.recording = False
        self.record_button.config(text="Iniciar Grabación", state=tk.NORMAL)
        self.status_label.config(text=f"Grabación completada - {len(self.actions)} acciones")
        
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            
        self.update_actions_list()
        
    def on_mouse_move(self, x, y):
        if self.recording:
            current_time = time.time() - self.start_time
            self.actions.append({
                'type': 'move',
                'x': x,
                'y': y,
                'time': current_time
            })
            
    def on_mouse_click(self, x, y, button, pressed):
        if self.recording:
            current_time = time.time() - self.start_time
            self.actions.append({
                'type': 'click',
                'x': x,
                'y': y,
                'button': button.name,
                'pressed': pressed,
                'time': current_time
            })
            
    def on_mouse_scroll(self, x, y, dx, dy):
        if self.recording:
            current_time = time.time() - self.start_time
            self.actions.append({
                'type': 'scroll',
                'x': x,
                'y': y,
                'dx': dx,
                'dy': dy,
                'time': current_time
            })
    
    # MODIFICADO: Función separada para el listener durante la grabación
    def on_key_press_recording(self, key):
        if key == Key.f9 and self.recording:
            self.stop_recording()
    
    # NUEVO: Función separada para el listener durante la reproducción
    def on_key_press_reproduction(self, key):
        if key == Key.f9 or key == Key.space:
            if self.reproducing:
                self.stop_reproduction_func()
                
    def update_actions_list(self):
        self.actions_listbox.delete(0, tk.END)
        for i, action in enumerate(self.actions):
            if action['type'] == 'move':
                text = f"{i+1}. Mover a ({action['x']}, {action['y']}) - {action['time']:.2f}s"
            elif action['type'] == 'click':
                state = "Presionar" if action['pressed'] else "Soltar"
                text = f"{i+1}. {state} {action['button']} en ({action['x']}, {action['y']}) - {action['time']:.2f}s"
            elif action['type'] == 'scroll':
                text = f"{i+1}. Scroll ({action['dx']}, {action['dy']}) en ({action['x']}, {action['y']}) - {action['time']:.2f}s"
            
            self.actions_listbox.insert(tk.END, text)
            
    def start_reproduction(self):
        if not self.actions:
            messagebox.showwarning("Advertencia", "No hay acciones grabadas para reproducir")
            return
            
        if self.reproducing:
            return
            
        try:
            repetitions = int(self.repeat_var.get())
        except ValueError:
            messagebox.showerror("Error", "Número de repeticiones inválido")
            return
            
        self.reproducing = True
        self.stop_reproduction = False
        self.play_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # NUEVO: Iniciar listener de teclado para la reproducción
        self.reproduction_keyboard_listener = KeyboardListener(
            on_press=self.on_key_press_reproduction
        )
        self.reproduction_keyboard_listener.start()
        
        # Iniciar reproducción en un hilo separado
        thread = threading.Thread(target=self.reproduce_actions, args=(repetitions,))
        thread.daemon = True
        thread.start()
        
    def reproduce_actions(self, repetitions):
        try:
            mouse_controller = mouse_control.Controller()
            speed_multiplier = self.speed_var.get()
            
            for rep in range(repetitions):
                if self.stop_reproduction:
                    break
                    
                self.root.after(0, lambda r=rep+1: self.status_label.config(
                    text=f"Reproduciendo... ({r}/{repetitions}) - F9 o ESPACIO para detener"))
                
                last_time = 0
                
                for action in self.actions:
                    if self.stop_reproduction:
                        break
                        
                    # Calcular delay ajustado por velocidad
                    delay = (action['time'] - last_time) / speed_multiplier
                    if delay > 0:
                        time.sleep(delay)
                    
                    # Ejecutar acción
                    if action['type'] == 'move':
                        mouse_controller.position = (action['x'], action['y'])
                    elif action['type'] == 'click':
                        button = Button.left if action['button'] == 'left' else Button.right
                        if action['pressed']:
                            mouse_controller.press(button)
                        else:
                            mouse_controller.release(button)
                    elif action['type'] == 'scroll':
                        mouse_controller.scroll(action['dx'], action['dy'])
                    
                    last_time = action['time']
                    
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error durante la reproducción: {str(e)}"))
        finally:
            self.root.after(0, self.reproduction_finished)
            
    def stop_reproduction_func(self):
        self.stop_reproduction = True
        
    def reproduction_finished(self):
        self.reproducing = False
        self.stop_reproduction = False
        self.play_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Reproducción completada")
        
        # NUEVO: Detener el listener de teclado de reproducción
        if self.reproduction_keyboard_listener:
            self.reproduction_keyboard_listener.stop()
            self.reproduction_keyboard_listener = None
        
    def save_actions(self):
        if not self.actions:
            messagebox.showwarning("Advertencia", "No hay acciones para guardar")
            return
            
        try:
            filename = f"mouse_actions_{int(time.time())}.json"
            with open(filename, 'w') as f:
                json.dump(self.actions, f, indent=2)
            messagebox.showinfo("Éxito", f"Acciones guardadas en {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {str(e)}")
            
    def load_actions(self):
        try:
            from tkinter import filedialog
            filename = filedialog.askopenfilename(
                title="Cargar acciones",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'r') as f:
                    self.actions = json.load(f)
                self.update_actions_list()
                messagebox.showinfo("Éxito", f"Acciones cargadas desde {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar: {str(e)}")
            
    def clear_actions(self):
        self.actions = []
        self.actions_listbox.delete(0, tk.END)
        self.status_label.config(text="Lista de acciones limpiada")
        
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
        
    def on_closing(self):
        if self.recording:
            self.stop_recording()
        if self.reproducing:
            self.stop_reproduction_func()
        
        # NUEVO: Asegurar que todos los listeners se detengan
        if self.reproduction_keyboard_listener:
            self.reproduction_keyboard_listener.stop()
            
        self.root.destroy()

if __name__ == "__main__":
    # Verificar dependencias
    try:
        import pynput
    except ImportError:
        print("Error: Se requiere la librería 'pynput'")
        print("Instálala con: pip install pynput")
        exit(1)
    
    app = MouseRecorder()
    app.run()