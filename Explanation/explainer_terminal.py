# TODO

# def promptYesNoQuestion(question):
#     print(f"XPer: {question} [Y/N]")
#     answer = input("XPee: ")
#     if answer in ["Y", "y", "Yes", "yes"]:
#         return True
#     elif answer in ["N", "n", "No", "no"]:
#         return False
#     else:
#         print("XPer: You gave an incorrect answer, please use Y for yes or N for no")
#         print("")
#         return promptYesNoQuestion(question)
#
#
# def checkIfUserHasAnyQuestion():
#     return promptYesNoQuestion("Do you have any questions?")
#
#
# def findOutAndAnswerUserQuestion(solution: Solution):
#
#     tabulation = "      "
#     print("XPer: Which question do you want to ask among the following? [Give the number corresponding to your question] ")
#     print(tabulation + "1. Why employee _ does not realize task _ instead of the task _ in his planning?")
#     print(tabulation + "2.1. Why employee _ does not realize task _ just after the activity _ in his planning?")
#     print(tabulation + "2.2. Why employee _ does not realize task _ in addition the tasks of his planning?")
#
#     try:
#         answer = float(input("XPee: "))
#
#         if np.any(np.isin(answer, [1, 2.1, 2.2, 2.3], assume_unique = True)):
#             print("XPer: Then please fill the following data")
#             employeeName = input(tabulation + "- Employee's name: ")
#             if not(solution.instance.hasEmployee(employeeName)):
#                 return False, solution
#             enteringTaskName = input(tabulation + "- Non-realized entering task's name: ")
#             if not(solution.instance.hasTask(enteringTaskName)):
#                 return False, solution
#             if answer == 1:
#                 leavingTaskName = input(tabulation + "- Realized leaving task's name: ")
#                 if not(solution.instance.hasTask(leavingTaskName)):
#                     return False, solution
#                 print("")
#                 return answerQuestionAboutReplacing(solution, employeeName, enteringTaskName, leavingTaskName)
#             elif answer == 2.1:
#                 beforeInsertionActivityName = input(tabulation + "- Activity's name before insertion: ")
#                 print("")
#                 return answerQuestionAboutInserting(solution, employeeName, enteringTaskName, beforeInsertionActivityName)
#             elif answer == 2.2:
#                 print("")
#                 return answerQuestionAboutInsertingInAddition(solution, employeeName, enteringTaskName)
#             elif answer == 2.3:
#                 print("")
#                 return answerQuestionAboutInsertingByForce(solution, employeeName, enteringTaskName)
#
#         else:
#             print("XPer: You gave an incorrect number")
#             return False, solution
#
#     except ValueError:
#         print("XPer: You did not give a number")
#         return False, solution
