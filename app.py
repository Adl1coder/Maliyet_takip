import tkinter as tk
from tkinter import messagebox, filedialog
import sqlite3, random, datetime
from abc import ABC, abstractmethod
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import openpyxl


##########################################
# Model, Factory ve Singleton Tasarımı   #
##########################################

class Part:
    """
    Parça model sınıfı.
    Her parça benzersiz ID, isim, ömür (tahmini kullanım saati), fiyat ve görsel yol bilgisine sahiptir.
    """

    def __init__(self, id: int, name: str, lifespan: int, price: float, image_path: str):
        self.id = id
        self.name = name
        self.lifespan = lifespan
        self.price = price
        self.image_path = image_path

    def __repr__(self):
        return f"Part({self.name}, Ömür: {self.lifespan}, Fiyat: {self.price} TL)"


class PartFactory:
    """
    Factory Pattern ile parça nesnelerinin oluşturulması merkezi hale getirilmiştir.
    """

    @staticmethod
    def create_part(id: int, name: str, lifespan: int, price: float, image_path: str) -> Part:
        return Part(id, name, lifespan, price, image_path)


class PartDatabase:
    """
    Singleton Pattern ile tek veritabanı bağlantısı oluşturulmuştur.
    Parçalar, in-memory SQLite veritabanında saklanır.
    """
    _instance = None

    def __init__(self):
        if PartDatabase._instance is not None:
            raise Exception("Bu sınıf yalnızca tekil olarak kullanılmalıdır!")
        self.conn = sqlite3.connect(":memory:")
        self.create_table()
        self.seed_data()
        PartDatabase._instance = self

    @staticmethod
    def get_instance():
        if PartDatabase._instance is None:
            PartDatabase()
        return PartDatabase._instance

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE parts (
                id INTEGER PRIMARY KEY,
                name TEXT,
                lifespan INTEGER,
                price REAL,
                image_path TEXT
            )
        """)
        self.conn.commit()

    def seed_data(self):
        """
        Parça veritabanına başlangıç verileri eklenir.
        """
        parts = [
            (1, "Body", 5000, 20.0, "body.png"),
            (2, "Sensor", 3000, 15.0, "sensor.png"),
            (3, "Devre Kartı", 4000, 25.0, "circuit.png"),
            (4, "Right Düğmesi", 7000, 5.0, "right_button.png"),
            (5, "Left Düğmesi", 7000, 5.0, "left_button.png"),
            (6, "Scroll", 4000, 7.0, "scroll.png"),
            # Alternatif isimler
            (7, "Body Premium", 8000, 35.0, "body_premium.png"),
            (8, "Sensor Pro", 5000, 30.0, "sensor_pro.png")
        ]
        cursor = self.conn.cursor()
        cursor.executemany("INSERT INTO parts VALUES (?, ?, ?, ?, ?)", parts)
        self.conn.commit()

    def get_parts(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM parts")
        rows = cursor.fetchall()
        parts = [PartFactory.create_part(*row) for row in rows]
        return parts


##########################################
# Activity Database (Simülasyon Verisi)    #
##########################################

class ActivityDatabase:
    """
    ActivityDatabase, son 1 yıla ait en az 100 adet örnek veri içeren faaliyet kayıtlarını tutar.
    Her kayıt; tarih, ürün, toplam maliyet, sabit gider, değişken gider, parça başına maliyet, parça başına ömür bilgilerini içerir.
    Singleton olarak uygulanmıştır.
    """
    _instance = None

    def __init__(self):
        if ActivityDatabase._instance is not None:
            raise Exception("Bu sınıf yalnızca tekil olarak kullanılmalıdır!")
        self.conn = sqlite3.connect(":memory:")
        self.create_table()
        self.seed_data()
        ActivityDatabase._instance = self

    @staticmethod
    def get_instance():
        if ActivityDatabase._instance is None:
            ActivityDatabase()
        return ActivityDatabase._instance

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE activity_log (
                id INTEGER PRIMARY KEY,
                date TEXT,
                product TEXT,
                total_cost REAL,
                fixed_expense REAL,
                variable_expense REAL,
                average_part_cost REAL,
                average_part_lifespan REAL
            )
        """)
        self.conn.commit()

    def seed_data(self):
        """
        1 yıl içinde rastgele 100 kayıt oluşturulur.
        """
        products = ["Mouse", "Keyboard", "Monitor", "Laptop", "Tablet"]
        base_date = datetime.datetime.now() - datetime.timedelta(days=365)
        records = []
        for i in range(100):
            random_days = random.randint(0, 365)
            record_date = base_date + datetime.timedelta(days=random_days)
            product = random.choice(products)
            total_cost = round(random.uniform(50, 300), 2)
            fixed_expense = round(random.uniform(10, 50), 2)
            variable_expense = round(random.uniform(5, 30), 2)
            average_part_cost = round(random.uniform(5, 50), 2)
            average_part_lifespan = random.randint(1000, 10000)
            records.append((i + 1, record_date.strftime("%Y-%m-%d"), product, total_cost,
                            fixed_expense, variable_expense, average_part_cost, average_part_lifespan))
        cursor = self.conn.cursor()
        cursor.executemany("INSERT INTO activity_log VALUES (?, ?, ?, ?, ?, ?, ?, ?)", records)
        self.conn.commit()


