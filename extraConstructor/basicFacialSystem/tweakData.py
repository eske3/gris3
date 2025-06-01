#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    フェイシャルのツイーク用ジョイントの位置情報を保持するモジュール
    
    Dates:
        date:2017/02/25 13:10[Eske](eske3g@gmail.com)
        update:2021/08/21 04:45 noriyoshi tsujimoto[tensoftware@hotmail.co.jp]
        
    License:
        Copyright 2017 noriyoshi tsujimoto[tensoftware@hotmail.co.jp] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from collections import OrderedDict


def createJointDataFromSelected():
    r"""
        シーン中の選択ノード（Joint）から、Tweak用ジョイントの位置情報を
        書き出すためのUtility関数。
        戻り値は本モジュールに記載されているような辞書形式の構文テキスト。
        
        Returns:
            str:
    """
    from ... import node
    import json
    datalist = OrderedDict()
    def getData(j):
        data = OrderedDict({'t':j('t')[0], 'radius':j('radius')})
        children_data = OrderedDict()
        for c in j.children():
            children_data[c] = getData(c)
        if children_data:
            data['jo'] = j('jo')[0]
            data['children'] = children_data
        return data
    for jnt in node.selected():
        datalist[jnt] = getData(jnt)
    return(json.dumps(datalist, indent=4))


TweakJointData = OrderedDict()
TweakJointData['facialBrowJnt_grp'] = {
    "browA_jnt_L": {
        "radius": 0.2, 
        "t": [
            2.12862, 
            150.353, 
            9.46497
        ]
    }, 
    "browB_jnt_L": {
        "radius": 0.2, 
        "t": [
            2.97577, 
            150.712, 
            9.19554
        ]
    }, 
    "browC_jnt_L": {
        "radius": 0.2, 
        "t": [
            3.95065, 
            150.759, 
            8.81643
        ]
    }, 
    "browD_jnt_L": {
        "radius": 0.2, 
        "t": [
            4.90589, 
            150.558, 
            8.42115
        ]
    }, 
    "browE_jnt_L": {
        "radius": 0.2, 
        "t": [
            5.79216, 
            150.167, 
            7.9804
        ]
    }, 
    "browA_jnt_R": {
        "radius": 0.2, 
        "t": [
            -2.12862, 
            150.353, 
            9.46497
        ]
    }, 
    "browB_jnt_R": {
        "radius": 0.2, 
        "t": [
            -2.97577, 
            150.712, 
            9.19554
        ]
    }, 
    "browC_jnt_R": {
        "radius": 0.2, 
        "t": [
            -3.95065, 
            150.759, 
            8.81643
        ]
    }, 
    "browD_jnt_R": {
        "radius": 0.2, 
        "t": [
            -4.90589, 
            150.558, 
            8.42115
        ]
    }, 
    "browE_jnt_R": {
        "radius": 0.2, 
        "t": [
            -5.79216, 
            150.167, 
            7.9804
        ]
    }
}


