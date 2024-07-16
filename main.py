from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Float, DATE, func
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField
from wtforms.validators import DataRequired
from data_movies import genre
import requests
import os

# api movie website: https://developer.themoviedb.org/docs/getting-started
DB_ADDRESS = "instance/movies-collection.db"
URL_MOVIE = "https://api.themoviedb.org/3/search/movie?include_adult=false&language=en-US&page=1"
URL_MOVIE_BY_ID = "https://api.themoviedb.org/3/movie/"
headers = {
    "accept": "application/json",
    "Authorization": os.environ.get("MOVIE_AUTHORIZATION")
}
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET")
Bootstrap5(app)


# CREATE DB
class Base(DeclarativeBase):
    pass


app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("MOVIE_DB")
db = SQLAlchemy(model_class=Base)
# initialize the app with the extension
db.init_app(app)
# CREATE TABLE


# Mis clases para la Database
class Movies(db.Model):
    __tablename__ = "movies_tabla"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    fecha_visto: Mapped[str] = mapped_column(DATE, nullable=True)
    genero_id: Mapped[str] = mapped_column(String(250), nullable=True)
    coleccion_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("coleccion_tabla.coleccion_id"))
    collection = relationship("Coleccion", back_populates="movies")
    genres = relationship("PeliculaGenero", back_populates="movies")
    movie_cast = relationship("Casting", back_populates="movie_name")


class Genero(db.Model):
    __tablename__ = "genero"
    genero_id: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True)
    genero: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    movies_genres = relationship("PeliculaGenero", back_populates="genre_name")


class PeliculaGenero(db.Model):
    __tablename__ = "pelicula_genero"
    id: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True)
    movie_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("movies_tabla.id"))
    movies = relationship("Movies", back_populates="genres")
    genero_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("genero.genero_id"))
    genre_name = relationship("Genero", back_populates="movies_genres")


class Actor(db.Model):
    __tablename__ = "actor"
    actor_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    actor_name: Mapped[str] = mapped_column(String(250), nullable=False, unique=True)
    gender: Mapped[int] = mapped_column(Integer, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250))
    movie_cast = relationship("Casting", back_populates="actor_name")


class Casting(db.Model):
    __tablename__ = "casting"
    casting_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    actor_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("actor.actor_id"))
    actor_name = relationship("Actor", back_populates="movie_cast")
    movie_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("movies_tabla.id"))
    movie_name = relationship("Movies", back_populates="movie_cast")
    character: Mapped[str] = mapped_column(String(250))


class Coleccion(db.Model):
    __tablename__ = "coleccion_tabla"
    coleccion_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    coleccion: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250))
    movies = relationship("Movies", back_populates="collection")


# Mis clases para formularios web
class EditForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5", validators=[DataRequired()])
    review = StringField("Your Review")
    fecha_visto = DateField(label="Date You Saw it")
    submit = SubmitField(label="Done")


class AddForm(FlaskForm):
    movie = StringField(label="Movie Title", validators=[DataRequired()])
    submit = SubmitField(label="Add Movie")


# Create table schema in the database. Requires application context.
with app.app_context():
    db.create_all()
#     new_movie = Movies(title="Phone Booth",
#                         year=2002,
#                         description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#                         rating=7.3,
#                         ranking=10,
#                         review="My favourite character was the caller.",
#                         img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg")
#     db.session.add(new_movie)
#     db.session.commit()


@app.route("/")
def home():
    result = db.session.execute(db.select(Movies).order_by(Movies.fecha_visto.desc()))
    all_movies = result.scalars().all()  # convert ScalarResult to Python List
    return render_template("index.html", all_movies=all_movies[:20], active_page='home')


@app.route("/topmovies")
def top_movies():
    result = db.session.execute(db.select(Movies).order_by(Movies.rating.desc()))
    all_movies = result.scalars().all()  # convert ScalarResult to Python List
    for i in range(len(all_movies)):
        all_movies[i].ranking = i + 1
    db.session.commit()
    return render_template("top_movies.html", all_movies=all_movies[:10], active_page='top_movies')


@app.route("/actorsall")
def actor_all():
    data_actors = db.session.execute(db.session.query(Actor, func.count(Casting.actor_id)).outerjoin(Casting, Actor.actor_id == Casting.actor_id).group_by(Actor.actor_id).order_by(func.count(Casting.actor_id).desc()).limit(10))
    # movies_db = sqlite3.connect(DB_ADDRESS)
    # cursor = movies_db.cursor()
    # cursor.execute("SELECT actor.*, COUNT(casting.actor_id) as num_peli FROM actor LEFT JOIN casting on actor.actor_id = casting.actor_id GROUP BY casting.actor_id ORDER BY num_peli DESC LIMIT 10")
    # data = cursor.fetchall()
    # movies_db.close()
    return render_template("actor_all.html", all_actors=data_actors, active_page='actor_all')


@app.route("/collections")
def collections():
    data_collection = db.session.execute(db.session.query(Coleccion, func.count(Movies.coleccion_id)).outerjoin(Movies, Coleccion.coleccion_id == Movies.coleccion_id).group_by(Coleccion.coleccion_id)).fetchall()
    return render_template("collections.html", collections=data_collection, active_page='collections')


