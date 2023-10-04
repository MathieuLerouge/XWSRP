# Local libraries
from src.explaining.questioning.constants import WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, \
    WHY_NOT_INS_3, WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3, WHY_NOT_ORD_LAT_1, \
    WHY_NOT_ORD_EAR_1, WHY_NOT_ORD_LAT_2, WHY_NOT_ORD_EAR_2, WHY_NOT_ORD_2, WHY_NOT_ORD_3
from src.explaining.questioning.question_template_field import *
from src.explaining.questioning.question_template import QuestionTemplate
from src.utils.language import LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY

# Categories
ILP_BASED_COMPUTATION_QUESTIONS_TEMPLATES_IDS = [WHY_NOT_INS_3, WHY_NOT_SWP_3, WHY_NOT_ORD_3]
BASED_ON_MOST_RELEVANT_NEIGHBORING_SOLUTION_QUESTIONS_TEMPLATES_IDS = [
    WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3,
    WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3,
    WHY_NOT_ORD_LAT_2, WHY_NOT_ORD_EAR_2, WHY_NOT_ORD_2, WHY_NOT_ORD_3
]

# Why-not / contrastive questions templates
QUESTIONS_TEMPLATES_LIST = [

    # Insertion
    QuestionTemplate(
        id=WHY_NOT_INS_1,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is employee {Employee} not performing task {Task} "
                                  "just after activity {Activity}?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas la tâche {Task} "
                                 "après l'activité {Activity} ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE), FieldAssumptions(TASK + NOT_PERFORMED_BY_0),
                            FieldAssumptions(ACTIVITY + PERFORMED_BY_0 + EXCLUDING_RETURN)]
    ),
    QuestionTemplate(
        id=WHY_NOT_INS_2A,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is employee {Employee} not performing task {Task} "
                                  "between two consecutive activities of their route?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas la tâche {Task} "
                                 "entre deux activités consécutives de son planning ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE), FieldAssumptions(TASK + NOT_PERFORMED_BY_0)]
    ),
    QuestionTemplate(
        id=WHY_NOT_INS_2B,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is employee {Employee} not performing any non-performed task "
                                  "between two consecutive activities of their route?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas une des tâches non-réalisées "
                                 "entre deux activités consécutives de son planning ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE)]
    ),
    QuestionTemplate(
        id=WHY_NOT_INS_2C,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is any employee not performing task {Task} "
                                  "between two consecutive activities of their route?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que la tâche {Task} n'est pas réalisée par un des employés "
                                 "entre deux activités consécutives de son planning ?"
        },
        fields_assumptions=[FieldAssumptions(TASK + NOT_PERFORMED)]
    ),
    QuestionTemplate(
        id=WHY_NOT_INS_3,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is employee {Employee} not performing task {Task} "
                                  "in addition to their already-performed activities "
                                  "(even if it means changing their order)?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas la tâche {Task} "
                                 "en plus des activités déjà réalisées dans son planning "
                                 "(quitte à en changer l'ordre) ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE), FieldAssumptions(TASK + NOT_PERFORMED_BY_0)]
    ),

    # Swap
    QuestionTemplate(
        id=WHY_NOT_SWP_1,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is employee {Employee} not performing task {Task1} "
                                  "rather than task {Task2}?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas la tâche {Task1} "
                                 "à la place de la tâche {Task2} ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE + PERFORMING_EMPLOYEE),
                            FieldAssumptions(TASK + NOT_PERFORMED_BY_0),
                            FieldAssumptions(TASK + PERFORMED_BY_0)]
    ),
    QuestionTemplate(
        id=WHY_NOT_SWP_2A,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is employee {Employee} not performing task {Task} "
                                  "rather than any of their already-performed tasks?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas la tâche {Task} "
                                 "à la place d'une tâche de son planning ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE + PERFORMING_EMPLOYEE),
                            FieldAssumptions(TASK + NOT_PERFORMED_BY_0)]
    ),
    QuestionTemplate(
        id=WHY_NOT_SWP_2B,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is employee {Employee} not performing any non-performed task "
                                  "rather than any of their already-performed tasks?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas une tâche non-réalisée "
                                 "à la place d'une tâche de son planning "
                                 "(sans changer l'ordre des activités dans le planning) ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE + PERFORMING_EMPLOYEE)]
    ),
    QuestionTemplate(
        id=WHY_NOT_SWP_2C,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is any employee is not performing task {Task} "
                                  "rather than any of their already-performed tasks?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce qu'un employé ne réalise pas la tâche {Task} "
                                 "à la place d'une tâche de son planning ?"
        },
        fields_assumptions=[FieldAssumptions(TASK + NOT_PERFORMED)]
    ),
    QuestionTemplate(
        id=WHY_NOT_SWP_3,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is employee {Employee} not performing task {Task} "
                                  "rather than any of their already-performed tasks "
                                  "(even if it means changing their order)?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas la tâche {Task} "
                                 "à la place d'une tâche de son planning "
                                 "(quitte à changer l'ordre des activités dans le planning) ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE + PERFORMING_EMPLOYEE),
                            FieldAssumptions(TASK + NOT_PERFORMED_BY_0)]
    ),

    # Reordering
    QuestionTemplate(
        id=WHY_NOT_ORD_LAT_1,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is employee {Employee} not performing task {Task1} "
                                  "later in their planning, just after task {Task2}?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas la tâche {Task1} "
                                 "plus tard dans son planning, juste après la tâche {Task2} ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE + PERFORMING_MORE_THAN_ONE_TASK_EMPLOYEE),
                            FieldAssumptions(TASK + PERFORMED_BY_0 + EXCLUDING_LAST_TASK),
                            FieldAssumptions(TASK + PERFORMED_BY_0 + AFTER_1)]
    ),
    QuestionTemplate(
        id=WHY_NOT_ORD_EAR_1,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is employee {Employee} not performing task {Task1} "
                                  "earlier in their planning, just before task {Task2}?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas la tâche {Task1} "
                                 "plus tôt dans son planning, juste avant la tâche {Task2} ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE + PERFORMING_MORE_THAN_ONE_TASK_EMPLOYEE),
                            FieldAssumptions(TASK + PERFORMED_BY_0 + EXCLUDING_FIRST_TASK),
                            FieldAssumptions(TASK + PERFORMED_BY_0 + BEFORE_1)]
    ),
    QuestionTemplate(
        id=WHY_NOT_ORD_LAT_2,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is employee {Employee} not performing task {Task} "
                                  "at a later stage of their planning?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas la tâche {Task} "
                                 "plus tard dans son planning ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE + PERFORMING_MORE_THAN_ONE_TASK_EMPLOYEE),
                            FieldAssumptions(TASK + PERFORMED_BY_0 + EXCLUDING_LAST_TASK)]
    ),
    QuestionTemplate(
        id=WHY_NOT_ORD_EAR_2,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is employee {Employee} not performing task {Task} "
                                  "at an earlier stage of their planning?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas la tâche {Task} "
                                 "plus tôt dans son planning ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE + PERFORMING_MORE_THAN_ONE_TASK_EMPLOYEE),
                            FieldAssumptions(TASK + PERFORMED_BY_0 + EXCLUDING_FIRST_TASK)]
    ),
    QuestionTemplate(
        id=WHY_NOT_ORD_2,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is employee {Employee} not performing task {Task} "
                                  "at any another stage in their planning?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas la tâche {Task} "
                                 "à un autre moment dans son planning ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE + PERFORMING_MORE_THAN_ONE_TASK_EMPLOYEE),
                            FieldAssumptions(TASK + PERFORMED_BY_0)]
    ),
    QuestionTemplate(
        id=WHY_NOT_ORD_3,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is employee {Employee} not performing the activities "
                                  "of their route in another order?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas les activités "
                                 "de son planning dans un autre ordre ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE + PERFORMING_MORE_THAN_ONE_TASK_EMPLOYEE)]
    )
]
QUESTIONS_TEMPLATES = dict([(template.id, template) for template in QUESTIONS_TEMPLATES_LIST])
