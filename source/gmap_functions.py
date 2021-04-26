from goto import with_goto
from generic_utils import unflatten
from fortran_utils import fort_range, fort_read, fort_write
import numpy as np

import linpack_slim
from linpack_utils import (pack_symmetric_matrix, unpack_symmetric_matrix,
                           unpack_utriang_matrix)

#
#      test option:  forced stop for testing purpose
#
def force_stop(file_IO4):
    format107 = "( '  REQUESTED STOP ' )"
    fort_write(file_IO4, format107)
    exit()


@with_goto
def read_prior(MC1, MC2, APR, LABL, IPP, file_IO3, file_IO4):
    #
    #      INPUT OF CROSS SECTIONS TO BE EVALUATED,ENERGY GRID AND APRIORI CS
    #
    #      MC1=NE      NO OF ENERGIES/PARAMETERS (total)
    #      MC2=NC      NO OF CROSS SECTION TYPES
    #      NR          NO OF PARAMETERS (cross sections)
    #
    label .lbl1
    NE = MC1
    NC = MC2
    NE1 = NE+1
    NR = 0
    for K in fort_range(1,NC):  # .lbl33
        format120 = r"(2A8)"
        LABL.CLAB[K, 1:3] = fort_read(file_IO3, format120)
        for L in fort_range(1,NE1):  # .lbl34
            format103 = "(2E10.4)"
            EX1, CSX1 = fort_read(file_IO3, format103)
            if EX1 == 0:
                goto .lbl35
            NR += 1
            APR.EN[NR] = EX1
            APR.CS[NR] = CSX1
            # label .lbl34
        L = L + 1  # to match L value of fortran after loop
        label .lbl35
        APR.MCS[K,1] = L-1
    # label .lbl33

    #
    #  MCS(k,l) CONTAINES IN l= 1 TOTAL NUMBER EACH CS
    #                           2 START BOUNDARY
    #                           3 END OF BOUNDARY
    #
    APR.MCS[1, 2] = 1
    APR.MCS[1, 3] = APR.MCS[1,1]
    for K in fort_range(2,NC):
        APR.MCS[K, 2] = APR.MCS[K-1, 2] + APR.MCS[K-1, 1]
        APR.MCS[K, 3] = APR.MCS[K-1, 3] + APR.MCS[K, 1]
    # label .lbl30
    format134 = r"(//2X,36HCROSS SECTIONS OF PRESENT EVALUATION//)" 
    fort_write(file_IO4, format134, [])
    format135 = "(10X,I3,5X,2A8)"
    for K in fort_range(1,NC):
        fort_write(file_IO4, format135, [K, LABL.CLAB[K, 1:3]])
    # label .lbl22
    if IPP[1] == 0:
        goto .lbl665
    format136 = "(1H1//,2X,35HENERGIES AND APRIORI CROSS SECTIONS//)" 
    fort_write(file_IO4, format136, [])
    format137 = "(/ '     INDEX     E/MEV   ',7X,2A8 /)"
    for  K in fort_range(1,NC):  # .lbl24
        fort_write(file_IO4, format137, LABL.CLAB[K,1:3])
        JC1 = APR.MCS[K, 2]
        JC2 = APR.MCS[K, 3]
        LQ = 0
        format138 = "(2X,2I4,3X,E10.4,3X,F15.8)"
        for L in fort_range(JC1, JC2):
            LQ += 1
            fort_write(file_IO4, format138, [LQ, L, APR.EN[L], APR.CS[L]])
            # label .lbl 23
        L = L + 1  # to match L value of fortran after loop
    # .lbl24
    K = K + 1
    label .lbl665
    format113 = "(/,' TOTAL NO OF PARAMETERS ',I4/)"
    fort_write(file_IO4, format113, [NR])

#
#      for checking
#
    if IPP[7] == 0:
        return (NC, NR)

    format4390 = "(' No of Parameters per Cross Section '/)"
    fort_write(file_IO4, format4390, [])
    format154 = "(3X,3HAPR.MCS,10I5)" 
    fort_write(file_IO4, format154, [APR.MCS[1:(NC+1), 1]])
    format4391 = "(/' Start Address '/)"
    fort_write(file_IO4, format4391, [])
    fort_write(file_IO4, format154, [APR.MCS[1:(NC+1), 2]])
    format4392 = "(/' End Address '/)"
    fort_write(file_IO4, format4392, [])
    fort_write(file_IO4, format154, [APR.MCS[1:(NC+1), 3]])
    return (NC, NR)


@with_goto
def read_block_input(data, gauss, LDA, LDB, KA, KAS, MODREP, file_IO4):
    #
    #      BLOCK INPUT
    #
    #      N     TOTAL NO OF DATA POINTS IN BLOCK
    #      ID    TOTAL NO OF DATA SETS IN BLOCK
    #

    N = 0
    ID = 0
    for K in fort_range(1,LDA):  # .lbl32
        gauss.AM[K] = 0.
        for I in fort_range(1,LDB):  # .lbl81
            # VP line with BM(I)=0.D0  was commented because BM(I) cleaning should 
            # VP done outside of the cycle on measured data 
            # VPBEG*****************************************************************
            # VP      BM(I)=0.D0
            # VPEND*****************************************************************
            KA[I,K] = 0
            gauss.AA[I,K] = 0.
            # .lbl81
        for J in fort_range(1,5):
            KAS[K, J] = 0
        for L in fort_range(1,LDA):
            data.ECOR[K,L] = 0.
        L = L + 1  # to match L value of fortran after loop
        # .lbl32
    NADD = 1
    if MODREP != 0:
        return (ID, N, NADD)   
    format108 = "(/' DATABLOCK************************DATABLOCK**************" + \
                "******************************************DATABLOCK '/)"
    fort_write(file_IO4, format108, [])
    return (ID, N, NADD)


