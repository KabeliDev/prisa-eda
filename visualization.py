import matplotlib.pyplot as plt


def visualize(
        different_sku_review_count,
        different_sku_conf_count,
        same_name_same_sku_count,
        similar_name_same_sku_count,
        diffrent_sku_different_prod,
        additional_name=None
):
    labels = [
        'Nombres distintos (productos iguales) con SKUs distintos\n(subempresas)',
        'Nombres y SKUs exactamente iguales',
        'Nombres similares con SKUs iguales',
        'Nombres distintos (productos distintos) con SKUs distintos'
    ]

    group1_total = different_sku_review_count + different_sku_conf_count
    heights = [group1_total, same_name_same_sku_count, similar_name_same_sku_count, diffrent_sku_different_prod]

    x = range(len(labels))

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.bar(0, same_name_same_sku_count, color='blue')
    ax.bar(1, similar_name_same_sku_count, color='purple')
    ax.bar(2, different_sku_review_count, label='100% iguales', color='green')
    ax.bar(2, different_sku_conf_count, bottom=different_sku_review_count, label='Con duda, > 88 % de similitud',
           color='orange')
    ax.bar(3, diffrent_sku_different_prod, color='red', label='Productos totalmente distintos')

    ax.set_ylabel('Cantidad de coincidencias')
    if additional_name:
        ax.set_title(f'Resumen de coincidencias entre subempresas para {additional_name}')
    else:
        ax.set_title('Resumen de coincidencias entre subempresas')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=10, ha='center')
    ax.legend()

    for i, count in enumerate(heights):
        ax.text(i, count + 1, str(count), ha='center', va='bottom')

    plt.tight_layout()
    plt.show()
