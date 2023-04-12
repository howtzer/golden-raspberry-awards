import os
import json
from copy import deepcopy
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, url_for, redirect, current_app as app
from sqlalchemy.sql import func, text
from sqlalchemy import ForeignKey
from utils import RESPONSE_GET, atualiza_segundo_valor, atualiza_response


##########
########## DATABASE CONFIG
##########

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__) #isso é do app.py
app.config['SQLALCHEMY_DATABASE_URI'] =\
        'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#########
####### DATABASE
#########

class Database():

    def __init__(self, id=None, year=None, title=None, studios=None, winner=None, producers=None):
        self.id = id
        self.year = year
        self.title = title
        self.studios = studios
        self.winner = winner
        self.producers = producers


    def get(self, movie_id=None):
        where = ""
        if movie_id:
            where = "where movie.id = '"+movie_id+"'" 

        sql = """select movie.*,
            producer.*
        from movie
        join movie_producer on (movie.id = movie_producer.movie_id)
        join producer on (producer.id = movie_producer.producer_id)
        """ + where
        result = self.select(sql)
        return result


    def create_movie(self):
        movie = Movie(year = self.year,
                      title = self.title,
                      studios = self.studios,
                      winner = self.winner)
        db.session.add(movie)
        db.session.commit()
        movie_id_created = movie.id
        #producers
        self.update_producers(producers=self.producers, movie_id=movie_id_created)
        return movie_id_created


    def create_producer(self, producer_name):
        producer = Producer(producer=producer_name)
        db.session.add(producer)
        db.session.commit()
        return producer
    

    def create_movie_producer(self, movie_id_created, producer_id_created):
        movie_producer = Movie_producer(
                movie_id = movie_id_created,
                producer_id = producer_id_created
            )
        db.session.add(movie_producer)
        db.session.commit()


    def update(self):
        movie = Movie.query.filter_by(id=self.id).first()

        movie.year=self.year
        movie.title = self.title
        movie.studios = self.studios
        movie.winner = self.winner

        db.session.add(movie)
        db.session.commit()
        #deleta vinculo com produtores
        self.delete_producers_movie(movie_id=movie.id)

        #atualiza vinculos com produtores
        self.update_producers(producers=self.producers, movie_id=movie.id)


    def update_producers(self, producers, movie_id):
        producers = self.producers.replace(", and", ", ")
        producers = producers.replace(" and ", ", ")
        producers = producers.split(", ")

        for i in producers:
            producer = Producer.query.filter_by(producer=i).first()
            if not producer:
                producer = self.create_producer(producer_name=i)
            
            #cria vinculo entre produtor e filme
            self.create_movie_producer(
                movie_id_created=movie_id,
                producer_id_created=producer.id
            )

    def list(self):
        movies = self.get()
        return movies


    def delete_movie(self):
        movie = Movie.query.get_or_404(self.id)
        db.session.delete(movie)
        db.session.commit()


    def delete_producers_movie(self, movie_id):
        producers = Movie_producer.query.filter_by(movie_id=movie_id).all()
        for i in producers:
            db.session.delete(i)
            db.session.commit()


    def select(self, sql_query):
        sql = text(sql_query)
        with db.engine.connect() as conn:
            results = conn.execute(sql)
        return results.all()

#########
######### MODELS
#########

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer)
    title = db.Column(db.String(255))
    studios = db.Column(db.String(255))
    #producers = db.Column(db.String(255))
    winner = db.Column(db.String(255))

    def __repr__(self):
        return f'<Movie {self.title}>'


class Producer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    producer = db.Column(db.String(255))


class Movie_producer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(ForeignKey(Movie.id))
    producer_id = db.Column(ForeignKey(Producer.id))


#########
######### URLS
#########

@app.route("/get", methods=["GET"])
def get():

    """ TENTATIVA DE REALIZAR A OPERAÇÃO VIA QUERY """

    #query_maior_intervalo = """select producer as prod,
    #                            min(year) as previousWin,
    #                            max(year) as followingWin,
    #                            max(year) - min(year) as interval,
    #                            from movie
    #                            join movie_producer on (movie.id = movie_producer.movie_id)
    #                            join producer on (producer.id = movie_producer.producer_id)
    #                            where movie.winner = 'yes'
    #                            group by producer
    #                            having count(movie.id) > 1
    #                            order by interval desc
    #                            limit 2"""

    ##carregando menor intervalo
    #query_menor_intervalo = """
    #    select producer as prod,
    #        min(year) min_year,
    #        max(year) max_year,
    #        max(year) - min(year) as interval
    #    from movie
    #    join movie_producer on (movie.id = movie_producer.movie_id)
    #    join producer on (producer.id = movie_producer.producer_id)
    #    where movie.winner = 'yes'
    #    group by producer
    #    having count(producer.id) > 1
    #    order by interval
    #    limit 2"""
    #database = Database()
    #result_menor_intervalo = database.select(query_menor_intervalo)
    #menor_intervalo = []
    #for i in result_menor_intervalo:
    #    menor_intervalo.append({"producer": i[0],
    #                            "interval": i[3],
    #                            "previousWin": i[1],
    #                            "followingWin": i[2]
    #                            })
    #response = {"min":menor_intervalo, "max":maior_intervalo}

    
    sql = """select producer.id as prod_id
                from movie
                join movie_producer on (movie.id = movie_producer.movie_id)
                join producer on (producer.id = movie_producer.producer_id)
             where movie.winner = 'yes'
                group by producer.id
                having count(movie.id) > 1
                order by producer"""
    
    database = Database()
    produtores_aptos = database.select(sql)
    intervalos = get_produtores_premiados(produtores_aptos)

    minIntervals = [9999, 9999]
    maxIntervals = [0, 0]
    response = RESPONSE_GET
    for i in intervalos:
        if all(i["intervalos"]["maxInterval"] > interval for interval in maxIntervals):
            if i["intervalos"]["maxInterval"] > maxIntervals[0]:
                atualiza_segundo_valor(response, operacao="max")
                maxIntervals[0] = i["intervalos"]["maxInterval"]
                atualiza_response(response, indice=0, intervalo=i, operacao="max")

        if all(i["intervalos"]["minInterval"] < interval for interval in minIntervals):
            if i["intervalos"]["minInterval"] < minIntervals[0]:
                atualiza_segundo_valor(response, operacao="min")
                minIntervals[0] = i["intervalos"]["minInterval"]
                atualiza_response(response, indice=0, intervalo=i, operacao="min")
    return response