@with_goto
def read_dataset_input(MC1, MC2, MC3, MC4, MC5, MC6, MC7, MC8,
        data, LABL, IDEN, NENF, NETG, NCSST, NEC, NT,
        ID, N, file_IO3, file_IO4):
    #
    #      DATA SET INPUT
    #
    #      MC1 NS      DATA SET NO
    #      MC2 MT      TYPE OF MEASUREMENT
    #      MC3 NCOX    CORRELATION MATRIX GIVEN IF .NE. 0
    #      MC4 NCT     NO OF CROSS SECTIONS INVOLVED
    #      MC5 NT(1)   CROSS SECTION IDENTIFICATION
    #      MC6 NT(2)   SAME
    #      MC7 NT(3)   SAME
    #      MC8 NNCOX   DIVIDE UNCERTAINTIES BY 10.
    #
    # label .lbl2
    NS = MC1
    MT = MC2
    NCOX = MC3
    NCT = MC4
    NT[1] = MC5
    NT[2] = MC6
    NT[3] = MC7
    NNCOX = MC8
    format123 = "(16I5)"
    if NCT > 3:
        NT[4:(NCT+1)] = fort_read(file_IO3, format123)
        L = NCT + 1  # to match L value of fortran after READ loop
    ID = ID+1
    IDEN[ID,2] = N+1
    IDEN[ID,6] = NS
    IDEN[ID,7] = MT
    #
    #       identify absolute or shape data
    #
    MTTP = 1
    IDEN[ID, 8] = 1
    if MT == 2 or MT == 4:
        goto .lbl510
    if MT == 8 or MT == 9:
        goto .lbl510
    goto .lbl511

    label .lbl510

    MTTP = 2
    IDEN[ID, 8] = 2

    label .lbl511

    # VP      if(modrep .ne. 0) go to 140
    format142 = "(//, ' ***********DATASET**************************** '/)"
    fort_write(file_IO4, format142, [])
    NU = NCT
    if NCT > 4:
        NU = 4
    NCT2 = NCT - NU
    NU1 = NU + 1
    format139 = "(2X,8HDATA SET,I5,2X,A16,4(2X,2A8))"
    tmp = [[LABL.CLAB[NT[K],L] for L in fort_range(1,2)] for K in fort_range(1,NU)]
    L = 3  # to reflect value of L after loop in Fortran
           # because L in list comprehension goes immediately out of scope
    fort_write(file_IO4, format139, [MC1, LABL.TYPE[MT],tmp])
    if NCT2 <= 0:
        goto .lbl140

    format149 = "(2X,6(2X,2A8))"
    tmp = [[LABL.CLAB[NT[K],L] for L in fort_range(1,2)] for K in fort_range(NU1,NCT2)]
    L = 3  # to reflect value of L after loop in Fortran
           # because L in list comprehension goes immediately out of scope
    fort_write(file_IO4, format149, tmp)

    label .lbl140

    #
    #       NAME ID AND REFERENCE I/O
    #
    format131 = "(3I5,4A8,4A8)"
    format132 = "(/' YEAR',I5,' TAG',I3,' AUTHOR:  ',4A8,4A8/)"
    IDEN[ID,3:6], LABL.CLABL[1:5], LABL.BREF[1:5] = unflatten(fort_read(file_IO3, format131), [[3],[4],[4]])
    fort_write(None, format132, [IDEN[ID, 3:5], LABL.CLABL[1:5], LABL.BREF[1:5]])
    # VP      if(modrep .ne. 0) go to 183
    fort_write(file_IO4, format132, [IDEN[ID, 3:5], LABL.CLABL[1:5], LABL.BREF[1:5]])

    label .lbl183
    NCCS = IDEN[ID, 5]
    #
    #       READ(3,    ) NORMALIZATION UNCERTAINTIES
    #
    XNORU = 0.
    if MTTP == 2:
        goto .lbl200

    format201 = "(10F5.1,10I3)"
    data.ENFF[ID, 1:11], NENF[ID, 1:11] = unflatten(fort_read(file_IO3, format201), [[10],[10]])

    #
    #       CALCULATE TOTAL NORMALIZATION UNCERTAINTY
    #
    for L in fort_range(1,10):  # .lbl208
        XNORU = XNORU + (data.ENFF[ID,L])**2
    L = L + 1  # to match L value of fortran after loop

    label .lbl200
    #
    #       READ(3,    ) ENERGY DEPENDENT UNCERTAINTY PARAMETERS
    #
    format202 = "(3F5.2,I3)"
    for K in fort_range(1,11):
        data.EPAF[1:4, K, ID], NETG[K, ID] = unflatten(fort_read(file_IO3, format202), [[3], 1])
    #
    #       READ(3,    ) CORRELATIONS INFORMATION
    #
    if NCCS == 0:
        #goto .lbl203
        return (MT, NCT, NS, NCOX, NNCOX, XNORU, NCCS, MTTP, ID, IDEN)

    format841 = "(10F5.1)"
    format205 = "(I5,20I3)"
    for K in fort_range(1,NCCS):  # .lbl204
        NCSST[K], tmp = unflatten(fort_read(file_IO3, format205), [1,[20]])
        NEC[1:3, 1:11, K] = np.reshape(tmp, (2,10), order='F')
        #NCSST[K], NEC[0:2, 0:10, K] = unflatten(fort_read(file_IO3, format205), [1,[20]])
        data.FCFC[1:11, K] = fort_read(file_IO3, format841)
    return (MT, NCT, NS, NCOX, NNCOX, XNORU, NCCS, MTTP, ID, IDEN)



@with_goto
def accounting(data, APR, MT, NT, NCT,
        KAS, NS, NADD, LDA, NNCOX, MOD2, XNORU, file_IO3):
    #
    #      ACCOUNTING
    #
    #      N,NADD      NO OF TOTAL DATA POINTS SO FAR IN BLOCK
    #      ID          NO OF EXPERIMENTAL DATA SETS
    #      NP          NO OF DATA POINTS IN THIS SET
    #
    NALT = NADD

    for KS in fort_range(1,LDA):  # .lbl21

        format109 = "(2E10.4,12F5.1)"
        data.E[NADD], data.CSS[NADD], data.CO[1:13, NADD] = unflatten(fort_read(file_IO3, format109), [2,[12]])
        L = 13  # to reflect fortran value after READ loop
        if data.E[NADD] == 0:
            return (NALT, L, NADD)
            #goto .lbl95

        #
        #      SORT EXP ENERGIES  TO FIND CORRESPONDING INDEX OF EVALUATION EN
        #
        #      KAS(I,L)   GIVES INDEX OF EVALUATION ENERGY FOR I.TH EXP POINT
        #                 AND L.TH CROSS SECTION
        #
        if MT == 6:
            goto .lbl70

        #
        #      NCT is the number of cross sections involved
        #
        for L in fort_range(1,NCT):  # .lbl48
            JE = APR.MCS[NT[L], 2]
            JI = APR.MCS[NT[L], 3]

            for K in fort_range(JE, JI):  # .lbl12
                E1 = .999*APR.EN[K]
                E2 = 1.001*APR.EN[K]
                if data.E[NADD] > E1 and data.E[NADD] < E2:
                    goto .lbl75
            # .lbl12
            goto .lbl15
            label .lbl75
            KAS[NADD, L] = K
            #
            #      Exception for dummy data sets
            #
            if NS >= 900 and NS <= 909:
                data.CSS[NADD] = APR.CS[K]
            # .lbl48
        L = L + 1  # to match L value of fortran after loop

        #
        #      this is the Axton special (uncertainties have been multiplied by 10
        #         in order to preserve precision beyond 0.1%)
        #
        label .lbl70
        if NNCOX == 0:
            goto .lbl59
        for LZ in fort_range(1,11):  # .lbl57
            data.CO[LZ, NADD] = data.CO[LZ, NADD] / 10.

        label .lbl59

        #
        #      test option:  as set with mode control
        #
        #      changing weights of data based on year or data set tag
        #
        if MOD2 == 0:
            goto .lbl320
        if MOD2 > 1000:
            goto .lbl321
        if MOD2 == 10:
            goto .lbl322
        if MOD2 > 10:
            goto .lbl320

        # replaces computed goto
        if MOD2 == 1:
            goto .lbl331
        if MOD2 > 1 and MOD2 < 10:
            goto .lbl336

        label .lbl331

        #
        #      downweighting data sets with tags .NE. 1
        #
        if IDEN[ID,4] == 1:
            goto .lbl320

        label .lbl342
        for I in fort_range(3,11):
            data.CO[I, NADD] = AMO3*data.CO[I, NADD]

        goto .lbl320

        #
        #      downweighting based on year of measurement
        #
        label .lbl321
        if IDEN[ID, 3] < MOD2:
            goto .lbl342

        goto .lbl320

        label .lbl322
        #
        #      downweighting of specified data sets
        #
        for IST in fort_range(1,NELI): # .lbl391
            if IDEN[ID, 6] == NRED[IST]:
                goto .lbl342

        label .lbl391
        goto .lbl320

        label .lbl336
        format339 = "('  WEIGHTING OPTION NOT IMPLEMENTED, DATA SET  ',I5/)" 
        fort_write(file_IO4, format339, NS)

        label .lbl320
        #
        #      CALCULATE TOTAL UNCERTAINTY  DCS
        #
        RELU = 0.
        for L in fort_range(3,11):  # .lbl207
            RELU += data.CO[L, NADD]**2
        L = L + 1  # to match L value of fortran after loop

        data.DCS[NADD] = np.sqrt(XNORU + RELU) 
        NADD += 1

        label .lbl15
    label .lbl21
    return (NALT, L, NADD)



