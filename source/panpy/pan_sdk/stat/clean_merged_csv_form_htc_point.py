import pandas as pd
import math
import re
from typing import Tuple


class HtcPointInterpreter:
    def __init__(self, csv_path: str) -> None:
        """
        Initialize htc point interpreter class
        @param csv_path: a full path to csv file
        """
        self.csv_path = csv_path
        return
    
    @staticmethod
    def reorder_columns(table: pd.DataFrame):
        x_columns = list(table.filter(regex=r"x\(*").columns)
        x_columns = sorted(x_columns)
        w_columns = list(table.filter(regex=r"w\(*").columns)
        w_columns = sorted(w_columns)
        f_columns = list(table.filter(regex=r"f\(@*").columns)
        f_columns = sorted(f_columns)
        old_columns = list(table.columns)
        new_columns = []
        if 'task_id' in old_columns:
            new_columns = new_columns + ['task_id']
        if 'T' in old_columns:
            new_columns = new_columns + ['T']
        new_columns = new_columns + x_columns + w_columns
        for c in old_columns:
            if c in x_columns or c in w_columns or c in f_columns or c in new_columns:
                continue
            new_columns.append(c)
        new_columns = new_columns + f_columns

        table_new = table[new_columns].copy()
        return table_new
        
    def get_table_and_units(self) -> Tuple[pd.DataFrame, dict]:
        """
        get units dict and dataframe table without units
        @return: dataframe table, units
        """
        merged = pd.read_csv(self.csv_path)

        # -- drop Unnamed: 0 column
        try:
            merged = merged.drop(['Unnamed: 0'], axis=1)
        except KeyError as e:
            print('Congrats! Your data is free from \'Unnamed: 0\'!')

        # -- get units
        units = dict(merged.iloc[0])
        unit_comp = ''
        for key, val in units.items():
            if type(val) != str:
                if math.isnan(val):
                    units[key] = ''
            elif re.match(r"x\(", key):
                unit_comp = val
        for key, val in units.items():
            if re.match(r"x\(", key):
                units[key] = unit_comp
        try:
            del units['task_id']
        except KeyError:
            ...
        # print(units)

        # -- drop unit row from dataframe
        try:
            merged.drop([0], inplace=True)
        except KeyError as e:
            print(e)

        # -- drop task_id column
        # try:
        #     merged.drop(['task_id'], axis=1, inplace=True)
        # except KeyError as e:
        #     print(e)
        # print(merged.columns)

        # -- update index id according to task id
        merged.index = range(len(merged))

        # -- transform phase names to sorted cs format
        try:
            merged['phase_name'].fillna('', inplace=True)
        except KeyError:
            print('there is no column \'phase_name\'')

        def m_sort(m_list):
            m_list.sort()
            return m_list

        try:
            merged['phase_name'] = merged['phase_name'].apply(lambda row: ','.join(m_sort(row.split('+'))))
        except KeyError:
            print('there is no column \'phase_name\'')

        for col in list(merged.filter(regex=r"x\(*").columns):
            merged[col].fillna(0, inplace=True)
            merged[col] = pd.to_numeric(merged[col])
        for col in list(merged.filter(regex=r"f\(@*").columns):
            merged[col].fillna(0, inplace=True)
            merged[col] = pd.to_numeric(merged[col])
        # merged.head()

        merged = self.reorder_columns(merged)

        try:
            merged['T'] = pd.to_numeric(merged['T'])
        except KeyError as e:
            print(e)

        return merged, units
