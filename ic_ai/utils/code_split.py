# import pandas as pd
# from collections import defaultdict
# from itertools import groupby
# import os
# from collections import Counter
# import subprocess
# import tempfile
# import shutil
 
 
# def edit_prefix(df):
#     def fix_nan(df):
#         df.loc[(df['label'] == 'code') &
#                ((df['ocr'].isna()) | (df['ocr'] == 'set()') | (df['ocr'] == 'nan') | (df['ocr'] == '[]') | (df['ocr'] == '')  ),
#                'label'] = 'codebackground'
#         return df
 
#     def find_most_common(df):
#         ocr_series = df.loc[df['label'] == 'code', 'ocr'].dropna()
#         split_ocr = sum(ocr_series.str.split(':'), [])
#         prefixes = [item.split('-')[0] for item in split_ocr]
#         prefix_counts = Counter(prefixes)
#         most_common_prefix = prefix_counts.most_common(1)[0][0]
#         return most_common_prefix
   
#     def replace_prefixes(ocr_text, common_prefix):
#         parts = ocr_text.split(':')
#         updated_parts = []
#         for part in parts:
#             suffix = '-'.join(part.split('-')[1:])  
#             updated_parts.append(f"{common_prefix}-{suffix}")
#         return ':'.join(updated_parts)
 
#     def find_max_occurence(start, end, code_lst):
#         tmp_dict = defaultdict(int)
#         for data in code_lst[start:end]:
#             items = str(data).split(":") if ":" in str(data) else [str(data)]
#             for item in items:
#                 if item == 'nan' or item.endswith('-0'):
#                     tmp_dict['nan'] += 1
#                     continue
#                 parts = item.split("-")
#                 tmp_dict[item if int(parts[2]) != 1 else f"{parts[0]}-{parts[1]}-2"] += 1
#         for k, v in list(tmp_dict.items()):
#             if v == 1 and k != 'nan':
#                 tmp_dict['nan'] += 1
#                 del tmp_dict[k]
               
#         if len(tmp_dict) > 1: tmp_dict.pop('nan', None)
       
#         max_count = max(tmp_dict.values())
#         if max_count == 1:
#             code_lst[start:end] = ['nan'] * (end - start)
#             return 'nan', code_lst
#         max_keys = [k for k, v in tmp_dict.items() if v == max_count]
       
#         key_max = max_keys[0]
#         # if max_count == 1: key_max = 'nan'
#         if len(tmp_dict) == 1 or len(max_keys) == 1:
#             window_start = max(0, start - 5)
#             window_end = min(len(code_lst), end + 5)
#             code_lst[window_start:window_end] = [key_max] * (window_end - window_start)
#             code_lst[start:end] = [key_max] * (end - start)
           
#         return key_max, code_lst
   
#     def fill_nan(lst, code_lst):
#         p, n = 0, 0
#         while n<len(lst)-1:
#             n += 1
#             if str(lst[n][-1]) == 'nan':
#                 # non_nan = [c for c in code_lst[max(0, lst[n][-3] - 50):lst[n][-3]] if str(c) != 'nan']
#                 # if non_nan:
#                 #     lst[n][-1] = non_nan[-1]
#                 #     p=n
#                 continue
#             if n-p==1:
#                 p=n
#                 continue
#             p_parts=lst[p][-1].split("-")
#             n_parts=lst[n][-1].split("-")
#             # print(p_parts, n_parts)
#             if int(p_parts[1]) != int(n_parts[1]) or abs(int(p_parts[2]) - int(n_parts[2])) == 1:
#                 p=n
#                 continue
#             r = range(int(p_parts[2])+1, int(n_parts[2])) if int(p_parts[2]) < int(n_parts[2]) else range(int(p_parts[2])-1, int(n_parts[2]), -1)
#             for i, v in enumerate(r):
#                 a = lst[p+1+i][-3]
#                 b = lst[p+1+i][-2]
#                 code_lst[a:b] = [f"{p_parts[0]}-{p_parts[1]}-{v}"] * (b - a)
#             p = n

#         return lst, code_lst
   
#     result=[]
#     idx = 0
#     label_lst = df['label'].to_list()
#     code_lst = df['ocr'].to_list()
#     for key, group in groupby(label_lst):
#         x = len(list(group))
#         idx+=x
#         if key != "code": continue
#         ret, code_lst = find_max_occurence(idx-x, idx, code_lst)
#         result.append([key, idx-x, idx, ret])
   
#     result, code_lst = fill_nan(result, code_lst)
#     # result, _ = fill_nan(result, code_lst)

#     df['ocr'] = code_lst
#     df = fix_nan(df)
#     mask = (df['label'] == 'code') & (df['ocr'].notna())
#     most_common_prefix = find_most_common(df)
#     df.loc[mask, 'ocr'] = df.loc[mask, 'ocr'].apply(lambda x: replace_prefixes(x, most_common_prefix))
#     return df
 
