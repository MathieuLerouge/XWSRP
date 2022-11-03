# Local libraries
from src.explaining.answering.explanation_template import ExplanationTemplate
from src.explaining.questioning.questions_templates_bank import *

# Why-not / contrastive explanations templates
EXPLANATIONS_TEMPLATES_LIST = [

    # Insertion
    ExplanationTemplate(
        id=WHY_NOT_INS_1,
        typical_expressions=dict(
            the_fact="{Task} is not performed by {Employee} just after {Activity}",
            # LANGUAGE_FRENCH_KEY: "{Task} n'est pas réalisée par {Employee} juste après {Activity}"
            the_foil="{Task} is performed by {Employee} just after {Activity}",
            # LANGUAGE_FRENCH_KEY: "{Task} est réalisée par {Employee} juste après {Activity}"
            having_the_foil="having {Task} performed by {Employee} just after {Activity}",
            # LANGUAGE_FRENCH_KEY: "ayant {Task} réalisée par {Employee} juste après {Activity}"
            applying_the_foil_transformation="inserting {Task} just after {Activity} in {Employee}'s planning"
            # LANGUAGE_FRENCH_KEY: "insérant {Task} juste après {Activity} dans le planning de {Employee}"
        )
    ),
    ExplanationTemplate(
        id=WHY_NOT_INS_2A,
        typical_expressions=dict(
            the_fact="{Task} is not performed by {Employee} between two consecutive activities of their planning",
            the_foil="{Task} is performed by {Employee} between two consecutive activities of their planning",
            having_the_foil="having {Task} performed by {Employee} "
                            "between two consecutive activities of their planning",
            neighbors="solutions obtained by inserting {Task} "
                      "between two consecutive activities of {Employee}'s planning"
        )
    ),
    ExplanationTemplate(
        id=WHY_NOT_INS_2B,
        typical_expressions=dict(
            the_fact="{Employee} is not performing any other non-performed task "
                     "between two consecutive activities of their planning",
            the_foil="a formerly-non-performed task is performed by {Employee} "
                     "between two consecutive activities of their planning",
            having_the_foil="having a formerly-non-performed task performed by {Employee} "
                            "between two consecutive activities of their planning",
            neighbors="solutions obtained by inserting a non-performed task "
                      "between two consecutive activities of {Employee}'s planning"
        )
    ),
    ExplanationTemplate(
        id=WHY_NOT_INS_2C,
        typical_expressions=dict(
            the_fact="{Task} is not performed by any of the employees "
                     "between two consecutive activities of their planning",
            the_foil="{Task} is performed by an employee between two consecutive activities of their planning",
            having_the_foil="having {Task} performed by an employee "
                            "between two consecutive activities of their planning",
            neighbors="solutions obtained by inserting {Task} "
                      "between two consecutive activities of an employee's planning"
        )
    ),
    ExplanationTemplate(
        id=WHY_NOT_INS_3,
        typical_expressions=dict(
            the_fact="{Task} is not performed by {Employee} in addition to their activities",
            the_foil="{Task} is performed by {Employee} in addition to their activities",
            having_the_foil="having {Task} performed by {Employee} in addition to their activities",
            neighbors="solutions obtained by assigning {Task} to {Employee} in addition to their activities"
        )
    ),

    # Swap
    ExplanationTemplate(
        id=WHY_NOT_SWP_1,
        typical_expressions=dict(
            the_fact="{Task1} is not performed by {Employee} in place of {Task2}",
            the_foil="{Task1} is performed by {Employee} in place of {Task2}",
            having_the_foil="{Task1} being performed by {Employee} in place of {Task2}",
            applying_the_foil_transformation="replacing {Task2} with {Task1} in {Employee}'s planning"
        )
    ),
    ExplanationTemplate(
        id=WHY_NOT_SWP_2A,
        typical_expressions=dict(
            the_fact="{Task} is not performed by {Employee} in place of any task of their planning",
            the_foil="{Task} is performed by {Employee} in place of one task of their planning",
            having_the_foil="{Task} being performed by {Employee} in place of one task of their planning",
            neighbors="solutions obtained by replacing a task in {Employee}'s planning with {Task}"
        )
    ),
    ExplanationTemplate(
        id=WHY_NOT_SWP_2B,
        typical_expressions=dict(
            the_fact="{Employee} is not performing any non-performed task in place of any task of their planning",
            the_foil="{Employee} is performing a non-performed task in place of one task of their planning",
            having_the_foil="{Employee} performing a non-performed task in place of one task of their planning",
            neighbors="solutions obtained by replacing a task in {Employee}'s planning with a non-performed task"
        )
    ),
    ExplanationTemplate(
        id=WHY_NOT_SWP_2C,
        typical_expressions=dict(
            the_fact="{Task} is not performed by any employee in place of any task of their planning",
            the_foil="{Task} is performed by an employee in place of one of the tasks of their planning",
            having_the_foil="{Task} being performed by an employee in place of one of the tasks of their planning",
            neighbors="solutions obtained by swapping {Task} with one of the tasks performed by an employee"
        )
    ),
    ExplanationTemplate(
        id=WHY_NOT_SWP_3,
        typical_expressions=dict(
            the_fact="{Task} is not performed by {Employee} instead of any task of their planning",
            the_foil="{Task} is performed by {Employee} instead of one of the tasks of their planning",
            having_the_foil="{Task} being performed by {Employee} instead of one of the tasks of their planning",
            neighbors="solutions obtained by exchanging {Task} with one of the tasks performed by {Employee}"
        )
    ),

    # Reordering
    ExplanationTemplate(
        id=WHY_NOT_ORD_LAT_1,
        typical_expressions=dict(
            the_fact="{Employee} is not performing the task {Task1} later just after the task {Task2}",
            applying_the_foil_transformation="moving {Task1} just after {Task2} in {Employee}'s planning"
        )
    ),
    ExplanationTemplate(
        id=WHY_NOT_ORD_EAR_1,
        typical_expressions=dict(
            the_fact="{Employee} is not performing the task {Task1} earlier just before the task {Task2}",
            applying_the_foil_transformation="moving {Task1} just before {Task2} in {Employee}'s planning"
        )
    ),
    ExplanationTemplate(
        id=WHY_NOT_ORD_LAT_2,
        typical_expressions=dict(
            the_fact="{Employee} is not performing the task {Task} at a later stage in their planning",
            neighbors="solutions obtained by moving {Task} at a later stage in {Employee}'s planning"
        )
    ),
    ExplanationTemplate(
        id=WHY_NOT_ORD_EAR_2,
        typical_expressions=dict(
            the_fact="{Employee} is not performing the task {Task} at an earlier stage in their planning",
            neighbors="solutions obtained by moving {Task} at an earlier stage in {Employee}'s planning"
        )
    ),
    ExplanationTemplate(
        id=WHY_NOT_ORD_2,
        typical_expressions=dict(
            the_fact="{Employee} is not performing the task {Task} at another stage in their planning",
            neighbors="solutions obtained by moving {Task} at another stage in {Employee}'s planning"
        )
    ),
    ExplanationTemplate(
        id=WHY_NOT_ORD_3,
        typical_expressions=dict(
            the_fact="{Employee} is not performing their activities in another order",
            neighbors="solutions obtained by permuting the activities in {Employee}'s planning"
        )
    )
]

EXPLANATIONS_TEMPLATES = dict([(template.id, template) for template in EXPLANATIONS_TEMPLATES_LIST])
