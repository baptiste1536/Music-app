import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import pygame
import os

pygame.mixer.init()
ctk.set_appearance_mode("dark")

# ── CONFIGURATION VISUELLE ──
BG, BARRE, CARTE, ROUGE = "#161618", "#1c1c1e", "#2c2c2e", "#fc3c44"
TEXTE, GRIS = "#f5f5f7", "#8e8e93"

def formater_temps(s):
    m, s = divmod(int(s), 60)
    return f"{m}:{s:02d}"

# ── BARRE DE PROGRESSION ──
class BarreMusique(tk.Canvas):
    def __init__(self, master, au_clic, **kwargs):
        super().__init__(master, height=6, bg="#38383a", highlightthickness=0, cursor="hand2", **kwargs)
        self.au_clic = au_clic
        self.bind("<Button-1>", self._clic)

    def dessiner(self, ratio):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        self.create_rectangle(0, 0, int(w * ratio), h, fill=ROUGE, outline="")

    def _clic(self, e):
        if self.winfo_width() > 0:
            self.au_clic(max(0.0, min(1.0, e.x / self.winfo_width())))

# ── ELEMENT DE LA LISTE ──
class CarteMorceau(ctk.CTkFrame):
    def __init__(self, master, chemin, index, app):
        super().__init__(master, fg_color=CARTE, corner_radius=8, height=45) # Hauteur réduite
        self.chemin, self.index, self.app = chemin, index, app
        self.pack_propagate(False)
        
        self.lbl = ctk.CTkLabel(self, text=f"{index+1}.  {os.path.basename(chemin)[:40]}", anchor="w")
        self.lbl.pack(side="left", padx=15, fill="x", expand=True)
        
        self.grip = ctk.CTkLabel(self, text="⠿", text_color=GRIS, width=40, cursor="fleur")
        self.grip.pack(side="right")

        self.lbl.bind("<Button-1>", lambda e: self.app.jouer_morceau(self.index))
        
        # Logique Drag & Drop
        self.grip.bind("<ButtonPress-1>", self._saisir)
        self.grip.bind("<ButtonRelease-1>", self._lacher)

    def _saisir(self, e):
        self.app.index_en_deplacement = self.index
        self.configure(fg_color=ROUGE, border_width=1, border_color="white")
        # Le titre reste visible ici

    def _lacher(self, e):
        y_souris = e.y_root
        nouvel_index = self.index
        
        # Détermine la place exacte entre les morceaux
        for c in self.app.cartes_widgets:
            y_centre = c.winfo_rooty() + (c.winfo_height() / 2)
            if y_souris < y_centre:
                nouvel_index = c.index
                break
            else:
                nouvel_index = c.index + 1
        
        self.app.appliquer_deplacement(self.app.index_en_deplacement, nouvel_index)

