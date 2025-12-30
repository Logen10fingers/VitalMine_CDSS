import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
import joblib

# 1. GENERATE SYNTHETIC MEDICAL DATA (The Textbooks)
# We create 1000 imaginary patients to teach the AI.
np.random.seed(42)
n_samples = 1000

# Random features: Temp (35-41), HR (50-140), RR (10-40), WBC (2000-20000)
temp = np.random.uniform(35, 41, n_samples)
hr = np.random.randint(50, 140, n_samples)
rr = np.random.randint(10, 40, n_samples)
wbc = np.random.randint(2000, 20000, n_samples)

# 2. DEFINE THE "CORRECT" ANSWERS (The Labeling)
# We basically tell the AI: "If they meet SIRS criteria, label them as 1 (Sick)"
# SIRS Criteria: Temp > 38 or < 36, HR > 90, RR > 20, WBC > 12000 or < 4000.
labels = []
for i in range(n_samples):
    score = 0
    if temp[i] > 38 or temp[i] < 36:
        score += 1
    if hr[i] > 90:
        score += 1
    if rr[i] > 20:
        score += 1
    if wbc[i] > 12000 or wbc[i] < 4000:
        score += 1

    # If score >= 2, they have Sepsis (1). Else Healthy (0).
    labels.append(1 if score >= 2 else 0)

# Create the dataframe
X = pd.DataFrame({"temp": temp, "hr": hr, "rr": rr, "wbc": wbc})
y = np.array(labels)

# 3. TRAIN THE MODEL (The Learning Process)
print("Training AI Model on 1000 mock patients...")
model = LogisticRegression()
model.fit(X, y)

# 4. TEST THE MODEL
test_patient = [[39.5, 110, 22, 13000]]  # A very sick patient
prediction = model.predict(test_patient)
prob = model.predict_proba(test_patient)[0][1]  # Probability of sickness

print(f"Test Prediction for Sick Patient: {prediction[0]} (1=Sick, 0=Healthy)")
print(f"Confidence Level: {prob*100:.2f}%")

# 5. SAVE THE BRAIN (The Jar)
joblib.dump(model, "sirs_model.pkl")
print("Success! Model saved to 'sirs_model.pkl'")