@with_goto
def should_exclude_dataset(NS, IELIM, NELIM, MTTP, ID, NADD, NALT, file_IO4): 

    NP = NADD - NALT
    if IELIM == 0:
        goto .lbl173
    #
    #      data set excluded ?
    #
    for K in fort_range(1,IELIM):
        if NS == NELIM[K]:
            goto .lbl517

    label .lbl172
    #
    #      NO VALID DATA POINTS OR SET REQUESTED TO BE EXCLUDED
    #
    label .lbl173
    if NP == 1 and MTTP == 2:
        goto .lbl517

    if NP != 0:
        return (False, NP, ID, NADD)

    label .lbl517
    format168 = "(' SET ',I5,' W/O VALID POINTS OR ELIMINATED'/)"
    fort_write(file_IO4, format168, [NS])
    ID = ID - 1
    NADD = NALT
    return (True, NP, ID, NADD)



@with_goto
def construct_Ecor(data, NETG, IDEN, NCSST, NEC,
        L, MODC, NCOX, NALT, NP, NADD1, ID,
        XNORU, NCCS, MTTP, NS, file_IO3, file_IO4):
    #
    #      CONSTRUCT ECOR
    #
    #         MODE  1   INPUT OF ECOR
    #               2   UNCORRELATED
    #               3   ALL CORRELATED ERRORS GIVEN
    #
    if NCOX == 0:
        goto .lbl5001
    MODAL = MODC
    MODC = 1

    label .lbl5001
    if MODC == 1:
        goto .lbl54
    elif MODC == 2:
        goto .lbl1779
    elif MODC >= 3 and MODC <= 6:
        goto .lbl56
    #
    #      INPUT OF ECOR
    #
    label .lbl54
    format161 = "(10F8.5)"
    for KS in fort_range(1,NCOX):  # .lbl61
        num_el_read = 0
        num_el_desired = KS
        res = []
        while num_el_read < num_el_desired:
            tmp = fort_read(file_IO3, format161)
            tmp = [x for x in tmp if x is not None]
            res += tmp
            num_el_read += len(tmp)

        data.ECOR[KS,1:(KS+1)] = res
    KS = KS + 1  # to match the value of KS after Fortran loop
    L = KS  # to match the value of L after READ (label 61 in Fortran code)


    MODC = MODAL
    goto .lbl79


    #
    #       CONSTRUCT ECOR FROM UNCERTAINTY COMPONENTS
    #
    label .lbl56
    data.ECOR[NALT, NALT] = 1.
    if NP == 1:
        goto .lbl1789
    NALT1 = NALT + 1
    for KS in fort_range(NALT1, NADD1):  # .lbl62
        C1 = data.DCS[KS]
        KS1 = KS - 1

        for KT in fort_range(NALT, KS1):  # .lbl162
            Q1 = 0.
            C2 = data.DCS[KT]
            for L in fort_range(3,11):  # .lbl215
                if NETG[L, ID] == 9:
                    goto .lbl214
                if NETG[L, ID] == 0:
                    goto .lbl214

                FKS = data.EPAF[1,L,ID] + data.EPAF[2,L,ID]
                XYY = data.EPAF[2,L,ID] - (data.E[KS]-data.E[KT])/(data.EPAF[3,L,ID]*data.E[KS])
                if XYY < 0.:
                    XYY = 0.
                FKT = data.EPAF[1, L, ID] + XYY
                Q1=Q1+data.CO[L,KS]*data.CO[L,KT]*FKS*FKT

                label .lbl214
                label .lbl215
            L = L + 1  # to match L value of fortran after loop
            CERR = (Q1 + XNORU) / (C1*C2)

            if CERR > .99:
                CERR = .99
            # limit accuracy of comparison to reflect
            # Fortran behavior

            label .lbl162
            data.ECOR[KS,KT] = CERR

        data.ECOR[KS, KS] = 1.
    label .lbl62

    #
    #   ADD CROSS CORRELATIONS OF EXPERIMENTAL DATA BLOCK
    #
    label .lbl1789
    if ID == 1:
        goto .lbl79
    if NCCS == 0:
        goto .lbl79
    ID1 = ID - 1
    
    for I in fort_range(1,NCCS):  # .lbl271

        NSET = NCSST[I]
        for II in fort_range(1,ID1):  # .lbl272
            if IDEN[II,6] == NSET:
                goto .lbl273
        #
        #   CORRELATED DATA SET NOT FOUND AHEAD OF PRESENT DATA
        #   SET WITHIN DATA BLOCK
        #
        format274 = "('CORRELATED DATA SET  ',I5,' NOT FOUND FOR SET ',I5)" 
        fort_write(file_IO4, format274, [NSET, NS])
        goto .lbl275

        label .lbl273
        NCPP = IDEN[II, 1]
        #
        #      cross correlation
        #
        MTT = IDEN[II, 8]
        if MTT == 2 and NP == 1:
            goto .lbl275
        if MTTP == 2 and NCPP == 1:
            goto .lbl275

        label .lbl469
        NCST = IDEN[II, 2]
        NCED = NCPP + NCST - 1
        for K in fort_range(NALT, NADD1):  # .lbl278
            C1 = data.DCS[K]
            for KK in fort_range(NCST, NCED):  # .lbl279
                C2 = data.DCS[KK]
                Q1 = 0.
                for KKK in fort_range(1,10):  # .lbl281
                    NC1 = NEC[1, KKK, I]
                    NC2 = NEC[2, KKK, I]
                    if NC1 > 21 or NC2 > 21:
                        goto .lbl2811
                    if NC1 == 0:
                        goto .lbl2753
                    if NC2 == 0:
                        goto .lbl2753
                    AMUFA = data.FCFC[KKK, I]
                    if NC1 > 10:
                        goto .lbl310
                    C11 = data.ENFF[ID, NC1]
                    goto .lbl311

                    label .lbl310
                    NC1 = NC1 - 10
                    if NETG[NC1, ID] == 9:
                        goto .lbl2800
                    FKT = data.EPAF[1, NC1, ID] + data.EPAF[2, NC1, ID]
                    goto .lbl2801

                    label .lbl2800
                    FKT = 1.
                    label .lbl2801

                    C11 = FKT*data.CO[NC1, K]

                    label .lbl311
                    if NC2 > 10:
                        goto .lbl312
                    C22 = data.ENFF[II, NC2]
                    goto .lbl313

                    label .lbl312
                    NC2 = NC2 - 10

                    if NETG[NC2, II] == 9:
                        goto .lbl2802

                    XYY = data.EPAF[2,NC2,II] - np.abs(data.E[K]-data.E[KK])/ (data.EPAF[3,NC2,II]*data.E[KK])
                    if XYY < 0.:
                        XYY = 0.
                    FKS = data.EPAF[1, NC2, II] + XYY
                    goto .lbl2803

                    label .lbl2802
                    FKS = 1.

                    label .lbl2803
                    C22 = FKS * data.CO[NC2, KK]

                    label .lbl313
                    Q1 = Q1 + AMUFA*C11*C22

                    label .lbl2811
                label .lbl281
                label .lbl2753
                data.ECOR[K,KK] = Q1/(C1*C2)

            label .lbl279
        label .lbl278
        label .lbl275
    label .lbl271

    goto .lbl79

    #
    #       UNCORRELATED OR SINGLE VALUE
    #
    label .lbl1779
    for KLK in fort_range(NALT, NADD1):  # .lbl74
        data.ECOR[KLK,KLK] = 1.

    label .lbl79
    return (MODC, L)



