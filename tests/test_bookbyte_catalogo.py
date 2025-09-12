import importlib
import os
import csv
import builtins
import pytest

MODULE_NAME = "bookbyte"


@pytest.fixture(scope="module")
def M():
    return importlib.import_module(MODULE_NAME)


@pytest.fixture
def catalogo(M):
    return M.Catalogo()


@pytest.fixture
def p_libro(M):
    return M.LibroFisico(
        titulo="Clean Code",
        autor="Robert C. Martin",
        codigo="LBR00001",
        precio=22000.0,
        isbn="9780132350884",
        peso_gramos=450,
    )


@pytest.fixture
def p_ebook(M):
    return M.EBook(
        titulo="Refactoring",
        autor="Martin Fowler",
        codigo="EBK12345",
        precio=12000.0,
        formato="epub",
        tam_mb=5.6,
    )


def test_agregar_y_buscar(M, catalogo, p_libro, p_ebook):
    catalogo.agregar(p_libro)
    catalogo.agregar(p_ebook)

    x = catalogo.buscar("LBR00001")
    y = catalogo.buscar("EBK12345")
    z = catalogo.buscar("NOEXISTE")
    assert x is p_libro
    assert y is p_ebook
    assert z is None


def test_agregar_duplicado_imprime_mensaje(M, catalogo, p_libro, capsys):
    catalogo.agregar(p_libro)
    catalogo.agregar(p_libro)  # duplicado
    out = capsys.readouterr().out
    assert f"Ya existe un producto con el código {p_libro.codigo}" in out


def test_eliminar_y_mensajes(M, catalogo, p_libro, capsys):
    # eliminar inexistente
    catalogo.eliminar("XXXXXX")
    out = capsys.readouterr().out
    assert "No existe producto con el código XXXXXX" in out

    # agregar y eliminar existente
    catalogo.agregar(p_libro)
    catalogo.eliminar("LBR00001")
    # debería ya no estar
    assert catalogo.buscar("LBR00001") is None


def test_listar_por_precio_vacio(M, catalogo, capsys):
    catalogo.listar_por_precio()
    out = capsys.readouterr().out.strip()
    assert out == "No hay productos en el catálogo"


def test_listar_por_precio_orden(M, catalogo, p_libro, p_ebook, capsys):
    # precios: ebook 12000 < libro 22000
    catalogo.agregar(p_libro)
    catalogo.agregar(p_ebook)
    catalogo.listar_por_precio()
    out_lines = capsys.readouterr().out.strip().splitlines()

    # Primera línea debe corresponder al ebook
    assert 'eBook "Refactoring" de Martin Fowler' in out_lines[0]
    assert 'Libro Físico "Clean Code" de Robert C. Martin' in out_lines[1]


def test_filtrar_baratos_header_y_total(M, catalogo, p_libro, p_ebook, capsys):
    catalogo.agregar(p_libro)   # 22000
    catalogo.agregar(p_ebook)   # 12000
    catalogo.filtrar_baratos(15000.0)
    out = capsys.readouterr().out.strip().splitlines()
    assert "=== PRODUCTOS CON PRECIO < 15000.0 ===" == out[0]
    # Debe listar solo el ebook y decir Total: 1
    assert any('eBook "Refactoring" de Martin Fowler' in line for line in out)
    assert out[-1].strip() == "Total: 1"


def test_exportar_csv_crea_archivo_con_campos(M, catalogo, p_libro, p_ebook, tmp_path):
    catalogo.agregar(p_libro)
    catalogo.agregar(p_ebook)
    ruta = tmp_path / "salida.csv"
    catalogo.exportar_csv(str(ruta))
    assert ruta.exists(), "No se creó el archivo CSV"

    with ruta.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Header exacto
    assert rows[0] == ["Tipo", "Titulo", "Autor", "Codigo", "Precio", "Extra"]

    # Dos filas (orden no estrictamente verificado)
    body = rows[1:]
    assert len(body) == 2

    # Contenido esperado por tipo
    joined = "\n".join(",".join(r) for r in body)
    assert "eBook,Refactoring,Martin Fowler,EBK12345,12000.0,Formato=epub;Tamaño=5.6MB" in joined
    assert "Libro Fisico,Clean Code,Robert C. Martin,LBR00001,22000.0,ISBN=9780132350884;Peso=450g" in joined


def test_exportar_csv_cat_vacio_no_crea_archivo(M, tmp_path):
    c = M.Catalogo()
    ruta = tmp_path / "nada.csv"
    c.exportar_csv(str(ruta))
    assert not ruta.exists(), "No debería generarse archivo con catálogo vacío"


def test_exportar_csv_error_escribe_mensaje(M, catalogo, p_libro, tmp_path, monkeypatch, capsys):
    catalogo.agregar(p_libro)
    ruta = tmp_path / "x.csv"

    def fake_open(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(builtins, "open", fake_open)
    catalogo.exportar_csv(str(ruta))
    out = capsys.readouterr().out
    assert "Error al escribir el archivo .csv" in out