@app.route("/post", methods=["POST"])
def post():
    try:
        data = json.loads(request.data)
        database = Database(year = data["year"],
                            title = data["title"],
                            studios = data["studios"],
                            producers = data["producers"],
                            winner = data["winner"])
        id = database.create_movie()
        response = app.response_class(
            status=200,
            mimetype='application/json',
            response=json.dumps({"id":id})
        )
    except Exception as e:
        app.logger.warning(e)
        response = app.response_class(
            status=500,
            mimetype='application/json'
        )
    return response


@app.route("/delete", methods=["DELETE"])
def delete():
    try:
        data = json.loads(request.data)
        database = Database(id=data["id"])
        database.delete_movie()
        response = app.response_class(
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        app.logger.warning(e)
        response = app.response_class(
            status=500,
            mimetype='application/json'
        )
    return response


@app.route("/put", methods=["PUT"])
def put():
    try:
        data = json.loads(request.data)
        database = Database(id = data["id"],
                            year = data["year"],
                            title = data["title"],
                            studios = data["studios"],
                            producers = data["producers"],
                            winner = data["winner"])
        database.update()

        response = app.response_class(
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        app.logger.warning(e)
        response = app.response_class(
            status=500,
            mimetype='application/json'
        )
    return response


#########
######### METODOS DE APOIO
#########


def get_produtores_premiados(produtores_aptos):
    intervalos = []
    database = Database()
    for produtor in produtores_aptos:
        prod_id = produtor[0]
        sql_movies = """
        select movie.year, producer.producer
            from movie
            join movie_producer on (movie.id = movie_producer.movie_id)
            join producer on (producer.id = movie_producer.producer_id)
            where movie.winner = 'yes' and producer.id = '"""+str(prod_id)+"'"
        produtor_filmes_premiados = database.select(sql_movies)
        premiacoes = []
        produtor = produtor_filmes_premiados[0][1]
        for movie in produtor_filmes_premiados:
            ano_premiacao = movie[0]
            premiacoes.append(ano_premiacao)
        #calcula intervalos aqui
        premiacoes.sort()
        minIntervalRange = []
        maxIntervalRange = []
        interval = 0
        maxInterval = 0
        minInterval = 9999
        for i in range(0, len(premiacoes)):
            if i+1 < len(premiacoes):
                interval = premiacoes[i+1] - premiacoes[i]
                if interval > maxInterval:
                    maxInterval = interval
                    maxIntervalRange = {"menorAno":premiacoes[i], "maiorAno": premiacoes[i+1]}
                if interval < minInterval:
                    minInterval = interval
                    minIntervalRange = {"menorAno":premiacoes[i], "maiorAno": premiacoes[i+1]}
                    
        intervalos.append({"produtor":produtor,
            "intervalos": {"maxInterval":maxInterval,
                        "minInterval":minInterval,
                        "minIntervalRange": minIntervalRange,
                        "maxIntervalRange":maxIntervalRange}
            })
    return intervalos



#########
######### CSV
#########


def load_movies_csv():
    movie_list = open("movielist.csv", "r").readlines()
    keys = deepcopy(movie_list[0].replace("\n", "").split(";"))
    movie_list.pop(0)
    movie_list_dict = []
    for linha in movie_list:
        linha = linha.replace("\n", "")
        lista_campos = linha.split(";")
        linha_dict = {}
        for key, value in zip(keys, lista_campos):
            linha_dict[key] = value
        movie_list_dict.append(linha_dict)
    return movie_list_dict


def import_movies_to_table():
    db.drop_all()
    db.create_all()
    app.logger.info("Carregando arquivo csv para database e convertendo para Dict")
    movies_dict = load_movies_csv()
    for movie in movies_dict:
        database = Database(year=movie["year"],
                            title=movie["title"],
                            studios=movie["studios"],
                            producers=movie["producers"],
                            winner=movie["winner"])
        database.create_movie()
    app.logger.info("Carga realizada com sucesso")

#########
######### RUN APP SETTINGS
#########

def run_app():
    with app.app_context():
        import_movies_to_table()
    app.run(host="0.0.0.0", port=8000, debug=True)
    app.logger.info("Iniciando app")


if __name__ == "__main__":
    run_app()