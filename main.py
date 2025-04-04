import flet as ft
import sqlite3, asyncio
from datetime import datetime

class InventoryApp: # Clase inventario
    def __init__(self, page: ft.Page): # Contructor
        self.page = page
        self.page.title = "Sistema de Inventario"
        self.page.theme_mode = ft.ThemeMode.SYSTEM
        self.page.padding = 20
        
        # Mostrar la pantalla de inicio
        asyncio.run(self.show_splash_screen())

        # Inicializar base de datos
        self.init_db()

        # Variables de estado
        self.selected_index = None
        self.edit_mode = False
        self.show_history = False

        # Configurar UI
        self.create_ui()

        # Cargar datos iniciales
        self.load_items()

# ----------------------------------- Pantalla de inicio ---------------------
    async def show_splash_screen(self):
        splash_screen = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Bienvenido al Sistema de Inventario", 
                            size=10 if self.page.width < 500 else 20, 
                            weight=ft.FontWeight.BOLD),
                    ft.ProgressRing(),  # Animación de carga
                ],
                alignment=ft.MainAxisAlignment.CENTER, # alinear a la 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            expand=True,
            alignment=ft.alignment.center,
        )
        # Mostrar la pantalla de inicio
        self.page.add(splash_screen)
        self.page.update()

        await asyncio.sleep(3) # Esperar 3 segundos

        # Cargar la interfaz principal
        self.load_main_ui()

    def load_main_ui(self, e=None):
        # Limpiar la pantalla de inicio
        self.page.controls.clear()
        # Cargar la interfaz principal
        self.page.update()
