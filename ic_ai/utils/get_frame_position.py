import pandas as pd
from collections import defaultdict
from itertools import groupby
from collections import Counter
import ast
def safe_literal_eval(x):
    try:
        if isinstance(x, str) and x.strip().startswith("["):
            return ast.literal_eval(x)
        elif isinstance(x, list):
            return x
        else:
            return []
    except Exception:
        return []
def prefix(t): return t.split("-")[0]
def infix(t): return t.split("-")[1]
def postfix(t): return t.split("-")[2]

def edit_prefix(df):
    def fix_nan(df):
        df.loc[(df['label'] == 'code') & 
               ((df['ocr'].isna()) | (df['ocr'] == 'set()') | (df['ocr'] == 'nan') | (df['ocr'] == '[]') | (df['ocr'] == '')  ), 
               'label'] = 'codebackground'
        return df

    def find_most_common(df):
        ocr_series = df.loc[df['label'] == 'code', 'ocr'].dropna()
        most_common_prefix = Counter(ocr_series.map(prefix)).most_common(1)[0][0]
        return most_common_prefix

    def replace_prefixes(ocr_text, common_prefix):
        suffix = '-'.join(ocr_text.split('-')[1:])
        return f"{common_prefix}-{suffix}"

    def find_max_occurence(start, end, code_lst):
        def normalized(item):
            s = str(item)
            if s == 'nan' or postfix(s) == '0':
                return None
            return s[:-1] + '2' if postfix(s) == '1' else s

        if end - start > 32:
            codes = [normalized(code_lst[i]) for i in range(start, end)]

            # Find longest consecutive nan gap
            gs = ge = gl = 0
            i = 0
            while i < len(codes):
                if codes[i] is None:
                    j = i + 1
                    while j < len(codes) and codes[j] is None:
                        j += 1
                    if j - i > gl:
                        gl, gs, ge = j - i, i, j
                    i = j
                else:
                    i += 1

            if gl > 10 and gs > 0 and ge < len(codes):
                left_codes = [c for c in codes[:gs] if c is not None]
                right_codes = [c for c in codes[ge:] if c is not None]
                if left_codes and right_codes:
                    first_code = Counter(left_codes).most_common(1)[0][0]
                    last_code = Counter(right_codes).most_common(1)[0][0]
                    code_lst[start:start + gs] = [first_code] * gs
                    code_lst[start + gs:start + ge] = ['nan'] * gl
                    code_lst[start + ge:end] = [last_code] * (end - start - ge)
                    return first_code, code_lst

        tmp_dict = defaultdict(int)
        for data in code_lst[start:end]:
            tmp_dict[normalized(data) or 'nan'] += 1

        if len(tmp_dict) > 1:
            tmp_dict.pop('nan', None)
        key_max = max(tmp_dict, key=tmp_dict.get)
        code_lst[start:end] = [key_max] * (end - start)
        return key_max, code_lst
    
    result=[]
    idx = 0
    label_lst = df['label'].to_list()
    code_lst = df['ocr'].to_list()
    for key, group in groupby(label_lst):
        x = len(list(group))
        idx+=x
        if key != "code": continue
        ret, code_lst = find_max_occurence(idx-x, idx, code_lst)
        result.append([key, idx-x, idx, ret])
    df['ocr'] = code_lst
    df = fix_nan(df)
    mask = (df['label'] == 'code') & (df['ocr'].notna())
    most_common_prefix = find_most_common(df)
    df.loc[mask, 'ocr'] = df.loc[mask, 'ocr'].apply(lambda x: replace_prefixes(x, most_common_prefix))
    # df.to_csv("test1.csv", index=False)
    # exit()
    return df


def group_code(df):
    label_lst = df['label'].to_list()
    ocr_lst = df['ocr'].to_list()
    processed_ocr = []
    idx = 0
    for key, group in groupby(label_lst):
        v = len(list(group))
        idx += v
        if key != "code": continue
        ocr = ocr_lst[idx - v]
        if not ocr: continue
        processed_ocr.append(['code', idx - v, idx, ocr])
    return processed_ocr

