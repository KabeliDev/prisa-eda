import matplotlib.pyplot as plt


def visualize(
        duplicates,
        different_sku_review_count,
        different_sku_conf_count,
        same_name_same_sku_count,
        similar_name_same_sku_count,
        diffrent_sku_different_prod,
        additional_name=None
):
    labels = [
        "Duplicados de SKU dentro de la misma empresa",
        'Nombres y SKUs exactamente iguales',
        'Nombres similares con SKUs iguales',
        'Nombres distintos (productos iguales) con SKUs distintos\n(subempresas)',
        'Nombres distintos (productos distintos) con SKUs distintos'
    ]

    group1_total = different_sku_review_count + different_sku_conf_count

    x = range(len(labels))

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(0, duplicates, color='gray')
    ax.bar(1, same_name_same_sku_count, color='blue')
    ax.bar(2, similar_name_same_sku_count, color='purple')
    ax.bar(3, different_sku_review_count, label='Con duda, > 88 % de similitud', color='green')
    ax.bar(3, different_sku_conf_count, bottom=different_sku_review_count,
           label='100% iguales', color='orange')
    ax.bar(4, diffrent_sku_different_prod, color='red')

    ax.set_ylabel('Cantidad de coincidencias')
    if additional_name:
        ax.set_title(f'Resumen de coincidencias entre subempresas para {additional_name}')
    else:
        ax.set_title('Resumen de coincidencias entre subempresas')

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=10, ha='center')
    ax.legend()
    ax.text(0, duplicates / 2, str(duplicates), ha='center', va='center')
    ax.text(1, same_name_same_sku_count / 2, str(same_name_same_sku_count), ha='center', va='center')
    ax.text(2, similar_name_same_sku_count / 2, str(similar_name_same_sku_count), ha='center', va='center')
    ax.text(3, group1_total / 2, str(group1_total), ha='center', va='center')
    ax.text(4, diffrent_sku_different_prod / 2, str(diffrent_sku_different_prod), ha='center', va='center')

    plt.tight_layout()
    plt.show()



def graficar_distribucion_productos(dictionary, color):
    """
    Un gráfico que muestra en cuántas subempresas aparecen productos duplicados.
    """
    empresas = sorted(dictionary.keys())
    productos = [dictionary[e] for e in empresas]

    etiquetas = [f"{e} empresa" if e == 1 else f"{e} empresas" for e in empresas]

    plt.figure(figsize=(8, 6))
    bars = plt.bar(etiquetas, productos, color=color, edgecolor='black')

    # Dejar espacio arriba ajustando el límite del eje Y
    max_height = max(productos)
    plt.ylim(0, max_height * 1.15)  # 15% de espacio extra arriba

    # Etiquetas encima de cada barra
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, height + (max_height * 0.01), str(height),
                 ha='center', va='bottom', fontsize=10)

    plt.title("Distribución de productos duplicados según el número de empresas en que aparecen", fontsize=14)
    plt.xlabel("Número de empresas", fontsize=12)
    plt.ylabel("Cantidad de productos únicos", fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()