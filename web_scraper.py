""" Estudiante: William Aguirre Zapata
	Referencia: https://medium.com/better-programming/how-to-scrape-multiple-pages-of-a-website-using-a-python-web-scraper-4e2c641cff8  
"""
import requests
from requests import get
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from time import sleep
from random import randint

# Contenido traducido al inglés de las URL que estamos solicitando
headers = {"Accept-Language": "en-US,en;q=0.5"}
titles = [] # Título de la película
years = [] # Año en que fue lanzada
time = [] # Cuanto dura la película
imdb_ratings = [] # Calificación de IMDb de la película
metascores = [] # El Metascore de la película
votes = [] # Cuántos votos obtuvo la película
us_gross = [] # Las ganancias brutas de la película en Dolares

""" 
-pages- Función de NumPy: start, stopy step. Es el número que define el espacio entre cada uno. 
Entonces: comience en, deténgase y avance. Ya que la página de las Top 100 imdb se divide
en dos páginas cada página con 50 películas
 """
pages = np.arange(1, 101, 50)

for page in pages:
	# Variable que usamos y que almacena cada una de nuestras nuevas URL y el contenido de ella
	page = requests.get("https://www.imdb.com/search/title/?groups=top_100&start=" + str(page) + "&ref_=adv_nxt", headers=headers)

	# Toma el contenido del texto page y usa el analizador HTML; esto permite que Python lea los componentes de la página en lugar de tratarla como una cadena larga
	soup = BeautifulSoup(page.text, 'html.parser')

	# Almacenamos todos los <div> o contenedores que tengan la clase "lister-item mode-advanced" -> <div class="lister-item mode-advanced">
	movie_div = soup.find_all('div', class_='lister-item mode-advanced')
	
	""" 
	Controlar la frecuencia del Web Scraper es beneficioso para el raspador y para el sitio web que estamos usando.
	Si evitamos golpear el servidor con muchas solicitudes a la vez, entonces es mucho menos probable que nos bloqueen
	nuestra dirección IP, y también evitamos interrumpir la actividad del sitio web que raspamos al permitir que 
	el servidor responda a otros usuarios.
	""" # Hace una pausa entre 2 y 10 segundos aleatoriamente, en el hilo de ejecución
	sleep(randint(2,10))
	
	for container in movie_div:

		# Extraer el título de la película y analizamos que se encuentra en la etiqueta <a> anidada a un <h3>
		# Que a su vez está anidado en un <div>
		name = container.h3.a.text
		titles.append(name)

		# Extraer el año de lanzamiento, se encuentra dentro de un <span> debajo de <a> del título, pero como ese <span>
		# se encuentra de segundo, aquí toca buscar la etiqueta <span> que tenga la clase "lister-item-year" de primerazo
		# <span class="class="lister-item-year ...">
		year = container.h3.find('span', class_='lister-item-year').text
		years.append(year)
		
		# Extraer el tiempo de duración de la película, igual que la anterior se encuentra dentro de
		# <span class="runtime"> pero este campo puede no existir, entonces si es así guardelo como vacío
		runtime = container.p.find('span', class_='runtime') if container.p.find('span', class_='runtime') else ''
		time.append(runtime)

		# Extraer la calificación del IMDb, analizando vemos que se encuentra dentro de a etiqueta <strong>
		# y dicha etiqueta es la única parte donde aparece por ello, solamente la extraemos
		imdb = float(container.strong.text)
		imdb_ratings.append(imdb)

		# Extraer Metascore, se encuentra dentro de un <span> con la clase "metascore" de primerazo
		# <span class="metascore ..."> y si el campo no existe guarde como vacío
		m_score = container.find('span', class_='metascore').text if container.find('span', class_='metascore') else ''
		metascores.append(m_score)

		# Extraer los votos, y de paso las ganancias, ya que se encuentran ambos dentro de un <span name="nv" ...>
		# Guardamos todo lo que encuentre con esos atributos y ya que las ganancias pueden ser vacías
		# Siempre en la posicion 0 o la primera posición almacenará los votos, y en la posicion 1 o 
		# Segunda posición almacena la ganancia en caso de que no exista, lo pone vacío.
		nv = container.find_all('span', attrs={'name': 'nv'})
		vote = nv[0].text
		votes.append(vote)
		grosses = nv[1].text if len(nv) > 1 else ''
		us_gross.append(grosses)


# Almacenamos todos los datos en un DataFrame (Tabla) para tener una sola estructura
movies = pd.DataFrame({
	'movie': titles,
	'year': years,
	'imdb': imdb_ratings,
	'metascore': metascores,
	'votes': votes,
	'us_grossMillions': us_gross,
	'timeMin': time
})

""" Hay que limpiar los datos, por si tiene datos faltantes o inconsistencias en ellos """

# Limpiar los votos, extraemos los puntos de las cantidades, y los reemplazamos por '' espacio vacío y convertimos a Integer
movies['votes'] = movies['votes'].str.replace(',', '').astype(int)

# Limpiamos el año, eliminando los parentesis al inicio y al final y convertimos a integer
movies.loc[:, 'year'] = movies['year'].str[-5:-1].astype(int)

# Limpiamos el tiempo, ya que se guarda con la palabra "Min" al final entonces extraemos solo el texto y convertimos a Int
movies['timeMin'] = movies['timeMin'].astype(str)
movies['timeMin'] = movies['timeMin'].str.extract('(\d+)').astype(int)

# Limpiamos Metascore, convirtiendo el texto
movies['metascore'] = movies['metascore'].str.extract('(\d+)')
movies['metascore'] = pd.to_numeric(movies['metascore'], errors='coerce')

# Limpiando las Ganacias en dolares, hay que quitarle el '$' al inicio y la 'M' al final
movies['us_grossMillions'] = movies['us_grossMillions'].map(lambda x: x.lstrip('$').rstrip('M'))
movies['us_grossMillions'] = pd.to_numeric(movies['us_grossMillions'], errors='coerce')

# Guardamos todos nuestros datos encontrados en un .csv
movies.to_csv('movies.csv')

# Generamos un Archivo JSON con los datos encontrados
json = movies.to_json(orient='records')
with open('movies.json', 'w') as f:
    f.write(json)