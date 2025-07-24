import pandas as pd
import re
from fuzzywuzzy import fuzz
from difflib import SequenceMatcher
from Levenshtein import distance as levenshtein_distance
from collections import defaultdict
import networkx as nx
from itertools import combinations


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

    all_numbers = list(
        map(float, standalone_numbers + after_letter + embedded_numbers)) + fraction_values + decimal_values
    return all_numbers


def find_internal_duplicates(df):
    """
    Finds products from the same subempresa with the same SKU and Nombre SKU.
    """
    duplicates = (
        df.groupby(['Sheet', 'SKU', 'Nombre SKU'])
        .filter(lambda x: len(x) > 1)
        .sort_values(['Sheet', 'SKU'])
    )
    return duplicates.reset_index(drop=True)


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

                if nums1 and nums2 and (nums1 != nums2):
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
            "¥": "n",  # like in word pina, which was written incorrectly with that symbol
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


def process_excel_for_duplicates_and_split_by_company(
        excel_path,
        confidence_threshold=93,
        low_confidence_threshold=88
):
    """Group by subcompany"""
    full_data = load_all_sheets(excel_path)
    confident, needs_review = process_excel_for_duplicates(
        excel_path,
        confidence_threshold=confidence_threshold,
        low_confidence_threshold=low_confidence_threshold
    )
    all_companies = pd.unique(
        pd.concat([confident["Sheet 1"], confident["Sheet 2"]], ignore_index=True)
    )

    grouped_confident = {}
    grouped_review = {}

    for company in all_companies:
        confident_rows = confident[
            (confident["Sheet 1"] == company) | (confident["Sheet 2"] == company)
            ]
        review_rows = needs_review[
            (needs_review["Sheet 1"] == company) | (needs_review["Sheet 2"] == company)
            ]

        grouped_confident[company] = confident_rows
        grouped_review[company] = review_rows

    return grouped_confident, grouped_review


def split_matches_by_company(exact_df, partial_df):
    """Group by subcompany"""
    all_companies = pd.unique(
        pd.concat([exact_df["Sheet 1"], exact_df["Sheet 2"],
                   partial_df["Sheet 1"], partial_df["Sheet 2"]], ignore_index=True)
    )

    grouped_exact = {}
    grouped_partial = {}

    for company in all_companies:
        grouped_exact[company] = exact_df[
            (exact_df["Sheet 1"] == company) | (exact_df["Sheet 2"] == company)
            ]
        grouped_partial[company] = partial_df[
            (partial_df["Sheet 1"] == company) | (partial_df["Sheet 2"] == company)
            ]

    return grouped_exact, grouped_partial


def subtract_table(df_all, confident):
    """find samples from df_all that are not present in other df confident"""
    confident_pairs_1 = list(zip(confident['Marca'], confident['Nombre SKU 1'], confident['SKU 1']))
    confident_pairs_2 = list(zip(confident['Marca'], confident['Nombre SKU 2'], confident['SKU 2']))

    confident_pairs_set = set(confident_pairs_1 + confident_pairs_2)
    filtered_df = df_all[
        ~df_all.apply(lambda row: (row['Marca'], row["Nombre SKU"], row['SKU']) in confident_pairs_set, axis=1)]
    return filtered_df


def find_normal_cases(excel_path):
    """Finds products that do not have similar by name, sku products in other companies as products that are nor belong to other categories"""
    data = load_all_sheets(excel_path)

    correct_products = find_similar_products(data, 88, different_sku=False)
    correct_products = correct_products.copy()
    correct_products = remove_flavor_variants(correct_products)
    columns_to_show = [col for col in correct_products.columns if col not in ['Numbers 1', 'Numbers 2']]
    correct_products = correct_products.loc[:, columns_to_show]
    exact_matches = correct_products[correct_products['Similarity'] == 100]
    partial_matches = correct_products[correct_products['Similarity'] < 100]
    confident, needs_review = process_excel_for_duplicates(
        excel_path,
        confidence_threshold=93,
        low_confidence_threshold=77
    )
    df_all = load_all_sheets(excel_path)
    print(df_all.shape)
    filtered = subtract_table(df_all, confident)
    print(filtered.shape)
    filtered = subtract_table(filtered, needs_review)
    filtered = subtract_table(filtered, exact_matches)
    filtered = subtract_table(filtered, partial_matches)
    return filtered


