"""Genera data/catalog/products.json: unos 200 productos realistas y deterministas (semilla fija).

Uso: uv run --directory ai-service python ../data/scripts/generar_catalogo.py
"""

import json
import random
from pathlib import Path

random.seed(42)

SALIDA = Path(__file__).resolve().parents[1] / "catalog" / "products.json"

MARCAS_ALIMENTO = ["NutriPet", "Campo Vivo", "VetBalance", "Origen Natural", "PetChef"]
MARCAS_GENERAL = ["HappyTail", "PetGear", "Mascotín", "ZooPlus Pro", "Patitas"]

ALIMENTOS = {
    "perro": [
        ("cachorro", "pequeño", "pollo y arroz", "DHA para el desarrollo cerebral y croquetas de bocado pequeño"),
        ("cachorro", "grande", "cordero y arroz", "calcio y fósforo balanceados para un crecimiento articular controlado"),
        ("adulto", "pequeño", "pollo", "alta palatabilidad y croqueta pequeña para mandíbulas chicas"),
        ("adulto", "mediano", "carne y vegetales", "fibra para una digestión saludable"),
        ("adulto", "grande", "pollo y arroz", "glucosamina y condroitina para cuidar las articulaciones"),
        ("senior", "todos", "pescado", "menos calorías y antioxidantes para perros mayores de 7 años"),
        ("adulto", "todos", "salmón sin granos", "fórmula hipoalergénica sin trigo ni maíz para perros sensibles"),
        ("adulto", "todos", "control de peso", "L-carnitina y bajo contenido de grasa para perros con sobrepeso"),
    ],
    "gato": [
        ("cachorro", "todos", "pollo", "proteína alta y DHA para gatitos de 2 a 12 meses"),
        ("adulto", "todos", "salmón", "omega 3 y 6 para un pelaje brillante"),
        ("adulto", "todos", "esterilizado", "control de peso y salud urinaria para gatos castrados"),
        ("adulto", "todos", "control de bolas de pelo", "fibra natural que ayuda a eliminar las bolas de pelo"),
        ("senior", "todos", "pavo", "apoyo renal y menor nivel de fósforo para gatos mayores de 10 años"),
        ("adulto", "todos", "urinario", "pH controlado para prevenir cristales urinarios"),
    ],
}

PRESENTACIONES = {"perro": [(3, 1.0), (7.5, 2.1), (15, 3.6)], "gato": [(1.5, 1.0), (3, 1.8), (7.5, 3.9)]}

SNACKS = {
    "perro": [
        ("Huesitos dentales", "reducen el sarro y la placa; apto para uso diario"),
        ("Tiras de pollo deshidratado", "100% pollo, sin conservantes artificiales"),
        ("Galletas de entrenamiento", "bocados pequeños y bajos en calorías para premiar en el adiestramiento"),
        ("Orejas de cerdo naturales", "masticable de larga duración"),
        ("Snack de batata y pollo", "sin granos, ideal para perros con estómago sensible"),
    ],
    "gato": [
        ("Snack cremoso de atún", "en sobres para dar en la mano; hidrata y premia"),
        ("Bocaditos dentales", "textura crujiente que ayuda a la higiene bucal"),
        ("Hierba gatera deshidratada", "estimula el juego y ayuda a eliminar bolas de pelo"),
        ("Bocados de salmón liofilizado", "un solo ingrediente, alto en proteína"),
    ],
}

JUGUETES = {
    "perro": [
        ("Pelota de goma ultrarresistente", "para perros que muerden fuerte; flota en el agua", 9.99),
        ("Cuerda de algodón para tirar", "ayuda a limpiar los dientes mientras juega", 7.49),
        ("Juguete dispensador de premios", "estimulación mental: el perro debe mover el juguete para sacar el premio", 15.99),
        ("Peluche con sonido", "relleno seguro, no recomendado para perros destructores", 8.99),
        ("Alfombra olfativa", "reduce la ansiedad y hace más lenta la comida", 22.50),
        ("Frisbee de silicona", "blando para no dañar encías", 11.99),
    ],
    "gato": [
        ("Caña con plumas", "estimula el instinto de caza; supervisar el juego", 6.99),
        ("Ratón con catnip", "relleno con hierba gatera orgánica", 4.50),
        ("Túnel plegable", "tres salidas, ideal para gatos de interior", 18.99),
        ("Puntero láser", "nunca apuntar a los ojos; terminar el juego con un juguete físico", 9.49),
        ("Circuito de pelotas", "juego autónomo para gatos que pasan tiempo solos", 16.99),
    ],
    "ave": [("Columpio de madera natural", "para jaulas medianas; madera sin tratar", 7.99)],
    "roedor": [("Rueda silenciosa 20 cm", "superficie cerrada para no lastimar las patas", 14.99)],
}

