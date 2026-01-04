import re
import csv
import logging
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from urllib.request import urlopen
from urllib.error import URLError
import time
from html.parser import HTMLParser

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.current_row = []
        self.rows = []
        self.cell_data = []

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.in_table = True
        elif tag == 'tr' and self.in_table:
            self.in_row = True
            self.current_row = []
        elif tag == 'td' and self.in_row:
            self.in_cell = True
            self.cell_data = []

    def handle_endtag(self, tag):
        if tag == 'table':
            self.in_table = False
        elif tag == 'tr' and self.in_row:
            self.in_row = False
            if self.current_row:
                self.rows.append(self.current_row)
        elif tag == 'td' and self.in_cell:
            self.in_cell = False
            cell_text = ''.join(self.cell_data).strip()
            self.current_row.append(cell_text)

    def handle_data(self, data):
        if self.in_cell:
            self.cell_data.append(data)


class DiseaseSymptomScraper:
    def __init__(self):
        self.url = "https://people.dbmi.columbia.edu/~friedma/Projects/DiseaseSymptomKB/index.html"
        self.max_retries = 3
        self.timeout = 10

    def fetch_html(self):
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Fetching from {self.url} (attempt {attempt + 1})")
                with urlopen(self.url, timeout=self.timeout) as response:
                    html_bytes = response.read()
                    for encoding in ['utf-8', 'iso-8859-1', 'latin-1', 'cp1252']:
                        try:
                            html = html_bytes.decode(encoding)
                            logger.info(f"Fetched {len(html)} chars using {encoding}")
                            return html
                        except UnicodeDecodeError:
                            continue
                    html = html_bytes.decode('utf-8', errors='replace')
                    return html
            except URLError as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise

    def parse_html_table(self, html):
        logger.info("Parsing HTML table...")
        parser = TableParser()
        parser.feed(html)
        logger.info(f"Found {len(parser.rows)} table rows")

        parsed_data = []
        current_disease = None
        current_frequency = None

        for row in parser.rows:
            if not row or len(row) < 3:
                continue

            if 'Disease' in row[0] or 'disease' in row[0].lower() and 'count' in row[1].lower():
                continue

            col1 = row[0].strip()
            col2 = row[1].strip() if len(row) > 1 else ''
            col3 = row[2].strip() if len(row) > 2 else ''

            if col1 and 'UMLS:' in col1:
                if col2 and col2.replace(',', '').isdigit():
                    current_disease = col1
                    current_frequency = col2.replace(',', '')
                    if col3 and 'UMLS:' in col3:
                        parsed_data.append({
                            'disease_code': current_disease,
                            'frequency': current_frequency,
                            'symptom_code': col3
                        })
            elif col3 and 'UMLS:' in col3 and current_disease:
                parsed_data.append({
                    'disease_code': current_disease,
                    'frequency': current_frequency,
                    'symptom_code': col3
                })

        logger.info(f"Extracted {len(parsed_data)} disease-symptom pairs")
        return parsed_data


class DataProcessor:
    @staticmethod
    def clean_umls_code(code):
        if not code:
            return ""

        code = ' '.join(code.split())

        if '^' in code:
            code = code.split('^')[-1].strip()

        if '_' in code:
            parts = code.split('_', 1)
            if len(parts) > 1 and parts[1].strip():
                name = parts[1]
            else:
                name = parts[0].replace('UMLS:', '')
        else:
            name = code.replace('UMLS:', '')

        name = name.replace('_', ' ')
        name = ' '.join(name.split())
        name = name.strip()

        if not name or name == '':
            return code

        return name

    @staticmethod
    def validate_data(data):
        logger.info("Validating data...")
        valid_data = []
        invalid = 0

        for item in data:
            if not item['disease_code'] or not item['symptom_code']:
                invalid += 1
                continue

            disease_clean = DataProcessor.clean_umls_code(item['disease_code'])
            symptom_clean = DataProcessor.clean_umls_code(item['symptom_code'])

            if not disease_clean or not symptom_clean:
                invalid += 1
                continue

            try:
                if int(item['frequency']) < 0:
                    invalid += 1
                    continue
            except (ValueError, TypeError):
                invalid += 1
                continue

            valid_data.append(item)

        logger.info(f"Valid: {len(valid_data)}, Invalid: {invalid}")
        return valid_data

    @staticmethod
    def create_disease_df(data):
        diseases = {}
        for item in data:
            code = item['disease_code']
            if code not in diseases:
                cleaned = DataProcessor.clean_umls_code(code)
                if cleaned:
                    diseases[code] = cleaned

        logger.info(f"Extracted {len(diseases)} unique diseases")
        return list(diseases.items())

    @staticmethod
    def create_symptom_df(data):
        symptoms = {}
        for item in data:
            code = item['symptom_code']
            if code not in symptoms:
                cleaned = DataProcessor.clean_umls_code(code)
                if cleaned:
                    symptoms[code] = cleaned

        logger.info(f"Extracted {len(symptoms)} unique symptoms")
        return list(symptoms.items())

    @staticmethod
    def create_mapping_df(data):
        mapping_data = []
        disease_symptoms = defaultdict(list)

        for item in data:
            disease_name = DataProcessor.clean_umls_code(item['disease_code'])
            symptom_name = DataProcessor.clean_umls_code(item['symptom_code'])

            if not disease_name or not symptom_name:
                continue

            frequency = int(item['frequency'])
            disease_symptoms[disease_name].append({
                'symptom': symptom_name,
                'frequency': frequency
            })

        for disease, symptoms in disease_symptoms.items():
            for rank, symptom_info in enumerate(symptoms, 1):
                mapping_data.append({
                    'disease_name': disease,
                    'symptom_name': symptom_info['symptom'],
                    'frequency_count': symptom_info['frequency'],
                    'symptom_rank': rank
                })

        logger.info(f"Created {len(mapping_data)} mappings")
        return mapping_data