# def get_highest_ocr_score(lst_score, lst_ocr):
#     return lst_ocr[lst_score.index(max(lst_score))]
 
# def check_overlap(prev_lst, current_lst):
#     prev_parts = prev_lst[-1].split("-")
       
#     def remove_unused_codes(lst):
#         lst_output = []
#         data_lst = [[data.split("-")[1], data.split("-")[2]] for data in lst]
 
#         data_in = defaultdict(int)
#         data_post = defaultdict(int)
#         for item in data_lst:
#             data_in[item[0]] += 1
#             if int(item[1]) == 1: data_post["2"] += 1
#             else: data_post[item[1]] += 1
       
#         max_count_infix = max(data_in.values())
#         max_infixes = [k for k, v in data_in.items() if v == max_count_infix]
#         if len(max_infixes) == 1: infix = max_infixes[0]
#         else: infix = min(max_infixes, key=lambda k: abs(int(k) - int(prev_parts[1])))
#         postfix = max(data_post, key=data_post.get)
#         if infix != prev_parts[1] and int(postfix) < 5:
#             if int(prev_parts[2]) not in [1, 2]: lst_output.append(f'{prev_parts[0]}-{prev_parts[1]}-0')
#             if int(postfix) not in [1, 2]: lst_output.append(f'{prev_parts[0]}-{infix}-0')
 
#         if int(postfix) == 2: lst_output.append(f'{prev_parts[0]}-{infix}-1')
#         lst_output.append(f'{prev_parts[0]}-{infix}-{postfix}')
#         return lst_output
 
#     current_lst = remove_unused_codes(current_lst)
#     flag = len(current_lst+prev_lst)-len(set(current_lst+prev_lst)) == 0
#     return flag, current_lst
 
# def correct_lst(lst):
#     re_score = 0
#     score = 0
#     for i in range(1,len(lst)):
#         if lst[i] > lst[i-1]: score+=1
#         if lst[i] < lst[i-1]: re_score+=1
#     return sorted(lst, reverse=(re_score > score))
 
# def get_prefix(data):
#     grouped = defaultdict(list)
#     for code in data:
#         parts = code.split('-')
#         prefix = f'{parts[0]}-{parts[1]}-'
#         suffix = int(parts[2])
#         grouped[prefix].append(suffix)
#     result = [[prefix, correct_lst(suffixes)] for prefix, suffixes in grouped.items() if len(suffixes) > 1]
#     for res in result:
#         if min(res[1]) == 0: continue
#         range_list = list(range(min(res[1]), max(res[1]) + 1))
#         for r in range_list:
#             if r not in res[1]: print("Missing", f"{res[0]}{r}")
#     flattened = [f"{prefix}{num}" for prefix, nums in result for num in nums]
   
#     return flattened
       
# def group_code(df):
#     label_lst = df['label'].to_list()
#     ocr_lst = df['ocr'].to_list()
#     score_lst = df['score'].to_list()
#     result = []
#     for key, group in groupby(label_lst): result.append((key, len(list(group))))
#     processed_ocr = []
#     idx = 0
#     for k, v in result:
#         idx += v
#         if k != "code": continue
#         ocr_data = ocr_lst[idx-v:idx]
#         score_data = score_lst[idx-v:idx]
#         ocr_texts = get_highest_ocr_score(score_data, ocr_data).split(":")
#         if len(ocr_texts) == 0: continue
       
#         if len(processed_ocr) == 0:
#             ocr_texts = sorted(ocr_texts, key=lambda x: int(x.split("-")[-1]))
#             processed_ocr.append(['code', idx-v, idx, ocr_texts])
#             continue
#         checker, texts = check_overlap(processed_ocr[-1][-1], ocr_texts)
#         texts = sorted(texts, key=lambda x: int(x.split("-")[-1]), reverse = (int(processed_ocr[-1][-1][0].split("-")[2]) == 3) )
#         if checker: processed_ocr.append(['code', idx-v, idx, texts])
#         else:
#             processed_ocr[-1][0] = 'code2'
#             processed_ocr[-1][-1] = texts
#             processed_ocr[-1][-2] = idx
#     return processed_ocr
 
