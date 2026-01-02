import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, messagebox
import math
import datetime

# IMPORT LOGIC FROM THE OTHER FILE
from network_logic import NetworkSimulator

# =============================================================================
#  VISUAL THEME
# =============================================================================
THEME = {
    "window_bg": "#0F172A",      # Deep Navy
    "panel_bg": "#1E293B",       # Lighter Navy
    "canvas_bg": "#0B1120",      # Almost Black
    "grid_color": "#1E293B",     # Faint grid lines
    
    "text_main": "#F1F5F9",      # White-ish
    "text_dim": "#94A3B8",       # Grey
    
    "accent_primary": "#38BDF8", # Neon Blue (Area 0 / Actions)
    "accent_secondary": "#F472B6", # Neon Pink (Area 1 / Selection)
    "accent_warn": "#FACC15",    # Yellow (ABR)
    "accent_danger": "#EF4444",  # Red (Error/Down)
    "accent_success": "#22C55E", # Green (Success/Up)
    
    "font_header": ("Segoe UI", 12, "bold"),
    "font_body": ("Segoe UI", 10),
    "font_mono": ("Consolas", 10),
}

# Animation Settings
ANIMATION_SPEED_MS = 20
PACKET_PIXELS_PER_FRAME = 9.0

# =============================================================================
#  GUI CLASSES
# =============================================================================

class ModernButton(tk.Label):
    """Custom Flat Button with Hover Effects"""
    def __init__(self, parent, text, cmd, bg_color, fg_color="white", width=20):
        super().__init__(parent, text=text, bg=bg_color, fg=fg_color, 
                         font=THEME['font_body'], pady=8, cursor="hand2")
        self.bg_normal = bg_color
        self.cmd = cmd
        self.bind("<Enter>", self._on_hover)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.pack(pady=5, padx=10, fill="x")

    def _on_hover(self, e):
        self.config(bg="#475569") # Grey-ish hover
        if self.bg_normal == THEME['accent_success']: self.config(bg="#4ADE80")

    def _on_leave(self, e):
        self.config(bg=self.bg_normal)

    def _on_click(self, e):
        self.cmd()

class ModernApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NEXUS NETWORK SIMULATOR [ULTIMATE]")
        self.root.geometry("1400x900")
        self.root.configure(bg=THEME['window_bg'])
        
        self.sim = NetworkSimulator()
        self.selected_router = None
        self.hovered_router = None
        self.packets = []
        
        self._build_layout()
        self._refresh_sim()

    def _build_layout(self):
        # 1. Header
        header = tk.Frame(self.root, bg=THEME['panel_bg'], height=60)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        
        tk.Label(header, text="NEXUS", fg=THEME['accent_primary'], bg=THEME['panel_bg'], 
                 font=("Impact", 24)).pack(side="left", padx=20)
        tk.Label(header, text="// ADVANCED ROUTING SIMULATION", fg=THEME['text_dim'], bg=THEME['panel_bg'], 
                 font=THEME['font_mono']).pack(side="left", pady=15)

        # 2. Sidebar (Controls)
        sidebar = tk.Frame(self.root, bg=THEME['panel_bg'], width=280)
        sidebar.pack(side="left", fill="y", padx=2)
        sidebar.pack_propagate(False)
        self._build_sidebar(sidebar)

        # 3. Content Area
        content = tk.Frame(self.root, bg=THEME['window_bg'])
        content.pack(side="left", fill="both", expand=True)

        # 4. Canvas (Top Center)
        self.canvas = tk.Canvas(content, bg=THEME['canvas_bg'], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        self._draw_grid()
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # 5. Log & Table Panel (Right Side)
        right_panel = tk.Frame(self.root, bg=THEME['panel_bg'], width=400)
        right_panel.pack(side="right", fill="y")
        right_panel.pack_propagate(False)
        self._build_right_panel(right_panel)

    def _build_sidebar(self, parent):
        self._lbl_header(parent, "CONFIGURATION")
        
        # Scenario
        self.var_scen = tk.StringVar(value="Complex (Default)")
        self._opt_menu(parent, self.var_scen, ["Complex (Default)", "Simple Ring", "Full Mesh"], self._on_config_change)
        
        # Protocol
        self.var_proto = tk.StringVar(value="Link-State (OSPF)")
        self._opt_menu(parent, self.var_proto, ["Link-State (OSPF)", "Distance-Vector (RIP)", "BGP (Path-Vector)"], self._on_config_change)
        
        # Area Switch
        self.var_area = tk.BooleanVar(value=False)
        cb = tk.Checkbutton(parent, text="Enable OSPF Areas", variable=self.var_area, 
                            bg=THEME['panel_bg'], fg=THEME['text_main'], 
                            selectcolor=THEME['window_bg'], activebackground=THEME['panel_bg'], 
                            activeforeground="white", command=self._on_config_change)
        cb.pack(pady=10, anchor="w", padx=20)
        
        self._spacer(parent)
        self._lbl_header(parent, "ACTIONS")
        
        ModernButton(parent, "⚡ RUN CONVERGENCE", self._refresh_sim, THEME['accent_success'], "black")
        
        # Packet Injection
        pkt_frame = tk.Frame(parent, bg=THEME['panel_bg'])
        pkt_frame.pack(fill="x", padx=10, pady=10)
        self.e_src = self._entry(pkt_frame, "A"); self.e_src.pack(side="left", padx=5)
        tk.Label(pkt_frame, text="➜", bg=THEME['panel_bg'], fg="white").pack(side="left")
        self.e_dst = self._entry(pkt_frame, "F"); self.e_dst.pack(side="left", padx=5)
        ModernButton(pkt_frame, "SEND", self._send_packet, THEME['accent_primary'], "black")

        self._spacer(parent)
        self._lbl_header(parent, "MANIPULATION")
        ModernButton(parent, "❌ Toggle Link", self._action_toggle_link, THEME['accent_danger'])
        ModernButton(parent, "💲 Change Cost", self._action_change_cost, "#64748B")

    def _build_right_panel(self, parent):
        # Routing Table
        self._lbl_header(parent, "ROUTING TABLE")
        self.lbl_selected = tk.Label(parent, text="Select a Node...", bg=THEME['panel_bg'], fg=THEME['accent_secondary'], font=THEME['font_mono'])
        self.lbl_selected.pack(pady=5)
        
        self.table_view = tk.Text(parent, height=15, bg=THEME['canvas_bg'], fg=THEME['text_main'], 
                                  font=THEME['font_mono'], relief="flat", padx=10, pady=10)
        self.table_view.pack(fill="x", padx=10, pady=5)
        
        # Console Log
        self._spacer(parent)
        self._lbl_header(parent, "SYSTEM LOGS")
        self.log_view = scrolledtext.ScrolledText(parent, bg="#000000", fg=THEME['accent_success'], 
                                                  font=THEME['font_mono'], relief="flat")
        self.log_view.pack(fill="both", expand=True, padx=10, pady=10)

    # --- WIDGET HELPERS ---
    def _lbl_header(self, p, t): tk.Label(p, text=t, bg=THEME['panel_bg'], fg=THEME['text_dim'], font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(20,5))
    def _spacer(self, p): tk.Frame(p, bg=THEME['panel_bg'], height=10).pack()
    def _entry(self, p, default): 
        e = tk.Entry(p, bg=THEME['window_bg'], fg="white", font=THEME['font_mono'], width=5, relief="flat", insertbackground="white")
        e.insert(0, default)
        return e
    def _opt_menu(self, p, var, options, cmd):
        m = tk.OptionMenu(p, var, *options, command=cmd)
        m.config(bg=THEME['window_bg'], fg="white", highlightthickness=0, relief="flat", activebackground=THEME['accent_primary'])
        m["menu"].config(bg=THEME['window_bg'], fg="white")
        m.pack(fill="x", padx=20, pady=5)

    def _draw_grid(self):
        w, h = 2000, 2000
        for i in range(0, w, 40):
            self.canvas.create_line(i, 0, i, h, fill=THEME['grid_color'])
        for i in range(0, h, 40):
            self.canvas.create_line(0, i, w, i, fill=THEME['grid_color'])

    # --- LOGIC INTEGRATION ---
    def _on_config_change(self, _=None):
        self.sim.load_scenario(self.var_scen.get())
        self.sim.protocol = self.var_proto.get()
        self.sim.areas_enabled = self.var_area.get()
        self.selected_router = None
        self._refresh_sim()

    def _refresh_sim(self):
        logs = self.sim.run_simulation()
        self.log_view.delete("1.0", "end")
        for l in logs: self._log(l)
        self._animate_loop()

    def _log(self, msg):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_view.insert("end", f"[{ts}] {msg}\n")
        self.log_view.see("end")

    # --- DRAWING & ANIMATION ---
    def _draw(self):
        self.canvas.delete("dynamic") # Clear moving elements
        
        # 1. Links
        for l in self.sim.links:
            r1, r2 = self.sim.routers[l.r1], self.sim.routers[l.r2]
            color = "#475569" if l.active else THEME['accent_danger']
            width = 2 if l.active else 1
            dash = None if l.active else (4, 4)
            
            if self.hovered_router and (self.hovered_router in [l.r1, l.r2]):
                color = "white"
                width = 3
                
            self.canvas.create_line(r1.x, r1.y, r2.x, r2.y, fill=color, width=width, dash=dash, tags="dynamic")
            
            # Cost label
            mx, my = (r1.x+r2.x)/2, (r1.y+r2.y)/2
            self.canvas.create_rectangle(mx-12, my-10, mx+12, my+10, fill=THEME['canvas_bg'], outline=color, tags="dynamic")
            self.canvas.create_text(mx, my, text=str(l.cost), fill="white", font=("Arial", 9), tags="dynamic")

        # 2. Routers
        for rid, r in self.sim.routers.items():
            if r.area_id == 0: base_col = THEME['accent_primary']
            else: base_col = THEME['accent_secondary']
            
            outline = base_col
            fill = THEME['canvas_bg']
            radius = 25
            
            if rid == self.selected_router:
                fill = base_col
                outline = "white"
                radius = 28
            elif rid == self.hovered_router:
                fill = "#334155"
            
            if rid == self.selected_router:
                self.canvas.create_oval(r.x-35, r.y-35, r.x+35, r.y+35, fill="", outline=base_col, width=1, tags="dynamic")

            self.canvas.create_oval(r.x-radius, r.y-radius, r.x+radius, r.y+radius, 
                                    fill=fill, outline=outline, width=3, tags="dynamic")
            
            text_col = "white" if rid != self.selected_router else "black"
            self.canvas.create_text(r.x, r.y, text=rid, fill=text_col, font=("Segoe UI", 12, "bold"), tags="dynamic")
            
            if r.is_abr:
                self.canvas.create_text(r.x, r.y+38, text="ABR", fill=THEME['accent_warn'], font=("Consolas", 8, "bold"), tags="dynamic")
            elif self.sim.areas_enabled:
                 self.canvas.create_text(r.x, r.y+38, text=f"AREA {r.area_id}", fill="#64748B", font=("Consolas", 8), tags="dynamic")

        # 3. Packets
        for p in self.packets:
            self.canvas.create_oval(p['x']-6, p['y']-6, p['x']+6, p['y']+6, 
                                    fill=THEME['accent_success'], outline="white", width=2, tags="dynamic")
            if len(p['hist']) > 0:
                prev = self.sim.routers[p['hist'][-1]]
                self.canvas.create_line(prev.x, prev.y, p['x'], p['y'], fill=THEME['accent_success'], width=1, tags="dynamic")

    def _update_table(self):
        self.table_view.delete("1.0", "end")
        if not self.selected_router:
            self.lbl_selected.config(text="Select a Router Node", fg=THEME['text_dim'])
            self.table_view.insert("end", "\n   Select a node to inspect routing.")
            return

        r = self.sim.routers[self.selected_router]
        self.lbl_selected.config(text=f"ROUTER {r.id} CONFIGURATION", fg="white")
        
        self.table_view.insert("end", f"{'DEST':<8} {'NEXT':<8} {'METRIC':<8}\n", "header")
        self.table_view.insert("end", "-"*35 + "\n", "dim")
        
        for d in sorted(r.routing_table.keys()):
            nh, c = r.routing_table[d]
            self.table_view.insert("end", f"{d:<8} {str(nh):<8} {str(c):<8}\n")
        
        self.table_view.tag_config("header", foreground=THEME['accent_primary'])
        self.table_view.tag_config("dim", foreground=THEME['text_dim'])

    # --- ANIMATION LOOP ---
    def _animate_loop(self):
        self._update_physics()
        self._draw()
        self._update_table()
        self.root.after(ANIMATION_SPEED_MS, self._animate_loop)

    def _update_physics(self):
        active_pkts = []
        for p in self.packets:
            if p['curr'] == p['dest']: continue
            
            r_curr = self.sim.routers[p['curr']]
            nh = r_curr.routing_table.get(p['dest'], (None, None))[0]
            
            if not nh or nh not in self.sim.routers:
                if not p.get('lost'):
                    self._log(f"⚠ Packet Lost at {p['curr']}")
                    p['lost'] = True
                continue
            
            r_next = self.sim.routers[nh]
            
            dx = r_next.x - r_curr.x
            dy = r_next.y - r_curr.y
            dist = math.hypot(dx, dy) or 1
            
            p['prog'] += PACKET_PIXELS_PER_FRAME / dist
            
            if p['prog'] >= 1.0:
                p['curr'] = nh
                p['prog'] = 0.0
                p['x'], p['y'] = r_next.x, r_next.y
                p['hist'].append(nh)
                self._log(f"[Packet {p['start']}->{p['dest']}] Reached {nh}")
                
                if nh == p['dest']:
                    self._log(f"✔ PACKET DELIVERED: {p['start']} -> {p['dest']}")
            else:
                p['x'] = r_curr.x + dx * p['prog']
                p['y'] = r_curr.y + dy * p['prog']
            
            if p['curr'] != p['dest']:
                active_pkts.append(p)
        
        self.packets = active_pkts

    # --- INTERACTION ---
    def _on_mouse_move(self, e):
        found = None
        for rid, r in self.sim.routers.items():
            if math.hypot(r.x-e.x, r.y-e.y) < 30:
                found = rid
                break
        self.hovered_router = found

    def _on_canvas_click(self, e):
        if self.hovered_router:
            self.selected_router = self.hovered_router
            self._update_table()

    def _send_packet(self):
        s, d = self.e_src.get().upper(), self.e_dst.get().upper()
        if s in self.sim.routers and d in self.sim.routers:
            self.packets.append({
                'start': s, 'dest': d, 'curr': s,
                'x': self.sim.routers[s].x, 'y': self.sim.routers[s].y,
                'prog': 0.0, 'hist': [s]
            })
            self._log(f"→ Dispatching Packet {s} to {d}")
        else:
            messagebox.showerror("Input Error", "Invalid Router IDs")

    def _action_toggle_link(self):
        res = simpledialog.askstring("Action", "Enter Link (e.g. A-B)")
        if res:
            parts = res.upper().split('-')
            if len(parts) == 2:
                l = self.sim.get_link(parts[0], parts[1])
                if l: l.active = not l.active; self._refresh_sim()

    def _action_change_cost(self):
        res = simpledialog.askstring("Action", "Enter Cost (e.g. A-B-10)")
        if res:
            parts = res.upper().split('-')
            if len(parts) == 3:
                l = self.sim.get_link(parts[0], parts[1])
                if l: l.cost = int(parts[2]); self._refresh_sim()

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernApp(root)
    root.mainloop()