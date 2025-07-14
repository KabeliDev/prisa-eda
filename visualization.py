import matplotlib.pyplot as plt



def visualize(different_sku_review_count, different_sku_conf_count, same_name_same_sku_count, similar_name_same_sku_count, additional_name=None):
    labels = [
        'Productos distintos con distinto SKU\n(subempresas)',
        'Nombre y SKU exactamente iguales',
        'Nombre similar y SKU igual'
    ]

    # Heights for the bars
    group1_total = different_sku_review_count + different_sku_conf_count
    heights = [group1_total, same_name_same_sku_count, similar_name_same_sku_count]

    # Positions for bars
    x = range(len(labels))

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot the first bar with two parts (stacked)
    ax.bar(0, different_sku_review_count, label='100% iguales', color='green')
    ax.bar(0, different_sku_conf_count, bottom=different_sku_review_count, label='Con duda', color='orange')

    # Plot the other bars
    ax.bar(1, same_name_same_sku_count, color='blue')
    ax.bar(2, similar_name_same_sku_count, color='purple')

    # Add labels and title
    ax.set_ylabel('Cantidad de coincidencias')
    if additional_name:
        ax.set_title(f'Resumen de coincidencias entre subempresas para {additional_name}')
    else:
        ax.set_title('Resumen de coincidencias entre subempresas')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=10, ha='center')
    ax.legend()

    # Optional: Add value labels above bars
    for i, count in enumerate([group1_total, same_name_same_sku_count, similar_name_same_sku_count]):
        ax.text(i, count + 1, str(count), ha='center', va='bottom')

    plt.tight_layout()
    plt.show()
