# ---------------------------------------------------------------------------
# LICENCE NOTICE -- THIS FILE IS NOT COVERED BY THIS REPOSITORY'S LICENCE.
#
# The arithmetic below is copied verbatim from
#   https://github.com/ClevelandClinicQHS/riskcalc-website
# which is licensed **PolyForm Noncommercial 1.0.0**, NOT Apache-2.0.
#
# The repository's own LICENSE (Apache-2.0) does not, and cannot, apply to it:
# nobody may relicense someone else's work by putting it in their tree. This
# file may be used only for a noncommercial purpose, which PolyForm defines as
# "any noncommercial purpose" regardless of who is using it.
#
# It is present because this project's use is academic research only. If that
# ever stops being true, this file must come out again -- and so must the five
# others listed in NOTICE beside it.
#
# Withheld from the public mirror until 2026-08-18 on the reasoning that a
# company repository could not have a noncommercial purpose. That reasoning
# tested the wrong thing: PolyForm gates on PURPOSE, not on who is using it.
# See docs/THIRD_PARTY_CODE.md and docs/ACADEMIC_USE_LICENSE_REVIEW.md.
# ---------------------------------------------------------------------------

# Run the deployed dutasteride model exactly as riskcalc.org does.
#
# The predict.* functions are copied VERBATIM from
#   https://github.com/ClevelandClinicQHS/riskcalc-website/blob/main/ProstateCancerConsideringDutasteride/server.R
#
# The raw.* copies are the same functions with only the display rounding
# removed, so parity can be checked on real numbers rather than whole percent.
# Note two asymmetries reproduced from the source: ASAP has no no-dutasteride
# arm, and HGPIN on dutasteride is a fixed 3.838831% with no predictors.
#
#   Rscript tests/parity/reference/dutasteride_reference.R > dutasteride_cases.json

