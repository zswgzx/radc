export FSLCONFDIR=$FSLDIR/config
include $FSLCONFDIR/default.mk

PROJNAME = randomise

USRINCFLAGS = -I${INC_NEWMAT} -I${INC_PROB} -I${INC_ZLIB} -fopenmp
USRLDFLAGS = -L${LIB_NEWMAT} -L${LIB_PROB} -L${LIB_ZLIB} -fopenmp -lpthread
#LDFLAGS= -fopenmp

#-lpthread
LIBS = -lnewimage -lmiscmaths -lutils -lm -lnewmat -lfslio -lniftiio -lznz -lprob -lz -lpthread

XFILES = randomise fdr unconfound randomise_openmp

SCRIPTS = design_ttest2 randomise_parallel tfce_support randomise_combine setup_masks

R_OBJS = randomise.o ranopts.o

F_OBJS = fdr.o


#MINE
#CXX = g++
Ro_OBJS = randomise_openmp.o ranopts.o

#OPTFLAGS =

all:	$XFILES

randomise:  ${R_OBJS}
	    $CXX  $CXXFLAGS $LDFLAGS -o $@ ${R_OBJS} $LIBS

unconfound: unconfound.o
	     $CXX  $CXXFLAGS $LDFLAGS -o $@ unconfound.o $LIBS

fdr: ${F_OBJS}
	    $CXX  $CXXFLAGS $LDFLAGS -o $@ ${F_OBJS} $LIBS

randomise_openmp:  ${Ro_OBJS}
	    $CXX  $CXXFLAGS $LDFLAGS -o $@ ${Ro_OBJS} $LIBS
