import pandas as pd
import re
from fuzzywuzzy import fuzz
from itertools import combinations
from difflib import SequenceMatcher
from Levenshtein import distance as levenshtein_distance


def normalize_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # remove punctuation
    text = re.sub(r'\s+', ' ', text).strip()  # remove extra spaces
    return text


def load_all_sheets(path, exclude_sheets=['Familia Corporativa']):
    xls = pd.ExcelFile(path)
    df_all = []
    for sheet in xls.sheet_names:
        if sheet not in exclude_sheets:
            df = xls.parse(sheet)
            if {'Marca', 'Nombre SKU', 'SKU'}.issubset(df.columns):
                df = df[['Marca', 'Nombre SKU', 'SKU']].copy()
                df['Sheet'] = sheet
                df_all.append(df)
    return pd.concat(df_all, ignore_index=True)


def extract_good_numbers(text):
    """Extracts all meaningful numbers, including fractions, decimals, and numbers inside letter combos like 180ML."""
    text_clean = re.sub(r'\([^)]*\)', '', text)  # remove anything in parentheses

    # Extract and remove fractions like "1/2"
    fractions = re.findall(r'\b(\d+)\s*/\s*(\d+)\b', text_clean)
    fraction_values = [int(n) / int(d) for n, d in fractions if int(d) != 0]
    text_clean = re.sub(r'\b\d+\s*/\s*\d+\b', '', text_clean)

    # Extract and remove decimal numbers like "3.5"
    decimal_numbers = re.findall(r'\d+\.\d+', text_clean)
    decimal_values = list(map(float, decimal_numbers))
    text_clean = re.sub(r'\d+\.\d+', '', text_clean)

    # Extract embedded numbers like "180ML", "50g"
    embedded_numbers = re.findall(r'\d+(?=[a-zA-Z])', text_clean)

    after_letter = re.findall(r'(?<=[a-zA-Z])\d+', text_clean)

    standalone_numbers = re.findall(r'\b\d+\b', text_clean)

    all_numbers = list(map(float, standalone_numbers + after_letter + embedded_numbers)) + fraction_values + decimal_values
    return all_numbers



def find_similar_products(df, similarity_threshold=90, different_sku=True):
    """different_sku = true -- if we find similar products with different skus
    if false find with the same sku"""
    df['Norm Name'] = df['Nombre SKU'].apply(normalize_text)
    df['Marca'] = df['Marca'].str.strip().str.upper()

    similar_groups = []

    for marca in df['Marca'].unique():
        sub_df = df[df['Marca'] == marca]


        for i, j in combinations(range(len(sub_df)), 2):
            row_i = sub_df.iloc[i]
            row_j = sub_df.iloc[j]

            if row_i['Sheet'] == row_j['Sheet']:
                continue

            name1 = row_i['Norm Name']
            name2 = row_j['Norm Name']
            sim = fuzz.token_sort_ratio(name1, name2)

            condition = row_i['SKU'] != row_j['SKU'] if different_sku else row_i['SKU'] == row_j['SKU']

            if sim >= similarity_threshold and condition:
                nums1 = extract_good_numbers(row_i['Nombre SKU'])

                nums2 = extract_good_numbers(row_j['Nombre SKU'])

                if nums1 and nums2 and ( nums1 != nums2):
                    continue

                similar_groups.append({
                    'Marca': marca,
                    'Nombre SKU 1': row_i['Nombre SKU'],
                    'SKU 1': row_i['SKU'],
                    'Sheet 1': row_i['Sheet'],
                    'Nombre SKU 2': row_j['Nombre SKU'],
                    'SKU 2': row_j['SKU'],
                    'Sheet 2': row_j['Sheet'],
                    'Similarity': sim,
                    'Numbers 1': nums1,
                    'Numbers 2': nums2
                })

    return pd.DataFrame(similar_groups).sort_values(by="Similarity", ascending=False).reset_index(drop=True)