def get_cols(processed_ocr, fps=30):
    if not processed_ocr:
        return (), (), []

    cols = []
    cur = [processed_ocr[0]]
    for i in range(1, len(processed_ocr)):
        prev, curr = processed_ocr[i - 1], processed_ocr[i]
        if infix(prev[-1]) != infix(curr[-1]):
            cols.append(cur)
            cur = [curr]
        else:
            cur.append(curr)
    cols.append(cur)

    if len(cols) > 1 and len(cols[0]) == 1:
        cols[1] = cols[0] + cols[1]
        cols = cols[1:]

    def trim_col(col):
        postfixes = [postfix(e[-1]) for e in col]
        if len(postfixes) == len(set(postfixes)):
            return col
        return col[:postfixes.index(max(postfixes, key=int)) + 1]
    cols = [trim_col(c) for c in cols]
    sps = [len(c) for c in cols]

    for i in range(1, len(cols) - 1):
        if sps[i] != 1:
            continue
        curr_pf = postfix(cols[i][0][-1])
        prev_pf = postfix(cols[i - 1][-1][-1])
        next_pf = postfix(cols[i + 1][0][-1])
        if prev_pf == curr_pf == next_pf:
            continue
        if (prev_pf == '3' and curr_pf == '2') or (prev_pf == '6' and curr_pf == '7'):
            cols[i - 1] = cols[i - 1] + cols[i]
            sps[i - 1] += 1
        elif (next_pf == '3' and curr_pf == '2') or (next_pf == '6' and curr_pf == '7'):
            cols[i + 1] = cols[i] + cols[i + 1]
            sps[i + 1] += 1

    pairs = [(s, c) for s, c in zip(sps, cols) if s != 1]
    if not pairs:
        return (), (), []
    sps, cols = map(list, zip(*pairs))

    ups = []
    for i, col in enumerate(cols):
        ups.append(int(postfix(col[0][-1])) < 5 and int(postfix(col[-1][-1])) > 4)
        for j, e in enumerate(col):
            if e[2] - e[1] > 2*fps:
                if j == 0:
                    if i > 0 and postfix(cols[i - 1][-1][-1]) == "3":
                        cols[i - 1].append([e[0], e[1], e[1] + fps, e[-1]])
                    e[1] = e[2] - fps // 2
                elif j == len(col) - 1:
                    if i < len(cols) - 1 and postfix(cols[i + 1][0][-1]) == "3":
                        cols[i + 1].insert(0, [e[0], e[2] - fps, e[2], e[-1]])
                    e[2] = e[1] + fps // 2

    return sps, cols, ups

def correct_lst_texts(lst_texts):
    postfixes = [int(postfix(t)) for t in lst_texts]
    base = f"{prefix(lst_texts[0])}-{infix(lst_texts[0])}-1"
    if postfixes[0] == min(postfixes) or postfixes[-1] == max(postfixes):
        lst_texts.insert(0, base)
    else:
        lst_texts.append(base)
    return lst_texts

def get_substracts(sps, cols, ups, endframe=111111, fps=30):
    substracts = []

    for i in range(len(sps)):
        updated_texts = correct_lst_texts([c[-1] for c in cols[i]])
        k = 1 if ups[i] else 2 
        first = cols[i][0][k]
        substract = (max(first - 3 * fps, 0), first)
        substracts.append((substract, updated_texts[0], ups[i]))

        for c in range(len(cols[i]) - 1):
            substract = (cols[i][c][k], cols[i][c + 1][k])
            substracts.append((substract, updated_texts[c + 1], ups[i]))

        last = cols[i][-1][k]
        substract = (last, min(last + 3 * fps, endframe))
        substracts.append((substract, updated_texts[-1], ups[i]))

    return substracts