@app.route("/details/<int:movie_id>")
def details_movie(movie_id):
    movie_data = db.session.execute(db.select(Movies).where(Movies.id == movie_id)).scalar()
    data_casting = db.session.execute(db.select(Casting.character, Actor.actor_name, Actor.img_url).join(Actor, Casting.actor_id == Actor.actor_id, isouter=True).where(Casting.movie_id == movie_id)).fetchall()
    return render_template("movie_details.html", casting=data_casting, movie=movie_data)



@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = EditForm()
    movie_id = request.args.get("movie_id")
    movie_to_edit = db.get_or_404(Movies, movie_id)
    if form.validate_on_submit():
        movie_to_edit.rating = float(form.rating.data)
        movie_to_edit.fecha_visto = form.fecha_visto.data
        if form.review.data != "":
            movie_to_edit.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", movie_to_edit=movie_to_edit, form=form)


@app.route("/delete")
def delete():
    movie_id = request.args.get("movie_id")
    movie_to_delete = db.session.execute(db.select(Movies).where(Movies.id == movie_id)).scalar()
    # Borrar pelicula de tabla pelicula_genero
    movie_del_genre = db.session.execute(db.select(PeliculaGenero).where(PeliculaGenero.movie_id == movie_id)).scalars()
    for item in movie_del_genre:  # tiene que tener un genero para eliminar no me funciona sin genero
        db.session.delete(item)
        db.session.commit()
    # Borrar pelicula de tabla casting
    movie_del_cast = db.session.execute(db.select(Casting).where(Casting.movie_id == movie_id)).scalars()
    for item in movie_del_cast:  # lo mismo que genero
        db.session.delete(item)
        db.session.commit()
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddForm()
    if form.validate_on_submit():
        parameters = {"query": form.movie.data}
        response = requests.get(URL_MOVIE, headers=headers, params=parameters)
        list_movies = response.json()["results"]
        return render_template("select.html", list_movies=list_movies)
    return render_template("add.html", form=form)


@app.route("/adding_movie")
def adding_movie():
    movie_id = request.args.get("movie_id")
    parameters = {"language": "en-US"}
    response = requests.get(f"{URL_MOVIE_BY_ID}{movie_id}", headers=headers, params=parameters)
    results = response.json()
    pelicula_buscada = db.session.execute(db.select(Movies).where(Movies.title == results["title"])).scalar()
    if pelicula_buscada:
        print("ya esta la pelicula")
        return redirect(url_for("home"))
    # TODO crear una pagina que diga la pelicula ya esta en la base de datos
    else:
        if results["belongs_to_collection"] is None:
            collection_add_id = None
        else:
            collection_buscar = db.session.execute(db.select(Coleccion.coleccion_id).where(Coleccion.coleccion == results["belongs_to_collection"]["name"])).scalar()
            if not collection_buscar:
                nueva_coleccion = Coleccion(coleccion=results["belongs_to_collection"]["name"], img_url=f"https://image.tmdb.org/t/p/w500{results['belongs_to_collection']['poster_path']}")
                db.session.add(nueva_coleccion)
                db.session.commit()
                collection_add_id = nueva_coleccion.coleccion_id
            else:
                collection_add_id = collection_buscar
        generos_lista = [item["name"] for item in results["genres"]]
        generos_lista = ", ".join(generos_lista)
        # crea nueva pelicula para insertar a tabla movies
        new_movie = Movies(title=results["title"], img_url=f"https://image.tmdb.org/t/p/w500{results['poster_path']}",
                           year=results['release_date'].split("-")[0], description=results["overview"][:400],
                           genero_id=generos_lista, coleccion_id=collection_add_id)
        db.session.add(new_movie)
        db.session.commit()
        # insertar datos a tabla pelicula_generos
        genre_ids_list = [item["id"] for item in results["genres"]]
        for ids in genre_ids_list:
            for dicc in genre:
                if dicc["id"] == ids:
                    genre_select = dicc["name"]
                    my_genre_id = db.session.execute(db.select(Genero.genero_id).where(Genero.genero == genre_select)).scalar()
                    movie_genre = PeliculaGenero(movie_id=new_movie.id, genero_id=my_genre_id)
                    db.session.add(movie_genre)
                    db.session.commit()
                    break
        # Insertar cast members a tabla casting y agregar a tabla actors
        response_cast = requests.get(f"{URL_MOVIE_BY_ID}{movie_id}/credits", headers=headers, params=parameters)
        results_cast = response_cast.json()
        for n in range(6):  # numero de actores
            actor_buscar = db.session.execute(db.select(Actor.actor_id).where(Actor.actor_name == results_cast["cast"][n]["original_name"])).scalar()
            if not actor_buscar:
                actor_nuevo = Actor(actor_name=results_cast["cast"][n]["original_name"], gender=results_cast["cast"][n]["gender"], img_url=f"https://image.tmdb.org/t/p/w500{results_cast['cast'][n]['profile_path']}")
                db.session.add(actor_nuevo)
                db.session.commit()
                actor_id_add = actor_nuevo.actor_id
            else:
                actor_id_add = actor_buscar
            nuevo_casting = Casting(actor_id=actor_id_add, movie_id=new_movie.id, character=results_cast["cast"][n]["character"])
            db.session.add(nuevo_casting)
            db.session.commit()

        return redirect(url_for("edit", movie_id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=False)