ACCESORIOS = [
    ("perro", "Collar ajustable reflectante", "visibilidad nocturna, hebilla de liberación rápida", 14.50, "todos"),
    ("perro", "Correa extensible 5 m", "con freno y bloqueo; hasta 25 kg", 24.99, "mediano"),
    ("perro", "Arnés antitirones", "anilla delantera que reduce los tirones durante el paseo", 29.99, "todos"),
    ("perro", "Cama ortopédica", "espuma viscoelástica, ideal para perros senior o con displasia", 59.99, "grande"),
    ("perro", "Bebedero portátil", "botella con cuenco plegable para paseos", 12.99, "todos"),
    ("perro", "Comedero lento", "laberinto que evita que el perro coma demasiado rápido", 13.99, "todos"),
    ("perro", "Transportadora rígida", "aprobada para viajes en avión en cabina hasta 8 kg", 49.99, "pequeño"),
    ("gato", "Rascador torre 120 cm", "postes de sisal y plataformas de descanso", 69.99, "todos"),
    ("gato", "Arenero cubierto con filtro", "reduce olores y salpicaduras de arena", 39.99, "todos"),
    ("gato", "Fuente de agua 2 L", "agua en movimiento que estimula la hidratación", 34.99, "todos"),
    ("gato", "Transportadora con apertura superior", "facilita las visitas al veterinario", 32.99, "todos"),
    ("gato", "Cama tipo iglú", "tela suave y lavable", 27.99, "todos"),
    ("ave", "Jaula mediana con accesorios", "incluye comederos, bebedero y perchas", 79.99, "todos"),
    ("roedor", "Jaula para hámster 2 pisos", "con tubos, casita y bebedero", 54.99, "todos"),
    ("reptil", "Terrario de vidrio 60 L", "ventilación frontal y tapa con cierre", 119.99, "todos"),
    ("reptil", "Lámpara UVB 10.0", "esencial para la síntesis de vitamina D3 en reptiles diurnos", 29.99, "todos"),
    ("pez", "Acuario 40 L con filtro", "kit inicial con iluminación LED y calentador", 89.99, "todos"),
    ("pez", "Filtro externo 600 L/h", "filtración mecánica, biológica y química", 64.99, "todos"),
]

HIGIENE = [
    ("perro", "Shampoo avena y aloe", "para piel sensible, pH balanceado para perros", 11.99),
    ("perro", "Shampoo antipulgas", "con extractos naturales; no reemplaza el antiparasitario", 13.49),
    ("perro", "Cepillo deslanador", "elimina el subpelo muerto en razas de doble manto", 19.99),
    ("perro", "Kit dental con pasta enzimática", "pasta sabor pollo, no usar pasta humana", 12.99),
    ("perro", "Toallitas húmedas", "limpieza de patas y pelaje después del paseo", 6.49),
    ("perro", "Bolsas biodegradables x120", "para recoger excrementos en el paseo", 8.99),
    ("gato", "Arena aglomerante 10 kg", "control de olores, baja en polvo", 15.99),
    ("gato", "Arena de sílice 5 L", "absorbe la humedad y dura hasta 4 semanas", 17.49),
    ("gato", "Cepillo de goma para gatos", "masajea y retira pelo muerto", 7.99),
    ("gato", "Shampoo en seco", "para gatos que no toleran el baño", 10.99),
    ("perro", "Cortauñas con tope de seguridad", "evita cortar la parte viva de la uña", 9.99),
]

SALUD = [
    ("perro", "Pipeta antipulgas y garrapatas 10-20 kg", "protección de 30 días; consultar al veterinario antes de usar", 18.99, "mediano"),
    ("perro", "Pipeta antipulgas y garrapatas 20-40 kg", "protección de 30 días; consultar al veterinario antes de usar", 21.99, "grande"),
    ("perro", "Collar antiparasitario 8 meses", "acción repelente contra pulgas y garrapatas", 34.99, "todos"),
    ("perro", "Suplemento articular", "glucosamina, condroitina y MSM; complemento, no reemplaza tratamiento", 27.99, "todos"),
    ("gato", "Pipeta antipulgas para gatos", "protección de 30 días; nunca usar pipetas de perro en gatos", 15.99, "todos"),
    ("gato", "Pasta de malta", "ayuda a eliminar bolas de pelo", 8.99, "todos"),
    ("perro", "Probiótico digestivo", "apoya la flora intestinal en cambios de dieta", 16.99, "todos"),
    ("gato", "Suplemento urinario", "arándano y D-manosa; complemento, no reemplaza tratamiento", 19.99, "todos"),
]