@with_goto
def determine_apriori_norm_shape(data, APR, KAS, LABL, NSETN,
        MT, L, NSHP, MTTP, MPPP, IPP, NS, NR, NALT, NADD1,
        MODREP, LDB, MC1, NCT, file_IO4):
    #
    #      DETERMINE APRIORI NORMALIZATION FOR SHAPE MEASUREMENTS
    #
    if MTTP == 1:
        goto .lbl2828

    NSHP = NSHP + 1
    NSETN[NSHP] = NS
    L = NR + NSHP
    if L > LDB:
        format701 = "( '   OVERFLOW OF UNKNOWN-VECTOR SPACE WITH SET  ',I3)"
        fort_write(file_IO4, format701, [MC1])
        exit()

    label .lbl2828
    #VP   PRIOR/EXP column is added
    format5173 = "(/'  ENERGY/MEV   VALUE    ABS. UNCERT. " + \
                 " PRIOR/EXP UNCERT./%    DIFF./%" + \
                 "  VAL.*SQRT(E)'/)"
    fort_write(file_IO4, format5173, [])
    AP = 0.
    WWT = 0.
    for K in fort_range(NALT, NADD1):  # .lbl29
        CSSK = data.CSS[K]
        DCSK = data.DCS[K]
        WXX = 1./(DCSK*DCSK)
        WWT = WWT + WXX

        label .lbl97
        KX = KAS[K, 1]
        KY=KAS[K,2]
        KZ=KAS[K, 3]
        AX = APR.CS[KX]
        if MT == 4 or MT == 3:
            AX = AX / APR.CS[KY]
        if MT == 8 or MT == 5:
            AX = AX + APR.CS[KY]
        if MT == 5 and NCT == 3:
            AX = AX + APR.CS[KZ]
        if MT == 8 and NCT == 3:
            AX = AX + APR.CS[KZ]
        if MT == 9 or MT == 7:
            AX = AX/(APR.CS[KY]+APR.CS[KZ])

        AZ = AX / CSSK

        #VPBEG Assigning uncertainties as % error relative the prior
        if MPPP == 1:
            data.DCS[K] = AZ*data.DCS[K]
        #VPEND 
        #
        #      DATA OUTPUT
        #
        if IPP[2] == 0:
            goto .lbl99

        SECS = np.sqrt(data.E[K])*CSSK
        FDQ = DCSK * CSSK/100.
        DIFF = (CSSK-AX)*100./AX
        #VP   AZ print out was added
        format133 = "(2X,E10.4,2X,E10.4,2X,E10.4,3X,F6.4,3X,F6.2," + \
                    " 3X,F10.2,3X,F10.4)"
        fort_write(file_IO4, format133, [data.E[K], CSSK, FDQ, AZ, DCSK, DIFF, SECS])
        #VP   Print out for Ratio of pior/exp value is added
        label .lbl99
        #
        AP=AP+AZ*WXX
    label .lbl29  # end for loop


    AP=AP/WWT
    # VP      if(modrep .ne. 0) go to 2627
    format111 = "(/' APRIORI NORM ',I4,F10.4,I5,2X,4A8)"
    fort_write(file_IO4, format111, [L, AP, NS, LABL.CLABL[1:5]])
    label .lbl2627
    if MTTP == 2:
        goto .lbl2826

    goto .lbl28a

    label .lbl2826
    if MODREP != 0:
        goto .lbl63

    AP = 1.0 / AP
    APR.CS[L] = AP
    goto .lbl28a

    label .lbl63
    AP=APR.CS[L]

    label .lbl28a
    return (NSHP, L, AP)