predict.highgrade.dutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = -2.5995679 + 0.092685394 * AGE -
        0.000042571616 * max(AGE - 55, 0)**3 +
        0.000085143232 * max(AGE - 63, 0)**3 -
        0.000042571616 * max(AGE - 71, 0)**3 -
        0.02729155 * B_PV +
        0.000003473756 * max(B_PV - 25.52, 0)**3 -
        0.000005955998 * max(B_PV - 43.47, 0)**3 +
        0.000002482242 * max(B_PV - 68.59, 0)**3 -
        0.021879504 * B_NOCOR -
        0.0013241433 * max(B_NOCOR - 6, 0)**3 +
        0.0026482866 * max(B_NOCOR - 9, 0)**3 -
        0.0013241433 * max(B_NOCOR - 12, 0)**3 +
        0.1414056 * B_OPSA -
        0.0038989431 * max(B_OPSA - 3.5, 0)**3 +
        0.006758168 * max(B_OPSA - 5.7, 0)**3 -
        0.0028592249 * max(B_OPSA - 8.7, 0)**3 -
        0.1644022 * B_OPFPS +
        0.00056993789 * max(B_OPFPS - 9.6774194, 0)**3 -
        0.0010176765 * max(B_OPFPS - 16.071429, 0)**3 +
        0.00044773859 * max(B_OPFPS - 24.210526, 0)**3 +
        0.31134948 * (HIS_PCA == "Yes") -
        0.52677693 * (B_DRE == "Yes") +
        0.01188137 * B_BMI +
        0.00011619678 * max(B_BMI - 23.15, 0)**3 -
        0.00019842834 * max(B_BMI - 26.83, 0)**3 +
        0.000082231564 * max(B_BMI - 32.03, 0)**3
    if (50 <= AGE && AGE <= 75 && 0 <= B_PV && B_PV <= 80 && 6 <= B_NOCOR && B_NOCOR <= 12 && 2 <= B_OPSA && B_OPSA <= 10 && 0 <= B_OPFPS && B_OPFPS <= 64 && HIS_PCA != "Unknown" && B_DRE != "Unknown" && 15 <= B_BMI && B_BMI <= 50) {
        round((1 - 0.9560246 ** exp(score)) * 100, 0)
    } else {
        "Not Applicable"
    }
}
predict.highgrade.nodutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = -5.291106 + 0.12865175 * AGE -
        0.00011792908 * max(AGE - 55, 0)**3 +
        0.00023585817 * max(AGE - 63, 0)**3 -
        0.00011792908 * max(AGE - 71, 0)**3 -
        0.041330344 * B_PV +
        2.0545925e-05 * max(B_PV - 25.52, 0)**3 -
        3.5227428e-05 * max(B_PV - 43.47, 0)**3 +
        1.4681503e-05 * max(B_PV - 68.59, 0)**3 -
        0.11735785 * B_NOCOR +
        0.002743688 * max(B_NOCOR - 6, 0)**3 -
        0.005487376 * max(B_NOCOR - 9, 0)**3 +
        0.002743688 * max(B_NOCOR - 12, 0)**3 +
        0.24274067 * B_OPSA -
        0.0096728386 * max(B_OPSA - 3.5, 0)**3 +
        0.016766254 * max(B_OPSA - 5.7, 0)**3 -
        0.007093415 * max(B_OPSA - 8.7, 0)**3 -
        0.14091258 * B_OPFPS +
        0.00050049136 * max(B_OPFPS - 9.6774194, 0)**3 -
        0.00089367332 * max(B_OPFPS - 16.071429, 0)**3 +
        0.00039318196 * max(B_OPFPS - 24.210526, 0)**3 +
        0.55482753 * (HIS_PCA == "Yes") -
        0.1854322 * (B_DRE == "Yes") +
        0.027549519 * B_BMI -
        0.0003469818 * max(B_BMI - 23.15, 0)**3 +
        0.00059253815 * max(B_BMI - 26.83, 0)**3 -
        0.00024555635 * max(B_BMI - 32.03, 0)**3
    if (50 <= AGE && AGE <= 75 && 0 <= B_PV && B_PV <= 80 && 2 <= B_OPSA && B_OPSA <= 10 && 0 <= B_OPFPS && B_OPFPS <= 64 && HIS_PCA != "Unknown" && B_DRE != "Unknown" && 15 <= B_BMI && B_BMI <= 50) {
        round((1 - 0.9485273 ** exp(score)) * 100, 0)
    } else {
        "Not Applicable"
    }
}
predict.aur.dutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = 1.1645202 -
        0.061061932 * AGE +
        0.00021214229 * max(AGE - 55, 0) ** 3 -
        0.00042428457 * max(AGE - 63, 0) ** 3 +
        0.00021214229 * max(AGE - 71, 0) ** 3 -
        0.0089110256 * B_PV +
        0.0000079993515 * max(B_PV - 25.52, 0) ** 3 -
        0.000013715449 * max(B_PV - 43.47, 0) ** 3 +
        0.0000057160971 * max(B_PV - 68.59, 0) ** 3 +
        0.32260345 * B_OPSA -
        0.014797257 * max(B_OPSA - 3.5, 0) ** 3 +
        0.025648579 * max(B_OPSA - 5.7, 0) ** 3 -
        0.010851322 * max(B_OPSA - 8.7, 0) ** 3 +
        0.13327946 * B_IPSS -
        0.0003871158 * max(B_IPSS - 2, 0) ** 3 +
        0.00064519299 * max(B_IPSS - 8, 0) ** 3 -
        0.0002580772 * max(B_IPSS - 17, 0) ** 3 +
        0.01045639 * B_QM -
        0.00016491276 * max(B_QM - 7.8, 0) ** 3 +
        0.00025179364 * max(B_QM - 13.2, 0) ** 3 -
        0.000086880871 * max(B_QM - 23.45, 0) ** 3 +
        0.008271271 * B_RSD -
        0.00000029329635 * max(B_RSD, 0) ** 3 +
        0.0000009545575 * max(B_RSD - 31, 0) ** 3 -
        0.0000001021594 * max(B_RSD - 120, 0) ** 3
    if (50 <= AGE && AGE <= 75 && 0 <= B_PV && B_PV <= 80 && 2 <= B_OPSA && B_OPSA <= 88 && 0 <= B_IPSS && B_IPSS <= 25 && 0 <= B_QM && B_QM <= 100 && B_RSD >= 0 ) {
        round((1 - 0.9881902 ** exp(score)) * 100, 0)
    } else {
        "Not Applicable"
    }
}
predict.aur.nodutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = -1.0281503 -
        0.00076540945 * AGE -
        0.000069130129 * max(AGE - 55, 0) ** 3 +
        0.00013826026 * max(AGE - 63, 0)**3 -
        0.000069130129 * max(AGE - 71, 0)**3 +
        0.045963842 * B_PV -
        0.000017356701 * max(B_PV - 25.52, 0)**3 +
        0.000029759281 * max(B_PV - 43.47, 0)**3 -
        0.000012402579 * max(B_PV - 68.59, 0)**3 +
        0.0023571984 * B_OPSA +
        0.00008654012 * max(B_OPSA - 3.5, 0)**3 -
        0.00015000288 * max(B_OPSA - 5.7, 0)**3 +
        0.000063462755 * max(B_OPSA - 8.7, 0)**3 +
        0.087108858 * B_IPSS -
        0.00025960794 * max(B_IPSS - 2, 0)**3 +
        0.00043267991 * max(B_IPSS - 8, 0)**3 -
        0.00017307196 * max(B_IPSS - 17, 0)**3 -
        0.11685329 * B_QM +
        0.00045782518 * max(B_QM - 7.8, 0)**3 -
        0.00069902089 * max(B_QM - 13.2, 0)**3 +
        0.0002411957 * max(B_QM - 23.45, 0)**3 +
        0.0061259723 * B_RSD -
        0.00000057253793 * max(B_RSD, 0)**3 +
        0.00000077196125 * max(B_RSD - 31, 0)**3 -
        0.00000019942332 * max(B_RSD - 120, 0)**3
    if (50 <= AGE && AGE <= 75 && 0 <= B_PV && B_PV <= 80 && 2 <= B_OPSA && B_OPSA <= 88 && 0 <= B_IPSS && B_IPSS <= 25 && 0 <= B_QM && B_QM <= 100 && B_RSD >= 0) {
        round((1 - 0.9424894 ** exp(score)) * 100, 0)
    } else {
        "Not Applicable"
    }
}
predict.bph.dutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = -5.1794212 + 0.082837869 * AGE -
        0.00019166777 * max(AGE - 55, 0)**3 +
        0.00038333555 * max(AGE - 63, 0)**3 -
        0.00019166777 * max(AGE - 71, 0)**3 +
        0.019842467 * B_PV -
        7.9898849e-06 * max(B_PV - 25.52, 0)**3 +
        1.3699217e-05 * max(B_PV - 43.47, 0)**3 -
        5.7093326e-06 * max(B_PV - 68.59, 0)**3 +
        0.024113451 * B_OPSA +
        0.0020938172 * max(B_OPSA - 3.5, 0)**3 -
        0.0036292832 * max(B_OPSA - 5.7, 0)**3 +
        0.001535466 * max(B_OPSA - 8.7, 0)**3 -
        0.084429276 * B_IPSS +
        0.0007641629 * max(B_IPSS - 2, 0)**3 -
        0.0012736048 * max(B_IPSS - 8, 0)**3 +
        0.00050944193 * max(B_IPSS - 17, 0)**3 -
        0.040246013 * B_QM +
        8.79458e-05 * max(B_QM - 7.8, 0)**3 -
        0.00013427822 * max(B_QM - 13.2, 0)**3 +
        4.6332421e-05 * max(B_QM - 23.45, 0)**3 +
        0.0028358349 * B_RSD -
        6.8147752e-07 * max(B_RSD, 0)**3 +
        9.188461e-07 * max(B_RSD - 31, 0)**3 -
        2.3736857e-07 * max(B_RSD - 120, 0)**3
    if (50 <= AGE && AGE <= 75 && 0 <= B_PV && B_PV <= 80 && 2 <= B_OPSA && B_OPSA <= 88 && 0 <= B_IPSS && B_IPSS <= 25 && 0 <= B_QM && B_QM <= 100 && B_RSD >= 0) {
        round((1 - 0.9880496 ** exp(score)) * 100, 0)
    } else {
        "Not Applicable"
    }
}
predict.bph.nodutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = -2.5335304 + 0.025530334 * AGE -
        0.00027794159 * max(AGE - 55, 0)**3 +
        0.00055588319 * max(AGE - 63, 0)**3 -
        0.00027794159 * max(AGE - 71, 0)**3 +
        0.031405179 * B_PV -
        0.000011141665 * max(B_PV - 25.52, 0)**3 +
        0.000019103165 * max(B_PV - 43.47, 0)**3 -
        0.0000079615 * max(B_PV - 68.59, 0)**3 -
        0.011456454 * B_OPSA +
        0.0030614148 * max(B_OPSA - 3.5, 0)**3 -
        0.0053064523 * max(B_OPSA - 5.7, 0)**3 +
        0.0022450375 * max(B_OPSA - 8.7, 0)**3 +
        0.17153886 * B_IPSS -
        0.00050278585 * max(B_IPSS - 2, 0)**3 +
        0.00083797642 * max(B_IPSS - 8, 0)**3 -
        0.00033519057 * max(B_IPSS - 17, 0)**3 -
        0.10624904 * B_QM +
        0.00037314418 * max(B_QM - 7.8, 0)**3 -
        0.00056972746 * max(B_QM - 13.2, 0)**3 +
        0.00019658328 * max(B_QM - 23.45, 0)**3 +
        0.0047543213 * B_RSD -
        0.00000044918222 * max(B_RSD, 0)**3 +
        0.00000060563894 * max(B_RSD - 31, 0)**3 -
        0.00000015645673 * max(B_RSD - 120, 0)**3
    if (50 <= AGE && AGE <= 75 && 0 <= B_PV && B_PV <= 80 && 2 <= B_OPSA && B_OPSA <= 88 && 0 <= B_IPSS && B_IPSS <= 25 && 0 <= B_QM && B_QM <= 100 && B_RSD >= 0) {
        round((1 - 0.9621862 ** exp(score)) * 100, 0)
    } else {
        "Not Applicable"
    }
}
predict.erectile.dutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = -0.82555754 +
        0.0021009936 * AGE -
        0.00018470233 * max(AGE - 55, 0)**3 +
        0.00036940465 * max(AGE - 63, 0)**3 -
        0.00018470233 * max(AGE - 71, 0)**3 +
        1.0040617 * (SBSRL == "Yes") +
        0.29803134 * (LIB == "Yes") -
        0.0028454973 * (IMP == "Yes")
    if (50 <= AGE && AGE<= 75 && SBSRL != "Unknown" && LIB != "Unknown" && IMP != "Unknown") {
        round((1 - 0.8331268 ** exp(score)) * 100, 0)
    } else {
        "Not Applicable"
    }
}
predict.erectile.nodutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = 0.49218732 - 0.017043475 * AGE -
        0.000099164052 * max(AGE - 55, 0)**3 +
        0.0001983281 * max(AGE - 63, 0)**3 -
        0.000099164052 * max(AGE - 71, 0)**3 +
        0.67408096 * (SBSRL == "Yes") +
        0.28603854 * (LIB == "Yes") +
        0.21585816 * (IMP == "Yes")
    if (50 <= AGE && AGE <= 75 && SBSRL != "Unknown" && LIB != "Unknown" && IMP != "Unknown") {
        round((1 - 0.8792946 ** exp(score)) * 100, 0)
    } else {
        "Not Applicable"
    }
}
predict.gynecomastia.dutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = -1.6541886 +
        0.013380387 * AGE -
        0.000025127812 * max(AGE - 55, 0)**3 +
        0.000050255624 * max(AGE - 63, 0)**3 -
        0.000025127812 * max(AGE - 71, 0)**3 +
        0.030085377 * B_BMI +
        0.0001100241 * max(B_BMI - 23.15, 0)**3 -
        0.00018788731 * max(B_BMI - 26.83, 0)**3 +
        0.00007786321 * max(B_BMI - 32.03, 0)**3
    if (50 <= AGE && AGE <= 75 && 15 <= B_BMI && B_BMI<= 50) {
        round((1 - 0.9634263 ** exp(score)) * 100, 0)
    } else {
        "Not Applicable"
    }
}
predict.gynecomastia.nodutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = -2.0653904 -
        0.0019965622 * AGE -
        0.00001577009 * max(AGE - 55, 0)**3 +
        0.00003154018 * max(AGE - 63, 0)**3 -
        0.00001577009 * max(AGE - 71, 0)**3 +
        0.083659972 * B_BMI -
        0.0005061525 * max(B_BMI - 23.15, 0)**3 +
        0.00086435274 * max(B_BMI - 26.83, 0)**3 -
        0.00035820023 * max(B_BMI - 32.03, 0)**3
    if (50 <= AGE && AGE <= 75 && 15 <= B_BMI && B_BMI <= 50) {
        round((1 - 0.9783186 ** exp(score)) * 100, 0)
    } else {
        "Not Applicable"
    }
}
predict.hgpin.dutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    if (50 <= AGE && AGE <= 75 && 0 <= B_PV && B_PV <= 80 && 6 <= B_NOCOR && B_NOCOR <= 12 && 2 <= B_OPSA && B_OPSA <= 10 && 0 <= B_OPFPS && B_OPFPS <= 64 && HIS_PCA != "Unknown" && B_DRE != "Unknown" && 15 <= B_BMI && B_BMI <= 50) {
        paste(round(0.03838831 * 100, 0), '%', sep='')
    } else {
        "Not Applicable"
    }
}
predict.hgpin.nodutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = 0.02314685 * AGE +
        9.462079e-05 * max(AGE - 55, 0)**3 -
        0.00018924158 * max(AGE - 63, 0)**3 +
        9.462079e-05 * max(AGE - 71, 0)**3 -
        0.0076597772 * B_PV +
        2.1045322e-06 * max(B_PV - 25.52, 0)**3 -
        3.6083679e-06 * max(B_PV - 43.47, 0)**3 +
        1.5038357e-06 * max(B_PV - 68.59, 0)**3 +
        0.024188546 * B_NOCOR +
        0.00028423913 * max(B_NOCOR - 6, 0)**3 -
        0.00056847825 * max(B_NOCOR - 9, 0)**3 +
        0.00028423913 * max(B_NOCOR - 12, 0)**3 -
        0.035761911 * B_OPSA +
        0.0018467184 * max(B_OPSA - 3.5, 0)**3 -
        0.0032009786 * max(B_OPSA - 5.7, 0)**3 +
        0.0013542602 * max(B_OPSA - 8.7, 0)**3 +
        0.031267747 * B_OPFPS -
        0.00013307385 * max(B_OPFPS - 9.6774194, 0)**3 +
        0.00023761559 * max(B_OPFPS - 16.071429, 0)**3 -
        0.00010454174 * max(B_OPFPS - 24.210526, 0)**3 +
        0.096023267 * (HIS_PCA == "Yes") -
        0.15972617 * (B_DRE == "Yes") -
        0.046172021 * B_BMI +
        0.00088524838 * max(B_BMI - 23.15, 0)**3 -
        0.0015117318 * max(B_BMI - 26.83, 0)**3 +
        0.00062648347 * max(B_BMI - 32.03, 0)**3
    if (50 <= AGE && AGE <= 75 && 0 <= B_PV && B_PV <= 80 && 6 <= B_NOCOR && B_NOCOR <= 12 && 2 <= B_OPSA && B_OPSA <= 10 && 0 <= B_OPFPS && B_OPFPS <= 64 && HIS_PCA != "Unknown" && B_DRE != "Unknown" && 15 <= B_BMI && B_BMI <= 50) {
        round((1 - 0.9676886 ** exp(score)) * 100, 0)
    } else {
        "Not Applicable"
    }
}
predict.prostate.dutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = -3.2873301 + 0.062184251 * AGE -
        7.1247133e-05 * max(AGE - 55, 0)**3 +
        0.00014249427 * max(AGE - 63, 0)**3 -
        7.1247133e-05 * max(AGE - 71, 0)**3 -
        0.013281746 * B_PV +
        4.2085264e-08 * max(B_PV - 25.52, 0)**3 -
        7.2158134e-08 * max(B_PV - 43.47, 0)**3 +
        3.007287e-08 * max(B_PV - 68.59, 0)**3 -
        0.020945724 * B_NOCOR -
        0.0013792832 * max(B_NOCOR - 6, 0)**3 +
        0.0027585664 * max(B_NOCOR - 9, 0)**3 -
        0.0013792832 * max(B_NOCOR - 12, 0)**3 +
        0.092260347 * B_OPSA -
        0.003146994 * max(B_OPSA - 3.5, 0)**3 +
        0.0054547896 * max(B_OPSA - 5.7, 0)**3 -
        0.0023077956 * max(B_OPSA - 8.7, 0)**3 -
        0.069689053 * B_OPFPS +
        0.00024776037 * max(B_OPFPS - 9.6774194, 0)**3 -
        0.0004423989 * max(B_OPFPS - 16.071429, 0)**3 +
        0.00019463854 * max(B_OPFPS - 24.210526, 0)**3 +
        0.32320144 * (HIS_PCA == "Yes") -
        0.091053957 * (B_DRE == "Yes") +
        0.035915989 * B_BMI -
        0.0005530593 * max(B_BMI - 23.15, 0)**3 +
        0.00094445511 * max(B_BMI - 26.83, 0)**3 -
        0.00039139581 * max(B_BMI - 32.03, 0)**3
    if (50 <= AGE && AGE <= 75 && 0 <= B_PV && B_PV <= 80 && 6 <= B_NOCOR && B_NOCOR <= 12 && 2 <= B_OPSA && B_OPSA <= 10 && 0 <= B_OPFPS && B_OPFPS <= 64 && HIS_PCA != "Unknown" && B_DRE != "Unknown" && 15 <= B_BMI && B_BMI<= 50) {
        round((1 - 0.8443213 ** exp(score)) * 100, 0)
    } else {
        "Not Applicable"
    }
}
predict.prostate.nodutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = -2.0022764 + 0.056199639 * AGE-
        0.000015829258 * max(AGE-55,0) ** 3 +
        0.000031658515 * max(AGE-63,0) ** 3-
        0.000015829258 * max(AGE-71,0) ** 3-
        0.028379627 * B_PV +
        0.00001559305 * max(B_PV-25.52,0) ** 3-
        0.000026735376 * max(B_PV-43.47,0) ** 3 +
        0.000011142327 * max(B_PV-68.59,0) ** 3-
        0.055600097 * B_NOCOR +
        0.00089358345 * max(B_NOCOR-6,0) ** 3-
        0.0017871669 * max(B_NOCOR-9,0) ** 3 +
        0.00089358345 * max(B_NOCOR-12,0) ** 3 +
        0.16137068 * B_OPSA-
        0.0067701874 * max(B_OPSA-3.5,0) ** 3 +
        0.011734992 * max(B_OPSA-5.7,0) ** 3-
        0.0049648041 * max(B_OPSA-8.7,0) ** 3 -
        0.066716939 * B_OPFPS +
        0.00017396904 * max(B_OPFPS-9.6774194,0) ** 3-
        0.00031063771 * max(B_OPFPS-16.071429,0) ** 3 +
        0.00013666867 * max(B_OPFPS-24.210526,0) ** 3 +
        0.43429612 * (HIS_PCA == "Yes")-
        0.25508281 * (B_DRE == "Yes")+
        0.016145135 * B_BMI-
        0.00038880393 * max(B_BMI-23.15,0) ** 3 +
        0.00066395748 * max(B_BMI-26.83,0) ** 3-
        0.00027515355 * max(B_BMI-32.03,0) ** 3
    if (50 <= AGE && AGE <= 75 && 0 <= B_PV && B_PV <= 80 && 6 <= B_NOCOR && B_NOCOR <= 12 && 2 <= B_OPSA && B_OPSA <= 10 && 0 <= B_OPFPS && B_OPFPS <= 64 && HIS_PCA != "Unknown" && B_DRE != "Unknown" && 15 <= B_BMI && B_BMI<= 50) {
        round((1 - 0.7987971 ** exp(score)) * 100, 0)
    } else {
        "Not Applicable"
    }
}
predict.uti.dutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = -0.33966523 + 0.014924564 * B_QM -
        0.000075239732 * max(B_QM - 7.8, 0)**3 +
        0.00011487823 * max(B_QM - 13.2, 0)**3 -
        0.000039638493 * max(B_QM - 23.45, 0)**3 +
        0.0059938379 * B_RSD -
        0.00000048861775 * max(B_RSD, 0)**3 +
        0.00000065881045 * max(B_RSD - 31, 0)**3 -
        0.0000001701927 * max(B_RSD - 120, 0)**3
    if (0 <= B_QM && B_QM <= 100 && B_RSD >= 0) {
        round((1 - 0.9433828 ** exp(score)) * 100, 0)
    } else {
        "Not Applicable"
    }
}
predict.uti.nodutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = 0.66770954 - 0.069385484 * B_QM +
        0.00028417274 * max(B_QM - 7.8, 0)**3 -
        0.00043388325 * max(B_QM - 13.2, 0)**3 +
        0.00014971051 * max(B_QM - 23.45, 0)**3 +
        0.0061318174 * B_RSD -
        0.00000062268412 * max(B_RSD, 0)**3 +
        0.0000008395741 * max(B_RSD - 31, 0)**3 -
        0.00000021688997 * max(B_RSD - 120, 0)**3
    if (0 <= B_QM && B_QM <= 100 && B_RSD >= 0) {
        round((1 - 0.9433828 ** exp(score)) * 100, 0)
    } else {
        "Not Applicable"
    }
}
predict.asap.dutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = -0.0011455882 * AGE +
        3.4941473e-05 * max(AGE - 55,0) ** 3 -
        6.9882947e-05 * max(AGE - 63, 0) ** 3 +
        3.4941473e-05 * max(AGE - 71, 0) ** 3 -
        0.013058082 * B_PV +
        2.2486763e-06 * max(B_PV - 25.52, 0) ** 3 -
        3.855513e-06 * max(B_PV - 43.47, 0) ** 3 +
        1.6068367e-06 * max(B_PV - 68.59, 0) ** 3 -
        0.11978819 * B_NOCOR +
        0.0048529883 * max(B_NOCOR - 6, 0) ** 3 -
        0.0097059765 * max(B_NOCOR - 9, 0) ** 3 +
        0.0048529883 * max(B_NOCOR - 12, 0) ** 3 +
        0.17271687 * B_OPSA -
        0.004776089 * max(B_OPSA - 3.5, 0) ** 3 +
        0.0082785543 * max(B_OPSA - 5.7, 0) ** 3 -
        0.0035024653 * max(B_OPSA - 8.7, 0) ** 3 +
        0.044464692 * B_OPFPS -
        0.00025552455 * max(B_OPFPS - 9.6774194, 0) ** 3 +
        0.00045626256 * max(B_OPFPS - 16.071429, 0) ** 3 -
        0.00020073801 * max(B_OPFPS - 24.210526, 0) ** 3 +
        0.5100204 * (HIS_PCA == "Yes") -
        0.2273623 * (B_DRE == "Yes") -
        0.0047034328 * B_BMI -
        0.00019338575 * max(B_BMI - 23.15, 0) ** 3 +
        0.00033024336 * max(B_BMI - 26.83, 0) ** 3 -
        0.00013685761 * max(B_BMI - 32.03, 0) ** 3
    if (B_OPFPS >= 0 && B_OPFPS <= 64) {
        round((1 - 0.9523463 ** exp(score)) * 100, 0)
    } else {
        "Not Applicable"
    }
}