# def get_corresponding_frame(processed_ocr, endframe=10000):
#     lst_texts = []
#     video_saving = [0]
#     selected_frames = []
#     for i, data in enumerate(processed_ocr):
#         lst_texts.extend(data[-1])
#         if i != 0 and data[-1][0].split("-")[1] != processed_ocr[i-1][-1][0].split("-")[1]:
#             if int(processed_ocr[i-1][-1][0].split("-")[2])==0:
#                 tmp=video_saving.pop(-1)
#                 video_saving.append((video_saving[-1] + tmp)//2)
#                 video_saving.append(tmp)
#             else: video_saving.append((data[2] + video_saving[-1])//2)
#         video_saving.append(data[2])
#     if endframe - video_saving[-1] > 100: video_saving.append(video_saving[-1]+200)
#     if video_saving[1]-video_saving[0]>300: video_saving[0] = video_saving[1]-200
#     lst_texts = get_prefix(lst_texts)
   
#     if int(lst_texts[0].split("-")[2]) == 2: lst_texts.insert(0,f'{lst_texts[0].split("-")[0]}-{lst_texts[0].split("-")[1]}-1')
#     elif int(lst_texts[0].split("-")[2]) not in [1, 2]:
#         t0, t1=lst_texts[0], lst_texts[1]
#         if t0.split("-")[2] < t1.split("-")[2]: lst_texts.insert(0,f'{t0.split("-")[0]}-{t0.split("-")[1]}-0')
#         else:
#             processed_ocr.pop(0)
#             lst_texts.pop(0)
           
#     for i, endings in enumerate(video_saving):
#         if i == 0: continue
#         selected_frames.append([video_saving[i-1] + 2, (video_saving[i-1] + endings)//2, endings-2])
   
#     if len(selected_frames) - len(lst_texts) == 1: lst_texts.append(f"{lst_texts[-1].split('-')[0]}-{lst_texts[-1].split('-')[1]}-0")
#     return selected_frames, lst_texts
 
# def get_frames_v2(len_video, name_video):
#     # assert len(len_video) == len(name_video), "len_video và name_video phải cùng độ dài."
   
#     ret = []
#     flag = name_video[0].split("-")[2] < name_video[1].split("-")[2]
#     for i, (frame_idx, video_name) in enumerate(zip(len_video, name_video)):
#         if i!=0 and video_name.split("-")[1] != name_video[i-1].split("-")[1]: flag = not flag
#         first_idx = frame_idx[0]
#         middle_idx = frame_idx[1]
#         last_idx = frame_idx[2]
#         frame_positions = [
#             (first_idx-10 if flag and first_idx-10 > 0 else last_idx, "code"),
#             (middle_idx+10 if flag else middle_idx-30, "front"),
#             (last_idx-10 if flag else first_idx, "top")
#         ]
#         length = abs(frame_positions[2][0] - frame_positions[0][0])
#         if length > 300 and int(video_name.split("-")[2]) >= 5:
#             length*=0.4
#             frame_positions[1] = (frame_positions[0][0] - int(0.5*length)-50 if frame_positions[2][0] < frame_positions[0][0] else frame_positions[0][0] + int(0.5*length), "front")
#             frame_positions[2] = (frame_positions[0][0] - int(length)-90 if frame_positions[2][0] < frame_positions[0][0] else frame_positions[0][0] + int(length), "top")
#         ret.append([sorted(frame_positions, key=lambda x: x[0]), video_name])
#         # print(f"Completed {video_name}: 3 frames saved to {video_folder}")
       
#     return ret
 
# def get_frames(len_video, name_video, fps=30):
#     # assert len(len_video) == len(name_video), "len_video và name_video phải cùng độ dài."
    
#     ret = []
#     flag = name_video[0].split("-")[2] < name_video[1].split("-")[2]
#     for i, (frame_idx, video_name) in enumerate(zip(len_video, name_video)):
#         if i!=0 and video_name.split("-")[1] != name_video[i-1].split("-")[1]: flag = not flag
#         first_idx = frame_idx[0]
#         middle_idx = frame_idx[1]
#         last_idx = frame_idx[2]
#         frame_positions = [
#             ((first_idx-fps//5 if first_idx-fps//5>0 else first_idx) if flag else last_idx, "code"),
#             (middle_idx+fps//5 if flag else middle_idx-fps//2, "front"),
#             ((last_idx-fps//5 if last_idx-fps//5>0 else last_idx) if flag else first_idx, "top")
#         ]
#         length = abs(frame_positions[2][0] - frame_positions[0][0])
#         if length > 6*fps and int(video_name.split("-")[2]) >= 5:
#             length*=0.5
#             frame_positions[1] = (frame_positions[0][0] - int(0.5*length)-fps if frame_positions[2][0] < frame_positions[0][0] else frame_positions[0][0] + int(0.5*length), "front")
#             frame_positions[2] = (frame_positions[0][0] - int(length)-2*fps if frame_positions[2][0] < frame_positions[0][0] else frame_positions[0][0] + int(length), "top")
#         # frame_positions = sorted(frame_positions, key=lambda x: x[0])
#         ret.append([frame_positions, video_name])
#         # print(f"Completed {video_name}: 3 frames saved to {video_folder}")
        