@with_goto
def fill_AA_AM_COV(data, APR, gauss, AP, KAS, KA, N, L, EAVR, NT, NCT, MT, NALT, NADD1, file_IO4):
    #
    #      FILL AA,AM,AND COV
    #
    for KS in fort_range(NALT, NADD1):  # .lbl18
        DQQQ = data.DCS[KS]*data.CSS[KS]*0.01
        J = KAS[KS,1]
        I = KAS[KS,2]
        I8 = KAS[KS,3]
        if J == 0 and MT != 6:
            goto .lbl89
        if I != 0:
            goto .lbl148
        if MT == 3:
            goto .lbl89
        if MT == 5:
            goto .lbl89
        if MT == 4:
            goto .lbl89
        if MT == 7:
            goto .lbl89
        if MT == 8:
            goto .lbl89
        if MT == 9:
            goto .lbl89

        label .lbl148
        if I8 != 0:
            goto .lbl147
        if MT == 7:
            goto .lbl89
        if MT == 9:
            goto .lbl89

        label .lbl147
        N = N + 1

        if MT == 6:
            goto .lbl46
        if MT == 5:
            goto .lbl45
        if MT == 8:
            goto .lbl248

        KA[J,1] = KA[J,1] + 1
        KR = KA[J,1]
        KA[J,KR+1] = N

        if MT == 1:
            goto .lbl41
        if MT == 2:
            goto .lbl42
        if MT == 3:
            goto .lbl43
        if MT == 4:
            goto .lbl44
        if MT == 5:
            goto .lbl446
        if MT == 6:
            goto .lbl446
        if MT == 7:
            goto .lbl247
        if MT == 8:
            goto .lbl446
        if MT == 9:
            goto .lbl249

        label .lbl446
        format447 = "(10H ERROR 446)"
        fort_write(file_IO4, format447, [])
        exit()
        #
        #      CROSS SECTION
        #
        label .lbl41
        CX = APR.CS[J]
        gauss.AA[J,KR] = CX / DQQQ
        goto .lbl36

        #
        #      CROSS SECTION SHAPE    L is shape data norm. const. index
        #
        label .lbl42
        CX = APR.CS[J]*AP
        CXX = CX/DQQQ
        gauss.AA[J,KR] = CXX
        KA[L,1] = KA[L,1]+1
        KR = KA[L,1]
        KA[L,KR+1] = N
        gauss.AA[L,KR] =  CXX
        goto .lbl36
        #
        #      RATIO
        #
        label .lbl43
        CX = APR.CS[J]/APR.CS[I]
        CCX = CX/DQQQ
        gauss.AA[J,KR] = CCX
        KA[I,1] = KA[I,1]+1
        KR = KA[I,1]
        KA[I,KR+1] = N
        gauss.AA[I,KR] = -CCX
        goto .lbl36
        #
        #      RATIO SHAPE
        #
        label .lbl44
        CX = APR.CS[J]*AP/APR.CS[I]
        CXX = CX/DQQQ
        gauss.AA[J,KR] = CXX
        KA[I,1] = KA[I,1]+1
        KR = KA[I,1]
        KA[I,KR+1] = N
        gauss.AA[I,KR] = -CXX
        KA[L,1] = KA[L,1]+1
        KR = KA[L,1]
        KA[L,KR+1] = N
        gauss.AA[L,KR] =  CXX
        goto .lbl36
        #
        #      TOTAL CROSS SECTION
        #
        label .lbl45
        CX = 0.
        for I in fort_range(1,NCT):  # .lbl49
            II = KAS[KS,I]
            CX = CX+APR.CS[II]


        for I in fort_range(1,NCT):  # .lbl60
            J  = KAS[KS,I]
            KA[J,1] = KA[J,1]+1
            KR = KA[J,1]
            KA[J,KR+1] = N
            gauss.AA[J,KR] = APR.CS[J]/DQQQ

        goto .lbl36

        #
        #      FISSION AVERAGE
        #
        label .lbl46
        K = 0
        if NT[1] == 9:
            K = 1
        JA = APR.MCS[NT[1],2]
        JE = APR.MCS[NT[1],3]
        NW1=1
        if NT[1] == 9:
            NW1 = 2
        NW=NW1
        FL=0.
        SFL=0.
        J1=JA+1
        J2=JE-1

        for LI in fort_range(J1, J2):  # .lbl53
            NW=NW+1
            FL=FL+data.FIS[NW]
            EL1=(APR.EN[LI]+APR.EN[LI-1])*0.5
            EL2=(APR.EN[LI]+APR.EN[LI+1])*0.5
            DE1=(APR.EN[LI]-EL1)*0.5
            DE2=(EL2-APR.EN[LI])*0.5
            SS1=.5*(APR.CS[LI]+0.5*(APR.CS[LI]+APR.CS[LI-1]))
            SS2=.5*(APR.CS[LI]+0.5*(APR.CS[LI]+APR.CS[LI+1]))
            CSSLI=(SS1*DE1+SS2*DE2)/(DE1+DE2)
            SFL=SFL+CSSLI*data.FIS[NW]

        FL=FL+data.FIS[1]+data.FIS[NW+1]
        SFL=SFL+data.FIS[1]*APR.CS[JA]+data.FIS[NW+1]*APR.CS[JE]
        SFIS=SFL/FL
        format156 = "( 'AP FISSION AVERAGE ',3F10.4,'  EXP. VAL. ',2F10.4)"
        fort_write(file_IO4, format156, [EAVR, SFIS, FL, data.CSS[KS], data.DCS[KS]])
        CX=SFIS
        for J in fort_range(JA, JE):  # .lbl39
            K=K+1
            KA[J,1]=KA[J,1]+1
            KR=KA[J,1]
            KA[J,KR+1]=N
            if J == JA or J == JE:
                goto .lbl195
            EL1=(APR.EN[J]+APR.EN[J-1])*0.5
            EL2=(APR.EN[J]+APR.EN[J+1])*0.5
            DE1=(APR.EN[J]-EL1)*0.5
            DE2=(EL2-APR.EN[J])*0.5
            SS1=.5*(APR.CS[J]+0.5*(APR.CS[J]+APR.CS[J-1]))
            SS2=.5*(APR.CS[J]+0.5*(APR.CS[J]+APR.CS[J+1]))
            CSSJ=(SS1*DE1+SS2*DE2)/(DE1+DE2)
            goto .lbl196
            label .lbl195
            CSSJ = APR.CS[J]
            label .lbl196

            gauss.AA[J,KR]=CSSJ*data.FIS[K]/DQQQ

        goto .lbl36

        #
        #   ABSOLUTE RATIO S1/(S2+S3)
        #
        label .lbl247
        CX=APR.CS[J]/(APR.CS[I]+APR.CS[I8])
        if I == J:
            goto .lbl251
        CBX=CX/DQQQ
        gauss.AA[J,KR]=CBX
        KA[I,1]=KA[I,1]+1
        KR=KA[I,1]
        KA[I,KR+1]=N
        CBX2=CBX*CBX*DQQQ/APR.CS[J]
        CCX=CBX2*APR.CS[I]
        gauss.AA[I,KR]=-CCX
        KA[I8,1]=KA[I8,1]+1
        KR=KA[I8,1]
        KA[I8,KR+1]=N
        CCX=CBX2*APR.CS[I8]
        gauss.AA[I8,KR]=-CCX
        goto .lbl36

        label .lbl251
        CBX=CX*CX*APR.CS[I8]/(APR.CS[J]*DQQQ)
        gauss.AA[J,KR]=CBX
        KA[I8,1]=KA[I8,1]+1
        KR=KA[I8,1]
        KA[I8,KR+1]=N
        gauss.AA[I8,KR]=-CBX
        goto .lbl36
        #
        #   SHAPE OF SUM
        #
        label .lbl248
        CX = 0.
        for I in fort_range(1,NCT):  # .lbl253
            II=KAS[KS,I]
            CX=CX+APR.CS[II]*AP

        APDQ=AP/DQQQ
        for I in fort_range(1,NCT):  # .lbl254
            J=KAS[KS,I]
            KA[J,1]=KA[J,1]+1
            KR=KA[J,1]
            KA[J,KR+1]=N
            gauss.AA[J,KR]=APR.CS[J]*APDQ

        KA[L,1]=KA[L,1]+1
        KR=KA[L,1]
        KA[L,KR+1]=N
        gauss.AA[L,KR]=CX/DQQQ
        goto .lbl36

        #
        #   SHAPE OF RATIO S1/(S2+S3)
        #
        label .lbl249
        CII8=APR.CS[I]+APR.CS[I8]
        CX=AP*APR.CS[J]/CII8
        CBX=CX/DQQQ
        if I == J:
            goto .lbl390

        gauss.AA[J,KR]=CBX
        KA[I,1]=KA[I,1]+1
        KR=KA[I,1]
        KA[I,KR+1]=N
        CDX=CBX*APR.CS[I]/CII8
        gauss.AA[I,KR]=-CDX
        KA[I8,1]=KA[I8,1]+1
        KR=KA[I8,1]
        KA[I8,KR+1]=N
        CDX=CBX*APR.CS[I8]/CII8
        gauss.AA[I8,KR]=-CDX
        KA[L,1]=KA[L,1]+1
        KR=KA[L,1]
        KA[L,KR+1]=N
        gauss.AA[L,KR]=CBX
        goto .lbl36

        label .lbl390
        CCX=CBX*APR.CS[I8]/CII8
        gauss.AA[J,KR]=CCX
        KA[I8,1]=KA[I8,1]+1
        KR=KA[I8,1]
        KA[I8,KR+1]=N
        gauss.AA[I8,KR]=-CCX
        KA[L,1]=KA[L,1]+1
        KR=KA[L,1]
        KA[L,KR+1]=N
        gauss.AA[L,KR]=CBX
        goto .lbl36

        label .lbl36
        gauss.AM[N]=(data.CSS[KS]-CX)/DQQQ
        goto .lbl667

        label .lbl89
        format704 = "( '  DATA POINT BUT NOT AN AP FOR SET ',I5,' NO ',I4)"
        fort_write(file_IO4, format704, [MC1, KS])

        label .lbl667
    label .lbl18  # end of for loop
    return N



