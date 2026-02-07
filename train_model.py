import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from joblib import dump

# Load dataset
df = pd.read_csv("crop_recommendation.csv")

if 'label' not in df.columns:
    raise KeyError("❌ 'label' column not found. Please check crop_recommendation.csv file.")

X = df.drop("label", axis=1)
y = df["label"]

# Encode labels
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# Split and train
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Save model and encoder
dump(model, "model.pkl")
dump(le, "label_encoder.pkl")

print("✅ Model and label encoder trained and saved successfully!")
