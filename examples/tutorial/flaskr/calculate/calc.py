import pandas as pd
import numpy as np


## 输入1
#返矿配比
alpha = 0.155
#入炉结构
pp_S = 90
pp_Q = 5
pp_K = 5

## 输入2
df = pd.read_excel("Sample_data1.xlsx")
df.fillna(0, inplace = True)

# P是配比，输入3
P_v = [
    0.2,
    0,
    0.2,
    0,
    0.05,
    0.05,
    0,
    0,
    0.04,
    0.04,
    0.03,
    0.06,
    0.045,
    0,
    0,
    0.05,
    0,
    0.03,
    0.02,
    0.03,
]
P = np.array(P_v).reshape(len(P_v),1)


def get_cal_res(alpha,pp_S,pp_Q,pp_K,df,P):
    l_ele = [
        'TFe',
        'SiO2',
        'Al2O3',
        'S',
        'P',
        'TiO2',
        'MnO',
        'MgO',
        'CaO',
        'K2O',
        'Na2O',
        'ZnO',
        'H2O',
        'As',
        'Cr',
        'FeO',
    ]
    #烧损
    LOI_delta = np.array([alpha * 100]*len(l_ele)).reshape(16,1)
    E = df.iloc[:-2,:][l_ele].T.values

    S_v = [1]*len(l_ele)
    S_v[2] = 0.22
    S = np.diag(S_v)
    K = np.diag((df.iloc[-1,:][l_ele]*pp_K/100 + df.iloc[-2,:][l_ele]*pp_Q/100).tolist())
    LOI = np.array([df.iloc[:-2,:]["烧存"].values.tolist()]*len(l_ele))
    Price = np.array(df["干基不含税到厂价"].tolist()[:-2]).reshape(20,1)
    #计算成分，单位为%，输出对应l_ele
    def get_S_ele(P):
        M_lhs = np.dot(pp_S * np.dot(S, E) + np.dot(K, LOI), P) + np.dot(K, LOI_delta)
        M_rhs = np.dot(LOI, P) + LOI_delta - np.dot(alpha * pp_S * S,
                                                    np.array([1] * S.shape[1]).reshape(
                                                        S.shape[1], 1))
        return (np.dot(S, (np.dot(E, P) + alpha * M_lhs / M_rhs)) / (
                np.dot(LOI, P) + LOI_delta))
    # get_S_ele(P).squeeze()
    #输出1成分
    df_成分 = pd.DataFrame()
    df_成分["成分"] = l_ele
    df_成分["占比%"] = [round(i,2) for i in get_S_ele(P).squeeze()*100]
    #输出2 成本
    O_v= np.dot(P.T, Price)
    P_s1 = O_v.squeeze()
    P_Q = df.iloc[-2, 1]
    P_K = df.iloc[-1, 1]
    P_F = (pp_S*(1-alpha)*P_s1 + pp_Q*P_Q + pp_K*P_K)/100/(1 - pp_S/100*alpha)
    chengben=(P_s1 + alpha*P_F)/(np.sum([i*j for i,j in zip(df.iloc[:-2]["烧存"].tolist(),P_v)])/100+alpha)
    return df_成分,chengben