def complete_symmetric_Ecor(data, MODC, N, N1, file_IO4):
    #
    #      FILL IN SYMMETRIC TERM
    #
    format2830 = "(80X,4HN = ,I5)"
    fort_write(file_IO4, format2830, [N])
    for K in fort_range(1,N1):  # .lbl25
        K1 = K + 1
        for L in fort_range(K1, N):  # .lbl25
            if MODC == 2:
                data.ECOR[L, K] = 0.
            data.ECOR[K, L] = data.ECOR[L, K]
            # label .lbl25
        L = L + 1  # to match L value of fortran after loop



def output_Ecor_matrix(data, N, file_IO4):
    #
    #      output of correlation matrix of data block
    #
    format101 = "(1H*//,'   CORRELATION MATRIX OF DATA BLOCK'/)"
    fort_write(file_IO4, format101, [])
    format151 = "(1X,24F7.4)"
    for K in fort_range(1,N):
        fort_write(file_IO4, format151, [data.ECOR[K,1:(K+1)]])



@with_goto
def invert_Ecor(data, N, IPP, MODC, IREP, file_IO4):
    #
    #      INVERT ECOR
    #

    while True:
        # cholesky decomposition
        #CALL DPOFA(ECOR,LDA,N,INFO)
        INFO = np.array(0)
        tmp = np.array(data.ECOR[1:(N+1),1:(N+1)], dtype='float64', order='F')
        linpack_slim.dpofa(a=tmp, info=INFO) 
        data.ECOR[1:(N+1),1:(N+1)] = tmp

        # ALTERNATIVE USING NUMPY FUNCTION cholesky
        # INFO = 0
        # try:
        #     data.ECOR[1:(N+1),1:(N+1)] = cholesky(data.ECOR[1:(N+1), 1:(N+1)]).T 
        # except np.linalg.LinAlgError:
        #     INFO = 1

        if INFO == 0:
            break
        else:
            #
            #      ATTEMPT TO MAKE CORR. MATRIX POSITIVE DEFINITE
            #
            format105 = "(/' EXP BLOCK CORREL. MATRIX NOT PD',20X,'***** WARNING *')" 
            fort_write(file_IO4, format105, [])
            IREP=IREP+1
            N1=N-1
            for K in fort_range(1,N1):  # .lbl2211
                K1=K+1
                for L in fort_range(K1, N):  # .lbl2211
                    if MODC == 2:
                        data.ECOR[L,K] = 0.
                    data.ECOR[K,L] = data.ECOR[L,K]
            label .lbl2211
            for K in fort_range(1,N):  # .lbl2212
                data.ECOR[K,K] = 1.

            CXZ=0.10
            for K in fort_range(1,N):  # .lbl37
                for L in fort_range(1,N):
                    data.ECOR[K,L]=data.ECOR[K,L]/(1.+CXZ)
                    if K == L:
                        data.ECOR[K,L] = 1.
            label .lbl37
            if IREP >= 15:
                return (False, IREP)

    JOB=1
    # CALL DPODI(ECOR,LDA,N,DET,JOB)
    tmp = np.array(data.ECOR[1:(N+1),1:(N+1)], dtype='float64', order='F')
    tmp_det = np.array([0., 0.], dtype='float64', order='F') 
    linpack_slim.dpodi(tmp, det=tmp_det, job=JOB)
    data.ECOR[1:(N+1),1:(N+1)] = tmp

    # ALTERNATIVE USING NUMPY inv function
    # tmp = inv(data.ECOR[1:(N+1),1:(N+1)])
    # data.ECOR[1:(N+1),1:(N+1)] = np.matmul(tmp.T, tmp)

    for K in fort_range(2,N):  # .lbl17
        L1=K-1
        for L in fort_range(1,L1):
            data.ECOR[K,L] = data.ECOR[L,K]
        L = L + 1  # to match L value of fortran after loop
    #
    #      output of inverted correlation matrix of data block
    #
    if IPP[5] == 0:
        goto .lbl19

    format151 = "(1X,24F7.4)"
    for K in fort_range(1,N):
        fort_write(file_IO4, format151, [data.ECOR[K,1:(K+1)]])

    label .lbl19
    return (True, IREP)



@with_goto
def get_matrix_products(gauss, data, N, LDA, LDB, MODREP,
        NR, NSHP, KA, NTOT, SIGMA2, file_IO4):
    #
    #      GET MATRIX PRODUCTS
    #
    NRS=NR+NSHP
    for I in fort_range(1,NRS):  # .lbl90
        NI=KA[I,1]
        if NI == 0:
            goto .lbl92

        for J in fort_range(I, NRS):  # .lbl83
            NJ=KA[J,1]
            if NJ == 0:
                goto .lbl84
            IJ=J*(J-1)//2+I

            for MI in fort_range(1,NI):  # .lbl85
                MIX=KA[I,MI+1]
                for MJ in fort_range(1,NJ):  # .lbl85
                    MJX=KA[J,MJ+1]
                    gauss.B[IJ]=gauss.B[IJ]+gauss.AA[I,MI]*gauss.AA[J,MJ]*data.ECOR[MIX,MJX]
                    
                label .lbl85

            label .lbl84
        label .lbl83
        label .lbl92
    label .lbl90

    for I in fort_range(1,NRS):  # .lbl91
        NI=KA[I,1]
        if NI == 0:
            goto .lbl93

        for MI in fort_range(1,NI):  # .lbl86
            MIX=KA[I,MI+1]
            for MJ in fort_range(1,N):  #.lbl86
                gauss.BM[I]=gauss.BM[I]+gauss.AA[I,MI]*data.ECOR[MIX,MJ]*gauss.AM[MJ]

        label .lbl93
    label .lbl91

    for I in fort_range(1,N):  # .lbl26
        SUX=0.
        for J in fort_range(1,N):  # .lbl52
            SUX=SUX+data.ECOR[I,J]*gauss.AM[J]
        
        SIGMA2=SIGMA2+gauss.AM[I]*SUX
    label .lbl26

    NTOT=NTOT+N
    SIGL=SIGMA2/NTOT
    format476 = "(/' ADDED ',I5,' TO GIVE ',I5,' TOTAL',2I5,F10.2/)"
    fort_write(None, format476, [N, NTOT, NSHP, NRS, SIGL])
    if N > LDA:
        exit()
    if NRS > LDB:
        exit()
    if MODREP == 0:
        fort_write(file_IO4, format476, [N, NTOT, NSHP, NRS, SIGL])
    return (NRS, NTOT, SIGMA2)



