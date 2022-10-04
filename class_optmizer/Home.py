import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pymongo import MongoClient

def add_test_data():
    """Adding mock data on MongoDB for testing purposes"""

    SUBJECT = "TESTE"
    SUBJECT2 = "TESTE2"
    TOPICS = ["Funções", "Módulos", "Decoradores"]
    TOPICS2 = ["BLA1", "BLA2"]
    NSTUDENTS = 5
    np.random.seed(123)
    MOCK_ANSWERS = []
    MOCK_ANSWERS2 = []

    for _ in range(NSTUDENTS):
        answers = {topic: int(np.random.choice(range(6))) for topic in TOPICS}
        MOCK_ANSWERS.append({"subject": SUBJECT, "answers_for_topics": answers.copy()})

    for _ in range(NSTUDENTS):
        answers = {topic: int(np.random.choice(range(6))) for topic in TOPICS2}
        MOCK_ANSWERS2.append({"subject": SUBJECT2, "answers_for_topics": answers.copy()})

    with MongoClient(st.secrets["mdb_conn_string"]) as client:
        db = client.class_optmizer_db
        # Adding a test subject
        db.subjects.insert_one({"subject": SUBJECT, "topics": TOPICS})
        db.subjects.insert_one({"subject": SUBJECT2, "topics": TOPICS2})
        # Adding answers
        db.answers.insert_many(MOCK_ANSWERS)
        db.answers.insert_many(MOCK_ANSWERS2)

def clear_database():
    with MongoClient(st.secrets["mdb_conn_string"]) as client:
        db = client.class_optmizer_db
        db.drop_collection("subjects")
        db.drop_collection("answers")

def get_data(subject: str = ""):
    """Get answers data from mongo database based on the subject"""
    with MongoClient(st.secrets["mdb_conn_string"]) as _client:
        if subject:
            data = list(_client.class_optmizer_db.answers.find({"subject": subject}))
        else:
            data = list(_client.class_optmizer_db.answers.find())

    return data


def set_up_data(subject):
    """
    Set up data for the part of the program that plot and handle
    answers
    """
    subject_ans = get_data(subject)
    answers = [ans["answers_for_topics"] for ans in subject_ans]
    data = pd.DataFrame(answers)
    fig = px.box(
            data,
            labels={"value": "Grau de familiaridade", "variable": "Tópico"},
            title="Familiaridade por tópico",
            points="all",
            )

    return data, answers, fig


if __name__ == "__main__":

    st.set_page_config(page_title="Class Optimizer", layout="wide")

    if st.button("Adicionar dados de teste"):
        add_test_data()

    if st.button("Limpar base de dados"):
        clear_database()

    if st.checkbox("Mostrar dados"):
        data = get_data()
        st.write(data)



    # Explainer 

    with st.container():

        st.title("Otimizador de aulas (v$\\alpha$)")

        st.write(
            """
            Este é um pequeno app cujo o intuito é otimizar as aulas do nosso
            curso, aproveitando da ferramenta fundamental abordada no curso: A
            análise de dados.


            A proposta é compartilhar dados entre os alunos e o professor para
            que o mesmo consiga adaptar melhor as aulas à nossa demanda.


            Para isso pedimos para que os colegas, de forma **anônima**,
            compartilhem o nível de familiaridade (numa escala de 0 a 5) em um
            conjunto de tópicos que serão ministrados em uma aula. Assim
            poderemos visualizar a distribuição da familiaridade por tópico de
            cada aula, assim o professor será capaz de adaptar as aulas para
            melhor atender à turma, otimizando o tempo e maximizando o
            aprendizado.
            """
        )

        st.warning( "Atenção: Este app é bem simples e portanto vunerável a ataques. Favor compartilhar o link apenas entre os colegas.")

    with st.container():
        
        st.title("Selecionar um assunto para dar feedback sobre os tópicos")

        with MongoClient(st.secrets["mdb_conn_string"]) as client:
            available_subjects_d = list(client.class_optmizer_db.subjects.find())
            available_subjects = [subject["subject"] for subject in available_subjects_d]

        subject = st.selectbox("Selecione o assunto", available_subjects)
        try:
            topics = next(filter(lambda x: x["subject"] == subject, available_subjects_d))["topics"]
        except StopIteration:
            print("Error: There isn't any topic available. Check if there is one on the database")
            st.warning("Se disponível, escolha um tópico")
            st.stop()

    
    # Status

    with st.container():

        st.title(f"Estado atual do feedback para: {subject}")

        if subject:
            data, answers, fig = set_up_data(subject)

        else:
            st.warning("Sem assunto para selecionar dados")
            st.stop()



        if st.checkbox("Mostrar Dados brutos"):

            summary_stats = data.describe()

            left, right = st.columns(2)

            with left:
                "Tabela"
                data

            with right:
                "Sumário"
                summary_stats

        plot_placeholder = st.empty()
        plot_placeholder.plotly_chart(fig)

        st.title("Compartilhar familiaridade com os tópicos")

        with st.form("my_form"):

           ans = {}

           for topic in topics:
               ans[topic] = st.slider(f"{topic}", 0, 5, 0)


           # Every form must have a submit button.
           submitted = st.form_submit_button("Enviar")


        if submitted:
            # Database Insertion
            with MongoClient(st.secrets["mdb_conn_string"]) as client:
                    db = client.class_optmizer_db
                    db.answers.insert_one({"subject": subject, "answers_for_topics": ans})

            # Feedback
            st.write("Resposta enviada!")
            st.json(ans)

            data, answers, fig = set_up_data(subject)
            plot_placeholder.plotly_chart(fig)
