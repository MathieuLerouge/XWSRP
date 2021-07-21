###########
# Modules #
###########

# Project modules
from Utils.time import *



#############
# Functions #
#############

def main():
    print(convertTimeStringToMinutes("2:00pm"))
    print(convertMinutesToTimeString(840))
    print(convertMinutesToTimeString(719))
    print(convertMinutesToTimeString(720))

if __name__ == '__main__':
    main()
