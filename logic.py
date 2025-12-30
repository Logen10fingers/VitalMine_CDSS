def check_sirs_risk(temp, heart_rate, resp_rate, wbc_count):
    """
    Calculates Sepsis Risk based on SIRS Criteria.
    Rule: If 2 or more conditions are met, patient is High Risk.
    """
    score = 0

    # Condition 1: Temperature (Fever or Hypothermia)
    if temp > 38.0 or temp < 36.0:
        score += 1

    # Condition 2: Heart Rate (Tachycardia)
    if heart_rate > 90:
        score += 1

    # Condition 3: Respiratory Rate (Tachypnea)
    if resp_rate > 20:
        score += 1

    # Condition 4: WBC Count (Leukocytosis or Leukopenia)
    if wbc_count > 12000 or wbc_count < 4000:
        score += 1

    # Final Decision
    if score >= 2:
        return "High Risk", "red"  # Message and Color
    else:
        return "Stable", "green"


# --- TEST ZONE (This runs only when you play this file) ---
if __name__ == "__main__":
    print("--- Testing VitalMine Brain ---")

    # Test Case 1: Healthy Person (Normal values)
    risk, color = check_sirs_risk(37.0, 72, 16, 8000)
    print(f"Healthy Patient: {risk} (Should be Stable)")

    # Test Case 2: Sick Person (Fever + High HR)
    risk, color = check_sirs_risk(39.5, 110, 18, 9000)
    print(f"Sick Patient:    {risk} (Should be High Risk)")
