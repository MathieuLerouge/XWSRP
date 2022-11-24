# Local libraries
from src.explaining.questioning.question_template_field import *
from src.explaining.questioning.question_template import QuestionTemplate
from src.utils.language import LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY

# Why-not / contrastive questions templates ids
# - Insertion
WHY_NOT_INS_1 = 'WN-Ins-1'
WHY_NOT_INS_2A = 'WN-Ins-2a'
WHY_NOT_INS_2B = 'WN-Ins-2b'
WHY_NOT_INS_2C = 'WN-Ins-2c'
WHY_NOT_INS_3 = 'WN-Ins-3'
# - Swap
WHY_NOT_SWP_1 = 'WN-Swp-1'
WHY_NOT_SWP_2A = 'WN-Swp-2'
WHY_NOT_SWP_2B = 'WN-Swp-2a'
WHY_NOT_SWP_2C = 'WN-Swp-2b'
WHY_NOT_SWP_3 = 'WN-Swp-3'
# - Reordering
WHY_NOT_ORD_LAT_1 = 'WN-Ord-Lat-1'
WHY_NOT_ORD_EAR_1 = 'WN-Ord-Ear-1'
WHY_NOT_ORD_LAT_2 = 'WN-Ord-Lat-2'
WHY_NOT_ORD_EAR_2 = 'WN-Ord-Ear-2'
WHY_NOT_ORD_2 = 'WN-Ord-2'
WHY_NOT_ORD_3 = 'WN-Ord-3'