# ── APPLICATION ──
class Lecteur(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Lecteur")
        self.geometry("450x600") # Taille réduite et plus compacte
        self.configure(fg_color=BG)

        self.playlist = []
        self.cartes_widgets = []
        self.index_actuel = -1
        self.duree, self.offset = 0, 0
        self.index_en_deplacement = None

        self._build_ui()
        self._boucle()

    def _build_ui(self):
        # Header
        h = ctk.CTkFrame(self, fg_color=BARRE, height=50, corner_radius=0)
        h.pack(fill="x")
        ctk.CTkButton(h, text="Importer", fg_color=ROUGE, width=70, height=28, command=self.charger).place(relx=0.95, rely=0.5, anchor="e")

        # Liste
        self.zone = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.zone.pack(fill="both", expand=True, padx=8, pady=8)

        # Player
        p = ctk.CTkFrame(self, fg_color=BARRE, height=140, corner_radius=0)
        p.pack(fill="x", side="bottom")
        
        self.titre_p = ctk.CTkLabel(p, text="Sélectionnez un dossier", font=("bold", 12), text_color=GRIS)
        self.titre_p.pack(pady=8)

        pz = ctk.CTkFrame(p, fg_color="transparent")
        pz.pack(fill="x", padx=20)
        self.t_cur = ctk.CTkLabel(pz, text="0:00", width=35, font=("", 11))
        self.t_cur.pack(side="left")
        self.barre_prog = BarreMusique(pz, au_clic=self.aller_a)
        self.barre_prog.pack(side="left", fill="x", expand=True, padx=10)
        self.t_tot = ctk.CTkLabel(pz, text="0:00", width=35, font=("", 11))
        self.t_tot.pack(side="right")

        c = ctk.CTkFrame(p, fg_color="transparent")
        c.pack(pady=10)
        ctk.CTkButton(c, text="⏮", width=35, fg_color="transparent", font=("", 18), command=self.prev).pack(side="left", padx=10)
        self.btn_p = ctk.CTkButton(c, text="▶", width=50, height=50, corner_radius=25, fg_color=ROUGE, font=("", 18), command=self.toggle)
        self.btn_p.pack(side="left", padx=10)
        ctk.CTkButton(c, text="⏭", width=35, fg_color="transparent", font=("", 18), command=self.next).pack(side="left", padx=10)

    def charger(self):
        d = filedialog.askdirectory()
        if d:
            self.playlist = [os.path.join(d, f) for f in os.listdir(d) if f.lower().endswith(('.mp3', '.wav', '.m4a'))]
            if self.playlist:
                self.index_actuel = 0
                self.titre_p.configure(text=os.path.basename(self.playlist[0]), text_color=GRIS)
            self.rafraichir()

    def rafraichir(self):
        for w in self.cartes_widgets: w.destroy()
        self.cartes_widgets = []
        for i, p in enumerate(self.playlist):
            c = CarteMorceau(self.zone, p, i, self)
            c.pack(fill="x", pady=1) # Espacement réduit
            self.cartes_widgets.append(c)
            if i == self.index_actuel:
                c.configure(fg_color="#3a1a1e")
                c.lbl.configure(text_color=ROUGE)

    def appliquer_deplacement(self, source, dest):
        if source is not None:
            morceau = self.playlist.pop(source)
            if dest > source: dest -= 1
            self.playlist.insert(dest, morceau)
            
            # Recalage de l'index de lecture
            if self.index_actuel == source: self.index_actuel = dest
            elif source < self.index_actuel <= dest: self.index_actuel -= 1
            elif dest <= self.index_actuel < source: self.index_actuel += 1
            
        self.index_en_deplacement = None
        self.rafraichir()

    def jouer_morceau(self, i):
        if not self.playlist: return
        self.index_actuel = i
        p = self.playlist[i]
        pygame.mixer.music.load(p)
        pygame.mixer.music.play()
        self.duree = pygame.mixer.Sound(p).get_length()
        self.offset = 0
        self.titre_p.configure(text=os.path.basename(p), text_color=TEXTE)
        self.t_tot.configure(text=formater_temps(self.duree))
        self.btn_p.configure(text="⏸")
        self.rafraichir()

    def toggle(self):
        if self.index_actuel == -1: return
        if not pygame.mixer.music.get_busy() and self.offset == 0:
            self.jouer_morceau(self.index_actuel)
        elif pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self.btn_p.configure(text="▶")
        else:
            pygame.mixer.music.unpause()
            self.btn_p.configure(text="⏸")

    def aller_a(self, r):
        if self.index_actuel != -1:
            self.offset = r * self.duree
            pygame.mixer.music.play(start=self.offset)
            self.btn_p.configure(text="⏸")

    def next(self): self.jouer_morceau((self.index_actuel + 1) % len(self.playlist))
    def prev(self): self.jouer_morceau((self.index_actuel - 1) % len(self.playlist))

    def _boucle(self):
        if pygame.mixer.music.get_busy():
            mtn = self.offset + (pygame.mixer.music.get_pos() / 1000)
            self.barre_prog.dessiner(mtn / self.duree if self.duree > 0 else 0)
            self.t_cur.configure(text=formater_temps(mtn))
            if mtn >= self.duree - 0.5: self.next()
        self.after(500, self._boucle)

if __name__ == "__main__":
    Lecteur().mainloop()