def is_different_flavor(name1: str, name2: str, min_len: int = 4, max_sim: float = 0.6) -> bool:
    FLAVOR_EXCEPTIONS = {"ajo", "té", "sal", "pic", "lim", "ají"}
    def clean_and_split(text):
        # Replace common special symbols with letter approximations
        replacements = {
            "¥": "n", # like in word pina, which was written incorrectly with that symbol
            "$": "s",
            "€": "e",
        }
        for symbol, replacement in replacements.items():
            text = text.replace(symbol, replacement)
        words = re.findall(r'\b[\wÀ-ÿ]+\b', text.lower())

        long_words = {w for w in words if len(w) >= min_len and not w.isdigit()}
        short_words = {w for w in words if 0 < len(w) < min_len and not w.isdigit()}
        return long_words, short_words

    def fuzzy_set_difference(set1, set2):
        unique = []
        for w1 in set1:
            found_similar = False
            for w2 in set2:
                max_allowed_edits = 1 if len(w1) <= 6 else 2
                if levenshtein_distance(w1, w2) <= max_allowed_edits:
                    found_similar = True
                    break
            if not found_similar:
                unique.append(w1)
        return unique

    tokens1, short1 = clean_and_split(name1)
    tokens2, short2 = clean_and_split(name2)
    # Add short flavor exceptions to the long token sets
    tokens1 |= {w for w in short1 if w.lower() in FLAVOR_EXCEPTIONS}
    tokens2 |= {w for w in short2 if w.lower() in FLAVOR_EXCEPTIONS}

    unique1 = fuzzy_set_difference(tokens1, tokens2)
    unique2 = fuzzy_set_difference(tokens2, tokens1)

    # Remove short tokens from unique lists unless they are the only token
    if len(unique1) == 1 and list(unique1)[0] in short1 and list(unique1)[0] not in FLAVOR_EXCEPTIONS:
        unique1 = []
    if len(unique2) == 1 and list(unique2)[0] in short2 and list(unique2)[0] not in FLAVOR_EXCEPTIONS:
        unique2 = []

    if len(unique1) == 1 and len(unique2) == 1:
        tok1 = unique1[0]
        tok2 = unique2[0]
        sim = SequenceMatcher(None, tok1, tok2).ratio()
        return sim < max_sim  # Very different, likely different flavors

    return False

def remove_flavor_variants(df: pd.DataFrame) -> pd.DataFrame:
    mask = df.apply(
        lambda row: is_different_flavor(row["Nombre SKU 1"], row["Nombre SKU 2"]),
        axis=1
    )
    return df[~mask].reset_index(drop=True)


def is_sku_too_close(row):
    try:
        return abs(int(row['SKU 1']) - int(row['SKU 2'])) <= 3
    except:
        return False


def process_excel_for_duplicates(
    excel_path,
    confidence_threshold=93,
    low_confidence_threshold=90
):
    df_all = load_all_sheets(excel_path)
    similar_df = find_similar_products(df_all, similarity_threshold=low_confidence_threshold)

    if similar_df.empty:
        return pd.DataFrame(), pd.DataFrame()
    similar_df = similar_df.copy()
    similar_df = remove_flavor_variants(similar_df)

    filtered_df = similar_df[~similar_df.apply(is_sku_too_close, axis=1)]

    confident_df = filtered_df[filtered_df['Similarity'] >= confidence_threshold]
    needs_review_df = pd.concat([
        filtered_df[
            (filtered_df['Similarity'] >= low_confidence_threshold) &
            (filtered_df['Similarity'] < confidence_threshold)
        ],
    ], ignore_index=True)

    confident_df = confident_df.sort_values(by='Similarity', ascending=False).reset_index(drop=True)
    needs_review_df = needs_review_df.sort_values(by='Similarity', ascending=False).reset_index(drop=True)

    return confident_df, needs_review_df

