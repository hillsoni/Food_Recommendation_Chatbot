from flask import Flask, request, render_template, jsonify
import pandas as pd
import re

# Load the dataset from CSV
file_path = 'Indian_Food_DF.csv'
df = pd.read_csv(file_path)

# Function to extract numeric value from 'nutri_energy' column
def extract_nutri_energy(value):
    if isinstance(value, str):
        match = re.search(r'([\d,]+)\s*kJ', value)
        if match:
            return float(match.group(1).replace(',', ''))
        match = re.search(r'([\d,]+)\s*kcal', value)
        if match:
            return float(match.group(1).replace(',', '')) * 4.184
    return None

df['nutri_energy'] = df['nutri_energy'].apply(extract_nutri_energy)

def calculate_bmr(weight, height, age, gender):
    if gender.lower() == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    elif gender.lower() == 'female':
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    else:
        raise ValueError("Gender must be 'male' or 'female'")
    return bmr

def calculate_calories(bmr, activity_level):
    activity_factors = {
        'sedentary': 1.2,
        'lightly active': 1.375,
        'moderately active': 1.55,
        'very active': 1.725,
        'extra active': 1.9
    }
    if activity_level.lower() in activity_factors:
        return bmr * activity_factors[activity_level.lower()]
    else:
        raise ValueError("Activity level must be one of: sedentary, lightly active, moderately active, very active, extra active")

def get_top_5_closest_meals(calorie_needs_kj, df):
    valid_meals = df[df['nutri_energy'] <= calorie_needs_kj].copy()
    if not valid_meals.empty:
        valid_meals['difference'] = (valid_meals['nutri_energy'] - calorie_needs_kj).abs()
        top_5_meals = valid_meals.sort_values(by='difference').head(5)
        top_5_meals.fillna('N/A', inplace=True)
        return top_5_meals.to_dict(orient='records')
    else:
        return []

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    weight = float(request.form['weight'])
    height = float(request.form['height'])
    age = int(request.form['age'])
    gender = request.form['gender']
    activity_level = request.form['activity_level']

    bmr = calculate_bmr(weight, height, age, gender)
    calorie_needs_kj = calculate_calories(bmr, activity_level)
    
    top_meals = get_top_5_closest_meals(calorie_needs_kj, df)
    
    return jsonify({
        'bmr': bmr,
        'calorie_needs_kj': calorie_needs_kj,
        'meals': top_meals
    })

if __name__ == '__main__':
    app.run(debug=True)
