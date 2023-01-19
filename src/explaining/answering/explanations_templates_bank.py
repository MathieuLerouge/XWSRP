# Local libraries
from src.explaining.answering.explanation_template import ExplanationTemplate
from src.explaining.questioning.questions_templates_bank import *

# Why-not / contrastive explanations templates
EXPLANATIONS_TEMPLATES_LIST = [

    # Insertion
    ExplanationTemplate(
        id=WHY_NOT_INS_1,
        all_typical_expressions={
            LANGUAGE_ENGLISH_KEY: dict(
                the_fact="{Task} is not performed by {Employee} just after {Activity}",
                the_foil="{Task} is performed by {Employee} just after {Activity}",
                having_the_foil="having {Task} performed by {Employee} just after {Activity}",
                applying_the_foil_transformation="inserting {Task} just after {Activity} in {Employee}'s planning"
            ),
            LANGUAGE_FRENCH_KEY: dict(
                the_fact="{Task} n'est pas réalisée par {Employee} juste après {Activity}",
                the_foil="{Task} est réalisée par {Employee} juste après {Activity}",
                having_the_foil="faire que {Task} soit réalisée par {Employee} juste après {Activity}",
                applying_the_foil_transformation="insérant {Task} juste après {Activity} dans le planning de {Employee}",
            )
        }
    ),
    ExplanationTemplate(
        id=WHY_NOT_INS_2A,
        all_typical_expressions={
            LANGUAGE_ENGLISH_KEY: dict(
                the_fact="{Task} is not performed by {Employee} between two consecutive activities of their planning",
                the_foil="{Task} is performed by {Employee} between two consecutive activities of their planning",
                having_the_foil="having {Task} performed by {Employee} "
                                "between two consecutive activities of their planning",
                neighbors="solutions obtained by inserting {Task} "
                          "between two consecutive activities of {Employee}'s planning"
            ),
            LANGUAGE_FRENCH_KEY: dict(
                the_fact="{Task} n'est pas réalisée par {Employee} entre deux activités consécutives de son planning",
                the_foil="{Task} est réalisée par {Employee} entre deux activités consécutives de son planning",
                having_the_foil="faire que {Task} soit réalisée par {Employee} "
                                "entre deux activités consécutives de son planning",
                neighbors="solutions obtenues en insérant {Task} "
                          "entre deux activités consécutives du planning de {Employee}",
            ),
        }
    ),
    ExplanationTemplate(
        id=WHY_NOT_INS_2B,
        all_typical_expressions={
            LANGUAGE_ENGLISH_KEY: dict(
                the_fact="{Employee} is not performing any other non-performed task "
                         "between two consecutive activities of their planning",
                the_foil="a formerly-non-performed task is performed by {Employee} "
                         "between two consecutive activities of their planning",
                having_the_foil="having a formerly-non-performed task performed by {Employee} "
                                "between two consecutive activities of their planning",
                neighbors="solutions obtained by inserting a non-performed task "
                          "between two consecutive activities of {Employee}'s planning"
            ),
            LANGUAGE_FRENCH_KEY: dict(
                the_fact="{Employee} ne réalise pas une tâche parmi les non-réalisées "
                         "entre deux activités consécutives de son planning",
                the_foil="une tâche précédemment non-réalisée est réalisée par {Employee} "
                         "entre deux activités consécutives de son planning",
                having_the_foil="faire qu'une tâche précédemment non-réalisée soit désormais réalisée par {Employee} "
                                "entre deux activités consécutives de son planning",
                neighbors="solutions obtenues en insérant une tâche non-réalisée "
                          "entre deux activités consécutives du planning de {Employee}"
            )
        }
    ),
    ExplanationTemplate(
        id=WHY_NOT_INS_2C,
        all_typical_expressions={
            LANGUAGE_ENGLISH_KEY: dict(
                the_fact="{Task} is not performed by any of the employees "
                         "between two consecutive activities of their planning",
                the_foil="{Task} is performed by an employee between two consecutive activities of their planning",
                having_the_foil="having {Task} performed by an employee "
                                "between two consecutive activities of their planning",
                neighbors="solutions obtained by inserting {Task} "
                          "between two consecutive activities of an employee's planning"
            ),
            LANGUAGE_FRENCH_KEY: dict(
                the_fact="{Task} n'est réalisée par aucun employé entre deux activités consécutives de leur planning",
                the_foil="{Task} est réalisée par un employé entre deux activités consécutives de son planning",
                having_the_foil="faire que {Task} soit réalisée par un employé "
                                "entre deux activités consécutives de son planning",
                neighbors="solutions obtenues en insérant {Task}"
                          " entre deux activités consécutives du planning d'un employé"
            )
        }
    ),
    ExplanationTemplate(
        id=WHY_NOT_INS_3,
        all_typical_expressions={
            LANGUAGE_ENGLISH_KEY: dict(
                the_fact="{Task} is not performed by {Employee} in addition to their activities",
                the_foil="{Task} is performed by {Employee} in addition to their activities",
                having_the_foil="having {Task} performed by {Employee} in addition to their activities",
                neighbors="solutions obtained by assigning {Task} to {Employee} in addition to their activities"
            ),
            LANGUAGE_FRENCH_KEY: dict(
                the_fact="{Task} n'est pas réalisée par {Employee} en plus des activités de son planning",
                the_foil="{Task} est réalisée par {Employee} en plus des activités de son planning",
                having_the_foil="faire que {Task} soit réalisée par {Employee} en plus des activités de son planning",
                neighbors="solutions obtenues en affectant {Task} à {Employee} en plus des activités de son planning"
            )
        }
    ),

    # Swap
    ExplanationTemplate(
        id=WHY_NOT_SWP_1,
        all_typical_expressions={
            LANGUAGE_ENGLISH_KEY: dict(
                the_fact="{Task1} is not performed by {Employee} in place of {Task2}",
                the_foil="{Task1} is performed by {Employee} in place of {Task2}",
                having_the_foil="{Task1} being performed by {Employee} in place of {Task2}",
                applying_the_foil_transformation="replacing {Task2} with {Task1} in {Employee}'s planning"
            ),
            LANGUAGE_FRENCH_KEY: dict(
                the_fact="{Task1} n'est pas réalisée par {Employee} à la place de {Task2}",
                the_foil="{Task1} est réalisée par {Employee} à la place de {Task2}",
                having_the_foil="faire que {Task1} soit réalisée par {Employee} à la place de {Task2}",
                applying_the_foil_transformation="remplaçant {Task1} par {Task2} dans le planning {Employee}"
            )
        }
    ),
    ExplanationTemplate(
        id=WHY_NOT_SWP_2A,
        all_typical_expressions={
            LANGUAGE_ENGLISH_KEY: dict(
                the_fact="{Task} is not performed by {Employee} in place of any task of their planning",
                the_foil="{Task} is performed by {Employee} in place of one of the tasks of their planning",
                having_the_foil="{Task} being performed by {Employee} in place of one of the tasks of their planning",
                neighbors="solutions obtained by replacing a task in {Employee}'s planning with {Task}"
            ),
            LANGUAGE_FRENCH_KEY: dict(
                the_fact="{Task} n'est pas réalisée par {Employee} à la place d'une des tâches de son planning",
                the_foil="{Task} est réalisée par {Employee} à la place d'une des tâches de son planning",
                having_the_foil="faire que {Task} soit réalisée par {Employee} "
                                "à la place d'une des tâches de son planning",
                neighbors="solutions obtenues en remplaçant une des tâches du planning de {Employee} par {Task} "
            )
        }
    ),
    ExplanationTemplate(
        id=WHY_NOT_SWP_2B,
        all_typical_expressions={
            LANGUAGE_ENGLISH_KEY: dict(
                the_fact="{Employee} is not performing any non-performed task in place of any task of their planning",
                the_foil="{Employee} is performing a non-performed task in place of one task of their planning",
                having_the_foil="{Employee} performing a non-performed task in place of one task of their planning",
                neighbors="solutions obtained by replacing a task in {Employee}'s planning with a non-performed task"
            ),
            LANGUAGE_FRENCH_KEY: dict(
                the_fact="{Employee} ne réalise pas une tâche parmi les non-réalisées "
                         "à la place d'une tâche de son planning",
                the_foil="{Employee} réalise une tâche parmi les non-réalisées "
                         "à la place d'une tâche de son planning",
                having_the_foil="faire que {Employee} réalise une tâche parmi les non-réalisées "
                                "à la place d'une tâche de son planning",
                neighbors="solutions obtenues en remplaçant une tâche du planning de {Employee} "
                          "par une tâche non-réalisée"
            )
        }
    ),
    ExplanationTemplate(
        id=WHY_NOT_SWP_2C,
        all_typical_expressions={
            LANGUAGE_ENGLISH_KEY: dict(
                the_fact="{Task} is not performed by any employee in place of any task of their planning",
                the_foil="{Task} is performed by an employee in place of one of the tasks of their planning",
                having_the_foil="{Task} being performed by an employee in place of one of the tasks of their planning",
                neighbors="solutions obtained by swapping {Task} with one of the tasks performed by an employee"
            ),
            LANGUAGE_FRENCH_KEY: dict(
                the_fact="{Task} n'est réalisée par aucun employé à la place d'une tâche de son planning",
                the_foil="{Task} est réalisée par un employé à la place d'une tâche de son planning",
                having_the_foil="faire que {Task} soit réalisée par un employé à la place d'une tâche de son planning",
                neighbors="solutions obtenues en remplaçant {Task} par une tâche du planning d'un employé"
            )
        }
    ),
    ExplanationTemplate(
        id=WHY_NOT_SWP_3,
        all_typical_expressions={
            LANGUAGE_ENGLISH_KEY: dict(
                the_fact="{Task} is not performed by {Employee} instead of any task of their planning",
                the_foil="{Task} is performed by {Employee} instead of one of the tasks of their planning",
                having_the_foil="{Task} being performed by {Employee} instead of one of the tasks of their planning",
                neighbors="solutions obtained by exchanging {Task} with one of the tasks performed by {Employee}"
            ),
            LANGUAGE_FRENCH_KEY: dict(
                the_fact="{Task} n'est pas réalisée par {Employee} à la place d'une tâche de son planning",
                the_foil="{Task} est réalisée par {Employee} à la place d'une tâche de son planning",
                having_the_foil="faire que {Task} soit réalisée par {Employee} à la place d'une tâche de son planning",
                neighbors="solutions obtenues en remplaçant une tâche dans le planning de {Employee} par {Task}"
            )
        }
    ),

    # Reordering
    ExplanationTemplate(
        id=WHY_NOT_ORD_LAT_1,
        all_typical_expressions={
            LANGUAGE_ENGLISH_KEY: dict(
                the_fact="{Employee} is not performing the task {Task1} later just after the task {Task2}",
                applying_the_foil_transformation="moving {Task1} just after {Task2} in {Employee}'s planning"
            ),
            LANGUAGE_FRENCH_KEY: dict(
                the_fact="{Employee} ne réalise pas {Task1} plus tard juste après {Task2}",
                applying_the_foil_transformation="déplaçant {Task1} juste après {Task2} dans le planning de {Employee}"
            )
        }
    ),
    ExplanationTemplate(
        id=WHY_NOT_ORD_EAR_1,
        all_typical_expressions={
            LANGUAGE_ENGLISH_KEY: dict(
                the_fact="{Employee} is not performing the task {Task1} earlier just before the task {Task2}",
                applying_the_foil_transformation="moving {Task1} just before {Task2} in {Employee}'s planning"
            ),
            LANGUAGE_FRENCH_KEY: dict(
                the_fact="{Employee} ne réalise pas {Task} plus tôt juste avant {Task2}",
                applying_the_foil_transformation="déplaçant {Task1} juste avant {Task2} dans le planning de {Employee}"
            )
        }
    ),
    ExplanationTemplate(
        id=WHY_NOT_ORD_LAT_2,
        all_typical_expressions={
            LANGUAGE_ENGLISH_KEY: dict(
                the_fact="{Employee} is not performing the task {Task} at a later stage in their planning",
                neighbors="solutions obtained by moving {Task} at a later stage in {Employee}'s planning"
            ),
            LANGUAGE_FRENCH_KEY: dict(
                the_fact="{Employee} ne réalise pas {Task} plus tard dans son planning",
                neighbors="solutions obtenues en déplaçant {Task} plus tard dans le planning de {Employee}"
            )
        }
    ),
    ExplanationTemplate(
        id=WHY_NOT_ORD_EAR_2,
        all_typical_expressions={
            LANGUAGE_ENGLISH_KEY: dict(
                the_fact="{Employee} is not performing the task {Task} at an earlier stage in their planning",
                neighbors="solutions obtained by moving {Task} at an earlier stage in {Employee}'s planning"
            ),
            LANGUAGE_FRENCH_KEY: dict(
                the_fact="{Employee} ne réalise pas {Task} plus tôt dans son planning",
                neighbors="solutions obtenues en déplaçant {Task} plus tôt dans le planning de {Employee}"
            )
        }
    ),
    ExplanationTemplate(
        id=WHY_NOT_ORD_2,
        all_typical_expressions={
            LANGUAGE_ENGLISH_KEY: dict(
                the_fact="{Employee} is not performing the task {Task} at another stage in their planning",
                neighbors="solutions obtained by moving {Task} at another stage in {Employee}'s planning"
            ),
            LANGUAGE_FRENCH_KEY: dict(
                the_fact="{Employee} ne réalise pas {Task} à un autre moment dans son planning",
                neighbors="solutions obtenues en déplaçant {Task} à un autre moment dans le planning de {Employee}"
            )
        }
    ),
    ExplanationTemplate(
        id=WHY_NOT_ORD_3,
        all_typical_expressions={
            LANGUAGE_ENGLISH_KEY: dict(
                the_fact="{Employee} is not performing their activities in another order",
                neighbors="solutions obtained by permuting the activities in {Employee}'s planning"
            ),
            LANGUAGE_FRENCH_KEY: dict(
                the_fact="{Employee} ne réalise pas les activités de son planning dans un autre ordre",
                neighbors="solutions obtenues en changeant l'ordre des activités du planning de {Employee}"
            )
        }
    )
]

EXPLANATIONS_TEMPLATES = dict([(template.id, template) for template in EXPLANATIONS_TEMPLATES_LIST])