class CSVWriter:
    def __init__(self, output_dir="disease_symptom_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def write_mappings(self, data):
        filename = self.output_dir / f"disease_symptom_mappings_{self.timestamp}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['disease_name', 'symptom_name', 'frequency_count', 'symptom_rank'])
            writer.writeheader()
            writer.writerows(data)
        logger.info(f"Wrote {len(data)} mappings to {filename}")
        return filename

    def write_diseases(self, data):
        filename = self.output_dir / f"diseases_{self.timestamp}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['disease_code', 'disease_name'])
            writer.writerows(data)
        logger.info(f"Wrote {len(data)} diseases to {filename}")
        return filename

    def write_symptoms(self, data):
        filename = self.output_dir / f"symptoms_{self.timestamp}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['symptom_code', 'symptom_name'])
            writer.writerows(data)
        logger.info(f"Wrote {len(data)} symptoms to {filename}")
        return filename


class DataLoader:
    def __init__(self, mappings_csv, diseases_csv, symptoms_csv):
        self.mappings_csv = mappings_csv
        self.diseases_csv = diseases_csv
        self.symptoms_csv = symptoms_csv
        self._mappings = None
        self._disease_to_symptoms = None
        self._symptom_to_diseases = None
        self._unique_symptoms = None

    def load_mappings(self):
        if self._mappings is not None:
            return self._mappings
        with open(self.mappings_csv, 'r', encoding='utf-8') as f:
            self._mappings = list(csv.DictReader(f))
        return self._mappings

    def get_unique_symptoms(self):
        if self._unique_symptoms is not None:
            return self._unique_symptoms
        with open(self.symptoms_csv, 'r', encoding='utf-8') as f:
            symptoms = [row['symptom_name'] for row in csv.DictReader(f)]
            self._unique_symptoms = sorted(symptoms)
        return self._unique_symptoms

    def get_disease_to_symptoms(self):
        if self._disease_to_symptoms is not None:
            return self._disease_to_symptoms
        mappings = self.load_mappings()
        d2s = defaultdict(list)
        for m in mappings:
            d2s[m['disease_name']].append((int(m['symptom_rank']), m['symptom_name']))
        self._disease_to_symptoms = {d: [s for _, s in sorted(syms)] for d, syms in d2s.items()}
        return self._disease_to_symptoms

    def get_symptom_to_diseases(self):
        if self._symptom_to_diseases is not None:
            return self._symptom_to_diseases
        mappings = self.load_mappings()
        s2d = defaultdict(list)
        for m in mappings:
            s2d[m['symptom_name']].append(m['disease_name'])
        self._symptom_to_diseases = dict(s2d)
        return self._symptom_to_diseases

    def get_confidence_score(self, disease, symptom):
        for m in self.load_mappings():
            if m['disease_name'] == disease and m['symptom_name'] == symptom:
                return max(0, 1 - (int(m['symptom_rank']) / 100))
        return 0.0


def main():
    logger.info("Starting Disease-Symptom Pipeline - CLEANED VERSION\n")

    try:
        logger.info("=== STEP 1: Data Collection ===")
        scraper = DiseaseSymptomScraper()
        html = scraper.fetch_html()
        raw_data = scraper.parse_html_table(html)

        if len(raw_data) == 0:
            logger.error("No data extracted!")
            sys.exit(1)

        logger.info("\n=== STEP 2: Data Validation ===")
        validated_data = DataProcessor.validate_data(raw_data)

        logger.info("\n=== STEP 3: Data Processing ===")
        diseases = DataProcessor.create_disease_df(validated_data)
        symptoms = DataProcessor.create_symptom_df(validated_data)
        mappings = DataProcessor.create_mapping_df(validated_data)

        logger.info("\n=== STEP 4: Writing CSV Files ===")
        writer = CSVWriter()
        mappings_file = writer.write_mappings(mappings)
        diseases_file = writer.write_diseases(diseases)
        symptoms_file = writer.write_symptoms(symptoms)

        logger.info("\n=== STEP 5: Testing Data Loader ===")
        loader = DataLoader(mappings_file, diseases_file, symptoms_file)
        symptoms_list = loader.get_unique_symptoms()
        logger.info(f"Unique symptoms: {len(symptoms_list)}")
        logger.info(f"Sample: {symptoms_list[:5]}")

        d2s = loader.get_disease_to_symptoms()
        logger.info(f"Total diseases: {len(d2s)}")
        if d2s:
            first = list(d2s.keys())[0]
            logger.info(f"Example: {first} -> {d2s[first][:3]}")

        s2d = loader.get_symptom_to_diseases()
        if s2d:
            first = list(s2d.keys())[0]
            logger.info(f"Example: {first} -> {s2d[first][:3]}")

        logger.info(f"\n✅ SUCCESS! Got {len(d2s)} diseases and {len(symptoms_list)} symptoms!")
        logger.info(f"📁 Output: {writer.output_dir}")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()