# Módulo 3. Pruebas de clase

Demostraciones hechas en directo en clase. No tienen tests.

## 1. Qué pasa al importar un módulo (`saludo.py`)

`saludo.py` tiene un `print` suelto, una función y, al final, el bloque `if __name__ == "__main__":`.

### Importarlo dos veces desde el REPL

```
cd modulo_03_funciones_modulos/pruebas_clase
python
>>> import saludo
Cargando saludo
__name__ vale: saludo
>>> import saludo
>>> saludo.saludar("Ada")
'Hola, Ada'
>>> import sys
>>> "saludo" in sys.modules
True
```

El mensaje sale **una sola vez**. La primera vez que se importa un módulo, Python ejecuta el fichero entero y lo guarda en `sys.modules`. En el segundo `import` lo encuentra ahí y no lo vuelve a ejecutar.

Si se cambia el fichero, un nuevo `import` en el mismo REPL no recoge los cambios. Hay que salir con `exit()` y volver a entrar.

### Ejecutarlo de las dos formas

| Cómo | Salida | `__name__` |
| --- | --- | --- |
| Como script: `python saludo.py` | `Cargando saludo`, `__name__ vale: __main__`, `Hola, mundo` | `"__main__"`, así que el `if` se cumple |
| Con import: `python -c "import saludo"` | `Cargando saludo`, `__name__ vale: saludo` | `"saludo"`, así que el `if` no se cumple |

El código suelto se ejecuta siempre. El que está dentro de `if __name__ == "__main__":` solo se ejecuta cuando el fichero se lanza directamente. Gracias a esto, los tests pueden importar las funciones sin que arranque el programa.

## 2. Dónde busca Python los módulos (`ejemplos/tienda/`)

Comandos desde la raíz del repositorio:

| Desde dónde | Comando | Resultado |
| --- | --- | --- |
| La carpeta del script | `cd modulo_03_funciones_modulos/ejemplos` y `python 04_usar_paquete.py` | ✅ Funciona |
| La raíz del repositorio | `python modulo_03_funciones_modulos/ejemplos/04_usar_paquete.py` | ✅ Funciona |
| La raíz del repositorio | `python -c "import tienda"` | ❌ `ModuleNotFoundError: No module named 'tienda'` |

- `sys.path` es la lista de carpetas donde Python busca los módulos al hacer `import`.
- Al ejecutar un script, Python pone como primera entrada de `sys.path` **la carpeta donde está el script**, no la carpeta desde la que se lanza. En los dos primeros casos es `ejemplos/`, que contiene `tienda/`. Por eso el segundo también funciona.
- Con `python -c` no hay script, así que la primera entrada es `''`, es decir, la carpeta actual. Desde la raíz no hay ninguna carpeta `tienda`, y Python lanza `ModuleNotFoundError`.
