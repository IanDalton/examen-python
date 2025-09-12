"""
BookByte - Sistema de tienda de libros físicos y eBooks
Implementación usando POO con herencia múltiple y mixins
"""

import csv
from typing import Optional, List


class Producto:
    """Clase base para todos los productos"""
    
    def __init__(self, titulo: str, autor: str, codigo: str, precio: float):
        # Validaciones
        if not titulo.strip():
            raise ValueError("El título no puede estar vacío")
        if not autor.strip():
            raise ValueError("El autor no puede estar vacío")
        if len(codigo) < 8 or len(codigo) > 12:
            raise ValueError("El código debe tener entre 8 y 12 caracteres")
        if precio <= 0:
            raise ValueError("El precio debe ser mayor a 0")
        
        self.titulo = titulo
        self.autor = autor
        self.codigo = codigo
        self.precio = precio
    
    @staticmethod
    def validar_ean13(codigo: str) -> bool:
        """Valida un EAN-13 (usar en ISBN de LibroFisico)."""
        if len(codigo) != 13 or not codigo.isdigit():
            return False
        suma_impar = sum(int(codigo[i]) for i in range(0, 12, 2))
        suma_par   = sum(int(codigo[i]) for i in range(1, 12, 2))
        checksum   = (10 - ((suma_impar + suma_par * 3) % 10)) % 10
        return checksum == int(codigo[-1])
    
    def __str__(self):
        """Representación base del producto"""
        return f'[Producto] "{self.titulo}" de {self.autor} | Código: {self.codigo} | ${self.precio}'


class ImponibleIVA:
    """Mixin para productos que tienen IVA (21%)"""
    
    def precio_con_iva(self) -> float:
        """Calcula el precio con IVA incluido (21%)"""
        return self.precio * 1.21


class Puntuable:
    """Mixin para productos que pueden recibir calificaciones"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ratings: List[float] = []
    
    def agregar_rating(self, valor: float):
        """Agrega una calificación entre 1 y 5"""
        if not (1 <= valor <= 5):
            raise ValueError("El rating debe estar entre 1 y 5")
        self._ratings.append(valor)
    
    def rating_promedio(self) -> Optional[float]:
        """Retorna el promedio de calificaciones o None si no hay"""
        if not self._ratings:
            return None
        return sum(self._ratings) / len(self._ratings)


class LibroFisico(Producto, ImponibleIVA, Puntuable):
    """Libro físico con herencia múltiple"""
    
    def __init__(self, titulo: str, autor: str, codigo: str, precio: float, 
                 isbn: str, peso_gramos: int):
        super().__init__(titulo, autor, codigo, precio)
        
        # Validaciones específicas
        if not self.validar_ean13(isbn):
            raise ValueError("ISBN inválido (debe ser EAN-13 válido)")
        if peso_gramos <= 0:
            raise ValueError("El peso debe ser mayor a 0")
        
        self.isbn = isbn
        self.peso_gramos = peso_gramos
        self._ratings = []  # Inicializar ratings list
    
    def __str__(self):
        return f'Libro Físico "{self.titulo}" de {self.autor} | ISBN: {self.isbn} | Código: {self.codigo} | ${self.precio}'


class EBook(Producto, Puntuable):
    """eBook con herencia múltiple"""
    
    def __init__(self, titulo: str, autor: str, codigo: str, precio: float, 
                 formato: str, tam_mb: float):
        super().__init__(titulo, autor, codigo, precio)
        
        # Validaciones específicas
        if formato not in {"pdf", "epub", "mobi"}:
            raise ValueError("Formato debe ser pdf, epub o mobi")
        if tam_mb <= 0:
            raise ValueError("El tamaño debe ser mayor a 0")
        
        self.formato = formato
        self.tam_mb = tam_mb
        self._ratings = []  # Inicializar ratings list
    
    def __str__(self):
        return f'eBook "{self.titulo}" de {self.autor} | Formato: {self.formato} | Código: {self.codigo} | ${self.precio}'


class Catalogo:
    """Catálogo de productos usando diccionario para acceso eficiente por código"""
    
    def __init__(self):
        self._productos = {}  # codigo -> Producto
    
    def agregar(self, producto: Producto):
        """Agrega un producto al catálogo"""
        if producto.codigo in self._productos:
            print(f"Ya existe un producto con el código {producto.codigo}.")
            return
        self._productos[producto.codigo] = producto
    
    def eliminar(self, codigo: str):
        """Elimina un producto por código"""
        if codigo not in self._productos:
            print(f"No existe producto con el código {codigo}.")
            return
        del self._productos[codigo]
    
    def buscar(self, codigo: str) -> Optional[Producto]:
        """Busca un producto por código"""
        return self._productos.get(codigo)
    
    def listar_por_precio(self):
        """Lista todos los productos ordenados por precio ascendente"""
        if not self._productos:
            print("No hay productos en el catálogo")
            return
        
        productos_ordenados = sorted(self._productos.values(), key=lambda p: p.precio)
        for producto in productos_ordenados:
            print(producto)
    
    def filtrar_baratos(self, umbral: float):
        """Muestra productos con precio menor al umbral"""
        print(f"=== PRODUCTOS CON PRECIO < {umbral} ===")
        productos_baratos = list(filter(lambda p: p.precio < umbral, self._productos.values()))
        
        for producto in productos_baratos:
            print(producto)
        print(f"Total: {len(productos_baratos)}")
    
    def exportar_csv(self, ruta: str):
        """Exporta el catálogo a un archivo CSV"""
        if not self._productos:
            return  # No genera archivo si está vacío
        
        try:
            with open(ruta, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Header
                writer.writerow(['Tipo', 'Titulo', 'Autor', 'Codigo', 'Precio', 'Extra'])
                
                # Mapear productos a filas CSV
                def producto_a_fila(producto):
                    if isinstance(producto, LibroFisico):
                        tipo = "Libro Fisico"
                        extra = f"ISBN={producto.isbn};Peso={producto.peso_gramos}g"
                    elif isinstance(producto, EBook):
                        tipo = "eBook"
                        extra = f"Formato={producto.formato};Tamaño={producto.tam_mb}MB"
                    else:
                        tipo = "Producto"
                        extra = ""
                    
                    return [tipo, producto.titulo, producto.autor, producto.codigo, producto.precio, extra]
                
                filas = map(producto_a_fila, self._productos.values())
                writer.writerows(filas)
                
        except Exception:
            print("Error al escribir el archivo .csv")
