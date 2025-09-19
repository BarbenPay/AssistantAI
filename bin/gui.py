# gui.py

import customtkinter
from PIL import Image
from enum import Enum

class ColorMode(Enum):
    DARKMODE = 1
    LIGHTMODE = 2

class AssistantApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("Assistant AI")
        self.geometry("800x600")
        self.app_state = "home"
        self.app_mode = ColorMode.LIGHTMODE

        # --- Chargement des ressources visuelles ---
        self.load_assets()

        # --- Lancement de la vue d'accueil ---
        self.setup_home_view()

    def load_assets(self):
        """Charge toutes les images et polices nécessaires."""
        try:
            # Police principale (vous pouvez la changer pour une autre police système)
            self.font_bold = ("Arial", 32, "bold")
            self.font_regular = ("Arial", 14)
            self.font_light = ("Arial", 12)

            # Logo principal
            logo_size = 120
            original_logo = Image.open("./ressources/logo_lightMode.png").convert("RGBA")
            resized_logo = original_logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            self.logo_image = customtkinter.CTkImage(light_image=resized_logo, dark_image=resized_logo, size=(logo_size, logo_size))

            # Icône d'envoi
            send_icon_image = Image.open("./ressources/send_icon.png").convert("RGBA")
            self.send_icon = customtkinter.CTkImage(light_image=send_icon_image, dark_image=send_icon_image, size=(18, 18))
        except Exception as e:
            print(f"Erreur lors du chargement des ressources : {e}")
            self.logo_image = None
            self.send_icon = None

    def setup_home_view(self):
        """Affiche la vue d'accueil épurée."""
        self.configure(fg_color='#1F1E1E')

        # --- NOUVEAU : Hiérarchie typographique ---
        self.title_label = customtkinter.CTkLabel(self, text="Assistant AI", font=self.font_bold, text_color="#2c3e50")
        self.title_label.place(relx=0.5, rely=0.30, anchor="center")

        self.subtitle_label = customtkinter.CTkLabel(self, text="Posez une question, obtenez une réponse.", font=self.font_regular, text_color="#7f8c8d")
        self.subtitle_label.place(relx=0.5, rely=0.36, anchor="center")

        self.logo_label = customtkinter.CTkLabel(self, text="", image=self.logo_image)
        self.logo_label.place(relx=0.5, rely=0.5, anchor="center")

        # --- NOUVEAU : Barre de saisie améliorée ---
        self.input_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.input_frame.place(relx=0.5, rely=0.7, anchor="center", relwidth=0.7)
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.entry = customtkinter.CTkEntry(self.input_frame, placeholder_text="Commencez à taper...", height=50,
                                            border_width=1, border_color="#bdc3c7", corner_radius=25, font=self.font_regular)
        self.entry.grid(row=0, column=0, sticky="ew")
        self.entry.bind("<Return>", self.send_message)

        # --- NOUVEAU : Bouton rond ---
        self.send_button = customtkinter.CTkButton(self.input_frame, text="", image=self.send_icon, width=40, height=40,
                                                   fg_color="#ecf0f1", hover_color="#bdc3c7", corner_radius=20,
                                                   command=self.send_message)
        self.send_button.grid(row=0, column=1, padx=(10, 0))

    def send_message(self, event=None):
        user_input = self.entry.get()
        if not user_input.strip(): return
        if self.app_state == "home":
            self.app_state = "chat"
            self.clear_home_widgets()
            self.setup_chat_view(user_input)
        else:
            self.add_message_to_chat(user_input, "user")
            self.entry.delete(0, "end")
            self.after(1000, lambda: self.add_message_to_chat("Réponse simulée...", "assistant"))

    def clear_home_widgets(self):
        """Nettoie les widgets de la page d'accueil."""
        self.title_label.destroy()
        self.subtitle_label.destroy()
        self.logo_label.destroy()
        self.input_frame.destroy()

    def setup_chat_view(self, first_message):
        """Configure la vue de discussion."""
        self.configure(fg_color=("#f0f2f5", "#2b2b2b")) # Fond légèrement gris
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.chat_frame = customtkinter.CTkScrollableFrame(self, fg_color="transparent")
        self.chat_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.chat_frame.grid_columnconfigure(0, weight=1)

        # Barre de saisie pour la vue chat
        bottom_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        bottom_frame.grid_columnconfigure(0, weight=1)

        self.entry = customtkinter.CTkEntry(bottom_frame, placeholder_text="Écrivez votre message...", height=50, corner_radius=25, font=self.font_regular)
        self.entry.grid(row=0, column=0, sticky="ew")
        self.entry.bind("<Return>", self.send_message)

        self.send_button = customtkinter.CTkButton(bottom_frame, text="", image=self.send_icon, width=40, height=40, corner_radius=20, command=self.send_message)
        self.send_button.grid(row=0, column=1, padx=(10, 0))

        self.add_message_to_chat(first_message, "user")
        self.after(1200, lambda: self.add_message_to_chat("Bonjour ! Bienvenue dans le chat.", "assistant"))

    def add_message_to_chat(self, message, sender):
        if sender == "user":
            label = customtkinter.CTkLabel(self.chat_frame, text=message, wraplength=500, justify="right",
                                           fg_color="#3b82f6", text_color="white", corner_radius=10, font=self.font_regular)
            label.pack(anchor="e", padx=10, pady=5, ipadx=8, ipady=5)
        else:
            label = customtkinter.CTkLabel(self.chat_frame, text=message, wraplength=500, justify="left",
                                           fg_color="#e5e5e5", text_color="black", corner_radius=10, font=self.font_regular)
            label.pack(anchor="w", padx=10, pady=5, ipadx=8, ipady=5)
        self.after(100, self.chat_frame._parent_canvas.yview_moveto, 1.0)

if __name__ == "__main__":
    app = AssistantApp()
    app.mainloop()