raw.highgrade.dutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = -2.5995679 + 0.092685394 * AGE -
        0.000042571616 * max(AGE - 55, 0)**3 +
        0.000085143232 * max(AGE - 63, 0)**3 -
        0.000042571616 * max(AGE - 71, 0)**3 -
        0.02729155 * B_PV +
        0.000003473756 * max(B_PV - 25.52, 0)**3 -
        0.000005955998 * max(B_PV - 43.47, 0)**3 +
        0.000002482242 * max(B_PV - 68.59, 0)**3 -
        0.021879504 * B_NOCOR -
        0.0013241433 * max(B_NOCOR - 6, 0)**3 +
        0.0026482866 * max(B_NOCOR - 9, 0)**3 -
        0.0013241433 * max(B_NOCOR - 12, 0)**3 +
        0.1414056 * B_OPSA -
        0.0038989431 * max(B_OPSA - 3.5, 0)**3 +
        0.006758168 * max(B_OPSA - 5.7, 0)**3 -
        0.0028592249 * max(B_OPSA - 8.7, 0)**3 -
        0.1644022 * B_OPFPS +
        0.00056993789 * max(B_OPFPS - 9.6774194, 0)**3 -
        0.0010176765 * max(B_OPFPS - 16.071429, 0)**3 +
        0.00044773859 * max(B_OPFPS - 24.210526, 0)**3 +
        0.31134948 * (HIS_PCA == "Yes") -
        0.52677693 * (B_DRE == "Yes") +
        0.01188137 * B_BMI +
        0.00011619678 * max(B_BMI - 23.15, 0)**3 -
        0.00019842834 * max(B_BMI - 26.83, 0)**3 +
        0.000082231564 * max(B_BMI - 32.03, 0)**3
    if (50 <= AGE && AGE <= 75 && 0 <= B_PV && B_PV <= 80 && 6 <= B_NOCOR && B_NOCOR <= 12 && 2 <= B_OPSA && B_OPSA <= 10 && 0 <= B_OPFPS && B_OPFPS <= 64 && HIS_PCA != "Unknown" && B_DRE != "Unknown" && 15 <= B_BMI && B_BMI <= 50) {
        (1 - 0.9560246 ** exp(score)) * 100
    } else {
        "Not Applicable"
    }
}
raw.highgrade.nodutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = -5.291106 + 0.12865175 * AGE -
        0.00011792908 * max(AGE - 55, 0)**3 +
        0.00023585817 * max(AGE - 63, 0)**3 -
        0.00011792908 * max(AGE - 71, 0)**3 -
        0.041330344 * B_PV +
        2.0545925e-05 * max(B_PV - 25.52, 0)**3 -
        3.5227428e-05 * max(B_PV - 43.47, 0)**3 +
        1.4681503e-05 * max(B_PV - 68.59, 0)**3 -
        0.11735785 * B_NOCOR +
        0.002743688 * max(B_NOCOR - 6, 0)**3 -
        0.005487376 * max(B_NOCOR - 9, 0)**3 +
        0.002743688 * max(B_NOCOR - 12, 0)**3 +
        0.24274067 * B_OPSA -
        0.0096728386 * max(B_OPSA - 3.5, 0)**3 +
        0.016766254 * max(B_OPSA - 5.7, 0)**3 -
        0.007093415 * max(B_OPSA - 8.7, 0)**3 -
        0.14091258 * B_OPFPS +
        0.00050049136 * max(B_OPFPS - 9.6774194, 0)**3 -
        0.00089367332 * max(B_OPFPS - 16.071429, 0)**3 +
        0.00039318196 * max(B_OPFPS - 24.210526, 0)**3 +
        0.55482753 * (HIS_PCA == "Yes") -
        0.1854322 * (B_DRE == "Yes") +
        0.027549519 * B_BMI -
        0.0003469818 * max(B_BMI - 23.15, 0)**3 +
        0.00059253815 * max(B_BMI - 26.83, 0)**3 -
        0.00024555635 * max(B_BMI - 32.03, 0)**3
    if (50 <= AGE && AGE <= 75 && 0 <= B_PV && B_PV <= 80 && 2 <= B_OPSA && B_OPSA <= 10 && 0 <= B_OPFPS && B_OPFPS <= 64 && HIS_PCA != "Unknown" && B_DRE != "Unknown" && 15 <= B_BMI && B_BMI <= 50) {
        (1 - 0.9485273 ** exp(score)) * 100
    } else {
        "Not Applicable"
    }
}
raw.aur.dutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = 1.1645202 -
        0.061061932 * AGE +
        0.00021214229 * max(AGE - 55, 0) ** 3 -
        0.00042428457 * max(AGE - 63, 0) ** 3 +
        0.00021214229 * max(AGE - 71, 0) ** 3 -
        0.0089110256 * B_PV +
        0.0000079993515 * max(B_PV - 25.52, 0) ** 3 -
        0.000013715449 * max(B_PV - 43.47, 0) ** 3 +
        0.0000057160971 * max(B_PV - 68.59, 0) ** 3 +
        0.32260345 * B_OPSA -
        0.014797257 * max(B_OPSA - 3.5, 0) ** 3 +
        0.025648579 * max(B_OPSA - 5.7, 0) ** 3 -
        0.010851322 * max(B_OPSA - 8.7, 0) ** 3 +
        0.13327946 * B_IPSS -
        0.0003871158 * max(B_IPSS - 2, 0) ** 3 +
        0.00064519299 * max(B_IPSS - 8, 0) ** 3 -
        0.0002580772 * max(B_IPSS - 17, 0) ** 3 +
        0.01045639 * B_QM -
        0.00016491276 * max(B_QM - 7.8, 0) ** 3 +
        0.00025179364 * max(B_QM - 13.2, 0) ** 3 -
        0.000086880871 * max(B_QM - 23.45, 0) ** 3 +
        0.008271271 * B_RSD -
        0.00000029329635 * max(B_RSD, 0) ** 3 +
        0.0000009545575 * max(B_RSD - 31, 0) ** 3 -
        0.0000001021594 * max(B_RSD - 120, 0) ** 3
    if (50 <= AGE && AGE <= 75 && 0 <= B_PV && B_PV <= 80 && 2 <= B_OPSA && B_OPSA <= 88 && 0 <= B_IPSS && B_IPSS <= 25 && 0 <= B_QM && B_QM <= 100 && B_RSD >= 0 ) {
        (1 - 0.9881902 ** exp(score)) * 100
    } else {
        "Not Applicable"
    }
}
raw.aur.nodutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = -1.0281503 -
        0.00076540945 * AGE -
        0.000069130129 * max(AGE - 55, 0) ** 3 +
        0.00013826026 * max(AGE - 63, 0)**3 -
        0.000069130129 * max(AGE - 71, 0)**3 +
        0.045963842 * B_PV -
        0.000017356701 * max(B_PV - 25.52, 0)**3 +
        0.000029759281 * max(B_PV - 43.47, 0)**3 -
        0.000012402579 * max(B_PV - 68.59, 0)**3 +
        0.0023571984 * B_OPSA +
        0.00008654012 * max(B_OPSA - 3.5, 0)**3 -
        0.00015000288 * max(B_OPSA - 5.7, 0)**3 +
        0.000063462755 * max(B_OPSA - 8.7, 0)**3 +
        0.087108858 * B_IPSS -
        0.00025960794 * max(B_IPSS - 2, 0)**3 +
        0.00043267991 * max(B_IPSS - 8, 0)**3 -
        0.00017307196 * max(B_IPSS - 17, 0)**3 -
        0.11685329 * B_QM +
        0.00045782518 * max(B_QM - 7.8, 0)**3 -
        0.00069902089 * max(B_QM - 13.2, 0)**3 +
        0.0002411957 * max(B_QM - 23.45, 0)**3 +
        0.0061259723 * B_RSD -
        0.00000057253793 * max(B_RSD, 0)**3 +
        0.00000077196125 * max(B_RSD - 31, 0)**3 -
        0.00000019942332 * max(B_RSD - 120, 0)**3
    if (50 <= AGE && AGE <= 75 && 0 <= B_PV && B_PV <= 80 && 2 <= B_OPSA && B_OPSA <= 88 && 0 <= B_IPSS && B_IPSS <= 25 && 0 <= B_QM && B_QM <= 100 && B_RSD >= 0) {
        (1 - 0.9424894 ** exp(score)) * 100
    } else {
        "Not Applicable"
    }
}
raw.bph.dutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = -5.1794212 + 0.082837869 * AGE -
        0.00019166777 * max(AGE - 55, 0)**3 +
        0.00038333555 * max(AGE - 63, 0)**3 -
        0.00019166777 * max(AGE - 71, 0)**3 +
        0.019842467 * B_PV -
        7.9898849e-06 * max(B_PV - 25.52, 0)**3 +
        1.3699217e-05 * max(B_PV - 43.47, 0)**3 -
        5.7093326e-06 * max(B_PV - 68.59, 0)**3 +
        0.024113451 * B_OPSA +
        0.0020938172 * max(B_OPSA - 3.5, 0)**3 -
        0.0036292832 * max(B_OPSA - 5.7, 0)**3 +
        0.001535466 * max(B_OPSA - 8.7, 0)**3 -
        0.084429276 * B_IPSS +
        0.0007641629 * max(B_IPSS - 2, 0)**3 -
        0.0012736048 * max(B_IPSS - 8, 0)**3 +
        0.00050944193 * max(B_IPSS - 17, 0)**3 -
        0.040246013 * B_QM +
        8.79458e-05 * max(B_QM - 7.8, 0)**3 -
        0.00013427822 * max(B_QM - 13.2, 0)**3 +
        4.6332421e-05 * max(B_QM - 23.45, 0)**3 +
        0.0028358349 * B_RSD -
        6.8147752e-07 * max(B_RSD, 0)**3 +
        9.188461e-07 * max(B_RSD - 31, 0)**3 -
        2.3736857e-07 * max(B_RSD - 120, 0)**3
    if (50 <= AGE && AGE <= 75 && 0 <= B_PV && B_PV <= 80 && 2 <= B_OPSA && B_OPSA <= 88 && 0 <= B_IPSS && B_IPSS <= 25 && 0 <= B_QM && B_QM <= 100 && B_RSD >= 0) {
        (1 - 0.9880496 ** exp(score)) * 100
    } else {
        "Not Applicable"
    }
}
raw.bph.nodutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = -2.5335304 + 0.025530334 * AGE -
        0.00027794159 * max(AGE - 55, 0)**3 +
        0.00055588319 * max(AGE - 63, 0)**3 -
        0.00027794159 * max(AGE - 71, 0)**3 +
        0.031405179 * B_PV -
        0.000011141665 * max(B_PV - 25.52, 0)**3 +
        0.000019103165 * max(B_PV - 43.47, 0)**3 -
        0.0000079615 * max(B_PV - 68.59, 0)**3 -
        0.011456454 * B_OPSA +
        0.0030614148 * max(B_OPSA - 3.5, 0)**3 -
        0.0053064523 * max(B_OPSA - 5.7, 0)**3 +
        0.0022450375 * max(B_OPSA - 8.7, 0)**3 +
        0.17153886 * B_IPSS -
        0.00050278585 * max(B_IPSS - 2, 0)**3 +
        0.00083797642 * max(B_IPSS - 8, 0)**3 -
        0.00033519057 * max(B_IPSS - 17, 0)**3 -
        0.10624904 * B_QM +
        0.00037314418 * max(B_QM - 7.8, 0)**3 -
        0.00056972746 * max(B_QM - 13.2, 0)**3 +
        0.00019658328 * max(B_QM - 23.45, 0)**3 +
        0.0047543213 * B_RSD -
        0.00000044918222 * max(B_RSD, 0)**3 +
        0.00000060563894 * max(B_RSD - 31, 0)**3 -
        0.00000015645673 * max(B_RSD - 120, 0)**3
    if (50 <= AGE && AGE <= 75 && 0 <= B_PV && B_PV <= 80 && 2 <= B_OPSA && B_OPSA <= 88 && 0 <= B_IPSS && B_IPSS <= 25 && 0 <= B_QM && B_QM <= 100 && B_RSD >= 0) {
        (1 - 0.9621862 ** exp(score)) * 100
    } else {
        "Not Applicable"
    }
}
raw.erectile.dutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = -0.82555754 +
        0.0021009936 * AGE -
        0.00018470233 * max(AGE - 55, 0)**3 +
        0.00036940465 * max(AGE - 63, 0)**3 -
        0.00018470233 * max(AGE - 71, 0)**3 +
        1.0040617 * (SBSRL == "Yes") +
        0.29803134 * (LIB == "Yes") -
        0.0028454973 * (IMP == "Yes")
    if (50 <= AGE && AGE<= 75 && SBSRL != "Unknown" && LIB != "Unknown" && IMP != "Unknown") {
        (1 - 0.8331268 ** exp(score)) * 100
    } else {
        "Not Applicable"
    }
}
raw.erectile.nodutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = 0.49218732 - 0.017043475 * AGE -
        0.000099164052 * max(AGE - 55, 0)**3 +
        0.0001983281 * max(AGE - 63, 0)**3 -
        0.000099164052 * max(AGE - 71, 0)**3 +
        0.67408096 * (SBSRL == "Yes") +
        0.28603854 * (LIB == "Yes") +
        0.21585816 * (IMP == "Yes")
    if (50 <= AGE && AGE <= 75 && SBSRL != "Unknown" && LIB != "Unknown" && IMP != "Unknown") {
        (1 - 0.8792946 ** exp(score)) * 100
    } else {
        "Not Applicable"
    }
}
raw.gynecomastia.dutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = -1.6541886 +
        0.013380387 * AGE -
        0.000025127812 * max(AGE - 55, 0)**3 +
        0.000050255624 * max(AGE - 63, 0)**3 -
        0.000025127812 * max(AGE - 71, 0)**3 +
        0.030085377 * B_BMI +
        0.0001100241 * max(B_BMI - 23.15, 0)**3 -
        0.00018788731 * max(B_BMI - 26.83, 0)**3 +
        0.00007786321 * max(B_BMI - 32.03, 0)**3
    if (50 <= AGE && AGE <= 75 && 15 <= B_BMI && B_BMI<= 50) {
        (1 - 0.9634263 ** exp(score)) * 100
    } else {
        "Not Applicable"
    }
}
raw.gynecomastia.nodutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = -2.0653904 -
        0.0019965622 * AGE -
        0.00001577009 * max(AGE - 55, 0)**3 +
        0.00003154018 * max(AGE - 63, 0)**3 -
        0.00001577009 * max(AGE - 71, 0)**3 +
        0.083659972 * B_BMI -
        0.0005061525 * max(B_BMI - 23.15, 0)**3 +
        0.00086435274 * max(B_BMI - 26.83, 0)**3 -
        0.00035820023 * max(B_BMI - 32.03, 0)**3
    if (50 <= AGE && AGE <= 75 && 15 <= B_BMI && B_BMI <= 50) {
        (1 - 0.9783186 ** exp(score)) * 100
    } else {
        "Not Applicable"
    }
}
raw.hgpin.dutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    if (50 <= AGE && AGE <= 75 && 0 <= B_PV && B_PV <= 80 && 6 <= B_NOCOR && B_NOCOR <= 12 && 2 <= B_OPSA && B_OPSA <= 10 && 0 <= B_OPFPS && B_OPFPS <= 64 && HIS_PCA != "Unknown" && B_DRE != "Unknown" && 15 <= B_BMI && B_BMI <= 50) {
        0.03838831 * 100
    } else {
        "Not Applicable"
    }
}
raw.hgpin.nodutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = 0.02314685 * AGE +
        9.462079e-05 * max(AGE - 55, 0)**3 -
        0.00018924158 * max(AGE - 63, 0)**3 +
        9.462079e-05 * max(AGE - 71, 0)**3 -
        0.0076597772 * B_PV +
        2.1045322e-06 * max(B_PV - 25.52, 0)**3 -
        3.6083679e-06 * max(B_PV - 43.47, 0)**3 +
        1.5038357e-06 * max(B_PV - 68.59, 0)**3 +
        0.024188546 * B_NOCOR +
        0.00028423913 * max(B_NOCOR - 6, 0)**3 -
        0.00056847825 * max(B_NOCOR - 9, 0)**3 +
        0.00028423913 * max(B_NOCOR - 12, 0)**3 -
        0.035761911 * B_OPSA +
        0.0018467184 * max(B_OPSA - 3.5, 0)**3 -
        0.0032009786 * max(B_OPSA - 5.7, 0)**3 +
        0.0013542602 * max(B_OPSA - 8.7, 0)**3 +
        0.031267747 * B_OPFPS -
        0.00013307385 * max(B_OPFPS - 9.6774194, 0)**3 +
        0.00023761559 * max(B_OPFPS - 16.071429, 0)**3 -
        0.00010454174 * max(B_OPFPS - 24.210526, 0)**3 +
        0.096023267 * (HIS_PCA == "Yes") -
        0.15972617 * (B_DRE == "Yes") -
        0.046172021 * B_BMI +
        0.00088524838 * max(B_BMI - 23.15, 0)**3 -
        0.0015117318 * max(B_BMI - 26.83, 0)**3 +
        0.00062648347 * max(B_BMI - 32.03, 0)**3
    if (50 <= AGE && AGE <= 75 && 0 <= B_PV && B_PV <= 80 && 6 <= B_NOCOR && B_NOCOR <= 12 && 2 <= B_OPSA && B_OPSA <= 10 && 0 <= B_OPFPS && B_OPFPS <= 64 && HIS_PCA != "Unknown" && B_DRE != "Unknown" && 15 <= B_BMI && B_BMI <= 50) {
        (1 - 0.9676886 ** exp(score)) * 100
    } else {
        "Not Applicable"
    }
}
raw.prostate.dutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = -3.2873301 + 0.062184251 * AGE -
        7.1247133e-05 * max(AGE - 55, 0)**3 +
        0.00014249427 * max(AGE - 63, 0)**3 -
        7.1247133e-05 * max(AGE - 71, 0)**3 -
        0.013281746 * B_PV +
        4.2085264e-08 * max(B_PV - 25.52, 0)**3 -
        7.2158134e-08 * max(B_PV - 43.47, 0)**3 +
        3.007287e-08 * max(B_PV - 68.59, 0)**3 -
        0.020945724 * B_NOCOR -
        0.0013792832 * max(B_NOCOR - 6, 0)**3 +
        0.0027585664 * max(B_NOCOR - 9, 0)**3 -
        0.0013792832 * max(B_NOCOR - 12, 0)**3 +
        0.092260347 * B_OPSA -
        0.003146994 * max(B_OPSA - 3.5, 0)**3 +
        0.0054547896 * max(B_OPSA - 5.7, 0)**3 -
        0.0023077956 * max(B_OPSA - 8.7, 0)**3 -
        0.069689053 * B_OPFPS +
        0.00024776037 * max(B_OPFPS - 9.6774194, 0)**3 -
        0.0004423989 * max(B_OPFPS - 16.071429, 0)**3 +
        0.00019463854 * max(B_OPFPS - 24.210526, 0)**3 +
        0.32320144 * (HIS_PCA == "Yes") -
        0.091053957 * (B_DRE == "Yes") +
        0.035915989 * B_BMI -
        0.0005530593 * max(B_BMI - 23.15, 0)**3 +
        0.00094445511 * max(B_BMI - 26.83, 0)**3 -
        0.00039139581 * max(B_BMI - 32.03, 0)**3
    if (50 <= AGE && AGE <= 75 && 0 <= B_PV && B_PV <= 80 && 6 <= B_NOCOR && B_NOCOR <= 12 && 2 <= B_OPSA && B_OPSA <= 10 && 0 <= B_OPFPS && B_OPFPS <= 64 && HIS_PCA != "Unknown" && B_DRE != "Unknown" && 15 <= B_BMI && B_BMI<= 50) {
        (1 - 0.8443213 ** exp(score)) * 100
    } else {
        "Not Applicable"
    }
}
raw.prostate.nodutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = -2.0022764 + 0.056199639 * AGE-
        0.000015829258 * max(AGE-55,0) ** 3 +
        0.000031658515 * max(AGE-63,0) ** 3-
        0.000015829258 * max(AGE-71,0) ** 3-
        0.028379627 * B_PV +
        0.00001559305 * max(B_PV-25.52,0) ** 3-
        0.000026735376 * max(B_PV-43.47,0) ** 3 +
        0.000011142327 * max(B_PV-68.59,0) ** 3-
        0.055600097 * B_NOCOR +
        0.00089358345 * max(B_NOCOR-6,0) ** 3-
        0.0017871669 * max(B_NOCOR-9,0) ** 3 +
        0.00089358345 * max(B_NOCOR-12,0) ** 3 +
        0.16137068 * B_OPSA-
        0.0067701874 * max(B_OPSA-3.5,0) ** 3 +
        0.011734992 * max(B_OPSA-5.7,0) ** 3-
        0.0049648041 * max(B_OPSA-8.7,0) ** 3 -
        0.066716939 * B_OPFPS +
        0.00017396904 * max(B_OPFPS-9.6774194,0) ** 3-
        0.00031063771 * max(B_OPFPS-16.071429,0) ** 3 +
        0.00013666867 * max(B_OPFPS-24.210526,0) ** 3 +
        0.43429612 * (HIS_PCA == "Yes")-
        0.25508281 * (B_DRE == "Yes")+
        0.016145135 * B_BMI-
        0.00038880393 * max(B_BMI-23.15,0) ** 3 +
        0.00066395748 * max(B_BMI-26.83,0) ** 3-
        0.00027515355 * max(B_BMI-32.03,0) ** 3
    if (50 <= AGE && AGE <= 75 && 0 <= B_PV && B_PV <= 80 && 6 <= B_NOCOR && B_NOCOR <= 12 && 2 <= B_OPSA && B_OPSA <= 10 && 0 <= B_OPFPS && B_OPFPS <= 64 && HIS_PCA != "Unknown" && B_DRE != "Unknown" && 15 <= B_BMI && B_BMI<= 50) {
        (1 - 0.7987971 ** exp(score)) * 100
    } else {
        "Not Applicable"
    }
}
raw.uti.dutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = -0.33966523 + 0.014924564 * B_QM -
        0.000075239732 * max(B_QM - 7.8, 0)**3 +
        0.00011487823 * max(B_QM - 13.2, 0)**3 -
        0.000039638493 * max(B_QM - 23.45, 0)**3 +
        0.0059938379 * B_RSD -
        0.00000048861775 * max(B_RSD, 0)**3 +
        0.00000065881045 * max(B_RSD - 31, 0)**3 -
        0.0000001701927 * max(B_RSD - 120, 0)**3
    if (0 <= B_QM && B_QM <= 100 && B_RSD >= 0) {
        (1 - 0.9433828 ** exp(score)) * 100
    } else {
        "Not Applicable"
    }
}
raw.uti.nodutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = 0.66770954 - 0.069385484 * B_QM +
        0.00028417274 * max(B_QM - 7.8, 0)**3 -
        0.00043388325 * max(B_QM - 13.2, 0)**3 +
        0.00014971051 * max(B_QM - 23.45, 0)**3 +
        0.0061318174 * B_RSD -
        0.00000062268412 * max(B_RSD, 0)**3 +
        0.0000008395741 * max(B_RSD - 31, 0)**3 -
        0.00000021688997 * max(B_RSD - 120, 0)**3
    if (0 <= B_QM && B_QM <= 100 && B_RSD >= 0) {
        (1 - 0.9433828 ** exp(score)) * 100
    } else {
        "Not Applicable"
    }
}
raw.asap.dutasteride <- function(B_OPFPS,AGE,SBSRL,B_BMI,IMP,LIB,HIS_PCA,B_IPSS,B_QM,B_NOCOR,B_OPSA,B_PV,B_RSD,B_DRE) {
    score = -0.0011455882 * AGE +
        3.4941473e-05 * max(AGE - 55,0) ** 3 -
        6.9882947e-05 * max(AGE - 63, 0) ** 3 +
        3.4941473e-05 * max(AGE - 71, 0) ** 3 -
        0.013058082 * B_PV +
        2.2486763e-06 * max(B_PV - 25.52, 0) ** 3 -
        3.855513e-06 * max(B_PV - 43.47, 0) ** 3 +
        1.6068367e-06 * max(B_PV - 68.59, 0) ** 3 -
        0.11978819 * B_NOCOR +
        0.0048529883 * max(B_NOCOR - 6, 0) ** 3 -
        0.0097059765 * max(B_NOCOR - 9, 0) ** 3 +
        0.0048529883 * max(B_NOCOR - 12, 0) ** 3 +
        0.17271687 * B_OPSA -
        0.004776089 * max(B_OPSA - 3.5, 0) ** 3 +
        0.0082785543 * max(B_OPSA - 5.7, 0) ** 3 -
        0.0035024653 * max(B_OPSA - 8.7, 0) ** 3 +
        0.044464692 * B_OPFPS -
        0.00025552455 * max(B_OPFPS - 9.6774194, 0) ** 3 +
        0.00045626256 * max(B_OPFPS - 16.071429, 0) ** 3 -
        0.00020073801 * max(B_OPFPS - 24.210526, 0) ** 3 +
        0.5100204 * (HIS_PCA == "Yes") -
        0.2273623 * (B_DRE == "Yes") -
        0.0047034328 * B_BMI -
        0.00019338575 * max(B_BMI - 23.15, 0) ** 3 +
        0.00033024336 * max(B_BMI - 26.83, 0) ** 3 -
        0.00013685761 * max(B_BMI - 32.03, 0) ** 3
    if (B_OPFPS >= 0 && B_OPFPS <= 64) {
        (1 - 0.9523463 ** exp(score)) * 100
    } else {
        "Not Applicable"
    }
}