def pairs_to_unique_products(table):
    """Receives dict of dfs for each subcompany with pairs of products
    Returns dict of dfs for each subcompany with unique products
    """
    products_grouped_review = {}

    if isinstance(table, dict):
        for company, df in table.items():
            df1 = df[['Marca', 'Nombre SKU 1', 'SKU 1', 'Sheet 1']].copy()
            df1.columns = ['Marca', 'Nombre SKU', 'SKU', 'Sheet']

            df2 = df[['Marca', 'Nombre SKU 2', 'SKU 2', 'Sheet 2']].copy()
            df2.columns = ['Marca', 'Nombre SKU', 'SKU', 'Sheet']

            combined = pd.concat([df1, df2], ignore_index=True)
            filtered = combined[combined['Sheet'] == company].reset_index(drop=True)
            filtered = filtered.drop_duplicates(subset=['Marca', 'Nombre SKU', 'SKU', "Sheet"]).reset_index(drop=True)
            products_grouped_review[company] = filtered
    else:
        # if there is one table
        df = table

        df1 = df[['Marca', 'Nombre SKU 1', 'SKU 1', 'Sheet 1']].copy()
        df1.columns = ['Marca', 'Nombre SKU', 'SKU', 'Sheet']

        df2 = df[['Marca', 'Nombre SKU 2', 'SKU 2', 'Sheet 2']].copy()
        df2.columns = ['Marca', 'Nombre SKU', 'SKU', 'Sheet']

        combined = pd.concat([df1, df2], ignore_index=True)
        filtered = combined.reset_index(drop=True)
        filtered = filtered.drop_duplicates(subset=['Marca', 'Nombre SKU', 'SKU', "Sheet"]).reset_index(drop=True)
        return filtered

    return products_grouped_review


def count_unique_subempresas_per_product(df):
    """
    For each product (Nombre SKU, SKU), count how many unique subcompanies (sheets) it appears in
    Products that are matched (appear in same row) are considered part of the same group.
    Use graph to register connection between related products
    """

    G = nx.Graph()

    for _, row in df.iterrows():
        prod1 = (row['Nombre SKU 1'], row['SKU 1'])
        prod2 = (row['Nombre SKU 2'], row['SKU 2'])
        G.add_edge(prod1, prod2)

    product_groups = list(nx.connected_components(G))

    product_to_sheets = defaultdict(set)

    for _, row in df.iterrows():
        prod1 = (row['Nombre SKU 1'], row['SKU 1'])
        prod2 = (row['Nombre SKU 2'], row['SKU 2'])

        product_to_sheets[prod1].add(row['Sheet 1'])
        product_to_sheets[prod2].add(row['Sheet 2'])

    result = {}

    for group in product_groups:
        all_sheets = set()
        for product in group:
            all_sheets.update(product_to_sheets[product])

        for product in group:
            result[product] = len(all_sheets)

    return result


def count_product_distribution_dict_only(product_company_counts):
    """Create a dict
    product: how many matches it has in other subcompanies"""
    statistics = defaultdict(int)
    cnt = 0
    counted = False
    for (name, sku), count in product_company_counts.items():
        # print(f"Product: {name} | SKU: {sku} | Count: {count}")
        if counted and cnt > 0:
            cnt -= 1
        else:
            counted = True
            cnt = count - 1
            statistics[count] += 1

    return statistics


def count_unique_products_per_sheet(exact_match_df):
    all_products = []

    for i in range(len(exact_match_df)):
        row = exact_match_df.iloc[i]
        all_products.append((row['Sheet 1'], row['SKU 1'], row['Nombre SKU 1'], row["Marca"]))
        all_products.append((row['Sheet 2'], row['SKU 2'], row['Nombre SKU 2'], row["Marca"]))

    product_df = pd.DataFrame(all_products, columns=["Sheet", "SKU", "Nombre SKU", "Marca"])

    # Drop duplicates across all columns (Sheet + SKU + Nombre SKU + Marca)
    unique_df = product_df.drop_duplicates(subset=["Sheet", "SKU", "Nombre SKU", "Marca"])

    # Now count per Sheet
    counts = unique_df.groupby("Sheet").size().to_dict()

    return counts


def find_common_products(dfs, df_names=None):
    """
    Given a list of DataFrames with columns ['Sheet', 'SKU'],
    prints out which pairs share common products.
    """
    if df_names is None:
        df_names = [f"df_{i}" for i in range(len(dfs))]

    standardized_dfs = []
    for df in dfs:
        df_std = df.rename(columns={"Subempresa": "Sheet"})[["Sheet", "SKU", "Marca", "Nombre SKU"]].drop_duplicates()
        standardized_dfs.append(df_std)

    for (i, j) in combinations(range(len(standardized_dfs)), 2):
        df1, name1 = standardized_dfs[i], df_names[i]
        df2, name2 = standardized_dfs[j], df_names[j]

        merged = df1.merge(df2, on=["Sheet", "SKU", "Marca", "Nombre SKU"], how="inner")
        if not merged.empty:
            print(f"✅ Common products between {name1} and {name2}: {len(merged)}")
            return merged
        else:
            print(f"❌ No common products between {name1} and {name2}")