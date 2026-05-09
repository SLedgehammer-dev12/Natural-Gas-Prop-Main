import re

filepath = "natural_gas_main/ui/output_panel.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. KPI Frame Titles
# We need to add title_var to self.kpis
old_kpis = """        self.kpis = {
            "Z-Faktörü": {"var": ctk.StringVar(value="-"), "unit": ""},
            "Yoğunluk": {"var": ctk.StringVar(value="-"), "unit": "kg/m³"},
            "Mol Kütlesi": {"var": ctk.StringVar(value="-"), "unit": "kg/mol"},
            "HHV": {"var": ctk.StringVar(value="-"), "unit": "MJ/Sm³"}
        }
        
        cols = len(self.kpis)
        for i, (title, data) in enumerate(self.kpis.items()):
            card = ctk.CTkFrame(self.kpi_frame, corner_radius=10, fg_color=("gray85", "gray25"))
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12)).pack(pady=(5, 0))
            ctk.CTkLabel(
                card, 
                textvariable=data["var"], 
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color="#4CAF50"
            ).pack()
            if data["unit"]:
                ctk.CTkLabel(card, text=data["unit"], font=ctk.CTkFont(size=10)).pack(pady=(0, 5))"""

new_kpis = """        self.kpis = {
            "Z-Faktörü": {"var": ctk.StringVar(value="-"), "unit": "", "title_var": ctk.StringVar(value="Z-Faktörü")},
            "Yoğunluk": {"var": ctk.StringVar(value="-"), "unit": "kg/m³", "title_var": ctk.StringVar(value="Yoğunluk")},
            "Mol Kütlesi": {"var": ctk.StringVar(value="-"), "unit": "kg/mol", "title_var": ctk.StringVar(value="Mol Kütlesi")},
            "HHV": {"var": ctk.StringVar(value="-"), "unit": "MJ/Sm³", "title_var": ctk.StringVar(value="HHV")}
        }
        
        for i, (title, data) in enumerate(self.kpis.items()):
            card = ctk.CTkFrame(self.kpi_frame, corner_radius=10, fg_color=("gray85", "gray25"))
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            
            ctk.CTkLabel(card, textvariable=data["title_var"], font=ctk.CTkFont(size=12)).pack(pady=(5, 0))
            ctk.CTkLabel(
                card, 
                textvariable=data["var"], 
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color="#4CAF50"
            ).pack()
            
            # Unit label var since we want to change it dynamically
            data["unit_var"] = ctk.StringVar(value=data["unit"])
            ctk.CTkLabel(card, textvariable=data["unit_var"], font=ctk.CTkFont(size=10)).pack(pady=(0, 5))"""

content = content.replace(old_kpis, new_kpis)

# 2. Add Secondary Treeview for Comparison under the first one
old_results_tree = """        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.pack(fill=tk.BOTH, expand=True)
        
        # Configure tag styles"""

new_results_tree = """        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.pack(fill=tk.BOTH, expand=True)
        
        # --- SECONDARY TREEVIEW FOR COMPARISON ---
        comp_frame = ctk.CTkFrame(results_tab, fg_color="transparent")
        comp_frame.pack(fill=tk.X, pady=(10, 0))
        ctk.CTkLabel(comp_frame, text="Yöntem Karşılaştırması (Z-Faktörü ve Temel Değerler)", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        
        comp_cols = ("Özellik", "Birim", "GERG-2008", "AGA8-Detail", "HEOS", "SRK", "PR", "Katz", "DAK")
        self.comp_tree = ttk.Treeview(
            results_tab,
            columns=comp_cols,
            show="headings",
            height=6
        )
        
        for col in comp_cols:
            self.comp_tree.heading(col, text=col)
            if col == "Özellik":
                self.comp_tree.column(col, width=150)
            elif col == "Birim":
                self.comp_tree.column(col, width=60)
            else:
                self.comp_tree.column(col, width=90)
                
        comp_scrollbar = ttk.Scrollbar(
            results_tab,
            orient=tk.VERTICAL,
            command=self.comp_tree.yview
        )
        self.comp_tree.configure(yscrollcommand=comp_scrollbar.set)
        
        comp_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.comp_tree.pack(fill=tk.X, pady=(5, 5))
        
        # Configure tag styles"""
content = content.replace(old_results_tree, new_results_tree)

