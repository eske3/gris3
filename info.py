#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    grisのバージョン情報などを保持するモジュール
    
    Dates:
        date:2017/01/22 0:02[Eske](eske3g@gmail.com)
        update:2020/10/13 14:47 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
# Grisに関する情報を登録している固定変数。/////////////////////////////////////
Author = 'eske3g@gmail.com'
Version = '2.0.0.1'
LastModified = 20250701
# /////////////////////////////////////////////////////////////////////////////


ReleaseNote = [
('2.0.0.2',
(
    'gadgets.facialExpressionManagerのExpressionButtonを選択式に変更。最後にクリックしたボタンがアクティブカラーになる',
    'gadgets.toolbarのToolbarクラスにウィジェットを追加するaddWidgetを追加',
    'Factoryの現在のプロジェクト表示ラベルをツールバーに追加する仕様に変更',
    'modelingSupporterのミラー機能のリネーム機能の改善',
)
),

('2.0.0.0',
(
    'PySide6対応。',
)
),

('1.1.6.0',
(
    '標準フェイシャル用エクストラコンストラクタの実装（ベータ版）',
)
),

('1.1.5.4',
(
    'node.BlendShape.listAttrNamesのアルゴリズムを変更。状況によって一覧に漏れが発生するバグに対応。',
    '上記変更に伴い、node.BlendShape.indexFromTextのアルゴリズムも正しく動作するよう修正。',
)
),


('1.1.5.3',
(
    'facialExpressionManager.ManagerEngineに管理ノードの更新機能を追加。',
    '合わせてGUIからも更新がかかるように一部修正。',
)
),

('1.1.5.2',
(
    'gadgets.facialExpressionManagerに表情一覧のリネーム機能を追加。',
    'tools.facialMemoryManagerに表情一覧のリネーム機能を追加。',
)
),

('1.1.5.0',
(
    'scriptManagerのGUI更新と、デバッグモードまわりの仕様変更。',
)
),

('1.1.4.6',
(
    'GUIのカラーに関する仕様を変更。uilibにカラークラスを作成し、そこからEnum形式でデータを取るように変更。',
)
),

('1.1.4.5',
(
    'node.AbstractNodeにlistInheritedTypesを追加。',
    'nodeRenamerにライト用の命名規則を追加',
)
),

('1.1.4.1',
(
    'facialExpressionManagerの登録ボタンを押した際にGUIが更新されないバグを修正。',
)
),

('1.1.4.0',
(
    'funcモジュールに２つのトランスフォームノード間の共通の親までの親リストを返す関数「listMatrixPath」を追加',
)
),

('1.1.3.2',
(
    'polyHalfRemoverとpolyMirrorのローカル軸対応。',
)
),

('1.1.3.0',
(
    'facialMemoryManagerならびにfacialExpressionManagerの追加。',
)
),

('1.1.2.0',
(
    'archiveモジュールのarchiveProject関数内のローカル関数を一部グローバル化。',
    'archiveモジュールにwriteToZip、defaultFilter、message関数とZipWriterクラスを追加。'
)
),

('1.1.1.0',
(
    'curvePrimitivesにラインの太さに関するパラメータを追加。'
    '作成されるカーブの太さのデフォルト値を設定。デフォルト値は3.0。'
)
),

('1.1.0.1',
(
    'nodeのcreateNode関数実行時に、型変換にバグがあったため修正。'
)
),

('1.1.0.0',
(
    'nodeのasObject関数実行時に、対象オブジェクトの型階層を見てクラスを返すように挙動を変更。',
    'tools.modelCheckerにcheckHistory関数の戻り値を変更。',
    'tools.sceneDataCheker.historyCheckerのクラスにcheckIgnoredHistoryNodeメソッドを追加。',
)
),


('1.0.16.0',
(
    'tools.modelCheckerにcheckHistory関数を追加。',
    'tools.sceneDataChekerにhistoryCheckerモジュールを追加。',
)
),


('1.0.15.2',
(
    'tools.cleanupのDefaultShadingEnginesにdefaultTextureList1を追加。',
)
),


('1.0.15.0',
(
    'node.SkinClusterにlistWeightsメソッドを追加。',
    'node.skinClusterのfixBrokenLimitInfluenceにwithWeightListオプションを追加。',
)
),


('1.0.14.0',
(
    'checkModulesに頂点カラーセットのチェック機能を追加。',
    'それに伴いcheckUtilとcheckModulesの仕様を一部変更。',
)
),


('1.0.13.0',
(
    'tools.skinUtilityにstoreWeightMdoelとrestoreWeightModel関数を追加。',
)
),


('1.0.12.3',
(
    'checkUtil内のクラスを細分化。',
    'toolsとcheckModules内にシーンデータをチェックするsceneDataCheckerを追加。',
)
),


('1.0.12.1',
(
    'modelCheckerの一部の機能に、チェック対象ノードを指定する引数を追加。',
)
),

('1.0.12.0',
(
    'tools.checkUtilを追加。',
    'gadgets.checkToolsを追加（暫定バージョン）',
)
),


('1.0.11.4',
(
    'curvePrimitiveにfootCを追加。',
    'ikFkChainのIKコントローラ生成アルゴリズムを修正、numberOfIkControlsの結果を正しく反映させるように。',
    '上記変更に伴い、ikFkChainのユニットにoldSpecificationを追加。',
    'ikFkChainユニットを最新版に更新するためのパッチ関数「ikFkChain.updateNewStyle1」を追加。',
)
),


('1.0.11.2',
(
    'skinUtility.transferObjectsWeightsの一部内部アルゴリズムをOpenMayaに置換して高速化。',
)
),

('1.0.11.1',
(
    'uilib.ClosableGroupにisExpandingメソッドを追加。',
)
),

('1.0.11.0',
(
    'Pythonモジュールの内部関数を一覧化するScriptViewerを追加。',
)
),

('1.0.10.1',
(
    'node.AbstractNodeにaddAngleAttrを追加。',
)
),

('1.0.10.0',
(
    'rigUtilにconnectMeshKeepingShape関数を追加。',
    'node.DoCommandの引数に、実行中カーソルをウェイトにするオプションを追加。',
)
),

('1.0.9.1',
(
    'ポーズのミラー・スワップ機能を背骨FKに対応。',
)
),

('1.0.9.0',
(
    'ポーズのミラー・スワップ機能をGUI化（暫定仕様版）',
)
),

('1.0.8.0',
(
    'ジョイントの自動リネーマ機能追加。',
)
),

('1.0.7.1',
(
    'extraJointExporterの書き出しを"wb"から"w"に変更。（Maya2023対応）',
)
),

('1.0.7.0',
(
    'IK/FKマッチングに4足リグを対応。',
)
),

('1.0.6.1',
(
    'core.createRigForAllUnit関数に引数rootPathを追加。（デフォルトは空文字)',
)
),

('1.0.6.0',
(
    'tools.animationUtilにクリーンナップ系コマンドを追加。',
)
),

('1.0.5.0',
(
    'tools.jointBendTwistSplitterモジュールを正式リリース。',
)
),

('1.0.4.2',
(
    'fileInfoManagerのFileInfoManagerデータ読み込み時のエンコード処理をPythonのバージョンごとに振り分け。',
)
),

('1.0.4.0',
(
    'Maya2023対応。',
)
),

('1.0.3.2',
(
    'tools.painSkinUtilityのselectBindedSkin関数で、状況によってはメッシュが取得できない不具合を修正。',
)
),

('1.0.3.1',
(
    'toHumanIKモジュールで、肘・膝のベンドコントローラのベイクオプションを追加。',
)
),

('1.0.3.0',
(
    'アニメーション周りの機能を追加。',
    'aiFacialUtilの瞬き機能の機能拡張。',
)
),

('1.0.2.2',
(
    'lib.encodeとlib.decodeをPython3以降で仕様を変更。',
    'qtArchiveをMaya2022以降に対応。',
    'simpleSpineRigをMaya2022以降に対応。',
)
),

('1.0.2.1',
(
    '小さなバグフィックス。',
)
),

('1.0.2.0',
(
    'ベース機能の拡張。',
)
),

('1.0.1.0',
(
    'Factoryのブラウザで任意のファイルをカレントとして適用する機能を追加。',
)
),

('1.0.0.2',
(
    'constructor.BasicConstructor.importJointsのバインディングボックスにたいする処理を修正',
)
),

('1.0.0.1',
(
    'Maya2022対応の際のバグを一部修正。',
)
),

('1.0.0.0Beta',
(
    'Maya2022対応（暫定）。',
)
),

('0.9.16.0',
(
    'extraConstructorにFKコントローラ作成補助モジュールfkCtrlHelperを追加。',
)
),

('0.9.15.0',
(
    'curvePrimitives.PrimitiveCreatorにcopyParamメソッドを追加。',
    'curvePrimitives.PrimitiveCreatorのcurveメソッドのスペルミスを修正。',
)
),


('0.9.14.1',
(
    'modelingSupporterのPolyOperationクラスのsetParentの挙動を調整。',
)
),

('0.9.14.0',
(
    'node.NurbsCurveにnormalとtangentを追加。',
)
),

('0.9.13.1',
(
    'gadgetsのspringSimulatorのUI表示バグを修正。',
)
),

('0.9.13.0',
(
    'modelCheckerにlistInstances関数を追加。',
    'gadgets.cleanUpにインスタンスをリストする機能を追加。',
)
),


('0.9.12.3',
(
    'BasicConstrutorのdeleteUnusedTopNodesの引数を追加。',
    'McpConstructorのfinished内で不要なトップノードを削除するように動作を変更。',
)
),

('0.9.12.2',
(
    'SkinEditorガジェットにbindToTube機能のGUIボタンを追加。',
)
),

('0.9.12.1',
(
    'IK/FKマッチングでworldコントローラが移動している場合にずれる不具合を修正。',
)
),

('0.9.12.0',
(
    'IK/FKマッチングしながらベイクする機能を追加。',
)
),

('0.9.11.2',
(
    'node.TransformのsetMatrixの引数worldがFalseの場合のバグを修正。',
)
),

('0.9.11.1',
(
    'core.createJointが戻り値としてjointCreatorを返すように変更。',
)
),

('0.9.11.0',
(
    'QtWidgets.qAppをQtWidgets.QApplicationに変更。Maya2020の一部スピナで起こるバグを修正。',
    'extraJointの選択にタグによるフィルタを追加。',
    'tools.selectionUtilにネームスペースをリストする関数を追加。',
)
),

('0.9.10.1',
(
    'simUtilityの一部のコードをmaya2020向けに対応',
    'toHumanIkモジュール内で肘・膝の追訴用コントローラを肘・膝に追従するように変更',
)
),

('0.9.10.0',
(
    'extraConstructor.ExtraConstructorにcreateSetupPartsを追加',
    'constructor.ConstructorにcreateExtraSetupPartsを追加',
    'toolsにanimUtilモジュールを追加',
    'constructor.BasicConstructorのloadSkinWeightsでウェイトの読み込み順序の制御機構を追加',
)
),

('0.9.9.1',
(
    'tools.selectionUtilにselectHardEdges関数を追加',
    'tools.modelingSupporterにunlockAndSetNormal関数を追加',
    'gadgets.cleanupToolsにunlockAndSetNormalへアクセスするボタンを追加',
)
),

('0.9.9.0',
(
    'ハードサーフェースモデリング用の便利機能モジュールhardsurfaceModelerを追加。',
    'ハードサーフェースモデリング用の便利機能集ガジェットを追加',
    'rigScripts.PresetElementクラスの引き数にsuffixを追加。',
    'showFactory関数に強制的にGUIを更新するforceUpdateオプションを追加。',
    'funcのドキュメントを更新。',
    'func.SoftModificationで作成されるradiusコントローラのアトリビュートをscaleXからradiusに変更。',
    'func.createSculptDeformerの戻り値の中身を全てnode.AbstractNode系に統一。',
)
),

('0.9.8.1',
(
    'nodeモジュールにshadingNode関数を追加。',
)
),

('0.9.8.0',
(
    'QObjectのサブクラスの__new__処理を全て削除し、maya2020に対応',
)
),
]
