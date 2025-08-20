#Ejercicio 1: Consigue un listado de clientes han gastado más 110€ en total de entre todos los alquileres que han realizado. Es decir, un cliente puede haber realizado 20 compras de 10€ a lo largo del tiempo, y por lo tanto debe aparecer en el listado. El listado debe contener el nombre y apellido del cliente y la cantidad total gastada por cada uno de ellos.
SELECT 
    cliente.first_name AS nombre, cliente.last_name AS apellido, SUM(pago.amount) AS total_gastado
FROM customer cliente
JOIN payment pago ON cliente.customer_id = pago.customer_id
GROUP BY cliente.customer_id, cliente.first_name, cliente.last_name
HAVING SUM(pago.amount) > 110
ORDER BY total_gastado ASC;

#Ejercicio 2: ¿Podrías sacar un listado de todos los clientes que están dados de alta en el comercio, pero nunca hicieron ninguna compra?
SELECT 
    cliente.first_name AS nombre, cliente.last_name AS apellido
FROM customer cliente LEFT JOIN payment pago 
       ON cliente.customer_id = pago.customer_id
WHERE pago.payment_id IS NULL
ORDER BY cliente.last_name, cliente.first_name;

#Ejercicio 3: Para pagar las comisiones por el empleado 345, necesitamos las ventas del año 2022 realizadas por dicho empleado desglosadas por meses. ¿Podrías obtener dicha información?
SELECT 
    pago.customer_id, DATE_FORMAT(pago.payment_date, '%Y-%m') AS mes, SUM(pago.amount) AS precio_total_ventas,COUNT(pago.payment_id) AS numero_de_ventas
FROM payment pago
WHERE pago.customer_id = 345
  AND YEAR(pago.payment_date) = 2022
GROUP BY DATE_FORMAT(pago.payment_date, '%Y-%m')
ORDER BY mes;

#Ejercicio 4: Obtener un listado en el que se muestren el total acumulado de los pagos realizados por cada cliente hasta la fecha de cada uno de los pagos. Es decir, en cada fila de la consulta debes mostrar cada uno de los pagos y una columna adicional con la cantidad total pagada por el cliente (no mezclar pagos de otros clientes), hasta la fecha del pago actual, incluyendo este último.
#Tiene que ser una subconsulta porque tienes que obtener el listado de los clientes 
SELECT
    pago_principal.customer_id AS cliente_ID,pago_principal.payment_date AS Fecha_pago,pago_principal.amount AS dinero_venta,
    (SELECT SUM(pago_sub.amount)
        FROM payment pago_sub
        WHERE pago_sub.customer_id = pago_principal.customer_id
          AND pago_sub.payment_date <= pago_principal.payment_date
    ) AS total_acumulado_por_fecha
FROM payment pago_principal
ORDER BY pago_principal.customer_id, pago_principal.payment_date;

#Ejercicio 5:Usando una consulta SQL, obtén un listado que contenga el número de películas que existen en el sistema para cada pareja de categoría (identificada por su nombre) e idioma (también por su nombre) existentes.
SELECT 
categoria.name AS categoria, idioma.name AS idioma, COUNT(pelicula.film_id) AS numero_peliculas
FROM film pelicula
INNER JOIN language idioma ON pelicula.language_id=idioma.language_id #Añadimos el idioma de cada pelicula de las tablas language y film
INNER JOIN film_category categoria_pelicula ON pelicula.film_id=categoria_pelicula.film_id #Juntamos por el film ID las tablas film (ya unida a language) y film category 
INNER JOIN category categoria ON categoria_pelicula.category_id=categoria.category_id # Juntamos por ultimo la categoria de pelicyla por el category ID, con las tablas anteriores.
GROUP BY categoria.name, idioma.name
ORDER BY categoria.name, idioma.name;

#Respuesta a la pregunta: Si sumásemos todos los valores de la columna NumFilms, ¿podríamos asegurar que dicha suma es igual al total de películas existentes en el sistema? Justifica tu respuesta.
### No podemoa asegurarlo, porque como estamos utilizando INNER JOIN , si carecemos de algún dato de una pelicula como el idioma o la categoría, no estaría incluida , por lo que el número de películas sería menor. 
### Sin embargo, si sabemos que tenemos todas las filas sin valores nulos, si que podriamos tener el mismo numero porque puede ser que una pelicula pertenezca a dos categorías y como las estamos agrupando, ambas peliculas procederían de la lista de film por lo que sería la misma cantidad.
### Otra cosa seria que dentro de la columna category_id o language_id tuviera más valores, es decir, que fuera 1, 2 para cada film_title, en ese caso si que estaríamos agrupando por separado y el sumatorio sería mayor.
