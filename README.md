##  Detección de Productos Duplicados 

### **Criterios utilizados para detectar productos similares**

1. **Marca igual**  
   Los productos deben pertenecer a la misma marca (`Marca`).

2. **Nombre similar**  
   Se utiliza *fuzzy matching* para comparar los nombres (`Nombre SKU`).  
   - El umbral mínimo de similitud se define como parámetro (`similarity_threshold`).
   
   Se excluyen productos que tienen el mismo SKU (código idéntico).

3. **Diferentes subempresas **  
Solo se comparan productos que pertenecen a distintas subempresas.

**4. Coincidencia de números clave**  
Se extraen cantidades relevantes del nombre del producto (por ejemplo: `500 ml`, `20 bolsitas`, `1/2 litro`).  
- Si ambos productos contienen la misma cantidad de números, todos deben coincidir exactamente.  
- Si la cantidad de números es distinta, al menos uno debe coincidir.  
Esto ayuda a evitar comparar productos de diferentes tamaños o presentaciones (por ejemplo: `180 ml` vs `270 ml`, o `20 bolsitas` vs `50 bolsitas`).

**5. Eliminación de variantes de sabor**  
Se excluyen pares cuando se detecta una palabra única significativa (más de 3 letras) en uno de los nombres que no está presente en el otro.  
La palabra no debe ser una abreviación del otro nombre.  
Esto previene que se agrupen productos iguales pero con diferentes sabores o fragancias, como: `limón`, `menta`, `canela`, `caramelo`, `vainilla`, etc.

---

###  **Tablas generadas**

####  1. **Tabla de coincidencias confiables** (`confident_df`)
Contiene pares de productos con:
- Similitud mayor o igual al umbral de confianza (`≥ confidence_threshold`, por defecto `93`)

####  2. **Tabla de revisión manual** (`needs_review_df`)
Contiene:
- Pairs con similitud entre el umbral bajo y el de confianza (`low_confidence_threshold ≤ similarity < confidence_threshold`, por defecto `90–92`)
