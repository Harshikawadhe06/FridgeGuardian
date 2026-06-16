import pandas as pd
import random

ingredients = [
    "onion","tomato","potato","carrot","beans","capsicum","cauliflower",
    "cabbage","broccoli","spinach","peas","corn","mushroom","beetroot",
    "apple","banana","mango","orange","grapes","pineapple",
    "milk","curd","butter","cheese","paneer",
    "chicken","egg","fish","mutton",
    "rice","poha","oats","bread",
    "garlic","ginger","chili","pepper"
]

recipe_types = [
    "Curry","Masala","Rice","Soup","Salad",
    "Sandwich","Wrap","Bowl","Pulao",
    "Snack","Breakfast","Dinner"
]

data = []

for i in range(3000):

    selected = random.sample(ingredients, random.randint(4,7))

    recipe_name = f"{selected[0].title()} {random.choice(recipe_types)}"

    instructions = (
        f"Cook using {', '.join(selected)}. "
        f"Prepare well and serve hot."
    )

    data.append([
        recipe_name,
        ",".join(selected),
        instructions
    ])

df = pd.DataFrame(
    data,
    columns=[
        "recipe_name",
        "ingredients",
        "instructions"
    ]
)

df.to_excel(
    "recipe_dataset.xlsx",
    index=False
)

print("recipe_dataset.xlsx created successfully")