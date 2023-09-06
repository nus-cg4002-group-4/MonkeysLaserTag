import os
import sys
import pandas as pd
from scipy.stats import zscore
from scipy import signal
import argparse
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

class MainApp:
    def __init__(self):
        self.home_dir = sys.path[0]

        parser = argparse.ArgumentParser(description='Trimmer Utility',
                                            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('input', help='Input .csv file. Will view if no options provided')
        parser.add_argument('-t', '--trim', nargs=2, help='Trim .csv file. Syntax: -t [Start frame] [Window size]', type=int)
        parser.add_argument('-e', '--expand', nargs=4, help='Trim .csv file based on window of x samples, then expand to y samples in steps of z. Syntax: -t [Start frame] [x] [y] [z]', type=int)
        parser.add_argument('-o', '--output', help='Output of trimmed .csv file')
        args = parser.parse_args()
        self.args_dict = vars(args)
        print(self.args_dict)

        try:
            self.data_df = pd.read_csv(self.args_dict['input'])
        except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError) as e:
            print('Error: cannot open .csv file.')
            return
        
        if self.args_dict['expand']:
            start = self.args_dict['expand'][0]
            expand = self.args_dict['expand'][2]
            wiggle = self.args_dict['expand'][2] - self.args_dict['expand'][1]
            step_size = self.args_dict['expand'][3]

            if start - wiggle < 0 or (start + expand) > self.data_df['acc_x'].size or wiggle < 0:
                print('Error: Index out of range.')
                return

            save_dfs = []
            for w in range(-wiggle // step_size, wiggle // step_size):
                save_dfs.append(self.data_df.iloc[start+w*step_size:start+w*step_size+expand])

            for df in range(len(save_dfs)):
                new_name = os.path.basename(self.args_dict['input']).split('.csv')[0] + '-' + str(df) + '.csv'
                if self.args_dict['output']:
                    save_dfs[df].to_csv(os.path.join(self.args_dict['output'], new_name), index=False)
                else:
                    save_dfs[df].to_csv(os.path.join(self.home_dir, 'trimmed_csv', new_name), index=False)
            return
        
        if self.args_dict['trim']:
            start = self.args_dict['trim'][0]
            size = self.args_dict['trim'][1]
            save_df = pd.DataFrame()

            if start < 0 or (start + size) > self.data_df['acc_x'].size:
                print('Error: Index out of range.')
                return
            
            save_df = self.data_df.iloc[start:start+size]

            if self.args_dict['output']:
                save_df.to_csv(os.path.join(self.args_dict['output'], os.path.basename(self.args_dict['input'])), index=False)
            else:
                save_df.to_csv(os.path.join(self.home_dir, 'trimmed_csv', os.path.basename(self.args_dict['input'])), index=False)
            return
        
        numeric_cols = self.data_df.select_dtypes(include=[np.number]).columns
        mod_df = self.data_df[numeric_cols].apply(signal.detrend)
        mod_df = mod_df[numeric_cols].apply(zscore)
        self.data_df.drop(labels=numeric_cols, axis="columns", inplace=True)
        self.data_df[numeric_cols] = mod_df[numeric_cols]
        
        for i in range(2):
            self.data_df['acc_x'] = self.data_df['acc_x'].astype('float').cumsum()
            self.data_df['acc_y'] = self.data_df['acc_y'].astype('float').cumsum()
            self.data_df['acc_z'] = self.data_df['acc_z'].astype('float').cumsum()

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.plot(self.data_df['acc_x'], self.data_df['acc_y'], self.data_df['acc_z'])

        plt.rc('font', size=8) 
        ax.text2D(0, 1, self.data_df['id'][0], transform=ax.transAxes)
        for i in range(self.data_df['acc_x'].size):
            if i % 5 == 0:
                ax.text(self.data_df['acc_x'][i], self.data_df['acc_y'][i], self.data_df['acc_z'][i], i)
        
        plt.show()
    
main = MainApp()
