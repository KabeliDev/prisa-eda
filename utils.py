import pandas as pd
import re
from fuzzywuzzy import fuzz
from itertools import combinations
from difflib import SequenceMatcher


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
    """Extracts standalone numbers and dot-suffix numbers (e.g., GDO.1), excluding anything in parentheses."""
    text_clean = re.sub(r'\([^)]*\)', '', text) # remove number inside parenthesis
    # fractions

    fractions = re.findall(r'\b(\d+)\s*/\s*(\d+)\b', text_clean)
    fraction_values = [int(n) / int(d) for n, d in fractions if int(d) != 0]
    text_clean = re.sub(r'\b\d+\s*/\s*\d+\b', '', text_clean)  # remove fractions from text

    # standalone numbers
    standalone_numbers = re.findall(r'\b\d+\b', text_clean)
    after_letter = re.findall(r'(?<=[a-zA-Z])\d+', text_clean)

    all_numbers = list(map(float, standalone_numbers  + after_letter)) + fraction_values

    return all_numbers


def find_similar_products(df, similarity_threshold=90):
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

            if sim >= similarity_threshold and row_i['SKU'] != row_j['SKU']:
                nums1 = extract_good_numbers(row_i['Nombre SKU'])

                nums2 = extract_good_numbers(row_j['Nombre SKU'])

                if nums1 and nums2 and (
                        (len(nums1) == len(nums2) and nums1 != nums2)
                ):
                    continue
                if nums1 and nums2 and not set(nums1) & set(nums2):
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
    def clean_and_split(text):
        return set([
            word.lower()
            for word in re.findall(r'\b\w+\b', text)
            if len(word) >= min_len and not word.isdigit()
        ])

    tokens1 = clean_and_split(name1)
    tokens2 = clean_and_split(name2)

    # Unique tokens in each name
    unique1 = tokens1 - tokens2
    unique2 = tokens2 - tokens1

    # Check if there's exactly one unique token on each side
    if len(unique1) == 1 and len(unique2) == 1:
        tok1 = next(iter(unique1))
        tok2 = next(iter(unique2))
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

    # too_close_df = similar_df[similar_df.apply(is_sku_too_close, axis=1)]
    filtered_df = similar_df[~similar_df.apply(is_sku_too_close, axis=1)]

    confident_df = filtered_df[filtered_df['Similarity'] >= confidence_threshold]
    needs_review_df = pd.concat([
        filtered_df[
            (filtered_df['Similarity'] >= low_confidence_threshold) &
            (filtered_df['Similarity'] < confidence_threshold)
        ],
        # too_close_df
    ], ignore_index=True)

    confident_df = confident_df.sort_values(by='Similarity', ascending=False).reset_index(drop=True)
    needs_review_df = needs_review_df.sort_values(by='Similarity', ascending=False).reset_index(drop=True)

    return confident_df, needs_review_df

