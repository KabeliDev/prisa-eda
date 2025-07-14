##  Detección de Productos Duplicados 

### **Criterios utilizados para detectar productos similares**

1. **Marca igual**  
   Los productos deben pertenecer a la misma marca (`Marca`).

2. **Nombre similar**  
   Se utiliza *fuzzy matching* para comparar los nombres (`Nombre SKU`).  
   - El umbral mínimo de similitud se define como parámetro (`similarity_threshold`).
   
   Se excluyen productos que tienen el mismo SKU (código idéntico).

3. **Diferentes subempresas**  
Solo se comparan productos que pertenecen a distintas subempresas.

4. **Coincidencia de números clave**  
Se extraen cantidades relevantes del nombre del producto (por ejemplo: `500 ml`, `20 bolsitas`, `1/2 litro`).  

Los números de ambos productos deben coincidir.

Los números entre paréntesis, como (1), que aparecen al copiar no se consideran.


**5. Eliminación de variantes de sabor**  
Se excluyen pares cuando se detecta una palabra única significativa (normalmente de más de 3 letras) en uno de los nombres que no está presente en el otro.  
La palabra no debe ser una abreviación o una forma plural del otro nombre.  

Esto previene que se agrupen productos que son iguales en base, pero diferentes en sabor, fragancia o variante funcional, como: `limón`, `menta`, `canela`, `caramelo`, `vainilla`, etc.

Por defecto se ignoran palabras de menos de 3 letras, salvo algunas excepciones relevantes como sabores cortos (`ajo`, `té`, `sal`) que están incluidas en una lista especial.

---

###  **Tablas generadas**

####  1. **Tabla de coincidencias confiables** (`confident_df`)
Contiene pares de productos con:
- Similitud mayor o igual al umbral de confianza (`≥ confidence_threshold`, por defecto `93`)

####  2. **Tabla de revisión manual** (`needs_review_df`)
Contiene:
- Pairs con similitud entre el umbral bajo y el de confianza (`low_confidence_threshold ≤ similarity < confidence_threshold`, por defecto `90–92`)

En esta tabla pueden aparecer unos ejemplos que en realidad pertenecen a los productos diferentes
Este enfoque no tiene comprensión semántica profunda.  
Por ejemplo, puede detectar como similares:
- "Café Nescafé Tradición"
- "Café Nescafé Tradición Tarro" → correcto

Pero también podría detectar como similares:
- "Cereal Nestlé Chocapic"
- "Cereal Nestlé Chocapic Yogurt" → incorrecto

Estos errores son inevitables sin un modelo que entienda el contexto del lenguaje. Técnicas simples como bolsa de palabras o listas de tokens frecuentes no cubren todas las combinaciones posibles.


### Resultados

Hay 58 casos seguros donde los nombres diferentes corresponden al mismo producto

#### Principales causas de discrepancia en nombres

- **Orden de palabras distinto:**  
  Ejemplo: `"COLISEO HALLADO"` vs `"HALLADO COLISEO"`

- **Puntuación o símbolos:**  
  Ejemplo: `"1 KG"` vs `"1 KG."`, `"C.K"` vs `"CERO K"`

- **Palabras abreviadas o sinónimos:**  
  Ejemplo: `"PASTA FIDEO"` vs `"FIDEO"`  
  `"SACHET"` vs `"SACHET APROX"`

- **Medidas diferentes expresadas igual:**  
  Ejemplo: `"ML"` vs `"CC"`

- **Errores o codificación especial:**  
  Ejemplo: `"PI¥A"` en lugar de `"PIÑA"`

- **Diferencias menores aceptables en ortografía/plural:**  
  Ejemplo: `"lomito"` vs `"lomitos"`



### Errores

12596 cafe Nescafe - tiene un error en el tamaño (400 en vez de 420)