@with_goto
def get_result(gauss, SIGMA2, NTOT, NRS, IPP, LDB, file_IO3, file_IO4):
#
#      GETTING THE RESULT
#
    file_IO3.seek(0,0)
    format6919 = "(' start getting the result ')"
    fort_write(None, format6919, [])
    SIGMAA=SIGMA2/float(NTOT-NRS)
    format9679 = "(/' UNCERTENTY SCALING   ',E12.4/)"
    fort_write(file_IO4, format9679, [SIGMAA])
    NRST=NRS*(NRS+1)/2
    if IPP[8] ==  0:
        force_stop(file_IO4)
    if IPP[4] == 0:
        goto .lbl68
    format116 = "(1H*//,'  MATRIX PRODUCT'//)"
    fort_write(file_IO4, format116, [])
    format152 = "(2X,10E10.4)"
    fort_write(file_IO4, format152, gauss.B[1:(NRST+1)])
    label .lbl68
    format2840 = "(80X,9HLDB,NRS= ,2I6,6H  NTOT,I8)"
    fort_write(file_IO4, format2840, [LDB, NRS, NTOT])
    format7103 = "(2E16.8)"
    format6918 = "(' start on matrix inversion ')"
    fort_write(None, format6918, [])


    # CALL DPPFA(B,NRS,INFO)
    NUMEL = NRS*(NRS+1)//2
    INFO = 0.
    tmp = np.array(gauss.B[1:(NUMEL+1)], dtype='float64', order='F')
    linpack_slim.dppfa(ap=tmp, n=NRS, info=INFO)
    gauss.B[1:(NUMEL+1)] = tmp

    # ALTERNATIVE: numpy does not know about the packed storaged format
    #              of symmetric matrices used by DPPFA, so we need to
    #              unpack the matrix first

    # INFO = 0
    # try:
    #     tmp[1:NRS+1,1:NRS+1] = cholesky(tmp[1:NRS+1,1:NRS+1]).T 
    # except np.linalg.LinAlgError:
    #     INFO = 1

    if INFO != 0:
        format105 = "(/' EXP BLOCK CORREL. MATRIX NOT PD',20X,'***** WARNING *')" 
        format106 = "( '  SOLUTION  CORREL. MATRIX NOT PD ' )"
        fort_write(file_IO4, format106)
        exit()

    format9171 = "(' INVERT SOLUTION MATRIX')"
    fort_write(file_IO4, format9171, [])
    fort_write(None, format9171, [])

    JOB = 1
    # CALL DPPDI(gauss.B,NRS,DET,JOB)
    NUMEL = NRS*(NRS+1)//2
    tmp_det = np.array([0., 0.], dtype='float64', order='F')
    tmp = np.array(gauss.B[1:(NUMEL+1)], dtype='float64', order='F')
    linpack_slim.dppdi(ap=tmp, n=NRS, det=tmp_det, job=JOB)
    gauss.B[1:(NUMEL+1)] = tmp

    # ALTERNATIVE: using numpy/scipy functions instead of LINPACK functions
    # invert the matrix, we do it a bit complicated to use the cholesky factor
    # we invert the cholesky factor and then mutliply its inverse by its transposed inverse
    # tmp = unpack_utriang_matrix(tmp)
    # tmp = inv(tmp)
    # tmp = np.matmul(tmp, tmp.T)
    # # pack the result again
    # gauss.B[1:(NUMEL+1)] = pack_symmetric_matrix(tmp)


    format6917 = "(' completed inversion of matrix')"
    fort_write(None, format6917, [])

    for I in fort_range(1,NRS):  # .lbl13
        gauss.DE[I]=0.
        for K in fort_range(1,NRS):  # .lbl13
            IK=K*(K-1)//2+I
            if K < I:
                IK = I*(I-1)//2 + K
            gauss.DE[I]=gauss.DE[I]+gauss.B[IK]*gauss.BM[K]
        label .lbl13


@with_goto
def output_result(gauss, data, APR, MODAP, NFIS, NR, NC,
        NSHP, NRS, LABL, NSETN, file_IO4, file_IO5):
    #
    #      output of the result
    #
    for L in fort_range(1,NC):  # .lbl14
        format117 = "(1H1,'   RESULT',5X,2A8//)" 
        fort_write(file_IO4, format117, [LABL.CLAB[L,1:3]])
        fort_write(file_IO5, format117, [LABL.CLAB[L,1:3]])
        format112 = "( '   E/MEV         CS/B            DCS/B       DCS/%" + \
                    "     DIF/%    CS*SQRT(E)'/)"
        fort_write(file_IO4, format112, [])
        JA=APR.MCS[L,2]
        JI=APR.MCS[L,3]
        FLX=0.

        for K in fort_range(JA, JI):  # .lbl77
            KBK=K*(K-1)//2+K
            DDX=APR.CS[K]*np.sqrt(gauss.B[KBK])
            CXX=APR.CS[K]*(1.+gauss.DE[K])
            CXXD=100.*(CXX-APR.CS[K])/CXX
            for KK in fort_range(1,NFIS):  # .lbl705
                if data.ENFIS[KK] > .999*APR.EN[K] and data.ENFIS[KK] < 1.001*APR.EN[K]:
                    goto .lbl703
            label .lbl705

            goto .lbl706
            label .lbl703
            if K == JA or K == JI:
                goto .lbl295

            EL1=(APR.EN[K]+APR.EN[K-1])*0.5
            EL2=(APR.EN[K]+APR.EN[K+1])*0.5
            DE1=(APR.EN[K]-EL1)*0.5
            DE2=(EL2-APR.EN[K])*0.5
            SS1=.5*(CXX+0.5*(CXX+(1.+gauss.DE[K-1])*APR.CS[K-1]))
            SS2=.5*(CXX+0.5*(CXX+(1.+gauss.DE[K+1])*APR.CS[K+1]))
            CSSK=(SS1*DE1+SS2*DE2)/(DE1+DE2)
            goto .lbl296
            label .lbl295
            CSSK=CXX
            label .lbl296
            FLX=FLX+data.FIS[KK]*CSSK
            label .lbl706
            FQW=DDX*100./CXX
            SECS=np.sqrt(APR.EN[K])*CXX
            format153 = "(1X,E10.4,2F15.8,2X,F6.1,3X,F7.2,3X,F10.5)" 
            fort_write(file_IO4, format153, [APR.EN[K],CXX,DDX,FQW,CXXD,SECS])
            fort_write(file_IO5, format153, [APR.EN[K],CXX,DDX,FQW,CXXD,SECS])
            if MODAP == 0:
                goto .lbl58
            if MODAP == 2 and K <= APR.MCS[5,3]:
                goto .lbl58
            APR.CS[K]=CXX
            label .lbl58
        label .lbl77

        # VP: 13 lines below are added by VP, 26 July, 2004
        format588 = "(6(1X,E10.5))"
        fort_write(file_IO4, format588, [
            (APR.EN[JA]*500000.),
            (APR.EN[JA:JI]+APR.EN[(JA+1):(JI+1)])*500000.,
            (-APR.EN[JI-1]+3*APR.EN[JI])*500000.
        ])

        tmp = np.vstack([APR.EN[JA:(JI+1)]*1000000., APR.CS[JA:(JI+1)]])
        tmp = tmp.T.flatten()
        fort_write(file_IO4, format588, tmp)
        for K in fort_range(JA+1, JI-1):
            DSMOOA = (APR.CS[K+1] * (APR.EN[K] - APR.EN[K-1]) \
                    +APR.CS[K-1] * (APR.EN[K+1] - APR.EN[K]) \
                    -APR.CS[K] * (APR.EN[K+1] - APR.EN[K-1])) \
                    /2./(APR.EN[K+1] - APR.EN[K-1])
            DSMOOR = DSMOOA / APR.CS[K]*100.
            SSMOO = APR.CS[K] + DSMOOA
            fort_write(file_IO4, format153, [APR.EN[K], APR.CS[K], SSMOO, DSMOOR])
        # VP above is writing CS in B-6 format and smoothing with CS conserving

        format158 = "(1H*//,'  FISSION AVERAGE ' ,F8.4//)" 
        fort_write(file_IO4, format158, [FLX])
        # label .lbl14  # end of for loop
    L = L + 1  # to match L value of fortran after loop

    #
    #   OUTPUT OF NORM. FACTORS FOR SHAPE DATA
    #
    format114 = "(1H*///, '  NORMALIZATION  OF SHAPE DATA '///)"
    fort_write(file_IO4, format114, [])
    NR1=NR+1
    LLX=0
    if NSHP != 0:
        for K in fort_range(NR1, NRS):  # .lbl82
            LLX=LLX+1
            KK=K*(K-1)//2+K
            ZCS=APR.CS[K]
            DDX=APR.CS[K]*np.sqrt(gauss.B[KK])
            CXX=APR.CS[K]*(1.+gauss.DE[K])
            DDXD=DDX*100./CXX
            format115 = "(2I6,4F10.4)"
            fort_write(file_IO4, format115, [K,NSETN[LLX],CXX,DDX,DDXD,ZCS])
            APR.CS[K]=CXX
        label .lbl82  # end for loop
    return JA