def get_frames(substracts, df, fps=30, target_y=540):
    def get_y(val):
        c = safe_literal_eval(val)
        return c[1] if len(c) > 1 else None

    code_df = df[df['label'] == 'code'].copy()
    code_df['_y'] = code_df['ocr_center'].apply(get_y)
    code_df = code_df.dropna(subset=['_y'])
    center_map = dict(zip(code_df['frame_idx'].astype(int), code_df['_y']))

    def best_frame(anchor, window=32):
        candidates = [(fid, abs(y - target_y)) for fid, y in center_map.items()
                      if anchor - window <= fid <= anchor + window]
        return min(candidates, key=lambda x: x[1])[0] if candidates else anchor


    ret = []
    for (first_idx, last_idx), text, is_up in substracts:
        code_anchor = first_idx if is_up else last_idx
        top_anchor = last_idx if is_up else first_idx

        frame_positions = [
            (best_frame(code_anchor), "code"),
            (top_anchor + (-fps//2 if is_up else fps//2), "front"),
            (best_frame(top_anchor), "top"),
        ]

        if int(postfix(text)) == 1:
            ref = frame_positions[2][0]
            frame_positions[0] = (ref, "code")

        ret.append([frame_positions, text])

    return ret


def get_all_codes(df, fps=30, target_y=540):
    df = edit_prefix(df)
    processed_ocr = group_code(df)
    sps, cols, ups = get_cols(processed_ocr, fps=fps)
    substracts = get_substracts(sps, cols, ups, endframe=len(df), fps=fps)
    ret = get_frames(substracts, df, fps=fps, target_y=target_y)
    return ret

# csv_path = '/ssd1/thaokb/inventory-count-ai/test/outputs_SD2_421_DF1/DJI_20250920134142_0001_D_176050440825_result/output_csv_processed.csv'
# csv_path = '/ssd1/thaokb/inventory-count-ai/test/outputs_SD3_001_CE1/DJI_20250920132248_0001_D_176050386883_result/output_csv_processed.csv'
# csv_path = '/ssd1/thaokb/inventory-count-ai/test/outputs_SD4_005_BB1/DJI_20250920113825_0005_D_176050345727_result/output_csv_processed.csv'
# csv_path = '/ssd1/thaokb/inventory-count-ai/test/outputs_SD2_521_AH1/DJI_20250920125352_0001_D_176050323234_result/output_csv_processed.csv'
# csv_path = '/ssd1/thaokb/inventory-count-ai/test/outputs_SD4_441_DF2/DJI_20250920134144_0001_D_176051333802_result/output_csv_processed.csv'
# csv_path = '/ssd1/thaokb/inventory-count-ai/test/outputs_SDC_001_CE2/DJI_20250920132245_0001_D_176051104349_result/output_csv_processed.csv'
# csv_path = '/ssd1/thaokb/inventory-count-ai/test/outputs_SD2_006_BB2/DJI_20250920113828_0006_D_176051412895_result/output_csv_processed.csv'
# csv_path = '/ssd1/thaokb/inventory-count-ai/test/outputs_SD4_541_AH2/DJI_20250920125354_0001_D_176051298918_result/output_csv_processed.csv'

# csv_path = "/ssd1/thaokb/inventory-count-ai/test/outputs_2510_SD2_BD21/DJI_20251025105412_0001_D_176155466730_result/output_csv_processed.csv"
# csv_path = "/ssd1/thaokb/inventory-count-ai/test/outputs_2510_SD4_BD11/DJI_20251025111046_0001_D_176155531394_result/output_csv_processed.csv"
# csv_path = "/ssd1/thaokb/inventory-count-ai/test/outputs_2510_SDC_BD22/DJI_20251025105306_0001_D_176155563343_result/output_csv_processed.csv"
# csv_path = "/ssd1/thaokb/inventory-count-ai/test/outputs_2510_SD3_BD12/DJI_20251025111142_0001_D_176155502069_result/output_csv_processed.csv"


if __name__ == "__main__":
    # csv_path = "/ssd1/thaokb/inventory-count-ai/outputs_2510_SD3_evenAD1/DJI_20251025135403_0001_D_176179853734_result/output_csv_processed.csv"
    csv_path = "/ssd1/tindd/inventory-count-ai/outputs/DJI_20251025105412_0001_D-1_177887010162_result/output_csv_processed.csv"

    df = pd.read_csv(csv_path)
    df = edit_prefix(df)
    ret = get_all_codes(df)
    # for r in ret:
    #     print(r, r[0][0][0]-r[0][2][0])
