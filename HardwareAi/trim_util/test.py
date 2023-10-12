import sys, os
import numpy as np
import pandas as pd
from pathlib import Path

def index_of_max_mag(df):
    return np.argmax([row['ax'] ** 2 + row['ay'] ** 2 + row['az'] ** 2 for index, row in df.iterrows()]).item()

fps = 40
target_frames = 80

cfd = sys.path[0]
data_folder = 'raw_csv'
data_dir = os.path.join(cfd, data_folder)

data_dict = {}

for path in Path(data_dir).rglob('*.csv'):
    action_name = path

    while Path(action_name).parent != Path(data_dir):
        action_name = Path(action_name).parent.absolute()
    action_name = os.path.basename(action_name)

    if action_name not in data_dict:
        data_dict[action_name] = []
        data_dict[action_name].append(pd.read_csv(path))

    data_dict[action_name].append(pd.read_csv(path))

for key in data_dict:
    for df in data_dict[key]:
        if len(df) <= target_frames:
            first_row = df.iloc[[0]]
            first_row = pd.DataFrame(np.repeat(first_row.values, target_frames - len(df), axis=0))
            df = pd.concat([first_row, df], ignore_index=True).reset_index(drop = True)
        else:
            max_index = index_of_max_mag(df)
            if max_index - target_frames // 2 < 0:
                df = df.iloc[0 : target_frames]
            elif max_index + target_frames // 2 > len(df):
                df = df.iloc[len(df) - 1 - target_frames : len(df) - 1]
            else:
                df = df.iloc[max_index - target_frames // 2 : max_index + target_frames // 2]


print(data_dict['spear'][0].to_numpy())
