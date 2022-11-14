import sqlite3
import pandas as pd

class Model1:
    def __init__(self):
        self.db_path = './model1/model1.db'

    def get(self, params):
        if type(params) != dict:
            return {'message': 'params must be dict'}

        if (params['tx'] == 'get_raw_data'):
            with sqlite3.connect(self.db_path) as con:
                df_raw_text = pd.read_sql('select * from raw_text', con)
            if params.get('cnt'):
                df_raw_text = df_raw_text.head(params['cnt'])
            return df_raw_text.T.to_dict()

    def __del__(self):
        pass

if __name__ == '__main__':
    model1 = Model1()
    print(model1.get({'tx': 'get_raw_data'}))