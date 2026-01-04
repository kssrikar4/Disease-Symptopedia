import streamlit as st
import csv
from collections import defaultdict
from pathlib import Path


class StreamlitDataLoader:
    @st.cache_resource
    def load_data_cached(_self, mappings_csv, diseases_csv, symptoms_csv):
        return {
            'mappings': _self._load_mappings(mappings_csv),
            'symptoms': _self._get_symptoms(symptoms_csv),
            'd2s': _self._build_d2s(mappings_csv),
            's2d': _self._build_s2d(mappings_csv),
        }

    @staticmethod
    def _load_mappings(csv_file):
        mappings = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            mappings = list(reader)
        return mappings

    @staticmethod
    def _get_symptoms(csv_file):
        symptoms = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                symptoms.append(row['symptom_name'])
        return sorted(list(set(symptoms)))

    @staticmethod
    def _build_d2s(csv_file):
        d2s = defaultdict(list)
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                disease = row['disease_name']
                symptom = row['symptom_name']
                rank = int(row['symptom_rank'])
                d2s[disease].append((rank, symptom))

        for disease in d2s:
            d2s[disease] = [s for _, s in sorted(d2s[disease])]

        return dict(d2s)

    @staticmethod
    def _build_s2d(csv_file):
        s2d = defaultdict(list)
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                disease = row['disease_name']
                symptom = row['symptom_name']
                s2d[symptom].append(disease)

        return dict(s2d)


def init_streamlit_app(mappings_csv, diseases_csv, symptoms_csv):
    loader = StreamlitDataLoader()
    data = loader.load_data_cached(mappings_csv, diseases_csv, symptoms_csv)
    return data