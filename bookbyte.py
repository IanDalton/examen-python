import csv


class Producto:
    """Clase base para todos los productos (SIN validaciones en el esqueleto)."""

    def __init__(self, titulo: str, autor: str, codigo: str, precio: float):
        # TODO: agregar validaciones (no vacíos, largo de código, precio > 0)
        self.titulo = titulo
        self.autor = autor
        self.codigo = codigo
        self.precio = float(precio)

    @staticmethod
    def validar_ean13(codigo: str) -> bool:
        """Valida un EAN-13 (usar en ISBN de LibroFisico)."""
        # TODO: implementar validador EAN-13 real
        return False

    def __str__(self):
        # TODO: ajustar al formato pedido
        return f'[Producto] "{self.titulo}" de {self.autor} | Código: {self.codigo} | ${self.precio}'


class ImponibleIVA:
    """Mixin para productos con IVA (21%)."""

    def precio_con_iva(self) -> float:
        # TODO: implementar cálculo real (precio * 1.21)
        return getattr(self, "precio", 0.0)


class Puntuable:
    """Mixin para productos que se pueden puntuar."""

    def __init__(self, *args, **kwargs):
        # TODO: respetar MRO y llamar a super()
        self._ratings: list = []

    def agregar_rating(self, valor: float):
        # TODO: validar 1..5 e incorporar al promedio
        self._ratings.append(float(valor))

    def rating_promedio(self) -> float|None:
        # TODO: devolver None si no hay ratings, o promedio si hay
        return None


# NOTA: En este esqueleto NO hay herencia múltiple.
# El/la estudiante debe cambiar estas líneas para heredar de los mixins.
class LibroFisico(Producto):  # TODO: -> (Producto, ImponibleIVA, Puntuable)
    """Libro físico (agregar herencia múltiple y validaciones)."""

    def __init__(self, titulo: str, autor: str, codigo: str, precio: float,
                 isbn: str, peso_gramos: int):
        Producto.__init__(self, titulo, autor, codigo, precio)
        self.isbn = isbn
        self.peso_gramos = int(peso_gramos)

    def __str__(self):
        # TODO: ajustar al formato pedido por el enunciado
        return (f'Libro Físico "{self.titulo}" de {self.autor} | ISBN: {self.isbn} '
                f'| Código: {self.codigo} | ${self.precio}')


class EBook(Producto):  
    """eBook (agregar herencia múltiple y validaciones)."""

    def __init__(self, titulo: str, autor: str, codigo: str, precio: float,
                 formato: str, tam_mb: float):
        Producto.__init__(self, titulo, autor, codigo, precio)
        self.formato = formato
        self.tam_mb = float(tam_mb)

    def __str__(self):
        # TODO: ajustar al formato pedido por el enunciado
        return (f'eBook "{self.titulo}" de {self.autor} | Formato: {self.formato} '
                f'| Código: {self.codigo} | ${self.precio}')


class Catalogo:

    def __init__(self):
        self._productos: dict[str, Producto] = {}

    def agregar(self, producto: Producto):
        # TODO: evitar duplicados (imprimir: "Ya existe un producto con el código {codigo}")
        self._productos[producto.codigo] = producto

    def eliminar(self, codigo: str):
        # TODO: imprimir "No existe producto con el código {codigo}" si no está
        self._productos.pop(codigo, None)

    def buscar(self, codigo: str) -> Producto|None:
        return self._productos.get(codigo)

    def listar_por_precio(self):
        # TODO:
        # - si vacío -> imprimir "No hay productos en el catálogo"
        # - ordenar ascendente por precio
        # - imprimir cada producto
        for p in self._productos.values():
            print(p)

    def filtrar_baratos(self, umbral: float):
        # TODO:
        # - imprimir encabezado EXACTO: "=== PRODUCTOS CON PRECIO < {umbral} ==="
        # - mostrar solo los con precio < umbral 
        # - al final imprimir "Total: N"
        print(f"=== PRODUCTOS CON PRECIO < {umbral} ===")
        for p in self._productos.values():
            if p.precio < umbral:
                print(p)
        print("Total: 0")  # TODO: reemplazar por conteo real

    def exportar_csv(self, ruta: str):
        # TODO:
        # - si vacío: no generar archivo
        # - header EXACTO: ["Tipo","Titulo","Autor","Codigo","Precio","Extra"]
        # - filas:
        #   * eBook -> "eBook", Extra="Formato=...;Tamaño=...MB"
        #   * Libro Fisico -> "Libro Fisico", Extra="ISBN=...;Peso=...g"
        # - manejar errores: imprimir "Error al escribir el archivo .csv"
        try:
            with open(ruta, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Tipo", "Titulo", "Autor", "Codigo", "Precio", "Extra"])
                # Sugerencia: usar map(...) para proyectar objetos a filas
                for p in self._productos.values():
                    if isinstance(p, EBook):
                        tipo = "eBook"
                        extra = f"Formato={p.formato};Tamaño={p.tam_mb}MB"
                    elif isinstance(p, LibroFisico):
                        tipo = "Libro Fisico"
                        extra = f"ISBN={p.isbn};Peso={p.peso_gramos}g"
                    else:
                        tipo = "Producto"
                        extra = ""
                    writer.writerow([tipo, p.titulo, p.autor, p.codigo, p.precio, extra])
        except Exception:
            print("Error al escribir el archivo .csv")
