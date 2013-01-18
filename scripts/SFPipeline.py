"""SFPipeline.py

Usage:
  SFPipeline.py CMD (--cfg=<cfgfile>) (--targets=<tgt>) (--log=<log>) [--print] [--forced=<forced>] [--verbose=<v>]

Arguments:
  CMD              The command to run {sf}

Options:
  -h --help          Help
  --cfg=<cfgfile>    Config file
  --targets=<tname>  Target tasks
  --forced=<fname>   Forced tasks
  --log=<lfile>      Log file [default:sfpipeline.log]
  --verbose=<v>      Verbosity level [default:10]
  --print            Only print the pipeline, don't run it [default:False]
"""
from docopt import docopt
import itertools
import glob
import subprocess
import shlex
from ruffus import *

## Can we avoid this global?
sfFiles = {}

if __name__ == '__main__':
    arguments = docopt(__doc__, version="SFPipeline v1.0")
    import logging
    import logging.handlers

    MESSAGE = 15
    logging.addLevelName(MESSAGE, "MESSAGE")

    def setup_std_logging (logger, log_file, verbose):
        """
        set up logging using programme options
        """
        class debug_filter(logging.Filter):
            """
            Ignore INFO messages
            """
            def filter(self, record):
                return logging.INFO != record.levelno

        class NullHandler(logging.Handler):
            """
            for when there is no logging
            """
            def emit(self, record):
                pass

        # We are interesting in all messages
        logger.setLevel(logging.DEBUG)
        has_handler = False

        # log to file if that is specified
        if log_file:
            handler = logging.FileHandler(log_file, delay=False)
            handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)6s - %(message)s"))
            handler.setLevel(MESSAGE)
            logger.addHandler(handler)
            has_handler = True

        # log to stderr if verbose
        if verbose:
            stderrhandler = logging.StreamHandler(sys.stderr)
            stderrhandler.setFormatter(logging.Formatter("    %(message)s"))
            stderrhandler.setLevel(logging.DEBUG)
            if log_file:
                stderrhandler.addFilter(debug_filter())
            logger.addHandler(stderrhandler)
            has_handler = True

        # no logging
        if not has_handler:
            logger.addHandler(NullHandler())


    #
    #   set up log
    #
    logger = logging.getLogger(__name__)
    setup_std_logging(logger, arguments["--log"], arguments["--verbose"])

    #
    #   Allow logging across Ruffus pipeline
    #
    def get_logger (logger_name, args):
        return logger

    from ruffus.proxy_logger import *
    (logger_proxy,
     logging_mutex) = make_shared_logger_and_proxy (get_logger,
                                                    __name__,
                                                    {})


    ##
    # Parse the config file so that the arguments are available when
    # the decorators are invoked.
    ##
    import config
    global configFile

    with open(arguments['--cfg'],'rb') as ifile:
    	configFile = config.Config( ifile )


####
#
# Tasks
#
####

def nobody():
	'''
	Task that does nothing.  @follows this if your task has no real
	dependencies but you may need to do something like mkdir
	'''
	pass

@follows(nobody, mkdir('../results'))
@files( list(itertools.chain(*[glob.glob(fpattern) for fpattern in configFile['BuildIndex']['depends']])),
        configFile['BuildIndex']['produces'],
        configFile['BuildIndex']
	  )
def buildIndex(input, output, config):
	'''
	Build the index for Sailfish.  The underlying program takes a jellyfish
	hash of the transcripts and a set of read files.  It produces a Sailfish
	'index', that consists of the kmers from the hash and their counts (i.e.
	this is the Sailfish version of the Jellyfish hash), and a 'count' file that
    enumerates the counts in the set of reads for all kmers present in the 
    transcripts.
	'''
	def procArg(k,v):
		if k == '--reads':
			v = ' '.join(glob.glob(v))
		return [k,v]

	argString = ' '.join( ' '.join(procArg(k,v)) for k,v in config['arguments'].iteritems() )
	executable = config['executable']
	cmd = [executable] + shlex.split(argString)
	#subprocess.call(cmd)


@follows(buildIndex, mkdir("../results"))
@files( list(itertools.chain(*[glob.glob(fpattern) for fpattern in configFile['Sailfish']['depends']])),
		configFile['Sailfish']['produces'],
		configFile['Sailfish']
	)
def computeExpression(input, output, config):
	'''
	Compute transcript-level expression using Sailfish.
	'''
	argString = ' '.join( ' '.join([k,v]) for k,v in config['arguments'].iteritems() )
	executable = config['executable']
	cmd = [executable] + shlex.split(argString)
	print("\n\nRunning Sailfish with cmd\n====\n {0} \n====\n\n".format(' '.join(cmd)))
	#subprocess.call(cmd)
	
@follows( nobody, mkdir("../results"))
@files( list(itertools.chain(*[glob.glob(fpattern) for fpattern in configFile['QPCRExtraction']['depends']])),
	    configFile['QPCRExtraction']['produces'],
	    configFile['QPCRExtraction']
	  )
def extractQPCRValues(input, output, config):
	'''
	Extract the expression values encoded in a .soft format qPCR file, map
	them to genes and return the result in a simple 2 column expression format.
	'''
	executable = config['executable']
	cmdString = executable + ' ' + ' '.join( ' '.join([k,v]) for k,v in config['arguments'].iteritems() )
	cmd = shlex.split(cmdString)
	subprocess.call(cmd)


####
#
# End of TASKS
#
####

if __name__ == '__main__':
	forcedTasks = [] if arguments['--forced'] is None else arguments['--forced']
	if arguments['--print']:
		pipeline_printout(sys.stdout, arguments['--targets'], forcedTasks)
	else:
		pipeline_run(arguments['--targets'], forcedTasks)

