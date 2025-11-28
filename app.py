import io
import base64
from flask import Flask, make_response, render_template, request, send_file, url_for, redirect, session, flash , send_from_directory
import pandas as pd
import joblib
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
import os
from werkzeug.security import generate_password_hash, check_password_hash
import json
import uuid
from datetime import datetime
import bcrypt

app = Flask(__name__)
app.secret_key = 'testkey'  # Replace with a strong secret key

# Local JSON file storage
USERS_FILE = 'users.json'
RESULTS_FILE = 'results.json'

def read_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return []

def write_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

# Load models and metadata at startup
try:
    depression_model = joblib.load("backend/models/DepressionModel.joblib")
    depression_encoder = joblib.load("backend/models/DepressionEncoder.joblib")
    BD_model = joblib.load("backend/models/BDModel.joblib")
    BD_label_encoder = joblib.load("backend/models/BD_label_encoder.joblib")
    anxiety_model = joblib.load("backend/models/AnxietyModel.joblib")
    anxiety_metadata = joblib.load("backend/models/AnxietyMetadata.joblib")
    anxiety_columns = anxiety_metadata['columns']
    anxiety_mappings = anxiety_metadata['category_mappings']
except Exception as e:
    print(f"Error loading models: {str(e)}")


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        security_question = request.form['security_question']
        security_answer = request.form['security_answer'].lower()
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
            
        users = read_json(USERS_FILE)
        existing_user = next((user for user in users if user['username'] == username), None)
        if existing_user:
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
            
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        users.append({
            'id': str(uuid.uuid4()),
            'name': name,
            'username': username,
            'password': hashed_password.decode('utf-8'),
            'security_question': security_question,
            'security_answer': security_answer,
            'created_at': datetime.utcnow().isoformat()
        })
        
        write_json(USERS_FILE, users)
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Invalid login attempt.', 'danger')
            return redirect(url_for('login'))

        users = read_json(USERS_FILE)
        user = next((user for user in users if user['username'] == username), None)
        if user:
            if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                session['username'] = username
                session['user_id'] = user['id']
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password.', 'danger')
        else:
            flash('Invalid username or password.', 'danger')
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/forgotpass', methods=['GET', 'POST'])
def forgotpass():
    if request.method == 'POST':
        username = request.form['username']
        security_answer = request.form['security_answer'].lower()
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('forgotpass'))
            
        users = read_json(USERS_FILE)
        user = next((user for user in users if user['username'] == username), None)
        if user:
            if security_answer == user['security_answer']:
                hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                user['password'] = hashed_password.decode('utf-8')
                
                # Update user in the list
                for i, u in enumerate(users):
                    if u['username'] == username:
                        users[i] = user
                        break
                
                write_json(USERS_FILE, users)
                flash('Password updated successfully! Please log in.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Security answer incorrect.', 'danger')
        else:
            flash('Username not found.', 'danger')
        return redirect(url_for('forgotpass'))
    return render_template('forgotpass.html')

@app.route('/previous_reports')
def previous_reports():
    if 'user_id' not in session:
        flash('Please log in to view reports.', 'warning')
        return redirect(url_for('login'))
    
    # Get all reports for current user
    results = read_json(RESULTS_FILE)
    reports = [r for r in results if r['username'] == session['username']]
    
    # Convert timestamp strings to datetime objects for sorting
    for report in reports:
        report['timestamp'] = datetime.fromisoformat(report['timestamp'])
    
    reports.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return render_template('previous_reports.html', reports=reports)

