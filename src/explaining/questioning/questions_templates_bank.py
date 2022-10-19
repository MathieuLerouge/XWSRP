# Local libraries
from src.explaining.questioning.question_template_field import *
from src.explaining.questioning.question_template import QuestionTemplate

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
        text="Why is the employee {Employee} not performing the task {Task} just after the activity {Activity}?",
        fields_assumptions=[FieldAssumptions(EMPLOYEE), FieldAssumptions(TASK+NOT_PERFORMED_BY_0),
                            FieldAssumptions(ACTIVITY+PERFORMED_BY_0+EXCLUDING_RETURN)]
    ),
    QuestionTemplate(
        id=WHY_NOT_INS_2A,
        text="Why is the employee {Employee} not performing the task {Task} "
             "between two consecutive activities of their planning?",
        fields_assumptions=[FieldAssumptions(EMPLOYEE), FieldAssumptions(TASK+NOT_PERFORMED_BY_0)]
    ),
    QuestionTemplate(
        id=WHY_NOT_INS_2B,
        text="Why is the employee {Employee} not performing any non-performed task "
             "between two consecutive activities of their planning?",
        fields_assumptions=[FieldAssumptions(EMPLOYEE)]
    ),
    QuestionTemplate(
        id=WHY_NOT_INS_2C,
        text="Why is any employee not performing the task {Task} "
             "between two consecutive activities of their planning?",
        fields_assumptions=[FieldAssumptions(TASK+NOT_PERFORMED)]
    ),
    QuestionTemplate(
        id=WHY_NOT_INS_3,
        text="Why is the employee {Employee} not performing the task {Task} in addition to their activities?",
        fields_assumptions=[FieldAssumptions(EMPLOYEE), FieldAssumptions(TASK+NOT_PERFORMED_BY_0)]
    ),

    # Swap
    QuestionTemplate(
        id=WHY_NOT_SWP_1,
        text="Why is the employee {Employee} not performing the task {Task1} in place of the task {Task2}?",
        fields_assumptions=[FieldAssumptions(EMPLOYEE), FieldAssumptions(TASK+NOT_PERFORMED_BY_0),
                            FieldAssumptions(TASK+PERFORMED_BY_0)]
    ),
    QuestionTemplate(
        id=WHY_NOT_SWP_2A,
        text="Why is the employee {Employee} not performing the task {Task} in place of any of their tasks?",
        fields_assumptions=[FieldAssumptions(EMPLOYEE), FieldAssumptions(TASK+NOT_PERFORMED_BY_0)]
    ),
    QuestionTemplate(
        id=WHY_NOT_SWP_2B,
        text="Why is the employee {Employee} not performing any non-performed task "
             "in place of any task of their planning?",
        fields_assumptions=[FieldAssumptions(EMPLOYEE)]
    ),
    QuestionTemplate(
        id=WHY_NOT_SWP_2C,
        text="Why is any employee is not performing the task {Task} in place of any task of their planning?",
        fields_assumptions=[FieldAssumptions(TASK+NOT_PERFORMED)]
    ),
    QuestionTemplate(
        id=WHY_NOT_SWP_3,
        text="Why is the employee {Employee} not performing the task {Task} rather than any task of their planning?",
        fields_assumptions=[FieldAssumptions(EMPLOYEE), FieldAssumptions(TASK+NOT_PERFORMED_BY_0)]
    ),

    # Reordering
    QuestionTemplate(
        id=WHY_NOT_ORD_LAT_1,
        text="Why is the employee {Employee} not performing the task {Task1} later, just after the task {Task2}?",
        fields_assumptions=[FieldAssumptions(EMPLOYEE), FieldAssumptions(TASK+PERFORMED_BY_0),
                            FieldAssumptions(TASK+PERFORMED_BY_0)]
        # TODO Add assumption DIFFERENT_FROM_0,1,2
    ),
    QuestionTemplate(
        id=WHY_NOT_ORD_EAR_1,
        text="Why is the employee {Employee} not performing the task {Task1} earlier, just before the task {Task2}?",
        fields_assumptions=[FieldAssumptions(EMPLOYEE), FieldAssumptions(TASK+PERFORMED_BY_0),
                            FieldAssumptions(TASK+PERFORMED_BY_0)]
        # TODO Add assumption DIFFERENT_FROM_0,1,2
    ),
    QuestionTemplate(
        id=WHY_NOT_ORD_LAT_2,
        text="Why is the employee {Employee} not performing the task {Task} later in their route?",
        fields_assumptions=[FieldAssumptions(EMPLOYEE), FieldAssumptions(TASK+PERFORMED_BY_0)]
    ),
    QuestionTemplate(
        id=WHY_NOT_ORD_EAR_2,
        text="Why is the employee {Employee} not performing the task {Task} earlier in their route?",
        fields_assumptions=[FieldAssumptions(EMPLOYEE), FieldAssumptions(TASK+PERFORMED_BY_0)]
    ),
    QuestionTemplate(
        id=WHY_NOT_ORD_2,
        text="Why is the employee {Employee} not performing the task {Task} at another step in their route?",
        fields_assumptions=[FieldAssumptions(EMPLOYEE), FieldAssumptions(TASK+PERFORMED_BY_0)]
    ),
    QuestionTemplate(
        id=WHY_NOT_ORD_3,
        text="Why is the employee {Employee} not performing the activities of their route in another order?",
        fields_assumptions=[FieldAssumptions(EMPLOYEE)]
    )
]
QUESTIONS_TEMPLATES = dict([(template.id, template) for template in QUESTIONS_TEMPLATES_LIST])


# Run some tests
if __name__ == '__main__':
    for template in QUESTIONS_TEMPLATES.values():
        print(template)
        print(template.fields_keys)