##########################################
# Strategy ve Observer Tasarım Desenleri   #
##########################################

class SortStrategy(ABC):
    """
    Parçaların sıralanması için strateji (Strategy Pattern).
    """

    @abstractmethod
    def sort(self, parts: list) -> list:
        pass


class OptimalSortStrategy(SortStrategy):
    """
    Optimal sıralama stratejisi: parçalar ömürleri azalmış, fiyatları artan şekilde sıralanır.
    """

    def sort(self, parts: list) -> list:
        return sorted(parts, key=lambda part: (-part.lifespan, part.price))


class Observable:
    """
    Observer Pattern için temel Observable sınıfı.
    """

    def __init__(self):
        self._observers = []

    def register(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def unregister(self, observer):
        if observer in self._observers:
            self._observers.remove(observer)

    def notify_observers(self, data):
        for observer in self._observers:
            observer.update(data)


class Observer(ABC):
    """
    Observer arayüzü; gözlemcilerin uygulaması gereken metot.
    """

    @abstractmethod
    def update(self, data):
        pass


class CostDisplay(Observer):
    """
    GUI üzerindeki maliyet kutusunu güncellemek için Observer Pattern kullanılır.
    """

    def __init__(self, label: tk.Label):
        self.label = label

    def update(self, total_cost):
        self.label.config(text=f"Toplam Maliyet: {total_cost:.2f} TL")


##########################################
# AssemblyComponent ve RepairProcess     #
##########################################

class AssemblyComponent:
    """
    Tek parça veya birleşik parçaları temsil eder.
    """

    def __init__(self, parts: list):
        self.parts = parts  # List[Part]

    def get_names(self):
        return [part.name for part in self.parts]

    def get_cost(self):
        return sum(part.price for part in self.parts)

    def __repr__(self):
        return f"Assembly({self.get_names()})"


class RepairProcess(Observable):
    """
    Tamir işlemleri (mouse montajı) yönetilir.
    Gerekli parça sırasını kontrol eder ve bileşenleri birleştirir.
    """

    def __init__(self, required_sequence: list):
        super().__init__()
        self.required_sequence = required_sequence  # Örn: ["Body", "Sensor", "Devre Kartı", "Right Düğmesi", "Left Düğmesi", "Scroll"]
        self.total_cost = 0.0

    def merge_components(self, comp1: AssemblyComponent, comp2: AssemblyComponent) -> AssemblyComponent:
        """
        İki bileşenin birleştirilmesi.
        Her parçanın isminin, beklenen isimle başlaması (startswith) kontrol edilir.
        """
        merged_parts = comp1.parts + comp2.parts
        if len(merged_parts) > len(self.required_sequence):
            raise Exception("Gereken parça sayısından fazla parça seçildi!")
        for i, part in enumerate(merged_parts):
            expected = self.required_sequence[i]
            if not part.name.startswith(expected):
                raise Exception("Seçilen parçalar doğru sırada değil!")
        return AssemblyComponent(merged_parts)

    def is_complete(self, component: AssemblyComponent) -> bool:
        return len(component.parts) == len(self.required_sequence)


##########################################
# Ana Menü, Tamir ve Analiz Ekranları     #
##########################################

class MainMenuGUI:
    """
    Ana menüde arka plan görseli ve iki seçenek (Tamir ve Faaliyet Raporları) sunulur.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Tamirci Simülasyonu - Ana Menü")
        self.root.geometry("400x400")

        # Arka plan resmi (background.png) yüklenmeye çalışılır.
        self.main_frame = tk.Frame(root, width=400, height=400)
        self.main_frame.pack(fill="both", expand=True)
        try:
            self.bg_image = tk.PhotoImage(file="background.png")
            self.bg_label = tk.Label(self.main_frame, image=self.bg_image)
            self.bg_label.place(relwidth=1, relheight=1)
        except Exception as e:
            pass  # Resim bulunamazsa boş geçilir.

        # Ana menü butonları
        self.tamir_button = tk.Button(self.main_frame, text="Tamir", command=self.open_repair)
        self.tamir_button.place(relx=0.3, rely=0.4)
        self.rapor_button = tk.Button(self.main_frame, text="Faaliyet Raporları", command=self.open_analysis)
        self.rapor_button.place(relx=0.3, rely=0.5)

    def open_repair(self):
        self.main_frame.destroy()
        RepairGUI(self.root, self)

    def open_analysis(self):
        self.main_frame.destroy()
        AnalysisGUI(self.root, self)


class RepairGUI:
    """
    Tamir ekranı, 640x480 boyutunda olup; parça seçim, bileşen birleştirme/silme ve toplam maliyet güncellemesi gibi işlevler sunar.
    Ayrıca "Ana Menüye Dön" butonu ile ana menüye geri dönüş sağlanır.
    """

    def __init__(self, root: tk.Tk, main_menu: MainMenuGUI):
        self.root = root
        self.main_menu = main_menu
        self.root.geometry("640x480")
        self.root.title("Tamirci Simülasyonu - Tamir")

        self.components = []
        self.component_buttons = {}
        self.selected_components = []

        self.repair_frame = tk.Frame(self.root)
        self.repair_frame.pack(fill="both", expand=True)

        top_frame = tk.Frame(self.repair_frame)
        top_frame.pack(side="top", fill="x", pady=10)
        self.cost_label = tk.Label(top_frame, text="Toplam Maliyet: 0.00 TL")
        self.cost_label.pack(side="right", padx=10)
        self.cost_display = CostDisplay(self.cost_label)
        self.required_sequence = ["Body", "Sensor", "Devre Kartı", "Right Düğmesi", "Left Düğmesi", "Scroll"]
        order_text = "Önerilen Sıra: " + " > ".join(self.required_sequence)
        self.order_label = tk.Label(top_frame, text=order_text)
        self.order_label.pack(side="right", padx=10)
        self.repair_process = RepairProcess(self.required_sequence)
        self.repair_process.register(self.cost_display)

        self.get_part_button = tk.Button(self.repair_frame, text="Parça Al", command=self.open_category_selection)
        self.get_part_button.pack(pady=10)

        self.components_frame = tk.Frame(self.repair_frame)
        self.components_frame.pack(pady=10)

        buttons_frame = tk.Frame(self.repair_frame)
        buttons_frame.pack(pady=10)
        self.merge_button = tk.Button(buttons_frame, text="Birleştir", command=self.merge_selected_components)
        self.merge_button.grid(row=0, column=0, padx=5)
        self.merge_button.config(state="disabled")
        self.delete_button = tk.Button(buttons_frame, text="Sil", command=self.delete_selected_component)
        self.delete_button.grid(row=0, column=1, padx=5)
        self.delete_button.config(state="disabled")

        # Ana Menüye dönüş butonu
        self.back_button = tk.Button(self.repair_frame, text="Ana Menüye Dön", command=self.return_to_main)
        self.back_button.pack(side="bottom", pady=10)

    def update_total_cost(self):
        total = sum(comp.get_cost() for comp in self.components)
        self.repair_process.total_cost = total
        self.repair_process.notify_observers(total)

    def open_category_selection(self):
        self.category_window = tk.Toplevel(self.root)
        self.category_window.title("Kategori Seçimi")
        self.category_window.geometry("480x640")
        categories = ["Body", "Sensor", "Devre Kartı", "Right Düğmesi", "Left Düğmesi", "Scroll"]
        for cat in categories:
            btn = tk.Button(self.category_window, text=cat, command=lambda c=cat: self.open_part_selection(c))
            btn.pack(pady=5)

    def open_part_selection(self, category: str):
        self.category_window.destroy()
        self.part_selection_window = tk.Toplevel(self.root)
        self.part_selection_window.title(f"{category} Parçaları")
        self.part_selection_window.geometry("480x640")
        try:
            db = PartDatabase.get_instance()
            parts = db.get_parts()
        except Exception as e:
            messagebox.showerror("Veritabanı Hatası", str(e))
            return
        filtered_parts = [part for part in parts if part.name.startswith(category)]
        sorter = OptimalSortStrategy()
        sorted_parts = sorter.sort(filtered_parts)
        for part in sorted_parts:
            btn = tk.Button(self.part_selection_window,
                            text=f"{part.name} (Ömür: {part.lifespan}, Fiyat: {part.price} TL)",
                            command=lambda p=part: self.select_part(p))
            btn.pack(pady=5)

    def select_part(self, part: Part):
        component = AssemblyComponent([part])
        self.components.append(component)
        btn = tk.Button(self.components_frame, text=part.name,
                        command=lambda comp=component: self.toggle_component_selection(comp))
        btn.pack(side="left", padx=5)
        self.component_buttons[component] = btn
        self.part_selection_window.destroy()
        self.update_total_cost()

    def toggle_component_selection(self, component: AssemblyComponent):
        btn = self.component_buttons[component]
        if component in self.selected_components:
            self.selected_components.remove(component)
            btn.config(relief="raised")
        else:
            self.selected_components.append(component)
            btn.config(relief="sunken")
        if len(self.selected_components) == 1:
            self.delete_button.config(state="normal")
            self.merge_button.config(state="disabled")
        elif len(self.selected_components) == 2:
            self.merge_button.config(state="normal")
            self.delete_button.config(state="disabled")
        else:
            self.merge_button.config(state="disabled")
            self.delete_button.config(state="disabled")

    def merge_selected_components(self):
        if len(self.selected_components) != 2:
            messagebox.showwarning("Uyarı", "Lütfen iki bileşen seçiniz!")
            return
        comp1, comp2 = self.selected_components
        try:
            new_component = self.repair_process.merge_components(comp1, comp2)
        except Exception as e:
            messagebox.showerror("Birleştirme Hatası", str(e))
            self.clear_selection()
            return
        for comp in self.selected_components:
            btn = self.component_buttons.pop(comp)
            btn.destroy()
            if comp in self.components:
                self.components.remove(comp)
        self.clear_selection()
        self.components.append(new_component)
        new_btn = tk.Button(self.components_frame, text=" + ".join(new_component.get_names()),
                            command=lambda comp=new_component: self.toggle_component_selection(comp))
        new_btn.pack(side="left", padx=5)
        self.component_buttons[new_component] = new_btn
        messagebox.showinfo("Birleştirme", "Parçalar başarıyla birleştirildi!")
        self.update_total_cost()
        if self.repair_process.is_complete(new_component):
            messagebox.showinfo("Tamamlandı",
                                f"Mouse tamamlandı!\nToplam Maliyet: {self.repair_process.total_cost:.2f} TL")

    def delete_selected_component(self):
        if len(self.selected_components) != 1:
            messagebox.showwarning("Uyarı", "Lütfen tek bir bileşen seçiniz!")
            return
        comp = self.selected_components[0]
        btn = self.component_buttons.pop(comp)
        btn.destroy()
        if comp in self.components:
            self.components.remove(comp)
        self.clear_selection()
        self.update_total_cost()

    def clear_selection(self):
        for comp in self.selected_components:
            btn = self.component_buttons.get(comp)
            if btn:
                btn.config(relief="raised")
        self.selected_components = []
        self.merge_button.config(state="disabled")
        self.delete_button.config(state="disabled")

    def return_to_main(self):
        self.repair_frame.destroy()
        MainMenuGUI(self.root)


class AnalysisGUI:
    """
    Analiz ekranı, faaliyet raporlarını günlük, haftalık, aylık, 3 aylık ve yıllık bazda gösterir.
    – Veriler, ActivityDatabase’den çekilir.
    – Rapor metin olarak ve grafiksel olarak sunulabilir.
    – Veriler ayrıca Excel’e aktarılabilir.
    – "Ana Menüye Dön" butonu ile ana menüye geri dönüş sağlanır.
    """

    def __init__(self, root: tk.Tk, main_menu: MainMenuGUI):
        self.root = root
        self.main_menu = main_menu
        self.root.title("Tamirci Simülasyonu - Faaliyet Raporları")
        self.root.geometry("800x600")
        self.activity_db = ActivityDatabase.get_instance()

        self.analysis_frame = tk.Frame(self.root)
        self.analysis_frame.pack(fill="both", expand=True)

        # Zaman aralığı seçimi için dropdown
        self.interval_var = tk.StringVar(value="Aylık")
        intervals = ["Günlük", "Haftalık", "Aylık", "3 Aylık", "Yıllık"]
        interval_label = tk.Label(self.analysis_frame, text="Zaman Aralığı:")
        interval_label.pack(pady=5)
        self.interval_menu = tk.OptionMenu(self.analysis_frame, self.interval_var, *intervals)
        self.interval_menu.pack(pady=5)

        # Butonlar: Raporu Göster, Grafik Göster, Excel'e Aktar, Ana Menüye Dön
        self.show_report_button = tk.Button(self.analysis_frame, text="Raporu Göster", command=self.show_report)
        self.show_report_button.pack(pady=5)
        self.show_chart_button = tk.Button(self.analysis_frame, text="Grafik Göster", command=self.show_chart)
        self.show_chart_button.pack(pady=5)
        self.export_button = tk.Button(self.analysis_frame, text="Excel'e Aktar", command=self.export_to_excel)
        self.export_button.pack(pady=5)
        self.back_button = tk.Button(self.analysis_frame, text="Ana Menüye Dön", command=self.return_to_main)
        self.back_button.pack(pady=5)

        # Raporun gösterileceği metin alanı
        self.report_text = tk.Text(self.analysis_frame, height=15, width=150)
        self.report_text.pack(pady=10)

    def fetch_activity_data(self):
        """
        ActivityDatabase'den veriler pandas DataFrame olarak çekilir.
        """
        query = "SELECT * FROM activity_log"
        df = pd.read_sql_query(query, self.activity_db.conn)
        df['date'] = pd.to_datetime(df['date'])
        return df

    def aggregate_data(self, df, interval):
        """
        Seçilen zaman aralığına göre veriler gruplandırılır.
        Grup metrikleri: toplam ve ortalama maliyet, sabit/gün değişken giderler, parça başına maliyet/ömür,
        en çok kullanılan ürün.
        """
        if interval == "Günlük":
            df['period'] = df['date'].dt.date
        elif interval == "Haftalık":
            df['period'] = df['date'].dt.to_period('W').apply(lambda r: r.start_time.date())
        elif interval == "Aylık":
            df['period'] = df['date'].dt.to_period('M').dt.start_time.dt.date
        elif interval == "3 Aylık":
            df['period'] = df['date'].dt.to_period('Q').dt.start_time.dt.date
        elif interval == "Yıllık":
            df['period'] = df['date'].dt.to_period('Y').dt.start_time.dt.date
        else:
            df['period'] = df['date'].dt.date
        agg_df = df.groupby('period').agg({
            'total_cost': ['sum', 'mean'],
            'fixed_expense': 'sum',
            'variable_expense': 'sum',
            'average_part_cost': 'mean',
            'average_part_lifespan': 'mean',
            'product': lambda x: x.value_counts().idxmax()  # en çok kullanılan ürün
        })
        agg_df.columns = ['toplam_maliyet', 'ortalama_maliyet', 'sabit_gider', 'degisen_gider', 'parca_basi_maliyet',
                          'parca_basi_omur', 'en_cok_kullanilan_urun']
        agg_df = agg_df.reset_index()
        return agg_df

    def show_report(self):
        df = self.fetch_activity_data()
        interval = self.interval_var.get()
        agg_df = self.aggregate_data(df, interval)
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, agg_df.to_string(index=False))

    def show_chart(self):
        df = self.fetch_activity_data()
        interval = self.interval_var.get()
        agg_df = self.aggregate_data(df, interval)
        plt.figure(figsize=(10, 5))
        plt.plot(agg_df['period'], agg_df['toplam_maliyet'], marker='o')
        plt.title(f"Toplam Maliyet - {interval}")
        plt.xlabel("Dönem")
        plt.ylabel("Toplam Maliyet")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def export_to_excel(self):
        df = self.fetch_activity_data()
        interval = self.interval_var.get()
        agg_df = self.aggregate_data(df, interval)
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if file_path:
            agg_df.to_excel(file_path, index=False)
            messagebox.showinfo("Başarılı", f"Rapor {file_path} konumuna kaydedildi.")

    def return_to_main(self):
        self.analysis_frame.destroy()
        MainMenuGUI(self.root)


if __name__ == "__main__":
    root = tk.Tk()
    # Veritabanlarını başlat
    PartDatabase.get_instance()
    ActivityDatabase.get_instance()
    MainMenuGUI(root)
    root.mainloop()
import tkinter as tk
from tkinter import PhotoImage

# Parça bilgileri
parcalar = [
    {"ad": "Üst Kapak", "maliyet": 50, "omur": 5000, "image": "images/top_cover.png"},
    {"ad": "Sol Tık", "maliyet": 30, "omur": 3000, "image": "images/left_click.png"},
    {"ad": "Sağ Tık", "maliyet": 30, "omur": 3000, "image": "images/right_click.png"},
    {"ad": "Tekerlek", "maliyet": 40, "omur": 4000, "image": "images/scroll_wheel.png"},
    {"ad": "Sensör", "maliyet": 150, "omur": 10000, "image": "images/sensor.png"},
    {"ad": "Devre Kartı", "maliyet": 200, "omur": 8000, "image": "images/pcb_board.png"},
    {"ad": "USB Kablo", "maliyet": 60, "omur": 6000, "image": "images/usb_cable.png"}
]

# Ana pencereyi oluştur
root = tk.Tk()
root.title("Parça Seçimi")


# Fotoğrafları ve butonları oluştur
def parca_sec(parca):
    print(f"Seçilen Parça: {parca['ad']} - Maliyet: {parca['maliyet']} - Ömür: {parca['omur']}")


frame = tk.Frame(root)
frame.pack()

for parca in parcalar:
    try:
        image = PhotoImage(file=parca["image"])
        img_label = tk.Label(frame, image=image)
        img_label.image = image  # Referans kaybetmemek için
        img_label.pack()

        btn = tk.Button(frame, text=parca["ad"], command=lambda p=parca: parca_sec(p))
        btn.pack()
    except Exception as e:
        print(f"{parca['ad']} için resim yüklenemedi: {e}")

root.mainloop()
import tkinter as tk
from tkinter import PhotoImage

# Parça bilgileri
parcalar = [
    {"ad": "Üst Kapak", "maliyet": 50, "omur": 5000, "image": "images/top_cover.png"},
    {"ad": "Sol Tık", "maliyet": 30, "omur": 3000, "image": "images/left_click.png"},
    {"ad": "Sağ Tık", "maliyet": 30, "omur": 3000, "image": "images/right_click.png"},
    {"ad": "Tekerlek", "maliyet": 40, "omur": 4000, "image": "images/scroll_wheel.png"},
    {"ad": "Sensör", "maliyet": 150, "omur": 10000, "image": "images/sensor.png"},
    {"ad": "Devre Kartı", "maliyet": 200, "omur": 8000, "image": "images/pcb_board.png"},
    {"ad": "USB Kablo", "maliyet": 60, "omur": 6000, "image": "images/usb_cable.png"}
]

# Ana pencereyi oluştur
root = tk.Tk()
root.title("Parça Seçimi")


# Fotoğrafları ve butonları oluştur
def parca_sec(parca):
    print(f"Seçilen Parça: {parca['ad']} - Maliyet: {parca['maliyet']} - Ömür: {parca['omur']}")


frame = tk.Frame(root)
frame.pack()

for parca in parcalar:
    try:
        image = PhotoImage(file=parca["image"])
        img_label = tk.Label(frame, image=image)
        img_label.image = image  # Referans kaybetmemek için
        img_label.pack()

        btn = tk.Button(frame, text=parca["ad"], command=lambda p=parca: parca_sec(p))
        btn.pack()
    except Exception as e:
        print(f"{parca['ad']} için resim yüklenemedi: {e}")

root.mainloop()
