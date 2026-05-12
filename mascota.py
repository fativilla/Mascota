"""
Desktop Pet — versión mejorada
==============================
Mejoras sobre el original:
  • Arquitectura limpia: VideoPlayer / WindowManager / BehaviorEngine / DesktopPet
  • Máquina de estados: IDLE → WALK → JUMP → DRAG
  • Caminata aleatoria con rebote en bordes de pantalla
  • Salto con parábola suave
  • Menú contextual (clic derecho): tamaño, siempre encima, cerrar
  • Configuración centralizada con dataclass
  • Limpieza de recursos garantizada (context manager / __del__)
  • GIF con transparencia nativa: sin pipeline de máscara, bordes limpios
"""

import os
import random
import tkinter as tk
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from PIL import Image, ImageTk


# ─────────────────────────── Configuración ────────────────────────────────────

@dataclass
class Config:
    video_path: str = "unicorn.gif"
    pet_size: int = 120
    update_delay_ms: int = 30          # ~33 fps
    transparent_color: str = "white"
    always_on_top: bool = True

    # Comportamiento
    walk_speed: int = 3                # px por frame
    walk_min_frames: int = 60          # mínimo frames caminando
    walk_max_frames: int = 180
    idle_min_frames: int = 90          # mínimo frames en idle
    idle_max_frames: int = 240
    jump_height: int = 60              # px hacia arriba
    jump_frames: int = 30              # duración total del salto
    jump_chance: float = 0.003         # probabilidad por frame en idle

    # Tamaños disponibles en el menú
    size_options: list = field(default_factory=lambda: [80, 120, 160, 200])


CFG = Config()


# ─────────────────────────── Estados ──────────────────────────────────────────

class State(Enum):
    IDLE  = auto()
    WALK  = auto()
    JUMP  = auto()
    DRAG  = auto()


# ─────────────────────────── VideoPlayer ──────────────────────────────────────