#     return ret

# def copy_frames(ret, img_folder="0019", output_dir="odd00199"):
#     os.makedirs(output_dir, exist_ok=True)
#     for frame_info in ret:
#         frame_positions, subfolder_name = frame_info
#         subfolder_path = os.path.join(output_dir, subfolder_name)
#         os.makedirs(subfolder_path, exist_ok=True)
#         for frame, label in frame_positions:
#             src_img = os.path.join(img_folder, f"frame_{frame:08d}.jpg")
#             dst_img = os.path.join(subfolder_path, f"{subfolder_name}_{label}.jpg")
#             if os.path.exists(src_img):
#                 shutil.copy(src_img, dst_img)
#                 print(f"Copied {src_img} to {dst_img}")
#             else:
#                 print(f"Warning: {src_img} does not exist.")
 
# def get_all_codes(df):
#     df=edit_prefix(df)
#     processed_ocr = group_code(df.copy())
#     print(processed_ocr)
#     len_video, name_video = get_corresponding_frame(processed_ocr, endframe=len(df))
#     ret = get_frames(len_video, name_video)
#     # copy_frames(ret)
#     return ret
 
 
 
# csv_path = '/ssd1/thaokb/inventory-count-ai/outputs_SD2_001/DJI_20250920125352_0001_D_175921934674_result/output_csv_processed.csv'
# # csv_path = '/hdd1/tindd/tindd/video_cutting/test_updated_ocr_fixed_1.csv'
# # csv_path = '/hdd1/tindd/tindd/video_cutting/test_updated_ocr_fixed_.csv'
# # csv_path = '/hdd1/tindd/tindd/video_cutting/test_updated_ocr_fixed_0.8_batch_PP-OCRv4.csv'
# # csv_path = '/hdd1/tindd/tindd/video_cutting/test_updated_ocr_fixed_0.8_batch.csv'
 
# # csv_path = '/hdd1/tindd/tindd/video_cutting/DJI_20250704145548_0018_D.csv'
# # csv_path = '/hdd1/tindd/tindd/video_cutting/DJI_20250704145548_0019_D_filtered_1.csv'
# # csv_path = '/ssd1/thaokb/inventory/output-refactor-result.csv'
# # csv_path ='/ssd1/thaokb/inventory/BE-110-top_neww.csv'
# # csv_path = '/ssd1/thaokb/test_updated_ocr_fixed_1.csv'
 
# # csv_path = '/ssd1/thaokb/DJI_20250704145548_0018_D.csv'
# # csv_path = '/ssd1/thaokb/DJI_20250704145548_0019_D_filtered_1.csv'
# # csv_path = '/ssd1/thaokb/inventory-count-ai/outputs_test/part_0060_175801394111_result/output_csv_processed.csv'
 
# df = pd.read_csv(csv_path)
# ret = get_all_codes(df)
 
# # prev_infix = None
# # for r in ret:
# #     infix = r[1].split("-")[1]
# #     if prev_infix is not None and infix != prev_infix: print()  
# #     print(r[1], end=' ')
# #     prev_infix = infix
# # print()  # đảm bảo xuống dòng cuối cùng
# # print(len(ret))
 
# # for r in ret:
# #     print(r, r[0][2][0]-r[0][0][0])
 
 
# # o_l=df["label"].to_list()  
# # for r in ret:
# #     print(r, r[0][2][0]-r[0][0][0])
# # print(len(ret))
# # for (((a1,a2),(b1,b2),(c1,c2)),d) in ret:
# #     a = min(a1,c1)
# #     c = max(a1,c1)
# #     num_carton = len([o_l[i] for i in range(a,c+1) if o_l[i] == "carton"])
# #     print(d, num_carton*100/(c-a+1))



import pandas as pd
from collections import defaultdict
from itertools import groupby
import os
from collections import Counter
import subprocess
import tempfile
import shutil


