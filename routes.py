from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime
from ..extensions import db
from ..models import Log, Food

main = Blueprint("main", __name__)

@main.route("/")
def index():
    logs = Log.query.order_by(Log.date.desc()).all()

    # Prepare summary totals per log for index page
    log_dates = []
    for log in logs:
        total_proteins = sum(food.proteins for food in log.foods)
        total_carbs = sum(food.carbs for food in log.foods)
        total_fats = sum(food.fats for food in log.foods)
        total_calories = sum(food.calories for food in log.foods)

        log_dates.append({
            'log_date': log,
            'proteins': total_proteins,
            'carbs': total_carbs,
            'fats': total_fats,
            'calories': total_calories
        })

    return render_template("index.html", log_dates=log_dates)


@main.route("/create_log", methods=["POST"])
def create_log():
    log_date_str = request.form.get("date")
    if log_date_str:
        log_date = datetime.strptime(log_date_str, "%Y-%m-%d").date()
        existing_log = Log.query.filter_by(date=log_date).first()
        if not existing_log:
            new_log = Log(date=log_date)
            db.session.add(new_log)
            db.session.commit()
    return redirect(url_for("main.index"))


@main.route("/delete_log/<int:log_id>", methods=["POST"])
def delete_log(log_id):
    log = Log.query.get_or_404(log_id)
    db.session.delete(log)
    db.session.commit()
    return redirect(url_for("main.index"))


@main.route("/view_log/<int:log_id>", methods=["GET", "POST"])
def view_log(log_id):
    log = Log.query.get_or_404(log_id)
    foods = Food.query.all()

    if request.method == "POST":
        food_id = request.form.get("food-select")
        if food_id:
            food = Food.query.get(food_id)
            if food and food not in log.foods:
                log.foods.append(food)
                db.session.commit()
        return redirect(url_for("main.view_log", log_id=log.id))

    totals = {
        'proteins': sum(food.proteins for food in log.foods),
        'carbs': sum(food.carbs for food in log.foods),
        'fats': sum(food.fats for food in log.foods),
        'calories': sum(food.calories for food in log.foods)
    }

    # Suggestion logic (protein goal fixed at 50g)
    protein_goal = 50
    suggestion = None
    if totals['proteins'] < protein_goal:
        deficit = protein_goal - totals['proteins']
        suggestion = (
            f"You are {deficit}g short of your protein goal. "
            "Try adding foods like boiled eggs (~6g each), milk (~8g per cup), "
            "or chicken breast (~25g per 100g)."
        )

    return render_template("view.html", log=log, foods=foods, totals=totals, suggestion=suggestion)


@main.route("/add_food", methods=["GET", "POST"])
def add_food():
    if request.method == "POST":
        name = request.form.get("food-name")
        proteins = request.form.get("protein")
        carbs = request.form.get("carbohydrates")
        fats = request.form.get("fat")

        if name and proteins and carbs and fats:
            new_food = Food(
                name=name,
                proteins=int(proteins),
                carbs=int(carbs),
                fats=int(fats)
            )
            db.session.add(new_food)
            db.session.commit()
            return redirect(url_for("main.add_food"))

    foods = Food.query.all()
    return render_template("add.html", foods=foods, food=None)


@main.route("/edit_food/<int:food_id>", methods=["GET", "POST"])
def edit_food(food_id):
    food = Food.query.get_or_404(food_id)
    if request.method == "POST":
        name = request.form.get("food-name")
        proteins = request.form.get("protein")
        carbs = request.form.get("carbohydrates")
        fats = request.form.get("fat")

        if name and proteins and carbs and fats:
            food.name = name
            food.proteins = int(proteins)
            food.carbs = int(carbs)
            food.fats = int(fats)
            db.session.commit()
            return redirect(url_for("main.add_food"))

    return render_template("add.html", food=food, foods=Food.query.all())


@main.route("/delete_food/<int:food_id>", methods=["POST", "GET"])
def delete_food(food_id):
    food = Food.query.get_or_404(food_id)
    db.session.delete(food)
    db.session.commit()
    return redirect(url_for("main.add_food"))


@main.route("/remove_food_from_log/<int:log_id>/<int:food_id>")
def remove_food_from_log(log_id, food_id):
    log = Log.query.get_or_404(log_id)
    food = Food.query.get_or_404(food_id)
    if food in log.foods:
        log.foods.remove(food)
        db.session.commit()
    return redirect(url_for("main.view_log", log_id=log.id))
