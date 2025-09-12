import importlib
import math
import types
import pytest

# Cambiá este nombre si pedís otro filename en la consigna
MODULE_NAME = "bookbyte"


@pytest.fixture(scope="module")
def M():
    mod = importlib.import_module(MODULE_NAME)
    # smoke check de nombres esperados
    for name in ["Producto", "ImponibleIVA", "Puntuable", "LibroFisico", "EBook", "Catalogo"]:
        assert hasattr(mod, name), f"Falta {name} en {MODULE_NAME}.py"
    return mod


def test_ean13_validator_exists(M):
    assert hasattr(M, "Producto")
    assert hasattr(M.Producto, "validar_ean13"), "Falta validar_ean13 en Producto"
    fn = M.Producto.validar_ean13
    assert isinstance(fn, (types.FunctionType, staticmethod)) or callable(fn)

    # Valida un ISBN/EAN-13 conocido
    # '9780132350884' es válido (Clean Code)
    assert M.Producto.validar_ean13("9780132350884") is True
    assert M.Producto.validar_ean13("9780132350880") is False
    assert M.Producto.validar_ean13("no-num") is False
    assert M.Producto.validar_ean13("123") is False


def test_librofisico_multiple_inheritance(M):
    libro = M.LibroFisico(
        titulo="Clean Code",
        autor="Robert C. Martin",
        codigo="LBR00001",
        precio=22000.0,
        isbn="9780132350884",
        peso_gramos=450,
    )
    assert isinstance(libro, M.Producto)
    assert isinstance(libro, M.ImponibleIVA)
    assert isinstance(libro, M.Puntuable)


def test_ebook_inherits_puntuable(M):
    eb = M.EBook(
        titulo="Refactoring",
        autor="Martin Fowler",
        codigo="EBK12345",
        precio=12000.0,
        formato="epub",
        tam_mb=5.6,
    )
    assert isinstance(eb, M.Producto)
    assert isinstance(eb, M.Puntuable)
    # No exige IVA en eBook
    assert not isinstance(eb, M.ImponibleIVA)


def test_validaciones_basicas_producto(M):
    # titulo vacío
    with pytest.raises(Exception):
        M.EBook(
            titulo="",
            autor="Autor",
            codigo="COD12345",
            precio=100.0,
            formato="pdf",
            tam_mb=1.0,
        )
    # autor vacío
    with pytest.raises(Exception):
        M.EBook(
            titulo="Algo",
            autor="",
            codigo="COD12345",
            precio=100.0,
            formato="pdf",
            tam_mb=1.0,
        )
    # codigo muy corto
    with pytest.raises(Exception):
        M.EBook(
            titulo="Algo",
            autor="Autor",
            codigo="C1",
            precio=100.0,
            formato="pdf",
            tam_mb=1.0,
        )
    # precio <= 0
    with pytest.raises(Exception):
        M.EBook(
            titulo="Algo",
            autor="Autor",
            codigo="COD12345",
            precio=0.0,
            formato="pdf",
            tam_mb=1.0,
        )


def test_validaciones_especificas(M):
    # EBook formato inválido
    with pytest.raises(Exception):
        M.EBook(
            titulo="X",
            autor="Y",
            codigo="EBKABCDE",
            precio=100.0,
            formato="txt",
            tam_mb=1.0,
        )
    # EBook tamaño inválido
    with pytest.raises(Exception):
        M.EBook(
            titulo="X",
            autor="Y",
            codigo="EBKABCDE",
            precio=100.0,
            formato="pdf",
            tam_mb=-2.0,
        )
    # LibroFisico: ISBN inválido
    with pytest.raises(Exception):
        M.LibroFisico(
            titulo="X",
            autor="Y",
            codigo="LBRABCDE",
            precio=100.0,
            isbn="9780132350880",  # checksum inválido
            peso_gramos=300,
        )
    # LibroFisico: peso inválido
    with pytest.raises(Exception):
        M.LibroFisico(
            titulo="X",
            autor="Y",
            codigo="LBRABCDE",
            precio=100.0,
            isbn="9780132350884",
            peso_gramos=0,
        )


def test_repr_formato(M, capsys):
    libro = M.LibroFisico(
        titulo="Clean Code",
        autor="Robert C. Martin",
        codigo="LBR00001",
        precio=22000.0,
        isbn="9780132350884",
        peso_gramos=450,
    )
    eb = M.EBook(
        titulo="Refactoring",
        autor="Martin Fowler",
        codigo="EBK12345",
        precio=12000.0,
        formato="epub",
        tam_mb=5.6,
    )

    # Permite __str__ o un método como mostrar(); se testea con print(obj)
    print(libro)
    print(eb)
    out = capsys.readouterr().out.strip().splitlines()

    assert 'Libro Físico "Clean Code" de Robert C. Martin' in out[0]
    assert "ISBN: 9780132350884" in out[0]
    assert "Código: LBR00001" in out[0]
    assert "$22000.0" in out[0]

    assert 'eBook "Refactoring" de Martin Fowler' in out[1]
    assert "Formato: epub" in out[1]
    assert "Código: EBK12345" in out[1]
    assert "$12000.0" in out[1]


def test_puntuable_ratings(M):
    eb = M.EBook(
        titulo="Refactoring",
        autor="Martin Fowler",
        codigo="EBK12345",
        precio=12000.0,
        formato="epub",
        tam_mb=5.6,
    )
    assert eb.rating_promedio() is None
    eb.agregar_rating(4)
    eb.agregar_rating(5)
    eb.agregar_rating(3.5)
    avg = eb.rating_promedio()
    assert avg is not None
    assert math.isclose(avg, (4 + 5 + 3.5) / 3, rel_tol=1e-6)


def test_imponible_iva(M):
    libro = M.LibroFisico(
        titulo="Algo",
        autor="Alguien",
        codigo="LBR00002",
        precio=100.0,
        isbn="9780132350884",
        peso_gramos=200,
    )
    assert hasattr(libro, "precio_con_iva")
    assert math.isclose(libro.precio_con_iva(), 121.0, rel_tol=1e-6)