# ------------------------------------------ base de datos --------------------------------------
    def init_db(self): 
        self.conn = sqlite3.connect('inventory.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                quantity INTEGER NOT NULL,
                min_stock INTEGER,
                last_updated TEXT
            )
        ''')
        self.conn.commit()
# ------------------------------------------- Cargar Data ------------------------------      
    def load_items(self, e=None):
        self.items_list.controls.clear()
        
        self.cursor.execute("SELECT * FROM items ORDER BY name")
        items = self.cursor.fetchall()
        
        if not items:
            self.items_list.controls.append(
                ft.ListTile(title=ft.Text("No hay productos registrados"))
            )
        else:
            for idx, item in enumerate(items):
                self.items_list.controls.append(
                    self.create_item_card(item, idx)
                )
        
        self.page.update()
# ---------------------------------------- Crear tarjetas de productos -------------------------------
    def create_item_card(self, item, index):
        id, name, category, quantity, min_stock, last_updated = item
        
        # Determinar color según stock
        quantity_color = ft.Colors.GREEN
        if min_stock and quantity <= min_stock:
            quantity_color = ft.Colors.ORANGE
        if quantity == 0:
            quantity_color = ft.Colors.RED
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.INVENTORY),
                        title=ft.Text(name),
                        subtitle=ft.Text(f"Categoría: {category}" if category else "Sin categoría"),
                    ),
                    
                    ft.Row([
                        ft.Text(f"Stock: {quantity}", color=quantity_color),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    
                    ft.Text(f"Última actualización: {last_updated}"),
                    
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_color=ft.Colors.BLUE,
                            on_click=lambda e, idx=index: self.edit_item(idx) 
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color=ft.Colors.RED,
                            on_click=lambda e, item_id=id: self.delete_item(id)  # Pasamos el id directamente
                        ),
                    ], alignment=ft.MainAxisAlignment.END)
                ]),
                padding=10
            )
        )
# ------------------------------------------ crear UI ---------------------------------
    def create_ui(self):
        # Campo de búsqueda
        self.search_field = ft.TextField(
            hint_text="Buscar productos...",
            on_change=self.search_items,
            expand=True
        )
        # Formulario de producto
        self.name_field = ft.TextField(label="Nombre", autofocus=True, expand=True)
        self.category_field = ft.TextField(label="Categoría", expand=True)
        self.quantity_field = ft.TextField(label="Cantidad", input_filter=ft.NumbersOnlyInputFilter(), expand=True)
        self.min_stock_field = ft.TextField(label="Stock mínimo", input_filter=ft.NumbersOnlyInputFilter(), expand=True)
        
        # Botones del formulario
        self.submit_button = ft.ElevatedButton(
            "Agregar Producto",
            on_click=self.add_item,
            icon=ft.Icons.ADD, 
            height=50,
            expand=True
        )
        self.clear_button = ft.ElevatedButton(
            "Limpiar",
            on_click=self.clear_form, 
            height=50,
            width= 80,
            bgcolor=ft.Colors.RED_800,
            color=ft.Colors.WHITE
            
        )
        
        # Botón para mostrar/ocultar Inventario
        self.toggle_inventario_button = ft.ElevatedButton(
            "Ver Inventario",
            on_click=self.toggle_history_view,
            icon=ft.Icons.HISTORY, 
            height=50
        )
        # Lista de productos
        self.items_list = ft.ListView(expand=True)
        
        # Contenedor del formulario (visible inicialmente)
        self.form_container = ft.Column(
            [
                ft.Text("Registrar Producto", style=ft.TextThemeStyle.TITLE_MEDIUM),
                self.name_field,
                self.category_field,
                self.quantity_field,
                self.min_stock_field,
                ft.Row([self.submit_button, self.clear_button])
            ],
            spacing=10
        )
        
        # Contenedor del Inventario (oculto inicialmente)
        self.history_container = ft.Column(
            [
                ft.Text("Productos en Inventario", style=ft.TextThemeStyle.TITLE_MEDIUM),
                self.items_list,
                ft.ElevatedButton(
                    "Volver al Formulario",
                    on_click=self.toggle_history_view,
                    icon=ft.Icons.ARROW_BACK, 
                    height=50
                )
            ],
            visible=False
        )
        # Diseño principal
        self.page.add(
            ft.Container(  # <-- Este es el contenedor nuevo que debes agregar
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.INVENTORY, size=40),
                                ft.Text("Inventario STB", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                                ft.IconButton(icon=ft.Icons.REFRESH, on_click=self.load_items)
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        )
                    ],
                ),
                padding=ft.padding.only(top=30),  # Margen superior de 30px
            ),
            ft.Container(  # <-- Este es el contenedor nuevo que debes agregar
                content=ft.Column(
                    [
                        ft.Row([self.search_field]),
                        ft.Row([self.toggle_inventario_button], alignment=ft.MainAxisAlignment.END),
                        ft.Divider(),
                        self.form_container,
                        self.history_container
                    ],
                    scroll=True,
                    expand=True,
                    spacing=10
                ),
                padding=ft.padding.only(top=20),  # Margen superior de 30px
                expand=True
            )
        )
# ------------------------------------- Funciones de UI ----------------------------------------    
    def toggle_history_view(self, e):
        self.show_history = not self.show_history
        
        # Actualizar visibilidad de los contenedores
        self.form_container.visible = not self.show_history
        self.history_container.visible = self.show_history
        
        # Cambiar el texto del botón según el estado
        self.toggle_inventario_button.text = "Ver Inventario" if not self.show_history else "Ocultar Inventario"
        
        # Si estamos mostrando el Inventario, cargar los items
        if self.show_history:
            self.load_items()
        
        self.page.update()
# ------------------------------------- Funciones de: agregar, editar, eliminar productos ------------------
    def add_item(self, e):
        name = self.name_field.value.strip()
        category = self.category_field.value.strip()
        quantity = self.quantity_field.value.strip()
        
        if not name or not quantity: 
            self.page.snack_bar = ft.SnackBar(ft.Text("Nombre y cantidad son obligatorios!"))
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        try:
            quantity = int(quantity)
            min_stock = int(self.min_stock_field.value) if self.min_stock_field.value else None
            
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if self.edit_mode and self.selected_index is not None:
                # Actualizar producto existente
                item_id = self.get_item_id(self.selected_index)
                self.cursor.execute(
                    '''
                    UPDATE items SET 
                    name=?, category=?, quantity=?, min_stock=?, last_updated=?
                    WHERE id=?
                    ''',
                    (name, category, quantity, min_stock, now, item_id)
                )
                self.page.snack_bar = ft.SnackBar(ft.Text("Producto actualizado!"))
            else:
                # Mostrar número de productos (solo para visualización)
                self.cursor.execute("SELECT COUNT(*) FROM items")
                count = self.cursor.fetchone()[0] + 1
                print(f"Este será el producto #{count}")
                # Insertar nuevo producto
                self.cursor.execute(
                    '''
                    INSERT INTO items (name, category, quantity, min_stock, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                    ''',
                    (name, category, quantity, min_stock, now)
                )
                self.page.snack_bar = ft.SnackBar(ft.Text("Producto agregado!"))
            
            self.conn.commit()
            self.clear_form()
            self.load_items()
            self.page.snack_bar.open = True
            self.page.update()
            
        except ValueError as ve:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error en los datos: {str(ve)}"))
            self.page.snack_bar.open = True
            self.page.update()

    def edit_item(self, index):
        item_id = self.get_item_id(index)
        self.cursor.execute("SELECT * FROM items WHERE id=?", (item_id,))
        item = self.cursor.fetchone()
        
        if item:
            _, name, category, quantity, min_stock, _ = item
            
            self.name_field.value = name
            self.category_field.value = category if category else ""
            self.quantity_field.value = str(quantity)
            self.min_stock_field.value = str(min_stock) if min_stock else ""
            
            self.selected_index = index
            self.edit_mode = True
            self.submit_button.text = "Actualizar Producto"
            self.submit_button.icon = ft.Icons.SAVE
            
            # Asegurarse de que el formulario esté visible
            if self.show_history:
                self.toggle_history_view(None)
            
            self.page.update()
    
    def delete_item(self, item_id):
        print(f"Intentando eliminar el producto con ID: {item_id}")
        
        self.cursor.execute("DELETE FROM items WHERE id=?", (item_id,)) # Ejecutar el borrado
        self.conn.commit() # Confirmar la transacción
        self.load_items() # Actualizar la lista de productos
        self.page.update() # Actualizar la UI              
# ------------------------------------ Obtener ID del producto -------------------------------
    def get_item_id(self, index):
        """Obtiene el ID del producto basado en su posición en la lista visual"""
        try:
            # Obtenemos todos los IDs ordenados igual que en la vista
            self.cursor.execute("SELECT id FROM items ORDER BY name")
            results = self.cursor.fetchall()
            
            if index < len(results):
                return results[index][0]
            return None
        except Exception as e:
            print(f"Error al obtener ID: {e}")
            return None
# ---------------------------------- Limpiar inputs del formulario -----------------------------   
    def clear_form(self, e=None):
        self.name_field.value = ""
        self.category_field.value = ""
        self.quantity_field.value = ""
        self.min_stock_field.value = ""
        
        self.selected_index = None
        self.edit_mode = False
        self.submit_button.text = "Agregar Producto"
        self.submit_button.icon = ft.Icons.ADD
        
        self.page.update()
# ------------------------------ Buscador -----------------------------------
    def search_items(self, e):
        search_term = self.search_field.value.strip().lower()
        
        if not search_term:
            self.load_items()
            return
        
        self.cursor.execute(
            "SELECT * FROM items WHERE LOWER(name) LIKE ? OR LOWER(category) LIKE ? ORDER BY name",
            (f"%{search_term}%", f"%{search_term}%")
        )
        items = self.cursor.fetchall()
        
        self.items_list.controls.clear()
        
        if not items:
            self.items_list.controls.append(
                ft.ListTile(title=ft.Text("No se encontraron productos"))
            )
        else:
            for idx, item in enumerate(items):
                self.items_list.controls.append(
                    self.create_item_card(item, idx)
                )
        
        self.page.update()
# -------------------------------- app.run ------------------------------------
def main(page: ft.Page):
    app = InventoryApp(page)

ft.app(target=main, assets_dir="assets")  # Sin parámetros de web/view) # Cambia a ft.WEB_BROWSER para abrir en el navegador