# 3. Modify update_results / display_results
old_kpi_update = """        # Update KPIs
        # Reset KPIs
        for k in self.kpis: self.kpis[k]["var"].set("-")
        
        # Find required values in display list
        for prop, val, unit in results_list:
            if "Sıkıştırılabilirlik" in prop:
                self.kpis["Z-Faktörü"]["var"].set(val)
            elif "Gerçek - ρ" in prop:
                self.kpis["Yoğunluk"]["var"].set(val)
                self.kpis["Yoğunluk"]["unit"] = unit # Update unit
            elif "Mol Kütlesi" in prop:
                self.kpis["Mol Kütlesi"]["var"].set(val)
            elif "(Hacimsel)" in prop and "HHV" in prop:
                self.kpis["HHV"]["var"].set(val)
                self.kpis["HHV"]["unit"] = unit"""

new_kpi_update = """        # Update KPIs
        # Reset KPIs
        for k in self.kpis: 
            self.kpis[k]["var"].set("-")
            
        self.kpis["Z-Faktörü"]["title_var"].set(f"Z-Faktörü\\n({result.backend_used})")
        self.kpis["Yoğunluk"]["title_var"].set(f"Yoğunluk\\n({result.backend_used})")
        self.kpis["Mol Kütlesi"]["title_var"].set(f"Mol Kütlesi\\n({result.backend_used})")
        
        heating_method = result.heating.calculation_method if result.heating else "Bulunamadı"
        self.kpis["HHV"]["title_var"].set(f"HHV\\n({heating_method})")
        
        # Find required values in display list
        for prop, val, unit in results_list:
            if "Sıkıştırılabilirlik" in prop:
                self.kpis["Z-Faktörü"]["var"].set(val)
            elif "Gerçek - ρ" in prop:
                self.kpis["Yoğunluk"]["var"].set(val)
                self.kpis["Yoğunluk"]["unit_var"].set(unit) # Update unit
            elif "Mol Kütlesi" in prop:
                self.kpis["Mol Kütlesi"]["var"].set(val)
            elif "(Hacimsel)" in prop and "HHV" in prop:
                self.kpis["HHV"]["var"].set(val)
                self.kpis["HHV"]["unit_var"].set(unit)"""
content = content.replace(old_kpi_update, new_kpi_update)


# 4. Modify populate comp_tree
old_clear = """    def clear_results(self) -> None:
        \"\"\"Clear all displayed results.\"\"\"
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        self.phase_ax.clear()"""

new_clear = """    def clear_results(self) -> None:
        \"\"\"Clear all displayed results.\"\"\"
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        if hasattr(self, 'comp_tree'):
            for item in self.comp_tree.get_children():
                self.comp_tree.delete(item)
        
        self.phase_ax.clear()"""
content = content.replace(old_clear, new_clear)


old_populate_tree = """        for prop, val, unit in results_list:
            tags = ()
            if "- " in prop and " -" in prop:
                tags = ('header',)
            elif val == "Hesaplanamadı" or "Hata" in prop:
                tags = ('error_header',)
                
            self.results_tree.insert("", tk.END, values=(prop, val, unit), tags=tags)"""

new_populate_tree = """        for prop, val, unit in results_list:
            tags = ()
            if "- " in prop and " -" in prop:
                tags = ('header',)
            elif val == "Hesaplanamadı" or "Hata" in prop:
                tags = ('error_header',)
                
            self.results_tree.insert("", tk.END, values=(prop, val, unit), tags=tags)
            
        # Populate Comparison Tree
        if hasattr(self, 'comp_tree') and result.z_factor_comparison:
            comp_methods = ["GERG-2008", "AGA8-Detail", "HEOS", "SRK", "PR", "Standing-Katz", "DAK"]
            # Convert to dict by method
            comp_map = {c.method: c for c in result.z_factor_comparison}
            
            # Helper to extract value
            def _get_val(method_name, attr_name, decimals):
                c = comp_map.get(method_name)
                if not c: return "-"
                val = getattr(c, attr_name, None)
                if val is None: return "-"
                return f"{val:.{decimals}f}"
                
            rows = [
                ("Z-Faktörü", "-", "z_factor", 5),
                ("Yoğunluk (ρ)", "kg/m³", "density", 4),
                ("Mol Kütlesi (M)", "kg/mol", "molar_mass", 4),
                ("Entalpi (h)", "kJ/kg", "enthalpy", 4),
                ("Entropi (s)", "kJ/kg·K", "entropy", 4),
                ("İzobarik Isı Kap. (Cp)", "kJ/kg·K", "cp", 4),
            ]
            
            for row_name, unit, attr_name, decimals in rows:
                row_vals = [row_name, unit]
                for m in comp_methods:
                    row_vals.append(_get_val(m, attr_name, decimals))
                self.comp_tree.insert("", tk.END, values=row_vals)"""
content = content.replace(old_populate_tree, new_populate_tree)


with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched output_panel.py")