@app.route('/view_report/<report_id>')
def view_report(report_id):
    if 'user_id' not in session:
        flash('Please log in to view reports.', 'warning')
        return redirect(url_for('login'))
    
    try:
        results = read_json(RESULTS_FILE)
        report = next((r for r in results if r['id'] == report_id and r['username'] == session['username']), None)
        
        if not report:
            flash('Report not found or you dont have access', 'danger')
            return redirect(url_for('previous_reports'))
        
        results_data = {
            "Depression": report['Depression'],
            "BipolarDisorder": report['BipolarDisorder'],
            "Anxiety": report['Anxiety'],
            "Report": report['Report'],
            "timestamp": datetime.fromisoformat(report['timestamp'])
        }
        
        return render_template('output.html', results=results_data)
    
    except Exception as e:
        flash(f'Error loading report: {str(e)}', 'danger')
        return redirect(url_for('previous_reports'))
    

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # Collect all inputs from the form
            shared_inputs = {
                "Age": int(request.form['age']),
                "SleepDuration": float(request.form['sleep_duration']),
                "Cortisol": float(request.form['cortisol']),
                "Vitamin_D": float(request.form['vitamin_d'])
            }

            # Depression inputs
            depression_input = {
                **shared_inputs,
                "Genotype_5HTTLPR": request.form['genotype_5httlpr'],
                "Genotype_COMT": request.form['genotype_comt'],
                "Genotype_MAOA": request.form['genotype_maoa'],
                "BDNF_Level": float(request.form['bdnf_level']),
                "CRP": float(request.form['crp']),
                "Tryptophan": float(request.form['tryptophan']),
                "Omega3_Index": float(request.form['omega3_index']),
                "MTHFR_Genotype": request.form['mthfr_genotype'],
                "Neuroinflammation_Score": float(request.form['neuroinflammation_score']),
                "Monoamine_Oxidase_Level": float(request.form['mao_level']),
                "Serotonin_Level": float(request.form['serotonin_level']),
                "HPA_Axis_Dysregulation": float(request.form['hpa_dysregulation']),
                "DepressionScore_PHQ9": int(request.form['phq9_score'])
            }

            # Bipolar inputs
            bipolar_input = {
                "Age": shared_inputs["Age"],
                "Sex": request.form['sex'],
                "Family_History": request.form['family_history'],
                "ANK3_rs10994336": request.form['ank3_rs10994336'],
                "CACNA1C_rs1006737": request.form['cacna1c_rs1006737'],
                "ODZ4_rs12576775": request.form['odz4_rs12576775'],
                "Glutamate_Level": request.form['glutamate_level'],
                "Tryptophan_Metabolites": request.form['tryptophan_metabolites'],
                "Cortisol_Level": request.form['cortisol_level'],
                "Circadian_Gene_Disruption": request.form['circadian_gene_disruption'],
                "Mitochondrial_Dysfunction": request.form['mitochondrial_dysfunction'],
                "Neuroinflammation": request.form['neuroinflammation'],
                "Omega3_Intake": request.form['omega3_intake'],
                "Folate_Level": request.form['folate_level'],
                "VitaminD_Level": request.form['vitamind_level'],
                "Average_Sleep_Hours": float(shared_inputs["SleepDuration"]),
                "Physical_Activity_Level": request.form['physical_activity']
            }

            anxiety_input = {
                "Age": shared_inputs["Age"],
                "SleepDuration": shared_inputs["SleepDuration"],
                "Genotype_5HTTLPR": request.form['genotype_5httlpr'],
                "Genotype_COMT": request.form['genotype_comt'],
                "Genotype_MAOA": request.form['genotype_maoa'],
                "Cortisol": shared_inputs["Cortisol"],
                "Alpha_Amylase": float(request.form['alpha_amylase']),
                "HRV (Heart Rate Variability)": float(request.form['HRV']),
                "GABA": float(request.form['gaba']),
                "IL6": float(request.form['IL6']), 
                "TNF_alpha": float(request.form['TNF_alpha']),
                "Tryptophan": float(request.form['tryptophan']),
                "Vitamin_B6": float(request.form['Vitamin_B6']), 
                "Omega3_Index": float(request.form['omega3_index']),
                "HPA_Axis_Dysregulation": float(request.form['hpa_dysregulation']),
                "Sympathetic_Activation_Score": float(request.form['Sympathetic_Activation_Score']), 
                "GABAergic_Function_Score": float(request.form['gaba_function']),
                "AnxietyScore_GAD7": int(request.form['anxiety_score'])
            }

            # Create DataFrame with correct columns
            anxiety_df = pd.DataFrame([anxiety_input], columns=anxiety_columns)

            # Make prediction
            anxiety_pred_code = anxiety_model.predict(anxiety_df)[0]
            anxiety_pred = anxiety_mappings['AnxietyDiagnosis'][anxiety_pred_code]

            # Make predictions
            depression_df = pd.DataFrame([depression_input])
            depression_pred = depression_encoder.inverse_transform(
                depression_model.predict(depression_df)
            )[0]

            bipolar_df = pd.DataFrame([bipolar_input])
            bipolar_pred = BD_label_encoder.inverse_transform(
                BD_model.predict(bipolar_df)
            )[0]

            # Generate report
            report = recommended_path(depression_pred, bipolar_pred, anxiety_pred)
            
            # Store results in session
            session['results'] = {
                "Depression": depression_pred,
                "BipolarDisorder": bipolar_pred,
                "Anxiety": anxiety_pred,
                "Report": report
            }

            # Save results to JSON file
            results = read_json(RESULTS_FILE)
            results.append({
                'id': str(uuid.uuid4()),
                'username': session['username'],
                'timestamp': datetime.utcnow().isoformat(),
                'Depression': depression_pred,
                'BipolarDisorder': bipolar_pred,
                'Anxiety': anxiety_pred,
                'Report': report
            })
            write_json(RESULTS_FILE, results)
                        
            return redirect(url_for('results'))
            
        except Exception as e:
            flash(f"Error processing your data: {str(e)}", "error")
            import traceback
            traceback.print_exc()
            return redirect(url_for('analyze'))
    
    return render_template('analysis.html')

