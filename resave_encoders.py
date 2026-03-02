import pickle
import joblib
import os

encoders_dir = 'ml/encoders'
for f in os.listdir(encoders_dir):
    if f.endswith('.pkl'):
        path = os.path.join(encoders_dir, f)
        obj = joblib.load(path)
        with open(path, 'wb') as fout:
            pickle.dump(obj, fout, protocol=4)
        print(f'Re-saved: {f}')

print('Done!')