def edit_prefix(df):
    def fix_nan(df):
        df.loc[(df['label'] == 'code') & 
               ((df['ocr'].isna()) | (df['ocr'] == 'set()') | (df['ocr'] == 'nan') | (df['ocr'] == '[]') | (df['ocr'] == '')  ), 
               'label'] = 'codebackground'
        return df

    def find_most_common(df):
        ocr_series = df.loc[df['label'] == 'code', 'ocr'].dropna()
        split_ocr = sum(ocr_series.str.split(':'), [])
        prefixes = [item.split('-')[0] for item in split_ocr]
        prefix_counts = Counter(prefixes)
        most_common_prefix = prefix_counts.most_common(1)[0][0]
        return most_common_prefix
    
    def replace_prefixes(ocr_text, common_prefix):
        parts = ocr_text.split(':')
        updated_parts = []
        for part in parts:
            suffix = '-'.join(part.split('-')[1:])  
            updated_parts.append(f"{common_prefix}-{suffix}")
        return ':'.join(updated_parts)

    def find_max_occurence(start, end, code_lst):
        tmp_dict = defaultdict(int)
        for data in code_lst[start-10 if start-10>0 else 0:end+10 if end+10<len(code_lst) else len(code_lst)]:
            items = str(data).split(":") if ":" in str(data) else [str(data)]
            for item in items:
                if item == 'nan' or item.endswith('-0'):
                    tmp_dict['nan'] += 1
                    continue
                parts = item.split("-")
                tmp_dict[item if int(parts[2]) != 1 else f"{parts[0]}-{parts[1]}-2"] += 1
        # for k, v in list(tmp_dict.items()):
        #     if v == 1 and k != 'nan':
        #         tmp_dict['nan'] += 1
        #         del tmp_dict[k]
                
        if len(tmp_dict) > 1: tmp_dict.pop('nan', None)
        max_count = max(tmp_dict.values())

        max_keys = [k for k, v in tmp_dict.items() if v == max_count]
        key_max = max_keys[0]
        
        # if max_count == 1: 
        #     print(tmp_dict)
        #     non_nan = [c for c in code_lst[start-20:end+20] if str(c) != 'nan']
        #     if non_nan:
        #         non_nan_counts = Counter(non_nan)
        #         most_common_non_nan = non_nan_counts.most_common(1)[0][0]
        #         key_max = most_common_non_nan
        #     print(start, end)
        #     print(non_nan)
        #     if non_nan and key_max not in non_nan: key_max = non_nan[0]
        # if max_count == 1: key_max = 'nan'
        if len(tmp_dict) == 1 or len(max_keys) == 1:
            window_start = max(0, start - 10)
            window_end = min(len(code_lst), end + 10)
            code_lst[window_start:window_end] = [key_max] * (window_end - window_start)
            code_lst[start:end] = [key_max] * (end - start)
            
        return key_max, code_lst
    
    def fill_nan(lst, code_lst):
        p, n = 0, 0
        while n<len(lst)-1:
            n += 1
            if str(lst[n][-1]) == 'nan':
                # non_nan = [c for c in code_lst[max(0, lst[n][-3] - 50):lst[n][-3]] if str(c) != 'nan']
                # if non_nan: 
                #     lst[n][-1] = non_nan[-1]
                #     p=n
                continue
            if n-p==1: 
                p=n
                continue
            p_parts=lst[p][-1].split("-")
            n_parts=lst[n][-1].split("-")
            # print(p_parts, n_parts)
            if int(p_parts[1]) != int(n_parts[1]) or abs(int(p_parts[2]) - int(n_parts[2])) == 1: 
                p=n
                continue
            r = range(int(p_parts[2])+1, int(n_parts[2])) if int(p_parts[2]) < int(n_parts[2]) else range(int(p_parts[2])-1, int(n_parts[2]), -1)
            for i, v in enumerate(r):
                a = lst[p+1+i][-3]
                b = lst[p+1+i][-2]
                code_lst[a:b] = [f"{p_parts[0]}-{p_parts[1]}-{v}"] * (b - a)
            p = n

        return lst, code_lst
    
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
    result, code_lst = fill_nan(result, code_lst)
    df['ocr'] = code_lst
    df = fix_nan(df)
    mask = (df['label'] == 'code') & (df['ocr'].notna())
    most_common_prefix = find_most_common(df)
    df.loc[mask, 'ocr'] = df.loc[mask, 'ocr'].apply(lambda x: replace_prefixes(x, most_common_prefix))
    df.to_csv("test1.csv")
    return df

def get_highest_ocr_score(lst_score, lst_ocr):
    return lst_ocr[lst_score.index(max(lst_score))]