# Why-not / contrastive questions templates
QUESTIONS_TEMPLATES_LIST = [

    # Insertion
    QuestionTemplate(
        id=WHY_NOT_INS_1,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is the employee {Employee} not performing the task {Task} "
                                  "just after the activity {Activity}?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas la tâche {Task} "
                                 "après l'activité {Activity} ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE), FieldAssumptions(TASK + NOT_PERFORMED_BY_0),
                            FieldAssumptions(ACTIVITY + PERFORMED_BY_0 + EXCLUDING_RETURN)]
    ),
    QuestionTemplate(
        id=WHY_NOT_INS_2A,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is the employee {Employee} not performing the task {Task} "
                                  "between two consecutive activities of their route?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas la tâche {Task} "
                                 "entre deux activités consécutives de son planning ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE), FieldAssumptions(TASK + NOT_PERFORMED_BY_0)]
    ),
    QuestionTemplate(
        id=WHY_NOT_INS_2B,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is the employee {Employee} not performing any non-performed task "
                                  "between two consecutive activities of their route?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas une des tâches non-réalisées "
                                 "entre deux activités consécutives de son planning ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE)]
    ),
    QuestionTemplate(
        id=WHY_NOT_INS_2C,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is any employee not performing the task {Task} "
                                  "between two consecutive activities of their route?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que la tâche {Task} n'est pas réalisée par un des employés "
                                 "entre deux activités consécutives de son planning ?"
        },
        fields_assumptions=[FieldAssumptions(TASK + NOT_PERFORMED)]
    ),
    QuestionTemplate(
        id=WHY_NOT_INS_3,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is the employee {Employee} not performing the task {Task} "
                                  "in addition to their already-performed activities"
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
            LANGUAGE_ENGLISH_KEY: "Why is the employee {Employee} not performing the task {Task1} "
                                  "in place of the task {Task2}?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas la tâche {Task1} "
                                 "à la place de la tâche {Task2} ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE), FieldAssumptions(TASK + NOT_PERFORMED_BY_0),
                            FieldAssumptions(TASK + PERFORMED_BY_0)]
    ),
    QuestionTemplate(
        id=WHY_NOT_SWP_2A,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is the employee {Employee} not performing the task {Task} "
                                  "in place of any of their already-performed tasks?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas la tâche {Task} "
                                 "à la place d'une tâche de son planning ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE), FieldAssumptions(TASK + NOT_PERFORMED_BY_0)]
    ),
    QuestionTemplate(
        id=WHY_NOT_SWP_2B,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is the employee {Employee} not performing any non-performed task "
                                  "in place of any of their already-performed tasks?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas une tâche non-réalisée "
                                 "à la place d'une tâche de son planning "
                                 "(sans changer l'ordre des activités dans le planning) ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE)]
    ),
    QuestionTemplate(
        id=WHY_NOT_SWP_2C,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is any employee is not performing the task {Task} "
                                  "in place of any of their already-performed tasks?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce qu'un employé ne réalise pas la tâche {Task} "
                                 "à la place d'une tâche de son planning ?"
        },
        fields_assumptions=[FieldAssumptions(TASK + NOT_PERFORMED)]
    ),
    QuestionTemplate(
        id=WHY_NOT_SWP_3,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is the employee {Employee} not performing the task {Task} "
                                  "instead of any of their already-performed tasks"
                                  "(even if it means changing their order)?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas la tâche {Task} "
                                 "à la place d'une tâche de son planning "
                                 "(quitte à changer l'ordre des activités dans le planning) ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE), FieldAssumptions(TASK + NOT_PERFORMED_BY_0)]
    ),

    # Reordering
    QuestionTemplate(
        id=WHY_NOT_ORD_LAT_1,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is the employee {Employee} not performing the task {Task1} "
                                  "later in their route, just after the task {Task2}?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas la tâche {Task1} "
                                 "plus tard dans son planning, juste après la tâche {Task2} ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE), FieldAssumptions(TASK + PERFORMED_BY_0),
                            FieldAssumptions(TASK + PERFORMED_BY_0)]
        # TODO Add assumption DIFFERENT_FROM_0,1,2
    ),
    QuestionTemplate(
        id=WHY_NOT_ORD_EAR_1,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is the employee {Employee} not performing the task {Task1} "
                                  "earlier in their route, just before the task {Task2}?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas la tâche {Task1} "
                                 "plus tôt dans son planning, juste avant la tâche {Task2} ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE), FieldAssumptions(TASK + PERFORMED_BY_0),
                            FieldAssumptions(TASK + PERFORMED_BY_0)]
        # TODO Add assumption DIFFERENT_FROM_0,1,2
    ),
    QuestionTemplate(
        id=WHY_NOT_ORD_LAT_2,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is the employee {Employee} not performing the task {Task} "
                                  "later in their route?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas la tâche {Task} "
                                 "plus tard dans son planning ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE), FieldAssumptions(TASK + PERFORMED_BY_0)]
    ),
    QuestionTemplate(
        id=WHY_NOT_ORD_EAR_2,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is the employee {Employee} not performing the task {Task} "
                                  "earlier in their route?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas la tâche {Task} "
                                 "plus tôt dans son planning ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE), FieldAssumptions(TASK + PERFORMED_BY_0)]
    ),
    QuestionTemplate(
        id=WHY_NOT_ORD_2,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is the employee {Employee} not performing the task {Task} "
                                  "at another position in their route?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas la tâche {Task} "
                                 "à un autre moment dans son planning ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE), FieldAssumptions(TASK + PERFORMED_BY_0)]
    ),
    QuestionTemplate(
        id=WHY_NOT_ORD_3,
        all_texts={
            LANGUAGE_ENGLISH_KEY: "Why is the employee {Employee} not performing the activities "
                                  "of their route in another order?",
            LANGUAGE_FRENCH_KEY: "Pourquoi est-ce que l'employé {Employee} ne réalise pas les activités "
                                 "de son planning dans un autre ordre ?"
        },
        fields_assumptions=[FieldAssumptions(EMPLOYEE)]
    )
]
QUESTIONS_TEMPLATES = dict([(template.id, template) for template in QUESTIONS_TEMPLATES_LIST])

# Run some tests

if __name__ == '__main__':
    for template in QUESTIONS_TEMPLATES.values():
        print(template)
        print(template.fields_keys)
        print(template.all_texts)
        print(template.text)
        template.set_language(LANGUAGE_FRENCH_KEY)
        print(template.text)
