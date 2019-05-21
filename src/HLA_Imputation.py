#-*- coding: utf-8 -*-

import os, sys, re
from os.path import join
import pandas as pd

from src.HLA_MultipleRefs import HLA_MultipleRefs


########## < Core Varialbes > ##########

std_MAIN_PROCESS_NAME = "\n[%s]: " % (os.path.basename(__file__))
std_ERROR_MAIN_PROCESS_NAME = "\n[%s::ERROR]: " % (os.path.basename(__file__))
std_WARNING_MAIN_PROCESS_NAME = "\n[%s::WARNING]: " % (os.path.basename(__file__))

HLA_names = ["A", "B", "C", "DPA1", "DPB1", "DQA1", "DQB1", "DRB1"]

# __overlap__ = [3000, 4000, 5000]
__overlap__ = [3000]


class HLA_Imputation(object):

    def __init__(self, MHC, _reference, _out, _hg,
                 _LINKAGE2BEAGLE, _BEAGLE2VCF, _PLINK, _BEAGLE4,
                 __save_intermediates, idx_process,
                 _aver_erate=None, _Genetic_Map=None, f_useMultipleMarkers=False):


        ### Class variables
        self.idx_process = idx_process
        self.__save_intermediates = __save_intermediates
        self.OUTPUT_dir = os.path.dirname(_out)
        self.OUTPUT_dir_ref = join(self.OUTPUT_dir, os.path.basename(_reference))
        self.f_useGeneticMap = False
        self.f_useMultipleMarkers = f_useMultipleMarkers



        ###### < Setting Flag for using Genetic Map > ######

        if _aver_erate and _Genetic_Map:

            # Both '--average-erate(-ae)' and '--genetic-map(-gm)' are given. => To use genetic map in imputation.

            if not os.path.exists(_aver_erate):
                print(std_ERROR_MAIN_PROCESS_NAME + "The file ('{}') doesn't exist.\n"
                                                    "Please check '--average-erate/-ae' argument again.".format(_aver_erate))
                sys.exit()

            if not os.path.exists(_Genetic_Map):
                print(std_ERROR_MAIN_PROCESS_NAME + "The file ('{}') doesn't exist.\n"
                                                    "Please check '--genetic-map/-gm' argument again.".format(_Genetic_Map))
                sys.exit()

            self.f_useGeneticMap = True

        else:

            if (_aver_erate and not _Genetic_Map) or (not _aver_erate and _Genetic_Map):
                print(std_ERROR_MAIN_PROCESS_NAME + "Either arguments '--genetic-map(-gm)' or '--average-erate(-ae)' wasn't given.\n"
                                                    "Please check whether both of them are given or not.")
                sys.exit()


        ###### < Loading information related to Multiple markers > ######

        df_reference_bim = pd.read_csv(_reference + '.bim', sep='\s+', names=['Chr', 'Label', 'GD', 'POS', 'A1', 'A2'])
        # print(std_MAIN_PROCESS_NAME + 'Loaded reference bim file : \n{}'.format(df_reference_bim.head()))

        df_EXON_info = pd.read_csv('data/HLA_EACH_EXON_POSITIONS_hg{}.txt'.format(_hg), header=0, sep='\s+', usecols=[0, 1, 4], index_col=[1])
        # print(std_MAIN_PROCESS_NAME + 'Loaded Exon information : \n{}'.format(df_EXON_info.loc['exon2', :]))




        ###### < 'CONVERT_IN', 'IMPUTE', 'CONVERT_OUT' with multiple markers. > ######

        # print(std_MAIN_PROCESS_NAME + "'CONVERT_IN', 'IMPUTE', 'CONVERT_OUT' with multiple markers.")

        ### Main iteration
        # for _exonN_ in ['exon2', 'exon3', 'exon4']:
        for _exonN_ in ['exon2']:

            __ExonN_Refs__ = HLA_MultipleRefs(_exonN_, df_EXON_info.loc[_exonN_, :].reset_index(drop=True).set_index('HLA'),
                                              _reference, df_reference_bim, _out, _hg, _PLINK, _LINKAGE2BEAGLE)


            for _overlap_ in __overlap__:

                print(std_MAIN_PROCESS_NAME + "exonN: {} / Overlap: {}".format(_exonN_, _overlap_))


                ### (1) CONVERT_IN

                # [Doubled_VCF, REF_PHASED_VCF] = self.CONVERT_IN(MHC, __ExonN_Refs__.getOUTPUT(), _out, _hg, _LINKAGE2BEAGLE, _BEAGLE2VCF, _PLINK, _BEAGLE4)


                ### (2) IMPUTE

                # Temporary Hard coding
                # Doubled_VCF = 'tests/_3_CookHLA/20190520/_3_HM_CEU_T1DGC_REF.MHC.QC.phasing_out_not_double.doubled.vcf'
                # REF_PHASED_VCF = 'tests/_3_CookHLA/20190520/T1DGC_REF.phased.vcf'

                # IMPUTED_RESULT_VCF = self.IMPUTE(_out, Doubled_VCF, REF_PHASED_VCF, _BEAGLE4, _aver_erate, _Genetic_Map)
                # print('Imputation result : {}'.format(IMPUTED_RESULT_VCF))

                ### (3) CONVERT_OUT





    def CONVERT_IN(self, MHC, _reference, _out, _hg, _LINKAGE2BEAGLE, _BEAGLE2VCF, _PLINK, _BEAGLE4):



        print("[{}] Converting data to beagle format.".format(self.idx_process))

        command = ' '.join(
            [_LINKAGE2BEAGLE, 'pedigree={}'.format(MHC + '.QC.nopheno.ped'), 'data={}'.format(MHC + '.QC.dat'),
             'beagle={}'.format(MHC + '.QC.bgl'), 'standard=true', '>', _out + '.bgl.log'])  # Making '*.bgl' file.
        # print(command)
        os.system(command)

        if not self.__save_intermediates:
            os.system(' '.join(['rm', MHC + '.QC.nopheno.ped']))
            os.system(' '.join(['rm', MHC + '.QC.dat']))
            os.system(' '.join(['rm', _out + '.bgl.log']))


        ### Converting data to reference_markers_Position (Dispersing same genomic position of some markers.)

        from src.redefineBPv1BH import redefineBP

        RefinedMarkers = redefineBP(_reference + '.markers',
                                    os.path.join(self.OUTPUT_dir, os.path.basename(_reference) + '.refined.markers'))


        ### Converting data to target_markers_Position and extract not_including snp.

        command = ' '.join(['awk \'{print $2" "$4" "$5" "$6}\'', MHC + '.QC.bim', '>',
                            MHC + '.QC.markers'])  # Making '*.markers' file.
        # print(command)
        os.system(command)

        if not self.__save_intermediates:
            os.system(' '.join(['rm', MHC + '.QC.{bed,bim,fam,log}']))

        command = ' '.join(['Rscript src/excluding_snp_and_refine_target_position-v1COOK02222017.R',
                            MHC + '.QC.markers', RefinedMarkers, MHC + '.QC.pre.markers'])
        # print(command)
        os.system(command)

        if not self.__save_intermediates:
            os.system(' '.join(['rm', MHC + '.QC.markers']))

        command = ' '.join(['mv', MHC + '.QC.bgl', MHC + '.QC.pre.bgl.phased'])
        # print(command)
        os.system(command)

        command = ' '.join(
            ["awk '{print $1}'", MHC + '.QC.pre.markers', '>', os.path.join(self.OUTPUT_dir, 'selected_snp.txt')])
        # print(command)
        os.system(command)

        from src.Panel_subset import Panel_Subset
        qc_refined = Panel_Subset(MHC + '.QC.pre', 'all', join(self.OUTPUT_dir, 'selected_snp.txt'), MHC + '.QC.refined')
        # print(qc_refined) # Refined Beagle files are generated here.

        if not self.__save_intermediates:
            os.system(' '.join(['rm', MHC + '.QC.pre.{bgl.phased,markers}']))
            os.system(' '.join(['rm', join(self.OUTPUT_dir, 'selected_snp.txt')]))


        ### Converting data to GC_change_beagle format.

        from src.bgl2GC_trick_bgl import Bgl2GC

        # target
        [GCchangeBGL, GCchangeMarkers] = Bgl2GC(MHC + '.QC.refined.bgl.phased', MHC + '.QC.refined.markers',
                                                MHC + '.QC.GCchange.bgl', MHC + '.QC.GCchange.markers')
        # print("<Target GCchanged bgl and marker file>\n"
        #       "bgl : {}\n"
        #       "markers : {}".format(GCchangeBGL, GCchangeMarkers))

        # reference
        [GCchangeBGL_REF, GCchangeMarkers_REF] = Bgl2GC(_reference + '.bgl.phased', RefinedMarkers,
                                                        self.OUTPUT_dir_ref + '.GCchange.bgl.phased',
                                                        self.OUTPUT_dir_ref + '.GCchange.markers')
        # print("<Reference GCchanged bgl and marker file>\n"
        #       "bgl : {}\n"
        #       "markers : {}".format(GCchangeBGL_REF, GCchangeMarkers_REF))

        if not self.__save_intermediates:
            os.system(' '.join(['rm', MHC + '.QC.refined.{bgl.phased,markers}']))
            os.system(' '.join(['rm', RefinedMarkers]))


        ### Converting data to vcf_format

        # target
        command = ' '.join([_BEAGLE2VCF, '6', GCchangeMarkers, GCchangeBGL, '0', '>', MHC + '.QC.vcf'])
        # print(command)
        os.system(command)

        MHC_QC_VCF = MHC + '.QC.vcf'


        # reference
        command = ' '.join([_BEAGLE2VCF, '6', GCchangeMarkers_REF, GCchangeBGL_REF, '0', '>', self.OUTPUT_dir_ref + '.vcf'])
        # print(command)
        os.system(command)

        reference_vcf = self.OUTPUT_dir_ref + '.vcf'


        ### Converting data to reference_phased

        command = ' '.join(['sed "s%/%|%g"', reference_vcf, '>', self.OUTPUT_dir_ref + '.phased.vcf'])
        # print(command)
        os.system(command)

        REF_PHASED_VCF = self.OUTPUT_dir_ref + '.phased.vcf'

        if not self.__save_intermediates:
            os.system(' '.join(['rm', reference_vcf]))
            os.system(' '.join(
                ['rm', '{} {} {} {}'.format(GCchangeBGL, GCchangeMarkers, GCchangeBGL_REF, GCchangeMarkers_REF)]))

        """
        (1) MHC + '.QC.vcf', 
        (2) self.OUTPUT_dir_ref + '.phased.vcf'
        
        These two files are to be passed into Beagle phasing;
        """


        # ### Performing Phasing
        #
        # command = ' '.join([_BEAGLE4, 'gt={} ref={} out={} impute=false > {}'.format(MHC_QC_VCF, REF_PHASED_VCF, MHC+'.QC.phasing_out_not_double', MHC+'.QC.phasing_out_not_double.vcf.log')])
        # # print(command)
        #
        # if not os.system(command):
        #     if not self.__save_intermediates:
        #         os.system(' '.join(['rm', MHC_QC_VCF]))
        #         os.system(' '.join(['rm', MHC+'.QC.phasing_out_not_double.vcf.log']))
        #         os.system(' '.join(['rm', MHC+'.QC.phasing_out_not_double.log']))
        # else:
        #     print(std_ERROR_MAIN_PROCESS_NAME + "Failed to Phasing.\n"
        #                                         "Please check log file('{}')".format(MHC+'.QC.phasing_out_not_double.vcf.log'))
        #     sys.exit()
        #
        #
        # ### Target data doubling step.
        #
        # PHASED_RESULT = MHC+'.QC.phasing_out_not_double'
        #
        #
        # command = 'gzip -d -f {}'.format(PHASED_RESULT+'.vcf.gz')
        # # print(command)
        # os.system(command)
        #
        #
        # command = 'grep ^## {} > {}'.format(PHASED_RESULT+'.vcf', PHASED_RESULT+'.vcf.header')
        # # print(command)
        # os.system(command)
        #
        # command = 'grep -v ^## {} > {}'.format(PHASED_RESULT+'.vcf', PHASED_RESULT+'.vcf.body')
        # # print(command)
        # os.system(command)
        #
        #
        # from src.Doubling_vcf import Doubling_vcf
        #
        # DOUBLED_VCF_body = Doubling_vcf(PHASED_RESULT+'.vcf.body', PHASED_RESULT+'.doubled.vcf.body')
        # # print(DOUBLED_VCF_body)
        #
        #
        # command = 'cat {} {} > {}'.format(PHASED_RESULT+'.vcf.header', DOUBLED_VCF_body, PHASED_RESULT+'.doubled.vcf')
        # # print(command)
        # os.system(command)
        #
        #
        # if not self.__save_intermediates:
        #     os.system(' '.join(['rm', PHASED_RESULT+'.vcf']))
        #     os.system(' '.join(['rm', PHASED_RESULT+'.vcf.gz']))
        #     os.system(' '.join(['rm', PHASED_RESULT+'.vcf.header']))
        #     os.system(' '.join(['rm', PHASED_RESULT+'.vcf.body']))
        #     os.system(' '.join(['rm', PHASED_RESULT+'.doubled.vcf.body']))
        #
        #
        #
        # self.idx_process += 1
        # __RETURN__ = [PHASED_RESULT+'.doubled.vcf', REF_PHASED_VCF]
        #
        # return __RETURN__




    def IMPUTE(self, _out, _Doubled_VCF, _REF_PHASED_VCF, _BEAGLE4, _aver_erate=None, _Genetic_Map=None):


        print("[{}] Performing HLA imputation (see {}.MHC.QC.imputation_out.log for progress).".format(self.idx_process, _out))


        OUT = _out+'.QC.doubled.imputation_out'

        if self.f_useGeneticMap:

            ### Using both 'Multiple Markers' and 'Adaptive Genetic Map'.

            """
            java -jar beagle4.jar gt=$MHC.QC.phasing_out_double.vcf ref=$REFERENCE.phased.vcf out=$MHC.QC.double.imputation_out impute=true lowmem=true gprobs=true ne=10000 overlap=5000 err=$aver_erate map=$geneticMap.refined.map
            """

        else:

            if self.f_useMultipleMarkers:

                ### Using Multiple Markers

                """
                java -jar beagle4.jar gt=$MHC.QC.phasing_out_double.vcf ref=$REFERENCE.phased.vcf out=$MHC.QC.double.imputation_out impute=true lowmem=true 
                """

                command = '{} gt={} ref={} out={} impute=true lowmem=true'.format(_BEAGLE4, _Doubled_VCF, _REF_PHASED_VCF, OUT)
                # print(command)
                if not os.system(command):
                    if not self.__save_intermediates:
                        os.system(' '.join(['rm', OUT+'.log']))
                        os.system(' '.join(['rm', _Doubled_VCF]))
                        os.system(' '.join(['rm', _REF_PHASED_VCF]))
                else:
                    print(std_ERROR_MAIN_PROCESS_NAME + "Failed to imputation on Multiple Markers")
                    sys.exit()

            else:

                ### Using plain beagle4
                pass


        command = 'gzip -d -f {}.vcf.gz'.format(OUT)
        # print(command)
        os.system(command)

        __RETURN__ = OUT+'.vcf'

        return __RETURN__




    def getIDX_PROCESS(self):
        return self.idx_process