@app.route('/results')
def results():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    results_data = read_json(RESULTS_FILE)
    user_results = [r for r in results_data if r['username'] == session['username']]
    user_results.sort(key=lambda x: x['timestamp'], reverse=True)
    
    if not user_results:
        flash('No available data!', 'info')
        return render_template('output.html', results=None)
    
    # Display the latest report
    latest_result = user_results[0]
    results_data = {
        "Depression": latest_result['Depression'],
        "BipolarDisorder": latest_result['BipolarDisorder'],
        "Anxiety": latest_result['Anxiety'],
        "Report": latest_result['Report'],
        "timestamp": datetime.fromisoformat(latest_result['timestamp'])
    }

    return render_template('output.html', results=results_data)

@app.route('/download_report')
def download_report():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Create PDF report
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Add title
    story.append(Paragraph("MindGen AI - Personalized Mental Health Report", styles['Title']))
    story.append(Spacer(1, 12))
    
    # Add results
    results = session['results']
    story.append(Paragraph("Diagnosis Results:", styles['Heading2']))
    story.append(Paragraph(f"Depression: {results['Depression']}", styles['Normal']))
    story.append(Paragraph(f"Bipolar Disorder: {results['BipolarDisorder']}", styles['Normal']))
    story.append(Paragraph(f"Anxiety: {results['Anxiety']}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Add treatment plan
    story.append(Paragraph("Personalized Treatment Plan:", styles['Heading2']))
    for line in results['Report'].split('\n'):
        if line.startswith('='):
            story.append(Paragraph(line, styles['Heading1']))
        elif line.startswith('-'):
            story.append(Paragraph(line, styles['Bullet']))
        else:
            story.append(Paragraph(line, styles['Normal']))
        story.append(Spacer(1, 6))
    
    doc.build(story)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name="MindGen_Report.pdf",
        mimetype='application/pdf'
    )

def recommended_path(depression_pred, bipolar_pred, anxiety_pred):
    """
    Generates a comprehensive, formatted treatment plan report based on predicted mental health conditions.
    """
    # Generate the treatment plan dictionary (using the previous function's logic)
    treatment_plan = generate_treatment_plan_dict(depression_pred, bipolar_pred, anxiety_pred)

    # Create the formatted report
    report = []

    # Header
    report.append("="*80)
    report.append("MINDGEN AI® PERSONALIZED TREATMENT PLAN REPORT")
    report.append("="*80)
    report.append("\n")

    # Overview section
    report.append("OVERVIEW")
    report.append("-"*80)
    report.append(treatment_plan["Overview"])
    report.append("\n")

    # Conditions Detected
    report.append("CONDITIONS IDENTIFIED")
    report.append("-"*80)
    if depression_pred != "False":
        report.append(f"- {depression_pred}")
    if bipolar_pred != "False":
        report.append(f"- {bipolar_pred}")
    if anxiety_pred != "False":
        report.append(f"- {anxiety_pred}")
    if depression_pred == "False" and bipolar_pred == "False" and anxiety_pred == "False":
        report.append("- No significant mental health conditions detected")
    report.append("\n")

    # Genetic Considerations
    if treatment_plan["Genetic_Considerations"]:
        report.append("GENETIC CONSIDERATIONS")
        report.append("-"*80)
        for item in treatment_plan["Genetic_Considerations"]:
            report.append(f"• {item}")
        report.append("\n")

    # Diagnostic Confirmation
    if treatment_plan["Diagnostic_Confirmation"]:
        report.append("DIAGNOSTIC CONFIRMATION STEPS")
        report.append("-"*80)
        for item in treatment_plan["Diagnostic_Confirmation"]:
            report.append(f"• {item}")
        report.append("\n")

    # Personalized Interventions
    if treatment_plan["Personalized_Interventions"]:
        report.append("PERSONALIZED INTERVENTIONS")
        report.append("-"*80)
        for i, item in enumerate(treatment_plan["Personalized_Interventions"], 1):
            report.append(f"{i}. {item}")
        report.append("\n")

    # Pharmacological Approach
    if treatment_plan["Pharmacological_Approach"]:
        report.append("PHARMACOLOGICAL APPROACH")
        report.append("-"*80)
        for i, item in enumerate(treatment_plan["Pharmacological_Approach"], 1):
            report.append(f"{i}. {item}")
        report.append("\n")

    # Nutrigenomic Recommendations
    if treatment_plan["Nutrigenomic_Recommendations"]:
        report.append("NUTRIGENOMIC RECOMMENDATIONS")
        report.append("-"*80)
        for item in treatment_plan["Nutrigenomic_Recommendations"]:
            report.append(f"• {item}")
        report.append("\n")

    # Lifestyle Modifications
    if treatment_plan["Lifestyle_Modifications"]:
        report.append("LIFESTYLE MODIFICATIONS")
        report.append("-"*80)
        for item in treatment_plan["Lifestyle_Modifications"]:
            report.append(f"• {item}")
        report.append("\n")

    # Therapeutic Approaches
    if treatment_plan["Therapeutic_Approaches"]:
        report.append("THERAPEUTIC APPROACHES")
        report.append("-"*80)
        for i, item in enumerate(treatment_plan["Therapeutic_Approaches"], 1):
            report.append(f"{i}. {item}")
        report.append("\n")

    # Monitoring and Follow-up
    if treatment_plan["Monitoring_and_Followup"]:
        report.append("MONITORING AND FOLLOW-UP PLAN")
        report.append("-"*80)
        for item in treatment_plan["Monitoring_and_Followup"]:
            report.append(f"• {item}")
        report.append("\n")

    # Special Considerations
    if treatment_plan["Special_Considerations"]:
        report.append("SPECIAL CONSIDERATIONS")
        report.append("-"*80)
        for item in treatment_plan["Special_Considerations"]:
            report.append(f"⚠️ {item}")
        report.append("\n")

    # Footer
    report.append("="*80)
    report.append("END OF REPORT")
    report.append("="*80)

    # Join all lines with newlines and return
    return "\n".join(report)


def generate_treatment_plan_dict(depression_pred, bipolar_pred, anxiety_pred):
    """
    Provides a customized treatment plan based on predicted mental health conditions.

    Parameters:
    - depression_pred: One of the depression types or 'False'
    - bipolar_pred: One of the bipolar disorder types or 'False'
    - anxiety_pred: One of the anxiety types or 'False'

    Returns:
    - A detailed treatment plan dictionary with sections for each condition and combined recommendations
    """

    # Initialize the treatment plan
    treatment_plan = {
        "Overview": "",
        "Genetic_Considerations": [],
        "Diagnostic_Confirmation": [],
        "Personalized_Interventions": [],
        "Pharmacological_Approach": [],
        "Nutrigenomic_Recommendations": [],
        "Lifestyle_Modifications": [],
        "Therapeutic_Approaches": [],
        "Monitoring_and_Followup": [],
        "Special_Considerations": []
    }

    # Helper function to add unique items to a section
    def add_unique(section, items):
        for item in items:
            if item not in treatment_plan[section]:
                treatment_plan[section].append(item)

    # Overview section
    conditions = []
    if depression_pred != "False":
        conditions.append(depression_pred)
    if bipolar_pred != "False":
        conditions.append(bipolar_pred)
    if anxiety_pred != "False":
        conditions.append(anxiety_pred)

    if not conditions:
        treatment_plan["Overview"] = "No significant mental health conditions detected. Maintain current wellness practices."
        return treatment_plan
    else:
        treatment_plan["Overview"] = f"Comprehensive treatment plan for: {', '.join(conditions)}"

    # ========================
    # DEPRESSION RECOMMENDATIONS
    # ========================
    if depression_pred != "False":
        # Genetic considerations for depression
        dep_genetic = [
            "Review 5-HTTLPR, COMT, and MAOA genotypes for serotonin metabolism insights",
            "Assess BDNF levels and genetic variants for neuroplasticity impact",
            "Evaluate MTHFR status for folate metabolism implications"
        ]
        add_unique("Genetic_Considerations", dep_genetic)

        # Diagnostic confirmation for depression
        dep_diagnostic = [
            "Confirm diagnosis with structured clinical interview (e.g., SCID)",
            "Assess severity using PHQ-9 and clinician-rated scales",
            "Evaluate for comorbid medical conditions affecting mood"
        ]
        add_unique("Diagnostic_Confirmation", dep_diagnostic)

        # Depression-specific interventions
        if depression_pred == "Major Depressive Disorder":
            dep_interventions = [
                "Initiate evidence-based psychotherapy (CBT or IPT)",
                "Consider pharmacogenomic testing for antidepressant selection",
                "Implement mood monitoring system",
                "Assess suicide risk and develop safety plan"
            ]
        elif depression_pred == "Persistent Depressive Disorder":
            dep_interventions = [
                "Long-term psychotherapy approach (CBT or psychodynamic)",
                "Consider combination treatment with medication and therapy",
                "Focus on building resilience and coping strategies",
                "Address chronic stressors and interpersonal factors"
            ]
        elif depression_pred == "Atypical Depression":
            dep_interventions = [
                "Prioritize MAOIs or SSRIs with noradrenergic effects",
                "Focus on regulating sleep and appetite patterns",
                "Behavioral activation to counteract lethargy",
                "Address rejection sensitivity in therapy"
            ]
        elif depression_pred == "Psychotic Depression":
            dep_interventions = [
                "Requires combination of antidepressant and antipsychotic",
                "Close monitoring for safety concerns",
                "Consider inpatient care if severe",
                "Family education and support"
            ]
        elif depression_pred == "Seasonal Affective Disorder":
            dep_interventions = [
                "Light therapy (10,000 lux for 30-45 min daily)",
                "Consider vitamin D supplementation",
                "Timed melatonin administration",
                "Cognitive-behavioral therapy adapted for SAD"
            ]
        add_unique("Personalized_Interventions", dep_interventions)

        # Pharmacological approach for depression
        dep_pharma = [
            "Select antidepressant based on genetic profile and subtype",
            "Consider SSRI first-line unless contraindicated",
            "Monitor for 4-6 weeks before assessing efficacy",
            "Adjust dose based on therapeutic drug monitoring if available"
        ]
        add_unique("Pharmacological_Approach", dep_pharma)

        # Nutrigenomic recommendations for depression
        dep_nutri = [
            "Ensure adequate tryptophan intake (precursor to serotonin)",
            "Optimize omega-3 fatty acids (EPA/DHA 1-2g daily)",
            "Consider methylfolate if MTHFR variants present",
            "Address potential micronutrient deficiencies (B12, zinc, magnesium)"
        ]
        add_unique("Nutrigenomic_Recommendations", dep_nutri)

        # Lifestyle modifications for depression
        dep_lifestyle = [
            "Regular aerobic exercise (3-5x/week)",
            "Sleep hygiene education and regulation",
            "Structured daily routine",
            "Social connection and support system building"
        ]
        add_unique("Lifestyle_Modifications", dep_lifestyle)

    # ========================
    # BIPOLAR DISORDER RECOMMENDATIONS
    # ========================
    if bipolar_pred != "False":
        # Genetic considerations for bipolar
        bp_genetic = [
            "Review ANK3, CACNA1C, and ODZ4 variants for calcium channel insights",
            "Assess circadian gene polymorphisms",
            "Evaluate mitochondrial DNA variants if dysfunction suspected"
        ]
        add_unique("Genetic_Considerations", bp_genetic)

        # Diagnostic confirmation for bipolar
        bp_diagnostic = [
            "Confirm diagnosis with MINI or SCID",
            "Detailed mood episode history and family history",
            "Rule out substance-induced mood episodes",
            "Assess for mixed features"
        ]
        add_unique("Diagnostic_Confirmation", bp_diagnostic)

        # Bipolar-specific interventions
        if bipolar_pred == "BD-I":
            bp_interventions = [
                "Mood stabilizer as foundation (lithium, valproate, or lamotrigine)",
                "Monitor for manic/hypomanic symptoms closely",
                "Psychoeducation about illness course",
                "Develop relapse prevention plan"
            ]
        elif bipolar_pred == "BD-II":
            bp_interventions = [
                "Lamotrigine or quetiapine as first-line",
                "Focus on depression prevention",
                "Careful monitoring for hypomania with antidepressants",
                "Address interpersonal and social rhythm disruptions"
            ]
        elif bipolar_pred == "Cyclothymia":
            bp_interventions = [
                "Consider low-dose mood stabilizer if impairing",
                "Focus on lifestyle regularity",
                "Cognitive therapy for mood swings",
                "Monitor for progression to BD-I or II"
            ]
        add_unique("Personalized_Interventions", bp_interventions)

        # Pharmacological approach for bipolar
        bp_pharma = [
            "Avoid antidepressants without mood stabilizer in BD-I",
            "Consider lithium for suicide prevention in BD",
            "Monitor valproate levels in women of childbearing age",
            "Adjust treatment based on phase (acute vs maintenance)"
        ]
        add_unique("Pharmacological_Approach", bp_pharma)

        # Nutrigenomic recommendations for bipolar
        bp_nutri = [
            "Ensure adequate omega-3 intake (may have mood stabilizing effects)",
            "Consider N-acetylcysteine as adjunctive",
            "Monitor homocysteine levels (may relate to folate metabolism)",
            "Address circadian-related nutrition (timed meals, caffeine management)"
        ]
        add_unique("Nutrigenomic_Recommendations", bp_nutri)

        # Lifestyle modifications for bipolar
        bp_lifestyle = [
            "Strict sleep-wake cycle maintenance",
            "Social rhythm therapy to stabilize daily patterns",
            "Stress reduction techniques",
            "Avoidance of substances and sleep deprivation"
        ]
        add_unique("Lifestyle_Modifications", bp_lifestyle)

    # ========================
    # ANXIETY DISORDER RECOMMENDATIONS
    # ========================
    if anxiety_pred != "False":
        # Genetic considerations for anxiety
        anx_genetic = [
            "Review SLC6A4 and other serotonin transporter variants",
            "Assess COMT Val158Met for stress response impact",
            "Evaluate GABA receptor polymorphisms if panic features present"
        ]
        add_unique("Genetic_Considerations", anx_genetic)

        # Diagnostic confirmation for anxiety
        anx_diagnostic = [
            "Confirm diagnosis with ADIS or similar structured interview",
            "Assess avoidance behaviors and functional impact",
            "Rule out medical causes (hyperthyroidism, etc.)",
            "Evaluate for trauma history if relevant"
        ]
        add_unique("Diagnostic_Confirmation", anx_diagnostic)

        # Anxiety-specific interventions
        if anxiety_pred == "Generalized Anxiety Disorder":
            anx_interventions = [
                "CBT with worry exposure and cognitive restructuring",
                "Mindfulness-based stress reduction",
                "Address intolerance of uncertainty",
                "Problem-solving skills training"
            ]
        elif anxiety_pred == "Panic Disorder":
            anx_interventions = [
                "Interoceptive exposure therapy",
                "Cognitive restructuring of catastrophic interpretations",
                "Breathing retraining",
                "Gradual exposure to avoided situations"
            ]
        elif anxiety_pred == "Social Anxiety Disorder":
            anx_interventions = [
                "Social skills training if deficits present",
                "Cognitive restructuring of negative beliefs",
                "Exposure to social situations",
                "Attention retraining for self-focused attention"
            ]
        elif anxiety_pred == "Agoraphobia":
            anx_interventions = [
                "In vivo exposure hierarchy development",
                "Cognitive challenging of safety behaviors",
                "Gradual expansion of safe zone",
                "Partner/family involvement if helpful"
            ]
        elif anxiety_pred == "Specific Phobia":
            anx_interventions = [
                "Exposure therapy tailored to phobic stimulus",
                "Systematic desensitization",
                "Cognitive restructuring of threat appraisal",
                "Modeling and reinforcement techniques"
            ]
        add_unique("Personalized_Interventions", anx_interventions)

        # Pharmacological approach for anxiety
        anx_pharma = [
            "Consider SSRI/SNRI as first-line pharmacotherapy",
            "Short-term benzodiazepine only if severe impairment",
            "Monitor for initial anxiety exacerbation with SSRIs",
            "Consider buspirone for GAD if SSRI not tolerated"
        ]
        add_unique("Pharmacological_Approach", anx_pharma)

        # Nutrigenomic recommendations for anxiety
        anx_nutri = [
            "Ensure balanced blood sugar (avoid hypoglycemia triggers)",
            "Consider L-theanine and magnesium for relaxation",
            "Monitor caffeine and alcohol intake",
            "Adequate protein intake for amino acid precursors"
        ]
        add_unique("Nutrigenomic_Recommendations", anx_nutri)

        # Lifestyle modifications for anxiety
        anx_lifestyle = [
            "Regular exercise (yoga can be particularly helpful)",
            "Breathing and relaxation practice",
            "Stimulant reduction (caffeine, nicotine)",
            "Sleep hygiene optimization"
        ]
        add_unique("Lifestyle_Modifications", anx_lifestyle)

    # ========================
    # COMBINATION CONSIDERATIONS
    # ========================

    # Special considerations for combinations
    combo_special = []

    # Depression + Anxiety
    if depression_pred != "False" and anxiety_pred != "False":
        combo_special.extend([
            "Address depression first if severe as it may limit anxiety treatment engagement",
            "Consider SNRIs that treat both conditions",
            "Modify CBT to address both disorders simultaneously",
            "Monitor for increased suicide risk with mixed depression/anxiety"
        ])

    # Bipolar + Anxiety
    if bipolar_pred != "False" and anxiety_pred != "False":
        combo_special.extend([
            "Stabilize mood first before aggressively treating anxiety",
            "Avoid benzodiazepines if possible (risk of misuse, worsening depression)",
            "Consider quetiapine or lurasidone which may help both",
            "Address anxiety in context of mood stability"
        ])

    # Bipolar + Depression
    if bipolar_pred != "False" and depression_pred != "False":
        combo_special.extend([
            "Differentiate between unipolar and bipolar depression in treatment approach",
            "Caution with antidepressants - use only with mood stabilizer",
            "Consider lamotrigine for bipolar depression",
            "Monitor closely for switching to hypomania/mania"
        ])

    # All three conditions
    if (depression_pred != "False" and bipolar_pred != "False"
        and anxiety_pred != "False"):
        combo_special.extend([
            "Prioritize mood stabilization as foundation",
            "Sequential treatment approach - bipolar stability first, then depression, then anxiety",
            "Consider comprehensive DBT approach for emotion regulation",
            "Multidisciplinary team management essential"
        ])

    add_unique("Special_Considerations", combo_special)

    # ========================
    # THERAPEUTIC APPROACHES
    # ========================
    therapies = []

    # Common evidence-based therapies
    therapies.extend([
        "Cognitive Behavioral Therapy (tailored to primary diagnosis)",
        "Psychoeducation about condition(s) and treatment",
        "Mindfulness-based interventions",
        "Behavioral activation (especially for depression)"
    ])

    # Condition-specific therapies
    if bipolar_pred != "False":
        therapies.extend([
            "Interpersonal and Social Rhythm Therapy (IPSRT)",
            "Family-focused therapy for bipolar disorder"
        ])

    if anxiety_pred != "False":
        therapies.extend([
            "Exposure-based therapies",
            "Acceptance and Commitment Therapy (ACT)"
        ])

    if depression_pred != "False":
        therapies.extend([
            "Behavioral Activation",
            "Problem-Solving Therapy"
        ])

    add_unique("Therapeutic_Approaches", therapies)

    # ========================
    # MONITORING AND FOLLOWUP
    # ========================
    monitoring = [
        "Regular clinical follow-up (frequency depends on severity)",
        "Standardized symptom tracking (e.g., mood charts, anxiety diaries)",
        "Routine labs as needed (lithium levels, metabolic monitoring)",
        "Periodic re-assessment of treatment plan efficacy",
        "Functional outcome assessment (work, relationships, quality of life)"
    ]

    if bipolar_pred != "False":
        monitoring.extend([
            "Mood episode symptom monitoring",
            "Early warning sign identification plan"
        ])

    if depression_pred != "False":
        monitoring.extend([
            "Suicide risk reassessment at each contact",
            "PHQ-9 tracking over time"
        ])

    if anxiety_pred != "False":
        monitoring.extend([
            "Exposure hierarchy progress tracking",
            "Anxiety diary review"
        ])

    add_unique("Monitoring_and_Followup", monitoring)

    return treatment_plan

if __name__ == '__main__':
    app.run(debug=True)