TweakJointData['facialEyeJnt_grp'] = {
    "eyeTopA_jnt_L": {
        "radius": 0.3, 
        "t": [
            2.0424, 
            147.35, 
            8.08239
        ]
    }, 
    "eyeTopB_jnt_L": {
        "radius": 0.3, 
        "t": [
            3.69499, 
            148.163, 
            7.81733
        ]
    }, 
    "eyeTopC_jnt_L": {
        "radius": 0.3, 
        "t": [
            4.98675, 
            147.87, 
            7.34929
        ]
    }, 
    "eyeTopD_jnt_L": {
        "radius": 0.3, 
        "t": [
            5.922, 
            146.679, 
            6.84652
        ]
    }, 
    "eyeTopE_jnt_L": {
        "radius": 0.3, 
        "t": [
            5.79166, 
            145.742, 
            6.79965
        ]
    }, 
    "eyeBtmA_jnt_L": {
        "radius": 0.3, 
        "t": [
            2.28947, 
            145.333, 
            7.97277
        ]
    }, 
    "eyeBtmB_jnt_L": {
        "radius": 0.3, 
        "t": [
            3.71314, 
            144.747, 
            7.6276
        ]
    }, 
    "eyeBtmC_jnt_L": {
        "radius": 0.3, 
        "t": [
            5.07291, 
            144.928, 
            7.131
        ]
    }, 
    "eyeTopA_jnt_R": {
        "radius": 0.3, 
        "t": [
            -2.0424, 
            147.35, 
            8.08239
        ]
    }, 
    "eyeTopB_jnt_R": {
        "radius": 0.3, 
        "t": [
            -3.69499, 
            148.163, 
            7.81733
        ]
    }, 
    "eyeTopC_jnt_R": {
        "radius": 0.3, 
        "t": [
            -4.98675, 
            147.87, 
            7.34929
        ]
    }, 
    "eyeTopD_jnt_R": {
        "radius": 0.3, 
        "t": [
            -5.922, 
            146.679, 
            6.84652
        ]
    }, 
    "eyeTopE_jnt_R": {
        "radius": 0.3, 
        "t": [
            -5.79166, 
            145.742, 
            6.79965
        ]
    }, 
    "eyeBtmA_jnt_R": {
        "radius": 0.3, 
        "t": [
            -2.28947, 
            145.333, 
            7.97277
        ]
    }, 
    "eyeBtmB_jnt_R": {
        "radius": 0.3, 
        "t": [
            -3.71314, 
            144.747, 
            7.6276
        ]
    }, 
    "eyeBtmC_jnt_R": {
        "radius": 0.3, 
        "t": [
            -5.07291, 
            144.928, 
            7.131
        ]
    }
}


TweakJointData['facialMouthJnt_grp'] = {
    "mouthTop_jnt_C": {
        "radius": 0.1, 
        "t": [
            0, 
            141.368896484375, 
            8.985084533691406
        ]
    }, 
    "mouthTop_jnt_L": {
        "radius": 0.1, 
        "t": [
            0.560931921005249, 
            141.38650512695312, 
            8.954192161560059
        ]
    }, 
    "mouthSideTop_jnt_L": {
        "radius": 0.1, 
        "t": [
            1.101129412651062, 
            141.3868408203125, 
            8.826103210449219
        ]
    }, 
    "mouthCornerTop_jnt_L": {
        "radius": 0.1, 
        "t": [
            1.3270424604415894, 
            141.41224670410156, 
            8.653575897216797
        ]
    }, 
    "mouthCorner_jnt_L": {
        "radius": 0.1, 
        "t": [
            1.4180048704147339, 
            141.4110107421875, 
            8.598675727844238
        ]
    }, 
    "mouthBtm_jnt_C": {
        "radius": 0.1, 
        "t": [
            0, 
            141.33065795898438, 
            9.058869361877441
        ]
    }, 
    "mouthBtm_jnt_L": {
        "radius": 0.1, 
        "t": [
            0.5851966738700867, 
            141.33860778808594, 
            9.030377388000488
        ]
    }, 
    "mouthSideBtm_jnt_L": {
        "radius": 0.1, 
        "t": [
            1.0732344388961792, 
            141.41421508789062, 
            8.791229248046875
        ]
    }, 
    "mouthCornerBtm_jnt_L": {
        "radius": 0.1, 
        "t": [
            1.3138282299041748, 
            141.404296875, 
            8.624814987182617
        ]
    }, 
    "mouthTop_jnt_R": {
        "radius": 0.1, 
        "t": [
            -0.560932, 
            141.387, 
            8.95419
        ]
    }, 
    "mouthSideTop_jnt_R": {
        "radius": 0.1, 
        "t": [
            -1.10113, 
            141.387, 
            8.8261
        ]
    }, 
    "mouthCornerTop_jnt_R": {
        "radius": 0.1, 
        "t": [
            -1.32704, 
            141.412, 
            8.65358
        ]
    }, 
    "mouthCorner_jnt_R": {
        "radius": 0.1, 
        "t": [
            -1.418, 
            141.411, 
            8.59868
        ]
    }, 
    "mouthBtm_jnt_R": {
        "radius": 0.1, 
        "t": [
            -0.585197, 
            141.339, 
            9.03038
        ]
    }, 
    "mouthSideBtm_jnt_R": {
        "radius": 0.1, 
        "t": [
            -1.07323, 
            141.414, 
            8.79123
        ]
    }, 
    "mouthCornerBtm_jnt_R": {
        "radius": 0.1, 
        "t": [
            -1.31383, 
            141.404, 
            8.62481
        ]
    }
}