class VideoPlayer:
    """
    Reproduce un GIF animado frame a frame usando PIL.

    Ventaja sobre OpenCV + MP4: el GIF ya tiene transparencia nativa
    en su paleta, así que no hace falta ningún pipeline de máscara.
    PIL expone cada frame con su canal alpha listo para usar.
    """

    def __init__(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Archivo no encontrado: {path}")

        self._gif = Image.open(path)
        if not hasattr(self._gif, "n_frames"):
            raise RuntimeError("El archivo no es un GIF animado válido.")

        self._n_frames = self._gif.n_frames
        self._current  = 0
        # Precargar todos los frames para evitar seek() en cada tick
        self._frames: list[Image.Image] = self._extract_frames()

    def _extract_frames(self) -> list[Image.Image]:
        """Extrae todos los frames del GIF como RGBA."""
        frames = []
        for i in range(self._n_frames):
            self._gif.seek(i)
            # convert("RGBA") respeta el índice de color transparente del GIF
            frames.append(self._gif.convert("RGBA").copy())
        return frames

    def next_frame(self, size: int) -> Optional[ImageTk.PhotoImage]:
        """Devuelve el siguiente frame escalado con transparencia nativa del GIF."""
        frame = self._frames[self._current].resize((size, size), Image.LANCZOS)
        self._current = (self._current + 1) % self._n_frames
        return ImageTk.PhotoImage(image=frame)

    def release(self):
        """Cierra el archivo GIF."""
        try:
            self._gif.close()
        except Exception:
            pass

    def __del__(self):
        self.release()


# ─────────────────────────── WindowManager ────────────────────────────────────

class WindowManager:
    """Gestiona geometría, transparencia y comportamiento de la ventana."""

    def __init__(self, root: tk.Tk, cfg: Config):
        self.root = root
        self.cfg = cfg
        self._always_on_top = cfg.always_on_top
        self._setup()

    def _setup(self):
        r = self.root
        r.overrideredirect(True)
        r.config(bg=self.cfg.transparent_color)
        r.wm_attributes("-transparentcolor", self.cfg.transparent_color)
        r.wm_attributes("-topmost", self._always_on_top)
        self.move_to(50, 50)

    def move_to(self, x: int, y: int):
        size = self.cfg.pet_size
        self.root.geometry(f"{size}x{size}+{x}+{y}")

    def get_pos(self) -> tuple[int, int]:
        return self.root.winfo_x(), self.root.winfo_y()

    def screen_size(self) -> tuple[int, int]:
        return self.root.winfo_screenwidth(), self.root.winfo_screenheight()

    def resize(self, new_size: int):
        self.cfg.pet_size = new_size
        x, y = self.get_pos()
        self.move_to(x, y)

    def toggle_topmost(self):
        self._always_on_top = not self._always_on_top
        self.root.wm_attributes("-topmost", self._always_on_top)
        return self._always_on_top


# ─────────────────────────── BehaviorEngine ───────────────────────────────────

class BehaviorEngine:
    """
    Máquina de estados simple para los comportamientos autónomos.
    Estados: IDLE ↔ WALK → JUMP
    El estado DRAG es controlado externamente (arrastre del usuario).
    """

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.state = State.IDLE
        self._frames_left = self._rand_idle()
        self._walk_dx = 0
        self._walk_dy = 0
        self._jump_frame = 0
        self._jump_base_y = 0
        self._paused = False           # True mientras está siendo arrastrado

    # ── API pública ──────────────────────────────────────────────────────────

    def pause(self):
        """Llamar cuando el usuario empieza a arrastrar."""
        self._paused = True
        self.state = State.DRAG

    def resume(self):
        """Llamar cuando el usuario suelta."""
        self._paused = False
        self._enter_idle()

    def tick(self, x: int, y: int, sw: int, sh: int) -> tuple[int, int]:
        """
        Calcula la nueva posición (x, y) según el estado actual.
        sw, sh = ancho y alto de pantalla.
        """
        if self._paused:
            return x, y

        if self.state == State.IDLE:
            x, y = self._tick_idle(x, y)
        elif self.state == State.WALK:
            x, y = self._tick_walk(x, y, sw, sh)
        elif self.state == State.JUMP:
            x, y = self._tick_jump(x, y, sh)

        return x, y

    # ── Transiciones ─────────────────────────────────────────────────────────

    def _enter_idle(self):
        self.state = State.IDLE
        self._frames_left = self._rand_idle()

    def _enter_walk(self):
        self.state = State.WALK
        self._frames_left = self._rand_walk()
        angle_choices = [-1, 1]
        self._walk_dx = random.choice(angle_choices) * self.cfg.walk_speed
        self._walk_dy = random.choice([0, 0, -1, 1])  # mayormente horizontal

    def _enter_jump(self, base_y: int):
        self.state = State.JUMP
        self._jump_frame = 0
        self._jump_base_y = base_y

    # ── Ticks por estado ─────────────────────────────────────────────────────

    def _tick_idle(self, x: int, y: int) -> tuple[int, int]:
        self._frames_left -= 1

        # Salto espontáneo
        if random.random() < self.cfg.jump_chance:
            self._enter_jump(y)
            return x, y

        if self._frames_left <= 0:
            self._enter_walk()
        return x, y

    def _tick_walk(self, x: int, y: int, sw: int, sh: int) -> tuple[int, int]:
        size = self.cfg.pet_size
        x += self._walk_dx
        y += self._walk_dy

        # Rebotar en bordes
        if x < 0:
            x = 0
            self._walk_dx = abs(self._walk_dx)
        elif x + size > sw:
            x = sw - size
            self._walk_dx = -abs(self._walk_dx)

        if y < 0:
            y = 0
            self._walk_dy = abs(self._walk_dy)
        elif y + size > sh:
            y = sh - size
            self._walk_dy = -abs(self._walk_dy)

        self._frames_left -= 1
        if self._frames_left <= 0:
            self._enter_idle()
        return x, y

    def _tick_jump(self, x: int, y: int, sh: int) -> tuple[int, int]:
        total = self.cfg.jump_frames
        h = self.cfg.jump_height
        t = self._jump_frame / total  # 0.0 → 1.0
        # Parábola: sube y baja suavemente
        offset = int(4 * h * t * (1 - t))
        new_y = self._jump_base_y - offset

        # No salir por arriba
        new_y = max(0, new_y)

        self._jump_frame += 1
        if self._jump_frame >= total:
            self._enter_idle()
            return x, self._jump_base_y   # volver a la posición base

        return x, new_y

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _rand_idle(self) -> int:
        return random.randint(self.cfg.idle_min_frames, self.cfg.idle_max_frames)

    def _rand_walk(self) -> int:
        return random.randint(self.cfg.walk_min_frames, self.cfg.walk_max_frames)


# ─────────────────────────── DesktopPet ───────────────────────────────────────

class DesktopPet:
    """Orquesta VideoPlayer, WindowManager y BehaviorEngine."""

    def __init__(self, root: tk.Tk, cfg: Config = CFG):
        self.root = root
        self.cfg = cfg

        self.video   = VideoPlayer(cfg.video_path)
        self.wm      = WindowManager(root, cfg)
        self.behavior = BehaviorEngine(cfg)

        self._drag_offset_x = 0
        self._drag_offset_y = 0

        self._build_label()
        self._build_menu()
        self._loop()

    # ── Construcción de widgets ───────────────────────────────────────────────

    def _build_label(self):
        self.label = tk.Label(self.root, bg=self.cfg.transparent_color, bd=0)
        self.label.pack()
        self.label.bind("<Button-1>",        self._on_drag_start)
        self.label.bind("<B1-Motion>",       self._on_drag_motion)
        self.label.bind("<ButtonRelease-1>", self._on_drag_end)
        self.label.bind("<Button-3>",        self._on_right_click)
        self.label.bind("<Double-Button-1>", lambda e: self._close())

    def _build_menu(self):
        self.menu = tk.Menu(self.root, tearoff=0)

        # Submenú de tamaños
        size_menu = tk.Menu(self.menu, tearoff=0)
        for s in self.cfg.size_options:
            size_menu.add_command(
                label=f"{s} × {s} px",
                command=lambda sz=s: self._set_size(sz)
            )
        self.menu.add_cascade(label="Tamaño", menu=size_menu)

        self.menu.add_command(label="Siempre encima: ✓", command=self._toggle_topmost)
        self.menu.add_separator()
        self.menu.add_command(label="Cerrar", command=self._close)

    # ── Loop principal ────────────────────────────────────────────────────────

    def _loop(self):
        # 1. Obtener frame
        photo = self.video.next_frame(self.cfg.pet_size)
        if photo:
            self.label.config(image=photo)
            self.label.image = photo   # evitar GC

        # 2. Comportamiento autónomo
        sw, sh = self.wm.screen_size()
        x, y   = self.wm.get_pos()
        nx, ny = self.behavior.tick(x, y, sw, sh)
        if (nx, ny) != (x, y):
            self.wm.move_to(nx, ny)

        self.root.after(self.cfg.update_delay_ms, self._loop)

    # ── Arrastre ─────────────────────────────────────────────────────────────

    def _on_drag_start(self, event):
        self._drag_offset_x = event.x
        self._drag_offset_y = event.y
        self.behavior.pause()

    def _on_drag_motion(self, event):
        x = self.root.winfo_pointerx() - self._drag_offset_x
        y = self.root.winfo_pointery() - self._drag_offset_y
        self.wm.move_to(x, y)

    def _on_drag_end(self, event):
        self.behavior.resume()

    # ── Menú contextual ───────────────────────────────────────────────────────

    def _on_right_click(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def _set_size(self, size: int):
        self.wm.resize(size)
        # Reempaquetar el label para que tome el nuevo tamaño
        self.label.pack_forget()
        self.label.pack()

    def _toggle_topmost(self):
        is_on = self.wm.toggle_topmost()
        label = "Siempre encima: ✓" if is_on else "Siempre encima: ✗"
        # Actualizar la etiqueta del ítem (índice 1, después del submenú)
        self.menu.entryconfig(1, label=label)

    # ── Cierre ────────────────────────────────────────────────────────────────

    def _close(self):
        self.video.release()
        self.root.destroy()


# ─────────────────────────── Entrada ──────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    app = DesktopPet(root)
    root.mainloop()