def check_overlap(prev_lst, current_lst):
    prev_parts = prev_lst[-1].split("-")
        
    def remove_unused_codes(lst):
        if all(e in prev_lst for e in lst): 
            # print("!!", prev_lst, lst)
            return prev_lst
        
        lst_output = []
        data_lst = [[data.split("-")[1], data.split("-")[2]] for data in lst]

        data_in = defaultdict(int)
        data_post = defaultdict(int)
        for item in data_lst:
            data_in[item[0]] += 1
            if int(item[1]) == 1: data_post["2"] += 1
            else: data_post[item[1]] += 1
        
        max_count_infix = max(data_in.values())
        max_infixes = [k for k, v in data_in.items() if v == max_count_infix]
        if len(max_infixes) == 1: infix = max_infixes[0]
        else: infix = min(max_infixes, key=lambda k: abs(int(k) - int(prev_parts[1])))
        if abs(int(infix)-int(prev_parts[1]))>10: infix=prev_parts[1]
        postfix = max(data_post, key=data_post.get)
        if infix != prev_parts[1] and int(postfix) < 5:
            
            if int(prev_parts[2]) not in [1, 2]: 
                lst_output.append(f'{prev_parts[0]}-{prev_parts[1]}-0')
                # print("@@", prev_lst, lst_output, lst)
            if int(postfix) not in [1, 2]: 
                lst_output.append(f'{prev_parts[0]}-{infix}-0')
                # print("##", prev_lst, lst_output, lst)
            if len(lst)==1 and int(lst[0].split("-")[2])==3 and int(prev_lst[-1].split("-")[2])==2:
                # print("vc", lst, prev_lst)
                return lst
            if len(lst)==1 and int(lst[0].split("-")[2])==2 and int(prev_lst[-1].split("-")[2])==3:
                lst_output=[]
        lst_output.append(f'{prev_parts[0]}-{infix}-{postfix}')

        if int(postfix) == 2: 
            if int(prev_lst[-1].split("-")[2])==3: lst_output.append(f'{prev_parts[0]}-{infix}-1')
            else: lst_output.insert(0,f'{prev_parts[0]}-{infix}-1')
        # print("&&", prev_lst, lst_output)
        return lst_output

    current_lst = remove_unused_codes(current_lst)
    flag = len(current_lst+prev_lst)-len(set(current_lst+prev_lst)) == 0 
    return flag, current_lst

