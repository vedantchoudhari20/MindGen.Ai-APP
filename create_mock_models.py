import os
import joblib
import pandas as pd
import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.preprocessing import LabelEncoder

def create_mocks():
    print("Creating mock directories and models...")
    os.makedirs("backend/models", exist_ok=True)

    # 1. Depression Models
    depression_classes = [
        "False", 
        "Major Depressive Disorder", 
        "Persistent Depressive Disorder", 
        "Atypical Depression", 
        "Psychotic Depression", 
        "Seasonal Affective Disorder"
    ]
    dep_le = LabelEncoder()
    dep_le.fit(depression_classes)

    # We fit the dummy classifier to output a class index (e.g., Seasonal Affective Disorder)
    X_dummy = pd.DataFrame([[30, 7.0]], columns=["Age", "SleepDuration"])
    y_dummy = [dep_le.transform(["Seasonal Affective Disorder"])[0]]
    
    dep_model = DummyClassifier(strategy="constant", constant=y_dummy[0])
    dep_model.fit(X_dummy, y_dummy)

    joblib.dump(dep_model, "backend/models/DepressionModel.joblib")
    joblib.dump(dep_le, "backend/models/DepressionEncoder.joblib")
    print("Depression mock models saved.")

    # 2. Bipolar Disorder Models
    bipolar_classes = ["False", "BD-I", "BD-II", "Cyclothymia"]
    bp_le = LabelEncoder()
    bp_le.fit(bipolar_classes)

    y_bp_dummy = [bp_le.transform(["BD-I"])[0]]
    bp_model = DummyClassifier(strategy="constant", constant=y_bp_dummy[0])
    bp_model.fit(X_dummy, y_bp_dummy)

    joblib.dump(bp_model, "backend/models/BDModel.joblib")
    joblib.dump(bp_le, "backend/models/BD_label_encoder.joblib")
    print("Bipolar disorder mock models saved.")

    # 3. Anxiety Models
    anxiety_classes = [
        "False", 
        "Generalized Anxiety Disorder", 
        "Panic Disorder", 
        "Social Anxiety Disorder", 
        "Agoraphobia", 
        "Specific Phobia"
    ]
    anx_le = LabelEncoder()
    anx_le.fit(anxiety_classes)

    # Anxiety uses metadata mapping
    y_anx_dummy = [anx_le.transform(["Social Anxiety Disorder"])[0]]
    anx_model = DummyClassifier(strategy="constant", constant=y_anx_dummy[0])
    anx_model.fit(X_dummy, y_anx_dummy)

    anxiety_columns = [
        "Age", "SleepDuration", "Genotype_5HTTLPR", "Genotype_COMT", "Genotype_MAOA",
        "Cortisol", "Alpha_Amylase", "HRV (Heart Rate Variability)", "GABA", "IL6",
        "TNF_alpha", "Tryptophan", "Vitamin_B6", "Omega3_Index", "HPA_Axis_Dysregulation",
        "Sympathetic_Activation_Score", "GABAergic_Function_Score", "AnxietyScore_GAD7"
    ]

    anxiety_metadata = {
        'columns': anxiety_columns,
        'category_mappings': {
            'AnxietyDiagnosis': {
                anx_le.transform([c])[0]: c for c in anxiety_classes
            }
        }
    }

    joblib.dump(anx_model, "backend/models/AnxietyModel.joblib")
    joblib.dump(anxiety_metadata, "backend/models/AnxietyMetadata.joblib")
    print("Anxiety mock models saved.")
    print("All mock models created successfully!")

if __name__ == "__main__":
    create_mocks()
