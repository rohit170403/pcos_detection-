from flask import Flask, render_template, request
import pickle

# Load the trained model
model = pickle.load(open('model.pkl', 'rb'))

# Initialize Flask app
app = Flask(__name__)

# Define the route to display the form and handle form submission
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Collect form data
        period_length = float(request.form['Period Length'])
        cycle_length = float(request.form['Cycle Length'])
        age = int(request.form['Age'])
        overweight = int(request.form['Overweight'])
        weight_loss_gain = int(request.form['loss weight gain / weight loss'])
        irregular_periods = int(request.form['irregular or missed periods'])
        difficulty_conceiving = int(request.form['Difficulty in conceiving'])
        chin_hair_growth = int(request.form['Hair growth on Chin'])
        cheeks_hair_growth = int(request.form['Hair growth on Cheeks'])
        breasts_hair_growth = int(request.form['Hair growth Between breasts'])
        upper_lips_hair_growth = int(request.form['Hair growth  on Upper lips'])
        arms_hair_growth = int(request.form['Hair growth in Arms'])
        inner_thighs_hair_growth = int(request.form['Hair growth on Inner thighs'])
        acne_skin_tags = int(request.form['Acne or skin tags'])
        hair_thinning = int(request.form['Hair thinning or hair loss'])
        dark_patches = int(request.form['Dark patches'])
        always_tired = int(request.form['always tired'])
        mood_swings = int(request.form['more Mood Swings'])
        exercise_per_week = int(request.form['Hours Exercise Per Week'])
        eat_outside_per_week = int(request.form['Eat Outside'])
        canned_food = int(request.form['Canned Food Consumption'])

        # Create a list of features based on the user input
        features = [
            period_length,
            cycle_length,
            age,
            overweight,
            weight_loss_gain,
            irregular_periods,
            difficulty_conceiving,
            chin_hair_growth,
            cheeks_hair_growth,
            breasts_hair_growth,
            upper_lips_hair_growth,
            arms_hair_growth,
            inner_thighs_hair_growth,
            acne_skin_tags,
            hair_thinning,
            dark_patches,
            always_tired,
            mood_swings,
            exercise_per_week,
            eat_outside_per_week,
            canned_food
        ]

        # Make a prediction using the model
        prediction = model.predict([features])
        
        # Map the prediction to a meaningful result
        if prediction[0] == 1:
            result = "PCOS Detected"
        else:
            result = "No PCOS Detected"

        # Render the template with the result
        return render_template('index.html', result=result)

    # Render the form if the request method is GET
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
