import pandas as pd
import ast
import re
import numpy as np

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
    
def process_csv_raw(df, output_csv, score_threshold=0.95, img_width=None):
    pattern = re.compile(r"([A-Z]{2})-(\d{3})-(\d)")
    df = df.replace("", np.nan)

    mid_x = img_width / 2 if img_width else None

    df_code = df[df['label'] == 'code'].copy()
    df_code['ocr'] = df_code['ocr'].apply(safe_literal_eval)
    df_code['score'] = df_code['score'].apply(
        lambda x: [float(s) for s in safe_literal_eval(x)]
    )
    df_code['ocr_center'] = df_code['ocr_center'].apply(safe_literal_eval)
    def process_row(row):
        ocr_list = row['ocr']
        score_list = row['score']
        center_list = row['ocr_center']
        if not isinstance(ocr_list, list):
            ocr_list = [ocr_list]
        if not isinstance(score_list, list):
            score_list = [score_list]
        if not isinstance(center_list, list):
            center_list = [center_list]
        cands = []
        for o, s, c in zip(ocr_list, score_list, center_list):
            m = pattern.search(str(o))
            if m:
                cands.append((m.group(0), s, c))
        if not cands:
            return "", "", None
        if mid_x is not None:
            def dist(cand):
                c = cand[2]
                if isinstance(c, (list, tuple)) and len(c) >= 1:
                    return abs(c[0] - mid_x)
                return float('inf')
            best_ocr, best_score, best_center = min(cands, key=dist)
        else:
            best_ocr, best_score, best_center = max(cands, key=lambda x: x[1])
        if best_score >= score_threshold:
            return str(best_ocr), str(best_score), str(best_center)
        return "", "", None

    result = df_code.apply(process_row, axis=1)
    df_code['ocr'] = [r[0] for r in result]
    df_code['score'] = [r[1] for r in result]
    df_code['ocr_center'] = [r[2] for r in result]
    df.update(df_code)
    df.loc[df_code.index, 'ocr_center'] = df_code['ocr_center'].values
    df['ocr'] = df['ocr'].apply(lambda x: x if isinstance(x, str) and x.strip() != "" else np.nan)
    df['score'] = pd.to_numeric(df['score'], errors="coerce")
    df.to_csv(output_csv, index=False)
    print('Hoàn thành xử lý csv gốc! Kết quả lưu tại', output_csv)
    return df

if __name__ == "__main__":
    csv_path = "/ssd1/thaokb/inventory/output.csv"
    df = pd.read_csv(csv_path)
    process_csv_raw(df, "/ssd1/thaokb/inventory/ocr_results.csv", score_threshold=0)




