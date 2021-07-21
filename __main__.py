###########
# Modules #
###########


# Basic modules
import sys

# Add directories
sys.path.append('Checking')
sys.path.append('Definition')
sys.path.append('Explanation')
sys.path.append('Extraction')
sys.path.append('Optimization')
sys.path.append('Representation')
sys.path.append('Tools')
sys.path.append('Writing')

# Project modules
import Checking.checking_routine
import Extraction.extraction_routine
import Explanation.explanation_routine
import Optimization.optimization_routine



########
# Main #
########

if __name__ == '__main__':
    Checking.checking_routine.main()
    Explanation.explanation_routine.main()
    #Extraction.extraction_routine.main()
    #Optimization.optimization_routine.main()