@with_goto
def output_result_correlation_matrix(gauss, data, APR, IPP, NC,
        LABL, JA, file_IO4):
    #
    #   OUTPUT OF CORRELATION MATRIX OF THE RESULT
    #
    if IPP[6] == 0:
        goto .lbl184

    format151 = "(1X,24F7.4)"
    for K in fort_range(1,NC):  # .lbl78
        J1=APR.MCS[K,2]
        J2=APR.MCS[K,3]

        # CVP 3 lines below are added by VP, 26 July, 2004
        NROW=J2-J1+2
        for III in fort_range(1, NROW):
            gauss.EGR[III] = 1.0*III
        # CVP

        for L in fort_range(1,K):  # .lbl80
            format122 = "(1H1, '  CORRELATION MATRIX OF THE RESULT   ',2A8,2A8///)"
            fort_write(file_IO4, format122, [LABL.CLAB[K,1:3], LABL.CLAB[L,1:3]])
            J3=APR.MCS[L,2]
            J4=APR.MCS[L,3]

            # CVP 3 lines below are added by VP, 26 July 2004
            NCOL = J4-J3+2
            for III in fort_range(1, NROW+NCOL):
                gauss.EEGR[III] = 1.0*III
            # CVP

            if K == L:
                goto .lbl87

            for I in fort_range(J1, J2):  # .lbl88
                II=I*(I-1)//2+I
                for J in fort_range(J3, J4):  # .lbl16
                    IJ=I*(I-1)//2+J
                    JJ=J*(J-1)//2+J
                    gauss.BM[J]=gauss.B[IJ]/np.sqrt(gauss.B[II]*gauss.B[JJ])
                    # CVP three lines below are inserted by VP
                    gauss.RELCOV[I-J1+1, J-J3+1] = gauss.B[IJ]
                    data.AAA[I-J1+1, J-J3+1] = gauss.BM[J]
                    data.AAA[J-J3+1, I-J1+1] = gauss.BM[J]
                    # CVP
                label .lbl16  # end loop
                fort_write(file_IO4, format151, [gauss.BM[J3:(J4+1)]]) 
            label .lbl88  # end loop

            # CVP   Lines below are added by VP, 26 July, 2004
            format388 = '(6E11.4)'
            fort_write(file_IO4, format388,
                    [gauss.EEGR[1:(NROW+NCOL+1)],
                        gauss.RELCOV[1:NROW, 1:NCOL].flatten()])
            fort_write(file_IO4, format388,
                    [gauss.EEGR[1:(NROW+NCOL+1)],
                     gauss.RELCOV[1:NROW, 1:NCOL].flatten(order='F')])
            # CVP   print below is inserted by VP Aug2013
            IMAX = J2-J1+1
            format389 = '(2x,f7.3,1x,200(E10.4,1x))'
            for I in fort_range(1, IMAX):
                fort_write(file_IO4, format389,
                        [APR.EN[JA+I-1],
                         data.AAA[I,1:(J4-J3+2)]])

            goto .lbl300

            label .lbl87
            for I in fort_range(J1, J2):  # .lbl55
                II=I*(I-1)//2+I
                for J in fort_range(J1,I):  # .lbl27
                    IJ=I*(I-1)//2+J
                    JJ=J*(J-1)//2+J
                    gauss.BM[J]=gauss.B[IJ]/np.sqrt(gauss.B[II]*gauss.B[JJ])
                    # CVP lines below are added by VP, 26 July, 2004
                    gauss.RELTRG[I-J1+1,J-J1+1] = gauss.B[IJ]
                    data.AAA[I-J1+1, J-J1+1] = gauss.BM[J]
                    data.AAA[J-J1+1, I-J1+1] = gauss.BM[J]
                    # CVP end

                label .lbl27
                label .lbl55
                fort_write(file_IO4, format151, [gauss.BM[J1:(I+1)]])

            format389 = '(2x,f7.3,1x,200(E10.4,1x))'
            IMAX = J2-J1+1
            for I in fort_range(1,IMAX):
                fort_write(file_IO4, format389,
                        [APR.EN[JA+I-1], data.AAA[I,1:(J2-J1+2)]])

            # CVP   Lines below are added by VP, 26 July, 2004
            format388 = '(6E11.4)'
            tmp = [[gauss.RELTRG[III,JJJ]
                    for III in fort_range(JJJ,NROW-1)]
                    for JJJ in fort_range(1, NROW-1)]
            fort_write(file_IO4, format388,
                    [gauss.EGR[1:(NROW+1)], tmp])
            # CVP

            label .lbl300
            label .lbl80
        L = L + 1  # to match L value of fortran after loop
    label .lbl78
    label .lbl184
    exit()