def correct_lst(lst):
    re_score = 0
    score = 0
    for i in range(1,len(lst)*2//3):
        if lst[i] > lst[i-1]: score+=1
        if lst[i] < lst[i-1]: re_score+=1
    if 0 not in lst and len(lst)!=max(lst): lst= range(1, max(lst)+1) #add rule
    return sorted(lst, reverse=(re_score > score))

def get_prefix(data):
    grouped = defaultdict(list)
    for code in data:
        parts = code.split('-')
        prefix = f'{parts[0]}-{parts[1]}-'
        suffix = int(parts[2])
        grouped[prefix].append(suffix)
    # group = [[k,v] for k,v in grouped.items()]
    # print("TinDD", group)
    result = [[prefix, correct_lst(suffixes)] for prefix, suffixes in grouped.items() if len(suffixes) > 2] #add rule
    # print("ThaoKB", result)
    for res in result:
        if min(res[1]) == 0: continue
        # range_list = list(range(min(res[1]), max(res[1]) + 1))
        # for r in range_list:
        #     if r not in res[1]: print("Missing", f"{res[0]}{r}")
    flattened = [f"{prefix}{num}" for prefix, nums in result for num in nums]
    
    return flattened
        
def group_code(df):
    label_lst = df['label'].to_list()
    ocr_lst = df['ocr'].to_list()
    score_lst = df['score'].to_list()
    result = []
    for key, group in groupby(label_lst): result.append((key, len(list(group))))
    processed_ocr = []
    idx = 0
    set_key = set()
    for k, v in result:
        idx += v
        if k != "code": continue
        ocr_data = ocr_lst[idx-v:idx]
        score_data = score_lst[idx-v:idx]
        ocr_texts = get_highest_ocr_score(score_data, ocr_data).split(":")
        if len(ocr_texts) == 0: continue
        
        if len(processed_ocr) == 0:
            ocr_texts = sorted(ocr_texts, key=lambda x: int(x.split("-")[-1]))
            processed_ocr.append(['code', idx-v, idx, ocr_texts])
            continue
        checker, texts = check_overlap(processed_ocr[-1][-1], ocr_texts)
        texts = sorted(texts, key=lambda x: int(x.split("-")[-1]), reverse = (int(processed_ocr[-1][-1][0].split("-")[2]) == 3) )
        if checker: 
            for te in texts:
                if te in set_key: continue
                set_key.add(te)
            processed_ocr.append(['code', idx-v, idx, texts])
        else:
            # processed_ocr[-1][0] = 'code'
            processed_ocr[-1][-1] = texts
            processed_ocr[-1][-2] = idx
    if int(processed_ocr[0][-1][0].split("-")[2])==2: processed_ocr[0][-1].insert(0,f'{processed_ocr[0][-1][0].split("-")[0]}-{processed_ocr[0][-1][0].split("-")[1]}-1')
    if int(processed_ocr[0][-1][0].split("-")[2]) not in [1, 2]: 
        if processed_ocr[0][-1][0].split("-")[2] < processed_ocr[1][-1][0].split("-")[2]: 
            processed_ocr[0][-1].insert(0,f'{processed_ocr[0][-1][0].split("-")[0]}-{processed_ocr[0][-1][0].split("-")[1]}-0')
    
    return processed_ocr

def get_corresponding_frame(processed_ocr, endframe=10000, fps=30):
    # print(processed_ocr)
    lst_texts = processed_ocr[0][-1]
    video_saving = [0]
    selected_frames = []
    set_key = set()
    
    for i in range(1,len(processed_ocr)):
        flag = False
        for tmp_ele in processed_ocr[i][-1]: 
            if tmp_ele in set_key: 
                flag=True
            else: set_key.add(tmp_ele)
        if flag: continue
        lst_texts.extend(processed_ocr[i][-1])
    lst_texts = get_prefix(lst_texts)
    # print(processed_ocr)
    rm=[]
    for i in range(0,len(processed_ocr)):
        if processed_ocr[i][-1][0] not in lst_texts: rm.append(i)
    for i in rm[::-1]: processed_ocr.pop(i)
    going_up = processed_ocr[0][-1][0].split("-")[2] < processed_ocr[1][-1][0].split("-")[2]
    for i in range(1,len(processed_ocr)):
        # stamp = (processed_ocr[i][-3]+processed_ocr[i][-2])//2
        if going_up: stamp = processed_ocr[i][-3]
        else: stamp = processed_ocr[i][-2]
        
        
        if i != 0 and processed_ocr[i][-1][0].split("-")[1] != processed_ocr[i-1][-1][0].split("-")[1] :
            if int(processed_ocr[i-1][-1][0].split("-")[2])==0:
                tmp=video_saving.pop(-1)
                video_saving.append((video_saving[-1] + tmp)//2)
                video_saving.append(tmp)
            else: 
                video_saving.append((stamp + video_saving[-1])//2)
            going_up = not going_up
        if going_up: stamp = processed_ocr[i][-3]
        else: stamp = processed_ocr[i][-2]
        video_saving.append(stamp)
        # print(processed_ocr[i][-1], stamp, going_up)
    video_saving.append(endframe)
    if video_saving[-1] - video_saving[-2] > 6*fps: 
        video_saving[-1] = video_saving[-2] + 5*fps
    if video_saving[1] - video_saving[0] > 6*fps: 
        video_saving[0] = video_saving[1] - 5*fps
    if int(lst_texts[0].split("-")[-1]) not in processed_ocr[0][-1]: video_saving.insert(0,video_saving[0]-5*fps)
        
    print(len(lst_texts),lst_texts)
    print(len(video_saving),video_saving)
    # print(len(processed_ocr))
    # if int(lst_texts[0].split("-")[2]) == 0: lst_texts.insert(0,f'{lst_texts[0].split("-")[0]}-{lst_texts[0].split("-")[1]}-1')
    
    for i in range(1,len(video_saving)): 
        selected_frames.append([video_saving[i-1]+1, (video_saving[i-1] + video_saving[i])//2, video_saving[i]-1])
    if len(selected_frames) - len(lst_texts) == 1: 
        lst_texts.append(f"{lst_texts[-1].split('-')[0]}-{lst_texts[-1].split('-')[1]}-0")
    return selected_frames, lst_texts

# def create_video(original_video, selected_frames, output_path, fps=30):
    
#     pass

def get_frames(len_video, name_video, fps=30):
    # assert len(len_video) == len(name_video), "len_video và name_video phải cùng độ dài."
    
    ret = []
    going_up = name_video[0].split("-")[2] < name_video[1].split("-")[2]
    for i, (frame_idx, video_name) in enumerate(zip(len_video, name_video)):
        if i!=0 and video_name.split("-")[1] != name_video[i-1].split("-")[1]: going_up = not going_up
        first_idx = frame_idx[0]
        middle_idx = frame_idx[1]
        last_idx = frame_idx[2]
        frame_positions = [
            (last_idx, "code"),
            (middle_idx, "front"),
            (first_idx, "top")
        ]
        # if going_up:
        #     frame_positions = [
        #         (first_idx, "code"),
        #         (middle_idx, "front"),
        #         (last_idx, "top")
        #     ]
        if int(video_name.split("-")[2]) != 1:
            frame_positions = [
                (int(last_idx-fps//3), "code"),
                (int(middle_idx-fps//1.3), "front"), # trừ nhiều để lui về trước nhiều
                (int(first_idx+fps//5), "top")
            ]
            if going_up:
                frame_positions = [
                    (int(first_idx+fps//3), "code"),
                    (int(middle_idx+fps//1.7), "front"), # cộng nhiều để tiến về sau nhiều
                    (int(last_idx-fps//10), "top")
                ]
        # if int(video_name.split("-")[2]) != 1:
        #     frame_positions = [
        #         (int(last_idx-fps//3), "code"),
        #         (int(middle_idx-fps//1.5), "front"),
        #         (int(first_idx+fps//2), "top")
        #     ]
        #     if going_up:
        #         frame_positions = [
        #             (int(first_idx+fps//2), "code"),
        #             (int(middle_idx+fps//1.5), "front"),
        #             (int(last_idx-fps//10), "top")
        #         ]
        
        length = abs(frame_positions[2][0] - frame_positions[0][0])
        if length > 5*fps and int(video_name.split("-")[2]) >= 5:
            length*=0.5
            # frame_positions[1] = (frame_positions[0][0] - int(0.5*length)-fps if frame_positions[2][0] < frame_positions[0][0] else frame_positions[0][0] + int(0.5*length), "front")
            # frame_positions[2] = (frame_positions[0][0] - int(length)-2*fps if frame_positions[2][0] < frame_positions[0][0] else frame_positions[0][0] + int(length), "top")
            frame_positions[1] = (frame_positions[0][0] - int(0.4*length) if frame_positions[2][0] < frame_positions[0][0] else frame_positions[0][0] + int(0.4*length), "front")
            frame_positions[2] = (frame_positions[0][0] - int(length) if frame_positions[2][0] < frame_positions[0][0] else frame_positions[0][0] + int(length), "top")
        if int(video_name.split("-")[2]) == 1: 
            if going_up: frame_positions[2] = (frame_positions[0][0]-1 if frame_positions[0][0]-1>0 else frame_positions[0][0]+1, "top")
            else: frame_positions[0] = (frame_positions[2][0]-1 if frame_positions[2][0]-1>0 else frame_positions[2][0]+1, "code")
        # frame_positions = sorted(frame_positions, key=lambda x: x[0])
        ret.append([frame_positions, video_name])
        # print(f"Completed {video_name}: 3 frames saved to {video_folder}")
        
    return ret

def get_all_codes(df):
    df=edit_prefix(df)
    processed_ocr = group_code(df.copy())
    len_video, name_video = get_corresponding_frame(processed_ocr, endframe=len(df))
    # print(processed_ocr)
    # for i in range(len(name_video)):
    #     print(len_video[i], name_video[i])
    ret = get_frames(len_video, name_video)
    # print(ret)
    return ret

def get_tfc_scores(ret, input_csv, output_csv):
    # Function to update scores with decreasing values
    def update_scores(scores_list, center, max_score, decay_step, range_limit, stable_range=0):
        for offset in range(-range_limit, range_limit + 1):
            frame_idx = center + offset
            if 0 <= frame_idx < len(scores_list):
                # Nếu offset nằm trong khoảng giữ nguyên điểm (stable_range), giữ điểm ở mức max_score
                if abs(offset) <= stable_range:
                    scores_list[frame_idx] = max(scores_list[frame_idx], max_score)
                else:
                    # Tính điểm giảm dần ngoài khoảng stable_range
                    new_score = max_score - decay_step * (abs(offset) - stable_range)
                    if new_score >= 50: scores_list[frame_idx] = max(scores_list[frame_idx], new_score)
    df = pd.read_csv(input_csv)
    frame_idxs = df['frame_idx'].tolist()
    labels = df['label'].tolist()
    ocrs = df['ocr'].tolist()
    scores = df['score'].tolist()
    code_scores = [0 for _ in range(len(frame_idxs))]
    front_scores = [0 for _ in range(len(frame_idxs))]
    top_scores = [0 for _ in range(len(frame_idxs))]
    for i, r in enumerate(ret):
        c, f, t = r[0][0][0], r[0][1][0], r[0][2][0]
        # print(r[0][0])
        # exit()
        update_scores(code_scores, center=c, max_score=100, decay_step=10, range_limit=10, stable_range=5)
        update_scores(front_scores, center=f, max_score=100, decay_step=10, range_limit=10, stable_range=5)
        update_scores(top_scores, center=t, max_score=100, decay_step=10, range_limit=10, stable_range=5)

    df['code_score'] = code_scores
    df['front_score'] = front_scores
    df['top_score'] = top_scores
    df.to_csv(output_csv, index=False)

csv_path = '/ssd1/thaokb/inventory-count-ai/outputs_SD2_521_AH2/DJI_20250920125352_0001_D_175999082921_result/output_csv_processed.csv'

df = pd.read_csv(csv_path)
ret = get_all_codes(df)

# prev_infix = None
# for r in ret:
#     infix = r[1].split("-")[1]
#     if prev_infix is not None and infix != prev_infix: print()  
#     print(r[1], end=' ')
#     prev_infix = infix
# print()  # đảm bảo xuống dòng cuối cùng
# print(len(ret))

get_tfc_scores(ret, csv_path, "tfc_scores2.csv")
# for r in ret: 
#     print(r, r[0][2][0]-r[0][0][0])