OTRAS_ESPECIES_ALIMENTO = [
    ("ave", "Mezcla de semillas para canarios", "semillas seleccionadas con vitaminas", 6.99),
    ("ave", "Mezcla para periquitos y cotorras", "con frutas deshidratadas", 8.49),
    ("ave", "Pellets para loros", "nutrición completa, reduce la selección de semillas", 18.99),
    ("roedor", "Alimento para conejos", "alto en fibra con heno de timothy", 9.99),
    ("roedor", "Heno de timothy 1 kg", "fibra esencial para conejos, cobayos y chinchillas", 11.49),
    ("roedor", "Alimento para hámster", "mezcla de semillas, granos y vegetales", 5.99),
    ("roedor", "Pellets para cobayos con vitamina C", "los cobayos no sintetizan vitamina C", 10.99),
    ("pez", "Escamas para peces tropicales", "alimento diario completo", 5.49),
    ("pez", "Alimento para peces de fondo", "pastillas que se hunden", 6.99),
    ("pez", "Acondicionador de agua", "elimina cloro y metales pesados del agua de la canilla", 7.99),
    ("reptil", "Alimento para tortugas acuáticas", "palitos flotantes con calcio", 7.49),
    ("reptil", "Grillos deshidratados", "suplemento proteico para reptiles insectívoros", 9.99),
    ("reptil", "Suplemento de calcio con D3", "espolvorear sobre los insectos", 12.49),
]

PREFIJO_CATEGORIA = {
    "alimento": "AL", "snack": "SN", "juguete": "JU", "accesorio": "AC", "higiene": "HI", "salud": "SA",
}


def producto(contador, categoria, especie, nombre, descripcion, precio, etapa="todos", tamano="todos", marca=None):
    sku = f"{PREFIJO_CATEGORIA[categoria]}-{contador[categoria]:03d}"
    contador[categoria] += 1
    return {
        "sku": sku,
        "name": nombre,
        "brand": marca or random.choice(MARCAS_GENERAL),
        "species": especie,
        "category": categoria,
        "lifeStage": etapa,
        "size": tamano,
        "priceUsd": round(precio, 2),
        "stock": random.choice([0, 3, 8, 12, 25, 40, 60, 90]),
        "description": descripcion,
    }


def main() -> None:
    contador = {k: 101 for k in PREFIJO_CATEGORIA}
    productos = []

    for especie, lineas in ALIMENTOS.items():
        for marca in MARCAS_ALIMENTO:
            for etapa, tamano, sabor, beneficio in lineas:
                kg, factor = random.choice(PRESENTACIONES[especie])
                base = 14 if especie == "perro" else 11
                precio = base * factor * (1.25 if marca == "VetBalance" else 1.0)
                etapa_txt = {"cachorro": "cachorros" if especie == "perro" else "gatitos",
                             "adulto": "adultos", "senior": "senior"}[etapa]
                tam_txt = "" if tamano == "todos" else f" raza {tamano}"
                nombre = f"{marca} {especie.capitalize()} {etapa_txt}{tam_txt} {sabor} {kg} kg"
                desc = (f"Alimento seco para {especie}s {etapa_txt}{tam_txt}, línea {sabor}. "
                        f"Fórmula con {beneficio}. Presentación de {kg} kg.")
                productos.append(producto(contador, "alimento", especie, nombre, desc, precio, etapa, tamano, marca))

    for especie, nombre, desc, precio in OTRAS_ESPECIES_ALIMENTO:
        productos.append(producto(contador, "alimento", especie, nombre, desc.capitalize() + ".", precio))

    for especie, items in SNACKS.items():
        for nombre, desc in items:
            for gramos in (100, 250, 500):
                precio = {100: 3.5, 250: 6.99, 500: 11.99}[gramos] * random.uniform(0.9, 1.3)
                productos.append(producto(contador, "snack", especie, f"{nombre} {gramos} g",
                                          f"{desc.capitalize()}. Paquete de {gramos} g.", precio))

    for especie, items in JUGUETES.items():
        for nombre, desc, precio in items:
            for variante in ("talle S", "talle M", "talle L") if especie == "perro" else ("",):
                n = f"{nombre} {variante}".strip()
                p = precio * {"talle M": 1.15, "talle L": 1.3}.get(variante, 1.0)
                productos.append(producto(contador, "juguete", especie, n, desc.capitalize() + ".", p))

    for especie, nombre, desc, precio, tamano in ACCESORIOS:
        if especie == "perro" and tamano == "todos":
            for talle, t, factor in (("S", "pequeño", 1.0), ("M", "mediano", 1.15), ("L", "grande", 1.3)):
                productos.append(producto(contador, "accesorio", especie, f"{nombre} talle {talle}",
                                          desc.capitalize() + f". Talle {talle} para perros de tamaño {t}.",
                                          precio * factor, tamano=t))
        else:
            productos.append(producto(contador, "accesorio", especie, nombre, desc.capitalize() + ".", precio,
                                      tamano=tamano))

    for especie, nombre, desc, precio in HIGIENE:
        productos.append(producto(contador, "higiene", especie, nombre, desc.capitalize() + ".", precio))

    for especie, nombre, desc, precio, tamano in SALUD:
        productos.append(producto(contador, "salud", especie, nombre, desc.capitalize() + ".", precio,
                                  tamano=tamano))

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(productos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(productos)} productos escritos en {SALIDA}")


if __name__ == "__main__":
    main()
