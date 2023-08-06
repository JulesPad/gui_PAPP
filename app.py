from flask import Flask, render_template, request, session, redirect, url_for
import subprocess, os, time, json

app = Flask(__name__)
app.secret_key = 'your secret key'

with open("question_checked.json", "r") as json_file:
    questions = json.load(json_file)

@app.route('/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        session['first_name'] = request.form.get('first_name')
        session['last_name'] = request.form.get('last_name')
        # Initialize animated_milestones here
        session['animated_milestones'] = { '25': False, '50': False, '75': False }
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/home')
def home():
    # Initialize animated_milestones here
    if 'animated_milestones' not in session:
        session['animated_milestones'] = { '25': False, '50': False, '75': False }

    if 'first_name' not in session or 'last_name' not in session:
        return redirect(url_for('register'))

    session['user_profile'] = {"REALISTE":0, "INVESTIGATEUR":0, "ARTISTIQUE":0, "SOCIAL":0, "ENTREPRENANT":0, "CONVENTIONNEL":0, "PLEIN AIR & PHYSIQUE":0, "PRATIQUE":0, "TECHNIQUE":0, "SCIENTIFIQUE":0, "COMMUNICATION":0, "ESTHETIQUE":0, "SOUTIEN SOCIAL":0, "SOINS MEDICAUX":0, "NEGOCIATION":0, "LEADERSHIP":0, "TRAVAIL de BUREAU":0, "INTÉRÊT POUR LES DONNÉES":0, "AGRICULTURE et PECHE":0, "MONDE ANIMALIER":0, "SPORT":0, "FORCES DE L’ORDRE":0, "BATIMENT ET TRAVAUX PUBLICS":0, "TRANSPORTS":0, "HOTELLERIE, RESTAURATION et TOURISME":0, "MECANIQUE":0, "DOMAINE INDUSTRIEL":0, "ÉLECTRICITÉ":0, "SCIENCES DE LA TERRE et DE LA MATIERE":0, "SCIENCES DE LA VIE":0, "MATHEMATIQUES":0, "ARTS DU SPECTACLE":0, "LETTRES":0, "ARTS GRAPHIQUES":0, "ARTS APPLIQUES":0, "ACCOMPAGNEMENT SOCIAL":0, "ENSEIGNEMENT & FORMATION":0, "SOINS MEDICAUX":0, "PARAMEDICAL":0, "VENTE DE PRODUITS ET DE SERVICES":0, "MARKETING et PUBLICITE":0, "JURIDIQUE et POLITIQUE":0, "MANAGEMENT":0, "RESSOURCES HUMAINES":0, "ADMINISTRATION":0, "COMPTABILITÉ et FINANCES":0, "INFORMATIQUE":0} # your existing initialization
    session['user_profile_keys'] = list(session['user_profile'].keys())
    session['question_number'] = 0

    # Initialize milestones here
    if 'milestones' not in session:
        session['milestones'] = { '25': False, '50': False, '75': False }

   
    total_questions = len(questions)
    return render_template('index.html', 
                           question=questions[session['question_number']], 
                           question_number=session['question_number']+1, 
                           user_profile=to_ordered_list(session['user_profile'], session['user_profile_keys']),
                           first_name=session['first_name'], 
                           last_name=session['last_name'],
                           milestones=session.get('milestones', { '25': False, '50': False, '75': False }),
                           animated_milestones=session.get('animated_milestones', { '25': False, '50': False, '75': False }),
                           total_questions=total_questions)  # Add total_questions here



@app.route('/next_question', methods=['POST'])
def next_question():
    selected_answer = request.form.get('answer')
    if selected_answer != "noneOfThose":
        session['user_profile'] = update_profile(questions[session['question_number']], selected_answer, session['user_profile'])

    with open(f"{session['first_name']}_{session['last_name']}_profile.json", 'w') as f:
        json.dump(session['user_profile'], f)
        
    session['question_number'] += 1
    session.modified = True 
    # Calculate milestones
    total_questions = len(questions)
    milestones = {
        '25': session['question_number'] / total_questions == 0.25,
        '50': session['question_number'] / total_questions == 0.50,
        '75': session['question_number'] / total_questions == 0.75,
    }

    session['milestones'] = milestones

    for percentage in milestones:
        if milestones[percentage] and not session['animated_milestones'][percentage]:
            session['animated_milestones'][percentage] = True

    session.modified = True

    if session['question_number'] >= total_questions:
        return redirect(url_for('results'))
    total_questions = len(questions)
    return render_template('index.html', 
                           question=questions[session['question_number']], 
                           question_number=session['question_number']+1, 
                           user_profile=to_ordered_list(session['user_profile'], session['user_profile_keys']),
                           first_name=session['first_name'], 
                           last_name=session['last_name'],
                           milestones=session.get('milestones', { '25': False, '50': False, '75': False }),
                           animated_milestones=session.get('animated_milestones', { '25': False, '50': False, '75': False }),
                           total_questions=total_questions)  # Add total_questions here

def update_profile(question, selected_answer, user_profile):
    answer_values = question['answers'][selected_answer]
    for key in answer_values:
        if key in user_profile:
            user_profile[key] += answer_values[key]
    return user_profile


@app.route('/set_animated', methods=['POST'])
def set_animated():
    percentage = request.form.get('percentage')
    if percentage in session['animated_milestones']:
        session['animated_milestones'][percentage] = True
    session.modified = True 
    return "success", 200

@app.route('/results')
def results():
    first_name = session['first_name']
    last_name = session['last_name']

    # Add code here to load profile from JSON file
    with open(f"{session['first_name']}_{session['last_name']}_profile.json", 'r') as f:
        user_profile = json.load(f)
    
    # Order the profile using the predefined key order in the session
    ordered_user_profile = to_ordered_list(user_profile, session['user_profile_keys'])

    # Save the ordered profile back to the same file. 
    # Convert the list of (key, value) pairs back to a dictionary before saving it.
    with open(f"{first_name}_{last_name}_profile_ordered.json", 'w') as f:
        json.dump({k: v for k, v in ordered_user_profile}, f)
    

    subprocess.Popen(['python', 'analysis.py', first_name, last_name])

    # Monitor the analysis file for changes
    analysis_file_path = "analysis.txt"

    # If the file doesn't exist yet, wait for it
    while not os.path.exists(analysis_file_path):
        time.sleep(1)

    # Get the initial modification time
    initial_mtime = os.path.getmtime(analysis_file_path)
    print("Initial modification time:", initial_mtime)
    while True:
        time.sleep(1)  # Check every second
        current_mtime = os.path.getmtime(analysis_file_path)
        if current_mtime != initial_mtime:
            break

    
    print("Analysis file has been modified")
    with open("analysis.txt", 'r') as f:
        analysis = f.read()

    print("Analysis:", analysis)
    ordered_user_profile = to_ordered_list(user_profile, session['user_profile_keys'])
    return render_template('final.html', user_profile=ordered_user_profile, first_name=first_name, last_name=last_name, analysis=analysis)







def to_ordered_list(dict, keys_order):
    return [(key, dict[key]) for key in keys_order]

if __name__ == '__main__':
    app.run(debug=True)
