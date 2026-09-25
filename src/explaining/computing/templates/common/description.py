# Local libraries
from src.modeling.activity import Activity
from src.modeling.comeback import COMING_BACK_HOME_STRING
from src.modeling.departure import LEAVING_HOME_STRING
from src.modeling.employee import Employee
from src.modeling.task import Task
from src.utils.language import LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY

# Global variable
HOME_NAMES = {LANGUAGE_ENGLISH_KEY: "Home", LANGUAGE_FRENCH_KEY: "Domicile"}


##############################
# TransformationDescriptions #
##############################

class TransformationDescriptions:
    """
    Builds the sentence describing an applied transformation, in each of the languages explanations are given in.

    Every method returns the same shape: the sentence keyed by language, ready to be carried by a
    TransformationResult and stored on the Explanation built from it.
    """

    @staticmethod
    def rename_route_ends_into_home_steps(route_description: str, language_key: str) -> str:
        """
        Return the route description with its departure and come-back steps named as the employee's home.

        Args:
            route_description: The route as the transformations spell it, e.g. "[Start, T7, T3, Return]".
            language_key: The language to name home in.

        Returns:
            The route description, e.g. "[Home, T7, T3, Home]" in English.
        """
        home_name = HOME_NAMES[language_key]
        return route_description.replace(LEAVING_HOME_STRING, home_name).replace(COMING_BACK_HOME_STRING, home_name)


    @staticmethod
    def write_routes_by_language(route_description: str) -> dict[str, str]:
        """Return the route description with its ends named as home, keyed by language."""
        return {language_key: TransformationDescriptions.rename_route_ends_into_home_steps(
                    route_description, language_key)
                for language_key in (LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY)}

    @staticmethod
    def for_insertion_after_activity(task: Task, activity: Activity, employee: Employee) -> dict[str, str]:
        """
        Describe inserting the task right after the given activity of the employee's planning.

        Args:
            task: The inserted task.
            activity: The activity the task is inserted after.
            employee: The employee whose planning is changed.

        Returns:
            The sentence keyed by language.
        """
        activity_names = {language_key: HOME_NAMES[language_key] if activity.name == LEAVING_HOME_STRING
                          else activity.name
                          for language_key in (LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY)}
        return {
            LANGUAGE_ENGLISH_KEY:
                f"inserting {task.name} just after {activity_names[LANGUAGE_ENGLISH_KEY]} "
                f"in {employee.name}'s planning",
            LANGUAGE_FRENCH_KEY:
                f"insérant {task.name} juste après {activity_names[LANGUAGE_FRENCH_KEY]} "
                f"dans le planning de {employee.name}",
        }

    @staticmethod
    def for_swap(leaving_task: Task, replacing_task: Task, employee: Employee) -> dict[str, str]:
        """
        Describe replacing one task of the employee's planning with another, leaving the route's order alone.

        Args:
            leaving_task: The task dropped from the planning.
            replacing_task: The task taking its place.
            employee: The employee whose planning is changed.

        Returns:
            The sentence keyed by language.
        """
        return {
            LANGUAGE_ENGLISH_KEY:
                f"replacing {leaving_task.name} from {employee.name}'s planning by {replacing_task.name}",
            LANGUAGE_FRENCH_KEY:
                f"remplaçant {leaving_task.name} du planning de {employee.name} par {replacing_task.name}"
        }

    @staticmethod
    def for_move_after(moving_task: Task, fixed_task: Task, employee: Employee) -> dict[str, str]:
        """
        Describe moving a task later in the employee's planning, to just after a task that stays put.

        Args:
            moving_task: The task being moved.
            fixed_task: The task it is moved after.
            employee: The employee whose planning is changed.

        Returns:
            The sentence keyed by language.
        """
        return {
            LANGUAGE_ENGLISH_KEY:
                f"moving {moving_task.name} just after {fixed_task.name} in {employee.name}'s planning",
            LANGUAGE_FRENCH_KEY:
                f"déplaçant {moving_task.name} juste après {fixed_task.name} dans le planning de {employee.name}"
        }

    @staticmethod
    def for_move_before(moving_task: Task, fixed_task: Task, employee: Employee) -> dict[str, str]:
        """
        Describe moving a task earlier in the employee's planning, to just before a task that stays put.

        Args:
            moving_task: The task being moved.
            fixed_task: The task it is moved before.
            employee: The employee whose planning is changed.

        Returns:
            The sentence keyed by language.
        """
        return {
            LANGUAGE_ENGLISH_KEY:
                f"moving {moving_task.name} just before {fixed_task.name} in {employee.name}'s planning",
            LANGUAGE_FRENCH_KEY:
                f"déplaçant {moving_task.name} juste avant {fixed_task.name} dans le planning de {employee.name}"
        }

    @staticmethod
    def for_insertion_route(task: Task, employee: Employee, route_description: str) -> dict[str, str]:
        """
        Describe adding a task to the employee's planning, spelling out the route it takes to fit in.

        Args:
            task: The added task.
            employee: The employee whose planning is changed.
            route_description: The route the transformation settled on.

        Returns:
            The sentence keyed by language.
        """
        routes = TransformationDescriptions.write_routes_by_language(route_description)
        return {
            LANGUAGE_ENGLISH_KEY:
                f"adding {task.name} in {employee.name}'s planning "
                f"according to the following route {routes[LANGUAGE_ENGLISH_KEY]}",
            LANGUAGE_FRENCH_KEY:
                f"ajoutant {task.name} dans le planning de {employee.name} "
                f"selon la route suivante {routes[LANGUAGE_FRENCH_KEY]}"
        }

    @staticmethod
    def for_swap_and_rerouting(leaving_task: Task, replacing_task: Task, employee: Employee,
                               route_description: str) -> dict[str, str]:
        """
        Describe swapping a task of the employee's planning and rerouting around it.

        Args:
            leaving_task: The task dropped from the planning.
            replacing_task: The task taking its place.
            employee: The employee whose planning is changed.
            route_description: The route the transformation settled on.

        Returns:
            The sentence keyed by language.
        """
        routes = TransformationDescriptions.write_routes_by_language(route_description)
        return {
            LANGUAGE_ENGLISH_KEY:
                f"replacing {leaving_task.name} by {replacing_task.name} in {employee.name}'s "
                f"and applying the following route {routes[LANGUAGE_ENGLISH_KEY]}",
            LANGUAGE_FRENCH_KEY:
                f"remplaçant {leaving_task.name} par {replacing_task.name} dans le planning de {employee.name} "
                f"et en appliquant l'itinéraire suivant {routes[LANGUAGE_FRENCH_KEY]}"
        }

    @staticmethod
    def for_swap_route(replaced_task: Task, replacing_task: Task, employee: Employee,
                       route_description: str) -> dict[str, str]:
        """
        Describe replacing one task of the employee's planning with another, spelling out the resulting route.

        Args:
            replaced_task: The task dropped from the planning.
            replacing_task: The task taking its place.
            employee: The employee whose planning is changed.
            route_description: The route the transformation settled on.

        Returns:
            The sentence keyed by language.
        """
        routes = TransformationDescriptions.write_routes_by_language(route_description)
        return {
            LANGUAGE_ENGLISH_KEY:
                f"replacing {replaced_task.name} with {replacing_task.name} "
                f"in {employee.name}'s planning according to the following route {routes[LANGUAGE_ENGLISH_KEY]}",
            LANGUAGE_FRENCH_KEY:
                f"remplaçant {replaced_task.name} par {replacing_task.name} "
                f"dans le planning de {employee.name} selon la route suivante {routes[LANGUAGE_FRENCH_KEY]}"
        }

    @staticmethod
    def for_reordering_route(employee: Employee, route_description: str) -> dict[str, str]:
        """
        Describe reordering the employee's whole route, spelling out the order settled on.

        Args:
            employee: The employee whose planning is changed.
            route_description: The route the transformation settled on.

        Returns:
            The sentence keyed by language.
        """
        routes = TransformationDescriptions.write_routes_by_language(route_description)
        return {
            LANGUAGE_ENGLISH_KEY:
                f"reordering {employee.name}'s route into the following route {routes[LANGUAGE_ENGLISH_KEY]}",
            LANGUAGE_FRENCH_KEY:
                f"réordonnant l'itinéraire de {employee.name} en l'itinéraire suivant {routes[LANGUAGE_FRENCH_KEY]}"
        }

    @staticmethod
    def for_task_moving_route(moving_task: Task, employee: Employee, route_description: str) -> dict[str, str]:
        """
        Describe moving one task within the employee's planning, spelling out the resulting route.

        Args:
            moving_task: The task being moved.
            employee: The employee whose planning is changed.
            route_description: The route the transformation settled on.

        Returns:
            The sentence keyed by language.
        """
        routes = TransformationDescriptions.write_routes_by_language(route_description)
        return {
            LANGUAGE_ENGLISH_KEY:
                f"moving {moving_task.name} in {employee.name}'s planning "
                f"according to the following route {routes[LANGUAGE_ENGLISH_KEY]}",
            LANGUAGE_FRENCH_KEY:
                f"déplaçant {moving_task.name} dans le planning de {employee.name} "
                f"selon la route suivante {routes[LANGUAGE_FRENCH_KEY]}"
        }

    @staticmethod
    def none() -> dict[str, str]:
        """Return the empty description, for a transformation that was never applied."""
        return {LANGUAGE_ENGLISH_KEY: "", LANGUAGE_FRENCH_KEY: ""}