CASES <- list(
 list(63,  5.7, "No",  "Yes","No", "No", "No",  16.0, 26.8, 12, 12.0, 9,  43.5, 40),
 list(52,  2.2, "Yes", "No", "Yes","Yes","Yes", 10.0, 22.0,  5,  8.0, 6,  25.6, 10),
 list(74,  9.8, "No",  "No", "No", "Yes","No",  24.0, 32.0, 25, 20.0, 12, 79.0, 90),
 list(58,  4.1, "Yes", "Yes","No", "No", "Yes", 30.0, 24.5,  8, 15.0, 10, 35.0,  5),
 list(69,  7.3, "No",  "Yes","Yes","No", "No",  12.0, 29.9, 18, 10.5, 11, 60.0, 55),
 list(50,  2.0, "No",  "No", "No", "No", "No",   9.7, 15.0,  0,  5.0, 6,   0.1,  0),
 list(75, 10.0, "Yes", "Yes","Yes","Yes","Yes", 64.0, 50.0, 35, 25.0, 12, 80.0,150),
 list(66,  6.0, "No",  "Yes","No", "No", "No",  18.0, 27.5, 14, 13.0, 10, 48.0, 30)
)
OUTCOMES <- c("highgrade","prostate","hgpin","asap","aur","bph","erectile","gynecomastia","uti")
num <- function(v) if (is.character(v)) "null" else sprintf("%.10f", v)
out <- c()
for (cs in CASES) {
  a <- list(B_OPFPS=cs[[8]], AGE=cs[[1]], SBSRL=cs[[4]], B_BMI=cs[[9]], IMP=cs[[5]],
            LIB=cs[[6]], HIS_PCA=cs[[7]], B_IPSS=cs[[10]], B_QM=cs[[11]],
            B_NOCOR=cs[[12]], B_OPSA=cs[[2]], B_PV=cs[[13]], B_RSD=cs[[14]], B_DRE=cs[[3]])
  parts <- c()
  for (o in OUTCOMES) {
    d <- do.call(get(paste0("raw.", o, ".dutasteride")), a)
    nd <- if (exists(paste0("raw.", o, ".nodutasteride")))
            do.call(get(paste0("raw.", o, ".nodutasteride")), a) else "Not Applicable"
    parts <- c(parts, sprintf('"%s": {"d": %s, "nd": %s}', o, num(d), num(nd)))
  }
  out <- c(out, sprintf(
    '  {"age": %g, "psa": %g, "dre_abnormal": %s, "sexually_active": %s, "history_of_impotence": %s, "history_of_libido_problems": %s, "family_history_prostate_cancer": %s, "percent_free_psa": %g, "bmi": %g, "ipss_score": %g, "max_urinary_flow_ml_s": %g, "biopsy_cores": %g, "prostate_volume_ml": %g, "residual_urine_ml": %g, "outcomes": {%s}}',
    cs[[1]], cs[[2]],
    tolower(cs[[3]]=="Yes"), tolower(cs[[4]]=="Yes"), tolower(cs[[5]]=="Yes"),
    tolower(cs[[6]]=="Yes"), tolower(cs[[7]]=="Yes"),
    cs[[8]], cs[[9]], cs[[10]], cs[[11]], cs[[12]], cs[[13]], cs[[14]],
    paste(parts, collapse=", ")))
}
cat("{\n", '  "source": "riskcalc.org ProstateCancerConsideringDutasteride/server.R, R ',
    paste0(R.version$major, ".", R.version$minor), '",\n  "cases": [\n',
    paste(out, collapse=",\n"), "\n  ]\n}\n", sep="")
