import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import csv
from db import init_db, query, execute

APP_TITLE = "Ewidencja Ubrań ZAZ — Desktop (SQLite)"
DATE_FMT = "%Y-%m-%d %H:%M"

def now():
    return datetime.now().strftime(DATE_FMT)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("980x640")
        self.style = ttk.Style(self)
        # Notebook
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        self.emp = EmployeesFrame(nb)
        self.items = ItemsFrame(nb)
        self.issue = IssueFrame(nb)
        self.stock = StockFrame(nb)

        nb.add(self.emp, text="Pracownicy")
        nb.add(self.items, text="Ubrania")
        nb.add(self.issue, text="Wydanie / Zwrot")
        nb.add(self.stock, text="Stany i braki")


class EmployeeCard(tk.Toplevel):
    def __init__(self, master, emp_id: int):
        super().__init__(master)
        self.emp_id = emp_id
        self.title(f"Karta pracownika #{emp_id}")
        self.geometry("760x520")
        self.resizable(True, True)

        # Vars
        self.v_name = tk.StringVar()
        self.v_department = tk.StringVar()
        self.v_position = tk.StringVar()
        self.v_email = tk.StringVar()
        self.v_phone = tk.StringVar()
        self.v_active = tk.BooleanVar(value=True)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        # Dane
        frm = ttk.Frame(nb)
        nb.add(frm, text="Dane")
        fields = [
            ("Imi i nazwisko", self.v_name),
            ("Dzia", self.v_department),
            ("Stanowisko", self.v_position),
            ("Email", self.v_email),
            ("Telefon", self.v_phone),
        ]
        for i, (label, var) in enumerate(fields):
            ttk.Label(frm, text=label).grid(row=i, column=0, sticky="e", padx=6, pady=4)
            ttk.Entry(frm, textvariable=var, width=40).grid(row=i, column=1, sticky="w", padx=6, pady=4)
        ttk.Checkbutton(frm, text="Aktywny", variable=self.v_active).grid(row=0, column=2, padx=6)
        box = ttk.Frame(frm); box.grid(row=0, column=3, rowspan=3, padx=6, pady=4, sticky="n")
        ttk.Button(box, text="Zapisz", command=self.save).pack(fill="x", pady=2)
        ttk.Button(box, text="Wydaj ubranie", command=self.quick_issue).pack(fill="x", pady=2)

        self.lbl_summary = ttk.Label(frm, text="")
        self.lbl_summary.grid(row=len(fields), column=0, columnspan=4, sticky="w", padx=6, pady=8)

        # Wydane (otwarte)
        frm_open = ttk.Frame(nb); nb.add(frm_open, text="Wydane (otwarte)")
        self.tree_open = ttk.Treeview(frm_open, columns=("id","date","item","inv","qty"), show="headings", height=12)
        for col, txt, w in [("id","ID",60),("date","Data",150),("item","Ubranie",240),("inv","Nr ewid.",110),("qty","Ilo",60)]:
            self.tree_open.heading(col, text=txt); self.tree_open.column(col, width=w, anchor="w")
        self.tree_open.pack(fill="both", expand=True, padx=8, pady=8)

        # Historia ruchw
        frm_hist = ttk.Frame(nb); nb.add(frm_hist, text="Historia ruchw")
        self.tree_hist = ttk.Treeview(frm_hist, columns=("date","type","item","inv","qty","note"), show="headings", height=12)
        for col, txt, w in [("date","Data",150),("type","Typ",90),("item","Ubranie",240),("inv","Nr ewid.",110),("qty","Ilo",60),("note","Notatka",220)]:
            self.tree_hist.heading(col, text=txt); self.tree_hist.column(col, width=w, anchor="w")
        self.tree_hist.pack(fill="both", expand=True, padx=8, pady=8)

        self.load()

    def load(self):
        rows = query("SELECT * FROM employees WHERE id = ?", (self.emp_id,))
        if not rows:
            messagebox.showerror("Karta", "Nie znaleziono pracownika."); self.destroy(); return
        r = rows[0]
        self.v_name.set(r["name"] or "")
        self.v_department.set(r["department"] or "")
        self.v_position.set(r["position"] or "")
        self.v_email.set(r["email"] or "")
        self.v_phone.set(r["phone"] or "")
        self.v_active.set(bool(r["active"]))

        open_rows = query(
            """
            SELECT i.id, i.issue_date, it.name as item, it.inv_number, i.qty
            FROM issues i
            JOIN items it ON it.id = i.item_id
            WHERE i.employee_id = ? AND i.status = 'Wydane'
            ORDER BY i.id DESC
            """, (self.emp_id,))
        for i in self.tree_open.get_children(): self.tree_open.delete(i)
        for rr in open_rows:
            self.tree_open.insert("", "end", values=(rr["id"], rr["issue_date"], rr["item"], rr["inv_number"] or "", rr["qty"]))

        hist_rows = query(
            """
            SELECT m.move_date, m.move_type, it.name as item, it.inv_number, m.qty, m.note
            FROM movements m
            LEFT JOIN items it ON it.id = m.item_id
            WHERE m.employee_id = ?
            ORDER BY m.id DESC
            """, (self.emp_id,))
        for i in self.tree_hist.get_children(): self.tree_hist.delete(i)
        for rr in hist_rows:
            self.tree_hist.insert("", "end", values=(rr["move_date"], rr["move_type"], rr["item"] or "", rr["inv_number"] or "", rr["qty"], rr["note"] or ""))

        self.lbl_summary.configure(text=f"Otwarte wydania: {len(open_rows)} | Aktywny: {'Tak' if self.v_active.get() else 'Nie'}")

    def save(self):
        name = self.v_name.get().strip()
        if not name:
            messagebox.showwarning("Dane", "Imi i nazwisko nie moe by7 puste."); return
        execute(
            "UPDATE employees SET name=?, department=?, position=?, email=?, phone=?, active=? WHERE id=?",
            (name,
             self.v_department.get().strip(),
             self.v_position.get().strip(),
             self.v_email.get().strip(),
             self.v_phone.get().strip(),
             1 if self.v_active.get() else 0,
             self.emp_id)
        )
        messagebox.showinfo("Zapis", "Zapisano zmiany.")
        self.load()
        try:
            self.master.emp.load()
            self.master.issue.refresh_lists()
        except Exception:
            pass

    def quick_issue(self):
        try:
            app = self.master  # App
            app.issue.select_employee_by_id(self.emp_id)
            app.issue.emp_combo.focus_set()
        except Exception:
            pass

class EmployeesFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        # Form
        form = ttk.Frame(self)
        form.pack(side="top", fill="x", padx=10, pady=5)
        self.name = tk.StringVar()
        self.department = tk.StringVar()
        self.position = tk.StringVar()
        self.email = tk.StringVar()
        self.phone = tk.StringVar()
        self.active = tk.BooleanVar(value=True)

        fields = [
            ("Imię i nazwisko", self.name),
            ("Dział", self.department),
            ("Stanowisko", self.position),
            ("Email", self.email),
            ("Telefon", self.phone)
        ]
        for i, (label, var) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=i, column=0, sticky="e", padx=4, pady=2)
            ttk.Entry(form, textvariable=var, width=32).grid(row=i, column=1, sticky="w", padx=4, pady=2)
        ttk.Checkbutton(form, text="Aktywny", variable=self.active).grid(row=0, column=2, padx=8)

        btns = ttk.Frame(form); btns.grid(row=0, column=3, rowspan=3, padx=8)
        ttk.Button(btns, text="Dodaj", command=self.add_emp).pack(fill="x", pady=2)
        ttk.Button(btns, text="Odśwież", command=self.load).pack(fill="x", pady=2)

        # Table
        self.tree = ttk.Treeview(self, columns=("id","name","department","position","active","email","phone"),
                                 show="headings", height=16)
        for col, txt, w in [
            ("id","ID",40), ("name","Imię i nazwisko",200), ("department","Dział",120),
            ("position","Stanowisko",120), ("active","Aktywny",80), ("email","Email",180), ("phone","Telefon",120)
        ]:
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        # Double click to open card
        self.tree.bind("<Double-1>", self.on_tree_double)
        # Context menu
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Otwrz kart", command=self.open_selected_card)
        self.menu.add_command(label="Kopiuj email", command=lambda: self.copy_from_selected(5))
        self.menu.add_command(label="Kopiuj telefon", command=lambda: self.copy_from_selected(6))
        self.menu.add_separator()
        self.menu.add_command(label="Aktywuj/Dezaktywuj", command=self.toggle_active_selected)
        self.tree.bind("<Button-3>", self.on_right_click)
        self.load()

    def add_emp(self):
        if not self.name.get().strip():
            messagebox.showwarning("Brak danych", "Wpisz imię i nazwisko.")
            return
        execute("""INSERT INTO employees(name,department,position,active,email,phone)
                   VALUES(?,?,?,?,?,?)""",
                (self.name.get().strip(), self.department.get().strip(),
                 self.position.get().strip(), 1 if self.active.get() else 0,
                 self.email.get().strip(), self.phone.get().strip()))
        self.clear_form(); self.load()

    def clear_form(self):
        self.name.set(""); self.department.set(""); self.position.set("")
        self.email.set(""); self.phone.set(""); self.active.set(True)

    def load(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        rows = query("SELECT * FROM employees ORDER BY id DESC")
        for r in rows:
            self.tree.insert("", "end", values=(r["id"], r["name"], r["department"],
                                                r["position"], "Tak" if r["active"] else "Nie",
                                                r["email"], r["phone"]))

    def get_selected_employee_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        vals = self.tree.item(sel[0]).get("values")
        if not vals:
            return None
        try:
            return int(vals[0])
        except Exception:
            return None

    def open_selected_card(self):
        emp_id = self.get_selected_employee_id()
        if not emp_id:
            messagebox.showwarning("Wybr", "Zaznacz pracownika z listy.")
            return
        EmployeeCard(self.winfo_toplevel(), emp_id)

    def on_tree_double(self, event):
        try:
            iid = self.tree.identify_row(event.y)
            if iid:
                self.tree.selection_set(iid)
                self.open_selected_card()
        except Exception:
            pass

    def on_right_click(self, event):
        try:
            iid = self.tree.identify_row(event.y)
            if iid:
                self.tree.selection_set(iid)
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            try:
                self.menu.grab_release()
            except Exception:
                pass

    def copy_from_selected(self, idx):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0]).get("values")
        try:
            v = str(vals[idx]) if idx < len(vals) else ""
            self.clipboard_clear(); self.clipboard_append(v)
        except Exception:
            pass

    def toggle_active_selected(self):
        emp_id = self.get_selected_employee_id()
        if not emp_id:
            return
        row = query("SELECT active FROM employees WHERE id = ?", (emp_id,))
        if not row:
            return
        new_val = 0 if row[0]["active"] else 1
        execute("UPDATE employees SET active = ? WHERE id = ?", (new_val, emp_id))
        self.load()

class ItemsFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        form = ttk.Frame(self); form.pack(side="top", fill="x", padx=10, pady=5)

        self.name = tk.StringVar()
        self.type = tk.StringVar()
        self.size = tk.StringVar()
        self.color = tk.StringVar()
        self.inv_number = tk.StringVar()
        self.min_stock = tk.IntVar(value=0)
        self.stock = tk.IntVar(value=0)
        self.location = tk.StringVar()
        self.active = tk.BooleanVar(value=True)

        fields = [
            ("Nazwa", self.name), ("Typ", self.type), ("Rozmiar", self.size),
            ("Kolor", self.color), ("Numer ewidencyjny", self.inv_number),
            ("Stan minimalny", self.min_stock), ("Stan magazynowy", self.stock),
            ("Lokalizacja", self.location)
        ]
        for i, (label, var) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=i//4, column=(i%4)*2, sticky="e", padx=4, pady=2)
            entry = ttk.Entry(form, textvariable=var, width=20)
            entry.grid(row=i//4, column=(i%4)*2+1, sticky="w", padx=4, pady=2)
        ttk.Checkbutton(form, text="Aktywne", variable=self.active).grid(row=0, column=8, padx=8)

        btns = ttk.Frame(form); btns.grid(row=0, column=9, rowspan=2, padx=8)
        ttk.Button(btns, text="Dodaj/Przyjmij", command=self.add_item).pack(fill="x", pady=2)
        ttk.Button(btns, text="Odśwież", command=self.load).pack(fill="x", pady=2)

        # Table
        self.tree = ttk.Treeview(self, columns=("id","name","type","size","color","inv","min","stock","loc","active"),
                                 show="headings", height=15)
        headers = [("id","ID",40), ("name","Nazwa",180), ("type","Typ",120), ("size","Rozmiar",90),
                   ("color","Kolor",90), ("inv","Nr ewid.",120), ("min","Stan min.",90),
                   ("stock","Stan",80), ("loc","Lokalizacja",120), ("active","Aktywne",80)]
        for col, txt, w in headers:
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.load()

    def add_item(self):
        if not self.name.get().strip():
            messagebox.showwarning("Brak danych", "Wpisz nazwę.")
            return
        # insert or update by inv_number
        inv = self.inv_number.get().strip() or None
        if inv:
            exist = query("SELECT id FROM items WHERE inv_number = ?", (inv,))
        else:
            exist = []
        if exist:
            # treat as Przyjęcie (increase stock)
            item_id = exist[0]["id"]
            execute("UPDATE items SET stock = stock + ?, active = ? WHERE id = ?",
                    (int(self.stock.get()), 1 if self.active.get() else 0, item_id))
            execute("""INSERT INTO movements(move_date, move_type, item_id, employee_id, qty, note)
                       VALUES(?,?,?,?,?,?)""",
                    (now(), "Przyjęcie", item_id, None, int(self.stock.get()), "Przyjęcie (istniejący)"))
        else:
            item_id = execute("""INSERT INTO items(name,type,size,color,inv_number,min_stock,stock,location,active)
                                 VALUES(?,?,?,?,?,?,?,?,?)""",
                              (self.name.get().strip(), self.type.get().strip(), self.size.get().strip(),
                               self.color.get().strip(), self.inv_number.get().strip() or None,
                               int(self.min_stock.get()), int(self.stock.get()), self.location.get().strip(),
                               1 if self.active.get() else 0))
            execute("""INSERT INTO movements(move_date, move_type, item_id, employee_id, qty, note)
                       VALUES(?,?,?,?,?,?)""",
                    (now(), "Przyjęcie", item_id, None, int(self.stock.get()), "Przyjęcie (nowy)"))
        self.clear_form(); self.load()

    def clear_form(self):
        self.name.set(""); self.type.set(""); self.size.set(""); self.color.set("")
        self.inv_number.set(""); self.min_stock.set(0); self.stock.set(0)
        self.location.set(""); self.active.set(True)

    def load(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        rows = query("SELECT * FROM items ORDER BY id DESC")
        for r in rows:
            self.tree.insert("", "end", values=(r["id"], r["name"], r["type"], r["size"], r["color"],
                                                r["inv_number"] or "", r["min_stock"], r["stock"], r["location"] or "",
                                                "Tak" if r["active"] else "Nie"))

class IssueFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        wrap = ttk.Frame(self); wrap.pack(fill="x", padx=10, pady=5)

        # employee select
        ttk.Label(wrap, text="Pracownik").grid(row=0, column=0, sticky="e")
        self.emp_combo = ttk.Combobox(wrap, width=32, state="readonly")
        self.emp_combo.grid(row=0, column=1, padx=4, pady=2)

        # item select
        ttk.Label(wrap, text="Ubranie (nr ewid.)").grid(row=0, column=2, sticky="e")
        self.item_inv = tk.StringVar()
        ttk.Entry(wrap, textvariable=self.item_inv, width=20).grid(row=0, column=3, padx=4)

        ttk.Label(wrap, text="Ilość").grid(row=0, column=4, sticky="e")
        self.qty = tk.IntVar(value=1)
        ttk.Entry(wrap, textvariable=self.qty, width=6).grid(row=0, column=5, padx=4)

        ttk.Button(wrap, text="Wydaj", command=self.issue_item).grid(row=0, column=6, padx=6)
        ttk.Button(wrap, text="Zwrot", command=self.return_item).grid(row=0, column=7, padx=6)
        ttk.Button(wrap, text="Odśwież listy", command=self.refresh_lists).grid(row=0, column=8, padx=6)

        # open issues table
        self.tree = ttk.Treeview(self, columns=("id","date","emp","item","inv","qty","status"),
                                 show="headings", height=16)
        for col, txt, w in [
            ("id","ID",50), ("date","Data wydania",150), ("emp","Pracownik",200),
            ("item","Ubranie",220), ("inv","Nr ewid.",110), ("qty","Ilość",60), ("status","Status",100)
        ]:
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        self.refresh_lists()
        self.load_open()

    def refresh_lists(self):
        emps = query("SELECT id, name FROM employees WHERE active=1 ORDER BY name")
        self.emp_map = {f'{e["name"]} (#{e["id"]})': e["id"] for e in emps}
        self.emp_combo["values"] = list(self.emp_map.keys())
        if emps and not self.emp_combo.get():
            self.emp_combo.current(0)

    def select_employee_by_id(self, emp_id: int):
        # odw listy i ustaw wybranego pracownika
        self.refresh_lists()
        for display, val in self.emp_map.items():
            if val == emp_id:
                self.emp_combo.set(display)
                break

    def load_open(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        rows = query("""SELECT i.id, i.issue_date, e.name as emp_name, it.name as item_name, it.inv_number, i.qty, i.status
                        FROM issues i
                        JOIN employees e ON e.id = i.employee_id
                        JOIN items it ON it.id = i.item_id
                        WHERE i.status='Wydane'
                        ORDER BY i.id DESC""")
        for r in rows:
            self.tree.insert("", "end", values=(r["id"], r["issue_date"], r["emp_name"],
                                                r["item_name"], r["inv_number"] or "", r["qty"], r["status"]))

    def issue_item(self):
        if not self.emp_combo.get():
            messagebox.showwarning("Brak danych", "Wybierz pracownika."); return
        inv = self.item_inv.get().strip()
        if not inv:
            messagebox.showwarning("Brak danych", "Wpisz numer ewidencyjny ubrania."); return
        item = query("SELECT * FROM items WHERE inv_number = ? AND active=1", (inv,))
        if not item:
            messagebox.showerror("Brak", "Nie znaleziono aktywnego ubrania o tym numerze."); return
        item = item[0]
        q = int(self.qty.get())
        if q <= 0:
            messagebox.showwarning("Ilość", "Ilość musi być > 0."); return
        if item["stock"] < q:
            messagebox.showerror("Stan", f"Za mały stan. Dostępne: {item['stock']}"); return
        emp_id = self.emp_map[self.emp_combo.get()]
        issue_id = execute("""INSERT INTO issues(issue_date, employee_id, item_id, qty, status)
                              VALUES(?,?,?,?,?)""", (now(), emp_id, item["id"], q, "Wydane"))
        execute("UPDATE items SET stock = stock - ? WHERE id = ?", (q, item["id"]))
        execute("""INSERT INTO movements(move_date, move_type, item_id, employee_id, qty, note)
                   VALUES(?,?,?,?,?,?)""", (now(), "Wydanie", item["id"], emp_id, q, f"Issue #{issue_id}"))
        self.load_open()
        self.item_inv.set("")
        messagebox.showinfo("OK", "Wydano.")

    def return_item(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Wybór", "Zaznacz rekord z listy otwartych wydań."); return
        row = self.tree.item(sel[0])["values"]
        issue_id = row[0]
        qty = row[5]
        # Find item_id and emp_id
        rec = query("SELECT * FROM issues WHERE id = ?", (issue_id,))
        if not rec: return
        rec = rec[0]
        execute("""INSERT INTO returns(return_date, issue_id, qty, state_after)
                   VALUES(?,?,?,?)""", (now(), issue_id, qty, "OK"))
        execute("UPDATE issues SET status='Zwrócone' WHERE id = ?", (issue_id,))
        execute("UPDATE items SET stock = stock + ? WHERE id = ?", (qty, rec["item_id"]))
        execute("""INSERT INTO movements(move_date, move_type, item_id, employee_id, qty, note)
                   VALUES(?,?,?,?,?,?)""", (now(), "Zwrot", rec["item_id"], rec["employee_id"], qty, f"Return for #{issue_id}"))
        self.load_open()
        messagebox.showinfo("OK", "Zwrot zarejestrowany.")

class StockFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        top = ttk.Frame(self); top.pack(fill="x", padx=10, pady=5)
        self.only_short = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="Pokaż tylko braki (Stan < Min)", variable=self.only_short, command=self.load).pack(side="left")
        ttk.Button(top, text="Odśwież", command=self.load).pack(side="left", padx=6)
        ttk.Button(top, text="Eksport CSV", command=self.export_csv).pack(side="left", padx=6)

        self.tree = ttk.Treeview(self, columns=("id","name","type","size","inv","min","stock","loc"),
                                 show="headings", height=18)
        for col, txt, w in [
            ("id","ID",50), ("name","Nazwa",220), ("type","Typ",120),
            ("size","Rozmiar",100), ("inv","Nr ewid.",120),
            ("min","Min",60), ("stock","Stan",60), ("loc","Lokalizacja",140)
        ]:
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.load()

    def load(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        if self.only_short.get():
            rows = query("SELECT * FROM items WHERE stock < min_stock ORDER BY (min_stock - stock) DESC")
        else:
            rows = query("SELECT * FROM items ORDER BY name ASC")
        for r in rows:
            self.tree.insert("", "end", values=(r["id"], r["name"], r["type"], r["size"], r["inv_number"] or "",
                                                r["min_stock"], r["stock"], r["location"] or ""))

    def export_csv(self):
        rows = query("SELECT name,type,size,color,inv_number,min_stock,stock,location FROM items ORDER BY name ASC")
        path = "export_stan_magazynowy.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Nazwa","Typ","Rozmiar","Kolor","Nr ewid.","Stan min.","Stan","Lokalizacja"])
            for r in rows:
                w.writerow([r["name"], r["type"], r["size"], r["color"], r["inv_number"] or "",
                            r["min_stock"], r["stock"], r["location"] or ""])
        messagebox.showinfo("Eksport", f"Zapisano {path} w katalogu aplikacji.")

def main():
    init_db()
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
