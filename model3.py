import pandas as pd
from model1 import Model1
from model2 import Model2

class Model3:
    def __init__(self):
        self.model1 = Model1()
        self.model2 = Model2()

    def get(self, params):
        if type(params) != dict:
            return {'message': 'params must be dict'}

        if (params['tx'] == 'get_raw_text_upper'):
            res = self.model1.get({'tx': 'get_raw_data'})
            inp = [v['text'] for k, v in res.items()]
            out = self.model2.get({'tx': 'get_upper', 'txt': inp})
            return out

            # return pd.Series(params['txt']).str.upper().to_dict()

    def __del__(self):
        pass

if __name__ == '__main__':
    model3 = Model3()
    print(model3.get({'tx': 'get_raw_text_upper'}))