TweakJointData['facialNoseJnt_grp'] = {
    "nose_jnt_C": {
        "radius": 0.2, 
        "t": [
            0, 
            143.79879760742188, 
            10.248152732849121
        ]
    }
}


TweakJointData['facialCheekJnt_grp'] = {
    "cheekA_jnt_L": {
        "radius": 0.5, 
        "t": [
            5.7773, 
            142.075, 
            5.98364
        ]
    }, 
    "cheekB_jnt_L": {
        "radius": 0.5, 
        "t": [
            3.75776, 
            140.26, 
            6.32701
        ]
    }, 
    "cheekA_jnt_R": {
        "radius": 0.5, 
        "t": [
            -5.7773, 
            142.075, 
            5.98364
        ]
    }, 
    "cheekB_jnt_R": {
        "radius": 0.5, 
        "t": [
            -3.75776, 
            140.26, 
            6.32701
        ]
    }, 
    "jaw_jnt_C": {
        "radius": 0.5, 
        "t": [
            0, 
            138.57896423339844, 
            7.798895835876465
        ]
    }
}


TweakJointData['facialInnerMouthJnt_grp'] = {
    "tongueA_jnt_C": {
        "radius": 0.32518579959869387, 
        "t": [
            0.0, 
            140.70889282226562, 
            4.808104753494263
        ], 
        "jo": [
            -89.99999999999994, 
            -31.88814441867232, 
            89.99999999999997
        ], 
        "children": {
            "tongueB_jnt_C": {
                "radius": 0.3251859188079834, 
                "t": [
                    0.9027974300304891, 
                    1.4210854715202004e-14, 
                    -1.6940658945086007e-21
                ], 
                "jo": [
                    0.0, 
                    2.522421932690238e-06, 
                    -48.14652463652879
                ], 
                "children": {
                    "tongueC_jnt_C": {
                        "radius": 0.3251901388168335, 
                        "t": [
                            0.8081189480604429, 
                            2.73495080207152e-16, 
                            2.842170943040401e-14
                        ], 
                        "jo": [
                            -9.478791598866946e-23, 
                            -3.0969711407415546e-06, 
                            -16.526013372804652
                        ], 
                        "children": {
                            "tongueD_jnt_C": {
                                "radius": 0.314946722984314, 
                                "t": [
                                    0.5398749443083233, 
                                    2.842170943040401e-14, 
                                    -2.637408605448083e-16
                                ], 
                                "jo": [
                                    -9.478791598867036e-23, 
                                    8.52191302732439e-06, 
                                    -8.003682032870744
                                ], 
                                "children": {
                                    "tongueE_jnt_C": {
                                        "radius": 0.283532452583313, 
                                        "t": [
                                            0.6326087710528583, 
                                            5.684341886080802e-14, 
                                            -3.0846398840159855e-16
                                        ], 
                                        "jo": [
                                            -0.06244818700997852, 
                                            0.22717154408921056, 
                                            -0.805977211998811
                                        ], 
                                        "children": {
                                            "tongueF_jnt_C": {
                                                "radius": 0.31037048339843754, 
                                                "t": [
                                                    0.7197489102831938, 
                                                    2.842170943040401e-14, 
                                                    -7.806255641895632e-16
                                                ], 
                                                "jo": [
                                                    0.10180466973075537, 
                                                    -0.3511194411168951, 
                                                    -0.7990475015760571
                                                ], 
                                                "children": {
                                                    "tongueEnd_jnt_C": {
                                                        "radius": 0.06774269938468934, 
                                                        "t": [
                                                            0.5081135746296042, 
                                                            0.0, 
                                                            1.0651202142497596e-15
                                                        ]
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}