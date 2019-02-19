import argparse as argp
import subprocess as subp
import os
import sys
import glob
from whichcraft import which


args = ''' 
arguments needed:
- sample name(s) X
- number of CPUS X
- reference FA X


- GDCF name NO
- location of genome directory? NOT as argument
- top directory? NOT as argument

command layout:

python tool.py Sample.1.fq Sample.2.fq ref.fa [numCPUS]


'''

# left to do:
# check errors in cmd function
# properly redirect stdout

# change language for help descriptions
# clean up variable names

def prereqs():
    programs = ["python", "bwa", "samtools", "STAR"]

    for i in range(0, len(programs)):
        if which(programs[i]) is None:
            print(programs[i] + " not installed. Please install " + programs[i])
    return




def cmd(args, write=False, filepath=None):

    if(write==True):
        temp = sys.stdout
        sys.stdout = open(filepath, 'w')

        try:
            subp.check_call(args, stdout=sys.stdout)
        except subp.CalledProcessError, e:
            print("Subprocesss error with code: " + e.returncode)
            return;
        except:
            print("An unknown error occurred")


        sys.stdout = temp

    else:
    	#subp.check_call(args)
        try:
            subp.check_call(args)
        except subp.CalledProcessError, e:
            print("Subprocesss error with code: " + e.returncode)
            return;
        except:
            print("An unknown error occurred")


    return

def main(): 

    myparse = argp.ArgumentParser(description='Runs the tool')
    myparse.add_argument('sampleName', metavar="sampleName", help="name of the sample(s) to be aligned")
    myparse.add_argument('reference', metavar="refFasta", help="the reference .fa file for the program")
    myparse.add_argument('path', metavar="path", help="path to the Human Genome")
    myparse.add_argument('-cpus', type=int, default=2, help="number of CPUS for processing")
    myparse.add_argument('-twosamps', type=bool, default=False, help="number of sample fq files")

    args = myparse.parse_args()

    prereqs()

    topdirectory = os.getcwd()

    nameOnly = args.sampleName.split(".")[0]

    if(args.twosamps == True):
        numSamples = 2
    else:
        numSamples = 1
            

    cmd(["mkdir", nameOnly])
    
    # don't really need, just modify paths
    # cmd(["cd", args.sampleName])
    # with cd(args.sampleName): # to change directories
            
         
    # # generates 2 fastq files (need to add option for just one)
    if(args.sampleName.lower().endswith(".bam")):
        cmd(["echo", "Extracting raw reads"]) # if bam file given as input, convert to fastq
        cmd(["samtools", "fastq",
             "-1{}.1.fq".format(args.sampleName),
             "-2{}.2.fq".format(args.sampleName),
             "-0{}".format(os.devnull), 
             "-n", "-F 0x900", "-@ {}".format(args.cpus-1),
             "{}".format(args.sampleName)])

    cmd(["echo", "Aligning reads to human genome"])

    ##generates Aligned.out.bam, Chimeric.out.junction, Log.final.out, Log.out
    ##Log.progress.out, SJ.out.tabl, Unmapped.out.mate1, Unmapped.out.mate2

    cmd(
        ["STAR", 
        "--genomeDir {path}".format(args.path),
        "--readFilesIn {sampleName}.1.fq {sampleName}.2.fq".format(sampleName=args.sampleName),
        "--runThreadN {}".format(args.cpus),
        "--chimSegmentMin 18",
        "--outSAMtype BAM Unsorted",
        "--outReadsUnmapped Fastx",
        "--outFilterMultimapNmax 100",
        "--outFileNamePrefix ./{}.".format(args.sampleName)])

    for format in {'*.out','*.junction','*.tab','*.Aligned.*'}:
        for file in glob.glob(format):
            os.remove(file)


    cmd(
        ["rm", 
        "{}.1.fq".format(args.sampleName), 
        "{}.2.fq".format(args.sampleName)])

    cmd(["echo", "Aligning reads to HPV genomes"])

    for i in range(1, numSamples + 1):
        cmd(
            ["bwa", 
            "aln", 
            "-t {}".format(args.cpus),
            "{}".format(args.reference),
            "{sampleName}.Unmapped.out.mate{i}".format(sampleName=args.sampleName, i=i)], 
            True, "{sampleName}.{i}.sai".format(sampleName=args.sampleName, i=i))

        cmd(
            ["bwa", 
            "samse", 
            "{}".format(args.reference), 
            "{sampleName}.{i}.sai".format(sampleName=args.sampleName, i=i),
            "{sampleName}.Unmapped.out.mate{i}".format(sampleName=args.sampleName, i=i)],
            True,"{sampleName}.{i}.aln-se.sam".format(sampleName=args.sampleName,i=i))

        cmd(
            ["samtools",
            "view",
            "-F4"
            "-@ {}".format((args.cpus - 1)),
            "{sampleName}.{i}.aln-se.sam".format(sampleName=args.sampleName, i=i)], 
            True,"{topdir}/{name}/HPV.aligned.{i}.sam".format(topdir=topdirectory, name=nameOnly, i=i))

        for format in {'*.sam','*.sai'}:
            for file in glob.glob(format):
                os.remove(file)


if __name__ == '__main__':
    main()
