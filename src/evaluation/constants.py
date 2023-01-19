# Local library
from src.explaining.questioning.questions_templates_bank import *


# Global variables - Instances and solutions
INSTANCES_FOR_EVALUATION_NAMES = \
    ["instance_evaluation_0", "instance_evaluation_1", "instance_evaluation_2", "instance_evaluation_3"]
SOLUTIONS_FOR_EVALUATION_NAMES = \
    [instance_name.replace("instance", "solution") for instance_name in INSTANCES_FOR_EVALUATION_NAMES]

# Global variables - Explainer
# ACTIVATED_QUESTIONS_TEMPLATES_IDS_FOR_EVALUATION = [WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_SWP_1, WHY_NOT_SWP_2A]
ACTIVATED_QUESTIONS_TEMPLATES_IDS_FOR_EVALUATION = [WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_3,
                                                    WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_3]

# Global variables - Evaluation experiment versions
EVALUATION_EXPERIMENT_ASA = 'asa'
EVALUATION_EXPERIMENT_ABA = 'aba'
EVALUATION_EXPERIMENT_ATH = 'ath'
EVALUATION_EXPERIMENT_ACR = 'acr'
EVALUATION_EXPERIMENT_AAL = 'aal'
EVALUATION_EXPERIMENT_BBE = 'bbe'
EVALUATION_EXPERIMENT_DGO = 'dgo'
EVALUATION_EXPERIMENT_DGR = 'dgr'
EVALUATION_EXPERIMENT_FFO = 'ffo'
EVALUATION_EXPERIMENT_IMA = 'ima'
EVALUATION_EXPERIMENT_LLA = 'lla'
EVALUATION_EXPERIMENT_MBO = 'mbo'

# Global variables - Evaluation experiment versions solution and user category
EVALUATION_SOLUTION_0_CATEGORY_1 = EVALUATION_EXPERIMENT_ASA
EVALUATION_SOLUTION_0_CATEGORY_2 = EVALUATION_EXPERIMENT_ABA
EVALUATION_SOLUTION_0_CATEGORY_3 = EVALUATION_EXPERIMENT_ATH
EVALUATION_SOLUTION_1_CATEGORY_1 = EVALUATION_EXPERIMENT_ACR
EVALUATION_SOLUTION_1_CATEGORY_2 = EVALUATION_EXPERIMENT_AAL
EVALUATION_SOLUTION_1_CATEGORY_3 = EVALUATION_EXPERIMENT_BBE
EVALUATION_SOLUTION_2_CATEGORY_1 = EVALUATION_EXPERIMENT_DGO
EVALUATION_SOLUTION_2_CATEGORY_2 = EVALUATION_EXPERIMENT_DGR
EVALUATION_SOLUTION_2_CATEGORY_3 = EVALUATION_EXPERIMENT_FFO
EVALUATION_SOLUTION_3_CATEGORY_1 = EVALUATION_EXPERIMENT_IMA
EVALUATION_SOLUTION_3_CATEGORY_2 = EVALUATION_EXPERIMENT_LLA
EVALUATION_SOLUTION_3_CATEGORY_3 = EVALUATION_EXPERIMENT_MBO

# Global variables - Solution-for-evaluation versions parameters
EVALUATION_EXPERIMENTS_PARAMETERS = {
    EVALUATION_SOLUTION_0_CATEGORY_1: {
        'instance_index': 0, 'enable_explanations': False, 'enable_explanations_representation': False
    },
    EVALUATION_SOLUTION_0_CATEGORY_2: {
        'instance_index': 0, 'enable_explanations': True, 'enable_explanations_representation': False
    },
    EVALUATION_SOLUTION_0_CATEGORY_3: {
        'instance_index': 0, 'enable_explanations': True, 'enable_explanations_representation': True
    },
    EVALUATION_SOLUTION_1_CATEGORY_1: {
        'instance_index': 1, 'enable_explanations': False, 'enable_explanations_representation': False
    },
    EVALUATION_SOLUTION_1_CATEGORY_2: {
        'instance_index': 1, 'enable_explanations': True, 'enable_explanations_representation': False
    },
    EVALUATION_SOLUTION_1_CATEGORY_3: {
        'instance_index': 1, 'enable_explanations': True, 'enable_explanations_representation': True
    },
    EVALUATION_SOLUTION_2_CATEGORY_1: {
        'instance_index': 2, 'enable_explanations': False, 'enable_explanations_representation': False
    },
    EVALUATION_SOLUTION_2_CATEGORY_2: {
        'instance_index': 2, 'enable_explanations': True, 'enable_explanations_representation': False
    },
    EVALUATION_SOLUTION_2_CATEGORY_3: {
        'instance_index': 2, 'enable_explanations': True, 'enable_explanations_representation': True
    },
    EVALUATION_SOLUTION_3_CATEGORY_1: {
        'instance_index': 3, 'enable_explanations': False, 'enable_explanations_representation': False
    },
    EVALUATION_SOLUTION_3_CATEGORY_2: {
        'instance_index': 3, 'enable_explanations': True, 'enable_explanations_representation': False
    },
    EVALUATION_SOLUTION_3_CATEGORY_3: {
        'instance_index': 3, 'enable_explanations': True, 'enable_explanations_representation': True
    }
}
