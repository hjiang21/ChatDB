# script used to fuzzy match patient profile dataset, create dataframes for table upload, and finally upload tables into postgres via neon tech 
# DATABASE SEEDING & LOADING SCRIPT 

import pandas as pd
from rapidfuzz import fuzz, process
from sqlalchemy import create_engine


def main():
    # load datasets 
    df_diseases = pd.read_csv('disease_data.csv')
    df_patients = pd.read_csv('patient_profile_disease_symptoms.csv')


    # creating disease master list (only unique instances from Disease & Overview)
    df_cleaned = df_diseases[['Disease', 'Overview']].drop_duplicates()
    df_cleaned = df_cleaned[df_cleaned['Disease'].notna()]      
    df_cleaned = df_cleaned[df_cleaned['Disease'].str.strip() != ""]    
    df_overview = df_cleaned[df_cleaned['Overview'].notna()]     # drop diseases that are missing an overview 
    df_overview.reset_index(drop=True, inplace=True)



    # ensure disease names are all in same casing (lowercasing) 
    df_overview['name'] = df_overview['Disease'].str.strip().str.lower()
    df_patients['disease'] = df_patients['Disease'].str.strip().str.lower()
    df_patients['outcome'] = df_patients['Outcome Variable'].str.strip().str.lower()     # add patients outcomes 



    # disease names across different datasets may be entered slightly differently, do fuzzy matching to standardize disease list across datasets
    # keep only the diseases that have at least a 90% match 
    disease_map = {}
    for d in df_patients['disease'].unique():
        # first pass with token sort scorer
        match, score, _ = process.extractOne(d, df_overview['name'].tolist(), scorer=fuzz.token_sort_ratio)
        if score >= 90:
            matched_disease = df_overview[df_overview['name'] == match]['Disease'].values[0]    # grabbing original formatting of the disease name 
            disease_map[d] = matched_disease
        elif score < 90 and len(d) > 5:
            # second pass with partial scorer to catch stragglers 
            # (can't use for disease names that are too short, e.g. 'uti' 100% matched 'autism spectrum disorder')
            match, score2, _ = process.extractOne(d, df_overview['name'].tolist(), scorer=fuzz.partial_ratio)
            if score2 >= 90:
                matched_disease = df_overview[df_overview['name'] == match]['Disease'].values[0]
                disease_map[d] = matched_disease



    # mapping the master list fuzzy-matched disease names onto the patient dataset 
    df_patients['matched_disease'] = df_patients['disease'].map(disease_map)
    df_patients = df_patients[df_patients['matched_disease'].notnull()]  # filter out entries with no match (to facilitate cleaner joins later on)


    # build disease table (make IDs in dxxx format)
    df_disease = df_overview[['Disease', 'Overview']].drop_duplicates().rename(columns={'Disease': 'name', 'Overview': 'overview'}).reset_index(drop=True)
    df_disease['disease_id'] = ['d' + str(i+1).zfill(3) for i in range(len(df_disease))]  # zfill to leftside pad with 0s --> d001, d002, etc. 


    # build symptom table (make IDs in sxxx format) 
    # only using symptoms from Extra Symptoms column bc the symptoms in the binary columns seem to show up there anyway 
    symptom_set = set() # store as set variable to avoid duplicates 
    for s_list in df_patients['Extra symptoms'].dropna():    
        if isinstance(s_list, str):
            for s in eval(s_list):
                symptom_set.add(s.strip().lower())

    symptom_list = sorted(symptom_set)
    df_symptom = pd.DataFrame({'name': symptom_list})
    df_symptom['symptom_id'] = ['s' + str(i+1).zfill(3) for i in range(len(df_symptom))]    # s001, s002, etc. 


    # build joint disease_symptom table from df_disease & df_symptom 
    disease_lookup = dict(zip(df_disease['name'], df_disease['disease_id']))    # {'disease_name1': 'd001', 'disease_name2': 'd002', ...}
    symptom_lookup = dict(zip(df_symptom['name'], df_symptom['symptom_id']))    # {'symptom_name1': 's001', 'symptom_name2': 's002', ...}

    join_rows = []
    for _, row in df_patients.iterrows():
        if row['outcome'] == 'positive':    # only consider positive diagnoses 
            did = disease_lookup[row['matched_disease']] 
            if isinstance(row['Extra symptoms'], str):  # row['Extra Symptoms'] looks like '['symptom1', 'symptom2', 'symptom3', ... ]
                for s in eval(row['Extra symptoms']):
                    sid = symptom_lookup[s.strip().lower()]
                    join_rows.append({'disease_id': did, 'symptom_id': sid})


    df_disease_symptom = pd.DataFrame(join_rows).drop_duplicates()


    # build patient table (make IDs in pxxx format), include corresponding disease_id
    df_patient = df_patients.rename(columns={'Age': 'age', 'Gender': 'gender'})[['age', 'gender', 'matched_disease']]
    df_patient['disease_id'] = df_patient['matched_disease'].map(disease_lookup)
    df_patient = df_patient.drop(columns=['matched_disease'])

    # Add patient_id in format p001, p002, etc.
    df_patient = df_patient.reset_index(drop=True)
    df_patient['patient_id'] = ['p' + str(i+1).zfill(4) for i in range(len(df_patient))]    # p0001, p0002, etc. 
    df_patient = df_patient[['patient_id', 'age', 'gender', 'disease_id']]




    import os
    from sqlalchemy import create_engine

    sync_url = os.getenv("DATABASE_URL_SYNC")
    if not sync_url:
        raise RuntimeError("DATABASE_URL_SYNC is not set. Add it to your .env")


    # upload processed dataframes as tables into postgres (using online postgres provider, Neon PostgreSQL) 
    engine = create_engine(sync_url, future=True, pool_pre_ping=True)
    df_disease[['disease_id', 'name', 'overview']].to_sql('disease', engine, if_exists='replace', index=False)
    df_symptom[['symptom_id', 'name']].to_sql('symptom', engine, if_exists='replace', index=False)
    df_disease_symptom.to_sql('disease_symptom', engine, if_exists='replace', index=False)
    df_patient.to_sql('patient', engine, if_exists='replace', index=False)




if __name__ == "__main__":
    main()

